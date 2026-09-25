---
type: reference
title: StratosphereOS Artifact Versioning Standard
description: Per-file semantic versioning and content-hash rules for distributed artifacts.
generated:
  by: Patrick Nennewitz
  at: 2026-09-15
version: "1.0.0"
---

# StratosphereOS Artifact Versioning Standard

StratosphereOS utilizes a robust, per-file versioning system combined with content hashing to selectively update distributed artifacts (workflows, templates, rules, constitution files) without clobbering a user's local edits.

## 1. Version Format & Semantics
All distributed artifacts MUST carry a semantic version `x.y.z`. The change-date field differs by scope: framework artifacts under `src/` carry `timestamp: YYYY-MM-DD` (a build field); in-scope OKF documents under `docs/` and `.memory/` carry `generated: {by, at}` instead (`okf-protocol.md` §2). The plugin version sets the baseline (e.g., `1.0.0`).

- **PATCH** (`x.y.Z`): Wording changes, formatting, typos.
- **MINOR** (`x.Y.0`): Additive/backward-compatible changes (new optional sections, new guidance).
- **MAJOR** (`X.0.0`): Breaks the file's contract (renamed/removed phases, changed hand-off contracts).

Note: The semver level communicates change magnitude to humans and drives the derived plugin bump; it does NOT gate the updater. The updater decides whether to auto-apply a change or perform a manual merge purely based on content. A framework block that the user has never customized is swapped automatically regardless of whether the change is a patch, minor, or major update. Conversely, any block the user has customized will result in a manual conflict-merge, regardless of its semver level.

## 2. Authoring Convention
With the introduction of the Open Knowledge Format (OKF), the versioning format has been strictly unified. Every distributed artifact (skills, rules, constitution files, and memory templates) MUST carry its version metadata within a YAML frontmatter block at the top of the file. Note the two date fields are **not** interchangeable: framework artifacts under `src/` keep `timestamp:` as a build field, while in-scope OKF documents under `docs/` and `.memory/` use `generated: {by, at}` (`okf-protocol.md` §2).

Add to the existing frontmatter block:
```yaml
version: "1.1.0"
timestamp: 2026-09-15
```

`timestamp` is OKF's standard last-change field; `version` is a StratOS extension. The retired `updated` field is no longer used.

*Note: For templates governed by strict external specifications (e.g., `@google/design.md`), this unified approach remains compliant. Their linters are designed to be extensible and will safely ignore custom OKF keys like `type`, `version`, and `timestamp` without error.*

## 3. Enforcement & Bump Guard
The build pipeline (`build.py`) generates a `versions.json` manifest recording the `version` and a `body_hash` for every artifact. 
The `body_hash` is computed **after stripping the version and timestamp keys from the frontmatter**, meaning a version bump alone never changes the hash.

**The Bump Guard:** `validate.py` enforces that if a file's content hash changes relative to the committed baseline, its `version` MUST be bumped. Builds will fail if a developer forgets to bump a modified file.

## 4. Plugin Version & Release Flow
The overall framework plugin version is derived from individual artifact version bumps using a "biggest change wins" strategy.

- **Derivation Logic**: If any modified artifact has a `MAJOR` bump, the plugin version receives a major bump. If no `MAJOR` bump is present but at least one artifact has a `MINOR` bump, the plugin receives a minor bump. Otherwise, it receives a `PATCH` bump. The `scripts/release.py` script computes this bump automatically by comparing changed files against the previous release tag's manifest.
- **Synchronized Locations**: The derived version is maintained in four places that must be kept in exact lockstep:
  1. `build/build.py` `VERSION` string
  2. `README.md` version badge
  3. `dist/claude-code/versions.json` `plugin_version`
  4. `dist/antigravity/versions.json` `plugin_version`
  
  The build validation script (`build/validate.py`) enforces this synchronization and fails the build on any mismatch.
- **End-to-End Release Flow**:
  1. **Edit & Bump**: Modify source files in `src/` and bump their individual versions in their frontmatter blocks.
  2. **Derive & Stage**: Run `python scripts/release.py` locally to automatically calculate the new plugin version, update `build/build.py` and `README.md`, re-compile the build outputs (`dist/`), and run validation.
  3. **PR & Merge**: Commit the changes, open a PR, and merge to the `main` branch.
  4. **Auto-Release**: The "Release on main" workflow detects the new version on push, verifies consistency, checks that a release for this version doesn't already exist, and automatically tags the commit as `v<VERSION>` and publishes a GitHub Release.
  5. **Client Update**: The `/stratosphere-update` skill runs a remote preflight check, comparing the locally installed version against the latest published release tag.
- **Release Invariant**: The tag name must exactly match `v` + `VERSION`, which must equal the plugin version in both platform manifests. This is guaranteed by `validate.py` and the CI stale-dist guard (`git status --porcelain dist/`).
- **Conditional Releases**: Releases are cut only when `VERSION` moves (indicating that a distributed artifact was modified and rebuilt). Documentation, testing, or CI-only changes do not bump version metadata and thus do not trigger a new release.
- **Initial Bootstrapping**: The very first release (`v1.1.0`) was cut manually since no prior tag existed for comparison. All subsequent releases are derived automatically via `release.py`.
- **What /stratosphere-update Covers**:
  - `scaffold.py` acts as the single installer and updater for all framework-owned files.
  - When running `/stratosphere-update` (which invokes `scaffold.py --update`), it selectively refreshes framework files according to their tier without clobbering user customizations:
    1. **Memory Registries (`.memory/`)**: Protected via `SOS:BLOCK` markers and three-way block-level merging. User-customized blocks are preserved; unedited blocks receive framework updates automatically.
    2. **Constitution Files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`)**: User edits are never overwritten. When upstream changes occur, the incoming template is staged at `<file>.stratosphere-new` and reported under `needs merge/review` for explicit user approval.
    3. **Project Scripts (`.agents/scripts/**`)**: Script baselines are tracked via SHA-256 in `.stratosphere-lock.json` across install, update, and repair-lock. Pristine scripts matching baseline or known historical release hashes are refreshed in place. Locally modified scripts are preserved byte-for-byte on disk, staged with `<script>.stratosphere-new`, and reported under `NEEDS-REVIEW (modified script)`.
    4. **Managed Rules & Skills (`.agents/rules/`, `.agents/skills/`, and host mirrors)**: Refreshed in place when updated upstream. Framework files removed or renamed between versions are safely pruned by the orphan-guard if pristine, or preserved under `NEEDS-REVIEW (modified orphan)` if modified.
    5. **Opted-in GitHub Actions**: Managed only if allowlisted and already opted-in by the project.
  - It additively reconciles required `.gitignore` and `.gitattributes` lines (e.g. `*.work.md` and linguist diff directives) without removing or reordering user-written lines.
  - Third-party and domain-specific skills are updated separately via `/sync-skills` as they are gitignored and fetched on demand.
  - An automated orphan-guard test in CI (`tests/verify_scripts.py`) enforces that no bundled framework file can be orphaned (every bundled file must be mapped by `scaffold.py` to its project destination or explicitly excluded with a documented reason).
