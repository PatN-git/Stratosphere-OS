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


def _section(text, start, end=None):
    i = text.index(start)
    j = text.index(end, i) if end else len(text)
    return text[i:j]


def _4a():
    return _read("workflows/4a-verify-and-ship.md")


STATUS = "python .agents/scripts/ci_gate.py status"


def test_4a_step4_runs_parity_after_the_release_commit_and_before_the_push():
    step4 = _section(_4a(), "4. **Release bump + push:**", "5. **PR (one per feature branch):**")
    assert "python .agents/scripts/ci_gate.py parity" in step4 and "[CI-PARITY]" in step4
    assert step4.index("release: prepare") < step4.index("ci_gate.py parity") < step4.index("Push the branch")
    assert "references/ci-gate.md" in step4 and "waive" in step4 and "tree changed" in step4


def test_4a_step8_runs_the_status_gate_after_the_audit_and_before_the_rebuild_and_ready():
    step8 = _section(_4a(), "8. **Epic Check:**", "9. **Terminal sync gate:**")
    assert STATUS in step8
    assert step8.index("Feature Acceptance Audit") < step8.index(STATUS) < step8.index("--close-parent") < step8.index("gh pr ready")
    for token in ("[CI-RED]", "[CI-FIX]", "--attempt", "--expect-checks", "--sha", "references/ci-gate.md"):
        assert token in step8, f"step 8 lost {token!r}"


def test_4a_step8_red_big_holds_the_pr_draft_and_the_epic_and_keeps_the_slice_in_review():
    step8 = _section(_4a(), "8. **Epic Check:**", "9. **Terminal sync gate:**")
    red = step8[step8.index("[CI-RED]"):]
    assert "draft" in red and "`in progress`" in red and "stays `in review`" in red
    assert "/3b-create-issue" in red and "step 9" in red


def test_4a_step8_under_3z_returns_ci_fix_without_committing():
    step8 = _section(_4a(), "8. **Epic Check:**", "9. **Terminal sync gate:**")
    assert "3z" in step8 and "does not commit" in step8 and "`[CI-FIX]`" in step8


def test_4a_standalone_issue_runs_the_gate_right_after_the_status_flip():
    step7 = _section(_4a(), "7. **Ship-status + backport:**", "8. **Epic Check:**")
    assert "Standalone issue" in step7 and STATUS in step7 and "non-draft" in step7


def test_4a_gate_is_wired_exactly_twice_and_never_in_the_audit_phases():
    text = _4a()
    assert text.count(STATUS) == 2, "standalone (step 7) and completing ship (step 8) only, never per intermediate slice"
    assert "ci_gate" not in _section(text, "## Phase 2", "## Phase 5"), "an audit-only run must never reach the gate"
    assert "ci_gate" in _section(text, "## Phase 5")


def test_4a_ship_line_names_a_pending_check_and_a_waived_parity():
    ship = next(line for line in _4a().splitlines() if line.startswith("11. Output:"))
    assert "ci:pending" in ship and "parity:waived" in ship
