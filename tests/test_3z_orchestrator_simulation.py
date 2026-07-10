#!/usr/bin/env python3
"""Simulation harness for 3z_afk-loop workflow state machine.

Simulates orchestrator execution across multiple mock slices:
1. BT-101 (execution_mode:AFK): Passes implementation and audit on Attempt 1.
2. BT-102 (execution_mode:AFK): Fails audit on Attempt 1 ([UNCOVERED] gap), self-heals on Attempt 2.
3. BT-103 (execution_mode:AFK): Fails audit 3 times consecutively -> flags status:blocked.
4. BT-104 (execution_mode:HITL): Excluded by Step 1B AFK pre-flight ([SKIP]).
5. BT-105 (execution_mode:AFK): Cosmetic slice -> returns [SKIP] -> treats as VERIFIED immediately.
6. BT-106 (no execution_mode): Excluded by Step 1B preflight.

Verifies queue grouping, retry attempts, feature ship qualification, conflict flagging,
and branch checkout simulations.
"""
import json
import sys

class MockSubagentResponse:
    def __init__(self, verdict, coverage_map, commit_sha="commit_123", needs_manual_qa=False):
        self.verdict = verdict
        self.coverage_map = coverage_map
        self.commit_sha = commit_sha
        self.needs_manual_qa = needs_manual_qa

class MockOrchestrator:
    def __init__(self, slices, ship_mode="auto-PR"):
        self.slices = slices
        self.ship_mode = ship_mode
        self.results = {}
        self.features = {}
        self.git_log = []

    def step_1b_preflight(self):
        kept = []
        skipped = []
        for s in self.slices:
            # Unknown/closed preflight check simulator
            if s.get("closed") or s.get("nonexistent"):
                raise ValueError(f"[ERROR] {s['id']} not found or closed")
                
            exec_mode = s.get("execution_mode")
            if exec_mode == "AFK":
                kept.append(s)
            elif exec_mode == "HITL":
                skipped.append(f"[SKIP] {s['id']} mode:HITL - excluded")
            else:
                skipped.append(f"[SKIP] {s['id']} no execution mode - excluded")

            # Gated single issue checks
            if len(self.slices) == 1:
                if exec_mode == "HITL":
                    raise ValueError("HALT: run /3d_implement-issue + /4a_verify-and-ship manually")
                elif not exec_mode:
                    raise ValueError("HALT: requires execution mode mode:AFK or mode:HITL to be run")

        # Group by parent feature and order
        grouped = sorted(kept, key=lambda x: (x["parent"], x.get("dep_order", 0), x["id"]))
        return grouped, skipped

    def run_slice_loop(self, queue, mock_responder):
        for s in queue:
            sid = s["id"]
            attempt = 1
            max_attempts = 3
            uncovered_report = None
            
            while attempt <= max_attempts:
                # Step 2A: Implement (sets status:in progress)
                impl_res = mock_responder.implement(sid, attempt, uncovered_report)
                
                # Step 2B: Verify
                audit_res = mock_responder.audit(sid, attempt, impl_res)
                
                # Step 2C: Decision gate
                if audit_res.verdict == "[PASS]" or audit_res.verdict == "[SKIP]":
                    status_verdict = "VERIFIED" if self.ship_mode == "auto-PR" else "VERIFIED-LOCAL"
                    self.results[sid] = {
                        "status": status_verdict,
                        "attempts": attempt,
                        "commit": impl_res.get("commit_shas", ["sha"])[-1],
                        "coverage": audit_res.coverage_map,
                        "cosmetic": audit_res.verdict == "[SKIP]",
                        "needs_manual_qa": impl_res.get("needs_manual_qa", False)
                    }
                    break
                else:
                    uncovered_report = audit_res.coverage_map
                    attempt += 1
            
            if attempt > max_attempts:
                self.results[sid] = {
                    "status": "BLOCKED",
                    "attempts": max_attempts,
                    "reason": f"Persistent gaps: {uncovered_report}"
                }
                # C2.1: Set status:blocked label on GitHub issue at circuit-break
                self.git_log.append(f"gh issue edit {sid} --remove-label status:in progress --add-label status:blocked")

    def phase_3_ship(self, queue):
        # Group slices by parent feature
        feature_slices = {}
        for s in queue:
            p = s["parent"]
            feature_slices.setdefault(p, []).append(s["id"])

        shipped_features = {}
        for feat, sids in feature_slices.items():
            all_verified = all(self.results[sid]["status"] in ("VERIFIED", "VERIFIED-LOCAL") for sid in sids)
            if all_verified:
                if self.ship_mode == "auto-PR":
                    # B2.1: Check out feature branch before shipping
                    feature_branch = f"feature/BT-{feat}"
                    self.git_log.append(f"git checkout {feature_branch}")
                    shipped_features[feat] = f"PR #{hash(feat) % 100 + 10}"
                else:
                    shipped_features[feat] = "local (verified-local, no PR ops)"
            else:
                reason = "local-only mode" if self.ship_mode != "auto-PR" else "blocked slice present"
                shipped_features[feat] = f"local ({reason})"
        return shipped_features


