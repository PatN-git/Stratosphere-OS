#!/usr/bin/env python3
"""
validate_memory.py

A deterministic memory validator for the Stratosphere OS memory protocol.
Ensures memory files follow trust tag, ID uniqueness, supersession,
cross-reference, and secret hygiene rules.

Exit Codes:
  0 - Clean
  1 - Errors (or Warnings if --warnings-as-errors is set)
  2 - Warnings (only when --warnings-as-errors is NOT set)
"""

import sys
import os
import re
import argparse
import json
import subprocess
from pathlib import Path

# Common Secret Signatures
STATUS_BUDGET = 3000

SECRET_PATTERNS = {
    'OpenAI API Key': r'\bsk-[a-zA-Z0-9]{48}\b',
    'GitHub Personal Access Token (Classic)': r'\bghp_[a-zA-Z0-9]{36}\b',
    'GitHub Fine-Grained Token': r'\bgithub_pat_[a-zA-Z0-9]{82}\b',
    'AWS Access Key ID': r'\bAKIA[A-Z0-9]{16}\b',
    'Generic Private Key': r'-----BEGIN [A-Z ]+ PRIVATE KEY-----'
}

_ACTIVE_HANDLE_RE = re.compile(r'\[\[([A-Za-z0-9_-]+)\]\]')
_ACTIVE_DEF_LINE_RE = re.compile(r'^\s*[-*+]\s+\**\s*\[\[([A-Za-z0-9_-]+)\]\](.*)')
_MEMORY_HANDLE_RE = re.compile(r'^(L|A|G|DR)-\d{3,}$')
_MEMORY_PLACEHOLDER_RE = re.compile(r'^(L|A|G|DR)-X+$')
_MEMORY_PLACEHOLDER_ALT_RE = re.compile(r'^(L|A|G|DR)-Y+$')
_WIKILINK_TOKEN_RE = re.compile(r'\[\[([^\]\n]+)\]\]')
_DEF_LINE_RE = re.compile(r'^\s*[-*+]\s+\**\s*\[\[([A-Za-z0-9_-]+)\]\]')
_FENCE_OPEN_RE = re.compile(r'^[ \t]*(`{3,}|~{3,})')
_IGNORED_DOC_SEGMENTS = ('archive', '.archive', '.tmp', '.templates', 'knowledge')
_RESERVED_DOC_STEMS = ('index', 'readme')

def scan_file_for_secrets(file_path):
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f, 1):
                for name, pattern in SECRET_PATTERNS.items():
                    if re.search(pattern, line):
                        errors.append(f"Secret detected ({name}) in {file_path.name}:{idx}")
    except Exception as e:
        errors.append(f"Could not read {file_path.name} for secrets: {e}")
    return errors

def is_placeholder(cid):
    return bool(_MEMORY_PLACEHOLDER_RE.match(cid) or _MEMORY_PLACEHOLDER_ALT_RE.match(cid))


def mask_code_and_comments(content: str) -> str:
    """Strip fenced code blocks, HTML comments, and inline code spans while preserving line numbers."""
    normalized = content.replace("\r\n", "\n")
    lines = normalized.split("\n")
    masked_lines = []
    fence_char = None
    fence_len = 0
    for line in lines:
        if fence_char is None:
            m = _FENCE_OPEN_RE.match(line)
            if m:
                marker = m.group(1)
                fence_char = marker[0]
                fence_len = len(marker)
                masked_lines.append("")
                continue
            masked_lines.append(line)
        else:
            stripped = line.strip()
            if stripped and all(ch == fence_char for ch in stripped) and len(stripped) >= fence_len:
                fence_char = None
                fence_len = 0
            masked_lines.append("")
    text = "\n".join(masked_lines)
    text = re.sub(r'<!--[\s\S]*?-->', lambda m: "\n" * m.group(0).count("\n"), text)
    text = re.sub(r'(`+)([^\n]*?)\1', '', text)
    return text


def parse_wikilink_token(raw_token: str) -> tuple[str, str | None, str | None]:
    """Parse 'stem#section|alias' into (stem, section, alias), preserving backslashes for validation."""
    target_part, has_pipe, alias_part = raw_token.partition('|')
    alias = alias_part.strip() or None if has_pipe else None
    stem_part, has_hash, section_part = target_part.partition('#')
    section = section_part.strip() or None if has_hash else None
    stem = stem_part.strip()
    while '//' in stem:
        stem = stem.replace('//', '/')
    if stem.startswith('./'):
        stem = stem[2:]
    return stem, section, alias


