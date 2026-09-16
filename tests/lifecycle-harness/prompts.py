#!/usr/bin/env python3
"""L3 Slice 3 - the opening turn of each phase, and nothing more.

Everything after the first turn belongs to the responder (Slice 0). These files
carry three things and no fourth: the invocation, enough context for the phase to
start, and a sentinel to print when it is done.

**A missing sentinel is a failure, never a skip.** It is the only evidence that a
phase ran to its own end rather than stopping somewhere in the middle with prose
that reads like success - which is why the sentinel is derived here rather than
written by hand per file, and why `test_l3_prompts.py` checks that each file
actually contains its own.

**The prompts do not carry the fixture.** `fixture/topic.md` belongs to the User
Proxy alone. Handing it to the driver would give `1b` the answers to its own grill,
and the brief it wrote would then be a transcription rather than a discovery - the
same collapse `1b:64` guards against. The prompts name the SUBJECT in one line; the
positions behind it stay with the proxy.

Phase order is the coverage the plan states: `0a` twice, because `0a` behaves
differently greenfield (halts, touches nothing) and post-backlog (restores state).
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).parent / "prompts"

# The driven chain, in order. `4a` runs its `audit-only` gate; `ship-only` is out of
# scope (fact 12) - a non-UI fixture has no theme.tokens.css, so Phase 5.2 would fail
# for a reason unrelated to anything L3 tests.
PHASES = ("0a", "1a", "1b", "2a", "2b", "0a-second", "3b", "3d", "4a", "0b")


def sentinel(phase: str) -> str:
    return f"L3-{phase.upper()}-COMPLETE"


def load(phase: str) -> str:
    path = HERE / f"{phase}.txt"
    if not path.exists():
        raise FileNotFoundError(f"no opening prompt for phase {phase!r} at {path}")
    return path.read_text(encoding="utf-8").strip()
