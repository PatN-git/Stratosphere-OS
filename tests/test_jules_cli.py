#!/usr/bin/env python3
"""CLI tests for dispatch.main / status.main (P3/P4) — offline via injected deps.

Covers the paths the unit tests missed: the sprint composition (dep gating over
_sprint_candidates→select_eligible→preflight), session-id normalization, and status.

Run: python tests/test_jules_cli.py
"""
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests"))
from test_jules import ReplayCaller, _fx  # sets pack sys.path

import dispatch  # noqa: E402
import status    # noqa: E402
from jules_api import JulesClient  # noqa: E402


def _issue(num, blocked_line=""):
    body = "Do X.\n" + (blocked_line + "\n" if blocked_line else "") + "## Acceptance Criteria\n- x"
    return {"number": num, "title": f"BT-{num}: t", "body": body,
            "labels": [{"name": "mode:AFK"}, {"name": "tier:slice"}], "state": "OPEN"}


def _created_client():
    return JulesClient(caller=ReplayCaller({("POST", "/sessions"): _fx("session_created.json")}))


def test_dispatch_cli_single():
    print("--- test_dispatch_cli_single ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = Path(d) / ".memory" / "jules-ledger.jsonl"
        rc = dispatch.main(["--slice", "42", "--source", "src/x", "--ledger", str(ledger)],
                           client=_created_client(), issue_fetcher=lambda s: _issue(42))
        assert rc == 0
        rows = dispatch.load_ledger(ledger)
        assert len(rows) == 1 and rows[0]["session_id"] == "sess_abc123", rows
    print("PASS"); return True


def test_dispatch_cli_normalizes_name_only_session():
    print("--- test_dispatch_cli_normalizes_name_only_session ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = Path(d) / ".memory" / "jules-ledger.jsonl"
        # API returns only AIP `name` (no bare id) — id must be stored bare, not doubled
        client = JulesClient(caller=ReplayCaller({("POST", "/sessions"): {"name": "sessions/sess_xyz"}}))
        dispatch.main(["--slice", "42", "--source", "src/x", "--ledger", str(ledger)],
                      client=client, issue_fetcher=lambda s: _issue(42))
        assert dispatch.load_ledger(ledger)[0]["session_id"] == "sess_xyz", "must strip 'sessions/' prefix"
    print("PASS"); return True


def test_dispatch_cli_sprint_dep_met():
    print("--- test_dispatch_cli_sprint_dep_met ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = Path(d) / ".memory" / "jules-ledger.jsonl"
        cands = [
            {"slice_id": "42", "labels": ["mode:AFK", "tier:slice"], "blocked_by": ["43"], "state": "open", "_issue": _issue(42, "Blocked-by: 43")},
            {"slice_id": "43", "labels": ["mode:AFK", "tier:slice"], "blocked_by": [], "state": "done", "_issue": _issue(43)},
            {"slice_id": "50", "labels": ["mode:AFK", "tier:slice"], "blocked_by": [], "state": "open", "_issue": _issue(50)},
        ]
        dispatch.main(["--sprint", "--source", "src/x", "--ledger", str(ledger)],
                      client=_created_client(), sprint_lister=lambda repo: cands)
        got = {r["slice_id"] for r in dispatch.load_ledger(ledger)}
        assert got == {"42", "50"}, f"43 done (skipped); 42 dep met -> expected {{42,50}}, got {got}"
    print("PASS"); return True


def test_dispatch_cli_sprint_dep_unmet():
    print("--- test_dispatch_cli_sprint_dep_unmet ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = Path(d) / ".memory" / "jules-ledger.jsonl"
        cands = [
            {"slice_id": "42", "labels": ["mode:AFK", "tier:slice"], "blocked_by": ["43"], "state": "open", "_issue": _issue(42, "Blocked-by: 43")},
            {"slice_id": "43", "labels": ["mode:AFK", "tier:slice"], "blocked_by": [], "state": "open", "_issue": _issue(43)},
            {"slice_id": "50", "labels": ["mode:AFK", "tier:slice"], "blocked_by": [], "state": "open", "_issue": _issue(50)},
        ]
        dispatch.main(["--sprint", "--source", "src/x", "--ledger", str(ledger)],
                      client=_created_client(), sprint_lister=lambda repo: cands)
        got = {r["slice_id"] for r in dispatch.load_ledger(ledger)}
        # 43 is open with no deps (itself eligible); 42's dep on 43 is unmet -> 42 excluded
        assert "42" not in got and got == {"43", "50"}, f"expected {{43,50}} with 42 excluded, got {got}"
    print("PASS"); return True


def test_dispatch_cli_dry_run_creates_nothing():
    print("--- test_dispatch_cli_dry_run_creates_nothing ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = Path(d) / ".memory" / "jules-ledger.jsonl"
        rc = ReplayCaller({("POST", "/sessions"): _fx("session_created.json")})
        dispatch.main(["--slice", "42", "--source", "src/x", "--ledger", str(ledger), "--dry-run"],
                      client=JulesClient(caller=rc), issue_fetcher=lambda s: _issue(42))
        assert not ledger.exists(), "dry-run must not write the ledger"
        assert not [c for c in rc.calls if c["method"] == "POST"], "dry-run must not create sessions"
    print("PASS"); return True


def test_status_cli_reports_and_flips():
    print("--- test_status_cli_reports_and_flips ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = Path(d) / ".memory" / "jules-ledger.jsonl"
        ledger.parent.mkdir(parents=True)
        ledger.write_text(json.dumps({"slice_id": "42", "session_id": "sess_abc123", "state": "DISPATCHED"}) + "\n", encoding="utf-8")
        client = JulesClient(caller=ReplayCaller({("GET", "/sessions/sess_abc123"): _fx("session_pr_ready.json")}))
        rc = status.main(["--ledger", str(ledger)], client=client, ci_fetcher=lambda u: "SUCCESS")
        assert rc == 0
        assert dispatch.load_ledger(ledger)[0]["state"] == "DONE"
    print("PASS"); return True


TESTS = [
    test_dispatch_cli_single, test_dispatch_cli_normalizes_name_only_session,
    test_dispatch_cli_sprint_dep_met, test_dispatch_cli_sprint_dep_unmet,
    test_dispatch_cli_dry_run_creates_nothing, test_status_cli_reports_and_flips,
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
