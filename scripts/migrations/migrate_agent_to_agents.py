#!/usr/bin/env python3
"""One-shot migration: rename a StratosphereOS project's constitution AGENT.md -> AGENTS.md.

StratosphereOS moved its constitution filename from the nonstandard `AGENT.md`
(singular) to `AGENTS.md` (plural) — the Linux Foundation "agents.md" open
standard that Claude Code (via a CLAUDE.md `@AGENTS.md` import), Antigravity,
and Google Jules all read. Fresh installs use the new name automatically; this
script migrates an EXISTING instantiated project in place.

It is intentionally NOT wired into scaffold.py's install/update lifecycle —
run it once, by hand, from the target project root.

What it does (all idempotent, content-preserving):
  1. Rename `AGENT.md` -> `AGENTS.md` (keeps your Vision/customizations).
  2. Repoint `CLAUDE.md` / `GEMINI.md` (swap any `AGENT.md` reference).
  3. Rename the `AGENT.md` key -> `AGENTS.md` in `.agents/.stratosphere-lock.json`.

Safety:
  - If BOTH `AGENT.md` and `AGENTS.md` already exist, it refuses to clobber and exits non-zero.
  - Re-running after a successful migration is a no-op.
  - `--dry-run` reports the plan without writing.

Usage:
  python migrate_agent_to_agents.py [--project PATH] [--dry-run]
"""
import argparse
import json
import sys
from pathlib import Path

OLD = "AGENT.md"
NEW = "AGENTS.md"
POINTERS = ("CLAUDE.md", "GEMINI.md")
LOCK_REL = Path(".agents") / ".stratosphere-lock.json"


def plan_and_apply(project: Path, dry: bool) -> int:
    old_p = project / OLD
    new_p = project / NEW
    actions = []      # human-readable planned actions
    writes = []       # callables performing the write, run only when not dry

    # --- 1. Constitution rename -------------------------------------------------
    if old_p.exists() and new_p.exists():
        print(f"ERROR: both {OLD} and {NEW} exist in {project}. Resolve manually "
              f"(merge your content into {NEW} and delete {OLD}), then re-run.", file=sys.stderr)
        return 2
    if not old_p.exists() and not new_p.exists():
        print(f"No {OLD} or {NEW} found in {project} — nothing to migrate "
              f"(is this a StratosphereOS project root?).")
        return 0
    if not old_p.exists() and new_p.exists():
        # Already migrated; still reconcile pointers/lock below for idempotent repair.
        pass
    else:
        actions.append(f"rename {OLD} -> {NEW}")
        writes.append(lambda: old_p.rename(new_p))

    # --- 2. Pointer files -------------------------------------------------------
    for name in POINTERS:
        p = project / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        if OLD in text:
            actions.append(f"repoint {name}: '{OLD}' -> '{NEW}'")
            new_text = text.replace(OLD, NEW)
            writes.append(lambda p=p, t=new_text: p.write_text(t, encoding="utf-8"))

    # --- 3. Lockfile artifact key ----------------------------------------------
    lock_p = project / LOCK_REL
    if lock_p.exists():
        try:
            lock = json.loads(lock_p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"WARNING: could not parse {LOCK_REL} ({e}); skipping lock update. "
                  f"You can regenerate it with `scaffold.py --repair-lock`.", file=sys.stderr)
            lock = None
        if isinstance(lock, dict):
            arts = lock.get("artifacts", {})
            if OLD in arts:
                actions.append(f"lock: rename artifact key '{OLD}' -> '{NEW}'")

                def _write_lock(lock=lock, lock_p=lock_p):
                    a = lock["artifacts"]
                    a[NEW] = a.pop(OLD)
                    lock_p.write_text(json.dumps(lock, indent=2), encoding="utf-8")

                writes.append(_write_lock)

    # --- report / apply ---------------------------------------------------------
    if not actions:
        print(f"Already on {NEW}; nothing to do.")
        return 0

    header = "[DRY-RUN] would apply:" if dry else "Applying:"
    print(header)
    for a in actions:
        print(f"  - {a}")

    if dry:
        print("[DRY-RUN] no files changed.")
        return 0

    for w in writes:
        w()
    print(f"Done. Migrated {len(actions)} item(s). "
          f"Review the changes and stage them (e.g. `git add -A`).")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Migrate a StratosphereOS project's AGENT.md -> AGENTS.md.")
    ap.add_argument("--project", default=".", help="Path to the project root (default: current directory).")
    ap.add_argument("--dry-run", action="store_true", help="Report the plan without writing.")
    args = ap.parse_args(argv)

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"ERROR: {project} is not a directory.", file=sys.stderr)
        return 2
    return plan_and_apply(project, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
