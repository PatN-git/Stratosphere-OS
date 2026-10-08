import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tests/ (conftest) when run as a script
from conftest import REPO_ROOT, update_skill_text

# NOTE: Since stratosphere-update's SKILL.md is an agentic markdown file, its runtime 
# execution behavior cannot be directly validated by automated unit tests. Real validation 
# of the preflight check is performed manually or via interactive dry-run testing.
# This test performs a static substring check to ensure required instructions are not deleted or modified.

def test_preflight_instructions():
    # SKILL.md plus the references/update-*.md its host-specific update paths moved to.
    content = update_skill_text()

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
        "Antigravity copy self-update pathway (bridge)": [
            "git clone --depth 1 --branch v<latest_version> https://github.com/PatN-git/Stratosphere-OS.git",
            "install-antigravity-bridge",
            "--target <skills-dir>",
            "actual",
            "reload plugins and re-run",
            "HALT"
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

    # BT-133: Claude Code copied-skills installs self-update; marketplace branch drives the CLI.
    # Each branch is its own reference file now; the combined text lists them in router order, so the
    # last one (copied skills) runs to the end of the text.
    def branch(start, end=None):
        i = content.index(start)
        return content[i:content.index(end, i)] if end else content[i:]

    copied = (REPO_ROOT / "src" / "references" / "update-copied-skills.md").read_text(encoding="utf-8")
    for path in ("`~/.claude/skills/`", "`./.claude/skills/`"):
        assert path in copied, f"copied-skills branch does not cover {path}"
    market = branch("**Claude Marketplace Cache**", "**Antigravity plugin install**")
    for needle in ("claude plugin marketplace update stratosphere-os", "claude plugin update stratosphere-os", "claude-code"):
        assert needle in market, f"marketplace branch missing {needle!r}"

    # The bridge (BT-120) records no provenance; a self-update must not depend on it.
    assert ".install-source.json" not in content, "stale .install-source.json provenance reference"

    failed = False
    print("--- Verifying stratosphere-update preflight instructions ---")
    for check_name, substrings in required_checks.items():
        missing = [sub for sub in substrings if sub not in content]
        if missing:
            print(f"FAIL: [{check_name}] is missing expected instructions: {missing}")
            failed = True
        else:
            print(f"PASS: [{check_name}] verified.")

    print("\nAll preflight instruction checks PASSED." if not failed else "\nSome preflight instruction checks FAILED.")
    assert not failed, "preflight instruction checks failed (see output above)"

if __name__ == "__main__":
    test_preflight_instructions()
