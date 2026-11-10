#!/usr/bin/env python3
"""Tests for src/scripts/validate_memory.py."""
import subprocess
import sys
from pathlib import Path

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "src" / "scripts" / "validate_memory.py"

GLOSSARY_HEADER = """---
type: glossary
version: "1.0.0"
---
# GLOSSARY

## Active Entries

"""

LEARNINGS_HEADER = """---
type: learnings
version: "1.0.0"
---
# LEARNINGS

## Active Entries

"""


def test_glossary_autofix_does_not_corrupt_glossary(tmp_path):
    mem = tmp_path / ".memory"
    mem.mkdir()
    (mem / "GLOSSARY.md").write_text(
        GLOSSARY_HEADER
        + "- **[[G-001]] [ASSUMED] [2026-10-13]** Model Grade: a capability spec. Avoid: model tier. Source: BT-001.\n"
        + "\n## Superseded\n",
        encoding="utf-8",
    )
    (mem / "LEARNINGS.md").write_text(
        LEARNINGS_HEADER
        + "- **[[L-001]] [ASSUMED] [2026-10-05]** References [[G-001]]. Source: BT-001.\n"
        + "\n## Superseded\n",
        encoding="utf-8",
    )

    # Running validate_memory with --autofix must NOT append 'Refs:' to GLOSSARY.md
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(mem), "--autofix"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    glossary_content = (mem / "GLOSSARY.md").read_text(encoding="utf-8")
    assert "Refs:" not in glossary_content, (
        f"GLOSSARY.md was corrupted with Refs: {glossary_content}"
    )

    # Validate memory should remain clean without warnings or errors
    res2 = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(mem)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert res2.returncode == 0, f"Validator failed after autofix: stdout={res2.stdout}, stderr={res2.stderr}"
    assert "One-way reference" not in res2.stdout
    assert "Glossary field" not in res2.stdout
