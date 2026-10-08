#!/usr/bin/env python3
"""BT-139 guards: 3d Phase 0.5 plan (persisted, mechanically checked), seams from the plan, deviations, 3z plan_path."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
PLAN_FILE = ".tmp/3d-plan-BT-<padded>.md"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def _phase(text: str, start: str, end: str) -> str:
    return text.split(start)[1].split(end)[0]


def test_3d_has_plan_phase_between_intake_and_tdd():
    text = _read("workflows/3d-implement-issue.md")
    assert "## Phase 0.5: Plan" in text
    assert text.index("## Phase 0:") < text.index("## Phase 0.5: Plan") < text.index("## Phase 1:")


def test_phase_0_hands_off_to_the_plan_not_past_it():
    phase0 = _phase(_read("workflows/3d-implement-issue.md"), "## Phase 0:", "## Phase 0.5:")
    assert "proceed to Phase 1" not in phase0
    assert "proceed to Phase 0.5" in phase0


def test_plan_phase_persists_plan_and_skips_only_cosmetic():
    plan = _phase(_read("workflows/3d-implement-issue.md"), "## Phase 0.5: Plan", "## Phase 1:")
    assert PLAN_FILE in plan
    assert "Fast-Track B" in plan and "cosmetic" in plan


def test_plan_phase_has_required_sections():
    plan = _phase(_read("workflows/3d-implement-issue.md"), "## Phase 0.5: Plan", "## Phase 1:")
    for section in ("[NEW]", "[MODIFY]", "seams to test", "AC → planned test path",
                    "existing tests at risk", "cross-cutting touchpoints", "memory IDs", "open decisions"):
        assert section in plan, section


def test_plan_phase_adds_no_review_halt_and_stays_host_neutral():
    plan = _phase(_read("workflows/3d-implement-issue.md"), "## Phase 0.5: Plan", "## Phase 1:")
    assert "no extra review halt" in plan
    assert "AFK" in plan and "no approval" in plan
    assert "the host's native planning mode" in plan
    for tool in ("EnterPlanMode", "ExitPlanMode", "AskUserQuestion"):
        assert tool not in plan, "plan phase must not require a host-specific tool name"


def test_plan_phase_mechanical_check_uses_repo_test_paths():
    plan = _phase(_read("workflows/3d-implement-issue.md"), "## Phase 0.5: Plan", "## Phase 1:")
    assert "git ls-files" in plan
    assert "Every AC needs a planned test path matching" in plan
    assert "every planned test path must match one" in plan


def test_phase_1_takes_seams_from_the_plan():
    phase1 = _phase(_read("workflows/3d-implement-issue.md"), "## Phase 1:", "## Phase 2:")
    assert "Declare Seam takes the seams from the plan" in phase1


def test_phase_3_compares_coverage_map_with_plan_and_writes_deviations():
    phase3 = _read("workflows/3d-implement-issue.md").split("## Phase 3:")[1]
    assert "Compare the coverage map with the plan's AC → test list" in phase3
    assert "## Deviations" in phase3
    assert PLAN_FILE in phase3


def test_3z_dispatch_json_has_plan_path_and_report_lists_it():
    text = _read("workflows/3z-afk-loop.md")
    step_2a = text.split("### Step 2A")[1].split("### Step 2B")[0]
    assert "plan_path" in step_2a
    phase4 = text.split("## Phase 4:")[1]
    assert "plan_path" in phase4


def test_plan_check_allows_an_explicit_uncovered_row_with_a_reason():
    """Phase 3 already allows `[UNCOVERED]`; the plan check must not force a test path for an AC that cannot have one."""
    plan = _phase(_read("workflows/3d-implement-issue.md"), "## Phase 0.5: Plan", "## Phase 1:")
    check = plan.split("**Mechanical plan check")[1]
    assert "[UNCOVERED]" in check, "plan check must accept an explicit [UNCOVERED] plan row"
    assert "reason" in check and "manual-only" in check and "design blocker" in check
    phase3 = _read("workflows/3d-implement-issue.md").split("## Phase 3:")[1]
    assert "[UNCOVERED]" in phase3 and "design blocker" in phase3


def test_plan_check_skips_the_filename_pattern_match_for_a_greenfield_repo():
    plan = _phase(_read("workflows/3d-implement-issue.md"), "## Phase 0.5: Plan", "## Phase 1:")
    check = plan.split("**Mechanical plan check")[1]
    assert "greenfield" in check and "no test files" in check
    assert "skip" in check and "say so" in check
