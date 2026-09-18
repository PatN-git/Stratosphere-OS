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

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PLATFORMS = ["dist/claude-code", "dist/antigravity"]

# Every bundled artifact is a skill. `Path.glob` on a missing directory yields
# nothing WITHOUT erroring, so a retargeting mistake would otherwise leave this
# walk iterating zero files and the build passing green on an empty set.
_skills_seen = 0
for plat in PLATFORMS:
    plat_skills = sorted((root / plat / "skills").glob("*/SKILL.md"))
    if not plat_skills:
        errs.append(f"{plat}/skills: NO skills found - the emitter or this path is wrong")
    for sk in plat_skills:
        _skills_seen += 1
        name_dir = sk.parent.name
        if sk.read_bytes().startswith(b'\xef\xbb\xbf'):
            errs.append(f"BOM DETECTED in {plat}/skills/{name_dir}/SKILL.md")
        fm = fm_dict(sk.read_text(encoding="utf-8"))
        k = set(fm.keys())
        required = {"name", "description", "version"}
        if not required.issubset(k):
            errs.append(f"{plat}/skills/{name_dir} missing required keys. Found {k}")

        # Agent Skills spec: name must match the regex AND equal the parent dir
        nm = str(fm.get("name", "")).strip().strip('"')
        if not SKILL_NAME_RE.match(nm):
            errs.append(f"{plat}/skills/{name_dir}: name {nm!r} fails ^[a-z0-9]+(-[a-z0-9]+)*$")
        elif nm != name_dir:
            errs.append(f"{plat}/skills/{name_dir}: name {nm!r} != parent directory")
        desc = str(fm.get("description", ""))
        if len(desc) > 1024:
            errs.append(f"{plat}/skills/{name_dir}: description {len(desc)} chars exceeds spec limit 1024")

        # no OKF type: outside the bundle scope (.memory/ + docs/)
        if "type" in k:
            errs.append(f"{plat}/skills/{name_dir}: carries OKF 'type:' but is outside the bundle scope")

if _skills_seen == 0:
    errs.append("FATAL: validated zero skills - the walk is looking in the wrong place")

# retired output directories must not reappear
for plat in PLATFORMS:
    for legacy in ("commands", "workflows"):
        if (root / plat / legacy).exists():
            errs.append(f"{plat}/{legacy}/ still emitted - retired in v4.0.0")

# The registry is the single source of truth; parse it rather than restating it,
# so a new type cannot be used without being registered (okf-protocol §3 forbids
# inventing types, but nothing enforced it before v4.0.0).
def _registered_types():
    src = root / "src" / "rules" / "okf-protocol.md"
    if not src.exists():
        return set()
    body = src.read_text(encoding="utf-8")
    sec = body.split("## 3. Type Registry", 1)
    if len(sec) < 2:
        return set()
    sec = sec[1].split("\n## ", 1)[0]
    return set(re.findall(r'^\| `([a-z-]+)` \|', sec, flags=re.M))


REGISTERED_TYPES = _registered_types()
if not REGISTERED_TYPES:
    errs.append("could not parse the OKF type registry from src/rules/okf-protocol.md")

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
        
        # Check version (all templates)
        content = p.read_text(encoding="utf-8")
        d = fm_dict(content)
        if "version" not in d or not d["version"]:
            errs.append(f"{plat}/assets/templates/{rel_path} missing version")

        # OKF `type:` is required only where the template SEEDS an in-scope
        # document. Rules and the constitution live outside the bundle scope
        # (.memory/ + docs/) and must NOT carry one (okf-protocol §1).
        is_seed = parent_dir == "memory" and not is_index

        if is_seed:
            ty = d.get("type")
            if not ty:
                errs.append(f"{plat}/assets/templates/{rel_path} missing type")
            elif ty not in REGISTERED_TYPES:
                errs.append(f"{plat}/assets/templates/{rel_path}: type {ty!r} is not in the okf-protocol registry")
        elif parent_dir in ("rules", "constitution") and "type" in d:
            errs.append(f"{plat}/assets/templates/{rel_path}: carries 'type:' but is outside the OKF bundle scope")

# 2.5. Frontmatter version check on reference files
for ref_file in (root / "src/references").glob("*.md"):
    if ref_file.read_bytes().startswith(b'\xef\xbb\xbf'):
        errs.append(f"BOM DETECTED in src/references/{ref_file.name}")
    k = fm_dict(ref_file.read_text(encoding="utf-8"))
    if "version" not in k:
        errs.append(f"src/references/{ref_file.name} missing version -> {k}")

for plat in ["dist/claude-code", "dist/antigravity"]:
    ref_dir = root / plat / "assets/templates/references"
    if ref_dir.exists():
        for ref_file in ref_dir.glob("*.md"):
            if ref_file.read_bytes().startswith(b'\xef\xbb\xbf'):
                errs.append(f"BOM DETECTED in {plat}/assets/templates/references/{ref_file.name}")
            k = fm_dict(ref_file.read_text(encoding="utf-8"))
            if "version" not in k:
                errs.append(f"{plat}/assets/templates/references/{ref_file.name} missing version -> {k}")



