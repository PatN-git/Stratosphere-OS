"""L3 - the seeded upstream, so the late chain can be driven on its own.

Driving `3b` onward otherwise costs four phases of live agent work to reach the one
under test. These artifacts stand in for that work.

The fixture has to be **self-consistent**, not merely present: the seeded epic must pass
`issues.py check`, or 3b's local check would fail on my fixture rather than on the
lifecycle, which is the worst possible finding to produce.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parent.parent / "lifecycle-harness"
REPO = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


e = _load("l3_env_seed", HARNESS / "env.py")
a = _load("l3_assertions_seed", HARNESS / "assertions.py")


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    """A scaffold-shaped project with the upstream artifacts installed."""
    project = tmp_path / "project"
    (project / ".memory").mkdir(parents=True)
    scripts = project / ".agents" / "scripts"
    scripts.mkdir(parents=True)
    for name in SCRIPTS:
        (scripts / name).write_text((REPO / "src" / "scripts" / name).read_text(encoding="utf-8"), encoding="utf-8")
    subprocess.run(["git", "init", str(project)], capture_output=True, check=True)

    child = {"PATH": os.environ.get("PATH", "")}
    shim_dir = e.install_shims(tmp_path, child)
    child.update({"GIT_AUTHOR_NAME": "L3", "GIT_AUTHOR_EMAIL": "l3@harness.invalid",
                  "GIT_COMMITTER_NAME": "L3",
                  "GIT_COMMITTER_EMAIL": "l3@harness.invalid"})
    assert issues(project, child, "init").returncode == 0  # what `scaffold.py --tracker local` runs
    e.seed_upstream(project, child, shim_dir)
    return project, child


SCRIPTS = ("issues.py", "reconcile.py", "nightly_state.py", "ice_read.py", "pr_body.py")


def issues(project, child, *argv):
    return subprocess.run([sys.executable, str(project / ".agents" / "scripts" / "issues.py"), *argv],
                          cwd=str(project), env={**os.environ, **child}, capture_output=True, text=True)


def store(child):
    return json.loads(Path(child["L3_GH_STORE"]).read_text(encoding="utf-8"))


# --- the artifacts 3b reads ---------------------------------------------------

def test_the_prd_carries_the_sections_3b_slices_from(seeded):
    """`3b:17`: PRD-sourced runs read sections 1, 6, 7 and 8."""
    project, _ = seeded
    prd = a.only(project, "docs/prds/BT-*.md")
    text = a.read(prd)
    for heading in ("## 1. Problem", "## 6. User Stories",
                    "## 7. Constraints & Direction", "## 8. Definition of Done"):
        assert heading in text, f"missing {heading}"


def test_the_prd_is_stable_and_typed(seeded):
    project, _ = seeded
    fm = a.frontmatter(a.read(a.only(project, "docs/prds/BT-*.md")))
    assert fm["type"] == "prd"
    assert fm["status"] == "stable"


def test_the_design_doc_is_path_c(seeded):
    """Fact 10: Path C is the only branch fully exercisable headlessly."""
    project, _ = seeded
    text = a.read(a.only(project, "docs/design/BT-*-interface.md"))
    assert "Interface Contract" in text and "Path C" in text


def test_the_brief_points_at_the_prd(seeded):
    """What `2a` writes back. Seeded here, so a seeded run proves nothing about it."""
    project, _ = seeded
    assert a.frontmatter(a.read(a.brief_path(project)))["linked-prd"] == "BT-001"


def test_the_research_carries_the_cost_section(seeded):
    """D6: the section 2a's Cost Approval Gate lifts from."""
    project, _ = seeded
    assert "## Cost & Viability Signals" in a.read(
        a.only(project, "docs/research/*.md"))


def test_the_upstream_artifacts_pass_their_own_phase_checks(seeded):
    """The fixture must satisfy the same assertions the real phases are held to."""
    project, child = seeded
    for phase in ("1a", "1b", "2a", "2b"):
        problems, _ = a.check(phase, a.Context(
            project=project, child_env=child, before=a.snapshot(project),
            handoff=True))
        assert problems == [], f"{phase}: {problems}"


# --- the world the artifacts describe -----------------------------------------

def test_the_local_backend_seed_touches_no_github(seeded):
    """The local backend never touches GitHub: the epic is a store issue and the shim's store stays empty."""
    _, child = seeded
    store_file = Path(child["L3_GH_STORE"])
    assert not store_file.exists() or not store(child)["issues"]


def test_the_local_epic_is_a_bt_local_issue_on_the_tracker_branch(seeded):
    """`issues.py create` (tracker-verbs `create`): status is a field, never a label; the store passes `check`."""
    project, child = seeded
    epic = json.loads(issues(project, child, "get", e._seed.LOCAL_EPIC_ID).stdout)
    assert epic["status"] == "planned" and epic["milestone"] == "v1.0.0"
    assert "tier:epic" in epic["labels"] and not any(l.startswith("status:") for l in epic["labels"])
    assert issues(project, child, "check").returncode == 0
    assert not list(a.backlog_maps(project))


def test_the_seed_is_committed_so_3d_starts_from_a_clean_tree(seeded):
    """`3d` cuts a branch and commits onto it; uncommitted upstream docs would ride
    along in its first commit and make the diff unreadable."""
    project, _ = seeded
    dirty = subprocess.run(["git", "-C", str(project), "status", "--porcelain"],
                           capture_output=True, text=True).stdout.strip()
    assert dirty == "", dirty


# --- the honesty of a seeded run ----------------------------------------------

def test_a_seeded_run_says_what_it_did_not_test(tmp_path, capsys):
    r = _load("l3_run_seed", HARNESS / "run-L3.py")
    assert r.parse_args(["--seed"]).seed is True
    assert r.parse_args([]).seed is False


# --- GitHub mode: the epic is the whole record ---------------------------------

def test_a_github_seed_mints_the_epic_but_writes_no_backlog_row(tmp_path):
    project = tmp_path / "project"
    (project / ".memory").mkdir(parents=True)
    subprocess.run(["git", "init", str(project)], capture_output=True, check=True)
    child = {"PATH": os.environ.get("PATH", ""), "GIT_AUTHOR_NAME": "L3", "GIT_AUTHOR_EMAIL": "l3@harness.invalid",
             "GIT_COMMITTER_NAME": "L3", "GIT_COMMITTER_EMAIL": "l3@harness.invalid"}
    shim_dir = e.install_shims(tmp_path, child)
    e.seed_upstream(project, child, shim_dir, tracker="github")
    assert not (project / ".memory" / "BACKLOG_MAP.md").exists()
    epic = store(child)["issues"]["1"]
    assert {"tier:epic", "status:planned"} <= {l["name"] for l in epic["labels"]}


def test_the_runner_threads_the_tracker_choice():
    r = _load("l3_run_tracker", HARNESS / "run-L3.py")
    assert r.parse_args([]).tracker == "local"
    assert r.parse_args(["--tracker", "github"]).tracker == "github"
