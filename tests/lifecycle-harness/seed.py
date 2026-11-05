#!/usr/bin/env python3
"""L3 seed - the upstream artifacts `0a`-`2b` would have produced, installed so `3b` onward can be driven alone.

Split out of `env.py` (one concern per file, A-003). `env.py` loads it by path and re-exports `seed_upstream`,
`EPIC_LABELS` and `UPSTREAM`, so callers keep using `env.seed_upstream`.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# The tracker backend whose store is GitHub itself: the minted epic is the whole record.
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

    Under `tracker: github` the parent epic is minted THROUGH the shim rather than
    written into its store by hand, so the store's shape has one author. Under the
    local backend GitHub is not touched: the epic is one `BT-LOCAL-<slug>` issue on the tracker branch, created
    with the installed `issues.py` (`references/tracker-verbs.md`), and the shim's store stays empty.
    """
    shutil.copytree(UPSTREAM, project, dirs_exist_ok=True)
    if tracker == GITHUB:  # GitHub is the only store there: the minted epic is the whole record
        _mint_epic(child, shim_dir)
    else:  # the local backend never touches GitHub: its store issue is the whole record
        _create_local_epic(project, child)
    subprocess.run(["git", "-C", str(project), "add", "-A"], capture_output=True)
    subprocess.run(["git", "-C", str(project), "commit", "-m",
                    "docs(BT-001): seeded upstream artifacts (L3 fixture)"],
                   env=child, capture_output=True)
    return sorted(str(p.relative_to(UPSTREAM)) for p in UPSTREAM.rglob("*")
                  if p.is_file())


EPIC_LABELS = ("status:planned", "type:feature", "tier:epic")

# `references/label-taxonomy.md`: what `stratosphere-setup` (greenfield) creates in a new repo. The shim refuses any
# label outside its registry, as real gh does, so a GitHub-mode run starts with this set. `area:*` slugs are the
# project's own and none is used here. A test pins this equal to `issues.py` CANONICAL + STATUSES.
LABELS = tuple(
    [f"type:{v}" for v in ("bug", "content", "feature", "improvement", "maintenance", "research")]
    + [f"mode:{v}" for v in ("HITL", "AFK")] + [f"tier:{v}" for v in ("epic", "slice")]
    + [f"priority:{v}" for v in ("high", "medium", "low")] + [f"size:{v}" for v in ("large", "medium", "small")]
    + [f"scope:{v}" for v in ("baseline", "differentiator", "deferred")]
    + [f"status:{v}" for v in ("needs_spec", "planned", "in progress", "in review", "blocked", "done")]
    + [f"concept:{v}" for v in ("map", "research", "grilling", "prototype", "task")] + ["risk:one-way"])


def seed_labels(child: dict, shim_dir: Path) -> None:
    """Fill the shim's label registry with the taxonomy, through the shim's own store functions (one author)."""
    spec = importlib.util.spec_from_file_location("l3_gh_shim_seed", shim_dir / "gh_shim.py")
    shim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shim)
    prior = os.environ.get("L3_GH_STORE")
    os.environ["L3_GH_STORE"] = child["L3_GH_STORE"]
    try:
        state = shim.load()
        for name in LABELS:
            shim.register_label(state, name)
        shim.save(state)
    finally:
        if prior is None:
            os.environ.pop("L3_GH_STORE")
        else:
            os.environ["L3_GH_STORE"] = prior


def _mint_epic(child: dict, shim_dir: Path) -> str:
    """`2a:30` mints the parent issue with `gh issue create`. Same path here, on a repo that already has its labels."""
    seed_labels(child, shim_dir)
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


LOCAL_EPIC_ID = "BT-LOCAL-local-feature-flag-evaluation"
EPIC_BODY = "Parent feature. Sliced by /3b-create-issue.\n\nPRD: docs/prds/BT-001-local-feature-flag-evaluation.md\n"


def _create_local_epic(project: Path, child: dict) -> str:
    """The local backend's epic, through the installed `issues.py create` (tracker-verbs `create`): status is a field,
    never a label. The body file lives outside the project, so the working tree stays clean."""
    fd, body = tempfile.mkstemp(suffix=".md")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(EPIC_BODY)
    try:
        r = subprocess.run(
            [sys.executable, str(project / ".agents" / "scripts" / "issues.py"), "create",
             "--title", "Local feature flag evaluation",
             "--label", ",".join(l for l in EPIC_LABELS if not l.startswith("status:")),
             "--status", "planned", "--milestone", "v1.0.0", "--body-file", body],
            cwd=str(project), env={**os.environ, **child}, capture_output=True, text=True)
    finally:
        os.unlink(body)
    if r.returncode != 0 or r.stdout.strip() != LOCAL_EPIC_ID:
        raise RuntimeError(f"could not create the local epic with issues.py: {r.stdout}{r.stderr}")
    return LOCAL_EPIC_ID
