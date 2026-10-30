#!/usr/bin/env python3
"""BT-222: validate_memory warns on glossary entry fields other than Avoid:/Source:."""
import subprocess
import sys

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "src" / "scripts" / "validate_memory.py"

HEADER = """---
type: glossary
title: Glossary
description: Test fixture.
generated:
  by: test
  at: 2026-10-27
version: "1.0.0"
---
# GLOSSARY

## Active Entries

"""


def _lint(tmp_path, entry):
    mem = tmp_path / ".memory"
    mem.mkdir()
    (mem / "GLOSSARY.md").write_text(HEADER + entry + "\n## Superseded\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), "--path", ".memory"], cwd=tmp_path,
                       capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def test_occurrences_field_warns_without_error(tmp_path):
    entry = ("- **[[G-001]] [PATTERN] [2026-10-13]** Model Grade: a capability spec. "
             "Avoid: model tier. Source: BT-234. Occurrences: BT-234, BT-237.\n")
    code, out = _lint(tmp_path, entry)
    assert code == 2, out
    assert "unknown field `Occurrences:` in G-001" in out
    assert "[ERROR]" not in out


def test_prose_label_inside_the_definition_does_not_warn(tmp_path):
    entry = ("- **[[G-001]] [ASSUMED] [2026-10-13]** Cart: items held before checkout. "
             "Note: a cart survives logout. Avoid: basket. Source: BT-001.\n")
    code, out = _lint(tmp_path, entry)
    assert code == 0, out
    assert "unknown field" not in out


def test_entry_with_only_avoid_and_source_passes(tmp_path):
    entry = ("- **[[G-001]] [ASSUMED] [2026-10-13]** Model Grade: a capability spec, "
             "e.g. light or high. Avoid: model tier. Source: docs/discovery/model-grade.md.\n")
    code, out = _lint(tmp_path, entry)
    assert code == 0, out
    assert "unknown field" not in out
