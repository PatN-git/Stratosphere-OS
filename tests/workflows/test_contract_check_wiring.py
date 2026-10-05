#!/usr/bin/env python3
"""BT-143 guards: 2a/2b/2c call `contract_check.py` with flags the script really accepts."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "src" / "workflows"
SCRIPT = ROOT / "src" / "scripts" / "contract_check.py"
CALL = re.compile(r"python \.agents/scripts/contract_check\.py ([^`]+)`")


def calls(name):
    return CALL.findall((WF / name).read_text(encoding="utf-8"))


def script_flags():
    out = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True).stdout
    return set(re.findall(r"--[a-z]+", out))


def test_2a_validate_phase_runs_the_check_on_the_prd():
    text = (WF / "2a-write-prd.md").read_text(encoding="utf-8")
    validate = text.split("## Phase 4: Validate")[1].split("## Phase 5")[0]
    assert "contract_check.py --docs <prd> --schema .memory/DATABASE_SCHEMA.md" in validate
    assert "[CONTRACT-MISSING]" in validate and "`> open:`" in validate


def test_2b_runs_the_check_over_prd_and_design_before_phase_5():
    text = (WF / "2b-interface-design.md").read_text(encoding="utf-8")
    before_publish = text.split("## Phase 5: Publish & Sync")[0]
    assert "contract_check.py --docs <prd> <design-doc>" in before_publish


def test_2c_scan_matrix_item_1_calls_the_script_and_keeps_the_auditor_guardrail():
    text = (WF / "2c-reconcile-specs.md").read_text(encoding="utf-8")
    item1 = re.search(r"^1\. \*\*Contract existence:\*\*.*$", text, re.M).group(0)
    assert "contract_check.py --docs <all resolved artifacts>" in item1
    assert "[CONTRACT-MISSING]" in item1 and "P0/P1" in item1
    assert "Return findings + one proposed resolution each; do not modify, create, or delete any spec document" in text


def test_every_workflow_call_uses_only_real_flags():
    flags = script_flags()
    seen = 0
    for name in ("2a-write-prd.md", "2b-interface-design.md", "2c-reconcile-specs.md"):
        for args in calls(name):
            seen += 1
            used = set(re.findall(r"--[a-z]+", args))
            assert used <= flags, f"{name}: {used - flags} not accepted by contract_check.py"
    assert seen >= 3
