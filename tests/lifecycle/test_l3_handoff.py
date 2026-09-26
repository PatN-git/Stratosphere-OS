"""L3 - hand-off mode: the chain at minimum depth.

A full-depth run is the driver plus five nested subagents that inherit its model,
and it costs hours. Hand-off mode keeps every phase - so every hand-off is still
exercised - and bounds each one. What it gives up is depth, and it says so out loud
rather than quietly producing findings nobody should trust.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parent.parent / "lifecycle-harness"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


p = _load("l3_prompts_handoff", HARNESS / "prompts.py")
d = _load("l3_driver_handoff", HARNESS / "driver.py")
r = _load("l3_run_handoff", HARNESS / "run-L3.py")


# --- the bounds ---------------------------------------------------------------

def test_handoff_keeps_every_phase():
    """Dropping phases would drop the hand-offs, which is the whole point."""
    assert r.chosen_phases(r.parse_args(["--handoff"])) == list(p.PHASES)


def test_handoff_lowers_the_turn_budget_and_the_rounds():
    args = r.parse_args(["--handoff"])
    assert (args.max_questions, args.max_rounds) == (3, 1)
    assert args.phase_budget == 600.0


def test_full_depth_is_still_the_default():
    args = r.parse_args([])
    assert (args.max_questions, args.max_rounds) == (10, 2)
    assert args.phase_budget is None
    assert args.handoff is False


def test_an_explicit_value_beats_the_handoff_default():
    args = r.parse_args(["--handoff", "--max-questions", "6"])
    assert args.max_questions == 6
    assert args.max_rounds == 1


# --- the suffix ---------------------------------------------------------------

def test_the_suffix_is_appended_only_in_handoff_mode():
    plain = p.load("2a")
    assert "HAND-OFF TEST MODE" not in plain
    assert p.load("2a", handoff=True).startswith(plain)
    assert "HAND-OFF TEST MODE" in p.load("2a", handoff=True)


def test_the_suffix_keeps_the_sentinel_and_the_invocation_intact():
    """Bounding the depth must not cost the two things the run is read by."""
    for phase in p.PHASES:
        text = p.load(phase, handoff=True)
        assert p.sentinel(phase) in text
        assert text.lstrip().startswith("/")


def test_the_suffix_asks_for_the_links_the_next_phase_reads():
    assert "linked to the previous phase" in p.HANDOFF_SUFFIX


# --- the wall clock -----------------------------------------------------------

class _Clock:
    def __init__(self, steps):
        self.steps = list(steps)

    def __call__(self):
        return self.steps.pop(0) if self.steps else 10_000


class _Chat:
    def __init__(self):
        self.sent = []

    def send(self, prompt):
        self.sent.append(prompt)
        from dataclasses import dataclass, field

        @dataclass
        class T:
            text: str = "still working on it"
            tool_uses: list = field(default_factory=list)
            is_error: bool | None = None
            raw: list = field(default_factory=list)
        return T()


class _Proxy:
    def answer(self, question, fixture):
        return "yes"


def test_a_phase_that_overruns_its_budget_fails_by_name():
    resp_mod = _load("l3_responder_handoff", HARNESS / "responder.py")
    responder = resp_mod.Responder(fixture="f", proxy=_Proxy())
    with pytest.raises(d.PhaseFailure) as exc:
        d.drive("2b", "prompt", "NEVER-PRINTED", _Chat(), responder,
                budget=60, clock=_Clock([0, 61]), log=lambda *a: None)
    assert "2b" in str(exc.value) and "budget" in str(exc.value)


def test_no_budget_means_the_responder_is_what_ends_the_phase():
    """The default lane is full depth, where a long phase is expected. Termination
    is still guaranteed - by the responder's own rules, not by a clock."""
    resp_mod = _load("l3_responder_handoff2", HARNESS / "responder.py")
    responder = resp_mod.Responder(fixture="f", proxy=_Proxy(), max_questions=1,
                                   max_rounds=1)
    with pytest.raises(resp_mod.ResponderFailure):
        d.drive("2b", "prompt", "NEVER-PRINTED", _Chat(), responder,
                clock=_Clock([0]), log=lambda *a: None)


# --- the auditor, demoted but not silenced ------------------------------------

class _Auditor:
    def judge(self, brief):
        return False, ["the riskiest assumption names no test"]


def test_an_advisory_auditor_reports_the_gap_but_does_not_reopen(tmp_path, capsys):
    class Env:
        project = tmp_path
    (tmp_path / "docs" / "discovery").mkdir(parents=True)
    (tmp_path / "docs" / "discovery" / "flags.md").write_text("brief", encoding="utf-8")

    ok, gaps = r._brief_settle(Env(), _Auditor(), advisory=True)()
    assert ok is True and gaps == []
    assert "would have reopened" in capsys.readouterr().out


def test_a_full_depth_auditor_still_fails_the_brief(tmp_path):
    class Env:
        project = tmp_path
    (tmp_path / "docs" / "discovery").mkdir(parents=True)
    (tmp_path / "docs" / "discovery" / "flags.md").write_text("brief", encoding="utf-8")

    ok, gaps = r._brief_settle(Env(), _Auditor(), advisory=False)()
    assert ok is False and gaps
