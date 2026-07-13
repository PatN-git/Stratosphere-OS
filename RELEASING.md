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
   
   **First Release Note:** The very first release of the project (`v1.1.0`) was cut manually (rebuild → validate → git tag v1.1.0) since `release.py` requires an existing tag to establish a baseline. Subsequent version bumps are automatically derived by the script.

 3. **Commit & Merge to Main via PR:**
    Commit the updated version metadata, `dist/` builds, and `README.md` version badge to your working branch, open a Pull Request, and merge it into the `main` branch (never push directly to `main` as per our governance rules):
    ```bash
    git add .
    git commit -m "release: prepare vX.Y.Z"
    ```

 4. **Automated Validation and Publishing:**
    Upon pushing to `main`, the "Release on main" GitHub Action (`.github/workflows/release.yml`) automatically triggers. It will:
    - Extract the version from `build/build.py`.
    - Check if a release tag for this version already exists. If it does (e.g., for doc-only, test-only, or CI-only commits where the version did not change), the workflow exits early with success (no-op).
    - Run the full build verification suite and ensure that committed `dist/` files are fully up-to-date with source code.
    - Automatically tag the commit as `vX.Y.Z` and publish the official GitHub Release page.

    No manual git tagging or tag pushing is required.

## Versioning Conventions

- **Change-Based Versioning:** When editing source files in `src/`, always bump each edited file's version in its YAML frontmatter by the size of its change:
  - **PATCH**: Routine bug fixes, formatting, and typo corrections.
  - **MINOR**: Additive or backward-compatible modifications.
  - **MAJOR**: Breaking changes.
- **Derived Bumps:** Because most routine framework updates consist of bug fixes and minor logic corrections, they will result in `PATCH` bumps. Most derived plugin releases will therefore be patch (`Z`) bumps (e.g., `v1.1.0` -> `v1.1.1`), which is the expected and correct behavior.
- **First Release Note:** The very first release of the project (`v1.1.0`) was cut manually to establish a baseline. All subsequent versions must be derived and staged via `release.py` prior to merging to `main`.