def _is_ignored_doc_path(rel_posix: str) -> bool:
    parts = rel_posix.split('/')
    if any(seg in _IGNORED_DOC_SEGMENTS for seg in parts[:-1]):
        return True
    if parts[0] == '.memory' and (len(parts) > 2 and parts[1] == 'resume' or parts[-1] == 'STATUS.md'):
        return True
    return False


def build_doc_index(tracked: set[str]) -> dict[str, list[str]]:
    """Build bare-stem -> sorted tracked POSIX path index across docs/** and .memory/**."""
    stems: dict[str, list[str]] = {}
    for rel in sorted(tracked):
        if not rel.endswith('.md') or not (rel.startswith('docs/') or rel.startswith('.memory/')):
            continue
        if _is_ignored_doc_path(rel):
            continue
        stem = rel.rsplit('/', 1)[-1][:-3]
        stems.setdefault(stem, []).append(rel)
    return stems


def resolve_document_wikilink(
    stem_or_path: str,
    tracked_files: set[str],
    doc_stems_map: dict[str, list[str]],
    _tracked_lower: dict[str, str] | None = None,
    _stems_lower: dict[str, list[str]] | None = None,
) -> tuple[str | None, str | None]:
    """Resolve a document wikilink against git-tracked files.

    Returns (resolved_rel_path, message):
      - (None, None): exempt placeholder
      - (path, None): resolved cleanly
      - (path, warning): ambiguous stem collision
      - (None, error): unresolvable, case-mismatch, backslash, or reserved stem
    """
    if is_placeholder(stem_or_path):
        return None, None
    if '\\' in stem_or_path:
        return None, f"Invalid backslash in wikilink '[[{stem_or_path}]]'; use POSIX forward slash /"
    if not stem_or_path or stem_or_path.startswith('/') or '..' in stem_or_path.split('/'):
        return None, f"Invalid document link path: '[[{stem_or_path}]]'"

    if '/' in stem_or_path:
        cand = stem_or_path if stem_or_path.endswith('.md') else f"{stem_or_path}.md"
        if cand in tracked_files:
            return cand, None
        tracked_lower = _tracked_lower if _tracked_lower is not None else {p.lower(): p for p in tracked_files}
        actual = tracked_lower.get(cand.lower())
        if actual:
            return None, f"Case mismatch against git index: '[[{stem_or_path}]]' does not match tracked path '{actual}'"
        return None, f"Dangling document link: '[[{stem_or_path}]]' ('{cand}' is not tracked by git)"

    stem = stem_or_path[:-3] if stem_or_path.endswith('.md') else stem_or_path
    if stem.lower() in _RESERVED_DOC_STEMS:
        return None, f"Reserved stem '[[{stem_or_path}]]' must be path-qualified (e.g. '[[docs/<folder>/{stem}]]')"
    matches = doc_stems_map.get(stem, [])
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        suggestions = ", ".join(f"[[{m[:-3]}]]" for m in matches)
        return matches[0], (
            f"Ambiguous stem '{stem}' matches multiple files ({', '.join(matches)}); "
            f"qualify with minimum vault-root prefix: {suggestions}"
        )

    stems_lower = _stems_lower if _stems_lower is not None else {k.lower(): v for k, v in doc_stems_map.items()}
    ci_matches = stems_lower.get(stem.lower())
    if ci_matches:
        return None, f"Case mismatch against git index: '[[{stem_or_path}]]' does not match tracked file '{ci_matches[0]}'"
    return None, f"Dangling document link: '[[{stem_or_path}]]'"

