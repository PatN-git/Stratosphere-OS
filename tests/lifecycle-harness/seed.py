#!/usr/bin/env python3
"""L3 seed - the upstream artifacts `0a`-`2b` would have produced, installed so `3b` onward can be driven alone.

Split out of `env.py` (one concern per file, A-003). `env.py` loads it by path and re-exports `seed_upstream`,
`EPIC_LABELS` and `UPSTREAM`, so callers keep using `env.seed_upstream`.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# The tracker backend that keeps no BACKLOG_MAP.md: the minted epic is the whole record.
GITHUB = "github"

UPSTREAM = Path(__file__).parent / "fixture" / "upstream"


def seed_upstream(project: Path, child: dict, shim_dir: Path, tracker: str = "local") -> list[str]:
    """Install what `0a`-`2b` would have produced, so `3b` onward can be driven alone.

    Driving the late chain otherwise costs the early chain every time - four phases
    of live agent work to reach the one being tested. These artifacts are a FIXTURE,
    written to match what a real run produced (a PRD with sections 1/6/7/8, which is
    what `3b:17` reads; a Path C interface design; the brief and research they cite).

    **A seeded run tests the phases it drives, not the hand-off into them.** `2a`
    writing `linked-prd` back into the brief is proven by driving `2a`, never by this.
    The run says so out loud, and Slice 9's report must record it, or a green late
    chain will be read as a green whole chain.

    The parent epic is minted THROUGH the shim rather than written into its store by
    hand, so the store's shape has one author. The BACKLOG row is then written to
    agree with it - `reconcile.py` compares the two, and a fixture that disagreed
    with itself would fail the first terminal gate `3b` reaches.
    """
    shutil.copytree(UPSTREAM, project, dirs_exist_ok=True)
    epic = _mint_epic(child, shim_dir)
    if tracker != GITHUB:  # GitHub is the only store there: the minted epic is the whole record
        _seed_backlog_row(project, epic)
    subprocess.run(["git", "-C", str(project), "add", "-A"], capture_output=True)
    subprocess.run(["git", "-C", str(project), "commit", "-m",
                    "docs(BT-001): seeded upstream artifacts (L3 fixture)"],
                   env=child, capture_output=True)
    return sorted(str(p.relative_to(UPSTREAM)) for p in UPSTREAM.rglob("*")
                  if p.is_file())


EPIC_LABELS = ("status:planned", "type:feature", "tier:epic")


def _mint_epic(child: dict, shim_dir: Path) -> str:
    """`2a:30` mints the parent issue with `gh issue create`. Same path here."""
    r = subprocess.run(
        ["python", str(shim_dir / "gh_shim.py"), "issue", "create",
         "--title", "BT-001: Local feature flag evaluation",
         "--body", "Parent feature. Sliced by /3b-create-issue.",
         "--label", ",".join(EPIC_LABELS), "--milestone", "v1.0.0"],
        env=child, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"could not mint the parent epic through the shim: "
                           f"{r.stdout}{r.stderr}")
    return r.stdout.strip()


def _seed_backlog_row(project: Path, epic_url: str) -> None:
    """One row, agreeing with the store: status bare in Status, never in Labels."""
    backlog = project / ".memory" / "BACKLOG_MAP.md"
    text = backlog.read_text(encoding="utf-8")
    labels = ", ".join(l for l in EPIC_LABELS if not l.startswith("status:"))
    row = (f"| BT-001 | Local feature flag evaluation | planned | {labels} "
           f"| v1.0.0 | — | — | I1.0×C80%/E1 | "
           f"docs/prds/BT-001-local-feature-flag-evaluation.md |")
    lines = text.splitlines()
    last_table_line = max(i for i, ln in enumerate(lines) if ln.lstrip().startswith("|"))
    lines.insert(last_table_line + 1, row)
    backlog.write_text("\n".join(lines) + "\n", encoding="utf-8")
