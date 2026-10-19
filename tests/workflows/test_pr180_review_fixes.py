#!/usr/bin/env python3
"""PR #180 review fixes: pointers resolve through the build, each gate's literal agrees with the text that cites it."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def _section(text, start, end=None):
    i = text.index(start)
    j = text.index(end, i + len(start)) if end else len(text)
    return text[i:j]


def test_red_flags_cite_code_smell_baseline_in_the_form_the_build_fans_out():
    """build.py copies only `references/<file>.md` citations; a bare basename left 2b and 4b without the file."""
    flags = _read("references/design-red-flags.md")
    assert "`references/code-smell-baseline.md`" in flags
    for skill in ("2b-interface-design", "4b-audit-architecture-drift"):
        assert (ROOT / "dist" / "skills" / skill / "references" / "code-smell-baseline.md").is_file(), skill


def test_4a_floor_guard_halt_literal_has_balanced_backticks():
    step0 = next(line for line in _read("workflows/4a-verify-and-ship.md").splitlines() if line.startswith("0. **Clean-tree guard"))
    assert step0.count("`") % 2 == 0, "a nested backtick closes the HALT literal early"


def test_4a_ci_fix_rerun_gets_attempt_2_and_skips_the_feature_audit():
    step8 = _section(_read("workflows/4a-verify-and-ship.md"), "8. **Epic Check:**", "9. **Terminal sync gate:**")
    assert "`--attempt 2` on a `ship-only` re-run after a CI fix" in step8
    assert "skip on a `ship-only` re-run after a CI fix" in step8.split("**CI gate**")[0]
    assert "dependents cleared in step 7" in step8 and "step 9 for slice only" not in step8


def test_4a_step_cites_name_the_reference_they_mean():
    step8 = _section(_read("workflows/4a-verify-and-ship.md"), "8. **Epic Check:**", "9. **Terminal sync gate:**")
    cites = [c for c in step8.split("ci-gate.md`")[1:]]
    assert len(cites) >= 3 and all(c.lstrip().startswith("§") for c in cites[1:]), "bare section marks collide with PRD section numbers"


def test_3z_halt_bullet_does_not_contradict_itself_and_ci_fix_failures_are_listed():
    step = _section(_read("workflows/3z-afk-loop.md"), "### Step 3A", "### Step 3B")
    halt = next(line for line in step.splitlines() if line.startswith("   - Any `ship-only` halt"))
    assert "leave slice local" not in halt and "except `[CI-RED]`" in halt
    assert "implementer `stuck` or red suite" in step
    assert "one capped CI-fix round may follow the push" in _read("workflows/3z-afk-loop.md")


def test_ci_gate_reference_gives_the_fix_round_an_exit_for_steps_1_to_3():
    fix = _section(_read("references/ci-gate.md"), "## 3. Fix", "## 4. Big")
    assert "Steps 1-3 fail" in fix and "BT-<padded> -- <cmd>" in fix


def test_4c_clean_exit_has_one_healthy_literal_and_regressions_have_a_handoff_line():
    text = _read("workflows/4c-codebase-health-audit.md")
    clean = _section(text, "If no finding ≥60 confidence across any pass:")
    assert clean.count("[HEALTHY] No findings") == 1 and "first token `[HEALTHY*]`" in clean
    handoff = _section(text, "## Phase 6: Handoff", "Await user direction")
    assert "Δ vs last run:" in handoff and "[REGRESSION]" in handoff and "[NO-DELTA]" in handoff


def test_4b_dismissals_are_returned_by_the_subagent_and_the_quote_it_cited_is_gone():
    text = _read("workflows/4b-audit-architecture-drift.md")
    assert 'exception to "do not report"' not in text
    assert "`Dismissed (deliberate)` lines" in text.split("**Output Contract:**")[1].splitlines()[0]


def test_3b_boundary_lines_carry_their_own_halt_rule_and_2a_does_not_describe_3b():
    line = next(l for l in _read("workflows/3b-create-issue.md").splitlines() if "PRD §7 Boundaries" in l)
    assert "HITL: halt and ask; AFK: return `stuck`" in line
    assert "3b copies" not in _read("workflows/2a-write-prd.md")


def test_2b_path_a_cites_the_template_instead_of_restating_its_states():
    step6 = next(l for l in _read("workflows/2b-interface-design.md").splitlines() if l.startswith("6. Freeze layout into Path A"))
    assert "Patterns to Reject" in step6 and "loading, empty, error" not in step6
