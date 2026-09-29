---
type: plan
title: "StratOS 4.1 Follow-ups — reconcile.py gh shape, plan frontmatter, local cleanup"
description: "Fix reconcile.py's crash on real gh output, make the test shim mirror real gh, and clear the loose ends found while updating this dev project to 4.1.0."
generated:
  by: Claude Sonnet 5.5
  at: 2026-09-29
status: draft
version: "4.1.0"
---

# Plan — StratOS 4.1 Follow-ups (rev 2, after independent review)

**Branch / PR:** `chore/BT-116-stratos-v4-1-0-update`, draft PR #124 (part of #116). Only item R touches shipped product code (`src/`).
**Deliberate structure decision:** the owner asked for everything in the one draft PR. The review noted a product fix normally gets its own feature PR (AGENTS.md §4) and that merging R cuts release 4.1.1 via `release.yml`. We keep one PR as instructed, give R its own tracking issue for commit traceability, and keep R's commits separate so it can be split out later if wanted.

**Origin:** updating this repo to v4.1.0 with `stratosphere-update` surfaced one product bug and several loose ends.

## R. `reconcile.py` crashes on real `gh` output (product fix)

**Verified** (live `gh` and a repro): `gh issue view 118 --json blockedBy,parent` returns `blockedBy: {"nodes": [], "totalCount": 0}`; `subIssues` has the same shape, with nodes `{id, number, state, title, url}`; `parent` is a plain object or `null`. `compare()` with that `blockedBy` raises `TypeError: string indices must be integers` (`src/scripts/reconcile.py:90` iterates the dict's keys).
It went unnoticed because both mocks use flat lists: `tests/workflows/test_reconcile.py` and `tests/lifecycle-harness/shims/gh_shim.py` (whose docstring claims to mirror real `gh`).
Only `reconcile.py:90` parses these shapes; everything else is agent-read prose (F2).

**Changes**
1. `src/scripts/reconcile.py`: normalise `blockedBy` to a list — accept `{"nodes": [...]}` (real), a flat list (back-compat), and `None`. Read only `number`. `parent` is untouched (verified real shape, already handled). *Known limit, documented in a comment:* `totalCount > len(nodes)` (pagination) is not followed.
2. `tests/workflows/test_reconcile.py` is **never collected by pytest** (only a `__main__` runner; `pytest --collect-only` → "no tests collected"). Convert it to a real collected test (wrap `main()` in a `test_*` function and turn `sys.exit` into an assert) so the suite actually guards reconcile. Make `gh_issue` emit the real shape; add cases: empty nodes, non-empty nodes matching and drifting, flat-list back-compat, `None`, and the `main()` online path with `{nodes}`. **Verify the new cases fail on the old code** by running them under pytest *before* the fix.
3. `tests/lifecycle-harness/shims/gh_shim.py`: serialise `blockedBy`/`subIssues` as `{"nodes": [...], "totalCount": n}` inside `project()` — the single output boundary shared by `issue view`, `issue list --json`, and `pr view` (internal store stays lists, so `assertions.py` is unaffected); add `id`/`url` to `brief()` so nodes match real `gh`; fix the docstring. Update `tests/lifecycle/test_l3_gh_shim.py:200-214` (reads `["subIssues"]`/`["blockedBy"]` as lists, asserts `== []`). That file also drives the real `reconcile.py` through the shim (lines ~266-300) and becomes the effective pytest regression for R. *Cannot verify offline:* the LLM-driven L3 lifecycle runs (e.g. `4a` epic check reading `subIssues`) will now see the real shape, which is correct.
4. Version: **4.1.0 → 4.1.1**, by hand. Rationale is `RELEASING.md` ("Non-Artifact Framework Changes ... MUST manually bump `VERSION`"), **not** `bump_guard.py` — it only watches `src/scripts/scaffold.py` and would pass without the bump. Do not use `scripts/release.py` (it derives from `.md` artifact bumps and would derive "none"). Files that change: `build/build.py` (VERSION), `README.md` badge, `dist/{antigravity,claude-code}/plugin.json`, both `versions.json` `plugin_version`, and the bundled `dist/*/scripts/reconcile.py`. Then `python build/build.py`, `validate.py`, `bump_guard.py`; expect `git diff --stat dist` to show only those. Adding `reconcile.py` to `bump_guard.FRAMEWORK_FILES` is a build-tooling decision, recorded as F5, not done here.

**Verify:** new tests fail before / pass after; live `fetch_issue`+`compare` on real issues #118 (has parent, empty blockedBy) and #108 (no parent) — no crash; full `pytest`; `validate.py`; `bump_guard.py`; CI `verify-dist` green.

**Not doing:** workflow/reference prose (F2).

## D. Five plans without OKF frontmatter

`validate_memory.py` reports exactly 5 errors: `docs/plans/{audit-report-then-slices,feature-level-acceptance-gate,host-agnostic-install-framework,lifecycle-run-defects,pr107-review-response}-plan.md`. Prepend a v0.2 block: `type: plan`, `title` (from H1), `description`, `generated.by` (git author of the file), `generated.at` (date added), `status`, and `version: "4.1.0"` (okf-protocol §5: `version` is the plugin version that last wrote the doc, never a revision). `status`: *Implemented/Applied* → `stable` (4 files); host-agnostic plan → `draft` (BT-108 is still open, slices unimplemented). Body stays byte-identical (files are LF, no BOM). **Verify:** `validate_memory.py` reports 0 errors; `git diff` shows additions only.

## L. Stale lockfile entries (local, gitignored)

`.agents/.stratosphere-lock.json` lists 35 stale `.agents/workflows/*` entries (of 132). Drop them by importing the existing `prune_lock` from `scripts/migrations/migrate_v3_to_v4.py` once (no import-time side effects; touches only the lockfile). **Do not run `migrate_v3_to_v4.py --apply`**: its frontmatter step turns `timestamp:` into a second `generated:` key and would corrupt the BT-108 docs, which already carry both (F1).

## P. Stale local Antigravity plugin (local, gitignored)

`.agents/plugins/stratosphere-os/` is a 3-skill v1.0.0-era copy (no `versions.json`/`.install-source.json`). It is a legitimate *layout* for local Antigravity installs (installer, `scaffold.py`, install-harness all support it), so the claim is only "stale here, and no code requires it to exist". Before moving it to the backup folder, confirm scaffold's plugin-root resolution from this repo does not depend on it (it resolved the global Claude plugin during the update). **Verify:** `python <plugin>/scripts/scaffold.py --verify` (or the update dry-run) still resolves the global plugin and reports no error.

## A. Global plugin refresh — after merge/release

Global Antigravity plugin is **4.0.0**; Claude global is 4.1.0. After 4.1.1 is released from `main`: run `install-antigravity.ps1 --global` and `install-claude-code.sh --global`, then `stratosphere-update` here.
**Correction:** `.agents/scripts/reconcile.py` is currently byte-identical to the buggy product copy — an earlier hand-merge of a `{nodes}` patch into it was overwritten by a later update run. So the local script crashes on `blockedBy` until R ships; the next update after 4.1.1 replaces it with the fixed product version. (The recurring "modified script / NEEDS-REVIEW" flag is the lockfile-hash issue F4, not a content divergence.)

## Observations recorded, not fixed here

- **F1** Memory templates (e.g. `STATUS.md`) and the BT-108 docs from 2a/2b/2c carry `timestamp:` beside `generated:`, and `status: approved` outside the v0.2 vocabulary; the v3→v4 migration would double the `generated:` key.
- **F2** `concept-map-operations.md:76` and `3c-sprint-planning.md:30` describe `blockedBy` loosely (list-like).
- **F3** `scaffold.py --update --dry-run` writes: `.tmp/stratosphere-update-worklist.json`, `*.stratosphere-new` for changed files (documented by design, gitignored), and — observed here — created the 26 missing bundled skills under `.agents/skills/`.
- **F4** Scripts absent from the lockfile always land in "modified script / NEEDS-REVIEW".
- **F5** `bump_guard.FRAMEWORK_FILES` lists only `scaffold.py`; other shipped non-`.md` files (e.g. `reconcile.py`, `validate_memory.py`) can change without a required bump.
Offer to file these as issues; none block this PR.

## Order of work

1. Create the tracking issue for R (`type:bug`), then R as commits: `test` (collect + real shape, red on old code) → `fix(BT-<n>)` → shim → `release` (4.1.1 + dist).
2. D as `docs(BT-116)`.
3. P then L locally (backups first, no commit).
4. Push to draft PR #124; ready-for-review only on the owner's say.
5. A after merge/release.

## Risks

- Non-empty `blockedBy` nodes are assumed to match `subIssues` nodes (same GraphQL connection type); today only empty `blockedBy` and non-empty `subIssues` were observable. The fix reads only `number` and accepts both shapes.
- Merging this PR releases 4.1.1 (release.yml tags on `main` when VERSION is new) even though the PR is titled `chore`; intentional, stated above.
