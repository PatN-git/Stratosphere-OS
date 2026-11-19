#!/usr/bin/env python3
"""Contract tests for smart multi-select and context-aware gate options (BT-284).

# md-crosscheck: lifecycle gate option contracts vs dist/ bundle and pr_body.VERDICTS
"""
import importlib.util
import re
from pathlib import Path

from conftest import REPO_ROOT, SRC, read_src

_spec = importlib.util.spec_from_file_location("pr_body", SRC / "scripts" / "pr_body.py")
pr_body = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr_body)

DIST_SKILLS = REPO_ROOT / "dist" / "skills"


def test_0b_resume_cleanup_empty_skip_and_multiselect():
    text = read_src("workflows/0b-stop-session.md")

    # Step 1 deletes .tmp/resume-BT-<n>.md after comment --body-file succeeds
    step1 = text.split("2. Update `.memory/STATUS.md`", 1)[0]
    assert re.search(r"delete\s+`?\.tmp/resume-BT-", step1, re.IGNORECASE), (
        "0b Step 1 must delete .tmp/resume-BT-<n>.md after posting comment"
    )
    assert re.search(r"comment[^\n]*--body-file[^\n]*succeeds|succeeds[^\n]*delete[^\n]*resume-BT", step1, re.IGNORECASE | re.S), (
        "0b Step 1 must sequence resume-file deletion after comment --body-file succeeds"
    )

    # Step 8b skips silently on zero non-exempt files and logs none / none (exempt only)
    step8b = text.split("8b.", 1)[1].split("\n9.", 1)[0]
    assert re.search(r"zero non-exempt|0 non-exempt", step8b, re.IGNORECASE), (
        "0b Step 8b must skip triage silently when zero non-exempt .tmp/ files exist"
    )
    assert "Tmp files triaged: none" in step8b and "none (exempt only)" in step8b, (
        "0b Step 8b must specify 'Tmp files triaged: none' and 'none (exempt only)' log values"
    )

    # Multi-select + per-file classification table + fallback + preserved exemptions
    output_mode = read_src("rules/output-mode.md")
    assert "multi-select" in step8b.lower() and ".agents/rules/output-mode.md" in step8b and "§5" in step8b, (
        "0b Step 8b must enable native multi-select via output-mode.md §5"
    )
    assert "is_multi_select: true" in output_mode and "multiSelect: true" in output_mode
    assert re.search(r"per-file classification table|classification table", step8b, re.IGNORECASE), (
        "0b Step 8b must emit a per-file classification table"
    )
    assert "Delete Transient Scratch" in step8b
    assert "Relocate Durable Artifacts to docs/" in step8b
    assert "Keep in .tmp/ for In-Flight Work" in step8b
    assert re.search(r"Fallback[^\n]*multi-action|combine|per-file", step8b, re.IGNORECASE), (
        "0b Step 8b fallback must support multi-action selection"
    )
    for exempt in (
        ".tmp/test-gate.json",
        ".tmp/3d-suite-*.json",
        ".tmp/3z-loop.work.md",
        ".tmp/3d-plan-*.md",
        ".tmp/4a-audit-*.json",
    ):
        assert exempt in step8b


def test_4a_verdict_branched_phase4_and_preserved_3z_contracts():
    text = read_src("workflows/4a-verify-and-ship.md")

    # Phase 1 steps 1 & 3 and Phase 2 Clean Exit Rule route HITL to Phase 4 (not Phase 5)
    phase1 = text.split("## Phase 1:", 1)[1].split("## Phase 2:", 1)[0]
    assert "proceed directly to Phase 5" not in phase1, (
        "4a Phase 1 HITL bypasses must route to Phase 4, not jump directly to Phase 5"
    )
    assert "Phase 4" in phase1, "4a Phase 1 must route HITL [SKIP] to Phase 4"

    phase2 = text.split("## Phase 2:", 1)[1].split("## Phase 3:", 1)[0]
    clean_exit = phase2.split("### Clean Exit Rule", 1)[1]
    assert "proceed directly to Phase 5" not in clean_exit, (
        "4a Phase 2 Clean Exit Rule must route HITL [PASS] to Phase 4, not jump to Phase 5"
    )
    assert "Phase 4" in clean_exit, "4a Phase 2 Clean Exit Rule must route HITL to Phase 4"

    # Preserves 3z audit-only and ship-only contracts
    assert re.search(r"Named gate[^a-zA-Z0-9]*`?audit-only`?[^\n]*Phases 1[\u2013-]3", phase2), (
        "4a must preserve 3z audit-only stopping after Phase 3"
    )
    assert "Named gate — `ship-only`" in text, "4a must preserve ship-only entering at Phase 5"

    # Phase 4 parameterized Audit Verdict + deterministic verdict-branched options + Decision Routing
    phase4 = text.split("## Phase 4:", 1)[1].split("## Phase 5:", 1)[0]
    assert re.search(r"Audit Verdict:.*\[PASS\].*\[SKIP\].*\[UNCOVERED\]|Audit Verdict:.*<PASS\|SKIP\|UNCOVERED>", phase4), (
        "4a Phase 4 card must parameterize Audit Verdict for [PASS], [SKIP], and [UNCOVERED]"
    )
    assert '["(Recommended) Confirm & Ship", "Defer (Stay Local)"]' in phase4, (
        "4a Phase 4 must offer Clean [PASS]/[SKIP] options without Revise/Abort"
    )
    assert '["(Recommended) Confirm & Ship", "Address Findings in 3d"]' in phase4, (
        "4a Phase 4 must offer Advisory [PASS] options"
    )
    assert '["(Recommended) Revise in 3d", "Waive Gaps & Ship", "Abort"]' in phase4, (
        "4a Phase 4 must offer Blocking [UNCOVERED] options"
    )
    assert "--verdict WAIVED" in phase4 and "WAIVED" in pr_body.VERDICTS, (
        "4a Phase 4 Waive Gaps & Ship must pass --verdict WAIVED accepted by pr_body.VERDICTS"
    )
    assert "Decision Routing" in phase4
    assert re.search(r"Defer.*Abort.*exit cleanly before Phase 5|Defer.*before Phase 5", phase4, re.IGNORECASE | re.S)


