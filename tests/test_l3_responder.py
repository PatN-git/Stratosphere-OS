"""L3 Slice 0 - the responder's policy, isolation and termination guarantees.

These run without the `claude` CLI: the proxy and auditor are stubs. What is proved
here is the part where a bug would be silent - a gate answered non-deterministically,
the proxy handed the draft brief, or a grill that never ends.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).parent / "lifecycle-harness" / "responder.py"
_spec = importlib.util.spec_from_file_location("l3_responder", _SRC)
r = importlib.util.module_from_spec(_spec)
sys.modules["l3_responder"] = r   # @dataclass resolves types via sys.modules
_spec.loader.exec_module(r)

FIXTURE = (Path(__file__).parent / "lifecycle-harness" / "fixture" / "topic.md").read_text(
    encoding="utf-8")


class StubProxy:
    """Records every call so isolation can be asserted, not assumed."""

    def __init__(self, reply="A position from the fixture."):
        self.reply = reply
        self.calls = []

    def answer(self, question, fixture):
        self.calls.append((question, fixture))
        return self.reply


def make(proxy=None, **kw):
    return r.Responder(fixture=FIXTURE, proxy=proxy or StubProxy(), **kw)


# --- the policy answers structured gates deterministically -------------------

def test_option_menu_picks_first():
    menu = "Which framing?\n1. Local evaluation\n2. Remote service\n3. Hybrid"
    a = make().reply(menu)
    assert a.text == "1"
    assert a.source == "policy:pick-first"


def test_lone_numeral_is_not_a_menu():
    """A '1.' in prose must reach the proxy, not be answered as a pick."""
    proxy = StubProxy()
    a = make(proxy).reply("1. is the bucketing key stable across processes?")
    assert a.source == "proxy"


def test_ice_prompt_is_fixed():
    a = make().reply("Give me Impact and Confidence for this slice, plus a size.")
    assert a.source == "policy:ice"
    assert "Impact 1.0" in a.text and "size:small" in a.text


def test_confirm_is_refused_until_the_budget_is_spent():
    """Superseded the old `test_confirm_is_yes`, which asserted the bug.

    Answering a confirm with "yes" while questions remain ends 1b's grill - the
    first full-depth run finished in three replies because of exactly this.
    """
    a = make(max_questions=10).reply("I have enough to proceed. Shall I write the brief?")
    assert a.source == "policy:not-yet"


def test_menu_beats_confirm():
    """'Shall I proceed with 1, 2 or 3' is a pick, not a yes."""
    a = make().reply("Shall I proceed?\n1. Yes now\n2. After more questions")
    assert a.source == "policy:pick-first"


# --- the proxy is isolated ---------------------------------------------------

def test_proxy_sees_only_the_question_and_the_fixture():
    proxy = StubProxy()
    resp = make(proxy)
    resp.reply("Who is the actor?")
    (question, fixture), = proxy.calls
    assert question == "Who is the actor?"
    assert fixture == FIXTURE
    assert len(proxy.calls) == 1


def test_responder_cannot_leak_a_brief_because_it_never_holds_one():
    """Isolation is structural, not a promise: there is no brief to leak.

    If a later change gives Responder the draft brief - to 'help' the proxy answer -
    the proxy starts grading work it wrote, which is the failure 1b:64 forbids. This
    test fails the moment such a field appears.
    """
    resp = make()
    held = {f for f in vars(resp) if "brief" in f.lower() or "draft" in f.lower()}
    assert not held, f"Responder now holds {held}; the proxy could be handed the brief"

    with pytest.raises(TypeError):
        r.Responder(fixture=FIXTURE, proxy=StubProxy(), brief="anything")


def test_empty_proxy_answer_fails_by_name():
    with pytest.raises(r.GateUnanswered) as e:
        make(StubProxy(reply="   ")).reply("Why not use a vendor SDK?")
    assert "Why not use a vendor SDK?" in str(e.value)


# --- the budget is the harness's stopping policy ------------------------------

def test_budget_sends_stop_after_max_questions():
    resp = make(max_questions=3)
    for i in range(3):
        assert resp.reply(f"question {i}").source == "proxy"
    a = resp.reply("question 4")
    assert a.source == "policy:budget"
    assert a.text == r.STOP


def test_next_round_resets_and_seeds_gaps():
    resp = make(max_questions=2, max_rounds=2)
    resp.reply("q1"); resp.reply("q2")
    assert resp.reply("q3").source == "policy:budget"

    seed = resp.next_round(["actor is vague", "no non-goals"])
    assert seed is not None
    assert "actor is vague" in seed and "no non-goals" in seed
    assert resp.asked == 0 and resp.rounds_used == 2
    assert resp.reply("q4").source == "proxy"   # answering again


def test_rounds_are_capped():
    resp = make(max_questions=1, max_rounds=2)
    assert resp.next_round(["gap"]) is not None   # round 2
    assert resp.next_round(["gap"]) is None       # no round 3


# --- termination is guaranteed -----------------------------------------------

def test_repeated_turn_is_a_loop():
    resp = make()
    resp.reply("same question")
    resp.reply("same question")
    with pytest.raises(r.LoopDetected):
        resp.reply("same question")


def test_whitespace_does_not_disguise_a_loop():
    resp = make()
    resp.reply("Same   Question")
    resp.reply("same question")
    with pytest.raises(r.LoopDetected):
        resp.reply("  SAME QUESTION  ")


def test_hard_ceiling_terminates_a_starved_run():
    """The termination proof: an agent that never stops, and an auditor that never
    passes, must still end the run - and say why."""
    resp = make(max_questions=5, max_rounds=2)
    with pytest.raises(r.BudgetExhausted) as e:
        for i in range(10_000):          # far past any legitimate grill
            resp.reply(f"unique question {i}")
            if resp.asked >= resp.max_questions:
                resp.next_round([f"still unresolved {i}"])   # auditor always FAILs
    assert "hard ceiling" in str(e.value)
    assert resp.replies <= resp.hard_ceiling + 1


def test_ceiling_holds_even_with_unlimited_rounds():
    """max_rounds is not what bounds the run; the ceiling is, independently."""
    resp = make(max_questions=2, max_rounds=999)
    with pytest.raises(r.BudgetExhausted):
        for i in range(10_000):
            resp.reply(f"q{i}")
            if resp.asked >= resp.max_questions:
                resp.next_round(["gap"])


# --- the grill must not be endable by the harness -----------------------------

def test_stop_gate_is_refused_while_budget_remains():
    """1b:64's primary stop gate is a restatement the user must accept.

    The first full-depth run answered it "Yes, proceed." and finished in three
    replies, never reaching the proxy or the auditor. The harness caused the early
    stop it exists to prevent.
    """
    resp = make(max_questions=10)
    a = resp.reply("Let me restate to confirm: the actor is a backend engineer, "
                   "the problem is latency. Is that right?")
    assert a.source == "policy:not-yet"
    assert "not yet" in a.text.lower()


def test_every_observed_1b_stop_phrasing_is_refused():
    for text in [
        "Before I continue, can you confirm my understanding of the actor?",
        "Shall I proceed to Phase 3 and crystallize vocabulary?",
        "I have enough to proceed. Shall I write the discovery brief?",
    ]:
        assert make(max_questions=10).reply(text).source == "policy:not-yet", text


def test_consent_only_once_the_budget_is_spent():
    resp = make(max_questions=2)
    # Texts must differ: three identical turns trip loop detection before the
    # budget branch is ever reached.
    assert resp.reply("Shall I proceed now?").source == "policy:not-yet"     # asked=1
    assert resp.reply("Can you confirm the actor?").source == "policy:confirm"  # last
    assert resp.reply("Shall I write it up?").source == "policy:budget"      # spent


def test_pushing_back_still_drains_the_budget():
    """Refusing must not be free, or the run never terminates."""
    resp = make(max_questions=3)
    for i in range(3):
        resp.reply(f"Can you confirm point {i}?")
    assert resp.asked == 3
    assert resp.reply("Can you confirm once more?").source == "policy:budget"
