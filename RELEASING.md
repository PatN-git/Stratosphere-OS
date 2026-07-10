# StratosphereOS Release Workflow

This document describes how to release a new version of the StratosphereOS plugin framework.

## Step-by-Step Release Process

1. **Update Artifact Versions:**
   For every source file you edited in `src/`, bump its version and timestamp in the YAML frontmatter following the [Artifact Versioning Standard](docs/VERSIONING.md). Note that the build pipeline's Bump Guard will fail if you forget to bump a modified file.

2. **Derive & Stage the Release:**
   Execute the release script to derive the overall plugin version bump level, write it to `build/build.py` and `README.md`, re-compile the build outputs, and run validation:
   ```bash
   python scripts/release.py
   ```
   *Note: This script enforces the "biggest change wins" convention (Major if any major bump or removal; Minor if any minor bump or addition; Patch if only patch bumps).*
   
   **First Release Note:** The very first release of the project (e.g. `v1.1.0`) must be cut manually (rebuild → validate → git tag v1.1.0) since `release.py` requires an existing tag to derive versions from. Subsequent version bumps will be automatically derived by the script.

3. **Commit the Staged Release:**
   Commit the updated version metadata, `dist/` builds, and `README.md` version badge:
   ```bash
   git add .
   git commit -m "release: prepare vX.Y.Z"
   ```

4. **Tag & Push:**
   Create a git tag matching the derived version exactly (the `v*` prefix is mandatory and tag MUST equal `v` + `build.py` VERSION), then push:
   ```bash
   git tag vX.Y.Z
   git push origin main --tags
   ```

5. **Automated Publishing:**
   The GitHub Action `.github/workflows/release.yml` will trigger, run the full validation suite, and create the official GitHub Release page automatically. The preflight check in `/stratosphere-update` relies on these releases to check for newer plugin versions.
