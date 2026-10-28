#!/usr/bin/env python3
# md-crosscheck: reconcile.py CLI surface vs the 3a/3b/3c/4a/post-merge-sync/0d prose that calls it
"""BT-200: the map-vs-GitHub diff, heal, summary and `--require-gh` are gone. Local mode keeps only `--edges`;
GitHub mode keeps the `--expect` gate; the deleted symbols stay deleted."""
import contextlib
import importlib.util
import io
from pathlib import Path

import pytest

from conftest import SRC, read_src

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("reconcile_bt200", SRC / "scripts" / "reconcile.py")
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)

MAP = """\
| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |
|----|-------|--------|--------|-----------|--------|------------|-----|-----|
| BT-001 | Shipped | done | type:feature | v1.0.0 | BT-100 | — | ICE | — |
| BT-003 | Waits on 1 | planned | type:feature | v1.0.0 | BT-100 | BT-001 | ICE | — |
"""

DELETED = ["stale_blockers", "fetch_issue", "classify", "summarize", "drift_kind", "heal", "upsert_cells",
           "gh_fix_commands", "KIND_PREFIXES", "CHRONIC_NIGHTS", "HEAL_KINDS", "HEAL_CELL", "STATE_DEFAULT",
           "_nightly_state", "_gh_state", "_cell_text", "_map_text"]
KEPT = ["parse_backlog", "open_ids", "effective_blockers", "edge_verdict", "edges_cmd", "compare",
        "closed_on_github", "open_on_github", "pr_merge_state", "make_merged_of", "github_gate", "github_main",
        "resolve_backend", "read_tracker", "parse_expect"]


def local_project(tmp_path):
    arch = tmp_path / "ARCHITECTURE.md"
    arch.write_text("---\ntype: architecture\ntracker: local\n---\n", encoding="utf-8")
    backlog = tmp_path / "BACKLOG_MAP.md"
    backlog.write_text(MAP, encoding="utf-8")
    return ["--arch", str(arch), "--backlog", str(backlog)]


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = rec.main(argv)
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


@pytest.mark.parametrize("name", DELETED)
def test_the_map_diff_heal_and_summary_symbols_are_gone(name):
    assert not hasattr(rec, name), f"reconcile.py still defines {name}"


@pytest.mark.parametrize("name", KEPT)
def test_the_github_gate_and_local_edge_symbols_stay(name):
    assert hasattr(rec, name), f"reconcile.py lost {name}"


@pytest.mark.parametrize("flag", [["--heal", "--kind", "status", "--source", "gh"], ["--summary"],
                                  ["--require-gh"], ["--keys-out", "x"], ["--state", "x"], ["--date", "2026-01-01"]])
def test_removed_flags_are_rejected_by_argparse(tmp_path, flag):
    code, _, err = run(["--ids", "BT-001", *local_project(tmp_path), *flag])
    assert code == 2 and "unrecognized arguments" in err


def test_local_mode_supports_only_edges(tmp_path):
    code, _, err = run(["--ids", "BT-003", *local_project(tmp_path)])
    assert code == 2 and "only --edges" in err


def test_local_edges_still_decide_blockers_and_dependents(tmp_path):
    base = local_project(tmp_path)
    code, out, _ = run(["--edges", "blockers", "--ids", "BT-003", *base])
    assert code == 0 and "[BLOCKER-OK BT-003 <- BT-001]" in out, out
    code, out, _ = run(["--edges", "dependents", "--all-open", *base])
    assert "[CLEAR BT-003 <- BT-001]" in out and "cmd:" in out, out


def test_github_mode_still_refuses_the_map_only_runs(tmp_path):
    arch = tmp_path / "ARCHITECTURE.md"
    arch.write_text("---\ntype: architecture\ntracker: github\n---\n", encoding="utf-8")
    code, _, err = run(["--all-open", "--arch", str(arch)])
    assert code == 2 and "tracker: github" in err


def test_the_gate_texts_speak_of_the_intended_state_not_a_map():
    row = {"status": "done", "labels": {"type:feature"}, "milestone": "v1.0.0", "parent": "BT-100",
           "blocked_by": set()}
    gh = {"state": "OPEN", "labels": [{"name": "status:in review"}, {"name": "type:feature"}, {"name": "x"}],
          "milestone": {"title": "v1.0.0"}}
    texts = rec.compare(row, gh, {"status", "labels"}, check_pr=False) + [rec.open_on_github(row, gh)]
    assert texts and all("map" not in t and "expect" in t for t in texts), texts


@pytest.mark.parametrize("rel", ["workflows/3a-version-planning.md", "workflows/3b-create-issue.md",
                                 "workflows/3c-sprint-planning.md", "workflows/4a-verify-and-ship.md",
                                 "references/post-merge-sync.md"])
def test_no_caller_passes_the_removed_require_gh_flag(rel):
    assert "--require-gh" not in read_src(rel), rel
