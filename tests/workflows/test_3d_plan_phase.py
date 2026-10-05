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


def test_phase_1_takes_seams_from_the_plan():
    phase1 = _phase(_read("workflows/3d-implement-issue.md"), "## Phase 1:", "## Phase 2:")
    assert "Declare Seam" in phase1 and "plan" in phase1


def test_phase_3_compares_coverage_map_with_plan_and_writes_deviations():
    phase3 = _read("workflows/3d-implement-issue.md").split("## Phase 3:")[1]
    assert "## Deviations" in phase3
    assert PLAN_FILE in phase3


def test_micro_tdd_stays_generic():
    assert ".tmp/" not in _read("skills/micro-tdd/SKILL.md")


def test_3z_dispatch_json_has_plan_path_and_report_lists_it():
    text = _read("workflows/3z-afk-loop.md")
    step_2a = text.split("### Step 2A")[1].split("### Step 2B")[0]
    assert "plan_path" in step_2a
    phase4 = text.split("## Phase 4:")[1]
    assert "plan_path" in phase4
