# StratosphereOS Artifact Versioning Standard

StratosphereOS utilizes a robust, per-file versioning system combined with content hashing to selectively update distributed artifacts (workflows, templates, rules, constitution files) without clobbering a user's local edits.

## 1. Version Format & Semantics
All distributed artifacts MUST carry a semantic version `x.y.z` and an updated date `YYYY-MM-DD`. The plugin version sets the baseline (e.g., `1.0.0`).

- **PATCH** (`x.y.Z`): Wording changes, formatting, typos. Safe for automatic application.
- **MINOR** (`x.Y.0`): Additive/backward-compatible changes (new optional sections, new guidance). Safe to adopt.
- **MAJOR** (`X.0.0`): Breaks the file's contract (renamed/removed phases, changed hand-off contracts). The updater flags these for manual review.

## 2. Authoring Convention
With the introduction of the Open Knowledge Format (OKF), the versioning format has been strictly unified. Every distributed artifact (workflows, commands, rules, constitution files, and memory templates) MUST carry its version metadata within a YAML frontmatter block at the top of the file.

Add to the existing frontmatter block:
```yaml
version: "1.0.0"
updated: 2026-06-17
```

*Note: For templates governed by strict external specifications (e.g., `@google/design.md`), this unified approach remains compliant. Their linters are designed to be extensible and will safely ignore custom OKF keys like `type`, `version`, and `updated` without error.*

## 3. Enforcement & Bump Guard
The build pipeline (`build.py`) generates a `versions.json` manifest recording the `version` and a `body_hash` for every artifact. 
The `body_hash` is computed **after stripping the version and updated keys from the frontmatter**, meaning a version bump alone never changes the hash.

**The Bump Guard:** `validate.py` enforces that if a file's content hash changes relative to the committed baseline, its `version` MUST be bumped. Builds will fail if a developer forgets to bump a modified file.
