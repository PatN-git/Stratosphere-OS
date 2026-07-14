#!/usr/bin/env python3
"""Deterministic StratosphereOS project scaffolder — zero LLM tokens.

Creates the project's folder structure and copies bundled templates into place.
New files are created if missing; with `--update`, **managed** framework files
(workflows, rules, references, validate_memory.py) are refreshed in place when
they differ, while **preserved** files (.memory/, .gitignore) and the
**constitution** (AGENT.md/CLAUDE.md/GEMINI.md) are never overwritten.

The script lives in the installed plugin at `<plugin>/scripts/scaffold.py`.
Run it FROM THE PROJECT ROOT (cwd = project), e.g.:

  python <plugin>/scripts/scaffold.py
  python <plugin>/scripts/scaffold.py --dry-run
  python <plugin>/scripts/scaffold.py --update            # refresh managed files
  python <plugin>/scripts/scaffold.py --update --dry-run  # preview the refresh

Plugin assets/templates and lifecycle workflows are resolved relative to the
script's own location; the project is resolved from the current directory.

Why this matters on Antigravity: a plugin's workflows/ are NOT registered as
slash commands, so the lifecycle workflows (0a–4b, sync-skills) are copied into
the project's `.agents/workflows/`, where Antigravity DOES surface them as `/`
commands. On Claude Code the plugin commands already register globally; the
project copies are inert there.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

# MUST match the block ids in memory-templates/*.md — enforced by test_known_block_ids_drift_guard
KNOWN_BLOCK_IDS = {
    "backlog-rules", "label-canonical", "backlog-header",
    "design-principles", "design-reference-rules",
    "arch-vocabulary", "arch-guidance",
    "learnings-guidance", "glossary-guidance", "dbschema-rules"
}

def semver_key(v_str):
    if not v_str:
        return (0, 0, 0)
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", v_str)
    if m:
        return tuple(int(x) for x in m.groups())
    return (0, 0, 0)

def get_blocks_map(text):
    blocks_map = {}
    for m in _versioning.CANONICAL_MARKER_PATTERN.finditer(text):
        if m.group(1) == "BLOCK":
            bid = m.group(2)
            try:
                blocks_map[bid] = _versioning.block_hash(text, bid)
            except Exception:
                pass
    return blocks_map

def get_marker_version(text, fallback):
    versions = []
    for m in _versioning.CANONICAL_MARKER_PATTERN.finditer(text):
        if m.group(1) == "BLOCK" and m.group(3):
            versions.append(m.group(3))
    if versions:
        try:
            return max(versions, key=semver_key)
        except Exception:
            return versions[0]
    return fallback

def parse_file_blocks(text, raw=False):
    if not raw:
        text = _versioning.normalize(text)
    matches = list(_versioning.CANONICAL_MARKER_PATTERN.finditer(text))
    
    seen_ids = set()
    open_blocks = {}
    for m in matches:
        full_match = m.group(0)
        tag_type = m.group(1)
        is_close = tag_type == "/BLOCK"
        block_id = m.group(2)
        version = m.group(3)
        if block_id not in KNOWN_BLOCK_IDS:
            # NOTE: Renaming a block ID in the future breaks forward compatibility. If a block ID is renamed
            # in the templates, downstream target projects with existing files carrying the old ID in the wild
            # will raise ValueError and skip updating. Renaming/removing block IDs requires writing a project
            # migration script (similar to inject_markers.py) to update target project files first.
            raise ValueError(f"Unknown block ID '{block_id}'")
        if not is_close:
            if block_id in seen_ids:
                raise ValueError(f"Duplicate block ID '{block_id}'")
            if block_id in open_blocks:
                raise ValueError(f"Nested block ID '{block_id}'")
            open_blocks[block_id] = m
            seen_ids.add(block_id)
        else:
            if block_id not in open_blocks:
                raise ValueError(f"Orphan close marker for block ID '{block_id}'")
            del open_blocks[block_id]
            
    if open_blocks:
        raise ValueError(f"Unterminated block markers: {list(open_blocks.keys())}")
        
    segments = []
    idx = 0
    while idx < len(text):
        m_start = _versioning.CANONICAL_MARKER_PATTERN.search(text, idx)
        if not m_start:
            segments.append({"type": "text", "content": text[idx:]})
            break
            
        if m_start.start() > idx:
            segments.append({"type": "text", "content": text[idx:m_start.start()]})
            
        if m_start.group(1) == "/BLOCK":
            raise ValueError(f"Unexpected close marker at {m_start.start()}")
            
        block_id = m_start.group(2)
        version = m_start.group(3)
        
        close_pat = re.compile(r'<!--\s*SOS:/BLOCK\s+id=' + re.escape(block_id) + r'\s*-->')
        m_end = close_pat.search(text, m_start.end())
        if not m_end:
            raise ValueError(f"Failed to find end marker for '{block_id}'")
            
        inter_content = text[m_start.end():m_end.start()]
        raw_block = text[m_start.start():m_end.end()]
        
        segments.append({
            "type": "block",
            "id": block_id,
            "version": version,
            "content": inter_content,
            "raw_block": raw_block
        })
        idx = m_end.end()
    return segments

def clean_for_raw_compare(text):
    has_bom = text.startswith("\ufeff")
    if has_bom:
        text = text[1:]
    lines = text.splitlines(keepends=True)
    fm_start = -1
    fm_end = -1
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if fm_start == -1:
                fm_start = i
            else:
                fm_end = i
                break
    if fm_start != -1 and fm_end != -1:
        cleaned_lines = []
        for i, line in enumerate(lines):
            if fm_start < i < fm_end:
                parts = line.split(":", 1)
                if parts and parts[0].strip() in ("version", "timestamp"):
                    continue
            cleaned_lines.append(line)
        res = "".join(cleaned_lines)
        if has_bom:
            return "\ufeff" + res
        return res
    if has_bom:
        return "\ufeff" + text
    return text

def verify_invariants(orig_text, prop_text, changed_block_ids):
    S_orig = parse_file_blocks(orig_text, raw=True)
    S_prop_raw = parse_file_blocks(prop_text, raw=True)
    
    orig_block_ids = {s["id"] for s in S_orig if s["type"] == "block"}
    for s in S_prop_raw:
        if s["type"] == "block" and s["id"] not in orig_block_ids:
            if s["id"] not in changed_block_ids:
                raise ValueError(f"New block '{s['id']}' was added but not in changed_block_ids")
            start_re = re.compile(r'^<!--\s*SOS:BLOCK\s+id=' + re.escape(s["id"]) + r'(?:\s+v=[^\s>]+)?\s*-->$')
            end_re = re.compile(r'^<!--\s*SOS:/BLOCK\s+id=' + re.escape(s["id"]) + r'\s*-->$')
            p_lines = s["raw_block"].strip().split("\n")
            if len(p_lines) < 2:
                raise ValueError(f"New block '{s['id']}' proposed raw block is too short")
            p_start_line = p_lines[0].strip()
            p_end_line = p_lines[-1].strip()
            if not start_re.match(p_start_line):
                raise ValueError(f"New block '{s['id']}' proposed start marker is malformed: '{p_start_line}'")
            if not end_re.match(p_end_line):
                raise ValueError(f"New block '{s['id']}' proposed end marker is malformed: '{p_end_line}'")
                
    S_prop = [s for s in S_prop_raw if not (s["type"] == "block" and s["id"] not in orig_block_ids)]
    
    if len(S_orig) != len(S_prop):
        raise ValueError("Structure mismatch: different number of segments (excluding new blocks)")
        
    for i in range(len(S_orig)):
        o = S_orig[i]
        p = S_prop[i]
        
        if o["type"] != p["type"]:
            raise ValueError(f"Structure mismatch at segment {i}: type changed from {o['type']} to {p['type']}")
            
        if o["type"] == "text":
            o_clean = clean_for_raw_compare(o["content"])
            p_clean = clean_for_raw_compare(p["content"])
            if o_clean != p_clean:
                raise ValueError(f"Raw out-of-block content changed in text segment {i}")
        else:
            if o["id"] != p["id"]:
                raise ValueError(f"Structure mismatch: block ID changed from '{o['id']}' to '{p['id']}'")
                
            if o["id"] not in changed_block_ids:
                if o["raw_block"] != p["raw_block"]:
                    raise ValueError(f"Block '{o['id']}' was modified but not marked as changed")
            else:
                start_re = re.compile(r'^<!--\s*SOS:BLOCK\s+id=' + re.escape(o["id"]) + r'(?:\s+v=[^\s>]+)?\s*-->$')
                end_re = re.compile(r'^<!--\s*SOS:/BLOCK\s+id=' + re.escape(o["id"]) + r'\s*-->$')
                
                p_lines = p["raw_block"].strip().split("\n")
                if len(p_lines) < 2:
                    raise ValueError(f"Block '{o['id']}' proposed raw block is too short")
                p_start_line = p_lines[0].strip()
                p_end_line = p_lines[-1].strip()
                
                if not start_re.match(p_start_line):
                    raise ValueError(f"Block '{o['id']}' proposed start marker is malformed: '{p_start_line}'")
                if not end_re.match(p_end_line):
                    raise ValueError(f"Block '{o['id']}' proposed end marker is malformed: '{p_end_line}'")

def check_cheap_corroborations(file_path: Path, orig_text, prop_text):
    name = file_path.name
    if name == "BACKLOG_MAP.md":
        bt_pattern = re.compile(r'\b(BT-\d{3,})\b')
        orig_bts = set(bt_pattern.findall(orig_text))
        prop_bts = set(bt_pattern.findall(prop_text))
        if orig_bts != prop_bts:
            raise ValueError(f"BT-id set changed. Original: {orig_bts}, Proposed: {prop_bts}")
            
        def get_backlog_rows(text):
            lines = text.split("\n")
            in_backlog = False
            rows = []
            for line in lines:
                if line.strip().startswith("## Backlog"):
                    in_backlog = True
                    continue
                if in_backlog and line.strip().startswith("##"):
                    in_backlog = False
                if in_backlog and line.strip().startswith("|") and "BT-" in line:
                    if "ID" not in line and ":---" not in line:
                        rows.append(line)
            return len(rows)
            
        if get_backlog_rows(orig_text) != get_backlog_rows(prop_text):
            raise ValueError(f"Backlog row count changed. Original: {get_backlog_rows(orig_text)}, Proposed: {get_backlog_rows(prop_text)}")
            
    elif name == "DESIGN_RULES.md":
        dr_pattern = re.compile(r'\[\[(DR-\w+)\]\]')
        def get_immortal_drs(text):
            lines = text.split("\n")
            in_immortal = False
            drs = set()
            for line in lines:
                if line.strip().startswith("## 3. Immortal Components"):
                    in_immortal = True
                    continue
                if in_immortal and line.strip().startswith("##"):
                    in_immortal = False
                if in_immortal:
                    drs.update(dr_pattern.findall(line))
            return drs
            
        if get_immortal_drs(orig_text) != get_immortal_drs(prop_text):
            raise ValueError(f"Immortal Components DR-id set changed. Original: {get_immortal_drs(orig_text)}, Proposed: {get_immortal_drs(prop_text)}")

def detect_and_apply_newline(text, original_text):
    has_bom = original_text.startswith("\ufeff")
    crlf_count = original_text.count("\r\n")
    lf_count = original_text.count("\n") - crlf_count
    is_crlf = crlf_count > lf_count
    normalized = text
    if normalized.startswith("\ufeff"):
        normalized = normalized[1:]
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    if is_crlf:
        normalized = normalized.replace("\n", "\r\n")
    if has_bom:
        return "\ufeff" + normalized
    return normalized

def normalize_proposed_bytes(prop_bytes, existing_path):
    if not existing_path.exists():
        return prop_bytes
    try:
        user_text = existing_path.read_bytes().decode("utf-8")
        prop_text = prop_bytes.decode("utf-8")
        normalized_prop_text = detect_and_apply_newline(prop_text, user_text)
        return normalized_prop_text.encode("utf-8")
    except Exception:
        return prop_bytes



PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
try:
    import _versioning
except ImportError:
    _versioning = None



ASSETS = PLUGIN_ROOT / "assets" / "templates"
# Lifecycle workflows live in workflows/ (Antigravity build) or commands/ (Claude build)
WF_SRC = PLUGIN_ROOT / "workflows" if (PLUGIN_ROOT / "workflows").exists() else PLUGIN_ROOT / "commands"

LIFECYCLE_RE = re.compile(r"^[0-4].*\.md$")  # 0a..4b
EXTRA_WORKFLOWS = {"sync-skills.md"}          # also copy this utility workflow

GITIGNORE_ENTRIES = [".tmp/", "node_modules/", ".DS_Store", "Thumbs.db",
                     "*.log", ".env", ".env.*", "token.json",
                     ".agents/skills/", "!.agents/skills/.lock.json",
                     "*.work.md", "*.stratosphere-new"]

FRAMEWORK_GITHUB_FILES = {"sync-labels-to-project.yml"}

def map_bundled_to_project(rel_path: str):
    parts = rel_path.split("/")
    if parts[0] == "assets" and parts[1] == "templates":
        sub = parts[2]
        name = parts[3]
        if sub == "constitution": return name
        elif sub == "memory": return f".memory/{name}"
        elif sub == "rules": return f".agents/rules/{name}"
        elif sub == "references": return f".agents/workflows/.reference/{name}"
        elif sub == "github": return f".github/workflows/{name}"
    elif parts[0] in ("workflows", "commands") and (re.match(r"^[0-4].*\.md$", parts[-1]) or parts[-1] == "sync-skills.md"):
        return f".agents/workflows/{parts[-1]}"
    return None

def reconcile_gitignore(project_dir, dry_run):
    gi = project_dir / ".gitignore"
    if not gi.exists():
        if dry_run:
            new_p = project_dir / ".gitignore.stratosphere-new"
            new_p.write_text("\n".join(GITIGNORE_ENTRIES) + "\n", encoding="utf-8")
            return GITIGNORE_ENTRIES
        gi.write_text("\n".join(GITIGNORE_ENTRIES) + "\n", encoding="utf-8")
        return GITIGNORE_ENTRIES
        
    content = gi.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]
    missing = [entry for entry in GITIGNORE_ENTRIES if entry.strip() not in lines]
    
    if missing:
        new_content = content
        if new_content and not new_content.endswith("\n"):
            new_content += "\n"
        new_content += "\n".join(missing) + "\n"
        if dry_run:
            new_p = project_dir / (gi.name + ".stratosphere-new")
            new_p.write_text(new_content, encoding="utf-8")
        else:
            gi.write_text(new_content, encoding="utf-8")
    return missing

def reconcile_gitattributes(project_dir, dry_run):
    ga = project_dir / ".gitattributes"
    required_lines = ["docs/okf-view.html linguist-generated=true -diff"]
    if not ga.exists():
        if dry_run:
            new_p = project_dir / ".gitattributes.stratosphere-new"
            new_p.write_text("\n".join(required_lines) + "\n", encoding="utf-8")
            return required_lines
        ga.write_text("\n".join(required_lines) + "\n", encoding="utf-8")
        return required_lines
        
    content = ga.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]
    missing = [entry for entry in required_lines if entry.strip() not in lines]
    
    if missing:
        new_content = content
        if new_content and not new_content.endswith("\n"):
            new_content += "\n"
        new_content += "\n".join(missing) + "\n"
        if dry_run:
            new_p = project_dir / (ga.name + ".stratosphere-new")
            new_p.write_text(new_content, encoding="utf-8")
        else:
            ga.write_text(new_content, encoding="utf-8")
    return missing

FOLDERS = [
    ".memory",
    ".agents/rules",
    ".agents/workflows",
    ".agents/workflows/.reference",
    ".agents/scripts",
    "docs/discovery",
    "docs/prds",
    "docs/research",
    "docs/design",
    "docs/knowledge",
    ".tmp",
]
KEEP_EMPTY = {"docs/discovery", "docs/prds", "docs/research", "docs/design", "docs/knowledge", ".tmp"}  # add .gitkeep so they survive git


def place(src: Path, dst: Path, res, dry, update: bool = False, tier: str = "preserved"):
    """Copy src->dst with tier-based update logic; record outcome."""
    rel = dst
    if dst.exists():
        if tier == "preserved":
            res["exists"].append(rel)
            return

        src_bytes = src.read_bytes()
        dst_bytes = dst.read_bytes()
        if src_bytes == dst_bytes:
            res["unchanged"].append(rel)
            return

        if tier == "managed":
            if update:
                if not dry:
                    shutil.copy2(src, dst)
                res["refreshed"].append(rel)
            else:
                res["stale"].append(rel)
        elif tier == "constitution":
            res["needs_review"].append(rel)
        return

    if dry:
        res["would"].append(rel)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    res["created"].append(rel)


def main():
    plugin_root = Path(__file__).resolve().parent.parent
    plugin_root_resolved = plugin_root.resolve()
    home = Path.home().resolve()
    cwd = Path.cwd().resolve()

    claude_cache = (home / ".claude" / "plugins" / "cache").resolve()
    if plugin_root_resolved == (home / ".claude" / "plugins" / "stratosphere-os").resolve():
        scope = "global Claude Code"
    elif plugin_root_resolved.is_relative_to(claude_cache):
        scope = "marketplace Claude Code"
    elif plugin_root_resolved == (cwd / ".claude" / "plugins" / "stratosphere-os").resolve():
        scope = "local Claude Code"
    elif plugin_root_resolved == (home / ".gemini" / "config" / "plugins" / "stratosphere-os").resolve():
        scope = "global Antigravity"
    elif plugin_root_resolved == (cwd / ".agents" / "plugins" / "stratosphere-os").resolve():
        scope = "local Antigravity"
    else:
        scope = "(custom path)"
    print(f"Resolved plugin root: {plugin_root_resolved} ({scope})")

    ap = argparse.ArgumentParser(description="Scaffold a StratosphereOS project (deterministic).")
    ap.add_argument("--dry-run", action="store_true", help="report what would happen without writing")
    ap.add_argument("--repair-lock", action="store_true", help="regenerate .stratosphere-lock.json from the current workspace")
    ap.add_argument("--update", action="store_true", help="refresh managed framework files in place")
    ap.add_argument("--verify", action="store_true", help="run invariants verification on proposed updates")
    args = ap.parse_args()

    project = Path.cwd()
    dry = args.dry_run or args.verify
    update = args.update or args.verify
    res = {
        "created": [], "would": [], "exists": [],
        "refreshed": [], "unchanged": [], "stale": [], "needs_review": []
    }

    if not ASSETS.exists():
        raise SystemExit(f"Cannot find bundled templates at {ASSETS}. Run from a project root with the plugin installed.")

    def generate_lockfile(dry_run, repair=False):
        if not _versioning: return False
        lock_file = project / ".agents" / ".stratosphere-lock.json"
        
        # Load existing lockfile if not repairing
        if not repair and lock_file.exists():
            try:
                lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
            except Exception:
                lock_data = {"installed_plugin_version": "unknown", "artifacts": {}}
        else:
            lock_data = {"installed_plugin_version": "unknown", "artifacts": {}}

        try:
            versions = json.loads((PLUGIN_ROOT / "versions.json").read_text(encoding="utf-8"))
            if repair or lock_data.get("installed_plugin_version") == "unknown":
                lock_data["installed_plugin_version"] = versions.get("plugin_version", "unknown")
            bundled_manifest = versions.get("artifacts", {})
        except Exception:
            bundled_manifest = {}
            
        count = 0
        for rel_path, b_meta in bundled_manifest.items():
            proj_path = map_bundled_to_project(rel_path)
            if not proj_path: continue
            if proj_path.startswith(".github/workflows/"):
                continue
            
            p = project / proj_path
            if repair:
                # In repair mode, we trust the workspace file and compute its current hash as the new baseline
                if p.exists():
                    text = p.read_bytes().decode("utf-8")
                    v = get_marker_version(text, "unknown")
                    lock_entry = {
                        "version": v,
                        "sha256_at_install": _versioning.body_hash(text)
                    }
                    blocks = get_blocks_map(text)
                    if blocks:
                        lock_entry["blocks"] = blocks
                    lock_data["artifacts"][proj_path] = lock_entry
                    count += 1
            else:
                # Normal mode: pull baseline hash from the bundled manifest, but ONLY if missing from lockfile
                if proj_path not in lock_data.get("artifacts", {}) and p.exists():
                    text = p.read_bytes().decode("utf-8")
                    v = get_marker_version(text, "unknown")
                    lock_entry = {
                        "version": v,
                        "sha256_at_install": _versioning.body_hash(text)
                    }
                    blocks = get_blocks_map(text)
                    if blocks:
                        lock_entry["blocks"] = blocks
                    lock_data.setdefault("artifacts", {})[proj_path] = lock_entry
                    count += 1
        
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        if not dry_run and count > 0:
            lock_file.write_text(json.dumps(lock_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return count

    if args.repair_lock:
        if not _versioning:
            raise SystemExit("Error: _versioning module not found. Cannot repair lock.")
        count = generate_lockfile(dry, repair=True)
        if not dry:
            print(f"Repaired .stratosphere-lock.json with {count} artifacts.")
        else:
            print(f"WOULD REPAIR .stratosphere-lock.json with {count} artifacts.")
        return

    if update:
        # Load versions.json
        versions_file = PLUGIN_ROOT / "versions.json"
        if not versions_file.exists():
            raise SystemExit(f"Missing versions.json in {PLUGIN_ROOT}")
        versions_data = json.loads(versions_file.read_text(encoding="utf-8"))
        bundled_manifest = versions_data.get("artifacts", {})
        plugin_version = versions_data.get("plugin_version", "unknown")
        
        # Load lockfile
        lock_file = project / ".agents" / ".stratosphere-lock.json"
        if lock_file.exists():
            try:
                lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
            except Exception:
                lock_data = {"installed_plugin_version": "unknown", "artifacts": {}}
        else:
            lock_data = {"installed_plugin_version": "unknown", "artifacts": {}}
            
        worklist = {
            "plugin_version": plugin_version,
            "stale_managed": [],
            "needs_review_constitution": [],
            "preserved_files": {}
        }
        
        proposed_files = {}  # proj_path -> proposed_bytes
        changed_blocks_per_file = {}  # proj_path -> set of block_ids
        
        for rel_path, b_meta in bundled_manifest.items():
            proj_path = map_bundled_to_project(rel_path)
            if not proj_path:
                continue
                
            p = project / proj_path

            # Framework GitHub Actions are opt-in: manage a bundled workflow only if it is
            # both allowlisted AND already present in the project. Skip anything else.
            if proj_path.startswith(".github/workflows/"):
                if Path(proj_path).name not in FRAMEWORK_GITHUB_FILES or not p.exists():
                    continue
            tier = "managed"
            if proj_path.startswith(".memory/"):
                tier = "preserved"
            elif proj_path in ("AGENT.md", "CLAUDE.md", "GEMINI.md"):
                tier = "constitution"
                
            new_p = p.parent / (p.name + ".stratosphere-new")
            has_new_file = new_p.exists()
            
            b_file = PLUGIN_ROOT / rel_path
            if not b_file.exists():
                continue
            bundled_bytes = b_file.read_bytes()
            
            if tier == "managed":
                is_stale = False
                if not p.exists():
                    is_stale = True
                else:
                    is_stale = (p.read_bytes() != bundled_bytes)
                    
                if is_stale:
                    worklist["stale_managed"].append(proj_path)
                    if has_new_file:
                        proposed_files[proj_path] = normalize_proposed_bytes(new_p.read_bytes(), p)
                    else:
                        proposed_files[proj_path] = normalize_proposed_bytes(bundled_bytes, p)
                        
            elif tier == "constitution":
                is_stale = False
                if not p.exists():
                    is_stale = True
                else:
                    is_stale = (p.read_bytes() != bundled_bytes)
                    
                if is_stale:
                    worklist["needs_review_constitution"].append(proj_path)
                    if has_new_file:
                        proposed_files[proj_path] = normalize_proposed_bytes(new_p.read_bytes(), p)
                        
            elif tier == "preserved":
                b_version = b_meta.get("version", "0.0.0")
                lock_entry = lock_data.get("artifacts", {}).get(proj_path, {})
                locked_version = lock_entry.get("version")
                
                bundled_text = bundled_bytes.decode("utf-8")
                bundled_block_hashes = get_blocks_map(bundled_text)
                
                is_stale = False
                if not p.exists():
                    is_stale = True
                elif not locked_version:
                    is_stale = True
                else:
                    locked_blocks = lock_entry.get("blocks", {})
                    is_stale = (
                        (semver_key(b_version) > semver_key(locked_version))
                        or (
                            (semver_key(b_version) == semver_key(locked_version))
                            and (
                                (set(locked_blocks) != set(bundled_block_hashes))
                                or any(locked_blocks.get(bid) != h for bid, h in bundled_block_hashes.items())
                            )
                        )
                    )
                
                if is_stale:
                    file_info = {
                        "status": "stale",
                        "old_version": locked_version or "none",
                        "new_version": b_version,
                        "blocks": {},
                        "template_blocks": bundled_block_hashes
                    }
                    
                    if not p.exists():
                        proposed_files[proj_path] = bundled_bytes
                        changed_blocks_per_file[proj_path] = set()
                        worklist["preserved_files"][proj_path] = file_info
                        continue
                        
                    user_text = p.read_bytes().decode("utf-8")
                    has_markers = "SOS:BLOCK" in user_text
                    
                    if not has_markers:
                        file_info["status"] = "unmarked"
                        worklist["preserved_files"][proj_path] = file_info
                        print(f"Notice: Unmarked framework file '{proj_path}' — run 'python scripts/migrations/inject_markers.py' to enable in-place updates.")
                        continue
                        
                    if has_new_file:
                        prop_text = new_p.read_bytes().decode("utf-8")
                        prop_text = detect_and_apply_newline(prop_text, user_text)
                        proposed_files[proj_path] = prop_text.encode("utf-8")
                        try:
                            user_segs = parse_file_blocks(user_text)
                            prop_segs = parse_file_blocks(prop_text)
                            changed = set()
                            for u_seg in user_segs:
                                if u_seg["type"] == "block":
                                    p_seg = next((s for s in prop_segs if s["type"] == "block" and s["id"] == u_seg["id"]), None)
                                    if p_seg and _versioning.normalize(u_seg["content"]) != _versioning.normalize(p_seg["content"]):
                                        changed.add(u_seg["id"])
                            user_block_ids = {s["id"] for s in user_segs if s["type"] == "block"}
                            for p_seg in prop_segs:
                                if p_seg["type"] == "block" and p_seg["id"] not in user_block_ids:
                                    changed.add(p_seg["id"])
                            changed_blocks_per_file[proj_path] = changed
                        except Exception:
                            changed_blocks_per_file[proj_path] = set()
                        file_info["status"] = "merged"
                        worklist["preserved_files"][proj_path] = file_info
                        continue
                        
                    try:
                        user_segments = parse_file_blocks(user_text)
                        bundled_text = b_file.read_bytes().decode("utf-8")
                        template_segments = parse_file_blocks(bundled_text)
                    except Exception as e:
                        file_info["status"] = f"malformed: {e}"
                        worklist["preserved_files"][proj_path] = file_info
                        print(f"Warning: skipped '{proj_path}' due to malformed block markers: {e}")
                        continue
                        
                    blocks_changed = []
                    conflicts = []
                    
                    user_block_ids = {s["id"] for s in user_segments if s["type"] == "block"}
                    for seg in template_segments:
                        if seg["type"] != "block":
                            continue
                        bid = seg["id"]
                        if bid not in user_block_ids:
                            blocks_changed.append(bid)
                            file_info["blocks"][bid] = {
                                "status": "pristine",
                                "old_hash": None,
                                "new_hash": _versioning.block_hash(bundled_text, bid)
                            }
                    
                    for seg in user_segments:
                        if seg["type"] != "block":
                            continue
                        bid = seg["id"]
                        
                        try:
                            H_user = _versioning.block_hash(user_text, bid)
                            H_new = _versioning.block_hash(bundled_text, bid)
                        except Exception as e:
                            conflicts.append(bid)
                            file_info["blocks"][bid] = {"status": "error", "message": str(e)}
                            continue
                            
                        H_base = lock_entry.get("blocks", {}).get(bid)
                        
                        is_inconsistent = False
                        if not H_base:
                            whole_file_matches = False
                            if "sha256_at_install" in lock_entry:
                                try:
                                    current_hash = _versioning.body_hash(p.read_bytes().decode("utf-8"))
                                    if current_hash == lock_entry["sha256_at_install"]:
                                        whole_file_matches = True
                                except Exception:
                                    pass
                            if whole_file_matches:
                                H_base = H_user
                            else:
                                is_inconsistent = True
                                
                        if is_inconsistent:
                            if H_user == H_new:
                                file_info["blocks"][bid] = {"status": "already_at_target", "old_hash": H_user, "new_hash": H_new}
                            else:
                                conflicts.append(bid)
                                file_info["blocks"][bid] = {"status": "conflict", "old_hash": H_user, "new_hash": H_new}
                        else:
                            if H_user == H_new:
                                file_info["blocks"][bid] = {"status": "already_at_target", "old_hash": H_user, "new_hash": H_new}
                            elif H_user == H_base and H_new != H_base:
                                blocks_changed.append(bid)
                                file_info["blocks"][bid] = {"status": "pristine", "old_hash": H_user, "new_hash": H_new}
                            elif H_user != H_base and H_new == H_base:
                                file_info["blocks"][bid] = {"status": "unchanged", "old_hash": H_user, "new_hash": H_new}
                            elif H_user != H_base and H_new != H_base and H_user != H_new:
                                conflicts.append(bid)
                                file_info["blocks"][bid] = {"status": "conflict", "old_hash": H_user, "new_hash": H_new}
                                
                    if conflicts:
                        file_info["status"] = "conflict"
                        worklist["preserved_files"][proj_path] = file_info
                        continue
                        
                    proposed_segments = list(user_segments)
                    current_block_ids = set(user_block_ids)
                    
                    for seg in template_segments:
                        if seg["type"] == "block" and seg["id"] not in user_block_ids:
                            bid = seg["id"]
                            t_idx = template_segments.index(seg)
                            inserted = False
                            
                            for j in range(t_idx - 1, -1, -1):
                                prev_seg = template_segments[j]
                                if prev_seg["type"] == "block" and prev_seg["id"] in current_block_ids:
                                    for idx, p_seg in enumerate(proposed_segments):
                                        if p_seg["type"] == "block" and p_seg["id"] == prev_seg["id"]:
                                            new_raw = f'<!-- SOS:BLOCK id={bid} v={b_version} -->\n{seg["content"]}\n<!-- SOS:/BLOCK id={bid} -->'
                                            proposed_segments.insert(idx + 1, {
                                                "type": "block",
                                                "id": bid,
                                                "version": b_version,
                                                "content": seg["content"],
                                                "raw_block": new_raw
                                            })
                                            current_block_ids.add(bid)
                                            inserted = True
                                            break
                                    if inserted:
                                        break
                                        
                            if not inserted:
                                for j in range(t_idx + 1, len(template_segments)):
                                    next_seg = template_segments[j]
                                    if next_seg["type"] == "block" and next_seg["id"] in current_block_ids:
                                        for idx, p_seg in enumerate(proposed_segments):
                                            if p_seg["type"] == "block" and p_seg["id"] == next_seg["id"]:
                                                new_raw = f'<!-- SOS:BLOCK id={bid} v={b_version} -->\n{seg["content"]}\n<!-- SOS:/BLOCK id={bid} -->'
                                                proposed_segments.insert(idx, {
                                                    "type": "block",
                                                    "id": bid,
                                                    "version": b_version,
                                                    "content": seg["content"],
                                                    "raw_block": new_raw
                                                })
                                                current_block_ids.add(bid)
                                                inserted = True
                                                break
                                        if inserted:
                                            break
                                            
                            if not inserted:
                                new_raw = f'<!-- SOS:BLOCK id={bid} v={b_version} -->\n{seg["content"]}\n<!-- SOS:/BLOCK id={bid} -->'
                                proposed_segments.append({
                                    "type": "block",
                                    "id": bid,
                                    "version": b_version,
                                    "content": seg["content"],
                                    "raw_block": new_raw
                                })
                                current_block_ids.add(bid)
                                
                    for idx, seg in enumerate(proposed_segments):
                        if seg["type"] == "block" and seg["id"] in user_block_ids and seg["id"] in blocks_changed:
                            new_seg = next(s for s in template_segments if s["type"] == "block" and s["id"] == seg["id"])
                            new_raw = f'<!-- SOS:BLOCK id={seg["id"]} v={b_version} -->\n{new_seg["content"]}\n<!-- SOS:/BLOCK id={seg["id"]} -->'
                            proposed_segments[idx] = {
                                "type": "block",
                                "id": seg["id"],
                                "version": b_version,
                                "content": new_seg["content"],
                                "raw_block": new_raw
                            }
                            
                    parts = []
                    for seg in proposed_segments:
                        if seg["type"] == "text":
                            parts.append(seg["content"])
                        else:
                            parts.append(seg["raw_block"])
                    proposed_text = "".join(parts)
                    proposed_text = detect_and_apply_newline(proposed_text, user_text)
                    
                    proposed_files[proj_path] = proposed_text.encode("utf-8")
                    changed_blocks_per_file[proj_path] = set(blocks_changed)
                    
                    file_info["status"] = "staged"
                    worklist["preserved_files"][proj_path] = file_info
                    
        tmp_dir = project / ".tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        worklist_file = tmp_dir / "stratosphere-update-worklist.json"
        worklist_file.write_text(json.dumps(worklist, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        
        verification_failed = False
        failures = []
        
        for proj_path, prop_bytes in proposed_files.items():
            p = project / proj_path
            if not p.exists():
                continue
            orig_text = p.read_bytes().decode("utf-8")
            prop_text = prop_bytes.decode("utf-8")
            
            if proj_path.startswith(".memory/"):
                changed_blocks = changed_blocks_per_file.get(proj_path, set())
                try:
                    verify_invariants(orig_text, prop_text, changed_blocks)
                    check_cheap_corroborations(p, orig_text, prop_text)
                except Exception as e:
                    failures.append(f"Validation failed for '{proj_path}': {e}")
                    verification_failed = True
                    
        if verification_failed:
            print("=== Invariant Verification Failed ===")
            for f in failures:
                print(f"  * {f}")
            raise SystemExit("Error: Update verification failed. No changes were written.")
            
        if dry:
            for proj_path, prop_bytes in proposed_files.items():
                p = project / proj_path
                new_p = p.parent / (p.name + ".stratosphere-new")
                new_p.parent.mkdir(parents=True, exist_ok=True)
                new_p.write_bytes(prop_bytes)
                print(f"STAGED: {proj_path}.stratosphere-new")
            print("Summary: All updates verified and written to *.stratosphere-new files (dry-run).")
            return
            
        unresolved = []
        for proj_path, info in worklist["preserved_files"].items():
            if info["status"] == "conflict" and proj_path not in proposed_files:
                unresolved.append(proj_path)
        for proj_path in worklist["needs_review_constitution"]:
            if proj_path not in proposed_files:
                unresolved.append(proj_path)
                
        if unresolved:
            print("=== Unresolved Conflicts / Reviews ===")
            for u in unresolved:
                print(f"  * {u} needs merge/review")
            raise SystemExit("Error: Cannot commit because there are unresolved conflicts or constitution changes.")
            
        for proj_path, prop_bytes in proposed_files.items():
            p = project / proj_path
            if p.exists() and p.read_bytes() == prop_bytes:
                new_p = p.parent / (p.name + ".stratosphere-new")
                if new_p.exists():
                    new_p.unlink()
                continue
                
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(prop_bytes)
            
            new_p = p.parent / (p.name + ".stratosphere-new")
            if new_p.exists():
                new_p.unlink()
                
            print(f"UPDATED: {proj_path}")
            
        for proj_path, info in worklist["preserved_files"].items():
            if proj_path not in proposed_files:
                continue
            p = project / proj_path
            if p.exists():
                text = p.read_bytes().decode("utf-8")
                lock_entry = {
                    "version": info["new_version"],
                    "sha256_at_install": _versioning.body_hash(text)
                }
                template_blocks = info.get("template_blocks")
                if template_blocks is not None:
                    lock_entry["blocks"] = template_blocks
                else:
                    blocks = get_blocks_map(text)
                    if blocks:
                        lock_entry["blocks"] = blocks
                lock_data["artifacts"][proj_path] = lock_entry
                
        for proj_path in worklist["stale_managed"] + worklist["needs_review_constitution"]:
            if proj_path not in proposed_files:
                continue
            if proj_path.startswith(".github/workflows/"):
                continue
            p = project / proj_path
            if p.exists():
                text = p.read_bytes().decode("utf-8")
                lock_data["artifacts"][proj_path] = {
                    "version": plugin_version,
                    "sha256_at_install": _versioning.body_hash(text)
                }
                
        # Reconcile gitignore and gitattributes
        gi_added = reconcile_gitignore(project, dry)
        ga_added = reconcile_gitattributes(project, dry)
        
        # Clean up stratosphere-new files if not dry
        if not dry:
            for name in (".gitignore", ".gitattributes"):
                new_p = project / (name + ".stratosphere-new")
                if new_p.exists():
                    new_p.unlink()
        
        if gi_added:
            verb = "WOULD RECONCILE" if dry else "RECONCILED"
            print(f"{verb} .gitignore: added {', '.join(gi_added)}")
        if ga_added:
            verb = "WOULD RECONCILE" if dry else "RECONCILED"
            print(f"{verb} .gitattributes: added {', '.join(ga_added)}")
                
        lock_data["installed_plugin_version"] = plugin_version
        lock_file.write_text(json.dumps(lock_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("Updated .stratosphere-lock.json successfully.")
        return

    # 1. Folders
    for f in FOLDERS:
        d = project / f
        if d.exists():
            res["exists"].append(Path(f) / "")
        elif not dry:
            d.mkdir(parents=True, exist_ok=True)
            res["created"].append(Path(f) / "")
            if f in KEEP_EMPTY:
                (d / ".gitkeep").write_text("", encoding="utf-8")
        else:
            res["would"].append(Path(f) / "")

    # 2. Constitution -> project root
    for name in ("AGENT.md", "CLAUDE.md", "GEMINI.md"):
        place(ASSETS / "constitution" / name, project / name, res, dry, update=update, tier="constitution")

    # 3. Memory templates -> .memory/
    for src in sorted((ASSETS / "memory").glob("*.md")):
        place(src, project / ".memory" / src.name, res, dry, update=update, tier="preserved")

    # 4. Rules -> .agents/rules/
    for src in sorted((ASSETS / "rules").glob("*.md")):
        place(src, project / ".agents" / "rules" / src.name, res, dry, update=update, tier="managed")

    # 5. Workflow references -> .agents/workflows/.reference/
    if (ASSETS / "references").exists():
        for src in sorted((ASSETS / "references").glob("*")):
            if src.is_file():
                place(src, project / ".agents" / "workflows" / ".reference" / src.name, res, dry, update=update, tier="managed")

    # 6. Lifecycle workflows -> .agents/workflows/ (discoverable on Antigravity)
    if WF_SRC.exists():
        for src in sorted(WF_SRC.glob("*.md")):
            if LIFECYCLE_RE.match(src.name) or src.name in EXTRA_WORKFLOWS:
                place(src, project / ".agents" / "workflows" / src.name, res, dry, update=update, tier="managed")

    # 6b. Project-local deterministic scripts (memory lint runs from the project)
    vm = PLUGIN_ROOT / "scripts" / "validate_memory.py"
    if vm.exists():
        place(vm, project / ".agents" / "scripts" / "validate_memory.py", res, dry, update=update, tier="managed")

    # 6c. Project-local design token scripts (design-theme, linter package.json)
    design_src_dir = PLUGIN_ROOT / "scripts" / "design"
    if design_src_dir.exists() and design_src_dir.is_dir():
        for src in sorted(design_src_dir.rglob("*")):
            if src.is_file():
                # Skip any path containing a 'test' segment
                if 'test' in src.parts:
                    continue
                rel_parts = src.relative_to(design_src_dir)
                dst = project / ".agents" / "scripts" / "design" / rel_parts
                place(src, dst, res, dry, update=update, tier="managed")

    # Copy OKF viewer files
    viewer_src_dir = PLUGIN_ROOT / "scripts" / "okf_viewer"
    if viewer_src_dir.exists() and viewer_src_dir.is_dir():
        for src in sorted(viewer_src_dir.rglob("*")):
            if src.is_file():
                rel_parts = src.relative_to(viewer_src_dir)
                dst = project / ".agents" / "scripts" / "okf_viewer" / rel_parts
                place(src, dst, res, dry, update=update, tier="managed")

    view_script = PLUGIN_ROOT / "scripts" / "okf_view.py"
    if view_script.exists():
        place(view_script, project / ".agents" / "scripts" / "okf_view.py", res, dry, update=update, tier="managed")

    # 8. .gitignore & .gitattributes Reconciliation
    gi_added = reconcile_gitignore(project, dry)
    ga_added = reconcile_gitattributes(project, dry)
    
    if gi_added:
        verb = "WOULD RECONCILE" if dry else "RECONCILED"
        print(f"{verb} .gitignore: added {', '.join(gi_added)}")
        if not dry:
            res["refreshed"].append(Path(".gitignore"))
    else:
        res["exists"].append(Path(".gitignore"))
        
    if ga_added:
        verb = "WOULD RECONCILE" if dry else "RECONCILED"
        print(f"{verb} .gitattributes: added {', '.join(ga_added)}")
        if not dry:
            res["refreshed"].append(Path(".gitattributes"))
    else:
        res["exists"].append(Path(".gitattributes"))

    # 8c. Update Lockfile
    count = generate_lockfile(dry, repair=False)
    if count and not dry:
        res["created"].append(Path(".agents/.stratosphere-lock.json"))


    # 9. Root index.md (create if missing; never edit an existing one)
    root_index = project / "index.md"
    if not root_index.exists():
        if dry:
            res["would"].append(Path("index.md"))
        else:
            root_index_content = (
                "---\n"
                "okf_version: \"0.1\"\n"
                "---\n\n"
                "# StratosphereOS Knowledge Bundle\n\n"
                "Conforms to Open Knowledge Format (OKF) v0.1.\n\n"
                "## Sections\n\n"
                "- [Memory](/.memory/index.md) - Internal memory registries.\n"
                "- [Product Requirement Documents](/docs/prds/index.md) - Feature specifications.\n"
                "- [Discovery Briefs](/docs/discovery/index.md) - Early problem exploration briefs.\n"
                "- [Research Docs](/docs/research/index.md) - Topic and competitive landscape research.\n"
                "- [Design Blueprints](/docs/design/index.md) - Surface and interface designs.\n"
                "- [Knowledge Sources](/docs/knowledge/index.md) - External ingested knowledge references.\n"
            )
            root_index.write_text(root_index_content, encoding="utf-8")
            res["created"].append(Path("index.md"))
    else:
        res["exists"].append(Path("index.md"))

    # 10. Seed empty index.md in subdirectories (create-only-if-missing)
    sub_indices = [
        (".memory", "Memory Index", "Registry of learnings, rules, status, and vocabulary."),
        ("docs/prds", "Product Requirement Documents", "Feature specifications."),
        ("docs/discovery", "Discovery Briefs", "Early problem framing and exploration briefs."),
        ("docs/research", "Research Documents", "Topic and competitive landscape research."),
        ("docs/design", "Design Blueprints", "Visual layouts and interface contracts."),
        ("docs/knowledge", "External Knowledge References", "Ingested external OKF bundles.")
    ]
    for rel_dir, title, desc in sub_indices:
        idx_file = project / rel_dir / "index.md"
        if not idx_file.exists():
            if dry:
                res["would"].append(Path(rel_dir) / "index.md")
            else:
                idx_content = f"# {title}\n\n{desc}\n\n*No entries yet.*\n"
                idx_file.write_text(idx_content, encoding="utf-8")
                res["created"].append(Path(rel_dir) / "index.md")
        else:
            res["exists"].append(Path(rel_dir) / "index.md")


    # Summary
    verb = "WOULD CREATE" if dry else "CREATED"
    created = res["would"] if dry else res["created"]
    print(f"=== StratosphereOS scaffold ({'dry-run' if dry else 'applied'}) ===")

    if created:
        print(f"{verb}: {len(created)}")
        for p in created:
            print(f"  + {p}")

    if res["refreshed"]:
        r_verb = "WOULD REFRESH" if dry else "REFRESHED"
        print(f"{r_verb}: {len(res['refreshed'])}")
        for p in res["refreshed"]:
            print(f"  ^ {p}")

    if res["unchanged"]:
        print(f"UNCHANGED: {len(res['unchanged'])}")
        for p in res["unchanged"]:
            print(f"  = {p}")

    if res["stale"]:
        print(f"STALE (run with --update to refresh): {len(res['stale'])}")
        for p in res["stale"]:
            print(f"  ~ {p}")

    if res["needs_review"]:
        print(f"NEEDS-REVIEW (constitution differs): {len(res['needs_review'])}")
        for p in res["needs_review"]:
            print(f"  ! {p}")

    if res["exists"]:
        print(f"LEFT AS-IS (already present, agent should drift-check): {len(res['exists'])}")
        for p in res["exists"]:
            print(f"  - {p}")



if __name__ == "__main__":
    main()
