#!/usr/bin/env python3
"""Release bump-guard — fail if shipped framework content changed since the last
release tag but build.py VERSION did not advance.

This closes the gap that let a feature merge without a version bump: validate.py's
existing guards only catch a *modified* .md whose frontmatter version didn't bump
(§5) and VERSION *consistency* (§2.9) — neither catches a NEW artifact or a non-.md
framework change (e.g. scaffold.py) landing without a plugin-VERSION bump.

Signals of "shipped content changed since <tag>":
  1. the dist versions.json artifact manifest differs (covers every .md artifact:
     workflows, commands, skills, rules, memory templates, references), OR
  2. a tracked non-.md framework file changed (scaffold.py).
If either changed AND VERSION <= the last tag's version -> error.

Doc-only / test-only / CI-only changes don't touch (1) or (2), so they pass (matching
release.yml's no-op policy). Intended for CI on PRs to main. Requires tags fetched
(checkout fetch-depth: 0). Run: python build/bump_guard.py [root]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
FRAMEWORK_FILES = ["src/scripts/scaffold.py"]  # non-.md files that also warrant a bump
MANIFEST = "dist/antigravity/versions.json"


def sh(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)


def semver(v):
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", (v or "").strip())
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def current_version():
    m = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', (ROOT / "build" / "build.py").read_text(encoding="utf-8"))
    return m.group(1) if m else None


def last_release_tag():
    tags = [t for t in sh("tag", "--list", "v[0-9]*", "--sort=-v:refname").stdout.splitlines() if t.strip()]
    return tags[0] if tags else None


def blob_at(ref, path):
    r = sh("show", f"{ref}:{path}")
    return r.stdout if r.returncode == 0 else None


def main():
    tag = last_release_tag()
    if not tag:
        print("bump-guard: no release tag found — skipping.")
        return 0

    tag_manifest_raw = blob_at(tag, MANIFEST)
    if tag_manifest_raw is None:
        print(f"bump-guard: cannot read {MANIFEST} at {tag} (are tags fetched? use checkout fetch-depth: 0) — skipping.")
        return 0

    cur_manifest = json.loads((ROOT / MANIFEST).read_text(encoding="utf-8")).get("artifacts", {})
    tag_manifest = json.loads(tag_manifest_raw).get("artifacts", {})

    reasons = []
    if cur_manifest != tag_manifest:
        added = sorted(set(cur_manifest) - set(tag_manifest))
        removed = sorted(set(tag_manifest) - set(cur_manifest))
        changed = sorted(p for p in cur_manifest if p in tag_manifest and cur_manifest[p] != tag_manifest[p])
        reasons.append(f"artifact manifest changed (added={added[:5]} removed={removed[:5]} changed={changed[:5]})")
    for f in FRAMEWORK_FILES:
        cur = (ROOT / f).read_text(encoding="utf-8") if (ROOT / f).exists() else None
        if cur is not None and cur != blob_at(tag, f):
            reasons.append(f"{f} changed")

    if not reasons:
        print(f"bump-guard: no shipped-content change since {tag} — OK.")
        return 0

    cur_v, tag_v = current_version(), tag.lstrip("v")
    if semver(cur_v) <= semver(tag_v):
        print(f"::error::Shipped content changed since {tag} but VERSION did not advance "
              f"(build.py VERSION={cur_v}, last release={tag_v}). Run 'python scripts/release.py' to bump before merge.")
        for r in reasons:
            print(f"  - {r}")
        return 1

    print(f"bump-guard: OK — VERSION {cur_v} > last release {tag_v}; changes: {reasons}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
