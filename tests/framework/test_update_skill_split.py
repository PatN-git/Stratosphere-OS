# md-crosscheck: router citations vs files that exist, and size budget
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


def test_references_carry_okf_frontmatter_and_a_heading():
    for name in REFS:
        text = (REFS_DIR / name).read_text(encoding="utf-8")
        fm = text.split("---\n", 2)[1]
        assert re.search(r"^description: \S", fm, re.M), f"{name}: description missing"
        assert re.search(r'^version: "\d+\.\d+\.\d+"$', fm, re.M) and re.search(
            r"^timestamp: \d{4}-\d{2}-\d{2}$", fm, re.M), f"{name}: version/timestamp"
        assert re.search(r"^# \S", text.split("---\n", 2)[2], re.M), f"{name}: one-line heading missing"


def test_skill_stays_lean():
    assert len(skill_text()) <= MAX_SKILL_CHARS, f"SKILL.md is {len(skill_text())} chars; budget {MAX_SKILL_CHARS}"


def test_update_skill_text_helper_joins_the_skill_and_every_cited_reference():
    from conftest import update_skill_text  # imported here so the guards above fail for their own reason
    combined = update_skill_text()
    assert combined.startswith(skill_text())
    for name in REFS:
        assert (REFS_DIR / name).read_text(encoding="utf-8") in combined
