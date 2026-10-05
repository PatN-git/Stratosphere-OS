#!/usr/bin/env python3
"""BT-138 guards: related tests per cycle, one full-suite run per slice, result reuse in 4a."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def test_micro_tdd_runs_related_tests_not_a_full_sweep():
    text = _read("skills/micro-tdd/SKILL.md")
    assert "full-suite sweep" not in text
    assert "related to the changed files" in text


def test_micro_tdd_stays_generic():
    text = _read("skills/micro-tdd/SKILL.md")
    assert ".tmp/" not in text, "execution skill must not name workflow scratch paths"


def test_3d_owns_the_single_full_run_and_records_it():
    text = _read("workflows/3d-implement-issue.md")
    assert ".tmp/3d-suite-BT-<padded>.json" in text
    assert "3d owns the full-suite runs" in text
    assert "no tracked writes" in text
    assert "Ephemeral (no writes)" not in text
    assert "return to the micro-tdd loop" in text.split("Run the full suite once at HEAD")[1]


def test_4a_reuses_suite_result_by_head_sha():
    text = _read("workflows/4a-verify-and-ship.md")
    assert ".tmp/3d-suite-BT-" in text
    assert "head_sha" in text
    assert "observed" in text
    assert "Never delete these files" in text
