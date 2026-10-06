#!/usr/bin/env python3
"""BT-138 guards: related tests per cycle, one full-suite run per slice, result reuse in 4a."""
import re
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
    text = _read("workflows/4a-verify-and-ship.md") + _read("references/pr-body-and-ship.md")
    assert ".tmp/3d-suite-BT-" in text
    assert "head_sha" in text
    assert "observed" in text
    assert "Never delete these files" in text


def test_3d_clean_tree_check_runs_after_the_full_suite_and_step_refs_resolve():
    """Files the suite generates must be caught: the clean-tree check follows the full run, and "step N" cites stay correct."""
    phase3 = _read("workflows/3d-implement-issue.md").split("## Phase 3:")[1]
    steps = {int(m.group(1)): m.group(2) for m in re.finditer(r"^(\d+)\. (.*)$", phase3, re.M)}

    def cites(s):  # "Phase 1 step 0" points into another workflow, not at a Phase 3 step
        return [int(c) for c in re.findall(r"step (\d+)", re.sub(r"Phase \S+ step \d+", "", s))]

    full = next(n for n, s in steps.items() if "Run the full suite once at HEAD" in s)
    clean = next(n for n, s in steps.items() if "git status --porcelain" in s)
    assert clean > full, f"clean-tree step {clean} must come after the full-suite step {full}"
    assert all(c in steps for s in steps.values() for c in cites(s)), "a step cites a step that does not exist"
    done_gate = next(s for s in steps.values() if s.startswith("Done only when"))
    assert cites(done_gate) == [full], "the done gate must cite the full-suite step"
