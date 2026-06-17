#!/usr/bin/env python3
"""Deterministic StratosphereOS project scaffolder — zero LLM tokens.

Creates the project's folder structure and copies bundled templates into place,
**create-only-if-missing** (never overwrites). The agent's instantiate command
calls this for all mechanical work and keeps only the reasoning steps
(brownfield audits, label reconciliation, skill selection).

The script lives in the installed plugin at `<plugin>/scripts/scaffold.py`.
Run it FROM THE PROJECT ROOT (cwd = project), e.g.:

  python <plugin>/scripts/scaffold.py
  python <plugin>/scripts/scaffold.py --dry-run

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
import subprocess
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
    ".tmp",
]
KEEP_EMPTY = {"docs/discovery", "docs/prds", "docs/research", "docs/design", ".tmp"}  # add .gitkeep so they survive git


def place(src: Path, dst: Path, res, dry):
    """Copy src->dst create-only-if-missing; record outcome."""
    rel = dst
    if dst.exists():
        res["exists"].append(rel)
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
    args = ap.parse_args()

    project = Path.cwd()
    dry = args.dry_run
    res = {"created": [], "exists": [], "would": []}

    if not ASSETS.exists():
        raise SystemExit(f"Cannot find bundled templates at {ASSETS}. Run from a project root with the plugin installed.")

    def generate_lockfile(dry_run):
        if not _versioning: return False
        lock_file = project / ".agents" / ".stratosphere-lock.json"
        lock_data = {"installed_plugin_version": "unknown", "artifacts": {}}
        try:
            versions = json.loads((PLUGIN_ROOT / "versions.json").read_text(encoding="utf-8"))
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
        for rel_path in bundled_manifest:
            proj_path = map_bundled_to_project(rel_path)
            if not proj_path: continue
            
            p = project / proj_path
            if p.exists():
                text = p.read_text(encoding="utf-8")
                v, u, form = _versioning.read_version(text, p)
                if v and form:
                    lock_data["artifacts"][proj_path] = {
                        "version": v,
                        "sha256_at_install": _versioning.body_hash(text, form)
                    }
                    count += 1
        
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        if not dry_run:
            lock_file.write_text(json.dumps(lock_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return count

    if args.repair_lock:
        if not _versioning:
            raise SystemExit("Error: _versioning module not found. Cannot repair lock.")
        count = generate_lockfile(dry)
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
        place(ASSETS / "constitution" / name, project / name, res, dry)

    # 3. Memory templates -> .memory/
    for src in sorted((ASSETS / "memory").glob("*.md")):
        place(src, project / ".memory" / src.name, res, dry)

    # 4. Rules -> .agents/rules/
    for src in sorted((ASSETS / "rules").glob("*.md")):
        place(src, project / ".agents" / "rules" / src.name, res, dry)

    # 5. Workflow references -> .agents/workflows/.reference/
    if (ASSETS / "references").exists():
        for src in sorted((ASSETS / "references").glob("*")):
            if src.is_file():
                place(src, project / ".agents" / "workflows" / ".reference" / src.name, res, dry)

    # 6. Lifecycle workflows -> .agents/workflows/ (discoverable on Antigravity)
    if WF_SRC.exists():
        for src in sorted(WF_SRC.glob("*.md")):
            if LIFECYCLE_RE.match(src.name) or src.name in EXTRA_WORKFLOWS:
                place(src, project / ".agents" / "workflows" / src.name, res, dry)

    # 6b. Project-local deterministic scripts (memory lint runs from the project)
    vm = PLUGIN_ROOT / "scripts" / "validate_memory.py"
    if vm.exists():
        place(vm, project / ".agents" / "scripts" / "validate_memory.py", res, dry)



    # 8. .gitignore (create if missing; never edit an existing one)
    gi = project / ".gitignore"
    gi_existed = gi.exists()
    if not gi_existed:
        if dry:
            res["would"].append(Path(".gitignore"))
        else:
            gi.write_text("\n".join(GITIGNORE_ENTRIES) + "\n", encoding="utf-8")
            res["created"].append(Path(".gitignore"))

    # 9. Update Lockfile
    count = generate_lockfile(dry)
    if count and not dry:
        res["created"].append(Path(".agents/.stratosphere-lock.json"))

    # Summary
    verb = "WOULD CREATE" if dry else "CREATED"
    created = res["would"] if dry else res["created"]
    print(f"=== StratosphereOS scaffold ({'dry-run' if dry else 'applied'}) ===")
    print(f"{verb}: {len(created)}")
    for p in created:
        print(f"  + {p}")
    if res["exists"]:
        print(f"LEFT AS-IS (already present, agent should drift-check): {len(res['exists'])}")
        for p in res["exists"]:
            print(f"  = {p}")
    if gi_existed:
        # existing .gitignore: remind agent to verify secret-hygiene entries
        print("NOTE: .gitignore already exists — verify it contains: " + ", ".join(GITIGNORE_ENTRIES))
        print("NOTE: Existing projects must manually add *.work.md to their .gitignore (scaffold never edits existing ones).")


if __name__ == "__main__":
    main()
