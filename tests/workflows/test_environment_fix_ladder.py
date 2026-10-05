#!/usr/bin/env python3
"""BT-141 guards: 0b environment-fix ladder, friction gate, one-proposal cap, post_merge follow-ups;
4c guardrail and test-suite-health lens."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
DIST = ROOT / "dist" / "skills"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def test_ladder_reference_has_six_rungs_and_the_three_rules():
    text = _read("references/environment-fix-ladder.md")
    for rung in ("Deterministic check", "Reviewer standard", "Existing law",
                 "Framework issue", "Issue / `STATUS.md`", "`LEARNINGS.md`"):
        assert rung in text, rung
    assert "Escalation" in text
    assert "Evidence rule" in text
    assert "Hypothesis rule" in text
    assert "references/" not in text.split("Reviewer standard")[1].split("Existing law")[0], \
        "rung 2 must name CODING_STANDARDS bare filenames, never a references/ prefix"


def test_0b_cites_the_ladder_and_gates_learnings_on_friction():
    text = _read("workflows/0b-stop-session.md")
    assert "references/environment-fix-ladder.md" in text
    assert "friction" in text
    assert "what would have prevented it" in text


def test_0b_caps_learnings_proposals_and_tombstones_removals():
    text = _read("workflows/0b-stop-session.md")
    assert "at most one" in text
    assert "[REMOVED]" in text
    assert "never reused" in text


def test_0b_proposes_follow_ups_from_post_merge_with_full_label_set():
    text = _read("workflows/0b-stop-session.md")
    assert "post_merge" in text
    assert "stratos-pr" in text
    for label in ("type:maintenance", "mode:HITL", "tier:slice", "size:small", "status:planned"):
        assert label in text, label
    assert "Follow-ups proposed:" in text


def test_memory_protocol_defines_the_tombstone():
    text = _read("rules/memory-protocol.md")
    assert "never reused" in text
    assert "- **[[L-xxx]] [REMOVED] [YYYY-MM-DD]** Reason:" in text


def test_build_ships_the_ladder_into_0b():
    assert (DIST / "0b-stop-session" / "references" / "environment-fix-ladder.md").is_file()


def test_scan_matrix_b2_names_both_new_checks():
    text = _read("references/health-audit-scan-matrix.md")
    b2 = text.split("### B2")[1].split("## Subagent C")[0]
    assert "Guardrail" in b2
    assert "Test-suite health" in b2
    assert "concurrency" in b2
    assert "runner summary" in b2


def test_4c_phase_1_passes_ci_and_hook_files_to_the_quality_auditor():
    text = _read("workflows/4c-codebase-health-audit.md")
    phase1 = text.split("## Phase 1")[1].split("## Phase 2")[0]
    assert ".github/workflows" in phase1
