# md-crosscheck: build and ship loop (3b, 3d, 3z, 4a, pr-body-and-ship, ci-gate) vs tracker-verbs.md and reconcile.py
"""BT-199: in `tracker: github` mode the build and ship loop asks GitHub for one issue at a time and 4a's ship gate is
one combined `reconcile.py` call. BT-221: the local backend is the issues.py store; no loop file names the old map.
"""
import importlib.util
import re

import pytest

from conftest import SRC, assert_argv_accepted, combined_gate_argv, combined_gate_calls, read_src, write_architecture

LOOP = ["workflows/3b-create-issue.md", "workflows/3d-implement-issue.md", "workflows/3z-afk-loop.md",
        "workflows/4a-verify-and-ship.md", "references/pr-body-and-ship.md", "references/ci-gate.md"]

_spec = importlib.util.spec_from_file_location("reconcile_ship_loop", SRC / "scripts" / "reconcile.py")
rec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rec)


@pytest.mark.parametrize("rel", LOOP)
def test_no_loop_file_names_the_retired_map(rel):
    offenders = [l.strip()[:120] for l in read_src(rel).splitlines() if re.search(r"BACKLOG|map row|map cell", l)]
    assert offenders == [], f"{rel} still reads or writes the retired map: {offenders}"


def test_3b_mints_the_draft_as_the_body_and_deletes_drafts_only_after_the_post_condition():
    text = read_src("workflows/3b-create-issue.md")
    assert re.search(r"`create`[^\n]*`\.tmp/3b-issue-body\.md`", text), "3b must mint with the body file"
    assert "issues.py check" in text, "3b's local post-condition is `issues.py check`"
    cleanup = next(l for l in text.splitlines() if "Scratch cleanup" in l)
    assert "`check`" in cleanup, "the drafts are deleted only after the gate or the local `check` passes"


def test_3d_claims_the_slice_and_halts_on_a_claimed_one():
    text = read_src("workflows/3d-implement-issue.md")
    assert re.search(r"`claim` the slice[^\n]*\[CLAIMED", text), "3d must `claim` the slice and halt on [CLAIMED]"


def test_3z_local_queue_comes_from_ready():
    assert "python .agents/scripts/issues.py ready" in read_src("workflows/3z-afk-loop.md")


def test_4a_auditor_reads_acceptance_criteria_with_get():
    line = next(l for l in read_src("workflows/4a-verify-and-ship.md").splitlines() if "Business-Logic Auditor" in l)
    assert re.search(r"Acceptance Criteria[^\n]*`get`", line), "the auditor reads the AC with the `get` read"


def test_4a_ship_push_also_pushes_the_tracker_branch():
    push = next(l for l in read_src("workflows/4a-verify-and-ship.md").splitlines() if "Release bump + push" in l)
    assert "git push origin" in push and "issues.py branch" in push, "4a's ship push must push the tracker branch"


@pytest.mark.parametrize("rel", ["workflows/3d-implement-issue.md", "workflows/3z-afk-loop.md", "workflows/4a-verify-and-ship.md"])
def test_status_writes_are_verbs(rel):
    assert "`set_status`" in read_src(rel), f"{rel} writes status without naming the verb"


def test_3d_reads_milestone_and_parent_from_the_single_issue():
    text = read_src("workflows/3d-implement-issue.md")
    assert "gh issue view <n> --json milestone,parent" in text


def test_3z_builds_its_queue_with_a_scoped_query():
    text = read_src("workflows/3z-afk-loop.md")
    assert "gh issue view <n> --json number,state,labels,milestone,parent" in text
    assert re.search(r"gh issue list --state open --milestone <[^>]+> --json number,title,labels,milestone,parent", text)


def test_4a_ship_gate_is_one_combined_call():
    calls = combined_gate_calls()
    assert len(calls) == 1, f"want exactly one combined `--with-edges dependents` call in 4a, found {len(calls)}"
    args = calls[0]
    for flag in ("--ids", "--pr-id", "--expect"):
        assert flag in args, f"4a's combined call lacks {flag}"
    assert "BT-<slice>:status=done" in args


def test_4a_combined_call_parses_under_the_real_argparse(tmp_path, monkeypatch):
    write_architecture(tmp_path / "ARCHITECTURE.md", "github")
    monkeypatch.setattr(rec, "fetch_nodes", lambda nums, comments=False, edges=False: {n: None for n in nums})
    assert_argv_accepted(rec.main, combined_gate_argv("BT-001", "BT-002") +
                         ["--arch", str(tmp_path / "ARCHITECTURE.md"), "--backlog", str(tmp_path / "BACKLOG_MAP.md")])


def test_4a_clears_dependents_through_the_verb_and_rechecks_once():
    text = read_src("workflows/4a-verify-and-ship.md")
    assert "`clear_blocker`" in text and "--edges dependents" in text
    assert re.search(r"re-run[^\n]*--edges dependents[^\n]*no `\[CLEAR\]`", text), \
        "4a must re-run `--edges dependents` once and require no [CLEAR] left"
