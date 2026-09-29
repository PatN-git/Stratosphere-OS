---
type: plan
title: "StratOS 4.1.1 Hygiene — frontmatter drift, dry-run wording, update-skill gap, bump guard"
description: "Sized plan for the F1–F5 observations from the 4.1 follow-ups: fix the drifted docs, lint for recurrence, correct misleading wording, and harden the bump guard."
generated:
  by: Claude Sonnet 5.5
  at: 2026-09-29
status: draft
version: "4.1.0"
---

# Plan — StratOS 4.1.1 Hygiene (F1–F5)

**Branch / PR:** same draft PR #124 (`chore/BT-116-stratos-v4-1-0-update`), on top of the reconcile fix. All product prose edits are **patch** bumps, so `release.py` derives 4.1.1 — the version the reconcile fix already set. No further version change.
**Sizing was verified by reading the code and by an empirical scratch-project run**, which corrected two claims in `stratos-4-1-followups-plan.md` (see F3, F4).

| # | Item | Size | Do now? |
|---|---|---|---|
| F1a | 3 BT-108 docs carry retired `timestamp:` / out-of-vocab `status` | XS | yes |
| F1b | Lint so it can't recur (`validate_memory.py`) | S | yes |
| F1c | Memory templates carry `timestamp:` (build field) into in-scope `.memory/` docs | M | **no — needs a decision** |
| F2 | Two references describe `blockedBy` as list-like | XS | yes |
| F3 | `--dry-run` help says "without writing" but stages files | XS | yes (wording) |
| F4 | `stratosphere-update` has no step for modified scripts | XS | yes (prose) |
| F5 | `bump_guard` watches one script; CRLF false positive on Windows | S | yes |

## F1a — fix the three drifted docs
Scan of `docs/` (excluding `archive/`, matching the validator's own skip list) finds exactly three files with problems: `docs/prds/BT-108-…md` (`timestamp:` + `status: approved`), `docs/design/BT-108-interface.md` (same), `docs/discovery/host-agnostic-skill-distribution.md` (`timestamp:` only; its `status` is the valid routing vocab). Cause: `PRD-template.md` is correct (`generated`, `draft|stable`); the 2a run deviated and 2c's reconcile added `generated:` without removing `timestamp:`. Change: delete the `timestamp:` line; `approved` → `stable`. Nothing else in those files. `version` is left as is. **Verify:** re-run the scan → 0 hits; `git diff` shows only those lines; `validate_memory.py` clean; the v3→v4 migration dry-run no longer wants to touch them.

## F1b — lint (deterministic, no agent pass)
In `src/scripts/validate_memory.py`'s existing OKF conformance loop, for files under `docs/` only (not `.memory/`, see F1c) add: (1) frontmatter key `timestamp` → message "retired inside the bundle scope, use `generated:`"; (2) `status` not in `draft|stable|deprecated` (strip trailing `# comment`), except `type: discovery-brief` (routing vocab). Severity follows the existing `okf_as_error` switch (warning by default) so consumer projects with legacy v0.1 docs are not newly broken. Tests: new `tests/framework/test_validate_memory_frontmatter.py` runs the script in a temp project with fixture docs (bad timestamp, bad status, valid, discovery-brief, archive-skipped) and asserts the messages — red before the change. Shipped script → covered by the 4.1.1 bump; rebuild `dist/`.

## F1c — deferred (decision needed, not done here)
`src/memory-templates/*.md` carry `timestamp:` (build-stamped) and no `generated:`; instantiated into `.memory/` (in scope) they violate the "timestamp retired" rule, and `migrate_v3_to_v4.py` would rewrite them. A proper fix touches `build.py` stamping, seven templates, the preserved-tier update path (existing projects never receive template frontmatter changes) and the migration. That is a design decision (stamp `generated:` at instantiation? exempt `.memory/` from the rule?). Recorded; lint F1b deliberately excludes `.memory/` so it doesn't fire on every project.

## F2 — reference prose
`src/references/concept-map-operations.md:76` and `src/workflows/3c-sprint-planning.md:30`: say `blockedBy` is a connection (`blockedBy.nodes`, gh returns `{nodes,totalCount}`) so an agent parsing it doesn't assume a list. One sentence each; patch-bump each file's `version`/`timestamp`. Because these are lifecycle/skill artifacts, edit under the repo-local `improve-workflows-skills` discipline (surgical, token-economy). **Verify:** `build.py`, `validate.py`, skill-conformance tests, `release.py` derives 4.1.1.

## F3 — dry-run wording (and a correction)
Empirical run in a scratch project: `--dry-run` (fresh) writes `.gitignore/.gitattributes.stratosphere-new`; `--update --dry-run` writes `*.stratosphere-new` proposals plus `.tmp/stratosphere-update-worklist.json` (also into an otherwise-missing skill dir, holding only the `.stratosphere-new`). This is by design — the update flow's Phase 1 depends on it. **Correction:** it does *not* create the real skill files; the earlier "created 26 skills" claim was wrong (it created their directories with staged proposals). Change: reword `--dry-run` help and the usage header in `scaffold.py` to "writes nothing except `*.stratosphere-new` proposals and `.tmp/` worklist". Wording only; no behaviour change. `scaffold.py` is watched by `bump_guard`, covered by 4.1.1.

## F4 — update-skill gap (and a correction)
`scaffold.py` classifies a script with no lock baseline and differing content as `needs_review_scripts` — correct and conservative; after one review the lock records a baseline, so it does **not** recur (the earlier "always" was wrong). The real gap: `src/commands/stratosphere-update/SKILL.md` Phase 2 handles preserved conflicts, constitution and unmarked files but has no step for `needs_review_scripts`, so the agent improvises. Observed hazard: editing `<script>.stratosphere-new` is futile — every update run re-stages the incoming bytes over it. Add a short Phase 2 subsection: merge incoming changes **into the real script** (keep local fixes, take new features), delete the `.stratosphere-new`, re-run `--update` so the lock records the baseline. Patch-bump the skill; `improve-workflows-skills` discipline. **Verify:** skill-conformance tests, `build/validate`.

## F5 — bump guard
`build/bump_guard.py` `FRAMEWORK_FILES = ["src/scripts/scaffold.py"]`. Other shipped scripts (`reconcile.py`, `validate_memory.py`, …) can change with no bump requirement (this is how 4.1.1 got missed by CI). Derive the list from the shipped scripts (`src/scripts/**/*.py`, excluding test dirs, matching what `build.py` bundles). Also normalise CRLF before comparing — on Windows the working copy differs from the tag blob byte-for-byte, producing a false "scaffold.py changed". Add `tests/framework/test_bump_guard.py` using a temp git repo with a tag (changed script without bump → exit 1; with bump → 0; CRLF-only difference → no reason). **Verify:** guard passes on the current branch; a deliberate unbumped script edit fails it.

## Order of work
1. F5 tests first (red), guard change.
2. F1a docs; F1b test (red) then lint.
3. F3 wording; F4 and F2 prose (via `improve-workflows-skills`).
4. `release.py` (expect derive 4.1.1 = current), `build`, `validate`, full `pytest`, `bump_guard`.
5. Push to PR #124; update PR body.

## Risks
- F1b severity: warning-by-default means drift is surfaced, not blocked; chosen to avoid breaking consumers with v0.1 docs. Upgrading to error later is a one-flag decision.
- F5 widening means future unbumped script edits fail CI — intended, but note this PR's own edits (`validate_memory.py`, `scaffold.py`) are covered by the existing 4.1.1.
- `release.py` may derive something other than 4.1.1 if a prose edit is mis-bumped (minor); the plan keeps all bumps patch.
