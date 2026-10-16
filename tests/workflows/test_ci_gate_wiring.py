#!/usr/bin/env python3
"""BT-187 guards: the CI gate is written into the constitution, the reference and the workflows, and shipped by the scaffold."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
CONSTITUTIONS = ("src/constitution/AGENTS.md", "AGENTS.md")
CONSTITUTION_BUDGET = 9200  # tests/framework/test_host_hygiene.py
SENTENCE = ("- **CI-fix exception:** after the ship confirmation, 4a (inline) or a 3z-dispatched 3d implementer may commit "
            "and push up to 2 `fix(BT-n): ci` commits for a failure `ci_gate.py` marks small; never `main`, never a merge. "
            "See `references/ci-gate.md`.")


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def _root(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_constitutions_carry_the_ci_fix_exception_once_within_budget():
    for rel in CONSTITUTIONS:
        text = _root(rel)
        assert text.count(SENTENCE) == 1, f"{rel} must carry the approved CI-fix sentence exactly once"
        assert len(text) <= CONSTITUTION_BUDGET, f"{rel} is {len(text)} chars (budget {CONSTITUTION_BUDGET})"
        sec4 = text.split("## 4. Version Control")[1].split("## 5.")[0]
        assert SENTENCE in sec4, "the exception belongs in section 4"
        assert "never merges" in sec4 and "Workflows never merge" in sec4, "the no-merge rule stays untouched"


def test_constitutions_are_bumped_to_3_4_0_and_section_8_is_unchanged():
    for rel in CONSTITUTIONS:
        text = _root(rel)
        assert re.search(r'^version: "3\.4\.0"$', text, re.M), f"{rel} needs the one per-PR bump"
        sec8 = text.split("## 8.")[1]
        assert "CI-fix" not in sec8, "a 3d implementer dispatched by 3z may already commit; section 8 stays as is"


def test_reference_exists_with_stamp_and_names_every_halt():
    text = _read("references/ci-gate.md")
    head = text.split("---")[1]
    assert re.search(r'^version: "\d+\.\d+\.\d+"$', head, re.M) and re.search(r"^timestamp: \d{4}-\d{2}-\d{2}$", head, re.M)
    assert re.search(r"^description: .+", head, re.M)
    for token in ("[CI-PARITY]", "[CI-RED]", "[CI-FIX]", "small", "big", "ci_gate.py parity", "ci_gate.py status", "ci_gate.py cap"):
        assert token in text, f"references/ci-gate.md lost {token!r}"


def test_scaffold_ships_ci_gate():
    assert '"ci_gate.py"' in _read("scripts/scaffold.py")


def test_verify_scripts_maps_ci_gate():
    verify = (ROOT / "tests" / "runners" / "verify_scripts.py").read_text(encoding="utf-8")
    assert 'rel_str == "scripts/ci_gate.py"' in verify and ".agents/scripts/ci_gate.py" in verify
