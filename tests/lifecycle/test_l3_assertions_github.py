"""BT-199: the `3b` assertions in GitHub mode (`tracker: github`, no BACKLOG_MAP.md).

Same shim and helpers as `test_l3_assertions.py` (a sibling module: pytest puts this directory on `sys.path`).
"""
import os
from pathlib import Path

from conftest import write_architecture
from test_l3_assertions import ARCH, BACKLOG, MAP, _project_with_reconcile, _shimmed, a, gh, write

EPIC_LABELS = "status:planned,type:feature,tier:epic"
SLICE_LABELS = "status:planned,type:feature,tier:slice,mode:AFK,size:small"


def _github_project(tmp_path):
    proj = _project_with_reconcile(tmp_path, BACKLOG)
    (proj / MAP).unlink()
    write_architecture(proj / ARCH, "github")
    return proj


def _mint_feature(slice_labels=SLICE_LABELS, link=True):
    gh.main(["issue", "create", "--title", "Epic", "--label", EPIC_LABELS, "--milestone", "v1.0.0"])
    gh.main(["issue", "create", "--title", "Slice", "--label", slice_labels, "--milestone", "v1.0.0"])
    if link:
        state = gh.load()
        epic, sl = state["issues"]["1"], state["issues"]["2"]
        sl["parent"] = gh.brief(epic)
        epic["subIssues"].append(gh.brief(sl))
        gh.save(state)


def _github_ctx(proj, child):
    return a.Context(project=proj, child_env={**os.environ}, store=Path(child["L3_GH_STORE"]),
                     before=a.snapshot(proj), tracker="github")


def test_3b_github_passes_with_no_map_and_a_store_that_matches(tmp_path, monkeypatch):
    child = _shimmed(tmp_path, monkeypatch)
    _mint_feature()
    proj = _github_project(tmp_path)
    problems, _ = a.check("3b", _github_ctx(proj, child))
    assert problems == [], problems


def test_3b_github_fails_when_a_map_file_exists(tmp_path, monkeypatch):
    child = _shimmed(tmp_path, monkeypatch)
    _mint_feature()
    proj = _github_project(tmp_path)
    write(proj / MAP, BACKLOG)
    problems, _ = a.check("3b", _github_ctx(proj, child))
    assert any("BACKLOG_MAP" in p for p in problems), problems


def test_3b_github_fails_when_the_gate_cannot_reach_the_expected_state(tmp_path, monkeypatch):
    child = _shimmed(tmp_path, monkeypatch)
    _mint_feature(slice_labels="status:done,type:feature,tier:slice,mode:AFK,size:small")
    proj = _github_project(tmp_path)
    problems, _ = a.check("3b", _github_ctx(proj, child))
    assert any("MIRROR-OK" in p for p in problems), problems


def test_3b_github_fails_when_a_slice_has_no_parent(tmp_path, monkeypatch):
    child = _shimmed(tmp_path, monkeypatch)
    _mint_feature(link=False)
    proj = _github_project(tmp_path)
    problems, _ = a.check("3b", _github_ctx(proj, child))
    assert any("parent" in p and "BT-002" in p for p in problems), problems


def test_3b_github_fails_when_a_slice_lacks_a_required_label(tmp_path, monkeypatch):
    child = _shimmed(tmp_path, monkeypatch)
    _mint_feature(slice_labels="status:planned,type:feature,tier:slice")
    proj = _github_project(tmp_path)
    problems, _ = a.check("3b", _github_ctx(proj, child))
    assert any("BT-002" in p and "size:" in p and "mode:" in p for p in problems), problems
