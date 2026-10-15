#!/usr/bin/env python3
"""BT-175 guards: the scaffold ships `spec_lint.py` into `.agents/scripts/` and the bundled-script orphan guard maps it.
Workflow wiring guards join this file when the lint is wired into 2a/1b/1c/2c."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def test_scaffold_ships_spec_lint():
    assert '"spec_lint.py"' in _read("scripts/scaffold.py")


def test_orphan_guard_maps_spec_lint_to_agents_scripts():
    runner = (ROOT / "tests" / "runners" / "verify_scripts.py").read_text(encoding="utf-8")
    assert 'rel_str == "scripts/spec_lint.py"' in runner and '".agents/scripts/spec_lint.py"' in runner
