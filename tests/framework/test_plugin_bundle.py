"""BT-150: the Antigravity plugin install (`agy plugin install dist`) is a first-class location.

`agy` copies the plugin to ~/.gemini/config/plugins/stratosphere-os/ (manifest + skills/), so the
installed scaffolder lives at .../plugins/stratosphere-os/skills/stratosphere-setup/. Setup and update
must find it there, the retired v4 plugin branch must stay gone (unreachable: the skills only run from
an installed bundle, and check_suite legacy cleans leftovers), and the release checklist must name both
plugin validators.
"""
import pytest

from conftest import REPO_ROOT

PLUGIN_SETUP_DIR = "~/.gemini/config/plugins/stratosphere-os/skills/stratosphere-setup/"
SETUP_SKILL = "src/commands/stratosphere-setup/SKILL.md"
UPDATE_SKILL = "src/commands/stratosphere-update/SKILL.md"


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def bullet(rel: str, marker: str) -> str:
    line = next((candidate for candidate in read(rel).splitlines() if marker in candidate), None)
    assert line, f"{rel} has no {marker!r} bullet"
    return line


@pytest.mark.parametrize("rel", [SETUP_SKILL, UPDATE_SKILL])
def test_setup_and_update_find_the_antigravity_plugin_install(rel):
    assert PLUGIN_SETUP_DIR in read(rel), f"{rel} must list the agy plugin install location"


def test_releasing_lists_both_plugin_validators():
    text = read("RELEASING.md")
    assert "claude plugin validate ." in text
    assert "agy plugin validate dist" in text
    assert "skills: 27 processed" in text, "RELEASING must show the expected agy output and the recorded dry run"


@pytest.mark.parametrize("rel", [SETUP_SKILL, UPDATE_SKILL])
def test_retired_v4_plugin_install_branch_is_gone(rel):
    text = read(rel).lower()
    assert "retired v4" not in text and "legacy v4 plugin installs" not in text, \
        f"{rel}: the retired v4 plugin branch is unreachable prose; check_suite.py legacy handles leftovers"


def test_update_refreshes_an_antigravity_plugin_install_by_reinstalling_dist():
    assert PLUGIN_SETUP_DIR in bullet(UPDATE_SKILL, "**Antigravity plugin install** (path")
    text = read(UPDATE_SKILL)
    assert "agy plugin install" in text and "<tmp>/dist" in text, "update must reinstall from the tag clone's dist"
