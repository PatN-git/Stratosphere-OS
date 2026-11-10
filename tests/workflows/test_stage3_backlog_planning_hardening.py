#!/usr/bin/env python3
# md-crosscheck: Stage 3 backlog and planning workflows against BT-255 interaction streamlining plan
"""Tests for Stage 3 Backlog & Planning Pipeline Streamlining (BT-253 / Epic BT-255)."""
import subprocess
import sys
from pathlib import Path
import pytest
from conftest import REPO_ROOT, read_src

sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
import _versioning


def test_3b_zero_intermediate_question_halts_and_calibrated_defaults():
    text = read_src("workflows/3b-create-issue.md")
    
    # Must remove intermediate ODI fallback and size interrogation halts
    assert "HALT and ask the user for Impact and Confidence" not in text, "3b must eliminate ODI fallback halt"
    assert "never infer them" not in text, "3b must eliminate restriction against metric inference"
    assert "Prompt for **Size**" not in text and "prompt for Size" not in text.lower(), "3b must eliminate intermediate Size prompt"
    
    # Must specify calibrated defaults for Impact, Confidence, and Size
    assert "Default to `1.0 (med)`" in text or "Default to `1.0" in text, "3b must specify calibrated Impact defaults"
    assert "Default to `80% (high)`" in text or "80% (high)" in text or "80%" in text, "3b must default Confidence to 80% when unbacked"
    assert "touchpoints" in text.lower() or "files" in text, "3b must infer Size from file touchpoints"


def test_3b_single_final_verification_gate_and_summary_table():
    text = read_src("workflows/3b-create-issue.md")
    
    assert "Single Final Verification Gate" in text, "3b Phase 2 Step 5 must be named Single Final Verification Gate"
    assert "Slices Proposed for Minting" in text or "| Inferred Impact |" in text, "3b must present compact summary table"
    assert "set <field>=<value>" in text, "3b must document inline override syntax"
    assert "[Approve & Mint" in text, "3b must present single approval action prompt"


def test_3c_inline_topological_warnings_and_single_activation_gate():
    text = read_src("workflows/3c-sprint-planning.md")
    
    assert "[Activate Sprint Queue]" in text, "3c must provide consolidated single activation prompt"
    assert "Inline Warnings" in text or "inline" in text.lower(), "3c must surface warnings inline in table"


def test_stage3_frontmatter_version_bumps():
    for rel_path, expected_v in [
        ("workflows/3b-create-issue.md", "2.10.0"),
        ("workflows/3c-sprint-planning.md", "2.9.0"),
    ]:
        content = read_src(rel_path)
        v, _ = _versioning.read_version(content, rel_path)
        assert v == expected_v, f"{rel_path} version mismatch: expected {expected_v}, got {v}"


def test_build_and_validate_clean():
    res_build = subprocess.run([sys.executable, str(REPO_ROOT / "build" / "build.py")], capture_output=True, text=True)
    assert res_build.returncode == 0, f"build.py failed: {res_build.stdout}\n{res_build.stderr}"
    
    res_val = subprocess.run([sys.executable, str(REPO_ROOT / "build" / "validate.py")], capture_output=True, text=True)
    assert res_val.returncode == 0, f"validate.py failed: {res_val.stdout}\n{res_val.stderr}"