def tracked_files(start):
    """Repo-relative tracked paths (forward slashes), or None without git or outside a repository."""
    try:
        top = subprocess.run(['git', '-C', str(start), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
        if top.returncode != 0:
            return None
        ls = subprocess.run(['git', '-C', top.stdout.strip(), 'ls-files', '-z'], capture_output=True, text=True, encoding='utf-8')
    except OSError:
        return None
    return set(filter(None, ls.stdout.split('\0'))) if ls.returncode == 0 else None


def check_binding_error(raw, tracked):
    """None when a `Check: <path>` binding names a tracked file (or, with a trailing `/`, a tracked directory)."""
    path = raw.replace('\\', '/')
    while path.startswith('./'):
        path = path[2:]
    if path.startswith('/') or '..' in path.split('/'):
        return "must stay inside the repository"
    if path in tracked or (path.endswith('/') and any(t.startswith(path) for t in tracked)):
        return None
    return "which git does not track"


def find_id_gaps(definitions):
    """Warnings for missing numbers inside each L-/G-/A-/DR- ID sequence."""
    seqs = {}
    for def_id in definitions:
        prefix, _, num = def_id.rpartition('-')
        if prefix in ('L', 'G', 'A', 'DR') and num.isdigit():
            seqs.setdefault(prefix, set()).add(int(num))
    out = []
    for prefix, nums in sorted(seqs.items()):
        runs = []
        for n in range(min(nums), max(nums) + 1):
            if n in nums:
                continue
            if runs and n == runs[-1][1] + 1:
                runs[-1][1] = n
            else:
                runs.append([n, n])
        for lo, hi in runs:
            span = f"{prefix}-{lo:03d}" if lo == hi else f"{prefix}-{lo:03d}..{prefix}-{hi:03d}"
            out.append(f"ID gap: possible hard-delete: {span} missing - add [REMOVED] tombstones to silence.")
    return out

def apply_autofix(memory_dir, file_name, line_num, cid):
    if file_name == 'GLOSSARY.md':
        return False
    fpath = Path(memory_dir) / file_name
    if not fpath.exists():
        return False
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        idx = line_num - 1
        if idx < 0 or idx >= len(lines):
            return False
            
        line = lines[idx]
        line_stripped = line.rstrip('\r\n')
        newline = line[len(line_stripped):]
        
        # Glossary or list item
        if f"[[{cid}]]" not in line_stripped:
            if "Refs:" in line_stripped:
                # Find last bracket link and append reference after it
                match = re.search(r'(\[\[[A-Za-z0-9_-]+\]\])\s*\.?$', line_stripped)
                if match:
                    end = match.end(1)
                    lines[idx] = line_stripped[:end] + f", [[{cid}]]" + line_stripped[end:] + newline
                else:
                    lines[idx] = line_stripped + f", [[{cid}]]" + newline
            else:
                if line_stripped.endswith('.'):
                    lines[idx] = line_stripped.rstrip('.') + f". Refs: [[{cid}]]." + newline
                else:
                    lines[idx] = line_stripped + f" Refs: [[{cid}]]" + newline

        with open(fpath, 'w', encoding='utf-8', newline='') as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"Error applying autofix to {file_name}:{line_num}: {e}")
        return False

def extract_active_refs(issue_body=None, query_issue=None, memory_dir=".memory", out_path=".tmp/active-memory-refs.txt"):
    """
    Deterministically extracts exact referenced tags ([[L-xxx]], [[A-xxx]], [[DR-xxx]], [[G-xxx]])
    from an issue body or queried issue ID, and writes matching definition blocks from memory_dir
    to out_path. Executes in <5ms with 0 model calls, preserving negative constraints verbatim.
    """
    memory_path = Path(memory_dir)
    target_out = Path(out_path)
    target_out.parent.mkdir(parents=True, exist_ok=True)

    text_to_scan = issue_body or ""
    if not text_to_scan and query_issue:
        # Normalize BT-<id> to numeric ID for gh CLI
        issue_id = re.sub(r'^[A-Za-z]+-', '', str(query_issue).strip())
        try:
            res = subprocess.run(["gh", "issue", "view", issue_id, "--json", "body"],
                                 capture_output=True, text=True, check=True)
            data = json.loads(res.stdout)
            text_to_scan = data.get("body", "")
        except Exception as e:
            text_to_scan = f"# Error fetching issue {query_issue}: {e}"

    # Extract all referenced ID handles: [[L-xxx]], [[A-xxx]], [[DR-xxx]], [[G-xxx]]
    raw_handles = _ACTIVE_HANDLE_RE.findall(text_to_scan)
    active_ids = []
    active_set = set()
    for h in raw_handles:
        if not is_placeholder(h) and h not in active_set:
            active_ids.append(h)
            active_set.add(h)

    # Scan target memory files for definitions (optimized by prefix filter)
    definitions = {}
    if active_set:
        target_files = []
        if any(i.startswith('A-') for i in active_set):
            target_files.append('ARCHITECTURE.md')
        if any(i.startswith('L-') for i in active_set):
            target_files.append('LEARNINGS.md')
        if any(i.startswith('G-') for i in active_set):
            target_files.append('GLOSSARY.md')
        if any(i.startswith('DR-') for i in active_set):
            target_files.append('DESIGN_RULES.md')
        if any(not i.startswith(('A-', 'L-', 'G-', 'DR-')) for i in active_set):
            target_files = ['ARCHITECTURE.md', 'LEARNINGS.md', 'GLOSSARY.md', 'DESIGN_RULES.md']

        for fname in target_files:
            fpath = memory_path / fname
            if not fpath.is_file():
                continue
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                continue

            lines = content.splitlines()
            current_def_id = None
            current_block = []

            for line in lines:
                if line and line.lstrip()[:1] in ('-', '*', '+'):
                    def_m = _ACTIVE_DEF_LINE_RE.match(line)
                    if def_m:
                        if current_def_id and current_block:
                            definitions[current_def_id] = "\n".join(current_block)
                        did = def_m.group(1)
                        if not is_placeholder(did):
                            current_def_id = did
                            current_block = [line]
                        else:
                            current_def_id = None
                            current_block = []
                        continue
                if current_def_id:
                    if line.startswith((' ', '\t')) or (line and not line.startswith(('#', '- ', '* '))):
                        current_block.append(line)
                    else:
                        definitions[current_def_id] = "\n".join(current_block)
                        current_def_id = None
                        current_block = []
            if current_def_id and current_block:
                definitions[current_def_id] = "\n".join(current_block)

    # Format active references output
    lines_out = [
        "# Active Memory References (Deterministic AST Indexer)",
        f"# Extracted at zero token cost for task context: {query_issue or 'custom'}",
        ""
    ]
    resolved_count = 0
    unresolved = []

    for rid in active_ids:
        if rid in definitions:
            lines_out.append(f"### [[{rid}]]")
            lines_out.append(definitions[rid].strip())
            lines_out.append("")
            resolved_count += 1
        else:
            unresolved.append(rid)

    if unresolved:
        lines_out.append("### Unresolved References")
        for u in unresolved:
            lines_out.append(f"- [[{u}]]: not found in active definitions")
        lines_out.append("")

    target_out.write_text("\n".join(lines_out), encoding="utf-8")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Validate Stratosphere OS memory protocol compliance.")
    parser.add_argument('--path', default='.memory', help='Path to the memory directory')
    parser.add_argument('--quiet', action='store_true', help='Suppress human-readable console output')
    parser.add_argument('--warnings-as-errors', action='store_true', help='Treat warnings as exit-code errors')
    parser.add_argument('--autofix', action='store_true', help='Automatically attempt to fix one-way reference warnings in place')
    parser.add_argument('--index', action='store_true', help='Extract referenced memory blocks for active issue/task')
    parser.add_argument('--query-issue', help='Issue ID or BT-xxx to fetch from tracker')
    parser.add_argument('--issue-body', help='Path to offline issue body markdown file')
    parser.add_argument('--memory-dir', default='.memory', help='Path to memory directory (alias for --path)')
    parser.add_argument('--out', default='.tmp/active-memory-refs.txt', help='Output file path for active refs')
    args = parser.parse_args()

    if args.index:
        mem_dir = args.memory_dir if args.memory_dir != '.memory' else args.path
        body = None
        if args.issue_body:
            try:
                body = Path(args.issue_body).read_text(encoding='utf-8')
            except Exception as e:
                print(f"Error reading issue body: {e}", file=sys.stderr)
                sys.exit(1)
        res = extract_active_refs(issue_body=body, query_issue=args.query_issue, memory_dir=mem_dir, out_path=args.out)
        if not args.quiet:
            print(f"AST Indexer: wrote active references to {args.out}")
        sys.exit(res)

    memory_dir = Path(args.path)
    repo_root = memory_dir.resolve().parent if memory_dir.name == '.memory' else Path.cwd().resolve()
    docs_dir = repo_root / 'docs'

    errors = []
    warnings = []

    # A missing .memory/ must NOT skip the docs/ OKF conformance walk below.
    # Coupling them meant the framework repo (which has no .memory/) never
    # validated docs/ at all, which is how unregistered types accumulated.
    docs_present = docs_dir.is_dir()
    if not memory_dir.exists() or not memory_dir.is_dir():
        if not docs_present:
            if not args.quiet:
                print(f"Neither '{args.path}' nor 'docs' exists. Skipping validation.")
            print("# MACHINE")
            print(json.dumps({"clean": True, "errors": [], "warnings": []}))
            sys.exit(0)
        if not args.quiet:
            print(f"Memory directory '{args.path}' does not exist - validating docs/ only.")

    # 1. Scan all files in memory directory for secrets (including STATUS.md, DESIGN.md, etc.)
    for path in memory_dir.glob('*'):
        if path.is_file():
            sec_errs = scan_file_for_secrets(path)
            errors.extend(sec_errs)

    # STATUS.md is folder state only: keep it small and local (gitignored).
    status_file = memory_dir / 'STATUS.md'
    if status_file.is_file():
        size = len(status_file.read_text(encoding='utf-8', errors='replace'))
        if size > STATUS_BUDGET:
            warnings.append(f"STATUS.md is {size} chars (budget {STATUS_BUDGET:,}): keep folder state only; history and next steps live on the issue.")
        try:
            tracked_status = subprocess.run(['git', '-C', str(memory_dir), 'ls-files', '--error-unmatch', 'STATUS.md'], capture_output=True).returncode == 0
        except OSError:
            tracked_status = False
        if tracked_status:
            warnings.append("STATUS.md is tracked by git: run `git rm --cached .memory/STATUS.md` and add `.memory/STATUS.md` to .gitignore.")

    # Files to parse for IDs and protocol compliance
    target_files = [
        'LEARNINGS.md',
        'GLOSSARY.md',
        'ARCHITECTURE.md',
        'DESIGN_RULES.md'
    ]
    # Local issues live on the tracker branch; `issues.py check` lints them.

    definitions = {}
    references = []
    doc_links = []

    def _record_token(raw_tok, file_label, line_idx, context_id, stripped_line, *, memory_handles=True):
        stem, section, alias = parse_wikilink_token(raw_tok)
        if section is None and alias is None and _MEMORY_HANDLE_RE.match(stem):
            if memory_handles:
                references.append({
                    'id': stem,
                    'file': file_label,
                    'line_num': line_idx,
                    'context_id': context_id,
                    'content': stripped_line,
                })
        elif section is None and alias is None and is_placeholder(stem):
            return
        elif not stem and section is not None:
            return
        else:
            doc_links.append({
                'raw': raw_tok,
                'stem': stem,
                'file': file_label,
                'line_num': line_idx,
            })

    # Parse target memory files
    for fname in target_files:
        fpath = memory_dir / fname
        if not fpath.exists():
            continue

        try:
            raw_text = fpath.read_text(encoding='utf-8')
        except Exception as e:
            errors.append(f"Could not read {fname}: {e}")
            continue

        lines = raw_text.replace('\r\n', '\n').split('\n')
        masked_lines = mask_code_and_comments(raw_text).split('\n')

        in_superseded = False
        current_context_id = None
        current_list_indent = None

        for line_idx, (line, masked_line) in enumerate(zip(lines, masked_lines), 1):
            stripped = line.strip()
            if not stripped:
                continue

            # Detect section transitions
            if line.startswith('#'):
                current_context_id = None
                current_list_indent = None
                heading_match = re.match(r'^(#+)\s+(.*)', line)
                if heading_match:
                    level = len(heading_match.group(1))
                    title = heading_match.group(2).strip().lower()
                    if 'superseded' in title:
                        in_superseded = True
                    elif level == 2:
                        in_superseded = False

            # Standard list/heading item parsing
            list_match = re.match(r'^(\s*)([-*+])\s+(.*)', line)
            is_list_item = list_match is not None

            tokens = _WIKILINK_TOKEN_RE.findall(masked_line)
            def_match = _DEF_LINE_RE.search(masked_line)
            is_heading_def = (
                masked_line.startswith('#')
                and bool(tokens)
                and masked_line.lstrip('#').strip().startswith('[[')
            )

            if def_match or is_heading_def:
                def_id = def_match.group(1) if def_match else tokens[0]

                if is_placeholder(def_id):
                    remaining_tokens = tokens[1:] if (tokens and tokens[0] == def_id) else tokens
                    if is_list_item:
                        indent = len(list_match.group(1))
                        if current_list_indent is not None and indent > current_list_indent:
                            pass
                        else:
                            current_list_indent = indent
                            current_context_id = None
                else:
                    # Parse trust tag
                    tag_match = re.search(r'\[(LAW|PATTERN|ASSUMED)\]', line)
                    tag = tag_match.group(1) if tag_match else None

                    # Parse superseded target
                    sup_match = re.search(r'\[SUPERSEDED BY\s+(?:\[\[)?([A-Za-z0-9_-]+)(?:\]\])?\]', line, re.IGNORECASE)
                    superseded_by = sup_match.group(1) if sup_match else None
                    removed = '[REMOVED]' in line
                    # A [LAW] entry may end with `Check: <repo path>` naming the test or lint that enforces it (single line)
                    check_match = re.search(r'\bCheck:\s*`?([^\s`]+)', line) if tag == 'LAW' else None

                    # Register definition
                    if def_id in definitions:
                        prev = definitions[def_id]
                        errors.append(f"Duplicate ID definition: '{def_id}' defined in {prev['file']}:{prev['line_num']} and {fname}:{line_idx}")
                    else:
                        definitions[def_id] = {
                            'id': def_id,
                            'file': fname,
                            'line_num': line_idx,
                            'tag': tag,
                            'superseded_by': superseded_by,
                            'removed': removed,
                            'check': check_match.group(1) if check_match else None,
                            'in_superseded': in_superseded,
                            'content': stripped
                        }

                    if is_list_item:
                        current_list_indent = len(list_match.group(1))
                        current_context_id = def_id

                    remaining_tokens = tokens[1:] if (tokens and tokens[0] == def_id) else tokens
            else:
                if is_list_item:
                    indent = len(list_match.group(1))
                    if current_list_indent is not None and indent > current_list_indent:
                        # Sub-item, keep context
                        pass
                    else:
                        current_list_indent = indent
                        current_context_id = None
                else:
                    indent = len(line) - len(line.lstrip())
                    if current_list_indent is not None and indent > current_list_indent:
                        # Indented text block, keep context
                        pass
                    else:
                        current_list_indent = None
                        current_context_id = None
                remaining_tokens = tokens

            for raw_tok in remaining_tokens:
                _record_token(raw_tok, fname, line_idx, current_context_id, stripped)

    # Also scan secondary .memory/ files (e.g. DESIGN.md, DATABASE_SCHEMA.md) for document wikilinks
    for fname in ('DESIGN.md', 'DATABASE_SCHEMA.md'):
        fpath = memory_dir / fname
        if not fpath.is_file():
            continue
        try:
            raw_text = fpath.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for line_idx, masked_line in enumerate(mask_code_and_comments(raw_text).split('\n'), 1):
            for raw_tok in _WIKILINK_TOKEN_RE.findall(masked_line):
                _record_token(raw_tok, f".memory/{fname}", line_idx, None, '', memory_handles=False)

    # Scan external files (docs/ directory, ignoring archives/templates) for memory handles and document wikilinks
    if docs_present:
        for path in sorted(docs_dir.rglob('*.md')):
            rel = path.relative_to(docs_dir)
            if any(seg in _IGNORED_DOC_SEGMENTS for seg in rel.parts):
                continue
            display_path = path.resolve().relative_to(repo_root).as_posix()
            if _MEMORY_HANDLE_RE.match(path.stem):
                errors.append(
                    f"Namespace collision: '{display_path}' uses reserved memory handle stem "
                    f"'{path.stem}' (reserved for .memory/ handles)."
                )
            try:
                raw_text = path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            raw_lines = raw_text.replace('\r\n', '\n').split('\n')
            masked_lines = mask_code_and_comments(raw_text).split('\n')
            for line_idx, (raw_line, masked_line) in enumerate(zip(raw_lines, masked_lines), 1):
                for raw_tok in _WIKILINK_TOKEN_RE.findall(masked_line):
                    _record_token(raw_tok, display_path, line_idx, None, raw_line.strip())

    # 1.5 OKF Conformance Check (Error tier: a missing/empty type field is a validation error)
    okf_as_error = True
    okf_files_to_check = []
    if memory_dir.exists() and memory_dir.is_dir():
        for path in memory_dir.glob('**/*.md'):
            if path.name == "index.md" or 'resume' in path.relative_to(memory_dir).parts[:-1]:
                continue  # resume/ holds per-task resume notes, local scratch with no frontmatter
            okf_files_to_check.append(path)

    if docs_present:
        for path in docs_dir.glob('**/*.md'):
            if path.name == "index.md":
                continue
            try:
                rel = path.relative_to(docs_dir)
                # Out of OKF scope: inbound foreign bundles, historical records,
                # and placeholder templates (okf-protocol §1, §6).
                if any(seg in ('knowledge', 'archive', '.archive', '.templates')
                       for seg in rel.parts):
                    continue
            except ValueError:
                pass
            okf_files_to_check.append(path)

    for path in okf_files_to_check:
        try:
            display_path = path.resolve().relative_to(repo_root).as_posix()
        except ValueError:
            display_path = str(path)
            
        try:
            content = path.read_text(encoding='utf-8')
            m = re.match(r"^---\r?\n(.*?)\r?\n---", content, re.S)
            if not m:
                msg = f"OKF conformance: {display_path} is missing parseable frontmatter."
                if okf_as_error:
                    errors.append(msg)
                else:
                    warnings.append(msg)
                continue
            
            fm_text = m.group(1)
            fm = {}
            for line in fm_text.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    k, v = line.split(':', 1)
                    fm[k.strip()] = v.strip()
            
            # Top-level keys only (nested generated.by/at are indented); warnings, not
            # errors, so legacy v0.1 docs in a consumer project are nudged, not blocked.
            top = {}
            for line in fm_text.splitlines():
                if line[:1] in (' ', chr(9)) or ':' not in line:
                    continue
                k, v = line.split(':', 1)
                top[k.strip()] = re.sub(r'\s+#.*$', '', v).strip().strip('"' + "'")
            if 'timestamp' in top:
                warnings.append(f"OKF v0.2: {display_path} carries retired 'timestamp:' - use 'generated: {{by, at}}' (frontmatter-only edit).")
            status = top.get('status')
            if (status and status not in ('draft', 'stable', 'deprecated')
                    and top.get('type') != 'discovery-brief'):
                warnings.append(f"OKF v0.2: {display_path} has status '{status}' - must be draft | stable | deprecated.")

            if 'type' not in fm or not fm['type']:
                msg = f"OKF conformance: {display_path} is missing a non-empty 'type' field in frontmatter."
                if okf_as_error:
                    errors.append(msg)
                else:
                    warnings.append(msg)
        except Exception as e:
            msg = f"OKF conformance: Could not read {display_path} for frontmatter: {e}"
            if okf_as_error:
                errors.append(msg)
            else:
                warnings.append(msg)

    # 2. Trust Tag Rules Validation
    for def_id, info in definitions.items():
        if info['in_superseded']:
            if info.get('removed'):
                continue  # [REMOVED] tombstone: valid terminal marker, no successor needed
            if not info['superseded_by']:
                errors.append(f"Supersession error: Superseded entry '{def_id}' in {info['file']}:{info['line_num']} is missing a valid [SUPERSEDED BY [[ID]]] target.")
            elif info['superseded_by'] not in definitions:
                errors.append(f"Supersession error: Superseded entry '{def_id}' in {info['file']}:{info['line_num']} points to undefined target '{info['superseded_by']}'.")
            continue
            
        # Active entries validation
        if not info['tag']:
            errors.append(f"Trust tag error: Missing trust tag for active definition '{def_id}' in {info['file']}:{info['line_num']}.")
        else:
            tag = info['tag']
            fname = info['file']
            if fname in ['ARCHITECTURE.md', 'DESIGN_RULES.md']:
                if tag != 'LAW':
                    errors.append(f"Purity error: Active entry '{def_id}' in {fname}:{info['line_num']} has trust tag '[{tag}]'. Must be '[LAW]'.")
            elif fname == 'GLOSSARY.md':
                if tag == 'LAW':
                    errors.append(f"Purity error: Glossary term '{def_id}' in {fname}:{info['line_num']} has trust tag '[LAW]'. Glossary entries cannot be '[LAW]'.")
                # An entry carries only Avoid:/Source:; promotion evidence is derived from Ref, never stored.
                # Fields start at the first Avoid:/Source:, so a prose label in the definition is not one.
                first = re.search(r'\.\s+(?:Avoid|Source):\s', info['content'])
                tail = info['content'][first.start():] if first else ''
                for field in re.findall(r'\.\s+([A-Z][a-z]+):\s', tail):
                    if field not in ('Avoid', 'Source'):
                        warnings.append(f"Glossary field: unknown field `{field}:` in {def_id} ({fname}:{info['line_num']}); glossary entries carry only Avoid:/Source: (promotion evidence is derived from Ref).")

    # 2.4 Check bindings: a [LAW] naming its check must name a file git tracks, so a stale binding cannot
    # silently switch the 4a Standards auditor off for that rule. No git: one warning, only when a binding exists.
    tracked = None
    tracked_checked = False
    bindings = [(i, info) for i, info in definitions.items() if info.get('check') and not info['in_superseded']]
    if bindings:
        tracked = tracked_files(repo_root)
        tracked_checked = True
        if tracked is None:
            warnings.append("Check bindings: could not verify Check bindings (not a git repository, or git is unavailable).")
        else:
            for def_id, info in bindings:
                problem = check_binding_error(info['check'], tracked)
                if problem:
                    errors.append(f"Check binding: '{def_id}' in {info['file']}:{info['line_num']} names '{info['check']}', {problem}.")

    # 2.5 ID gaps: a hard-deleted entry frees its ID for reuse. Warning only, because
    # existing projects carry gaps from past deletes; a [REMOVED] tombstone closes one.
    warnings.extend(find_id_gaps(definitions))

    # 3. Cross-reference Integrity
    directed_links = set()
    for ref in references:
        rid = ref['id']
        if rid not in definitions:
            errors.append(f"Dangling reference: '{rid}' referenced in {ref['file']}:{ref['line_num']} is not defined anywhere in the memory layer.")
        else:
            if ref['context_id']:
                directed_links.add((ref['context_id'], rid))

    # 4. Bidirectional Consistency (Warning only)
    for cid, rid in directed_links:
        # Reciprocity is checked ONLY for memory-to-memory links (L/A/DR <-> L/A/DR).
        # Glossary entries carry only Avoid:/Source: and are exempt from reciprocal Refs:.
        if cid.startswith('G-') or rid.startswith('G-'):
            continue
        if not (any(cid.startswith(p) for p in ['L-', 'A-', 'DR-']) and any(rid.startswith(p) for p in ['L-', 'A-', 'DR-'])):
            continue
            
        c_info = definitions.get(cid)
        r_info = definitions.get(rid)
        if c_info and r_info:
            if not c_info['in_superseded'] and not r_info['in_superseded']:
                if (rid, cid) not in directed_links:
                    if getattr(args, 'autofix', False):
                        if apply_autofix(args.path, r_info['file'], r_info['line_num'], cid):
                            if not args.quiet:
                                print(f"[AUTO-FIXED] Added reciprocal reference to '{cid}' in {r_info['file']}:{r_info['line_num']}")
                            continue
                    warnings.append(f"One-way reference: '{cid}' references '{rid}' in {c_info['file']}:{c_info['line_num']}, but '{rid}' does not reference '{cid}' back.")

    # 5. Document Wikilink Existence & Hygiene Validation (git-tracked authority)
    if doc_links:
        if not tracked_checked:
            tracked = tracked_files(repo_root)
        if tracked is None:
            warnings.append("Document wikilinks: could not verify document links (not a git repository, or git is unavailable).")
        else:
            doc_stems_map = build_doc_index(tracked)
            tracked_lower = {p.lower(): p for p in tracked}
            stems_lower = {k.lower(): v for k, v in doc_stems_map.items()}
            for link in doc_links:
                resolved, msg = resolve_document_wikilink(
                    link['stem'], tracked, doc_stems_map, tracked_lower, stems_lower
                )
                if msg:
                    loc = f"{link['file']}:{link['line_num']}"
                    if resolved is None:
                        errors.append(f"{msg} in {loc}")
                    else:
                        warnings.append(f"{msg} in {loc}")

    # Print human-readable report if not quiet
    if not args.quiet:
        print("=== Stratosphere OS Memory Validator ===")
        if errors:
            print(f"\nErrors found ({len(errors)}):")
            for err in errors:
                print(f"  [ERROR] {err}")
        else:
            print("\nNo errors found.")
            
        if warnings:
            print(f"\nWarnings found ({len(warnings)}):")
            for wrn in warnings:
                print(f"  [WARNING] {wrn}")
        else:
            print("\nNo warnings found.")
        print("========================================")

    # Machine JSON block output
    is_clean = len(errors) == 0 and len(warnings) == 0
    print("# MACHINE")
    print(json.dumps({
        "clean": is_clean,
        "errors": errors,
        "warnings": warnings
    }))

    # Set exit status
    if errors:
        sys.exit(1)
    elif warnings:
        sys.exit(1 if args.warnings_as_errors else 2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
