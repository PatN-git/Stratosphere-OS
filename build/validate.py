import json
import re
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "scripts"))
import _versioning

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

# 5. Version format and bump-guard validation
for plat in ["dist/claude-code", "dist/antigravity"]:
    versions_file = root / plat / "versions.json"
    if not versions_file.exists():
        errs.append(f"MISSING {versions_file}")
        continue
        
    try:
        built_manifest = json.loads(versions_file.read_text(encoding="utf-8")).get("artifacts", {})
    except Exception as e:
        errs.append(f"BAD JSON {versions_file}: {e}")
        continue
        
    try:
        git_path = versions_file.relative_to(root).as_posix()
        prev_json = subprocess.check_output(["git", "-C", str(root), "show", f"HEAD:{git_path}"], stderr=subprocess.STDOUT).decode("utf-8")
        prev = json.loads(prev_json).get("artifacts", {})
    except Exception:
        prev = {}
        
    for path, meta in built_manifest.items():
        v = meta.get("version", "")
        if not _versioning.SEMVER.match(v):
            errs.append(f"{plat}/{path}: version '{v}' is not semver x.y.z")
            
        if path in prev and meta["sha256"] != prev[path]["sha256"] and meta["version"] == prev[path]["version"]:
            errs.append(f"{plat}/{path}: content changed but version not bumped (still {meta['version']})")

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
