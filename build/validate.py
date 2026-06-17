import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
errs = []

# List of JSON files to validate
json_files = [
    "dist/claude-code/.claude-plugin/plugin.json",
    "dist/antigravity/plugin.json",
    ".claude-plugin/marketplace.json",
    "src/external-skills.json",
    "dist/claude-code/external-skills.json",
    "dist/antigravity/external-skills.json"
]

# 1. JSON validity and BOM checks
for j in json_files:
    p = root / j
    if not p.exists():
        errs.append(f"MISSING {j}")
    else:
        # Check for BOM
        try:
            content_bytes = p.read_bytes()
            if content_bytes.startswith(b'\xef\xbb\xbf'):
                errs.append(f"BOM DETECTED in {j}")
            # Try to load as JSON
            json.loads(content_bytes.decode("utf-8"))
        except Exception as e:
            errs.append(f"BAD JSON {j}: {e}")

# 2. Frontmatter name+description on every command/workflow + skill
def fm_keys(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return set()
    return {l.split(':', 1)[0].strip() for l in m.group(1).splitlines() if l and not l[0].isspace() and ':' in l}

for plat, inv in [("dist/claude-code", "commands"), ("dist/antigravity", "workflows")]:
    for md in (root / plat / inv).glob("*.md"):
        # Check BOM
        if md.read_bytes().startswith(b'\xef\xbb\xbf'):
            errs.append(f"BOM DETECTED in {plat}/{inv}/{md.name}")
        k = fm_keys(md.read_text(encoding="utf-8"))
        if "name" not in k or "description" not in k:
            errs.append(f"{plat}/{inv}/{md.name} missing {{'name','description'}}-{k}")
            
    for sk in (root / plat / "skills").glob("*/SKILL.md"):
        # Check BOM
        if sk.read_bytes().startswith(b'\xef\xbb\xbf'):
            errs.append(f"BOM DETECTED in {plat}/skills/{sk.parent.name}/SKILL.md")
        k = fm_keys(sk.read_text(encoding="utf-8"))
        if "name" not in k or "description" not in k:
            errs.append(f"{plat}/skills/{sk.parent.name} missing name/description -> {k}")

# 2.5. Frontmatter version check on reference files
for ref_file in (root / "src/references").glob("*.md"):
    if ref_file.read_bytes().startswith(b'\xef\xbb\xbf'):
        errs.append(f"BOM DETECTED in src/references/{ref_file.name}")
    k = fm_keys(ref_file.read_text(encoding="utf-8"))
    if "version" not in k:
        errs.append(f"src/references/{ref_file.name} missing version -> {k}")

for plat in ["dist/claude-code", "dist/antigravity"]:
    ref_dir = root / plat / "assets/templates/references"
    if ref_dir.exists():
        for ref_file in ref_dir.glob("*.md"):
            if ref_file.read_bytes().startswith(b'\xef\xbb\xbf'):
                errs.append(f"BOM DETECTED in {plat}/assets/templates/references/{ref_file.name}")
            k = fm_keys(ref_file.read_text(encoding="utf-8"))
            if "version" not in k:
                errs.append(f"{plat}/assets/templates/references/{ref_file.name} missing version -> {k}")


# Also check python script files in dist for BOM
for plat in ["dist/claude-code", "dist/antigravity"]:
    for py in (root / plat / "scripts").glob("*.py"):
        if py.read_bytes().startswith(b'\xef\xbb\xbf'):
            errs.append(f"BOM DETECTED in {plat}/scripts/{py.name}")

# 4. Check for broken reference links in workflows/commands
ref_regex = re.compile(r'\.agents/workflows/\.reference/([a-zA-Z0-9_\-\.]+)')
src_path = root / "src"
references_dir = src_path / "references"

# Gather md files to scan (recursively under workflows and commands)
md_files_to_scan = list(src_path.glob("workflows/**/*.md")) + list(src_path.glob("commands/**/*.md"))

for md_file in md_files_to_scan:
    try:
        content = md_file.read_text(encoding="utf-8")
        for match in ref_regex.finditer(content):
            ref_name = match.group(1)
            # Check if there is a matching file in src/references/
            if not (references_dir / ref_name).exists():
                errs.append(f"BROKEN REFERENCE in {md_file.relative_to(root)}: '{ref_name}' does not exist in src/references/")
    except Exception as e:
        errs.append(f"ERROR reading {md_file} during reference validation: {e}")

# 3. Counts
for plat, inv in [("dist/claude-code", "commands"), ("dist/antigravity", "workflows")]:
    n = len(list((root / plat / inv).glob('*.md')))
    print(f"{plat}/{inv}: {n} invocables")
print("external skills:", len(json.loads((root / 'src/external-skills.json').read_text(encoding='utf-8'))['skills']))

if errs:
    print("\nERRORS:")
    for e in errs:
        print(" -", e)
    sys.exit(1)

print("\nVALIDATION OK")
