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
import json
import re
import shutil
import sys
from pathlib import Path

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
    args = ap.parse_args()

    project = Path.cwd()
    dry = args.dry_run
    update = args.update
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
            
        def map_bundled_to_project(rel_path: str):
            parts = rel_path.split("/")
            if parts[0] == "assets" and parts[1] == "templates":
                sub = parts[2]
                name = parts[3]
                if sub == "constitution": return name
                elif sub == "memory": return f".memory/{name}"
                elif sub == "rules": return f".agents/rules/{name}"
                elif sub == "references": return f".agents/workflows/.reference/{name}"
            elif parts[0] in ("workflows", "commands") and (re.match(r"^[0-4].*\.md$", parts[-1]) or parts[-1] == "sync-skills.md"):
                return f".agents/workflows/{parts[-1]}"
            return None
            
        count = 0
        for rel_path, b_meta in bundled_manifest.items():
            proj_path = map_bundled_to_project(rel_path)
            if not proj_path: continue
            
            p = project / proj_path
            if repair:
                # In repair mode, we trust the workspace file and compute its current hash as the new baseline
                if p.exists():
                    text = p.read_text(encoding="utf-8")
                    v, ts = _versioning.read_version(text, p)
                    if v:
                        lock_data["artifacts"][proj_path] = {
                            "version": v,
                            "sha256_at_install": _versioning.body_hash(text)
                        }
                        count += 1
                    else:
                        print(f"Warning: skipped '{proj_path}' during lock repair (missing version stamp).")
            else:
                # Normal mode: pull baseline hash from the bundled manifest, but ONLY if missing from lockfile
                if proj_path not in lock_data.get("artifacts", {}) and p.exists():
                    lock_data.setdefault("artifacts", {})[proj_path] = {
                        "version": b_meta.get("version", "unknown"),
                        "sha256_at_install": b_meta.get("sha256", "unknown")
                    }
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
                place(src, dst, res, dry)

    view_script = PLUGIN_ROOT / "scripts" / "okf_view.py"
    if view_script.exists():
        place(view_script, project / ".agents" / "scripts" / "okf_view.py", res, dry)

    # 8. .gitignore (create if missing; never edit an existing one)
    gi = project / ".gitignore"
    gi_existed = gi.exists()
    if not gi_existed:
        if dry:
            res["would"].append(Path(".gitignore"))
        else:
            gi.write_text("\n".join(GITIGNORE_ENTRIES) + "\n", encoding="utf-8")
            res["created"].append(Path(".gitignore"))

    # 8b. .gitattributes (create if missing; never edit an existing one)
    ga = project / ".gitattributes"
    ga_existed = ga.exists()
    if not ga_existed:
        if dry:
            res["would"].append(Path(".gitattributes"))
        else:
            ga_content = "docs/okf-view.html linguist-generated=true -diff\n"
            ga.write_text(ga_content, encoding="utf-8")
            res["created"].append(Path(".gitattributes"))
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
    if gi_existed:
        # existing .gitignore: remind agent to verify secret-hygiene entries
        print("NOTE: .gitignore already exists — verify it contains: " + ", ".join(GITIGNORE_ENTRIES))
        print("NOTE: Existing projects must manually add *.work.md to their .gitignore (scaffold never edits existing ones).")
    if ga_existed:
        print("NOTE: .gitattributes already exists — verify it contains: docs/okf-view.html linguist-generated=true -diff")


if __name__ == "__main__":
    main()
