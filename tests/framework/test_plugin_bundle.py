"""BT-150: the Antigravity plugin install (`agy plugin install dist`) is a first-class location.

`agy` copies the plugin to ~/.gemini/config/plugins/stratosphere-os/ (manifest + skills/), so the
installed scaffolder lives at .../plugins/stratosphere-os/skills/stratosphere-setup/. Setup and update
must find it there, the retired v4 plugin branch must stay gone (unreachable: the skills only run from
an installed bundle, and check_suite legacy cleans leftovers), and the release checklist must name both
plugin validators.
"""
import re

import pytest

from conftest import REPO_ROOT, update_skill_text

PLUGIN_SETUP_DIR = "~/.gemini/config/plugins/stratosphere-os/skills/stratosphere-setup/"
SETUP_SKILL = "src/commands/stratosphere-setup/SKILL.md"
UPDATE_SKILL = "src/commands/stratosphere-update/SKILL.md"
SYNC_SKILL = "src/commands/sync-skills/SKILL.md"
PROPOSAL = "docs/proposals/upstream-watch-2026-10-adjustments.md"


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def flow(rel: str) -> str:
    """The skill's text; for the update skill, SKILL.md plus the references its update paths moved to."""
    return update_skill_text() if rel == UPDATE_SKILL else read(rel)


def bullet(rel: str, marker: str) -> str:
    line = next((candidate for candidate in flow(rel).splitlines() if marker in candidate), None)
    assert line, f"{rel} has no {marker!r} bullet"
    return line


@pytest.mark.parametrize("rel", [SETUP_SKILL, UPDATE_SKILL, SYNC_SKILL])
def test_setup_update_and_sync_find_the_antigravity_plugin_install(rel):
    assert PLUGIN_SETUP_DIR in read(rel), f"{rel} must list the agy plugin install location"


def test_sync_skills_lists_the_plugin_install_before_the_marketplace_cache():
    text = read(SYNC_SKILL)
    assert text.index(PLUGIN_SETUP_DIR) < text.index("marketplace cache")


def test_releasing_lists_both_plugin_validators():
    text = read("RELEASING.md")
    assert "claude plugin validate ." in text
    assert "agy plugin validate dist" in text
    assert re.search(r"skills: \d+ processed", text), "RELEASING must record the observed agy output"


def test_releasing_does_not_pin_the_skill_count_or_a_stale_tree():
    text = read("RELEASING.md")
    expected, dry_run = text.split("*Recorded dry run", 1)
    assert "skills: <N> processed" in expected, "the expected count is the dist/skills directory count, not a literal"
    assert not re.search(r"skills\s*: \d+ processed", expected), "no literal skill count outside the recorded dry run"
    assert "working tree before the 4.5.0 bump" in dry_run and "tree at v4.4.0" not in text
    assert "`claude plugin validate .` could not run" in dry_run, "keep the honest not-run note"


@pytest.mark.parametrize("rel", [SETUP_SKILL, UPDATE_SKILL])
def test_retired_v4_plugin_install_branch_is_gone(rel):
    text = flow(rel).lower()
    assert "retired v4" not in text and "legacy v4 plugin installs" not in text, \
        f"{rel}: the retired v4 plugin branch is unreachable prose; check_suite.py legacy handles leftovers"


def test_update_refreshes_an_antigravity_plugin_install_by_reinstalling_dist():
    assert PLUGIN_SETUP_DIR in bullet(UPDATE_SKILL, "**Antigravity plugin install** (path")
    text = flow(UPDATE_SKILL)
    assert "agy plugin install" in text and "<tmp>/dist" in text, "update must reinstall from the tag clone's dist"


def test_update_deletes_the_throwaway_clone_on_every_outcome():
    """A HALT after a failed clone or agy exit must not leave <tmp> behind (both clone paths)."""
    lines = [line for line in flow(UPDATE_SKILL).splitlines() if "Delete `<tmp>`" in line]
    assert len(lines) == 2, "expected the plugin-install and the copied-skills clone steps"
    for line in lines:
        assert "on every outcome" in line and "HALT" in line.split("on every outcome", 1)[1], line


def test_proposal_status_records_what_shipped():
    status = next(line for line in read(PROPOSAL).splitlines() if line.startswith("**Status:**"))
    assert "nothing implemented" not in status
    for needle in ("PR #151", "BT-148", "BT-149", "BT-150", "host-matrix.md", "kept as evidence"):
        assert needle in status, f"Status line must mention {needle}"
    assert "`AGENTS.md:69-71`" in status and "no longer exists" in status
