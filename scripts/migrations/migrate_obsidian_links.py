#!/usr/bin/env python3
"""Deterministic migration CLI to rewrite legacy markdown links to Obsidian wikilinks
and regenerate directory index.md Maps of Content (MOCs) per OKF v0.2 §4 and BT-233.

Usage:
    python scripts/migrations/migrate_obsidian_links.py [--dry-run] [--write] [--project PATH] [--force]
"""
from __future__ import annotations

import argparse
import os
import posixpath
import re
import subprocess
import sys
from pathlib import Path

# Ensure project scripts are importable
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _ensure_sys_path(project_root: Path) -> None:
    for cand in [
        project_root / "src" / "scripts",
        project_root / ".agents" / "scripts",
        _REPO_ROOT / "src" / "scripts",
    ]:
        if cand.is_dir() and str(cand) not in sys.path:
            sys.path.insert(0, str(cand))


# Import validation primitives
try:
    _ensure_sys_path(_REPO_ROOT)
    import validate_memory
except ImportError:
    validate_memory = None


_IGNORED_SEGMENTS = {
    "archive",
    ".archive",
    ".templates",
    ".tmp",
    "node_modules",
    ".git",
    "build",
    "dist",
}

_RESERVED_STEMS = {"index", "readme"}


def is_ignored_path(rel_posix: str) -> bool:
    """Check if relative POSIX path falls under ignored directories or scratch files."""
    parts = rel_posix.split("/")
    if any(seg in _IGNORED_SEGMENTS for seg in parts[:-1]):
        return True
    if parts[0] == ".memory" and (
        (len(parts) > 2 and parts[1] == "resume") or parts[-1] == "STATUS.md"
    ):
        return True
    return False


