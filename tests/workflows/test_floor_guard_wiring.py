#!/usr/bin/env python3
"""BT-172 guards: 3d, 4a and 3z run the floor guard at the named points; the scaffold ships the script."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
GUARD = "python .agents/scripts/floor_guard.py"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def _section(text, start, end=None):
    i = text.index(start)
    j = text.index(end, i) if end else len(text)
    return text[i:j]


def test_scaffold_ships_floor_guard():
    assert '"floor_guard.py"' in _read("scripts/scaffold.py")


def test_3d_step6_runs_guard_before_full_run():
    phase3 = _read("workflows/3d-implement-issue.md").split("## Phase 3:")[1]
    step = next(l for l in phase3.splitlines() if l.startswith("6. "))
    assert GUARD in step and "Run the full suite once at HEAD" in step
    assert step.index(GUARD) < step.index("Run the full suite once at HEAD"), "a fix after the full run would stale the suite record"
    assert "exit 2" in step and "not a pass" in step
    assert "human-merged" in step, "an exception row must come from the default branch, never be self-written"


def test_4a_step0_and_ship_only_line_name_the_guard():
    text = _read("workflows/4a-verify-and-ship.md")
    step0 = next(l for l in text.splitlines() if l.startswith("0. **Clean-tree guard"))
    assert GUARD in step0 and "[FLOOR]" in step0
    assert "exit 2" in step0 and "before" in step0
    assert text.index("[FLOOR]") < text.index("Context Isolation Rule")
    line = next(l for l in text.splitlines() if l.startswith("> **Named gate — `ship-only`"))
    assert "floor guard" in line


def test_3z_2a_orchestrator_runs_guard_never_implementer_and_3a_halts_on_floor():
    z = _read("workflows/3z-afk-loop.md")
    step_2a = _section(z, "### Step 2A", "### Step 2B")
    assert GUARD in step_2a and "Orchestrator" in step_2a
    assert "Step 2B" in step_2a.split(GUARD)[1], "a failing guard must skip Step 2B like `stuck`"
    assert "Step 2C" in step_2a.split(GUARD)[1]
    gate = _section(z, "### Step 2C", "## Phase 3:")
    assert "[FLOOR]" in gate and "attempt" in gate
    assert "[FLOOR]" in _section(z, "### Step 3A", "### Step 3B")
