"""BT-199: the gh-call budget of one 3z slice run in `tracker: github` mode.

The 4a ship-gate call is read out of the workflow text (not retyped here), so the budget follows the document. `gh` is
stubbed: every GraphQL read counts as one call and answers from a small in-memory repository (epic 5, slices 7 and 8,
8 blocked by 7, both in epic 5's ship unit). The live measurement on CleanTechHub is a separate, manual read-only run.
"""
import contextlib
import importlib.util
import io
import json
import re
from pathlib import Path

from conftest import combined_gate_argv

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("reconcile_gh_calls", ROOT / "src" / "scripts" / "reconcile.py")
rec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rec)

BUDGET = 10  # gh calls per 3z slice run (epic BT-194, slice BT-199 AC)


def _ref(n, state="OPEN", tags=("tier:slice",), parent=None, blocked=(), blocking=(), comments=()):
    node = {"number": n, "state": state, "milestone": None,
            "labels": {"nodes": [{"name": t} for t in tags]},
            "parent": None, "blockedBy": {"nodes": [_ref(b) for b in blocked]},
            "blocking": {"nodes": [dict(_ref(d, tags=("tier:slice", "status:planned")), parent=_ref(5, tags=("tier:epic",)))
                                   for d in blocking]},
            "comments": {"nodes": [{"body": c} for c in comments]}}
    if parent:
        node["parent"] = dict(_ref(parent, tags=("tier:epic", "status:in review")), blockedBy={"nodes": []})
    return node


class Repo:
    """The stub `gh`: counts calls and serves `i_<n>` aliases."""

    def __init__(self):
        self.calls = 0
        self.cleared = False  # set once 4a ran the [CLEAR] command on 8's edge

    def nodes(self):
        return {
            5: _ref(5, tags=("tier:epic", "status:in review")),
            7: _ref(7, "CLOSED", ("tier:slice", "status:done"), parent=5, blocking=() if self.cleared else (8,),
                    comments=("Shipped in https://github.com/o/r/pull/42",)),
            8: _ref(8, tags=("tier:slice", "status:planned"), parent=5, blocked=() if self.cleared else (7,)),
        }

    def run(self, args):
        self.calls += 1
        query = next(a for a in args if a.startswith("query="))
        table = self.nodes()
        repo = {f"i_{n}": table.get(int(n)) for n in re.findall(r"i_(\d+): issue", query)}
        return 0, json.dumps({"data": {"repository": repo}}), ""


def _run(tmp_path, argv):
    arch = tmp_path / "ARCHITECTURE.md"
    arch.write_text("---\ntype: architecture\ntracker: github\n---\n# A\n", encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = rec.main(argv + ["--arch", str(arch), "--backlog", str(tmp_path / "BACKLOG_MAP.md")])
    return code, buf.getvalue()


def test_a_3z_slice_run_costs_one_gh_call_per_reconcile_invocation_and_stays_in_budget(monkeypatch, tmp_path):
    repo = Repo()
    monkeypatch.setattr(rec, "_gh_run", repo.run)
    seen = []

    def invoke(argv, expect_code=None):
        before = repo.calls
        code, out = _run(tmp_path, argv)
        seen.append(repo.calls - before)
        if expect_code is not None:
            assert code == expect_code, out
        return out

    invoke(["--edges", "blockers", "--ids", "BT-007,BT-008"])                    # 3z Phase 1: the whole queue, once
    invoke(["--edges", "blockers", "--ids", "BT-007"])                           # 3z 2A.0: the frontier of this slice
    out = invoke(combined_gate_argv("BT-007", "BT-005"), expect_code=0)                     # 4a: status gate + dependents together
    assert "[MIRROR-OK BT-007,BT-005]" in out and "[CLEAR BT-008 <- BT-007]" in out, out
    repo.cleared = True                                                          # 4a ran the [CLEAR] cmd
    out = invoke(["--edges", "dependents", "--ids", "BT-007,BT-005"])            # 4a: re-check, once
    assert "[CLEAR" not in out, out

    assert seen == [1, 1, 1, 1], f"each reconcile invocation must be one batched gh call, got {seen}"
    assert sum(seen) <= BUDGET
