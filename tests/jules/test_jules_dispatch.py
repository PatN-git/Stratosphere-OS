#!/usr/bin/env python3
"""Offline tests for config / preflight / dispatch (P2+P3). No network, no key.

Run: python tests/test_jules_dispatch.py
"""
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
from test_jules import ReplayCaller, _fx  # sets sys.path for the pack + reuses caller

import config          # noqa: E402
import preflight       # noqa: E402
import dispatch        # noqa: E402
from jules_api import JulesClient, JulesError  # noqa: E402

GOOD_ISSUE = {"number": 42, "title": "BT-0042: add a comment",
              "body": "Do X.\n\n## Acceptance Criteria\n- a comment is added",
              "labels": [{"name": "mode:AFK"}, {"name": "tier:slice"}], "state": "OPEN"}


def _client():
    return JulesClient(caller=ReplayCaller({("POST", "/sessions"): _fx("session_created.json")}))


# ---- P2: config ----
def test_config_missing_key_fails_closed():
    print("--- test_config_missing_key_fails_closed ---")
    with tempfile.TemporaryDirectory() as d:
        try:
            config.load_api_key(project_root=d, env={})
        except JulesError as e:
            assert "JULES_API_KEY" in e.message
            print("PASS"); return True
    raise AssertionError("expected JulesError when key absent")


def test_config_reads_dotenv():
    print("--- test_config_reads_dotenv ---")
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".env.local").write_text('JULES_API_KEY="fake-key-123"\nOTHER=x\n', encoding="utf-8")
        assert config.load_api_key(project_root=d, env={}) == "fake-key-123"
    print("PASS"); return True


def test_env_beats_dotenv():
    print("--- test_env_beats_dotenv ---")
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".env.local").write_text("JULES_API_KEY=from-dotenv\n", encoding="utf-8")
        assert config.load_api_key(project_root=d, env={"JULES_API_KEY": "from-env"}) == "from-env"
    print("PASS"); return True


# ---- P2: preflight ----
def test_preflight_eligible_and_ineligible():
    print("--- test_preflight_eligible_and_ineligible ---")
    assert preflight.preflight("BT-0042", fetcher=lambda s: GOOD_ISSUE).ok
    epic = dict(GOOD_ISSUE, labels=[{"name": "mode:AFK"}, {"name": "tier:epic"}])
    assert not preflight.preflight("BT-1", fetcher=lambda s: epic).ok
    no_afk = dict(GOOD_ISSUE, labels=[{"name": "tier:slice"}])
    assert not preflight.preflight("BT-2", fetcher=lambda s: no_afk).ok
    no_ac = dict(GOOD_ISSUE, body="just do it")
    assert not preflight.preflight("BT-3", fetcher=lambda s: no_ac).ok
    spike = dict(GOOD_ISSUE, labels=GOOD_ISSUE["labels"] + [{"name": "status:needs_spec"}])
    assert not preflight.preflight("BT-4", fetcher=lambda s: spike).ok
    print("PASS"); return True


