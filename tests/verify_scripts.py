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

if __name__ == "__main__":
    success = True
    if not test_validate_memory():
        success = False
    if not test_sync_skills():
        success = False
    if not test_scaffold():
        success = False
        
    if success:
        print("\nAll script verification tests passed.")
        sys.exit(0)
    else:
        print("\nScript verification tests failed.")
        sys.exit(1)
