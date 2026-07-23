#!/usr/bin/env python3
"""Lock the terminal-sync / process-integrity wiring (wiring only — runtime behavior
is guaranteed by reconcile.py's exit code, covered in test_reconcile.py)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS = {
    # script-gated sync workflows must call the deterministic gate
    "src/workflows/4a_verify-and-ship.md": ["reconcile.py", "terminal-sync-invariant", "--pr-id"],
    "src/workflows/3b_create-issue.md": ["reconcile.py", "terminal-sync-invariant"],
    "src/workflows/3c_sprint-planning.md": ["reconcile.py", "terminal-sync-invariant"],
    "src/workflows/3a_version-planning.md": ["reconcile.py", "terminal-sync-invariant"],
    # P4: 3z surfaces the reference docs read
    "src/workflows/3z_afk-loop.md": ["docs_read", "red_confirmed"],
    # P1: universal disclosure rule
    "src/rules/output-mode.md": ["Disclose omissions"],
    # P3: micro-tdd records the observed RED
    "src/skills/micro-tdd/SKILL.md": ["Record the observed RED", "red_confirmed"],
    # the reference itself exists with the heal contract
    "src/references/terminal-sync-invariant.md": ["upsert keyed by", "Never append", "reconcile.py"],
}

failed = False
for rel, phrases in CHECKS.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    missing = [p for p in phrases if p not in text]
    if missing:
        failed = True
        print(f"FAIL: {rel} missing: {missing}")
    else:
        print(f"PASS: {rel}")

# the deterministic gate script must exist
if not (ROOT / "src/scripts/reconcile.py").exists():
    failed = True
    print("FAIL: src/scripts/reconcile.py missing")
else:
    print("PASS: src/scripts/reconcile.py present")

if failed:
    print("\nTerminal-sync wiring checks FAILED.")
    sys.exit(1)
print("\nAll terminal-sync wiring checks PASSED.")
