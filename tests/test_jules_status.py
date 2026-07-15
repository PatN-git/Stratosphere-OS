#!/usr/bin/env python3
"""Offline tests for status.py (P4) + the no-merge / no-orchestration guardrails.

Run: python tests/test_jules_status.py
"""
import json
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests"))
from test_jules import ReplayCaller, _fx  # sets pack sys.path

import status  # noqa: E402
import dispatch  # noqa: E402
from jules_api import JulesClient, JulesError  # noqa: E402

PACK = REPO_ROOT / "src" / "experimental" / "jules-dispatch"


def _seed_ledger(d, session_id="sess_abc123", state="DISPATCHED"):
    ledger = Path(d) / ".memory" / "jules-ledger.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(json.dumps({
        "slice_id": "BT-0042", "session_id": session_id, "source": "src/x",
        "title": "BT-0042", "created_at": "t", "state": state,
    }) + "\n", encoding="utf-8")
    return ledger


def test_status_pr_ready_flips_done():
    print("--- test_status_pr_ready_flips_done ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = _seed_ledger(d)
        c = JulesClient(caller=ReplayCaller({("GET", "/sessions/sess_abc123"): _fx("session_pr_ready.json")}))
        out = []
        rows = status.status(c, ledger, ci_fetcher=lambda url: "SUCCESS", printer=out.append)
        assert rows[0]["state"] == "DONE" and rows[0]["pr_url"].endswith("/pull/123")
        assert any("PR ready" in line for line in out)
        assert any("/4a_verify-and-ship" in line for line in out), "must instruct human handoff"
        # persisted
        assert dispatch.load_ledger(ledger)[0]["state"] == "DONE"
    print("PASS"); return True


def test_status_running_stays_dispatched():
    print("--- test_status_running_stays_dispatched ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = _seed_ledger(d)
        c = JulesClient(caller=ReplayCaller({("GET", "/sessions/sess_abc123"): _fx("session_running.json")}))
        out = []
        rows = status.status(c, ledger, ci_fetcher=lambda u: "x", printer=out.append)
        assert rows[0]["state"] == "DISPATCHED"
        assert any("still running" in line for line in out)
    print("PASS"); return True


def test_status_skips_done_rows():
    print("--- test_status_skips_done_rows ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = _seed_ledger(d, state="DONE")
        rc = ReplayCaller({("GET", "/sessions/sess_abc123"): _fx("session_pr_ready.json")})
        status.status(JulesClient(caller=rc), ledger, ci_fetcher=lambda u: "x", printer=lambda *_: None)
        assert len(rc.calls) == 0, "DONE rows must not be re-polled (idempotent)"
    print("PASS"); return True


def test_status_session_error_marks_failed():
    print("--- test_status_session_error_marks_failed ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = _seed_ledger(d)
        c = JulesClient(caller=ReplayCaller({("GET", "/sessions/sess_abc123"): ("error", 404)}))
        rows = status.status(c, ledger, ci_fetcher=lambda u: "x", printer=lambda *_: None)
        assert rows[0]["state"] == "FAILED"
    print("PASS"); return True


def test_no_merge_calls_in_code():
    print("--- test_no_merge_calls_in_code ---")
    # Precise merge-ACTION patterns (prose 'merge' in docs is allowed; code calls are not).
    pat = re.compile(r"gh\s+pr\s+merge|pulls/[^\"']*/merge|merge_method|enableAutoMerge|autoMerge|--auto\b", re.I)
    offenders = []
    for py in PACK.glob("*.py"):
        for i, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if pat.search(line):
                offenders.append(f"{py.name}:{i}: {line.strip()}")
    assert not offenders, "merge action found in pack code:\n" + "\n".join(offenders)
    print("PASS"); return True


def test_no_workflow_invocation_in_status():
    print("--- test_no_workflow_invocation_in_status ---")
    # status.py may PRINT the /4a handoff instruction, but must not SUBPROCESS a workflow.
    src = (PACK / "status.py").read_text(encoding="utf-8")
    # exactly one subprocess call, and it is the read-only `gh pr view` CI check
    assert src.count("subprocess.run(") == 1, "status.py must have exactly one subprocess call"
    assert '["gh", "pr", "view"' in src, "the only subprocess must be the read-only gh pr view CI check"
    # 4a is referenced only as a printed handoff instruction, never invoked as a process
    assert "4a_verify-and-ship" in src, "should reference the handoff instruction (as text only)"
    print("PASS"); return True


TESTS = [
    test_status_pr_ready_flips_done, test_status_running_stays_dispatched,
    test_status_skips_done_rows, test_status_session_error_marks_failed,
    test_no_merge_calls_in_code, test_no_workflow_invocation_in_status,
]

if __name__ == "__main__":
    ok = True
    for t in TESTS:
        try:
            ok = t() and ok
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}"); ok = False
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
    sys.exit(0 if ok else 1)
