#!/usr/bin/env python3
"""One-shot migration: bring a StratosphereOS v3 project up to the v4.0.0 layout.

v4.0.0 renames every lifecycle artifact to Agent Skills spec form and moves it
from `.agents/workflows/*.md` to `.agents/skills/<name>/SKILL.md`. Running
`stratosphere-update` alone is NOT sufficient, for three reasons:

  1. `reconcile_gitignore()` in scaffold.py only ADDS entries. A v3 project's
     `.gitignore` still contains `.agents/skills/`, so every migrated skill
     lands in an ignored directory and silently drops out of version control.
  2. The update flow has no removal phase, so the 19 superseded
     `.agents/workflows/*.md` and their `.reference/` tree stay on disk. Until
     2026-11-01 Antigravity indexes both, and `/0a_start-session` and
     `/0a-start-session` both resolve — to different versions of the same skill.
  3. `.memory/` and `docs/` are `preserved` tier, so the scaffolder never
     migrates the project's own OKF frontmatter to v0.2.

Like `migrate_agent_to_agents.py`, this is intentionally NOT wired into
scaffold.py's install/update lifecycle — run it once, by hand, from the target
project root. It is idempotent and safe to re-run.

Unlike that script, it defaults to a DRY RUN: this one deletes files.

    python migrate_v3_to_v4.py [--project PATH] [--apply]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Any spelling that ignores the bundled-skills tree. v3 projects carry several
# (`.agents/skills/`, `.agents/skills/*`, `/.agents/skills/**`), and leaving ONE
# behind silently untracks all 26 migrated skills — the failure this script exists
# to prevent. Matched after normalising leading `/` and trailing `/`, `/*`, `/**`.
STALE_SKILLS_IGNORE = ".agents/skills"
STALE_GITIGNORE = ("!.agents/skills/.lock.json",)


def _is_stale_ignore(line: str) -> bool:
    l = line.strip()
    if l in STALE_GITIGNORE:
        return True
    l = l.lstrip("/").rstrip("/")
    for suffix in ("/**", "/*"):
        if l.endswith(suffix):
            l = l[: -len(suffix)]
    return l == STALE_SKILLS_IGNORE

STATUS_MAP = {
    "approved": "stable", "active": "stable", "ready-to-implement": "stable",
    "superseded": "deprecated", "stale": "deprecated", "proposed": "draft",
}
DISCOVERY_VOCAB = {"ready-for-prd", "exit-bug", "exit-spike", "dropped"}
SKIP_DIRS = {"archive", ".archive", ".templates", "knowledge", "node_modules"}


# --- helpers ---------------------------------------------------------------

def load_lock(project: Path) -> dict:
    p = project / ".agents" / ".stratosphere-lock.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("artifacts", {})
    except Exception:
        return {}


def git_author(project: Path, rel: Path) -> str:
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%an", "--", str(rel)],
                             cwd=project, capture_output=True, text=True, timeout=15)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


# --- steps -----------------------------------------------------------------

def fix_gitignore(project: Path, dry: bool, log: list) -> None:
    gi = project / ".gitignore"
    if not gi.exists():
        return
    lines = gi.read_text(encoding="utf-8").splitlines()
    keep = [l for l in lines if not _is_stale_ignore(l)]
    if len(keep) == len(lines):
        log.append("  .gitignore: already clean")
        return
    removed = [l for l in lines if _is_stale_ignore(l)]
    for r in removed:
        log.append(f"  .gitignore: remove {r.strip()!r}  <- was untracking every bundled skill")
    if not dry:
        gi.write_text("\n".join(keep) + "\n", encoding="utf-8")


def remove_legacy_tree(project: Path, dry: bool, log: list) -> None:
    wf = project / ".agents" / "workflows"
    if not wf.exists():
        log.append("  .agents/workflows/: already absent")
        return
    lock = load_lock(project)
    owned, foreign = [], []
    for p in sorted(wf.rglob("*")):
        if p.is_file():
            rel = p.relative_to(project).as_posix()
            (owned if rel in lock else foreign).append(p)

    for p in owned:
        log.append(f"  remove (framework-owned): {p.relative_to(project).as_posix()}")
    for p in foreign:
        log.append(f"  KEEP (user-authored, not in lockfile): {p.relative_to(project).as_posix()}")

    if not dry:
        for p in owned:
            p.unlink()
        # prune now-empty dirs, deepest first; a dir holding user files survives
        for d in sorted((d for d in wf.rglob("*") if d.is_dir()), key=lambda x: -len(x.parts)):
            if not any(d.iterdir()):
                d.rmdir()
        if not any(wf.iterdir()):
            wf.rmdir()
        elif foreign:
            log.append("  .agents/workflows/ kept: it still holds user-authored files")

    if foreign:
        log.append(f"  NOTE: {len(foreign)} user-authored file(s) left in place. Move them to "
                   f".agents/skills/<name>/SKILL.md yourself if they should remain invocable.")


def migrate_frontmatter(project: Path, dry: bool, log: list) -> None:
    roots = [project / ".memory", project / "docs"]
    changed = 0
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.md")):
            if p.name == "index.md" or any(s in p.relative_to(root).parts for s in SKIP_DIRS):
                continue
            txt = p.read_text(encoding="utf-8")
            m = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n', txt, flags=re.S)
            if not m:
                continue
            fm = orig = m.group(1)

            ts = re.search(r'^timestamp:[ \t]*(.+?)[ \t]*$', fm, flags=re.M)
            if ts:
                by = git_author(project, p.relative_to(project))
                fm = re.sub(r'^timestamp:[ \t]*.+?[ \t]*$',
                            f'generated:\n  by: {by}\n  at: {ts.group(1)}', fm, count=1, flags=re.M)

            st = re.search(r'^status:[ \t]*(.+?)[ \t]*$', fm, flags=re.M)
            if st:
                val = st.group(1).strip().strip('"').strip("'")
                if val not in DISCOVERY_VOCAB and "|" not in val and val in STATUS_MAP:
                    fm = re.sub(r'^status:[ \t]*.+?[ \t]*$',
                                f'status: {STATUS_MAP[val]}', fm, count=1, flags=re.M)

            if fm != orig:
                changed += 1
                log.append(f"  frontmatter -> OKF v0.2: {p.relative_to(project).as_posix()}")
                if not dry:
                    p.write_text(txt[:m.start(1)] + fm + txt[m.end(1):], encoding="utf-8")
    if not changed:
        log.append("  frontmatter: already OKF v0.2")


def prune_lock(project: Path, dry: bool, log: list) -> None:
    lp = project / ".agents" / ".stratosphere-lock.json"
    if not lp.exists():
        return
    try:
        data = json.loads(lp.read_text(encoding="utf-8"))
    except Exception:
        log.append("  lockfile: unreadable, skipped")
        return
    arts = data.get("artifacts", {})
    stale = [k for k in arts if k.startswith(".agents/workflows/")]
    if not stale:
        log.append("  lockfile: no stale workflow entries")
        return
    log.append(f"  lockfile: drop {len(stale)} stale .agents/workflows/ entries")
    if not dry:
        for k in stale:
            arts.pop(k, None)
        lp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# --- entry point -----------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Migrate a StratosphereOS project from v3 to the v4.0.0 skills layout.")
    ap.add_argument("--project", default=".", help="Project root (default: cwd).")
    ap.add_argument("--apply", action="store_true", help="Write changes. Without it this is a dry run.")
    args = ap.parse_args(argv)

    project = Path(args.project).resolve()
    if not (project / ".agents").exists():
        print(f"ERROR: {project} does not look like a StratosphereOS project (no .agents/).")
        return 1

    dry = not args.apply
    log: list = []
    print(f"{'DRY RUN' if dry else 'APPLYING'} - v3 -> v4.0.0 migration in {project}\n")

    fix_gitignore(project, dry, log)
    remove_legacy_tree(project, dry, log)
    migrate_frontmatter(project, dry, log)
    prune_lock(project, dry, log)

    for line in log:
        print(line)

    print()
    if dry:
        print("No changes written. Re-run with --apply to perform the migration.")
    else:
        print("Migration complete. Now run /stratosphere-update to install the v4 skills,")
        print("then confirm `git status` shows .agents/skills/ as tracked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
