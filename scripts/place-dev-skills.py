#!/usr/bin/env python3
"""Place StratOS's dev-only skills into THIS repo's agent directories.

`src/dev-skills/` holds skills used to develop StratosphereOS itself. They must
never reach a consumer project, so `build/build.py` does not glob them the way it
globs `src/skills/`. This script is the only thing that installs them, and it
installs them here and nowhere else.

Run from the repo root after editing anything under `src/dev-skills/`:

    python scripts/place-dev-skills.py [--check]

--check exits non-zero if a placed copy has drifted from its source, so CI can
guard the copies without rewriting them.
"""
from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "dev-skills"
IN_TREE_TARGETS = (ROOT / ".agents" / "skills", ROOT / ".claude" / "skills")
GLOBAL_AGY_TARGET = Path.home() / ".gemini" / "config" / "skills"


def main() -> int:
    check = "--check" in sys.argv
    if not SRC.is_dir():
        print(f"no dev-skills source at {SRC}")
        return 0

    targets = list(IN_TREE_TARGETS)
    if not check:
        # Clean up retired directory names from previous versions
        for t in targets + ([GLOBAL_AGY_TARGET] if GLOBAL_AGY_TARGET.parent.exists() else []):
            stale = t / "improve-workflows-skills"
            if stale.is_dir():
                shutil.rmtree(stale)
        # Ensure dev-only skills never leak into global Antigravity config
        if GLOBAL_AGY_TARGET.is_dir():
            for skill in SRC.iterdir():
                stale_global = GLOBAL_AGY_TARGET / skill.name
                if stale_global.is_dir():
                    shutil.rmtree(stale_global)

    drifted: list[str] = []
    placed = 0
    for skill in sorted(SRC.iterdir()):
        if not skill.is_dir():
            continue
        for src_file in sorted(skill.rglob("*")):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(SRC)
            for target in targets:
                dst = target / rel
                if check:
                    # This repo gitignores `.agents/` wholesale, so that copy is
                    # absent in a fresh clone. Absent != drifted; only compare
                    # targets the checkout actually carries.
                    if not target.exists():
                        continue
                    if not dst.exists() or not filecmp.cmp(src_file, dst, shallow=False):
                        rel_name = dst.relative_to(ROOT) if dst.is_relative_to(ROOT) else dst
                        drifted.append(str(rel_name))
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst)
                placed += 1

    if check:
        if drifted:
            print("DEV-SKILL DRIFT — run `python scripts/place-dev-skills.py`:")
            for d in drifted:
                print(f"  {d}")
            return 1
        print("dev-skills: placed copies match source")
        return 0

    print(f"dev-skills: placed {placed} file(s) into {len(targets)} target(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
