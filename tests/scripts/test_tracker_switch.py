"""BT-197: `tracker_switch.py` moves a local-tracker project to GitHub and records `tracker: github`.

Seams: `write_tracker` (the frontmatter record, shared with scaffold.py) and `main(argv)` against the
gh shim (`tests/lifecycle-harness/shims/gh_shim.py`, a JSON-store `gh`), with `reconcile._gh_run` pointed at it.
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT

SCRIPTS = REPO_ROOT / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import tracker_switch as ts  # noqa: E402


# --- write_tracker: the `tracker:` frontmatter key --------------------------------------------------

def test_write_tracker_inserts_the_key_before_the_closing_fence(tmp_path):
    p = tmp_path / "ARCHITECTURE.md"
    p.write_text("---\ntype: architecture\nversion: \"1.0.0\"\n---\n# Body\ntracker: not frontmatter\n", encoding="utf-8")
    assert ts.write_tracker(p, "github") is True
    assert p.read_text(encoding="utf-8") == (
        "---\ntype: architecture\nversion: \"1.0.0\"\ntracker: github\n---\n# Body\ntracker: not frontmatter\n")


def test_write_tracker_replaces_an_existing_value_and_reports_no_change_when_equal(tmp_path):
    p = tmp_path / "ARCHITECTURE.md"
    p.write_text("---\ntracker: local\ntype: architecture\n---\n", encoding="utf-8")
    assert ts.write_tracker(p, "github") is True
    assert p.read_text(encoding="utf-8") == "---\ntracker: github\ntype: architecture\n---\n"
    assert ts.write_tracker(p, "github") is False


def test_write_tracker_keeps_crlf_line_endings(tmp_path):
    p = tmp_path / "ARCHITECTURE.md"
    p.write_bytes(b"---\r\ntype: architecture\r\n---\r\n# Body\r\n")
    ts.write_tracker(p, "github")
    assert p.read_bytes() == b"---\r\ntype: architecture\r\ntracker: github\r\n---\r\n# Body\r\n"


def test_write_tracker_refuses_a_file_without_frontmatter(tmp_path):
    p = tmp_path / "ARCHITECTURE.md"
    p.write_text("# Body only\n", encoding="utf-8")
    with pytest.raises(ValueError):
        ts.write_tracker(p, "github")
    assert p.read_text(encoding="utf-8") == "# Body only\n"
