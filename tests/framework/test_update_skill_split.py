"""PR #151 round 3: the update skill stays lean.

The host-specific "Out of date" update paths live in src/references/update-*.md and SKILL.md only
routes to them; the pre-v4 layout phase is deleted (both known projects are post-v4). These guards
keep SKILL.md small and keep every moved path's confirm-once gate and HALT intact.
"""
import re

from conftest import REPO_ROOT

SKILL = REPO_ROOT / "src" / "commands" / "stratosphere-update" / "SKILL.md"
REFS_DIR = REPO_ROOT / "src" / "references"
# Detection order, which is also the router's row order.
REFS = ("update-claude-marketplace.md", "update-antigravity-plugin.md", "update-copied-skills.md")
# The "(path" suffix tells the branch header apart from the locate list's `**Antigravity plugin install** (`agy ...`) entry.
MOVED_HEADINGS = ("**Claude Marketplace Cache** (path", "**Antigravity plugin install** (path",
                  "**Antigravity / copied-skills Install** (path")
UPDATE_CITE = re.compile(r"(?<![\w/.])references/(update-[A-Za-z0-9_.-]+\.md)")
MAX_SKILL_CHARS = 13500  # ~13.2k after the split (18.8k before); room for small edits, not for re-inlining a branch


def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_router_cites_exactly_the_three_update_references_and_they_exist():
    cited = set(UPDATE_CITE.findall(skill_text()))
    assert cited == set(REFS), f"router must cite exactly {REFS}, found {sorted(cited)}"
    for name in cited:
        assert (REFS_DIR / name).is_file(), f"src/references/{name} is cited but missing"


def test_router_keeps_detection_order_with_git_checkout_and_catch_all_inline():
    text = skill_text()
    order = [text.index(f"references/{name}") for name in REFS]
    order += [text.index("**In-place Git Checkout**"), text.index("**Else / Catch-all")]
    assert order == sorted(order), "detection order: marketplace, agy plugin, copied skills, git checkout, catch-all"
    out_of_date = text[text.index("**Out of date:**"):text.index("**In-place Git Checkout**")]
    assert "HALT" in out_of_date and re.search(r"confirm[- ]once", out_of_date, re.I), \
        "router must state the invariant: confirm-once gate + HALT on every update path"


def test_router_rows_map_each_path_condition_to_its_own_reference():
    """Swapping two rows' conditions would send an update down the wrong host's path."""
    markers = {"update-claude-marketplace.md": "~/.claude/plugins/cache/",
               "update-antigravity-plugin.md": "~/.gemini/config/plugins/stratosphere-os/skills/stratosphere-setup/",
               "update-copied-skills.md": "~/.agents/skills/"}
    rows = [line for line in skill_text().splitlines() if line.lstrip().startswith("|") and "references/update-" in line]
    assert len(rows) == len(REFS)
    for ref, marker in markers.items():
        (row,) = [r for r in rows if f"references/{ref}" in r]
        condition = row.split("|")[1]
        assert marker in condition, f"{ref}: its path condition must name {marker}"
        for other_ref, other_marker in markers.items():
            if other_ref != ref:
                assert other_marker not in condition, f"{ref}: condition also names {other_marker}"


def test_router_invariant_allows_only_an_explicit_user_override():
    text = skill_text()
    assert "no path continues to Phase 1 except an explicit user override that the reference names" in text
    assert "First match wins" in text


def test_each_reference_keeps_its_confirm_once_gate_and_halt():
    for name in REFS:
        text = (REFS_DIR / name).read_text(encoding="utf-8")
        assert "Confirm once" in text, f"{name}: confirm-once gate is gone"
        assert "HALT" in text, f"{name}: HALT is gone"


def test_references_carry_okf_frontmatter_and_a_heading():
    for name in REFS:
        text = (REFS_DIR / name).read_text(encoding="utf-8")
        fm = text.split("---\n", 2)[1]
        assert re.search(r"^description: \S", fm, re.M), f"{name}: description missing"
        assert 'version: "1.0.0"' in fm and "timestamp: 2026-10-07" in fm, f"{name}: version/timestamp"
        assert re.search(r"^# \S", text.split("---\n", 2)[2], re.M), f"{name}: one-line heading missing"


def test_skill_stays_lean():
    assert len(skill_text()) <= MAX_SKILL_CHARS, f"SKILL.md is {len(skill_text())} chars; budget {MAX_SKILL_CHARS}"


def test_pre_v4_layout_phase_is_gone_and_phases_are_renumbered():
    text = skill_text()
    for gone in ("Pre-v4", "PRE-V4", "migrate_v3_to_v4", "Phase 0.6"):
        assert gone not in text, f"{gone!r} must not survive in SKILL.md"
    phase0 = text.index("## Phase 0: Plugin Freshness")
    suite = text.index("## Phase 0.5: Suite Integrity & Legacy Cleanup")
    assert phase0 < suite < text.index("## Phase 1: Compute Update Scope")
    assert text.count("## Phase 0.5") == 1


def test_moved_branches_are_not_inline_but_the_tiny_ones_are():
    text = skill_text()
    for heading in MOVED_HEADINGS:
        assert heading not in text, f"{heading} moved to its reference"
    assert "git clone" not in text and "install-antigravity-bridge" not in text and "claude plugin update" not in text
    assert "**In-place Git Checkout**" in text and "**Else / Catch-all" in text


def test_update_skill_text_helper_joins_the_skill_and_every_cited_reference():
    from conftest import update_skill_text  # imported here so the guards above fail for their own reason
    combined = update_skill_text()
    assert combined.startswith(skill_text())
    for name in REFS:
        assert (REFS_DIR / name).read_text(encoding="utf-8") in combined
