"""BT-198: ICE on read. In `tracker: github` mode no score is stored; 3c computes it from the issue body's
Impact and Confidence plus the `size:` label, and lists its candidates through one scoped `gh issue list`.

Seams: `ice_from_body` / `parse_metrics` (pure), `candidates` (pure over gh's JSON) and `main` with `gh` stubbed.
"""
import json
import re
import sys

import pytest

from conftest import REPO_ROOT

SCRIPTS = REPO_ROOT / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import ice_read
import reconcile

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "ice"


def _body(impact, confidence):
    return f"### ICE Priorities\n- **Impact:** {impact}\n- **Confidence:** {confidence}\n- **ICE Score:** x\n"


def _issue(n, labels, body="", title="t", milestone=None):
    return {"number": n, "title": title, "labels": [{"name": l} for l in labels],
            "milestone": {"title": milestone} if milestone else None, "body": body}


LEAF = ["tier:slice", "type:feature", "mode:AFK", "size:medium"]


@pytest.mark.parametrize("impact,confidence,want", [
    ("2.0", "100%", (2.0, 1.0)),
    ("2.0 (Directly unblocks dozens)", "100% (High confidence; pattern established)", (2.0, 1.0)),
    ("3", "0.8", (3.0, 0.8)),
    ("1.5", "80 %", (1.5, 0.8)),
])
def test_parse_metrics_reads_the_formats_3b_writes(impact, confidence, want):
    got = ice_read.parse_metrics(_body(impact, confidence))
    assert (got["impact"], got["confidence"]) == want


@pytest.mark.parametrize("label,weight", [("size:small", 1), ("size:medium", 2), ("size:large", 3)])
def test_effort_weight_comes_from_the_size_label(label, weight):
    assert ice_read.ice_from_body(_body("3", "100%"), ["tier:slice", label]) == pytest.approx(3 / weight, abs=0.01)


def test_ice_is_none_without_metrics_or_a_size_label():
    assert ice_read.ice_from_body("### Overview\nno metrics here", LEAF) is None
    assert ice_read.ice_from_body("### ICE Priorities\n- Not set at mint (user decision)", LEAF) is None
    assert ice_read.ice_from_body(_body("2.0", "100%"), ["tier:slice"]) is None


@pytest.mark.parametrize("name", ["cth-bt241.json", "cth-bt243.json"])
def test_real_bodies_reproduce_stored_score(name):
    """Two real CleanTechHub bodies (BT-241, BT-243): the computed score equals the score 3b stored in the body."""
    issue = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    stored = float(re.search(r"\*\*ICE Score:\*\*\s*([0-9.]+)", issue["body"]).group(1))
    assert ice_read.ice_from_body(issue["body"], issue["labels"]) == pytest.approx(stored, abs=0.01)


def test_candidates_keep_planned_and_needs_spec_leaves_only():
    issues = [
        _issue(1, LEAF + ["status:planned", "scope:baseline"], _body("2.0", "100%")),
        _issue(2, LEAF + ["status:needs_spec"], title="spike"),
        _issue(3, LEAF + ["status:in progress"]),
        _issue(4, ["tier:epic", "type:feature", "status:planned"]),
        _issue(5, LEAF + ["status:planned", "concept:research"]),
        _issue(6, LEAF + ["status:planned", "scope:deferred"]),
    ]
    lines, _ = ice_read.candidates(issues)
    assert [l.split(" | ")[0] for l in lines] == ["BT-001", "BT-002"]


def test_candidate_line_carries_status_labels_milestone_and_ice():
    issues = [_issue(7, LEAF + ["status:planned", "scope:baseline", "area:BE-api"], _body("3", "100%"), "Do it", "v1.2.0")]
    (line,), missing = ice_read.candidates(issues)
    assert missing == []
    assert line == "BT-007 | planned | Do it | area:BE-api mode:AFK scope:baseline size:medium type:feature | v1.2.0 | ICE 1.5"


def test_a_spike_and_a_body_without_metrics_print_no_score():
    issues = [_issue(8, LEAF + ["status:needs_spec"]), _issue(9, LEAF + ["status:planned"], "### Overview\nx")]
    lines, _ = ice_read.candidates(issues)
    assert all(l.endswith("| ICE —") for l in lines)


def test_a_leaf_missing_a_required_label_is_listed_not_sequenced():
    issues = [_issue(10, ["tier:slice", "type:feature", "status:planned"], title="no size or mode")]
    lines, missing = ice_read.candidates(issues)
    assert lines == []
    assert missing == ["[MISSING-LABELS] BT-010 - no size or mode (mode:, size:)"]


def test_main_prints_lines_then_missing_labels(monkeypatch, capsys):
    issues = [_issue(1, LEAF + ["status:planned"], _body("2.0", "100%")), _issue(2, ["status:planned"], title="bare")]
    monkeypatch.setattr(reconcile, "_gh_run", lambda args: (0, json.dumps(issues), ""))
    assert ice_read.main(["candidates"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("BT-001 | planned") and out[-1].startswith("[MISSING-LABELS] BT-002")


def test_main_halts_on_a_gh_failure_and_never_falls_back_to_a_map(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(reconcile, "_gh_run", lambda args: calls.append(args) or (1, "", "boom"))
    monkeypatch.setattr(reconcile, "_sleep", lambda s: None)
    assert ice_read.main(["candidates"]) == 3
    out = capsys.readouterr().out
    assert "GH-UNAVAILABLE" in out and "BACKLOG" not in out
    assert len(calls) == len(reconcile.RETRY_DELAYS) + 1


def test_main_warns_when_the_open_issue_list_hits_the_cap(monkeypatch, capsys):
    """Audit watch: `gh issue list --limit` silently drops issues past the cap; the output says so."""
    issues = [_issue(n, LEAF + ["status:planned"], _body("2.0", "100%")) for n in range(1, ice_read.LIST_LIMIT + 1)]
    monkeypatch.setattr(reconcile, "_gh_run", lambda args: (0, json.dumps(issues), ""))
    assert ice_read.main(["candidates"]) == 0
    assert "[TRUNCATED" in capsys.readouterr().out.splitlines()[-1]


def test_main_does_not_warn_below_the_cap(monkeypatch, capsys):
    monkeypatch.setattr(reconcile, "_gh_run", lambda args: (0, json.dumps([_issue(1, LEAF + ["status:planned"])]), ""))
    assert ice_read.main(["candidates"]) == 0
    assert "TRUNCATED" not in capsys.readouterr().out
