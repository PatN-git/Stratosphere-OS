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

if __name__ == "__main__":
    success = True
    if not test_validate_memory():
        success = False
    if not test_sync_skills():
        success = False
    if not test_scaffold():
        success = False
    if not test_scaffold_repair_lock():
        success = False
        
    if success:
        print("\nAll script verification tests passed.")
        sys.exit(0)
    else:
        print("\nScript verification tests failed.")
        sys.exit(1)
