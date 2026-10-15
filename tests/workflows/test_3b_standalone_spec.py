#!/usr/bin/env python3
"""BT-178 guards: 3b's no-PRD path locates a brief, seeds the slice body from it, holds a minimum spec bar, and escalates a feature to 2a/2b."""
from conftest import read_src as _read


def _line(text, prefix):
    return next(l for l in text.splitlines() if l.lstrip().startswith(prefix))


def _3b():
    return _read("workflows/3b-create-issue.md")


def test_raw_idea_branch_names_the_brief_lookup_and_its_routes():
    line = _line(_3b(), "- Else raw idea/MVI is scope")
    for token in ("2a Phase 1 step 5", "`linked-prd:", "`ready-for-prd`", "`/2a-write-prd`", "HALT", "`dropped`",
                  "`exit-spike`", "Decoupled Follow-ups"):
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
    assert "`[BRIEF-GAP]`" in audit and "do not apply" in audit  # the PRD-relative gap flag is off without a PRD


def test_escalation_rule_is_stated_once_with_its_triggers_and_routes():
    text = _3b()
    assert text.count("**Escalation rule") == 1
    line = _line(text, "- **Escalation rule")
    for token in ("Blocked-by", "UI surface", "ADR", "external cost", "`/2a-write-prd`", "`/2b-interface-design`",
                  "HALT", "overrides"):
        assert token in line, token
    assert line.index("`/2a-write-prd`") < line.index("`/2b-interface-design`")  # 2b is post-PRD, never an alternative to 2a


def test_brief_open_questions_reuse_the_spike_rule_on_the_10_bullet():
    line = _line(_3b(), "- **§10:**")
    assert "Open Questions" in line and "Riskiest Assumption" in line and "→ a Spike" in line
