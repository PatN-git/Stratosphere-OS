import os
import sys
import subprocess
from pathlib import Path

def test_validate_memory():
    print("--- Testing validate_memory.py ---")
    tmp_mem = Path(".tmp/dummy_memory")
    tmp_mem.mkdir(parents=True, exist_ok=True)
    # Write a fake memory file with a secret
    (tmp_mem / "fake.md").write_text("Hello\nSecret: sk-123456789012345678901234567890123456789012345678\nWorld", encoding="utf-8")
    
    # Run validate_memory.py from dist/antigravity/scripts/
    result = subprocess.run([sys.executable, "dist/antigravity/scripts/validate_memory.py", "--path", str(tmp_mem)], capture_output=True, text=True)
    print("Exit code:", result.returncode)
    if result.returncode == 1 and "Secret detected" in result.stdout:
        print("validate_memory test passed!")
        return True
    else:
        print("validate_memory test failed! Output:\n", result.stdout, result.stderr)
        return False

def test_validate_memory_backlog():
    print("\n--- Testing validate_memory.py Backlog checks ---")
    tmp_mem = Path(".tmp/dummy_memory_backlog")
    if tmp_mem.exists():
        shutil.rmtree(tmp_mem, ignore_errors=True)
    tmp_mem.mkdir(parents=True, exist_ok=True)
    
    backlog_content = """---
type: backlog
title: Backlog Map
description: Test
timestamp: 2026-06-18
version: "1.1.1"
---
# BACKLOG MAP

## Rules
- Dummy rule

## Label Registry
- **Primary Type (`type:<class>`)**: `type:feature`
- **Execution Mode (`type:<mode>`)**: `type:HITL`, `type:AFK`

## Backlog

| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |
|:---|:---|:---|:---|:---|:---|:---|:---|
| BT-059-01 | Hierarchical | planned | type:feature, type:HITL | v1.0.0 | — | — | — |
| BT-060 | Missing primary type | in progress | type:HITL, size:medium | v1.0.0 | — | — | — |
| BT-061 | Missing execution mode | in progress | type:feature, size:medium | v1.0.0 | — | — | — |
| BT-062 | Fully valid slice | in progress | type:feature, type:HITL, size:medium | v1.0.0 | — | — | — |
| BT-063 | Parent feature is ignored | in progress | type:feature, size:large | v1.0.0 | — | — | — |
| BT-064 | Needs spec row exempt | needs_spec | size:medium | v1.0.0 | — | — | — |
| BT-065 | Planned row exempt | planned | size:medium | v1.0.0 | — | — | — |
| BT-066 | Leftover needs_spec invalid primary | in progress | type:NEEDS_SPEC, type:AFK, size:medium | v1.0.0 | — | — | — |
"""
    (tmp_mem / "BACKLOG_MAP.md").write_text(backlog_content, encoding="utf-8")
    
    result = subprocess.run([sys.executable, "dist/antigravity/scripts/validate_memory.py", "--path", str(tmp_mem)], capture_output=True, text=True)
    print("Exit code:", result.returncode)
    
    # Assertions
    passed = True
    if result.returncode != 1:
        print("Error: Expected exit code 1, got", result.returncode)
        passed = False
        
    expected_errors = [
        "Invalid Backlog ID format 'BT-059-01'",
        "Slice 'BT-060'",
        "is missing a Primary Type label",
        "Slice 'BT-061'",
        "is missing an Execution Mode label",
        "Slice 'BT-066'",
        "is missing a Primary Type label"
    ]
    
    for err in expected_errors:
        if err not in result.stdout:
            print(f"Error: Expected to find '{err}' in output, but did not. Output:\n", result.stdout)
            passed = False
            
    unexpected_errors = [
        "BT-062",
        "BT-063",
        "BT-064",
        "BT-065"
    ]
    for uerr in unexpected_errors:
        if uerr in result.stdout and ("missing" in result.stdout or "Invalid" in result.stdout) and f"'{uerr}'" in result.stdout:
            print(f"Error: Unexpected error reported for '{uerr}'. Output:\n", result.stdout)
            passed = False
            
    if passed:
        print("validate_memory backlog checks passed!")
    return passed

def test_sync_skills():
    print("\n--- Testing sync_skills.py ---")
    # Run sync_skills.py from dist/antigravity/scripts/
    result = subprocess.run([sys.executable, "dist/antigravity/scripts/sync_skills.py", "--list"], capture_output=True, text=True)
    print("Exit code:", result.returncode)
    if result.returncode == 0:
        print("sync_skills.py test passed!")
        return True
    else:
        print("sync_skills.py test failed! Output:\n", result.stderr)
        return False

