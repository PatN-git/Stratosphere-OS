#!/usr/bin/env python3
"""BT-221: install, update and the constitution follow the local tracker contract (one file per issue on the
`<repo>/issues` branch, every read and write through `issues.py`; a v5 BACKLOG_MAP.md is only migrated)."""
# md-crosscheck: every `issues.py <command>` the setup and update skills name is a subcommand of issues.parser()
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SETUP = "src/commands/stratosphere-setup/SKILL.md"
UPDATE = "src/commands/stratosphere-update/SKILL.md"
CONSTITUTION = "src/constitution/AGENTS.md"


def read(rel):
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_setup_installs_the_local_tracker_branch_not_a_map():
    text = read(SETUP)
    assert "BACKLOG_MAP" not in text
    for needle in ("tracker_branch: <repo>/issues", "issues.py init", "issues.py create", "issues.py label"):
        assert needle in text, needle


def test_update_migrates_a_v5_map_once_after_confirmation_and_never_merges_it():
    text = read(UPDATE)
    assert "issues.py migrate" in text
    lines = [l for l in text.splitlines() if "BACKLOG_MAP" in l]
    assert lines and all("migrate" in l for l in lines), lines


def test_every_issues_command_the_install_skills_name_exists():
    sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
    import issues
    commands = issues.parser()._subparsers._group_actions[0].choices
    named = {m for rel in (SETUP, UPDATE) for m in re.findall(r"issues\.py (\w+)", read(rel))}
    assert named and named <= set(commands), named - set(commands)


def test_constitution_pushes_the_tracker_branch_with_the_ship_push():
    line = next(l for l in read(CONSTITUTION).splitlines() if l.startswith("- **Push timing:**"))
    assert "`tracker_branch`" in line and "4a ship" in line


def test_user_facing_pages_name_no_map():
    for rel in ("README.md", "docs/status-label-contract.md"):
        assert "BACKLOG_MAP" not in read(rel), rel
    assert "docs/issues/" in read("README.md")