class ScenarioMockResponder:
    def implement(self, sid, attempt, gap_report):
        needs_qa = (sid == "BT-101")
        return {
            "files_changed": [f"src/{sid}.py"],
            "tests_added": [] if sid == "BT-105" else [f"tests/test_{sid}.py"],
            "commit_shas": [f"{sid}_att{attempt}"],
            "ac_self_coverage": {"AC1": "test_1"},
            "needs_manual_qa": needs_qa
        }

    def audit(self, sid, attempt, impl_res):
        if sid == "BT-101":
            return MockSubagentResponse("[PASS]", {"AC1": "test_1"})
        elif sid == "BT-102":
            if attempt == 1:
                return MockSubagentResponse("[UNCOVERED]", {"AC1": "[UNCOVERED] missing edge test"})
            return MockSubagentResponse("[PASS]", {"AC1": "test_edge"})
        elif sid == "BT-103":
            return MockSubagentResponse("[UNCOVERED]", {"AC1": "[UNCOVERED] unresolved architectural dependency"})
        elif sid == "BT-105":
            return MockSubagentResponse("[SKIP]", {}) # cosmetic bypass
        return MockSubagentResponse("[PASS]", {})


def test_simulation(ship_mode="auto-PR"):
    raw_backlog = [
        {"id": "BT-101", "parent": "FEAT-10", "execution_mode": "AFK", "dep_order": 1},
        {"id": "BT-102", "parent": "FEAT-10", "execution_mode": "AFK", "dep_order": 2},
        {"id": "BT-103", "parent": "FEAT-20", "execution_mode": "AFK", "dep_order": 1},
        {"id": "BT-104", "parent": "FEAT-20", "execution_mode": "HITL", "dep_order": 2},
        {"id": "BT-105", "parent": "FEAT-10", "execution_mode": "AFK", "dep_order": 3},
        {"id": "BT-106", "parent": "FEAT-20", "dep_order": 3}, # no execution mode
    ]

    orch = MockOrchestrator(raw_backlog, ship_mode=ship_mode)
    queue, skipped = orch.step_1b_preflight()
    
    assert any("BT-104" in x and "mode:HITL" in x for x in skipped), "HITL slice BT-104 should be skipped"
    assert any("BT-106" in x and "no execution mode" in x for x in skipped), "BT-106 with no execution mode should be skipped"
    assert len(queue) == 4, "Only AFK slices should be queued"

    responder = ScenarioMockResponder()
    orch.run_slice_loop(queue, responder)

    # Verify results
    terminal_pass = "VERIFIED" if ship_mode == "auto-PR" else "VERIFIED-LOCAL"
    assert orch.results["BT-101"]["status"] == terminal_pass and orch.results["BT-101"]["attempts"] == 1
    assert orch.results["BT-102"]["status"] == terminal_pass and orch.results["BT-102"]["attempts"] == 2
    assert orch.results["BT-103"]["status"] == "BLOCKED" and orch.results["BT-103"]["attempts"] == 3
    assert orch.results["BT-105"]["status"] == terminal_pass and orch.results["BT-105"]["cosmetic"] is True

    # C2.1 Assertion: verify status:blocked label transition command was logged
    assert f"gh issue edit BT-103 --remove-label status:in progress --add-label status:blocked" in orch.git_log

    # Verify ship pass
    shipped = orch.phase_3_ship(queue)
    if ship_mode == "auto-PR":
        assert "PR #" in shipped["FEAT-10"], "FEAT-10 should have a PR"
        assert f"git checkout feature/BT-FEAT-10" in orch.git_log, "Must check out feature branch before shipping"
    else:
        assert "PR #" not in shipped["FEAT-10"]
        assert "local" in shipped["FEAT-10"]
        
    assert "local" in shipped["FEAT-20"], "FEAT-20 should stay local"

    print(f"=== 3z_afk-loop Simulation Test PASSED ({ship_mode}) ===")
    print("Skipped:", skipped)
    print("Slice Results:", json.dumps(orch.results, indent=2))
    print("Feature Ship Status:", json.dumps(shipped, indent=2))
    print("Git operations:", orch.git_log)

def run_tests():
    # Run auto-PR mode simulation
    test_simulation("auto-PR")
    print()
    # Run local-only mode simulation
    test_simulation("local-only")

    # Verify unknown/closed preflight check throws
    raw_backlog_invalid = [{"id": "BT-999", "parent": "FEAT-99", "execution_mode": "AFK", "closed": True}]
    orch = MockOrchestrator(raw_backlog_invalid)
    try:
        orch.step_1b_preflight()
        print("FAIL: Expected ValueError for closed issue BT-999")
        sys.exit(1)
    except ValueError as e:
        assert "not found or closed" in str(e)
        print("Pass: Preflight correctly raised error for closed issue.")

    # Verify single HITL preflight check throws
    raw_backlog_single_hitl = [{"id": "BT-888", "parent": "FEAT-88", "execution_mode": "HITL"}]
    orch = MockOrchestrator(raw_backlog_single_hitl)
    try:
        orch.step_1b_preflight()
        print("FAIL: Expected ValueError for single HITL issue")
        sys.exit(1)
    except ValueError as e:
        assert "run /3d_implement-issue" in str(e)
        print("Pass: Preflight correctly raised error for single HITL issue.")

    # Verify single missing mode preflight check throws
    raw_backlog_single_missing = [{"id": "BT-777", "parent": "FEAT-77"}]
    orch = MockOrchestrator(raw_backlog_single_missing)
    try:
        orch.step_1b_preflight()
        print("FAIL: Expected ValueError for single missing mode issue")
        sys.exit(1)
    except ValueError as e:
        assert "requires execution mode" in str(e)
        print("Pass: Preflight correctly raised error for single missing mode issue.")

if __name__ == "__main__":
    run_tests()
