# md-crosscheck: build and ship loop (3d, 3z, 4a, pr-body-and-ship, ci-gate) vs tracker-verbs.md and reconcile.py
"""BT-199: in `tracker: github` mode the build and ship loop asks GitHub for one issue at a time, 4a's ship gate is one
combined `reconcile.py` call, and the map is named only as the local backend.
"""
import importlib.util
import re

import pytest

from conftest import SRC, combined_gate_argv, combined_gate_calls, read_src

LOOP = ["workflows/3d-implement-issue.md", "workflows/3z-afk-loop.md", "workflows/4a-verify-and-ship.md",
        "references/pr-body-and-ship.md", "references/ci-gate.md"]
NAME_THE_MAP = [r for r in LOOP if r != "references/ci-gate.md"]  # ci-gate never read the map
GH_WRITE = re.compile(r"gh issue (create|edit|close|comment|reopen)|gh api graphql|addBlockedBy|addSubIssue|removeBlockedBy"
                      r"|--add-label|--remove-label|--milestone|`(set_status|set_milestone|close|create|clear_blocker)`")

_spec = importlib.util.spec_from_file_location("reconcile_ship_loop", SRC / "scripts" / "reconcile.py")
rec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rec)


@pytest.mark.parametrize("rel", LOOP)
def test_the_map_is_only_named_as_the_local_backend(rel):
    offenders = [l.strip()[:120] for l in read_src(rel).splitlines()
                 if re.search(r"BACKLOG|map row", l) and not re.search(r"local", l, re.I)]
    assert offenders == [], f"{rel} reads or writes the map outside a local clause: {offenders}"


@pytest.mark.parametrize("rel", LOOP)
def test_no_sentence_writes_both_github_and_the_map(rel):
    offenders = []
    for line in read_src(rel).splitlines():
        for sentence in re.split(r"(?<=[.;:])\s+", line):
            if "BACKLOG" in sentence and GH_WRITE.search(sentence):
                offenders.append(sentence.strip()[:120])
    assert offenders == [], f"{rel} writes GitHub and the map in one sentence: {offenders}"


@pytest.mark.parametrize("rel", NAME_THE_MAP)
def test_every_loop_file_keeps_its_local_clause(rel):
    assert "BACKLOG_MAP" in read_src(rel), f"{rel} lost its local-backend clause"


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
    for flag in ("--require-gh", "--ids", "--pr-id", "--expect"):
        assert flag in args, f"4a's combined call lacks {flag}"
    assert "BT-<slice>:status=done" in args


def test_4a_combined_call_parses_under_the_real_argparse(tmp_path, monkeypatch):
    arch = tmp_path / "ARCHITECTURE.md"
    arch.write_text("---\ntype: architecture\ntracker: github\n---\n# A\n", encoding="utf-8")
    monkeypatch.setattr(rec, "fetch_nodes", lambda nums, comments=False, edges=False: {n: None for n in nums})
    argv = combined_gate_argv("BT-001", "BT-002")
    try:
        rec.main(argv + ["--arch", str(arch), "--backlog", str(tmp_path / "BACKLOG_MAP.md")])
    except SystemExit as e:
        assert e.code != 2, f"`{' '.join(argv)}` rejected by reconcile.py argparse"


def test_4a_clears_dependents_through_the_verb_and_rechecks_once():
    text = read_src("workflows/4a-verify-and-ship.md")
    assert "`clear_blocker`" in text and "--edges dependents" in text
    assert re.search(r"re-run[^\n]*--edges dependents[^\n]*no `\[CLEAR\]`", text), \
        "4a must re-run `--edges dependents` once and require no [CLEAR] left"
