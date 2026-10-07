#!/usr/bin/env python3
"""BT-152 guards: micro-tdd routes each change, localizes unclear bugs, and reports stuck to 3d/3z."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    return text.split(start)[1].split(end)[0]


def _route_rows():
    route = _section(_read("skills/micro-tdd/SKILL.md"), "## 2. Route", "## 3.")
    return [m.group(1) for m in re.finditer(r"^\| \*\*(\w+)\*\* \|", route, re.M)], route


def test_route_table_orders_risk_first_and_has_every_route():
    rows, _ = _route_rows()
    assert rows == ["Risk", "Direct", "Visual", "Bug", "Logic"], rows


def test_direct_route_has_a_guard_and_falls_back_to_logic():
    _, route = _route_rows()
    assert "it is not Direct" in route
    assert "Unsure → Logic" in route


def test_risk_route_covers_every_4a_audit_category():
    """micro-tdd's Risk row and 4a's full-audit trigger must not drift apart."""
    _, route = _route_rows()
    risk_row = next(l for l in route.splitlines() if l.startswith("| **Risk**"))
    gate = _read("workflows/4a-verify-and-ship.md").split("## Phase 1:")[1].split("## Phase 2:")[0]
    step2 = next(l for l in gate.splitlines() if l.startswith("2. "))
    for category in ("security/RLS", "auth", "billing/entitlements", "core math/algorithms"):
        assert category in step2, f"4a step 2 no longer names {category}; update this guard"
        assert category in risk_row, category


def test_red_step_bans_tautological_expected_values():
    text = _read("skills/micro-tdd/SKILL.md")
    red = _section(text, "**Isolate & Specify (RED):**", "**Implement & Pass (GREEN):**")
    assert "independent source" in red
    assert "Name the break" in red


def test_bug_loop_localizes_an_unclear_cause_and_proves_the_regression():
    loop = _read("skills/micro-tdd/SKILL.md").split("### The Anti-Regression Bug Loop")[1]
    for token in ("red-capable command", "falsifiable", "cheapest", "[DEBUG-", "repro passes"):
        assert token in loop, token
    assert "revert the fix" in loop


def test_stuck_is_countable_and_returns_to_an_afk_caller():
    stuck = _section(_read("skills/micro-tdd/SKILL.md"), '### The "Stuck" Protocol', "### The Anti-Regression Bug Loop")
    assert "3 failed GREEN attempts" in stuck
    assert "exactly two" in stuck
    assert "`stuck: {reason, options}`" in stuck


def test_3d_phase_1_passes_risk_paths_and_handles_stuck():
    phase1 = _section(_read("workflows/3d-implement-issue.md"), "## Phase 1:", "## Phase 2:")
    assert "references/merge-risk-paths.md" in phase1
    assert "`stuck`" in phase1


def test_3z_returns_stuck_and_blocks_the_slice_on_it():
    text = _read("workflows/3z-afk-loop.md")
    step_2a = _section(text, "### Step 2A", "### Step 2B")
    assert '\\"stuck\\": null' in step_2a
    gate = _section(text, "### Step 2C", "## Phase 3:")
    stuck = next(l for l in gate.splitlines() if "`stuck`" in l)
    assert '--add-label "status:blocked"' in stuck
    assert "gh issue comment" in stuck
