#!/usr/bin/env python3
"""
StratosphereOS Release Version Derivation & Staging Tool.

Convention: "Biggest change wins"
- Major bump if any artifact has a MAJOR bump, or an artifact is removed.
- Minor bump if any artifact has a MINOR bump, or a new artifact is added.
- Patch bump if any artifact has a PATCH bump.
- None if no artifact versions were bumped.

This script derives the new plugin version based on changes to individual artifacts since the last git release tag.
It is a release-time tool and is not executed during normal local builds.
"""

import json
import re
import sys
import subprocess
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def get_bump_level(path, old_v, new_v):
    if old_v == new_v:
        return "none"
    try:
        o = list(map(int, old_v.split('.')))
        n = list(map(int, new_v.split('.')))
        if len(o) < 3 or len(n) < 3:
            return "patch"
        if n < o:
            print(f"Warning: Artifact version downgrade detected for {path}! {old_v} -> {new_v}")
            return "none"
        if n[0] > o[0]:
            return "major"
        elif n[1] > o[1]:
            return "minor"
        elif n[2] > o[2]:
            return "patch"
    except Exception:
        pass
    return "none"

def raise_version(v, level):
    parts = list(map(int, v.split('.')))
    if len(parts) < 3:
        parts = [1, 0, 0]
    if level == "major":
        return f"{parts[0]+1}.0.0"
    elif level == "minor":
        return f"{parts[0]}.{parts[1]+1}.0"
    elif level == "patch":
        return f"{parts[0]}.{parts[1]}.{parts[2]+1}"
    return v

def run_cmd(args, capture=True):
    res = subprocess.run(args, cwd=str(ROOT), capture_output=capture, text=True)
    return res

