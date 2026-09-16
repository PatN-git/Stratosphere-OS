#!/usr/bin/env python3
"""L3 Slice 0 - the scripted responder that stands in for the user.

`1b-concept-framing` runs a deliberately unbounded grill: 20-50 questions, and the
*user* - never the agent - declares "enough" (1b:64,68). That design is correct and
stays. But `claude -p` is single-turn, so an unattended run needs something to play
the user. That is this module.

Two things answer, and the split is the point:

  * The POLICY answers structured gates deterministically - picking among generated
    options, ICE numbers, proceed/confirm. These change control flow, so a run must
    not vary on them.
  * The USER PROXY answers everything else from the pinned fixture. It is given the
    fixture and the question and nothing else - never the draft brief - so it cannot
    rubber-stamp work it has not read. That isolation is what keeps this from being
    the agent answering its own questions.

The budget belongs to the harness, not to `1b`. It is the harness's own stopping
policy expressed as the user's, not a change to the skill.

Termination is guaranteed by a hard ceiling on total replies, independent of every
other rule. See `test_l3_responder.py::test_hard_ceiling_terminates`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol


class ResponderFailure(Exception):
    """Base for every way the responder refuses to continue.

    Every subclass names what went wrong and quotes the text that caused it: a run
    that dies here must say which gate beat it, never just "timed out" (E6).
    """


class GateUnanswered(ResponderFailure):
    """Neither the policy nor the proxy could answer."""


class BudgetExhausted(ResponderFailure):
    """Rounds ran out, or the hard ceiling tripped."""


class LoopDetected(ResponderFailure):
    """The agent asked the same thing repeatedly and made no progress."""


class Proxy(Protocol):
    def answer(self, question: str, fixture: str) -> str:
        """Answer `question` in character, knowing only `fixture`."""


class Auditor(Protocol):
    def judge(self, brief: str) -> tuple[bool, list[str]]:
        """Return (sufficient, gaps). Gaps seed the next round when not sufficient."""


@dataclass
class Answer:
    text: str
    source: str  # "policy:<rule>" | "proxy"


STOP = ("That is enough questioning - you have what you need. "
        "Proceed with what you have and write it up.")

# Structured gates. Order matters: an option list wins over a bare confirm, because
# "shall I proceed with 1, 2 or 3?" is a pick, not a yes.
_OPTION = re.compile(r"^\s*(?:\*\*)?(?:option\s*)?([1-3])[.):]", re.I | re.M)
_ICE = re.compile(r"\bimpact\b.*\bconfidence\b|\bconfidence\b.*\bimpact\b", re.I | re.S)
_CONFIRM = re.compile(r"\bproceed\?|\bconfirm\b|\bshall i\b|\bok to\b|\bshould i continue\b", re.I)


def _is_pick(text: str) -> bool:
    # Two or more distinct markers, so a lone "1." in prose is not mistaken for a menu.
    return len(set(_OPTION.findall(text))) >= 2


@dataclass
class Responder:
    """Answers an agent's turns as the user would, with a bounded stopping policy."""

    fixture: str
    proxy: Proxy
    max_questions: int = 10
    max_rounds: int = 2
    loop_threshold: int = 3

    asked: int = 0
    rounds_used: int = 1
    replies: int = 0
    _seen: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Independent of every other rule, so no combination of them can spin forever.
        self.hard_ceiling = self.max_questions * self.max_rounds + 5

    def reply(self, agent_text: str) -> Answer:
        self.replies += 1
        if self.replies > self.hard_ceiling:
            raise BudgetExhausted(
                f"hard ceiling of {self.hard_ceiling} replies reached after "
                f"{self.rounds_used} round(s); last turn: {agent_text[:200]!r}")

        key = _normalize(agent_text)
        self._seen[key] = self._seen.get(key, 0) + 1
        if self._seen[key] >= self.loop_threshold:
            raise LoopDetected(
                f"agent repeated the same turn {self._seen[key]} times with no "
                f"progress: {agent_text[:200]!r}")

        if self.asked >= self.max_questions:
            return Answer(STOP, "policy:budget")

        self.asked += 1
        if _is_pick(agent_text):
            return Answer("1", "policy:pick-first")
        if _ICE.search(agent_text):
            return Answer("Impact 1.0, Confidence 80%, size:small, mode:AFK", "policy:ice")
        if _CONFIRM.search(agent_text):
            return Answer("Yes, proceed.", "policy:confirm")

        text = self.proxy.answer(agent_text, self.fixture)
        if not text or not text.strip():
            raise GateUnanswered(
                f"proxy returned nothing for: {agent_text[:200]!r}")
        return Answer(text.strip(), "proxy")

    def next_round(self, gaps: list[str]) -> str | None:
        """Open another round seeded by the auditor's gaps, or None when none remain."""
        if self.rounds_used >= self.max_rounds:
            return None
        self.rounds_used += 1
        self.asked = 0
        bullets = "\n".join(f"- {g}" for g in gaps)
        return ("Not yet - these are still unresolved and I want them explored "
                f"before you write it up:\n{bullets}")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()[:400]
