import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check_workflow(filepath, required_substrings):
    full = os.path.join(ROOT, filepath)
    if not os.path.exists(full):
        print(f"FAIL: {filepath} does not exist.")
        return False

    with open(full, 'r', encoding='utf-8') as f:
        content = f.read()

    missing = [substring for substring in required_substrings if substring not in content]
    if missing:
        print(f"FAIL: {filepath} is missing plan-html delegation instructions:")
        for m in missing:
            print(f"  - {m}")
        return False
    print(f"PASS: {filepath} contains explicit plan-html delegation.")
    return True

WORKFLOWS = {
    "src/workflows/1b_concept-framing.md": [
        "plan-html",
        "plan-document"
    ],
    "src/workflows/2a_write-prd.md": [
        "plan-html",
        "plan-document"
    ],
    "src/workflows/2b_interface-design.md": [
        "plan-html",
        "wireframe-compare"
    ],
    "src/workflows/3a_version-planning.md": [
        "plan-html"
    ]
}

def run():
    all_passed = True
    for filepath, substrings in WORKFLOWS.items():
        if not check_workflow(filepath, substrings):
            all_passed = False
    print("\nAll plan-html delegation checks PASSED." if all_passed else "\nSome plan-html delegation checks FAILED.")
    return all_passed

def test_plan_html_delegation():
    assert run(), "plan-html delegation checks failed (see output above)"

if __name__ == "__main__":
    sys.exit(0 if run() else 1)
