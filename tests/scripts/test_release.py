#!/usr/bin/env python3
"""Tests for scripts/release.py release validation."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("release", ROOT / "scripts" / "release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def test_release_validates_through_the_gate_record_only_when_the_tree_was_clean():
    """BT-183: the release commit stages build.py and *.json; the pre-commit test gate only lets them through if a
    passing run recorded them. But `record` hashes every dirty file, so an unrelated dirty tree must not be blessed."""
    import sys
    gate = ROOT / "src" / "scripts" / "test_gate.py"
    clean = release.validate_cmd(True)
    assert clean[:4] == [sys.executable, str(gate), "record", "--"] and clean[-1].endswith("validate.py")
    assert release.validate_cmd(False) == [sys.executable, "build/validate.py"]
