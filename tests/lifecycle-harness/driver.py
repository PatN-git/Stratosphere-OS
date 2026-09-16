#!/usr/bin/env python3
"""L3 Slice 4 - drive one phase from its opening prompt to its sentinel.

This is the loop Slice 0 proved against `1b`, generalised to any phase. It is kept
in one place rather than copied per phase because every line of it exists to stop a
specific failure that looked like success:

  * **The sentinel is the only evidence a phase finished.** Not the agent saying so
    in prose, not the absence of an error. A missing sentinel is a failure, never a
    skip (plan, section 9).
  * **A failed turn is a driver failure, not a question.** An empty turn fed to the
    responder surfaces as "proxy returned nothing", blaming the proxy for a CLI
    problem; and a turn can carry `is_error` while still holding perfectly readable
    text - "Not logged in - Please run /login" is a good string, so a text-only
    check passes it through and the harness grills an error message for ten rounds.
  * **Reaching the sentinel is not the same as being finished.** `settle` exists for
    `1b`, whose first full-depth run printed the sentinel in three replies with a
    brief nobody had audited. A phase that hands in a `settle` says the sentinel is
    necessary but not sufficient, and the gaps it returns seed another round.

Nothing here knows what a phase produces. That is `assertions.py`.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


class PhaseFailure(RuntimeError):
    """The phase did not reach its own end, and the message says which one."""


@dataclass
class PhaseRun:
    phase: str
    turns: list = field(default_factory=list)
    replies: int = 0
    rounds: int = 1

    @property
    def last(self):
        return self.turns[-1] if self.turns else None


def guard(turn, phase: str):
    """Reject a turn that is an infrastructure failure rather than a question."""
    blob = (turn.text + "\n" + "\n".join(turn.raw)).lower()
    hint = ""
    if "not logged in" in blob or "/login" in blob:
        hint = ("\n  The CLI is unauthenticated in the temp HOME. Seeding "
                "~/.claude/.credentials.json is NOT always enough; run "
                "`claude /login` once for the CLI this harness resolves to, or "
                "point CLAUDE_CLI at an already-authenticated binary.")
    if turn.is_error:
        raise PhaseFailure(f"{phase}: the agent reported an error turn: "
                           f"{turn.text[:300]!r}{hint}")
    if not turn.text.strip():
        tail = "\n".join(turn.raw[-5:]) or "<no output at all>"
        raise PhaseFailure(
            f"{phase}: the agent produced an empty turn - the CLI is not driving."
            f"{hint}\n  last stream lines:\n{tail}")
    return turn


def drive(phase: str, prompt: str, sentinel: str, chat, responder,
          settle=None, log=print, budget: float | None = None,
          clock=time.monotonic) -> PhaseRun:
    """Run one phase to its sentinel. Raises PhaseFailure if it never gets there.

    `settle()` returns `(ok, gaps)` or None when there is nothing to judge yet. It
    is consulted at the sentinel and whenever the responder spends its budget, so a
    phase can be reopened with the gaps rather than accepted thin.
    """
    run = PhaseRun(phase=phase)
    started = clock()
    turn = guard(chat.send(prompt), phase)
    run.turns.append(turn)

    while True:
        # A phase that stalls must fail by name rather than consume the run's
        # remaining wall clock. Checked between turns, so a turn in flight is
        # never killed mid-write.
        if budget is not None and clock() - started > budget:
            raise PhaseFailure(
                f"{phase}: exceeded its {budget:.0f}s budget after "
                f"{len(run.turns)} turn(s) without reaching its sentinel")
        if sentinel in turn.text:
            if settle is None:
                return run
            verdict = settle()
            if verdict is None:
                raise PhaseFailure(
                    f"{phase}: the sentinel was printed but there is nothing to "
                    f"judge - the phase's artifact does not exist")
            ok, gaps = verdict
            log(f"[audit] sufficient={ok} gaps={len(gaps)}")
            if ok:
                return run
            turn = _reopen(phase, run, chat, responder, gaps)
            continue

        answer = responder.reply(turn.text)
        run.replies = responder.replies
        log(f"[{responder.replies:>3}] {answer.source:<18} {answer.text[:80]!r}")
        turn = guard(chat.send(answer.text), phase)
        run.turns.append(turn)

        if answer.source == "policy:budget":
            verdict = settle() if settle else None
            if verdict is not None and not verdict[0]:
                turn = _reopen(phase, run, chat, responder, verdict[1])


def _reopen(phase: str, run: PhaseRun, chat, responder, gaps: list[str]):
    seed = responder.next_round(gaps)
    if seed is None:
        raise PhaseFailure(
            f"{phase}: rounds exhausted with gaps still open:\n  "
            + "\n  ".join(gaps))
    run.rounds = responder.rounds_used
    turn = guard(chat.send(seed), phase)
    run.turns.append(turn)
    return turn