def test_scaffold():
    print("\n--- Testing scaffold.py ---")
    # Run scaffold.py from dist/antigravity/scripts/
    result = subprocess.run([sys.executable, "dist/antigravity/scripts/scaffold.py", "--dry-run"], capture_output=True, text=True)
    print("Exit code:", result.returncode)
    if result.returncode == 0:
        print("scaffold.py test passed!")
        return True
    else:
        print("scaffold.py test failed! Output:\n", result.stderr)
        return False

import shutil

def test_scaffold_repair_lock():
    print("\n--- Testing scaffold.py --repair-lock ---")
    repo_root = Path(__file__).resolve().parent.parent
    scaffold_script = repo_root / "dist" / "antigravity" / "scripts" / "scaffold.py"
    
    # Create temp directory inside repo's .tmp/ for testing
    tmp_project = repo_root / ".tmp" / "repair_lock_test_project"
    if tmp_project.exists():
        shutil.rmtree(tmp_project, ignore_errors=True)
    tmp_project.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Run normal scaffolding first to set up files
        scaffold_res = subprocess.run(
            [sys.executable, str(scaffold_script)],
            cwd=str(tmp_project),
            capture_output=True,
            text=True
        )
        print("Scaffold install exit code:", scaffold_res.returncode)
        if scaffold_res.returncode != 0:
            print("scaffold.py install failed! Output:\n", scaffold_res.stderr)
            return False
            
        # Step 2: Run repair-lock dry-run
        repair_res = subprocess.run(
            [sys.executable, str(scaffold_script), "--repair-lock", "--dry-run"],
            cwd=str(tmp_project),
            capture_output=True,
            text=True
        )
        print("Repair dry-run exit code:", repair_res.returncode)
        if repair_res.stdout:
            print("Stdout snippet:", repair_res.stdout.strip().splitlines()[-1])
        
        if repair_res.returncode != 0:
            print("scaffold.py --repair-lock failed! Output:\n", repair_res.stderr)
            return False
            
        # Step 3: Assertions
        if "artifacts" not in repair_res.stdout:
            print("scaffold.py --repair-lock output did not mention 'artifacts'. Output:\n", repair_res.stdout)
            return False
            
        if " 0 artifacts" in repair_res.stdout:
            print("scaffold.py --repair-lock processed 0 artifacts! It should have matched the scaffolded project files. Output:\n", repair_res.stdout)
            return False
            
        print("scaffold.py --repair-lock test passed!")
        return True
    finally:
        # Clean up temp project directory
        if tmp_project.exists():
            shutil.rmtree(tmp_project, ignore_errors=True)

def test_update_flow():
    print("\n--- Testing in-place update E2E pipeline ---")
    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run([sys.executable, "tests/test_update_flow.py"], cwd=str(repo_root), capture_output=True, text=True)
    print("Exit code:", result.returncode)
    sys.stdout.flush()
    if result.returncode == 0:
        print("Update E2E pipeline test passed!")
        return True
    else:
        print("Update E2E pipeline test failed! Output:\n", result.stdout, result.stderr)
        sys.stdout.flush()
        sys.stderr.flush()
        raise AssertionError(f"test_update_flow.py failed with exit code {result.returncode}.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

def test_update_preflight():
    print("\n--- Testing update preflight instructions ---")
    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run([sys.executable, "tests/test_update_preflight.py"], cwd=str(repo_root), capture_output=True, text=True)
    print("Exit code:", result.returncode)
    sys.stdout.flush()
    if result.returncode == 0:
        print("update_preflight instructions test passed!")
        return True
    else:
        print("update_preflight instructions test failed! Output:\n", result.stdout, result.stderr)
        return False

if __name__ == "__main__":
    success = True
    if not test_validate_memory():
        success = False
    if not test_validate_memory_backlog():
        success = False
    if not test_sync_skills():
        success = False
    if not test_scaffold():
        success = False
    if not test_scaffold_repair_lock():
        success = False
    if not test_update_preflight():
        success = False
    if not test_update_flow():
        success = False
        
    if success:
        print("\nAll script verification tests passed.")
        sys.exit(0)
    else:
        print("\nScript verification tests failed.")
        sys.exit(1)
