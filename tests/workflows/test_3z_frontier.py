#!/usr/bin/env python3
"""BT-140 guards: 3z frontier skip, workspace/depth guardrails, AGENTS.md subagent-nesting contract.

Deliberately reads the real workflow text; `test_3z_orchestrator_simulation.py` mocks 3z and never does.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
Z = (ROOT / "src" / "workflows" / "3z-afk-loop.md").read_text(encoding="utf-8")


def _section(text, start, end=None):
    """Text from heading `start` up to heading `end` (or EOF)."""
    i = text.index(start)
    j = text.index(end, i) if end else len(text)
    return text[i:j]


def test_skip_dep_in_step_2a():
    step_2a = _section(Z, "### Step 2A", "### Step 2B")
    assert "[SKIP-DEP]" in step_2a, "Step 2A has no [SKIP-DEP] frontier check"
    assert "Frontier check" in step_2a
    assert step_2a.index("Frontier check") < step_2a.index("Activate Slice"), \
        "frontier check must run before the slice is activated"
    assert "VERIFIED-LOCAL" in step_2a and "status:in review" in step_2a


def test_skip_dep_leaves_status_unchanged():
    step_2a = _section(Z, "### Step 2A", "### Step 2B")
    assert re.search(r"status unchanged|do \*\*not\*\* mark it blocked", step_2a)


def test_skip_dep_is_a_terminal_state():
    done = re.search(r"_Loop done when[^\n]*", Z).group(0)
    assert "SKIP-DEP" in done, f"terminal-state list omits SKIP-DEP: {done}"


def test_skip_dep_keeps_feature_local():
    step_3a = _section(Z, "### Step 3A", "### Step 3B")
    assert "SKIP-DEP" in step_3a, "a feature with a SKIP-DEP slice must stay local"


def test_skip_dep_in_phase_4_report():
    phase_4 = _section(Z, "## Phase 4", "## Phase 5")
    assert "SKIP-DEP" in phase_4, "Phase 4 must list SKIP-DEP slices"


def test_3z_workspace_and_depth_guardrails():
    guard = _section(Z, "## Authority & Guardrails", "## Phase 1")
    assert "shared/inherit" in guard, "3z guardrails lack the shared/inherit workspace bullet"
    assert "worktree" in guard
    assert re.search(r"at most one (further|more) level", guard), "3z guardrails lack the depth budget"


def test_agents_files_define_subagent_nesting():
    for rel in ("src/constitution/AGENTS.md", "AGENTS.md"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "Subagent nesting" in text, f"{rel} lacks the Subagent nesting paragraph"
        para = _section(text, "Subagent nesting", "\n- **HITL enforcement")
        for needle in ("depth", "inline", "commit", "shared/inherit"):
            assert needle in para, f"{rel}: Subagent nesting paragraph omits {needle!r}"


def test_3z_bootstrap_line_does_not_require_0a_for_subagents():
    guard = _section(Z, "## Authority & Guardrails", "## Phase 1")
    assert "bootstrapped by `/0a" not in guard
    assert "self-hydrates" in guard


def test_3z_ship_only_halts_leave_the_slice_local_and_continue():
    step_3a = _section(Z, "### Step 3A", "### Step 3B")
    for halt in ("[UNCOMMITTED]", "[DRAFT-RULE]", "[MIRROR-UNVERIFIED]", "Feature Acceptance Audit"):
        assert halt in step_3a, halt
    assert "[BLOCKED-ship] <the halt message>" in step_3a
    assert "continue" in step_3a


def test_3z_step_1b_approval_preauthorizes_the_ship_confirmation():
    step_3a = _section(Z, "### Step 3A", "### Step 3B")
    assert "Step 1B" in step_3a and "Phase 5 step 3" in step_3a


def test_3z_report_tells_how_to_resume_a_skip_dep_feature():
    phase_4 = _section(Z, "## Phase 4", "## Phase 5")
    assert "re-run /3z after BT-<blocker> reaches in review" in phase_4
