#!/usr/bin/env python3
"""BT-144 follow-up guard: 0b reuses the recorded suite result via pr_body.py instead of re-running it."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEXT = (ROOT / "src" / "workflows" / "0b-stop-session.md").read_text(encoding="utf-8")


def _step9() -> str:
    return TEXT.split("\n9. ")[1].split("\n10. ")[0]


def test_0b_step9_reuses_suite_result_via_pr_body_suite():
    step9 = _step9()
    assert "python .agents/scripts/pr_body.py suite" in step9
    assert "else run" in step9
    assert "python .agents/scripts/validate_memory.py" in step9


def test_0b_does_not_restate_the_reuse_rule():
    assert "release: prepare" not in TEXT and "head_sha" not in TEXT
