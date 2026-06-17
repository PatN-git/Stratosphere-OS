# StratosphereOS Artifact Versioning Standard

StratosphereOS utilizes a robust, per-file versioning system combined with content hashing to selectively update distributed artifacts (workflows, templates, rules, constitution files) without clobbering a user's local edits.

## 1. Version Format & Semantics
All distributed artifacts MUST carry a semantic version `x.y.z` and an updated date `YYYY-MM-DD`. The plugin version sets the baseline (e.g., `1.0.0`).

- **PATCH** (`x.y.Z`): Wording changes, formatting, typos. Safe for automatic application.
- **MINOR** (`x.Y.0`): Additive/backward-compatible changes (new optional sections, new guidance). Safe to adopt.
- **MAJOR** (`X.0.0`): Breaks the file's contract (renamed/removed phases, changed hand-off contracts). The updater flags these for manual review.

## 2. Authoring Convention (Forms)
A version must be stamped directly into the artifact. To prevent plugin-level metadata from leaking into produced or user-owned documents, we strictly use two forms depending on the artifact's role.

### Form A: YAML Frontmatter
For plugin-owned files that are read in place (e.g., workflows, commands, skills, rules, constitution, pure reference guides).
Add to the existing frontmatter block:
```yaml
version: "1.0.0"
updated: 2026-06-17
```

### Form B: Top HTML Comment
For templates that become user-edited living documents or produced docs (e.g., memory templates, instance templates like PRDs, `DESIGN.md`).
Add as the absolute **first line** of the file (before any `---`):
```markdown
<!-- stratosphere: version=1.0.0 updated=2026-06-17 -->
```

## 3. Enforcement & Bump Guard
The build pipeline (`build.py`) generates a `versions.json` manifest recording the `version` and a `body_hash` for every artifact. 
The `body_hash` is computed **after stripping the Form A or Form B version marker**, meaning a version bump alone never changes the hash.

**The Bump Guard:** `validate.py` enforces that if a file's content hash changes relative to the committed baseline, its `version` MUST be bumped. Builds will fail if a developer forgets to bump a modified file.
