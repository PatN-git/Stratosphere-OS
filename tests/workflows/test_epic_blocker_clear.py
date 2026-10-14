#!/usr/bin/env python3
"""BT-162 F5 guards: an epic-level blocker is cleared when the epic flips to `in review`, the gate
covers it, heals remove a stale blocker on both sides, and 0b re-checks after its post-merge clearing."""
from conftest import read_repo as _text


def _between(text: str, start: str, end: str) -> str:
    return text[text.index(start):text.index(end)]


def test_4a_step8_clears_the_epic_id_from_dependents_after_the_flip():
    step8 = _between(_text("src/workflows/4a-verify-and-ship.md"), "8. **Epic Check:**", "9. **Terminal sync gate:**")
    assert "Standing epic" in step8 and step8.index("Standing epic") < step8.index("**every sibling")
    flip = step8.index('--add-label "status:in review"')
    clear = step8.index("clear `BT-<parent>` from every dependent's `Blocked by`")
    assert flip < clear, "the epic-id clear follows the epic's flip to in review"
    assert "`removeBlockedBy`" in step8[clear:] and "step 7" in step8[clear:]


def test_4a_step9_passes_dependents_cleared_in_step_7_or_8():
    step9 = _between(_text("src/workflows/4a-verify-and-ship.md"), "9. **Terminal sync gate:**", "10. **Cleanup:**")
    assert "<each dependent cleared in Step 7 or 8>" in step9
    assert "--fields status,blocked_by" in step9


def test_terminal_sync_heal_clears_a_stale_blocker_on_both_sides():
    ref = _text("src/references/terminal-sync-invariant.md")
    heal = _between(ref, "## Heal", "## Boundaries")
    assert "stale blocker" in heal and "map cell" in heal and "`removeBlockedBy`" in heal
    assert "(slice or epic id)" in ref
    assert heal.index("stale blocker") < heal.index("re-run `reconcile.py`")


def test_0b_gates_its_post_merge_clearing_with_a_bounded_reconcile():
    step1 = _between(_text("src/workflows/0b-stop-session.md"), "1. Compare completed", "2. Update")
    assert "reconcile.py --require-gh --ids <cleared dependents> --fields blocked_by" in step1
    assert "If any dependent was cleared, run" in step1, "--ids must never be empty"
    assert "at most 3 attempts" in step1


def test_4a_step7_clear_blockers_is_one_clean_sentence_chain():
    step7 = _between(_text("src/workflows/4a-verify-and-ship.md"), "7. **Ship-status", "8. **Epic Check:**")
    bullet = step7.split("**Clear blockers (single writer for this edge):**")[1]
    assert "`Blocked by` in `.memory/BACKLOG_MAP.md` **and** the GitHub blocked-by relationship" in bullet
    assert "Refresh `generated.at`" in bullet and bullet.index("Refresh") > bullet.index("faithful mirror")


def test_0b_handoff_has_a_framework_feedback_line():
    handoff = _between(_text("src/workflows/0b-stop-session.md"), "## Handoff Note Format", "## Constraints")
    assert "- Framework feedback (skill · installed version · defect · evidence · suggested fix):" in handoff
    assert handoff.index("New glossary terms") < handoff.index("Framework feedback") < handoff.index("Follow-ups proposed")
