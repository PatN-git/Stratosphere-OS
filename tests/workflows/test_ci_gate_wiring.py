#!/usr/bin/env python3
"""BT-187 guards: the CI gate is written into the constitution, the reference and the workflows, and shipped by the scaffold."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
CONSTITUTIONS = ("src/constitution/AGENTS.md", "AGENTS.md")
CONSTITUTION_BUDGET = 9200  # tests/framework/test_host_hygiene.py
SENTENCE = ("- **CI-fix exception:** after the ship confirmation, 4a may commit and push up to 2 `fix(BT-n): ci` commits "
            "for a failure `ci_gate.py` marks small; a 3z-dispatched 3d implementer only commits, `ship-only` pushes; "
            "never `main`, never a merge. See `references/ci-gate.md`.")


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
    for token in ("[CI-RED]", "[CI-FIX]", "small", "big", "ci_gate.py status", "ci_gate.py cap"):
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


def test_no_pre_push_parity_replay_is_wired_anywhere():
    """BT-187 measured a local CI replay at 113 s against about 45 s on GitHub and dropped it; nothing may bring it back unseen."""
    script = _read("scripts/ci_gate.py")
    assert "parity" not in script and "select_steps" not in script
    for rel in ("workflows/4a-verify-and-ship.md", "workflows/3z-afk-loop.md", "references/ci-gate.md"):
        text = _read(rel)
        assert "ci_gate.py parity" not in text and "[CI-PARITY]" not in text and "parity:waived" not in text, rel
    step4 = _section(_4a(), "4. **Release bump + push:**", "5. **PR (one per feature branch):**")
    assert step4.rstrip().endswith("Push the branch.") and "ci_gate" not in step4
    assert "replaying CI locally before the push" in _read("references/ci-gate.md")


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


def test_4a_ship_line_names_a_pending_check():
    ship = next(line for line in _4a().splitlines() if line.startswith("11. Output:"))
    assert "ci:pending" in ship


def _3z():
    return _read("workflows/3z-afk-loop.md")


def _step3a():
    return _section(_3z(), "### Step 3A", "### Step 3B")


def test_3z_step3a_runs_the_gate_once_per_feature_and_delegates_the_fix_to_a_3d_implementer():
    step = _step3a()
    for token in ("references/ci-gate.md", "`[CI-FIX]`", "fresh 3d implementer", "ci_gate.py cap", "floor_guard.py",
                  "`ship-only`", "never per intermediate slice", "do NOT push", "skip the Phase 0 status flip"):
        assert token in step, f"3z Step 3A lost {token!r}"
    assert "fix(BT-<padded>): ci - <step>" in step, "3z names the commit subject the 3d implementer must use"


def test_3z_halt_list_names_the_ci_halts_and_keeps_the_literal_flag():
    step = _step3a()
    assert "[BLOCKED-ship] <the halt message>" in step and "continue the frontier" in step
    assert "`[CI-RED]`" in step
    assert "pushed" in step and "held draft" in step, "a halt after the push must not claim the slice stayed local"


def test_3z_never_mints_an_issue_for_a_big_ci_failure_and_never_runs_the_gate_in_audit_only():
    z = _3z()
    step = _step3a()
    assert "never mints" in step and "3b" in step and "HITL" in step
    assert "ci_gate" not in _section(z, "### Step 2B", "### Step 2C"), "audit-only must never reach the CI gate"


def test_3d_honors_the_ci_fix_dispatch_overrides():
    d = _read("workflows/3d-implement-issue.md")
    step2 = next(line for line in d.splitlines() if line.startswith("2. Read slice issue."))
    assert "CI fix" in step2 and "references/ci-gate.md" in step2 and "skips this flip" in step2
    commits = next(line for line in d.splitlines() if line.startswith("3. **Incremental Commits:**"))
    assert "fix(BT-<slicePadded>): ci - <step>" in commits


def test_4a_step6_skips_a_duplicate_pr_link_comment():
    step6 = _section(_4a(), "6. **PR-link comment", "7. **Ship-status + backport:**")
    assert "already" in step6 and "CI fix" in step6


def _fix_order_ok(text):
    """True when section 3 of the reference runs the fix steps in the safe order and states the 2-commit cap."""
    fix = text[text.index("## 3. Fix"):text.index("## 4. Big")]
    order = ["test_gate.py record --suite", "commit;", "ci_gate.py cap --commit HEAD", "floor_guard.py", "push;", "status --attempt"]
    positions = [fix.find(token) for token in order]
    return all(p >= 0 for p in positions) and positions == sorted(positions) and "at most 2 fix commits" in fix.lower()


def test_reference_runs_each_fix_in_the_safe_order_with_the_two_commit_cap():
    ref = _read("references/ci-gate.md")
    assert _fix_order_ok(ref)
    fix = ref[ref.index("## 3. Fix"):ref.index("## 4. Big")]
    assert "[FLOOR]" in fix and "never `main`, never a merge" in fix and "[CI-FIX]" in fix


def test_3z_fix_loop_states_one_round_two_commits_suite_first_and_the_safe_order():
    step = _step3a()
    assert "At most 2 fix commits" in step and "one round" in step and "`--attempt 2`" in step
    assert "record the full suite (`test_gate.py record --suite`) before the commit" in step
    order = ["ci_gate.py cap", "floor_guard.py", "re-runs `ship-only`"]
    positions = [step.index(token) for token in order]
    assert positions == sorted(positions), "cap and floor guard run before ship-only pushes again"


def test_4a_step8_names_the_two_status_runs_and_points_to_the_fix_rule():
    step8 = _section(_4a(), "8. **Epic Check:**", "9. **Terminal sync gate:**")
    assert "--attempt 1" in step8 and "--attempt 2" in step8 and "§3" in step8
    step7 = _section(_4a(), "7. **Ship-status + backport:**", "8. **Epic Check:**")
    assert "--attempt 1" in step7


def test_reference_states_one_attempt_rule_and_matches_the_script_behavior():
    ref = _read("references/ci-gate.md")
    assert "one fix round" in ref.lower() and "`--attempt 2`" in ref
    assert "worst state" in ref, "the script keeps the worst state of a check's runs"
    assert "ending at the failing step's last `##[error]`" in ref and "`sha`" in ref


def test_status_calls_name_the_host_tool_timeout_and_exit_2_is_a_halt():
    ref = _read("references/ci-gate.md")
    step7 = _section(_4a(), "7. **Ship-status + backport:**", "8. **Epic Check:**")
    step8 = _section(_4a(), "8. **Epic Check:**", "9. **Terminal sync gate:**")
    for name, text in (("reference", ref), ("4a step 7", step7), ("4a step 8", step8)):
        assert "timeout" in text and "--wait" in text, f"{name} must say how to keep the 480 s wait inside the host tool timeout"
    assert "600000" in step8 and "600000" in step7
    for name, text in (("reference", ref), ("4a step 8", step8), ("3z Step 3A", _step3a())):
        assert "exit 2" in text and "could not check" in text, f"{name} must treat exit 2 from status or cap as a halt"
    assert "cannot_run" in ref.split("## 2. Status")[1].split("## 3.")[0]


def test_the_constitution_says_the_implementer_only_commits_and_ship_only_pushes():
    for rel in CONSTITUTIONS:
        sentence = next(line for line in _root(rel).splitlines() if line.startswith("- **CI-fix exception:**"))
        assert "only commits" in sentence and "`ship-only` pushes" in sentence
    ref = _read("references/ci-gate.md")
    assert "does not push" in ref or "no push" in ref


def test_reference_states_the_fix_cap_once():
    fix = _read("references/ci-gate.md").split("## 3. Fix")[1].split("## 4. Big")[0]
    assert fix.lower().count("at most 2 fix commits") == 1 and fix.lower().count("one fix round") <= 1
