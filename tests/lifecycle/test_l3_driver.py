"""L3 Slice 4 - the phase loop, driven by fakes.

Every path through `drive()` exists because something once looked like success.
Fakes rather than an agent: the loop's logic is what is under test here, and
proving it needs no model calls at all.
"""
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parent.parent / "lifecycle-harness"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


d = _load("l3_driver", HARNESS / "driver.py")
resp_mod = _load("l3_responder_driver", HARNESS / "responder.py")

SENTINEL = "L3-TEST-COMPLETE"


@dataclass
class FakeTurn:
    text: str
    tool_uses: list = field(default_factory=list)
    is_error: bool | None = None
    raw: list = field(default_factory=list)


class FakeChat:
    """Replies in order; the last reply repeats if the loop asks for more."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.sent = []

    def send(self, prompt):
        self.sent.append(prompt)
        nxt = self.replies.pop(0) if self.replies else FakeTurn(SENTINEL)
        return nxt if isinstance(nxt, FakeTurn) else FakeTurn(nxt)


class EchoProxy:
    def answer(self, question, fixture):
        return "the fixture says so"


def responder(**kw):
    return resp_mod.Responder(fixture="fixture", proxy=EchoProxy(), **kw)


def silent(*a, **kw):
    pass


# --- the happy paths ---------------------------------------------------------

def test_a_phase_that_finishes_on_its_first_turn_needs_no_answer():
    chat = FakeChat([FakeTurn(f"all done. {SENTINEL}")])
    run = d.drive("2a", "prompt", SENTINEL, chat, responder(), log=silent)
    assert run.replies == 0
    assert len(chat.sent) == 1


def test_the_responder_answers_until_the_sentinel_arrives():
    chat = FakeChat([FakeTurn("What is the actor?"),
                     FakeTurn("And the problem?"),
                     FakeTurn(f"Written. {SENTINEL}")])
    run = d.drive("1b", "prompt", SENTINEL, chat, responder(), log=silent)
    assert run.replies == 2
    assert chat.sent[1:] == ["the fixture says so", "the fixture says so"]


# --- the failures that used to look like success -----------------------------

def test_an_error_turn_is_a_driver_failure_not_a_question():
    """A turn can carry is_error while still holding readable text, so a text-only
    check passes it through and the harness grills an error message for ten rounds."""
    chat = FakeChat([FakeTurn("Invalid API key", is_error=True)])
    with pytest.raises(d.PhaseFailure) as exc:
        d.drive("1a", "prompt", SENTINEL, chat, responder(), log=silent)
    assert "1a" in str(exc.value) and "error turn" in str(exc.value)


def test_an_empty_turn_names_the_cli_not_the_proxy():
    """Fed to the responder, an empty turn surfaces as 'proxy returned nothing',
    which blames the proxy for a CLI problem."""
    chat = FakeChat([FakeTurn("", raw=["{}"])])
    with pytest.raises(d.PhaseFailure) as exc:
        d.drive("0a", "prompt", SENTINEL, chat, responder(), log=silent)
    assert "empty turn" in str(exc.value)


def test_a_login_failure_says_how_to_fix_it():
    chat = FakeChat([FakeTurn("Not logged in - please run /login", is_error=True)])
    with pytest.raises(d.PhaseFailure) as exc:
        d.drive("1b", "prompt", SENTINEL, chat, responder(), log=silent)
    assert "CLAUDE_CLI" in str(exc.value)


# --- settle: the sentinel is necessary, not sufficient -----------------------

def test_a_failed_audit_reopens_the_phase_with_the_gaps():
    chat = FakeChat([FakeTurn(SENTINEL), FakeTurn(SENTINEL)])
    verdicts = iter([(False, ["no non-goals"]), (True, [])])

    run = d.drive("1b", "prompt", SENTINEL, chat, responder(),
                  settle=lambda: next(verdicts), log=silent)
    assert run.rounds == 2
    assert "no non-goals" in chat.sent[-1]


def test_rounds_exhausted_fails_naming_the_open_gaps():
    chat = FakeChat([FakeTurn(SENTINEL)] * 6)
    with pytest.raises(d.PhaseFailure) as exc:
        d.drive("1b", "prompt", SENTINEL, chat, responder(max_rounds=1),
                settle=lambda: (False, ["the riskiest assumption has no test"]),
                log=silent)
    assert "rounds exhausted" in str(exc.value)
    assert "riskiest assumption" in str(exc.value)


def test_a_sentinel_with_no_artifact_to_judge_fails():
    """The first full-depth 1b run printed the sentinel in three replies and never
    audited anything, so [pass] meant only that the headings existed."""
    chat = FakeChat([FakeTurn(SENTINEL)])
    with pytest.raises(d.PhaseFailure) as exc:
        d.drive("1b", "prompt", SENTINEL, chat, responder(),
                settle=lambda: None, log=silent)
    assert "nothing to judge" in str(exc.value)


def test_the_hard_ceiling_still_terminates_a_phase_that_never_finishes():
    """No combination of loop rules may spin forever."""
    chat = FakeChat([FakeTurn(f"question {i}") for i in range(200)])
    with pytest.raises(resp_mod.BudgetExhausted):
        d.drive("1b", "prompt", SENTINEL, chat,
                responder(max_questions=2, max_rounds=1), log=silent)
