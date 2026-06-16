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
def fm_dict(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return {}
    res = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            k, v = line.split(':', 1)
            res[k.strip()] = v.strip()
    return res

for plat, inv in [("dist/claude-code", "commands"), ("dist/antigravity", "workflows")]:
    for md in (root / plat / inv).glob("*.md"):
        # Check BOM
        if md.read_bytes().startswith(b'\xef\xbb\xbf'):
            errs.append(f"BOM DETECTED in {plat}/{inv}/{md.name}")
        d = fm_dict(md.read_text(encoding="utf-8"))
        if "name" not in d or "description" not in d:
            errs.append(f"{plat}/{inv}/{md.name} missing {{'name','description'}}")
        # Assert version exists on shipped command/workflow
        if "version" not in d or not d["version"]:
            errs.append(f"{plat}/{inv}/{md.name} missing version")
            
    for sk in (root / plat / "skills").glob("*/SKILL.md"):
        # Check BOM
        if sk.read_bytes().startswith(b'\xef\xbb\xbf'):
            errs.append(f"BOM DETECTED in {plat}/skills/{sk.parent.name}/SKILL.md")
        d = fm_dict(sk.read_text(encoding="utf-8"))
        if "name" not in d or "description" not in d:
            errs.append(f"{plat}/skills/{sk.parent.name} missing name/description")
        # Assert version exists on shipped skill
        if "version" not in d or not d["version"]:
            errs.append(f"{plat}/skills/{sk.parent.name}/SKILL.md missing version")

# 2.5 Asset templates type + version validation
concept_references = {
    "PRD-template.md",
    "discovery_brief_template.md",
    "research-competitive-template.md",
    "research-problem-template.md",
    "design-doc-template.md"
}

for plat in ["dist/claude-code", "dist/antigravity"]:
    assets = root / plat / "assets" / "templates"
    if not assets.exists():
        continue
    for p in assets.rglob("*.md"):
        if not p.is_file():
            continue
        rel_path = p.relative_to(assets)
        parent_dir = rel_path.parent.name
        filename = p.name

        is_index = filename == "index.md"
        is_design = filename == "DESIGN.md"
        
        # Check version (all templates except DESIGN.md)
        content = p.read_text(encoding="utf-8")
        d = fm_dict(content)
        if not is_design:
            if "version" not in d or not d["version"]:
                errs.append(f"{plat}/assets/templates/{rel_path} missing version")

        # Check type (only concept templates)
        is_concept = False
        if parent_dir == "memory" and not is_index and not is_design:
            is_concept = True
        elif parent_dir == "rules" and not is_index:
            is_concept = True
        elif parent_dir == "constitution" and filename == "AGENT.md":
            is_concept = True
        elif parent_dir == "references" and filename in concept_references:
            is_concept = True

        if is_concept:
            if "type" not in d or not d["type"]:
                errs.append(f"{plat}/assets/templates/{rel_path} missing type")

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

# 4.5 Absolute file:// link guard check
for mr in [root/"src", root/"dist/claude-code", root/"dist/antigravity"]:
    if not mr.exists(): continue
    for md in mr.rglob("*.md"):
        try:
            if "file:///" in md.read_text(encoding="utf-8"):
                errs.append(f"ABSOLUTE file:// LINK in {md.relative_to(root)}")
        except Exception:
            pass

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
