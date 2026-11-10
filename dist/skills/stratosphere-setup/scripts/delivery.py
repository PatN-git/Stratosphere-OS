#!/usr/bin/env python3
"""Multi-host skill delivery bridge for StratosphereOS.

Allows inspecting delivery mode, switching modes between 'plugin' and 'in-repo',
and restoring lifecycle skills on-demand for non-plugin hosts (Cursor, Codex, Devin).
"""
import argparse
import glob
import json
import os
import subprocess
import sys
from pathlib import Path


def find_project_root(start: Path) -> Path:
    curr = start.resolve()
    for parent in [curr] + list(curr.parents):
        if (parent / ".agents" / ".stratosphere-lock.json").exists() or (parent / ".agents").is_dir():
            return parent
    return curr


def get_lockfile_data(project_root: Path) -> tuple[Path, dict]:
    lock_file = project_root / ".agents" / ".stratosphere-lock.json"
    if not lock_file.exists():
        return lock_file, {}
    try:
        return lock_file, json.loads(lock_file.read_text(encoding="utf-8"))
    except Exception:
        return lock_file, {}


def locate_scaffolder(project_root: Path) -> Path | None:
    """Locates the scaffold.py script in dev workspaces or global plugin caches."""
    if "STRATOSPHERE_SCAFFOLD_SCRIPT" in os.environ:
        p = Path(os.environ["STRATOSPHERE_SCAFFOLD_SCRIPT"])
        if p.is_file():
            return p

    # 1. Dev repository / workspace root check (ancestors of cwd or project_root)
    for start in [Path.cwd().resolve(), project_root.resolve()]:
        for p in [start] + list(start.parents):
            c = p / "dist" / "skills" / "stratosphere-setup" / "scripts" / "scaffold.py"
            if c.is_file():
                return c

    # 2. Global plugin caches
    home = Path.home()
    candidates = [
        home / ".gemini" / "config" / "plugins" / "stratosphere-os" / "skills" / "stratosphere-setup" / "scripts" / "scaffold.py",
        home / ".gemini" / "config" / "skills" / "stratosphere-setup" / "scripts" / "scaffold.py",
    ]
    claude_cache = home / ".claude" / "plugins" / "cache"
    if claude_cache.is_dir():
        for p in glob.glob(str(claude_cache / "**" / "stratosphere-setup" / "scripts" / "scaffold.py"), recursive=True):
            candidates.append(Path(p))

    for c in candidates:
        if c.is_file():
            return c
    return None


def cmd_status(project_root: Path):
    lock_file, data = get_lockfile_data(project_root)
    if not lock_file.exists():
        print(f"Status: unconfigured (no lockfile found at {lock_file})")
        return 1

    mode = data.get("skill_delivery", "in-repo (legacy/default)")
    version = data.get("installed_plugin_version", "unknown")
    plugin_id = data.get("plugin_id", "none")

    print(f"StratosphereOS Delivery Status:")
    print(f"  Project Root:     {project_root}")
    print(f"  Skill Delivery:   {mode}")
    print(f"  Plugin ID:        {plugin_id}")
    print(f"  Installed Version:{version}")
    print(f"  Lockfile:         {lock_file}")
    return 0


def cmd_set_mode(project_root: Path, mode: str):
    lock_file, data = get_lockfile_data(project_root)
    if not lock_file.exists():
        print(f"Error: No lockfile found at {lock_file}. Run /stratosphere-setup first.")
        return 1

    scaffolder = locate_scaffolder(project_root)
    if scaffolder:
        cmd = [sys.executable, str(scaffolder), "--delivery", mode]
        print(f"Running scaffolder: {' '.join(cmd)}")
        res = subprocess.run(cmd, cwd=str(project_root))
        return res.returncode

    # Fallback if no global scaffolder found: update lockfile directly
    data["skill_delivery"] = mode
    lock_file.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Updated skill_delivery to '{mode}' in {lock_file}")
    return 0


def cmd_restore_skills(project_root: Path):
    print("Restoring lifecycle skills into .agents/skills/ for non-plugin host compatibility...")
    scaffolder = locate_scaffolder(project_root)
    if scaffolder:
        cmd = [sys.executable, str(scaffolder), "--delivery", "in-repo"]
        print(f"Running scaffolder: {' '.join(cmd)}")
        res = subprocess.run(cmd, cwd=str(project_root))
        if res.returncode == 0:
            print("[RESTORE OK] Bundled lifecycle skills restored into .agents/skills/.")
        return res.returncode

    print("Scaffolder payload not found locally in plugin cache.")
    print("Attempting restore via npx skills...")
    npx_cmd = ["npx", "skills", "add", "PatN-git/Stratosphere-OS/dist/skills", "-a", "agents", "--copy", "-y"]
    try:
        res = subprocess.run(npx_cmd, cwd=str(project_root))
        return res.returncode
    except FileNotFoundError:
        print("Error: neither local plugin cache nor 'npx' was found.")
        print("Remediation: Install the StratosphereOS plugin or run from a host with plugin support.")
        return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Multi-host skill delivery bridge for StratosphereOS.")
    ap.add_argument("--project", default=".", help="Project directory (default: current directory)")
    ap.add_argument("--status", action="store_true", help="Inspect current skill delivery status")
    ap.add_argument("--set-mode", choices=["plugin", "in-repo"], help="Switch delivery mode")
    ap.add_argument("--restore-skills", action="store_true", help="Restore bundled lifecycle skills into .agents/skills/")
    args = ap.parse_args(argv)

    project_root = find_project_root(Path(args.project))

    if args.status:
        return cmd_status(project_root)
    elif args.set_mode:
        return cmd_set_mode(project_root, args.set_mode)
    elif args.restore_skills:
        return cmd_restore_skills(project_root)
    else:
        ap.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
