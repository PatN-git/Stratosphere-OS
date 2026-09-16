"""L3 Slice 3 - the opening prompts, and the gate inventory they will be answered by.

Text files, checked as contracts. What can be verified without an agent is verified
here; whether each phase actually completes under the responder is Slice 4's job.
"""
import importlib.util
import re
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).parent / "lifecycle-harness"

_spec = importlib.util.spec_from_file_location("l3_prompts", HARNESS / "prompts.py")
p = importlib.util.module_from_spec(_spec)
sys.modules["l3_prompts"] = p
_spec.loader.exec_module(p)

GATES = (HARNESS / "gates.md").read_text(encoding="utf-8")

# The invocation each phase's opening turn must carry. `0a` is driven twice: once
# greenfield, where it must halt without touching anything, and once after the
# backlog exists, where it restores state.
INVOCATION = {
    "0a": "/0a-start-session",
    "0a-second": "/0a-start-session",
    "1a": "/1a-research",
    "1b": "/1b-concept-framing",
    "2a": "/2a-write-prd",
    "2b": "/2b-interface-design",
    "3b": "/3b-create-issue",
    "3d": "/3d-implement-issue",
    "4a": "/4a-verify-and-ship",
    "0b": "/0b-stop-session",
}


@pytest.mark.parametrize("phase", p.PHASES)
def test_every_phase_has_a_prompt(phase):
    assert p.load(phase)


@pytest.mark.parametrize("phase", p.PHASES)
def test_the_prompt_invokes_the_phase_it_names(phase):
    assert INVOCATION[phase] in p.load(phase)


@pytest.mark.parametrize("phase", p.PHASES)
def test_the_prompt_carries_its_own_sentinel(phase):
    """A missing sentinel is a failure, never a skip: it is the only evidence that
    a phase ran to its own end rather than stopping mid-way with prose."""
    assert p.sentinel(phase) in p.load(phase)


def test_sentinels_are_unique_across_phases():
    """`0a` runs twice. If both printed the same sentinel, the second run could be
    satisfied by the first one's output still sitting in the transcript."""
    sentinels = [p.sentinel(ph) for ph in p.PHASES]
    assert len(set(sentinels)) == len(sentinels)


def test_the_phase_list_is_the_coverage_the_plan_states():
    assert p.PHASES == ("0a", "1a", "1b", "2a", "2b", "0a-second",
                        "3b", "3d", "4a", "0b")


def test_no_prompt_carries_the_fixture():
    """The proxy's isolation is what makes its answers worth anything.

    Handing `topic.md` to the driver would give `1b` the answers to its own grill,
    and the brief would be a transcription rather than a discovery. The prompts name
    the subject in one line; the positions behind it stay with the proxy.
    """
    fixture = (HARNESS / "fixture" / "topic.md").read_text(encoding="utf-8")
    # Any distinctive line of the fixture appearing verbatim in a prompt is a leak.
    distinctive = [ln.strip() for ln in fixture.splitlines()
                   if len(ln.strip()) > 60 and not ln.strip().startswith("#")]
    assert distinctive, "the fixture has no distinctive lines to check against"
    for phase in p.PHASES:
        text = p.load(phase)
        leaked = [ln for ln in distinctive if ln in text]
        assert not leaked, f"{phase} leaks the fixture: {leaked[:1]}"


def test_4a_asks_for_the_audit_only_gate_and_forbids_shipping():
    """Fact 12: `ship-only` runs design_theme.py --check unconditionally in 5.2, so
    a non-UI fixture cannot ship for a reason unrelated to anything L3 tests."""
    text = p.load("4a")
    assert "audit-only" in text
    assert "ship-only" in text and "Do not run" in text


def test_2b_states_the_fixture_has_no_ui_so_path_c_is_reachable():
    """Fact 10: Path C is the only branch fully exercisable headlessly - A needs
    Stitch or the Claude Design MCP, B is native UI."""
    assert "no user interface" in p.load("2b")


def test_1a_pins_quick_search():
    """Fact 9: Quick Search bypasses the Phase 2 deep loop and the refutation
    subagent, and the 24-query cap is a Deep Research budget, not a Quick one."""
    assert "Quick Search" in p.load("1a")


def test_a_missing_prompt_says_which_phase():
    with pytest.raises(FileNotFoundError) as exc:
        p.load("9z")
    assert "9z" in str(exc.value)


# --- the gate inventory ------------------------------------------------------

@pytest.mark.parametrize("phase", p.PHASES)
def test_gates_md_covers_every_driven_phase(phase):
    """"Every gate is answered" is only falsifiable if every phase is listed."""
    skill = INVOCATION[phase].lstrip("/")
    assert f"`{skill}`" in GATES


def test_every_gate_row_names_its_source_line():
    """A gate row without a source is a guess. Each must cite `<skill>:<line>`."""
    rows = [ln for ln in GATES.splitlines()
            if re.match(r"^\| \d?[0-9ab]{1,2}[a-z]?-G\d+ \|", ln)]
    assert len(rows) >= 25, f"only {len(rows)} gate rows found"
    for row in rows:
        assert re.search(r"`[0-9][a-z]:\d+", row), f"no source line in: {row[:80]}"


def test_every_gate_row_names_an_answer_source():
    known = ("policy:pick-first", "policy:ice", "policy:confirm", "policy:budget",
             "policy:not-yet", "proxy", "No question", "No answer", "Not a question",
             "Not a user", "Not reached", "Never reached", "finding")
    rows = [ln for ln in GATES.splitlines()
            if re.match(r"^\| \d?[0-9ab]{1,2}[a-z]?-G\d+ \|", ln)]
    for row in rows:
        assert any(k in row for k in known), f"no answer source in: {row[:80]}"