# ---- P3: dispatch ----
def test_dispatch_one_writes_ledger():
    print("--- test_dispatch_one_writes_ledger ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = Path(d) / ".memory" / "jules-ledger.jsonl"
        row = dispatch.dispatch_one(_client(), "src/x", "BT-0042", GOOD_ISSUE, ledger,
                                    starting_branch="main", now="2026-07-15T09:00:00Z")
        assert row["state"] == "DISPATCHED" and row["session_id"] == "sess_abc123"
        rows = dispatch.load_ledger(ledger)
        assert len(rows) == 1 and rows[0]["slice_id"] == "BT-0042"
    print("PASS"); return True


def test_dispatch_idempotent():
    print("--- test_dispatch_idempotent ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = Path(d) / ".memory" / "jules-ledger.jsonl"
        rc = ReplayCaller({("POST", "/sessions"): _fx("session_created.json")})
        c = JulesClient(caller=rc)
        dispatch.dispatch_one(c, "src/x", "BT-0042", GOOD_ISSUE, ledger, now="t")
        second = dispatch.dispatch_one(c, "src/x", "BT-0042", GOOD_ISSUE, ledger, now="t")
        assert second.get("noop") is True
        posts = [x for x in rc.calls if x["method"] == "POST"]
        assert len(posts) == 1, f"expected 1 create, got {len(posts)}"
        assert len(dispatch.load_ledger(ledger)) == 1
    print("PASS"); return True


def test_dispatch_many_partial_failure_and_cap():
    print("--- test_dispatch_many_partial_failure_and_cap ---")
    with tempfile.TemporaryDirectory() as d:
        ledger = Path(d) / ".memory" / "jules-ledger.jsonl"

        # caller fails only for slice BT-BAD (body marker), succeeds otherwise
        def caller(method, path, body=None, query=None):
            if method == "POST" and "BT-BAD" in (body or {}).get("title", ""):
                raise JulesError(500, "injected server error")
            return _fx("session_created.json")

        c = JulesClient(caller=caller)
        items = [("BT-1", GOOD_ISSUE), ("BT-BAD", GOOD_ISSUE), ("BT-3", GOOD_ISSUE), ("BT-4", GOOD_ISSUE)]
        results = dispatch.dispatch_many(c, "src/x", items, ledger, max_sessions=2, now="t")
        states = {r["slice_id"]: r["state"] for r in results}
        assert states["BT-BAD"] == "FAILED", states
        assert states["BT-1"] == "DISPATCHED", states
        # cap=2 successful dispatches; BT-BAD failed (doesn't count), so BT-3 dispatches, BT-4 capped
        assert states["BT-4"] == "SKIPPED_CAP", states
    print("PASS"); return True


def test_select_eligible_dep_exclusion():
    print("--- test_select_eligible_dep_exclusion ---")
    slices = [
        {"slice_id": "BT-1", "labels": ["mode:AFK", "tier:slice"], "blocked_by": []},
        {"slice_id": "BT-2", "labels": ["mode:AFK", "tier:slice"], "blocked_by": ["BT-404"]},  # unmet dep (BT-404 not done)
        {"slice_id": "BT-3", "labels": ["mode:AFK", "tier:epic"]},                             # epic
        {"slice_id": "BT-4", "labels": ["tier:slice"]},                                        # no AFK
        {"slice_id": "BT-9", "labels": ["mode:AFK", "tier:slice"], "state": "done"},
        {"slice_id": "BT-5", "labels": ["mode:AFK", "tier:slice"], "blocked_by": ["BT-9"]},   # dep met
        {"slice_id": "BT-6", "labels": ["mode:AFK", "tier:slice", "status:needs_spec"]},  # Spike
    ]
    got = {s["slice_id"] for s in dispatch.select_eligible(slices)}
    assert got == {"BT-1", "BT-5"}, got
    print("PASS"); return True


def _gh_list_stub(monkeypatch_target, issues):
    """Fake `gh issue list` output for _sprint_candidates (no network)."""
    class _R:
        returncode, stderr = 0, ""
        stdout = json.dumps(issues)
    monkeypatch_target.run = lambda *a, **k: _R()


def _blocked_pair(blocker_state="CLOSED"):
    blocker = {"number": 43, "title": "t", "body": "x", "state": blocker_state,
               "labels": [{"name": "mode:AFK"}, {"name": "tier:slice"}]}
    dep = {"number": 42, "title": "t", "body": "Blocked-by: 43", "state": "OPEN",
           "labels": [{"name": "mode:AFK"}, {"name": "tier:slice"}]}
    return [dep, blocker]


def _eligible_ids(pr_state, blocker_state="CLOSED", looked_up=None):
    """Run _sprint_candidates -> select_eligible with reconcile.pr_merge_state stubbed to `pr_state`."""
    import subprocess

    class _Rec:
        @staticmethod
        def pr_merge_state(bt, cache=None):
            if looked_up is not None:
                looked_up.append((bt, cache is not None))
            return pr_state

    orig_run, orig_load = subprocess.run, dispatch._load_reconcile
    try:
        _gh_list_stub(subprocess, _blocked_pair(blocker_state))
        dispatch._load_reconcile = lambda: _Rec
        return {s["slice_id"] for s in dispatch.select_eligible(dispatch._sprint_candidates())}
    finally:
        subprocess.run, dispatch._load_reconcile = orig_run, orig_load


def test_closed_blocker_gated_on_pr_merge_state():
    print("--- test_closed_blocker_gated_on_pr_merge_state ---")
    assert "42" not in _eligible_ids("open"), "closed blocker with an unmerged PR must keep dependent ineligible"
    assert "42" in _eligible_ids("merged")
    assert "42" in _eligible_ids("none"), "closed with no PR comment (spike/manual close) is satisfied"
    assert "42" not in _eligible_ids(None), "gh failure -> not done"
    print("PASS"); return True


def test_closed_unmerged_blocker_never_redispatched():
    print("--- test_closed_unmerged_blocker_never_redispatched ---")
    got = _eligible_ids("open")
    assert "43" not in got, f"a closed issue must never be dispatch-eligible: {got}"
    print("PASS"); return True


def test_open_blocker_unchanged_and_no_lookup():
    print("--- test_open_blocker_unchanged_and_no_lookup ---")
    seen = []
    got = _eligible_ids("merged", blocker_state="OPEN", looked_up=seen)
    assert "42" not in got and "43" in got, got
    assert seen == [], f"open blockers need no PR lookup: {seen}"
    print("PASS"); return True


def test_lookup_only_for_blockers_with_shared_cache():
    print("--- test_lookup_only_for_blockers_with_shared_cache ---")
    import subprocess
    calls = []
    issues = _blocked_pair() + [
        {"number": 99, "title": "t", "body": "y", "state": "CLOSED", "labels": [{"name": "mode:AFK"}]},  # closed, not a blocker
        {"number": 44, "title": "t", "body": "Blocked-by: 43", "state": "OPEN", "labels": [{"name": "mode:AFK"}]},
    ]

    class _Rec:
        @staticmethod
        def pr_merge_state(bt, cache=None):
            calls.append((bt, id(cache)))
            return "merged"

    orig_run, orig_load = subprocess.run, dispatch._load_reconcile
    try:
        _gh_list_stub(subprocess, issues)
        dispatch._load_reconcile = lambda: _Rec
        dispatch._sprint_candidates()
    finally:
        subprocess.run, dispatch._load_reconcile = orig_run, orig_load
    assert [c[0] for c in calls] == ["BT-43"], calls
    assert calls[0][1] != id(None), "a cache dict must be passed"
    print("PASS"); return True


def test_load_reconcile_resolves_sibling_scripts_dir():
    print("--- test_load_reconcile_resolves_sibling_scripts_dir ---")
    rec = dispatch._load_reconcile()
    assert callable(rec.pr_merge_state), "reconcile.py must be reachable from the pack (../../scripts)"
    print("PASS"); return True


# ---- P2: secret hygiene / log-scan ----
def test_secret_never_logged():
    print("--- test_secret_never_logged ---")
    FAKE = "AIzaFAKEKEY_shouldnotappear_0000"
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".env.local").write_text(f"JULES_API_KEY={FAKE}\n", encoding="utf-8")
        ledger = Path(d) / ".memory" / "jules-ledger.jsonl"
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            key = config.load_api_key(project_root=d, env={})
            # client built from the key, but ReplayCaller used so no real HTTP; the key
            # would only ever surface via a header we never print.
            c = JulesClient(caller=ReplayCaller({("POST", "/sessions"): _fx("session_created.json")}))
            dispatch.dispatch_one(c, "src/x", "BT-0042", GOOD_ISSUE, ledger, now="t")
            print(config.safe_log(f"debug: key={key}", key))  # even if someone logs it, scrub
        combined = buf_out.getvalue() + buf_err.getvalue() + ledger.read_text(encoding="utf-8")
        assert FAKE not in combined, "API key leaked into stdout/stderr/ledger!"
        assert "***REDACTED***" in buf_out.getvalue()
    print("PASS"); return True


def test_merge_state_reads_the_named_repo_and_restores_gh_repo():
    """--repo X: the PR lookup runs with GH_REPO=X (gh reads it), and the caller's GH_REPO is restored."""
    import os
    seen = []

    class Rec:
        @staticmethod
        def pr_merge_state(bt, cache):
            seen.append((bt, os.environ.get("GH_REPO")))
            return "merged"

    prev = os.environ.pop("GH_REPO", None)
    try:
        assert dispatch._merge_state(Rec, 70, {}, "owner/other") == "merged"
        assert seen[-1] == ("BT-70", "owner/other")
        assert "GH_REPO" not in os.environ
        os.environ["GH_REPO"] = "owner/mine"
        dispatch._merge_state(Rec, 71, {}, "owner/other")
        assert os.environ["GH_REPO"] == "owner/mine"
        dispatch._merge_state(Rec, 72, {})
        assert seen[-1] == ("BT-72", "owner/mine")
    finally:
        os.environ.pop("GH_REPO", None)
        if prev is not None:
            os.environ["GH_REPO"] = prev
    print("PASS"); return True


TESTS = [
    test_merge_state_reads_the_named_repo_and_restores_gh_repo,
    test_config_missing_key_fails_closed, test_config_reads_dotenv, test_env_beats_dotenv,
    test_preflight_eligible_and_ineligible,
    test_dispatch_one_writes_ledger, test_dispatch_idempotent,
    test_dispatch_many_partial_failure_and_cap, test_select_eligible_dep_exclusion,
    test_secret_never_logged,
    test_closed_blocker_gated_on_pr_merge_state, test_closed_unmerged_blocker_never_redispatched,
    test_open_blocker_unchanged_and_no_lookup, test_lookup_only_for_blockers_with_shared_cache,
    test_load_reconcile_resolves_sibling_scripts_dir,
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
