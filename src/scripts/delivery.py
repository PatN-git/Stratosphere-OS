#!/usr/bin/env python3
"""Multi-host skill delivery bridge for StratosphereOS.

Allows inspecting delivery mode, switching modes between 'plugin' and 'in-repo',
and restoring lifecycle skills on-demand for non-plugin hosts (Cursor, Codex, Devin).
"""
import argparse
import glob
import json
import os
import re
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


def _parse_version_key(v_str: str):
    """Sort key for semantic version directories like 1.0.0, 1.10.0, v1.8.0."""
    cleaned = v_str.lstrip("v")
    return tuple((0, int(part)) if part.isdigit() else (1, part) for part in re.split(r"[-.+_]", cleaned))


def _claude_cache_version(path: Path, cache_root: Path):
    """Extract version sort key from a scaffold.py path inside ~/.claude/plugins/cache."""
    rel = path.relative_to(cache_root).parts
    if "stratosphere-os" in rel:
        idx = rel.index("stratosphere-os")
        if idx + 1 < len(rel):
            return _parse_version_key(rel[idx + 1])
    if "skills" in rel:
        idx = rel.index("skills")
        if idx >= 2 and rel[idx - 1] == "dist":
            return _parse_version_key(rel[idx - 2])
        if idx >= 1:
            return _parse_version_key(rel[idx - 1])
    if "stratosphere-setup" in rel:
        idx = rel.index("stratosphere-setup")
        if idx >= 1:
            return _parse_version_key(rel[idx - 1])
    return _parse_version_key("")


def locate_scaffolder(project_root: Path) -> Path | None:
    """Locates the scaffold.py script in dev workspaces or global plugin caches."""
    if "STRATOSPHERE_SCAFFOLD_SCRIPT" in os.environ:
        p = Path(os.environ["STRATOSPHERE_SCAFFOLD_SCRIPT"])
        if p.is_file():
            return p

    env_skills = os.environ.get("STRATOSPHERE_PLUGIN_SKILLS")
    if env_skills:
        p = Path(env_skills) / "stratosphere-setup" / "scripts" / "scaffold.py"
        if p.is_file():
            return p

    rel_scaffold = Path("stratosphere-setup") / "scripts" / "scaffold.py"

    # 1. Dev repository / workspace root check (ancestors of cwd or project_root)
    for start in [Path.cwd().resolve(), project_root.resolve()]:
        for p in [start] + list(start.parents):
            c = p / "dist" / "skills" / rel_scaffold
            if c.is_file():
                return c

    # 2. Global plugin caches
    home = Path.home()
    candidates = [
        *sorted((home / ".gemini" / "config" / "plugins").glob(f"*/skills/{rel_scaffold.as_posix()}"), reverse=True),
        home / ".gemini" / "config" / "plugins" / "stratosphere-os" / "skills" / rel_scaffold,
        home / ".gemini" / "antigravity" / "plugins" / "stratosphere-os" / "skills" / rel_scaffold,
        home / ".gemini" / "config" / "skills" / rel_scaffold,
    ]
    claude_cache = home / ".claude" / "plugins" / "cache"
    if claude_cache.is_dir():
        hits = [Path(p) for p in glob.glob(str(claude_cache / "**" / rel_scaffold), recursive=True)]
        candidates.extend(sorted(hits, key=lambda p: (_claude_cache_version(p, claude_cache), str(p)), reverse=True))

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