def check_working_tree_clean(project_root: Path) -> bool:
    """Returns True if git status --porcelain is empty."""
    try:
        res = subprocess.run(
            ["git", "-C", str(project_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if res.returncode != 0:
            return False
        return not bool(res.stdout.strip())
    except Exception:
        return False


def get_protected_spans(content: str) -> list[tuple[int, int]]:
    """Identifies spans inside fenced code blocks and HTML comments."""
    protected: list[tuple[int, int]] = []

    # 1. Fenced code blocks
    lines = content.splitlines(keepends=True)
    pos = 0
    fence_char = None
    fence_len = 0
    fence_start = 0
    for line in lines:
        stripped = line.strip()
        if fence_char is None:
            m = re.match(r"^(`{3,}|~{3,})", stripped)
            if m:
                marker = m.group(1)
                fence_char = marker[0]
                fence_len = len(marker)
                fence_start = pos
        else:
            if stripped and all(ch == fence_char for ch in stripped) and len(stripped) >= fence_len:
                protected.append((fence_start, pos + len(line)))
                fence_char = None
                fence_len = 0
        pos += len(line)
    if fence_char is not None:
        protected.append((fence_start, len(content)))

    # 2. HTML comments
    for m in re.finditer(r"<!--[\s\S]*?-->", content):
        protected.append((m.start(), m.end()))

    return sorted(protected)


def get_inline_code_spans(content: str, protected_blocks: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Identifies inline code spans outside fenced blocks/comments."""
    spans: list[tuple[int, int]] = []
    for m in re.finditer(r"(`+)([^\n`]+?)\1", content):
        start, end = m.span()
        # Ensure not inside an already protected fenced block or comment
        if not any(b_start <= start and end <= b_end for b_start, b_end in protected_blocks):
            spans.append((start, end))
    return spans


def extract_title_and_description(doc_path: Path) -> tuple[str, str]:
    """Extracts (title, description) from YAML frontmatter, falling back to stem/body."""
    try:
        text = doc_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return doc_path.stem, ""

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            title = None
            description = None
            for line in fm_text.splitlines():
                line_str = line.strip()
                if line_str.startswith("title:"):
                    val = line_str[len("title:"):].strip().strip("\"'")
                    if val:
                        title = val
                elif line_str.startswith("description:"):
                    val = line_str[len("description:"):].strip().strip("\"'")
                    if val:
                        description = val
            if title is not None:
                return title, description or ""

    for line in text.splitlines():
        line_str = line.strip()
        if line_str.startswith("# "):
            return line_str[2:].strip(), ""

    return doc_path.stem, ""


def rebuild_moc_index(
    dir_path: Path,
    files: list[Path],
    doc_stems_map: dict[str, list[str]] | None = None,
    project_root: Path | None = None,
) -> str:
    """Constructs a frontmatter-free OKF v0.2 MOC listing for dir_path/index.md using shortest-path wikilinks:

    # <Dir Name>
    * [[<doc-stem>|<Title>]] - <Description>
    """
    root = project_root or _REPO_ROOT
    lines: list[str] = []
    for f in sorted(files, key=lambda p: p.name.lower()):
        if f.name == "index.md":
            continue
        stem = f.stem
        try:
            rel_f = f.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            rel_f = f.as_posix()
        rel_f_no_ext = rel_f[:-3] if rel_f.endswith(".md") else rel_f

        # Determine wikilink target (shortest disambiguated path)
        if stem.lower() in _RESERVED_STEMS:
            target_wikilink = rel_f_no_ext
        elif doc_stems_map and len(doc_stems_map.get(stem, [])) > 1:
            target_wikilink = rel_f_no_ext
        else:
            target_wikilink = stem

        title, description = extract_title_and_description(f)
        desc_clean = " ".join(description.split()) if description else ""

        if title and title != stem:
            link_expr = f"[[{target_wikilink}|{title}]]"
        else:
            link_expr = f"[[{target_wikilink}]]"

        if desc_clean:
            lines.append(f"* {link_expr} - {desc_clean}")
        else:
            lines.append(f"* {link_expr}")

    content = f"# {dir_path.name}\n"
    if lines:
        content += "\n" + "\n".join(lines) + "\n"
    return content


_LINK_RE = re.compile(r"(?<!\!)\[(?P<label>[^\]\r\n]+)\]\((?P<target>[^)\r\n]+)\)")


def rewrite_markdown_links(
    file_path: Path,
    content: str,
    tracked_stems: dict[str, list[str]],
    project_root: Path | None = None,
    tracked_files: set[str] | None = None,
    log_details: list[dict] | None = None,
) -> tuple[str, int]:
    """Transforms [Label](path/to/stem.md) into [[stem|Label]] (or [[docs/folder/stem|Label]] on collision).

    Preserves external URLs (http/https/mailto) and image links without alteration.
    Returns (updated_content, replacement_count).
    """
    root = project_root or _REPO_ROOT
    protected_blocks = get_protected_spans(content)
    inline_spans = get_inline_code_spans(content, protected_blocks)

    try:
        file_rel = file_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        file_rel = file_path.as_posix()
    file_dir = posixpath.dirname(file_rel)

    replacements: list[tuple[int, int, str]] = []

    for m in _LINK_RE.finditer(content):
        l_start, l_end = m.span()

        # 1. Skip if link is inside fenced block or HTML comment
        if any(b_start <= l_start and l_end <= b_end for b_start, b_end in protected_blocks):
            continue

        # 2. Skip if link is strictly inside an inline code span
        if any(c_start <= l_start and l_end <= c_end for c_start, c_end in inline_spans):
            continue

        raw_label = m.group("label").strip()
        raw_target = m.group("target").strip()

        # Handle target partitioning (anchor / section)
        target_path_part, has_hash, anchor_part = raw_target.partition("#")
        target_path_part = target_path_part.strip().strip("<>")
        anchor_str = f"#{anchor_part.strip()}" if has_hash and anchor_part.strip() else ""

        # Anchor-only link (#heading) -> keep untouched
        if not target_path_part:
            continue

        # External URLs / schemes -> keep untouched
        if (
            re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target_path_part)
            or target_path_part.startswith("mailto:")
        ):
            continue

        # Only process links targeting markdown documents
        if not (target_path_part.endswith(".md") or "/" in target_path_part or "\\" in target_path_part):
            continue

        # Non-markdown extensions (.png, .json, .py, etc.) -> keep untouched
        ext = posixpath.splitext(target_path_part)[1].lower()
        if ext and ext != ".md":
            continue

        # Normalize relative path to project root
        norm_target = target_path_part.replace("\\", "/")
        if norm_target.startswith("/"):
            target_rel = norm_target.lstrip("/")
        else:
            target_rel = posixpath.normpath(posixpath.join(file_dir, norm_target))

        target_rel_no_ext = target_rel[:-3] if target_rel.endswith(".md") else target_rel
        target_stem = posixpath.basename(target_rel_no_ext)

        # Check if target is inside docs/ or .memory/
        if not (target_rel.startswith("docs/") or target_rel.startswith(".memory/")):
            # Outside documentation scope (e.g. src/ or root) -> keep untouched
            continue

        # Determine wikilink target representation
        if target_stem.lower() in _RESERVED_STEMS:
            wikilink_target = target_rel_no_ext
        else:
            candidates = tracked_stems.get(target_stem, [])
            if len(candidates) > 1:
                wikilink_target = target_rel_no_ext
            elif len(candidates) == 1:
                wikilink_target = target_stem
            else:
                # Target not found in indexed stems
                if tracked_files and (target_rel in tracked_files or f"{target_rel_no_ext}.md" in tracked_files):
                    wikilink_target = target_rel_no_ext
                else:
                    # Unresolvable link
                    wikilink_target = target_stem

        full_target = f"{wikilink_target}{anchor_str}"
        if raw_label == full_target or raw_label == target_stem:
            replacement = f"[[{full_target}]]"
        else:
            replacement = f"[[{full_target}|{raw_label}]]"

        replacements.append((l_start, l_end, replacement))
        if log_details is not None:
            log_details.append({
                "label": raw_label,
                "target": raw_target,
                "replacement": replacement,
            })

    if not replacements:
        return content, 0

    # Apply replacements from end to start to preserve character offsets
    out_chars = list(content)
    for start, end, repl in reversed(replacements):
        out_chars[start:end] = list(repl)

    return "".join(out_chars), len(replacements)


def build_stems_index(project_root: Path, tracked: set[str] | None = None) -> dict[str, list[str]]:
    """Builds bare-stem -> sorted list of relative POSIX paths index across docs/** and .memory/**."""
    stems: dict[str, list[str]] = {}
    if tracked is not None:
        file_list = sorted(tracked)
    else:
        file_list = [
            p.relative_to(project_root).as_posix()
            for p in sorted(project_root.rglob("*.md"))
        ]

    for rel in file_list:
        if not rel.endswith(".md") or not (rel.startswith("docs/") or rel.startswith(".memory/")):
            continue
        if is_ignored_path(rel):
            continue
        stem = rel.rsplit("/", 1)[-1][:-3]
        stems.setdefault(stem, []).append(rel)
    return stems


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate legacy markdown links to Obsidian wikilinks and regenerate directory MOCs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview all conversions and MOC regenerations without modifying files (default).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Apply in-place modifications to docs/** and .memory/**.",
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="Path to project root (defaults to CWD).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Bypass clean working tree pre-check.",
    )
    args = parser.parse_args(argv)
    if args.write:
        args.dry_run = False
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = args.project.resolve()
    _ensure_sys_path(project_root)

    # Clean working tree safety gate
    if args.write and not args.force:
        if not check_working_tree_clean(project_root):
            sys.stderr.write("Error: Working tree is dirty. Commit or stash changes before running --write\n")
            return 1

    # Discover candidate files in docs/** and .memory/**
    candidate_files: list[Path] = []
    for folder_name in ("docs", ".memory"):
        folder = project_root / folder_name
        if not folder.is_dir():
            continue
        for p in sorted(folder.rglob("*.md")):
            rel = p.relative_to(project_root).as_posix()
            if is_ignored_path(rel):
                continue
            candidate_files.append(p)

    # Retrieve tracked files or local file set
    tracked = None
    if validate_memory is not None:
        tracked = validate_memory.tracked_files(project_root)
    if tracked is None:
        tracked = {
            p.relative_to(project_root).as_posix()
            for p in project_root.rglob("*")
            if p.is_file()
        }
    else:
        # Also ensure candidate files on disk in docs/ and .memory/ are included
        tracked = set(tracked)
        for p in candidate_files:
            tracked.add(p.relative_to(project_root).as_posix())

    stems_map = build_stems_index(project_root, tracked)

    # 1. Transform markdown links in memory
    modified_files: dict[Path, str] = {}
    total_link_rewrites = 0
    candidate_rewrites_log: list[str] = []

    for p in candidate_files:
        try:
            raw_content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            sys.stderr.write(f"Error reading '{p}': {e}\n")
            return 1

        file_details: list[dict] = []
        new_content, count = rewrite_markdown_links(
            p,
            raw_content,
            stems_map,
            project_root=project_root,
            tracked_files=tracked,
            log_details=file_details,
        )
        if count > 0:
            modified_files[p] = new_content
            total_link_rewrites += count
            rel_p = p.relative_to(project_root).as_posix()
            detail_strs = ", ".join(d["replacement"] for d in file_details)
            candidate_rewrites_log.append(f"  {rel_p}: {count} link(s) rewritten ({detail_strs})")

    # 2. Discover directories for MOC generation
    moc_files: dict[Path, str] = {}
    candidate_moc_dirs: set[Path] = set()

    memory_dir = project_root / ".memory"
    if memory_dir.is_dir():
        candidate_moc_dirs.add(memory_dir)

    docs_dir = project_root / "docs"
    if docs_dir.is_dir():
        for d in sorted(docs_dir.rglob("*")):
            if d.is_dir():
                rel_d = d.relative_to(project_root).as_posix()
                if not is_ignored_path(rel_d):
                    candidate_moc_dirs.add(d)

    candidate_mocs_log: list[str] = []
    for d in sorted(candidate_moc_dirs):
        child_mds = [
            f for f in sorted(d.glob("*.md"))
            if f.name != "index.md" and not is_ignored_path(f.relative_to(project_root).as_posix())
        ]
        if not child_mds:
            continue
        moc_content = rebuild_moc_index(
            d,
            child_mds,
            doc_stems_map=stems_map,
            project_root=project_root,
        )
        moc_path = d / "index.md"
        moc_files[moc_path] = moc_content
        rel_moc = moc_path.relative_to(project_root).as_posix()
        candidate_mocs_log.append(f"  {rel_moc}: {len(child_mds)} document(s) indexed")

    # 3. Two-phase commit validation: Verify 100% of candidate wikilinks resolve
    if validate_memory is not None and tracked is not None:
        # Build hypothetical tracked set including newly generated index.md files
        hypothetical_tracked = set(tracked)
        for moc_p in moc_files:
            rel_m = moc_p.relative_to(project_root).as_posix()
            hypothetical_tracked.add(rel_m)

        hypo_stems_map = build_stems_index(project_root, hypothetical_tracked)
        tracked_lower = {p.lower(): p for p in hypothetical_tracked}
        stems_lower = {k.lower(): v for k, v in hypo_stems_map.items()}

        validation_errors: list[str] = []

        # Validate rewrites
        for p, content in modified_files.items():
            rel_p = p.relative_to(project_root).as_posix()
            masked = validate_memory.mask_code_and_comments(content)
            for m in validate_memory._WIKILINK_TOKEN_RE.finditer(masked):
                token = m.group(1).strip()
                if validate_memory._MEMORY_HANDLE_RE.match(token) or validate_memory.is_placeholder(token):
                    continue
                stem, _, _ = validate_memory.parse_wikilink_token(token)
                resolved, err = validate_memory.resolve_document_wikilink(
                    stem, hypothetical_tracked, hypo_stems_map, tracked_lower, stems_lower
                )
                if resolved is None and err:
                    validation_errors.append(f"{err} in {rel_p}")

        # Validate MOCs
        for p, content in moc_files.items():
            rel_p = p.relative_to(project_root).as_posix()
            masked = validate_memory.mask_code_and_comments(content)
            for m in validate_memory._WIKILINK_TOKEN_RE.finditer(masked):
                token = m.group(1).strip()
                if validate_memory._MEMORY_HANDLE_RE.match(token) or validate_memory.is_placeholder(token):
                    continue
                stem, _, _ = validate_memory.parse_wikilink_token(token)
                resolved, err = validate_memory.resolve_document_wikilink(
                    stem, hypothetical_tracked, hypo_stems_map, tracked_lower, stems_lower
                )
                if resolved is None and err:
                    validation_errors.append(f"{err} in {rel_p}")

        if validation_errors:
            sys.stderr.write("Validation errors encountered during link migration pre-check:\n")
            for err in validation_errors:
                sys.stderr.write(f"  [ERROR] {err}\n")
            return 1

    # 4. Output reports / Dry-Run vs In-Place Write
    if args.dry_run:
        print("=== Obsidian Link Migration: Dry-Run Preview ===")
        print(f"Total candidate link rewrites: {total_link_rewrites} in {len(modified_files)} file(s)")
        for log in candidate_rewrites_log:
            print(log)
        print(f"\nTotal candidate MOC index files: {len(moc_files)}")
        for log in candidate_mocs_log:
            print(log)
        print("\nDry-run complete. 0 files modified.")
        return 0

    # Write in-place
    # 1. Update modified documents preserving original line endings
    for p, new_content in modified_files.items():
        try:
            raw_bytes = p.read_bytes()
            newline = "\r\n" if b"\r\n" in raw_bytes else "\n"
            p.write_text(new_content, encoding="utf-8", newline=newline)
        except Exception as e:
            sys.stderr.write(f"Error writing to '{p}': {e}\n")
            return 1

    # 2. Write generated MOC index files (preserve if existing, else LF)
    for p, moc_content in moc_files.items():
        try:
            if p.exists():
                raw_bytes = p.read_bytes()
                newline = "\r\n" if b"\r\n" in raw_bytes else "\n"
            else:
                newline = "\n"
            p.write_text(moc_content, encoding="utf-8", newline=newline)
        except Exception as e:
            sys.stderr.write(f"Error writing MOC to '{p}': {e}\n")
            return 1

    print("=== Obsidian Link Migration: Migration Complete ===")
    print(f"Applied {total_link_rewrites} link rewrite(s) across {len(modified_files)} file(s).")
    print(f"Generated/updated {len(moc_files)} directory MOC index file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
