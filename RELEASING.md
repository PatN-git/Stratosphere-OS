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

   **Then validate the plugin manifests (manual).** Both hosts' validators check what the host really loads, which `tests/framework/test_dist_bundle.py` only approximates. They are not in CI yet because that needs both CLIs installed there; revisit once a checklist run has caught something.
   ```bash
   claude plugin validate .      # Claude Code marketplace + plugin: expect no errors
   agy plugin validate dist      # Antigravity plugin root: expect [ok] and `skills: <N> processed`
   ```
   `<N>` is the number of directories in `dist/skills` (the real output pads the colon: `skills      : <N> processed`); a count of `skipped (not found)` means `dist/plugin.json` or `dist/skills/` is missing.
   *Recorded dry run (2026-10-06, `agy` 1.3.0, working tree before the 4.5.0 bump): `agy plugin validate dist` printed `[ok] dist` and `skills: 27 processed`. `claude plugin validate .` could not run: the `claude` CLI is not installed on that machine, so its expected output is not yet recorded.*
   
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
- **Non-Artifact Framework Changes:** Changes to non-`.md` framework files (e.g. `scaffold.py`, `.github` Action workflows, build configurations, and scripts under `build/` or `scripts/`) are not versioned via YAML frontmatter. Therefore, `release.py` will not derive an automatic version bump from them. When making such changes, you MUST manually bump the `VERSION` variable in `build/build.py` (and the README.md version badge) to ensure a new release is cut and preflight checks flag it for downstream projects.
- **First Release Note:** The very first release of the project (`v1.1.0`) was cut manually to establish a baseline. All subsequent versions must be derived and staged via `release.py` prior to merging to `main`.

## v4.0.0 — breaking release

v4.0.0 renames every lifecycle artifact to Agent Skills spec form (`_` → `-`) and moves
them from `.agents/workflows/*.md` to `.agents/skills/<name>/SKILL.md`. **There are no
alias shims** — `/0a-start-session` stops resolving; use `/0a-start-session`.

Existing projects need a one-shot migration. `stratosphere-update` alone is **not**
sufficient: `reconcile_gitignore()` only adds entries, so an upgraded project keeps
`.agents/skills/` in its `.gitignore` and silently ignores every migrated skill.

```bash
# from the target project root, after updating the plugin
python <plugin>/scripts/migrations/migrate_v3_to_v4.py            # dry run (default)
python <plugin>/scripts/migrations/migrate_v3_to_v4.py --apply
```

It rewrites the stale `.gitignore` entry, removes the superseded `.agents/workflows/`
tree (sparing user-authored files), and migrates the project's own `.memory/` and
`docs/` frontmatter to OKF v0.2. It is idempotent and **defaults to a dry run** — unlike
`migrate_agent_to_agents.py`, which only renames a file, this one deletes, so the
safe default is inverted. It spares user-authored workflow files and reports
anything it leaves behind.

## v5.0.0 — breaking release

v5.0.0 makes GitHub the only store of issue state when `tracker: github` (BT-194). There is no
`BACKLOG_MAP.md` in that mode: workflows read through scoped `gh --json` queries and a post-condition
gate (`reconcile.py --expect`) checks each multi-write phase against the phase's own intended state.
The local backend (`tracker: local`) **never touches GitHub** and no longer uses `BACKLOG_MAP.md` (BT-221):
each issue is one markdown file (frontmatter plus the full body, Acceptance Criteria included, plus comments)
on the `<repo>/issues` branch, never in a feature branch, so every branch and worktree sees one state.
`python .agents/scripts/issues.py` is its only reader and writer (`get`, `list`, `wip`, `ready`, `create`, `set`,
`comment`, `claim`, `close`, `check`, `sync`); `ice_read.py candidates` runs on both backends.

**Removed, no shims:** the map-vs-GitHub diff, `reconcile.py --heal`, `--summary`, `--all-open --summary`
and `--require-gh`; `nightly_state.py drift` and the `drift` key of `.last-run.json`; 0d's backlog drift
check and heal; the local `--ids ... --fields` gate clauses in 3a, 3b, 3c, 4a and `post-merge-sync.md`.
`STATUS.md` is now folder state only (session lines; a task's progress is a resume note on its issue).

**What an existing project must do** (`stratosphere-update` alone is not enough):
- A project with a `BACKLOG_MAP.md` (and no `tracker: github`) must migrate it once: `stratosphere-update`
  offers it, or run from the project root, after updating:

```bash
python .agents/scripts/issues.py migrate           # map -> <repo>/issues branch; the map moves to .memory/archive/
```

  Then set `tracker: local` in `.memory/ARCHITECTURE.md` to stay local. To use GitHub issues instead, migrate
  first, then:

```bash
python .agents/scripts/tracker_switch.py          # dry run (default)
python .agents/scripts/tracker_switch.py --apply  # creates the issues with their bodies and comments, rewrites BT-LOCAL ids, sets tracker: github
```

  It is safe to re-run and writes `tracker: github` last. `scaffold --update` prints a NOTE for exactly this
  case (`tracker_advisory` in the worklist). Migrated issues carry the map row's fields, ICE metrics and
  `Refs:` line; bodies the map never stored cannot be recovered.
- A local project with a remote pushes `<repo>/issues` with the 4a ship push; `0a` runs `issues.py sync`.
- `scaffold --update` flags the constitution (`needs_review_constitution`: the 0a branch rule in
  AGENTS.md section 4 changed) and the STATUS template (unmarked): accept the trimmed STATUS file that
  0b proposes (an old-format STATUS keeps working; `validate_memory.py` warns when it is over 3,000
  characters or tracked by git). `.memory/STATUS.md` and `.memory/resume/` are now
  in the managed `.gitignore` entries; untrack a tracked STATUS with `git rm --cached .memory/STATUS.md`.
- The `BACKLOG_MAP.md` template is gone; `scaffold --update` neither places nor merges a map.
