#!/usr/bin/env python3
"""Offline tests for the jules-dispatch adapter (jules_api.py). No network, no key.

Run: python tests/test_jules.py
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src" / "experimental" / "jules-dispatch"))
import jules_api  # noqa: E402
from jules_api import JulesClient, JulesError  # noqa: E402

FIX = REPO_ROOT / "tests" / "fixtures" / "jules"


def _fx(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


class ReplayCaller:
    """Maps (method, path-prefix) -> fixture dict, or ('error', status[, retry_after]).
    Longest prefix wins so /sessions/x/activities beats /sessions/x. Records calls."""
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, method, path, body=None, query=None):
        self.calls.append({"method": method, "path": path, "body": body, "query": query})
        best = None
        for (m, pfx), val in self.routes.items():
            if m == method and path.startswith(pfx):
                if best is None or len(pfx) > len(best[0]):
                    best = (pfx, val)
        if best is None:
            raise JulesError(404, f"no route for {method} {path}")
        val = best[1]
        if isinstance(val, tuple) and val and val[0] == "error":
            raise JulesError(val[1], "injected", retry_after=(val[2] if len(val) > 2 else None))
        return val


def test_list_sources():
    print("--- test_list_sources ---")
    c = JulesClient(caller=ReplayCaller({("GET", "/sources"): _fx("sources.json")}))
    srcs = c.list_sources()
    assert len(srcs) >= 1 and srcs[0]["id"] == "github/PatN-git/cleantech_jobs"
    print("PASS"); return True


def test_create_session_payload():
    print("--- test_create_session_payload ---")
    rc = ReplayCaller({("POST", "/sessions"): _fx("session_created.json")})
    c = JulesClient(caller=rc)
    c.create_session("sources/github/PatN-git/cleantech_jobs",
                     "BT-0042: do the thing", title="BT-0042",
                     auto_pr=True, require_plan_approval=True, starting_branch="main")
    body = rc.calls[-1]["body"]
    assert body["automationMode"] == "AUTO_CREATE_PR", body
    assert body["requirePlanApproval"] is True, body
    assert body["title"] == "BT-0042"
    assert body["sourceContext"]["githubRepoContext"]["startingBranch"] == "main"
    assert body["prompt"], "prompt must be non-empty"
    print("PASS"); return True


def test_find_pr_url_ready():
    print("--- test_find_pr_url_ready ---")
    c = JulesClient(caller=ReplayCaller({("GET", "/sessions/sess_abc123"): _fx("session_pr_ready.json")}))
    url = c.find_pr_url("sess_abc123")
    assert url == "https://github.com/PatN-git/cleantech_jobs/pull/123", url
    print("PASS"); return True


def test_find_pr_url_running_is_none():
    print("--- test_find_pr_url_running_is_none ---")
    c = JulesClient(caller=ReplayCaller({("GET", "/sessions/sess_abc123"): _fx("session_running.json")}))
    assert c.find_pr_url("sess_abc123") is None
    print("PASS"); return True


def test_list_activities_forwards_since():
    print("--- test_list_activities_forwards_since ---")
    rc = ReplayCaller({("GET", "/sessions/sess_abc123/activities"): _fx("activities.json")})
    c = JulesClient(caller=rc)
    acts = c.list_activities("sess_abc123", since="2026-07-15T09:02:00Z")
    assert len(acts) == 2
    assert rc.calls[-1]["query"]["createTime"] == "2026-07-15T09:02:00Z", rc.calls[-1]["query"]
    print("PASS"); return True


def test_error_401():
    print("--- test_error_401 ---")
    c = JulesClient(caller=ReplayCaller({("GET", "/sources"): ("error", 401)}))
    try:
        c.list_sources()
    except JulesError as e:
        assert e.status == 401
        print("PASS"); return True
    raise AssertionError("expected JulesError(401)")


def test_error_429_carries_retry_after():
    print("--- test_error_429_carries_retry_after ---")
    c = JulesClient(caller=ReplayCaller({("POST", "/sessions"): ("error", 429, "30")}))
    try:
        c.create_session("src", "p")
    except JulesError as e:
        assert e.status == 429 and e.retry_after == "30", (e.status, e.retry_after)
        print("PASS"); return True
    raise AssertionError("expected JulesError(429) with retry_after")


def test_client_requires_key_or_caller():
    print("--- test_client_requires_key_or_caller ---")
    try:
        JulesClient()
    except JulesError:
        print("PASS"); return True
    raise AssertionError("expected JulesError when no key and no caller")


TESTS = [
    test_list_sources, test_create_session_payload, test_find_pr_url_ready,
    test_find_pr_url_running_is_none, test_list_activities_forwards_since,
    test_error_401, test_error_429_carries_retry_after, test_client_requires_key_or_caller,
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
