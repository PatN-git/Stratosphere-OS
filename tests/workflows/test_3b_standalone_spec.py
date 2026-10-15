#!/usr/bin/env python3
"""BT-178 guards: 3b's no-PRD path locates a brief, seeds the slice body from it, holds a minimum spec bar, and escalates a feature to 2a/2b."""
from conftest import read_src as _read


def _line(text, prefix):
    return next(l for l in text.splitlines() if l.lstrip().startswith(prefix))


def _3b():
    return _read("workflows/3b-create-issue.md")


def test_raw_idea_branch_names_the_brief_lookup_and_its_status_routes():
    line = _line(_3b(), "- Else raw idea/MVI is scope")
    for token in ("a brief path the user names wins", "`docs/discovery/*.md`", "`*.work.md`", "`*.map.md`",
                  "2a Phase 1 step 5", "`linked-prd:", "`ready-for-prd`", "`dropped`", "`exit-spike`",
                  "Decoupled Follow-ups"):
        assert token in line, token


def test_brief_seed_maps_each_section_on_one_bullet():
    line = _line(_3b(), "- **Brief seed")
    for pair in ("Established Facts → Current state", "Problem → Overview", "Success State → Acceptance Criteria",
                 "Constraints & Settled Decisions → constraints in The Path", "Non-Goals → Notes"):
        assert pair in line, pair


def test_minimum_spec_bar_is_defined_once_and_audited_in_no_prd_mode():
    text = _3b()
    assert text.count("**Minimum spec bar") == 1
    bar = _line(text, "- **Minimum spec bar")
    for token in ("problem statement", "verifiable AC", "constraints or non-goals"):
        assert token in bar, token
    audit = _line(text, "- **No PRD:**")
    assert "spec bar" in audit and "[UNCOVERED?]" in audit
    assert "`[BRIEF-GAP]`" in audit  # states that the PRD-relative gap flag does not apply without a PRD


def test_escalation_rule_is_stated_once_with_its_three_triggers_and_both_routes():
    text = _3b()
    assert text.count("**Escalation rule") == 1
    line = _line(text, "- **Escalation rule")
    for token in ("depend on each other", "new UI surface", "ADR", "external cost", "`/2a-write-prd`",
                  "`/2b-interface-design`", "HALT", "Spikes excluded"):
        assert token in line, token
    assert "Open Question" in line and "Riskiest Assumption" in line and "§10 rule" in line
