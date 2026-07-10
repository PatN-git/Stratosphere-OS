import os
import sys

def test_preflight_instructions():
    filepath = "src/commands/update/Stratosphere-Update.md"
    if not os.path.exists(filepath):
        print(f"FAIL: {filepath} does not exist.")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

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
            "Could not verify latest StratOS release (offline/no gh); proceeding with installed v"
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
            "confirm"
        ],
        "Current version check": [
            "StratOS plugin is current (v"
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
