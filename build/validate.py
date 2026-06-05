import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
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

# Also check python script files in dist for BOM
for plat in ["dist/claude-code", "dist/antigravity"]:
    for py in (root / plat / "scripts").glob("*.py"):
        if py.read_bytes().startswith(b'\xef\xbb\xbf'):
            errs.append(f"BOM DETECTED in {plat}/scripts/{py.name}")

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
