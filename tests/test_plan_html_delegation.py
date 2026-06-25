import os
import sys

def check_workflow(filepath, required_substrings):
    if not os.path.exists(filepath):
        print(f"FAIL: {filepath} does not exist.")
        return False
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing = []
    for substring in required_substrings:
        if substring not in content:
            missing.append(substring)
            
    if missing:
        print(f"FAIL: {filepath} is missing plan-html delegation instructions:")
        for m in missing:
            print(f"  - {m}")
        return False
    print(f"PASS: {filepath} contains explicit plan-html delegation.")
    return True

workflows_to_check = {
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

all_passed = True
for filepath, substrings in workflows_to_check.items():
    if not check_workflow(filepath, substrings):
        all_passed = False

if all_passed:
    print("\nAll plan-html delegation checks PASSED.")
    sys.exit(0)
else:
    print("\nSome plan-html delegation checks FAILED.")
    sys.exit(1)
