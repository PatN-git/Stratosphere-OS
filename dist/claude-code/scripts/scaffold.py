#!/usr/bin/env python3
"""Deterministic StratosphereOS project scaffolder — zero LLM tokens.

Creates the project's folder structure and copies bundled templates into place,
**create-only-if-missing** (never overwrites). The agent's instantiate command
calls this for all mechanical work and keeps only the reasoning steps
(brownfield audits, label reconciliation, skill selection).

The script lives in the installed plugin at `<plugin>/scripts/scaffold.py`.
Run it FROM THE PROJECT ROOT (cwd = project), e.g.:

  python <plugin>/scripts/scaffold.py            # core scaffold
  python <plugin>/scripts/scaffold.py --personas # also scaffold persona layer
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
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent

def prompt_personas():
    while True:
        try:
            val = input("Scaffold the StratosphereOS persona layer (Analyst, PM, Designer, Dev, Reviewer)? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return False
        if not val or val in ("n", "no"):
            return False
        if val in ("y", "yes"):
            return True
        print("Please enter 'y' or 'n'.")

ASSETS = PLUGIN_ROOT / "assets" / "templates"
# Lifecycle workflows live in workflows/ (Antigravity build) or commands/ (Claude build)
WF_SRC = PLUGIN_ROOT / "workflows" if (PLUGIN_ROOT / "workflows").exists() else PLUGIN_ROOT / "commands"

LIFECYCLE_RE = re.compile(r"^[0-4].*\.md$")  # 0a..4b
EXTRA_WORKFLOWS = {"sync-skills.md"}          # also copy this utility workflow

GITIGNORE_ENTRIES = [".tmp/", "node_modules/", ".DS_Store", "Thumbs.db",
                     "*.log", ".env", ".env.*", "token.json",
                     ".agents/skills/", "!.agents/skills/.lock.json"]

FOLDERS = [
    ".memory",
    ".agents/rules",
    ".agents/workflows",
    ".agents/workflows/.reference",
    ".agents/scripts",
    "docs/discovery",
    "docs/prds",
    ".tmp",
]
KEEP_EMPTY = {"docs/discovery", "docs/prds", ".tmp"}  # add .gitkeep so they survive git


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

    if plugin_root_resolved == (home / ".claude" / "plugins" / "stratosphere-os").resolve():
        scope = "global Claude Code"
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
    ap.add_argument("--personas", dest="personas", action="store_true", default=None, help="scaffold the optional persona layer")
    ap.add_argument("--no-personas", dest="personas", action="store_false", help="do not scaffold the optional persona layer")
    ap.add_argument("--dry-run", action="store_true", help="report what would happen without writing")
    args = ap.parse_args()

    # Interactive prompt if run without configuration flags in a TTY
    if args.personas is None:
        if not args.dry_run and sys.stdin.isatty():
            args.personas = prompt_personas()
        else:
            print("Non-interactive context: defaulting to --no-personas")
            args.personas = False

    project = Path.cwd()
    dry = args.dry_run
    res = {"created": [], "exists": [], "would": []}

    if not ASSETS.exists():
        raise SystemExit(f"Cannot find bundled templates at {ASSETS}. Run from a project root with the plugin installed.")

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

    # 7. Personas (optional)
    if args.personas and (ASSETS / "personas").exists():
        for name in ("designer.md", "_persona-template.md"):
            src = ASSETS / "personas" / name
            if src.exists():
                place(src, project / ".agents" / "workflows" / name, res, dry)

    # 8. .gitignore (create if missing; never edit an existing one)
    gi = project / ".gitignore"
    gi_existed = gi.exists()
    if not gi_existed:
        if dry:
            res["would"].append(Path(".gitignore"))
        else:
            gi.write_text("\n".join(GITIGNORE_ENTRIES) + "\n", encoding="utf-8")
            res["created"].append(Path(".gitignore"))

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


if __name__ == "__main__":
    main()
