import os
import sys
from pathlib import Path

# NOTE: Since Stratosphere-Update.md is an agentic markdown workflow file, its runtime 
# execution behavior cannot be directly validated by automated unit tests. Real validation 
# of the preflight check is performed manually or via interactive dry-run testing.
# This test performs a static substring check to ensure required instructions are not deleted or modified.

def test_preflight_instructions():
    # Resolve file path relative to this script's location
    test_dir = Path(__file__).resolve().parent
    repo_root = test_dir.parent
    filepath = repo_root / "src" / "commands/update/Stratosphere-Update.md"
    
    if not filepath.exists():
        print(f"FAIL: {filepath} does not exist.")
        sys.exit(1)

    content = filepath.read_text(encoding='utf-8')

    # Core required patterns in the remote preflight phase
    required_checks = {
        "Installed version read": [
            "<plugin>/versions.json",
            "plugin_version"
        ],
        "GitHub CLI version lookup": [
            "gh release view",
            "--repo PatN-git/Stratosphere-OS",
            "tagName"
        ],
        "Offline fallback behavior": [
            "Could not verify latest StratOS release (offline/no gh); proceeding under installed v"
        ],
        "Marketplace cache path check & halt": [
            "cache",
            "marketplace update",
            "HALT"
        ],
        "Antigravity copy update pathway": [
            "install-antigravity",
            "clone"
        ],
        "In-place git pull pathway": [
            ".git",
            "git -C <plugin> pull --ff-only",
            "confirm",
            "reload plugins and re-run",
            "HALT"
        ],
        "Current version check": [
            "StratOS plugin is current (v"
        ],
        "Manual/copied Claude install catch-all and halt": [
            "Else / Catch-all (Manual/Copied Claude Install or other)",
            "Update your installed StratOS plugin from its source (re-run your original install method)",
            "HALT"
        ]
    }

    failed = False
    print("--- Verifying Stratosphere-Update.md preflight instructions ---")
    for check_name, substrings in required_checks.items():
        missing = [sub for sub in substrings if sub not in content]
        if missing:
            print(f"FAIL: [{check_name}] is missing expected instructions: {missing}")
            failed = True
        else:
            print(f"PASS: [{check_name}] verified.")

    if failed:
        sys.exit(1)
    else:
        print("\nAll preflight instruction checks PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    test_preflight_instructions()
