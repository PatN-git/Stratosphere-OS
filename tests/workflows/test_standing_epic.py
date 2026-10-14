#!/usr/bin/env python3
"""BT-167 guards: the standing-epic rule is defined once and cited at each step it changes;
4a's release bump reruns at every ship."""
from conftest import read_repo as _text

REF = "references/terminal-sync-invariant.md"
CITE = f"{REF}` §Standing epic"


def _between(text: str, start: str, end: str) -> str:
    return text[text.index(start):text.index(end)]


def _rule() -> str:
    return _text("src/references/terminal-sync-invariant.md").split("## Standing epic")[1]


def test_predicate_is_stated_once_with_both_conditions():
    rule = _rule()
    first = rule.split("\n- ")[0]
    assert "no `BT-<parentPadded>` row in `.memory/BACKLOG_MAP.md`" in first, "no-BACKLOG-row condition missing"
    assert "no `status:*` label" in first and "offline: BACKLOG only" in first, "no-status-label condition missing"
    assert first.count("**standing**") == 1
    for rel in ("3d-implement-issue", "4a-verify-and-ship", "3b-create-issue", "3z-afk-loop", "0a-start-session"):
        assert "**standing**" not in _text(f"src/workflows/{rel}.md"), f"{rel} restates the definition"


def test_rule_covers_branch_promotion_draft_and_close_parent():
    rule = _rule()
    for token in ("`<type>/BT-<slicePadded>-<slug>`", "Never promote it", "reconcile.py --ids",
                  "non-draft", "no `--close-parent`", "no Feature Acceptance Audit"):
        assert token.lower() in rule.lower(), f"standing-epic rule lost {token!r}"


def test_3d_steps_1_and_2_cite_the_rule():
    text = _text("src/workflows/3d-implement-issue.md")
    step1 = _between(text, "1. **Branch Isolation:**", "2. Read slice issue.")
    step2 = _between(text, "2. Read slice issue.", "3. **Conditional Read:**")
    assert CITE in step1 and "<type>/BT-<slicePadded>-<slug>" in step1 and "user names" in step1
    assert CITE in step2 and "never a standing epic" in step2


def test_3b_defensive_promotion_skips_a_standing_epic():
    text = _text("src/workflows/3b-create-issue.md")
    step2 = _between(text, "2. **Defensive epic promotion", "3. **Scope:**")
    assert CITE in step2 and "standing epic" in step2


def test_4a_steps_cite_the_rule():
    text = _text("src/workflows/4a-verify-and-ship.md")
    contract = _between(text, "**Hand-off contract:**", "## Phase 0")
    step1 = _between(text, "1. **Branch isolation:**", "2. **CSS check")
    step5 = _between(text, "5. **PR (one per feature branch):**", "6. **PR-link comment")
    step8 = _between(text, "8. **Epic Check:**", "9. **Terminal sync gate:**")
    step9 = _between(text, "9. **Terminal sync gate:**", "10. **Cleanup:**")
    assert CITE in contract and "non-draft" in contract
    assert CITE in step1 and "user-named branch" in step1 and "NOT `main`/`master`" in step1
    assert CITE in step5 and "standing-epic slice" in step5 and "non-draft" in step5
    assert CITE in step8 and step8.index("Standing epic") < step8.index("**every sibling")
    assert "never a standing epic" in step9 and "standing-epic slice" in step9.split("**Draft rule**")[1]


def test_4a_step4_reruns_release_at_every_ship_and_commits_only_if_changed():
    text = _text("src/workflows/4a-verify-and-ship.md")
    step4 = _between(text, "4. **Release bump + push:**", "5. **PR (one per feature branch):**")
    assert "once per PR" not in step4
    assert "at every ship" in step4
    assert "only if its output changed" in step4 and "`release: prepare v<x>`" in step4
    assert step4.index("scripts/release.py") < step4.index("Push the branch")


def test_3z_groups_and_promotes_per_the_rule():
    text = _text("src/workflows/3z-afk-loop.md")
    group = _between(text, "3. **Group** slices", "4. Detect `gh auth status`")
    activate = _between(text, "1. **Activate Slice (Orchestrator):**", "2. **Dispatch Implementer")
    ship = _between(text, "2. **Execute Ship (once per slice):**", "_Done when:_ every all-passed")
    assert CITE in group and "its own feature" in group
    assert CITE in activate and "never a standing epic" in activate
    assert CITE in ship and "never for a standing epic" in ship


def test_0a_promotion_skips_a_standing_epic():
    text = _text("src/workflows/0a-start-session.md")
    step3 = _between(text, "3. **State transition (first-slice rule):**", "## Output Pattern")
    assert CITE in step3 and "never a standing epic" in step3


def test_constitution_granularity_allows_a_slice_branch_for_a_standing_epic():
    for rel in ("src/constitution/AGENTS.md", "AGENTS.md"):
        lines = _text(rel).splitlines()
        granularity = [ln for ln in lines if ln.startswith("- **Granularity:**")][0]
        branch = [ln for ln in lines if ln.startswith("- **Branch name:**")][0]
        assert "a slice under a standing epic, degenerates to its own branch+PR" in granularity, rel
        assert "standing-epic slice: `<type>/BT-<slicePadded>-<slug>`" in branch and "§Standing epic" in branch, rel


def test_4a_pr_title_for_a_standing_epic_is_slice_keyed():
    text = _text("src/workflows/4a-verify-and-ship.md")
    step5 = _between(text, "5. **PR (one per feature branch):**", "6. **PR-link comment")
    assert "standing epic: `<type>(BT-<slicePadded>): <slice title>`" in step5 and "keeps its existing PR title" in step5
