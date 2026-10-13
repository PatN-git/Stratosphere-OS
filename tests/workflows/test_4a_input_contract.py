#!/usr/bin/env python3
"""BT-166 (4a side) guards: slice AC is the auditor's primary input, deviations and manual-QA reach the PR body, FAA scope names PRD sections."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def _4a() -> str:
    return _read("workflows/4a-verify-and-ship.md")


def _line(text: str, prefix: str) -> str:
    return next(l for l in text.splitlines() if l.lstrip().startswith(prefix))


def test_business_logic_auditor_input_is_the_slice_issue_ac_plus_prd_sections():
    auditor = _line(_4a(), "1. **Strict Business-Logic Auditor:**")
    assert "slice issue body's `### Acceptance Criteria`" in auditor and "gh issue view <n>" in auditor
    assert auditor.index("Acceptance Criteria") < auditor.index("parent PRD §6/§7/§8")
    assert "docs/design/BT-<parentPadded>-interface.md" in auditor  # BT-165 parent-keyed path kept


def test_auditor_receives_plan_deviations_and_judges_them():
    auditor = _line(_4a(), "1. **Strict Business-Logic Auditor:**")
    assert "`## Deviations`" in auditor and ".tmp/3d-plan-BT-<padded>.md" in auditor
    assert "judged on merit" in auditor


def test_phase_3_table_says_slice_ac_and_phase_1_gate_keys_on_prd_dod():
    text = _4a()
    assert "| Slice AC / Requirement |" in text and "| AC / Requirement |" not in text.replace("| Slice AC / Requirement |", "")
    assert "covers a PRD §8 Definition-of-Done item" in _line(text, "2. If task touches security/RLS")
    assert "explicit slice AC" not in text
    assert "PRD AC" not in text and "PRD Acceptance" not in text


def test_step5_build_literal_carries_deviation_and_manual_qa():
    text = _4a()
    step5 = text[text.index("5. **PR (one per feature branch):**"):text.index("6. **PR-link comment")]
    build = _line(step5, "- **Build:**")
    assert "--deviation" in build and "--manual-qa" in build
    assert "`## Deviations`" in build and "needs_manual_qa" in build


def test_plan_is_deleted_last_and_the_wording_is_true():
    text = _4a()
    cleanup = text[text.index("10. **Cleanup:**"):text.index("11. Output:")]
    assert "rm -f .tmp/3d-plan-BT-<padded>.md" in cleanup
    assert "last step" in cleanup and "step 5's `--deviation`" in cleanup
    assert "are in the PR body now" not in cleanup


def test_pr_body_reference_agrees_on_deviation_and_manual_qa_flags():
    ref = _read("references/pr-body-and-ship.md")
    flags = _line(ref, "- **Optional flags:**")
    assert "--deviation" in flags and "--manual-qa" in flags and "`## Deviations`" in flags


def test_feature_acceptance_audit_scope_names_prd_sections_not_the_full_ac_set():
    faa = _read("references/feature-acceptance-audit.md")
    inp = _line(faa, "- **Input:**")
    for token in ("§8 Definition of Done", "§5 Success Signals", "`[BASELINE]`/`[DIFFERENTIATOR]` §6"):
        assert token in inp, token
    assert "full AC set" not in faa
    assert "**Audit epic**" in faa and "Coverage table" in faa  # audit-epic branch intact
