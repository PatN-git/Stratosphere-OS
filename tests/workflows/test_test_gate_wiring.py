#!/usr/bin/env python3
"""BT-153 guards: the pre-commit test gate ships to projects, setup offers it, update advises, 3d records through it."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
RECORD = "python .agents/scripts/test_gate.py record --"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def test_scaffold_ships_the_gate_to_projects():
    assert '"test_gate.py"' in _read("scripts/scaffold.py")


def test_setup_offers_the_gate_as_opt_in():
    setup = _read("commands/stratosphere-setup/SKILL.md")
    cp = setup.split("### Checkpoint 5.3: Test gate (opt-in)")[1].split("## Checkpoint 6")[0]
    assert "python .agents/scripts/test_gate.py install" in cp
    assert "ask" in cp.lower() and "never install without" in cp.lower()


def test_update_only_advises_when_the_gate_is_absent():
    update = _read("commands/stratosphere-update/SKILL.md").split("## Phase 4:")[1].split("## Phase 5:")[0]
    assert "python .agents/scripts/test_gate.py status" in update
    assert "do not install" in update


def test_3d_records_test_runs_through_the_gate_and_never_bypasses_it():
    text = _read("workflows/3d-implement-issue.md")
    phase2 = text.split("## Phase 2:")[1].split("## Phase 3:")[0]
    commits = next(l for l in phase2.splitlines() if "**Incremental Commits:**" in l)
    assert RECORD in commits and "--no-verify" in commits
    phase3 = text.split("## Phase 3:")[1]
    full = next(l for l in phase3.splitlines() if "Run the full suite once at HEAD" in l)
    assert RECORD in full
