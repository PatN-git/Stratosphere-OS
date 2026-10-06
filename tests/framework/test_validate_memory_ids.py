#!/usr/bin/env python3
"""BT-141 guards: validate_memory ID-reuse lint (duplicate, gap, [REMOVED] tombstone)."""
import subprocess
import sys

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "src" / "scripts" / "validate_memory.py"

HEADER = """---
type: learnings
title: Learnings
description: Test fixture.
generated:
  by: test
  at: 2026-10-05
version: "1.0.0"
---
# LEARNINGS

## Active Entries

"""


def _lint(tmp_path, active, superseded=""):
    mem = tmp_path / ".memory"
    mem.mkdir()
    body = HEADER + active + "\n## Superseded\n" + superseded
    (mem / "LEARNINGS.md").write_text(body, encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), "--path", ".memory"], cwd=tmp_path,
                       capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def _entry(n, text="Lesson."):
    return f"- **[[L-{n:03d}]] [ASSUMED] [2026-10-05]** {text} Source: BT-001.\n"


def test_duplicate_id_is_an_error(tmp_path):
    code, out = _lint(tmp_path, _entry(1) + _entry(1, "Reused id."))
    assert code == 1, out
    assert "Duplicate ID definition" in out


def test_id_gap_warns_with_exit_2_and_no_error(tmp_path):
    code, out = _lint(tmp_path, _entry(1) + _entry(4))
    assert code == 2, out
    assert "possible hard-delete: L-002..L-003 missing" in out
    assert "[ERROR]" not in out


def test_removed_tombstone_is_valid_and_closes_the_gap(tmp_path):
    tomb = "- **[[L-002]] [REMOVED] [2026-10-05]** Reason: duplicate of a check.\n"
    code, out = _lint(tmp_path, _entry(1) + _entry(3), superseded=tomb)
    assert code == 0, out
    assert "possible hard-delete" not in out


def test_superseded_entry_without_target_or_tombstone_still_errors(tmp_path):
    bare = "- **[[L-002]] [ASSUMED] [2026-10-05]** Old lesson, no successor.\n"
    code, out = _lint(tmp_path, _entry(1) + _entry(3), superseded=bare)
    assert code == 1, out
    assert "missing a valid [SUPERSEDED BY" in out


def test_placeholder_ids_do_not_count_as_gaps(tmp_path):
    placeholder = "- **[[L-XXX]] [ASSUMED] [YYYY-MM-DD]** Example placeholder. Source: BT-XXX.\n"
    code, out = _lint(tmp_path, placeholder + _entry(1) + _entry(2))
    assert code == 0, out
