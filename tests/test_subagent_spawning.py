import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check_workflow(filepath, required_phrases):
    with open(os.path.join(ROOT, filepath), 'r', encoding='utf-8') as f:
        content = f.read()

    missing = [phrase for phrase in required_phrases if phrase not in content]
    if missing:
        print(f"FAIL: {filepath} is missing required phrases:")
        for m in missing:
            print(f"  - {m}")
        return False
    print(f"PASS: {filepath} matches subagent conventions.")
    return True

WORKFLOWS = {
    "src/workflows/1a_research.md": [
        "Invoke a subagent",
        "remaining = 24 - issued",
        "Return verdicts + queries_used"
    ],
    "src/workflows/1b_concept-framing.md": [
        "Skeptical Challenger",
        "Report only; do not write any file."
    ],
    "src/workflows/2b_interface-design.md": [
        "Stress Tester",
        "Report the matrix only; do not edit any file."
    ],
    "src/workflows/3a_version-planning.md": [
        "Invoke a Release Auditor subagent",
        "Report the audit findings only; do not edit any file, create milestones, or modify the roadmap."
    ],
    "src/workflows/3b_create-issue.md": [
        "Slice Draft Auditor subagent",
        "Report findings + one proposed fix each; do not create issues or edit any file."
    ],
    "src/workflows/4a_verify-and-ship.md": [
        "Context Isolation Rule",
        "invoke an independent Strict Business-Logic Auditor subagent",
        "Audit + format the AC↔test table only; do not edit code/tests, do not commit or push; return to main for Phase 4.",
        # Lock in the two-separate-subagents requirement (the Standards Auditor must be a
        # distinct dispatch, never folded into the Business-Logic Auditor).
        "two separate, independent subagents in two isolated contexts",
        "a second, separate subagent",
        # Lock in the anti-discovery dispatch semantic: the parent resolves audit targets and
        # the subagent is forbidden from repo-wide discovery. Assert the meaning, not a heading.
        "the subagent must never run repo-wide discovery"
    ],
    "src/workflows/4b_audit-architecture-drift.md": [
        "Context Isolation Rule",
        "invoke an independent Staff-Level Architect subagent",
        "Return findings + confidence only; do not modify production code or write refactor files (matches Phase 1/3 constraints)."
    ]
}

def run():
    all_passed = True
    for filepath, phrases in WORKFLOWS.items():
        if not check_workflow(filepath, phrases):
            all_passed = False
    print("\nAll subagent instruction checks PASSED." if all_passed else "\nSome subagent instruction checks FAILED.")
    return all_passed

def test_subagent_conventions():
    assert run(), "subagent instruction checks failed (see output above)"

if __name__ == "__main__":
    sys.exit(0 if run() else 1)