# 2.6 Trigger-enum contract (OKF §2.1): rules and workflows share one `trigger` vocabulary.
RULE_TRIGGERS = {"always_on", "glob", "model_decision"}
for plat in ["dist/claude-code", "dist/antigravity"]:
    # Rule templates: trigger in RULE_TRIGGERS; glob rules must carry both globs (Antigravity) and paths (Claude).
    rules_dir = root / plat / "assets/templates/rules"
    if rules_dir.exists():
        for rp in rules_dir.glob("*.md"):
            if rp.name == "index.md":
                continue
            d = fm_dict(rp.read_text(encoding="utf-8"))
            trig = d.get("trigger")
            if trig not in RULE_TRIGGERS:
                errs.append(f"{plat}/assets/templates/rules/{rp.name} trigger={trig!r}; must be one of {sorted(RULE_TRIGGERS)}")
            elif trig == "glob":
                if not d.get("globs"):
                    errs.append(f"{plat}/assets/templates/rules/{rp.name} trigger=glob but missing `globs` (Antigravity)")
                if "paths" not in d:
                    errs.append(f"{plat}/assets/templates/rules/{rp.name} trigger=glob but missing `paths` (Claude Code)")
    # Workflows/commands: all are user-invoked -> trigger must be `manual`.
    inv = "commands" if plat.endswith("claude-code") else "workflows"
    for md in (root / plat / inv).glob("*.md"):
        d = fm_dict(md.read_text(encoding="utf-8"))
        # only enforce on lifecycle workflows (installer entrypoints are skills/commands without a trigger)
        if "trigger" in d and d.get("trigger") != "manual":
            errs.append(f"{plat}/{inv}/{md.name} trigger={d.get('trigger')!r}; workflows must be `manual`")

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

# 5. Version format and bump-guard validation
# Baseline for the per-file bump check is the PR fork point (merge-base with the
# default branch), so a changed file needs only ONE bump above the last-released
# state per PR — not a fresh bump on every commit. Falls back to last release tag, then HEAD.
def _bump_baseline_ref():
    def _sh(*a):
        return subprocess.check_output(["git", "-C", str(root), *a], stderr=subprocess.DEVNULL).decode().strip()
    try:
        default = _sh("symbolic-ref", "refs/remotes/origin/HEAD").rsplit("/", 1)[-1]
    except Exception:
        default = "main"
    for cand in (f"origin/{default}", default):
        try:
            return _sh("merge-base", "HEAD", cand)
        except Exception:
            continue
    try:
        return _sh("describe", "--tags", "--match", "v[0-9]*", "--abbrev=0")
    except Exception:
        return "HEAD"

bump_baseline = _bump_baseline_ref()
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
        prev_json = subprocess.check_output(["git", "-C", str(root), "show", f"{bump_baseline}:{git_path}"], stderr=subprocess.STDOUT).decode("utf-8")
        prev = json.loads(prev_json).get("artifacts", {})
    except Exception:
        prev = {}
        
    for path, meta in built_manifest.items():
        v = meta.get("version", "")
        if not _versioning.SEMVER.match(v):
            errs.append(f"{plat}/{path}: version '{v}' is not semver x.y.z")
            
        if path in prev and meta["sha256"] != prev[path]["sha256"] and meta["version"] == prev[path]["version"]:
            errs.append(f"{plat}/{path}: content changed but version not bumped (still {meta['version']})")

# 2.9 Versioning Consistency Guard
build_version = None
readme_version = None

# Extract version from build/build.py
build_py = root / "build" / "build.py"
if not build_py.exists():
    errs.append("MISSING build/build.py")
else:
    build_content = build_py.read_text(encoding="utf-8")
    m = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', build_content)
    if not m:
        errs.append("Could not find VERSION in build/build.py")
    else:
        build_version = m.group(1)

# Extract version from README.md badge
readme_md = root / "README.md"
if not readme_md.exists():
    errs.append("MISSING README.md")
else:
    readme_content = readme_md.read_text(encoding="utf-8")
    m = re.search(r'version-(\d+\.\d+\.\d+)', readme_content)
    if not m:
        errs.append("Could not find version badge in README.md")
    else:
        readme_version = m.group(1)

if build_version and readme_version and build_version != readme_version:
    errs.append(f"VERSION MISMATCH: build/build.py VERSION ({build_version}) != README.md badge ({readme_version})")

# Extract and compare plugin_version in dist/*/versions.json
for plat in ["dist/claude-code", "dist/antigravity"]:
    v_file = root / plat / "versions.json"
    if not v_file.exists():
        errs.append(f"MISSING {plat}/versions.json")
    else:
        try:
            data = json.loads(v_file.read_text(encoding="utf-8"))
            plugin_v = data.get("plugin_version")
            if not plugin_v:
                errs.append(f"MISSING plugin_version in {plat}/versions.json")
            elif build_version and plugin_v != build_version:
                errs.append(f"VERSION MISMATCH: build/build.py VERSION ({build_version}) != {plat}/versions.json plugin_version ({plugin_v})")
        except Exception as e:
            errs.append(f"ERROR reading {plat}/versions.json: {e}")

# 2.95 Experimental source must NEVER leak into dist. The jules-dispatch pack lives
# under src/experimental/ and ships on demand via sync-skills, not the plugin bundle.
for plat in ["dist/claude-code", "dist/antigravity"]:
    pdir = root / plat
    if pdir.exists():
        for p in pdir.rglob("*"):
            if "experimental" in p.relative_to(pdir).parts:
                errs.append(f"EXPERIMENTAL PATH LEAKED INTO {plat}: {p.relative_to(root)}")

# 3. Counts
for plat in PLATFORMS:
    n = len(list((root / plat / "skills").glob('*/SKILL.md')))
    print(f"{plat}/skills: {n} skills")
print("external skills:", len(json.loads((root / 'src/external-skills.json').read_text(encoding='utf-8'))['skills']))

if errs:
    print("\nERRORS:")
    for e in errs:
        print(" -", e)
    sys.exit(1)

print("\nVALIDATION OK")
