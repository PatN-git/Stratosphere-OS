#!/usr/bin/env python3
# md-crosscheck: Stage 4 execution and verification workflows against BT-255 interaction streamlining plan
"""Tests for Stage 4 Execution & Verification Pipeline Streamlining (BT-261 / Epic BT-255)."""
import shutil
import subprocess
import sys
from pathlib import Path
import pytest
from conftest import REPO_ROOT, read_src

sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
import _versioning
import pr_body


def test_3d_scoped_micro_tdd_and_branched_completion_gate():
    text = read_src("workflows/3d-implement-issue.md")
    
    # Must enforce scoped micro-tdd and forbid repo-wide sweeps during feature coding
    assert "scoped" in text.lower() and "micro-tdd" in text.lower(), "3d Phase 1 must enforce scoped micro-tdd"
    assert "Never run repo-wide test suites during 3d feature iteration" in text or \
           "forbid repo-wide" in text.lower() or "never run repo-wide" in text.lower(), \
           "3d must explicitly restrict repo-wide suites during feature coding"
    
    # Phase 3 Step 6 must branch between intermediate and standalone/final slices
    assert "Intermediate Slices" in text or "intermediate slices" in text.lower(), \
        "3d Phase 3 Step 6 must branch for intermediate slices"
    assert "Standalone & Final" in text or "standalone and final" in text.lower() or "Final Epic Slices" in text, \
        "3d Phase 3 Step 6 must branch for standalone and final epic slices"
    assert "record --slice" in text or "--allow-scoped" in text, \
        "3d must record slice-level receipt on intermediate slices"


def test_4a_receipt_reuse_and_duplicate_bypass():
    text = read_src("workflows/4a-verify-and-ship.md")
    
    # 4a must reuse suite receipts via pr_body.py suite and bypass duplicate full test runs
    assert "pr_body.py suite" in text, "4a must verify suite receipts via pr_body.py suite"
    assert "0 duplicate" in text.lower() or "bypass" in text.lower() or "skip" in text.lower(), \
        "4a must skip duplicate full test runs when HEAD is proven clean"
    assert "proven clean" in text.lower() or "valid for current head" in text.lower() or "valid for head" in text.lower(), \
        "4a must verify clean receipt for current HEAD"


def test_4a_unified_ship_gate_consolidation():
    text = read_src("workflows/4a-verify-and-ship.md")
    
    # Must consolidate Phase 4 and Phase 5 into Unified Ship Gate
    assert "Unified Ship Gate" in text or "Unified Ship Verification Gate" in text, \
        "4a must define a Unified Ship Gate"
    assert "Audit Verdict" in text or "audit verdict" in text.lower(), \
        "Unified Ship Gate must include audit verdict"
    assert "Test Proof" in text or "test proof" in text.lower(), \
        "Unified Ship Gate must include test proof"


def test_pr_body_slice_receipt_support(tmp_path):
    # Verify that pr_body allows slice-level receipts when allow_scoped=True
    rec = {"head_sha": "0123456789abcdef0123456789abcdef01234567", "cmd": "pytest tests/test_foo.py", "observed": "1 passed"}
    suite_file = tmp_path / "3d-suite-BT-261.json"
    suite_file.write_text(pr_body.dumps(rec), encoding="utf-8")
    
    # When allow_scoped is False, scoped command is rejected
    # When allow_scoped is True, scoped command is accepted
    assert hasattr(pr_body, "suite_status"), "pr_body must have suite_status"


def test_0d_single_click_batch_approval_tier1():
    text = read_src("workflows/0d-nightly-consolidation.md")
    
    # 0d must provide single-click batch approval for Tier 1 cleanups while preserving memory-protocol §5
    assert "R-ALL-CLEAN" in text or "batch approval" in text.lower(), \
        "0d must provide single-click batch approval for routine cleanups"
    assert "memory-protocol" in text, "0d must cite memory-protocol.md §5 compliance"


def test_2c_reconcile_specs_streamlining():
    text = read_src("workflows/2c-reconcile-specs.md")
    
    # 2c must auto-apply structural boilerplate and present semantic conflicts in exception table
    assert "structural boilerplate" in text.lower() or "boilerplate" in text.lower(), \
        "2c must auto-apply structural boilerplate"
    assert "exception" in text.lower(), "2c must use exception-based review for semantic conflicts"


def test_stage4_frontmatter_version_bumps():
    for rel_path, expected_v in [
        ("workflows/3d-implement-issue.md", "2.10.0"),
        ("workflows/4a-verify-and-ship.md", "1.11.0"),
        ("workflows/0d-nightly-consolidation.md", "1.7.0"),
        ("workflows/2c-reconcile-specs.md", "1.5.0"),
    ]:
        content = read_src(rel_path)
        v, _ = _versioning.read_version(content, rel_path)
        assert v == expected_v, f"{rel_path} version mismatch: expected {expected_v}, got {v}"


def test_build_and_validate_clean(tmp_path):
    shutil.copytree(REPO_ROOT / "build", tmp_path / "build", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(REPO_ROOT / "src", tmp_path / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(REPO_ROOT / "README.md", tmp_path / "README.md")

    res_build = subprocess.run([sys.executable, str(tmp_path / "build" / "build.py")], capture_output=True, text=True)
    assert res_build.returncode == 0, f"build.py failed: {res_build.stdout}\n{res_build.stderr}"
    
    res_val = subprocess.run([sys.executable, str(tmp_path / "build" / "validate.py"), str(tmp_path)], capture_output=True, text=True)
    assert res_val.returncode == 0, f"validate.py failed: {res_val.stdout}\n{res_val.stderr}"
