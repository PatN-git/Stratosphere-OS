import os
import re
from pathlib import Path

ROOT = Path(".")

# Files for Form A
FORM_A_DIRS = [
    "src/workflows",
    "src/commands",
    "src/skills",
    "src/rules",
    "src/constitution"
]
FORM_A_PURE_REFS = [
    "src/references/brainstorm-techniques.md",
    "src/references/research-evidence-standards.md",
    "src/references/shadcn-build-guide.md",
    "src/references/stitch-brief-guide.md",
    "src/references/multi-sided-discovery.md"
]

# Files for Form B
FORM_B_INSTANCE_TEMPLATES = [
    "src/references/PRD-template.md",
    "src/references/design-doc-template.md",
    "src/references/discovery_brief_template.md",
    "src/references/research-competitive-template.md",
    "src/references/research-problem-template.md"
]
FORM_B_DIRS = [
    "src/memory-templates"
]

VERSION_TAG = 'version: "1.0.0"'
UPDATED_TAG = 'updated: 2026-06-17'
FORM_B_MARKER = '<!-- stratosphere: version=1.0.0 updated=2026-06-17 -->\n'

def process_form_a(path: Path):
    if not path.is_file() or path.suffix != ".md": return
    content = path.read_text(encoding="utf-8")
    
    # Skip DESIGN.md which is explicitly Form B
    if path.name == "DESIGN.md" and "memory-templates" in path.parts: return

    # Check if already stamped
    if 'version: "1.0.0"' in content and 'updated: 2026-06-17' in content: return

    if content.startswith("---"):
        parts = content.split("---\n", 2)
        if len(parts) >= 3:
            fm = parts[1]
            if not re.search(r'^version:', fm, flags=re.M):
                fm += f"{VERSION_TAG}\n"
            else:
                # Update existing version to "1.0.0" except DESIGN.md which we skipped
                fm = re.sub(r'^version:.*$', VERSION_TAG, fm, flags=re.M)
                
            if not re.search(r'^updated:', fm, flags=re.M):
                fm += f"{UPDATED_TAG}\n"
            else:
                fm = re.sub(r'^updated:.*$', UPDATED_TAG, fm, flags=re.M)
                
            new_content = f"---\n{fm}---\n{parts[2]}"
            path.write_text(new_content, encoding="utf-8")
            print(f"Stamped Form A: {path}")
    else:
        # File has no frontmatter
        fm = f"---\nname: {path.stem}\ndescription: {path.stem}\n{VERSION_TAG}\n{UPDATED_TAG}\n---\n\n"
        path.write_text(fm + content, encoding="utf-8")
        print(f"Added Form A frontmatter to: {path}")

def process_form_b(path: Path):
    if not path.is_file() or path.suffix != ".md": return
    content = path.read_text(encoding="utf-8")
    
    if content.startswith("<!-- stratosphere: version="):
        content = re.sub(r'^<!-- stratosphere:.*?-->\n', FORM_B_MARKER, content)
        print(f"Updated Form B marker: {path}")
    else:
        content = FORM_B_MARKER + content
        print(f"Stamped Form B: {path}")
        
    # Remove any plugin-version frontmatter `version: "1.0.0"` leaking in instance templates
    # BUT wait, DESIGN.md has `version: alpha` which must NOT be stripped!
    if path.name != "DESIGN.md":
        if "---\n" in content:
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                fm = parts[1]
                # Strip only the string version "1.0.0" or similar plugin versions, but safely it's instance templates
                if re.search(r'^version:.*\n', fm, flags=re.M):
                    fm = re.sub(r'^version:.*\n', '', fm, flags=re.M)
                    content = f"{parts[0]}---\n{fm}---\n{parts[2]}"
    
    path.write_text(content, encoding="utf-8")

def main():
    for d in FORM_A_DIRS:
        for root, _, files in os.walk(ROOT / d):
            for f in files:
                process_form_a(Path(root) / f)
                
    for f in FORM_A_PURE_REFS:
        p = ROOT / f
        if p.exists(): process_form_a(p)
        
    for f in FORM_B_INSTANCE_TEMPLATES:
        p = ROOT / f
        if p.exists(): process_form_b(p)
        
    for d in FORM_B_DIRS:
        for root, _, files in os.walk(ROOT / d):
            for f in files:
                process_form_b(Path(root) / f)

if __name__ == "__main__":
    main()