def main():
    parser = argparse.ArgumentParser(description="StratosphereOS release version derivation tool.")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt (CI mode).")
    args = parser.parse_args()

    # 1. Find last tag
    print("Finding the last release tag...")
    tag_res = run_cmd(["git", "describe", "--tags", "--abbrev=0", "--match", "v[0-9]*"])
    last_tag = tag_res.stdout.strip() if tag_res.returncode == 0 else None

    baseline_manifest = {}
    baseline_plugin_version = None

    if last_tag:
        print(f"Last release tag found: {last_tag}")
        # 2. Get baseline manifest
        git_show = run_cmd(["git", "show", f"{last_tag}:dist/claude-code/versions.json"])
        if git_show.returncode == 0:
            try:
                baseline_data = json.loads(git_show.stdout)
                baseline_plugin_version = baseline_data.get("plugin_version")
                baseline_manifest = baseline_data.get("artifacts", {})
                print(f"Loaded baseline manifest from tag {last_tag} (plugin version: {baseline_plugin_version})")
            except Exception as e:
                print(f"Warning: Could not parse baseline manifest: {e}")
        else:
            print("Warning: Could not read dist/claude-code/versions.json from last tag.")
    else:
        print("No prior release tag found. Using current build.py version as baseline without derivation.")

    # 3. Read current build.py VERSION
    build_py_path = ROOT / "build" / "build.py"
    build_content = build_py_path.read_text(encoding="utf-8")
    m = re.search(r'VERSION\s*=\s*(["\'])([^"\']+)((?:\1))', build_content)
    if not m:
        print("Error: Could not find VERSION variable in build/build.py")
        sys.exit(1)
    current_build_version = m.group(2)

    if not last_tag or not baseline_plugin_version:
        print(f"Baseline plugin version falls back to current build.py version: {current_build_version}")
        baseline_plugin_version = current_build_version
        # Skip derivation, just perform build + validate
        derived_version = current_build_version
        overall_bump = "none"
        changes_summary = []
    else:
        # 4. Generate new manifest by running build.py
        print("Compiling current artifacts...")
        build_res = run_cmd([sys.executable, "build/build.py"])
        if build_res.returncode != 0:
            print(f"Error compiling artifacts: {build_res.stderr}")
            sys.exit(1)

        new_versions_file = ROOT / "dist/claude-code/versions.json"
        if not new_versions_file.exists():
            print("Error: build.py succeeded but dist/claude-code/versions.json was not created.")
            sys.exit(1)

        new_data = json.loads(new_versions_file.read_text(encoding="utf-8"))
        new_manifest = new_data.get("artifacts", {})

        # 5. Derivation logic
        overall_bump = "none"
        changes_summary = []

        # Check for additions and updates
        for path, meta in new_manifest.items():
            new_v = meta.get("version", "1.0.0")
            if path not in baseline_manifest:
                changes_summary.append((path, "added", "minor"))
                if overall_bump not in ["major"]:
                    overall_bump = "minor"
            else:
                old_v = baseline_manifest[path].get("version", "1.0.0")
                bump = get_bump_level(path, old_v, new_v)
                if bump != "none":
                    changes_summary.append((path, f"{old_v} -> {new_v}", bump))
                    if bump == "major":
                        overall_bump = "major"
                    elif bump == "minor" and overall_bump != "major":
                        overall_bump = "minor"
                    elif bump == "patch" and overall_bump not in ["major", "minor"]:
                        overall_bump = "patch"

        # Check for removals
        for path in baseline_manifest:
            if path not in new_manifest:
                changes_summary.append((path, "removed", "major"))
                overall_bump = "major"

        if overall_bump == "none":
            print("\nNo changes detected across artifacts. No version bump is derived.")
            derived_version = baseline_plugin_version
        else:
            derived_version = raise_version(baseline_plugin_version, overall_bump)
            print(f"\nDerived Bump Level: {overall_bump.upper()}")
            print(f"New Plugin Version: {derived_version} (previous: {baseline_plugin_version})")

    if changes_summary:
        print("\nArtifact Changes Summary:")
        for path, change, bump in changes_summary:
            print(f"  - {path}: {change} ({bump})")
    else:
        if last_tag:
            print("\nNo artifact changes detected against baseline.")

    # 6. Confirmation and write
    if derived_version != current_build_version or overall_bump != "none" or not last_tag:
        if not args.yes:
            ans = input(f"\nDo you want to stage version {derived_version} to build/build.py and README.md? (y/n): ").strip().lower()
            if ans not in ['y', 'yes']:
                print("Aborted.")
                sys.exit(0)

        did_update = False
        if derived_version != current_build_version:
            # Update build/build.py with captured quote style
            m_quote = re.search(r'VERSION\s*=\s*(["\'])([^"\']+)((?:\1))', build_content)
            if m_quote:
                new_build_content = re.sub(
                    r'(VERSION\s*=\s*)(["\'])([^"\']+)(\2)',
                    r'\g<1>\g<2>' + derived_version + r'\g<4>',
                    build_content
                )
                build_py_path.write_text(new_build_content, encoding="utf-8")
                print("Updated build/build.py VERSION.")
                did_update = True
            else:
                print("Error: Could not re-parse VERSION to detect quote character.")
                sys.exit(1)

            # Update README.md version badge (shield URL) with count=1 limit
            readme_path = ROOT / "README.md"
            readme_content = readme_path.read_text(encoding="utf-8")
            new_readme_content = re.sub(
                r'(img\.shields\.io/badge/version-)(\d+\.\d+\.\d+)',
                r'\g<1>' + derived_version,
                readme_content,
                count=1
            )
            readme_path.write_text(new_readme_content, encoding="utf-8")
            print("Updated README.md badge version.")

        # If it is a first release (no last_tag) or we updated the version, compile it
        if did_update or not last_tag:
            print("Recompiling with new version...")
            run_res = run_cmd([sys.executable, "build/build.py"])
            if run_res.returncode != 0:
                print(f"Build failed: {run_res.stderr}")
                sys.exit(1)
        else:
            print("No version change. Re-using previous compilation.")

        # Always validate the resulting build outputs
        print("Running validate.py...")
        val_res = run_cmd([sys.executable, "build/validate.py"])
        if val_res.returncode != 0:
            print(f"Validation failed: {val_res.stdout}\n{val_res.stderr}")
            sys.exit(1)

        print(f"\nSuccessfully staged and validated version {derived_version}!")
    else:
        print("\nCodebase is already up to date with derived version.")

if __name__ == "__main__":
    main()