def test_3a_condition_tailored_roadmap_options():
    text = read_src("workflows/3a-version-planning.md")
    step3 = text.split("3. **Present and Halt:**", 1)[1].split("## Phase 3:", 1)[0]

    assert '["(Recommended) Approve Roadmap & Close Stated Releases", "Adjust Release Placements", "Abort"]' in step3
    assert '["(Recommended) Approve Roadmap", "Adjust Release Placements", "Abort"]' in step3, (
        "3a must omit 'Close Stated Releases' when 0 releases are closable"
    )
    assert '["(Recommended) Close Stated Releases", "Abort"]' in step3, (
        "3a must trim 'Approve Roadmap & ' and omit 'Adjust Release Placements' on Condition-3-only close-out runs"
    )


def test_0d_conditional_r_all_clean_options():
    text = read_src("workflows/0d-nightly-consolidation.md")
    step4 = text.split("4. **Decision Halt:**", 1)[1].split("## Constraints", 1)[0] if "## Constraints" in text else text.split("4. **Decision Halt:**", 1)[1]

    # Native + fallback both conditional on >= 1 Tier 1 cleanup vs 0 Tier 1 cleanups
    assert '["(Recommended) Apply Cleanups (R-ALL-CLEAN)", "Review Cleanups Individually", "Decline All"]' in step4
    assert '["(Recommended) Review Recommendations Individually", "Decline All"]' in step4, (
        "0d must omit R-ALL-CLEAN when 0 Tier 1 cleanups qualify"
    )
    assert re.search(r"Fallback[^\n]*Review Recommendations Individually", step4, re.IGNORECASE), (
        "0d fallback must also branch when 0 Tier 1 cleanups qualify"
    )


def test_stratosphere_update_batched_constitution_multiselect():
    text = read_src("commands/stratosphere-update/SKILL.md")
    sec2 = text.split("### 2. Constitution Files (`needs_review_constitution`)", 1)[1].split("### 3.", 1)[0]

    assert re.search(r"empty[^\n]*skip silently|skip silently[^\n]*empty", sec2, re.IGNORECASE), (
        "stratosphere-update §2 must skip silently when needs_review_constitution is empty"
    )
    output_mode = read_src("rules/output-mode.md")
    assert "multi-select" in sec2.lower() and ".agents/rules/output-mode.md" in sec2 and "§5" in sec2, (
        "stratosphere-update §2 must use native multi-select via output-mode.md §5 to batch constitution files"
    )
    assert "is_multi_select: true" in output_mode and "multiSelect: true" in output_mode
    assert "Keep all current (skip merges)" in sec2, (
        "stratosphere-update §2 must include explicit 'Keep all current (skip merges)' option"
    )
    assert re.search(r"0[- ]selection|zero[- ]selection|none selected|Keep all current", sec2, re.IGNORECASE)
    assert "<filepath>.stratosphere-new" in sec2 and "verbatim" in sec2, (
        "stratosphere-update §2 must copy unselected/declined files verbatim to <filepath>.stratosphere-new"
    )
    assert "Found updates to constitution file `<filename>`. Merge them?" not in sec2, (
        "stratosphere-update §2 must replace the per-file prompt loop with one batched prompt"
    )


def test_dist_skills_match_src_gate_contracts():
    pairs = [
        ("workflows/0b-stop-session.md", "0b-stop-session/SKILL.md"),
        ("workflows/4a-verify-and-ship.md", "4a-verify-and-ship/SKILL.md"),
        ("workflows/3a-version-planning.md", "3a-version-planning/SKILL.md"),
        ("workflows/0d-nightly-consolidation.md", "0d-nightly-consolidation/SKILL.md"),
        ("commands/stratosphere-update/SKILL.md", "stratosphere-update/SKILL.md"),
    ]
    for src_rel, dist_rel in pairs:
        src_text = read_src(src_rel)
        dist_path = DIST_SKILLS / dist_rel
        assert dist_path.is_file(), f"Missing built skill: {dist_path}"
        dist_text = dist_path.read_text(encoding="utf-8")
        assert dist_text == src_text, f"dist drift detected: {dist_rel} != src/{src_rel}"
