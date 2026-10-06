#!/usr/bin/env python3
"""BT-142 guards: 0d is a drift-only advisor with scripted indices, sampling and a decisions record."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEXT = (ROOT / "src" / "workflows" / "0d-nightly-consolidation.md").read_text(encoding="utf-8")


def _phase(start: str, end: str) -> str:
    return TEXT.split(start)[1].split(end)[0]


def test_calls_the_scripts_instead_of_reasoning():
    assert "python .agents/scripts/reconcile.py --all-open" in TEXT
    assert "python .agents/scripts/okf_view.py --rebuild-indices" in TEXT
    assert "verbatim" in _phase("Backlog Drift Check", "## Phase 4")


def test_planning_advisor_is_gone_but_the_no_lifecycle_guard_stays():
    assert "Recommendation (evaluate in this order" not in TEXT
    assert "also pending" not in TEXT
    assert "/3a-version-planning" not in TEXT and "ROADMAP" not in TEXT
    assert "Planning-State Advisor" not in TEXT
    assert "Backlog Drift Check" in TEXT
    assert "This phase invokes no lifecycle skill." in TEXT


def test_description_says_backlog_drift():
    head = TEXT.split("---")[1]
    assert "check backlog drift" in head and "roadmap health" not in head


def test_phase1_ladder_sampling_and_lean_report():
    phase1 = _phase("## Phase 1", "## Phase 2")
    assert "references/environment-fix-ladder.md" in phase1
    assert "~15" in phase1 and "5 with the most failed tool calls" in phase1 and "3 random" in phase1
    assert "roster" in phase1 and "positive observations" in phase1  # named so they stay out of the report


def test_watermark_is_last_run_only():
    assert "sessions_reviewed" not in TEXT
    assert '{"last_run": ' in _phase("## Phase 2", "## Phase 3: Crystallize")


def test_decisions_record_is_read_in_phase2_and_appended_in_phase4():
    phase2 = _phase("## Phase 2", "## Phase 3: Crystallize")
    assert "## Decisions" in phase2 and "declined" in phase2
    assert "`## Decisions`" in phase2 and "30 lines" in phase2 and "last 7" in phase2  # bounded read, not whole reports
    phase4 = TEXT.split("## Phase 4")[1]
    assert "## Decisions" in phase4 and "accepted" in phase4 and "declined" in phase4


def test_assumed_entries_aged_by_inline_date_and_superseded_not_deleted():
    phase3 = _phase("## Phase 3: Crystallize", "## Phase 3.5")
    assert "7 days" in phase3 and "[YYYY-MM-DD]" in phase3
    assert "5 sessions" not in phase3
    assert "Delete?" not in phase3
    assert "Supersede with" in phase3 and "[REMOVED]" in phase3


def test_drift_lines_are_numbered_proposal_items_with_a_heal_route():
    drift = _phase("Backlog Drift Check", "## Phase 4")
    assert "python .agents/scripts/reconcile.py --all-open" in drift and "verbatim" in drift
    assert "`D-1`" in drift and "`D-2`" in drift
    assert "references/terminal-sync-invariant.md" in drift
    assert "approval" in drift


def test_decisions_cover_drift_items():
    phase4 = TEXT.split("## Phase 4")[1]
    assert "`D-n`" in phase4
    assert "BT id" in phase4


def test_constraint_is_scoped_to_the_workflows_own_writes():
    constraint = _phase("## Constraint", "## Phase 1")
    assert "Do not modify files without user approval" in constraint
    for write in ("report", ".last-run.json", "indices", "approved heals"):
        assert write in constraint, write


def test_decisions_read_is_host_neutral_and_cannot_hang_without_reports():
    """`grep ... $(ls docs/nightly/nightly-*.md | tail -7)` reads stdin when no report exists (hangs an unattended run) and is bash-only."""
    phase2 = _phase("## Phase 2", "## Phase 3: Crystallize")
    assert "$(ls" not in TEXT and "grep" not in phase2 and "tail -7" not in TEXT
    assert "docs/nightly/nightly-*.md" in phase2
    assert "none yet" in phase2 and "skip" in phase2
