---
type: plan
title: BT-189 Decision Record — BACKLOG_MAP in GitHub mode
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-20
version: "1.2.1"
---

# Decision record: BT-189, BACKLOG_MAP as a generated read-only cache of GitHub

Status: **decided 2026-10-20 (H3), revised after independent review (58/100 → see Review log).**
- **Partial adopt of C.**
- **Ref** moves to a `Refs:` line in the issue body.
- **The tracker backend is recorded in `.memory/ARCHITECTURE.md`**, and setup asks for it with GitHub as the recommended answer.
- **CleanTechHub's switch is a one-off throwaway script.** The ongoing skill keeps only the local → GitHub path.

**Inputs:** the brief `docs/discovery/backlog-map-generated-cache.md` and the plan `docs/plans/backlog-map-spike-plan.md`.

**Evidence:** `.tmp/bt189/` (`s1-classification.md`, `s2-inventory.md`, `s3-measurements.md`, `gen_map.py`, `drift_by_ref.py`). Each analyst report was graded with 8-row spot checks.

**Test repos:** CleanTechHub (`PatN-git/cleantech_jobs`, the representative consumer) and StratOS.

## Decision: PARTIAL ADOPT of option C
When the tracker backend is GitHub, **there is no map**. Workflows read through scoped `gh --json` queries, and a **slimmer post-condition gate** checks each multi-write phase against the phase's own expected state.
- With the local tracker backend, today's table remains the issue store.
- B (generated map) is rejected.

| Criterion | A (today) | B (generated) | C (no map) | Verdict for C |
|---|---|---|---|---|
| (i) gh calls per 3z slice run, CTH | 13 | 10 | 9 for gate and reads, plus 3–4 `--edges` calls = **12–13**; **≤ 10** once 4a's three reconcile calls are merged into one (S1 combined mode, wired in S5) | pass only with the merge |
| (i) wall time per 3z slice run, CTH | 9.6 s | 9.8 s | 8.7 s for gate and reads, ≈ 10.5 s with the `--edges` calls; the merge brings it back below 9.6 s | pass only with the merge |
| read tokens per 3z slice run, CTH / StratOS | 47.4k / 19.3k | 34.1k / 16.8k | **0.9k / 0.3k** | −98% |
| (ii) map-diff checks, mirror writes, mirror heals | all | regenerate replaces writes | **all deleted** in GitHub mode; post-condition gate kept | pass (reworded ii) |
| (iii) net framework text, like for like (±30%) | 0 | ≈ −10.2k chars | ≈ **−10.8k chars** | pass, small |
| always-loaded text | — | ≈ −650 chars | ≈ −650 chars (789 removed, a short pointer added) | small |

**Why not B:**
- It saves about the same text as C.
- It must regenerate before every read, or it shows stale data right after the agent's own write.
- Its reads cost 38× more than C's in CleanTechHub.

**Why A is not a safe baseline:**
- CleanTechHub's hand-written map is wrong today, measured against GitHub:
  - **≈ 60 of 163 rows** (≈ 27 open issues) on the active branch `feat/BT-051-…`;
  - **83 of 160 rows** (49 open) on `origin/main`.

  Re-runs give ±3 rows, because another session keeps committing map syncs to CleanTechHub.
- CleanTechHub **commits `.memory/` to git**, so each branch carries its own stale copy of a 48 KB table, and status changes reach `main` only at merge. GitHub has no branch dimension, so C removes this failure mode.
- StratOS's map is correct on every open row, but StratOS is a small, well-tended backlog.
- CleanTechHub L-016 records a similar case: a copy of a source of truth (`DATABASE_SCHEMA.md`) went stale and broke ingestion for 5 days.

## Riskiest assumption: FAILED, and the spike was re-scoped at H1
The assumption was "removing the map removes the sync layer". The map-only share measured below the 80% bar on all three measures:
- `reconcile.py`: 71%;
- gate and heal prose: 70%;
- logged incidents: 56%.

The 18 incident root causes come from 15 in CleanTechHub's 7 nightly reports plus 3 from git history and plan docs. 5 were GitHub-side misses a map cannot catch, for example the 2026-09-15 dropped status step, stale `BT-215` edges and the PR-link ordering.

**Surviving post-condition gate (about 254 non-blank lines):**
- the blocker predicate;
- closed ≡ done;
- the PR-link check;
- 101 lines of gh/CLI plumbing.

## Write inventory (A2, `src/` only)
- **Sites:** 122 in total: reads 33, mirror writes 29, local-only writes 11, gate/heal 19, rules/definitions 30.
- **By disposition:** 109 removable, 7 need a GitHub equivalent, 6 offline-only.
- **Text:** 22,555 chars of BACKLOG-related sentences. Always-loaded: 789 chars, all in `memory-protocol.md`.
- **Outside `src/` and not in the 122:** the test harness (`tests/lifecycle-harness/shims/gh_shim.py`, `assertions.py`, `env.py`), `tests/workflows/test_reconcile.py` (929 lines) and the workflow crosschecks. They are owned by the slices below.

## Measured cost (A3; median of 3 runs)
- **Today's gate:** 1 `gh auth status` plus 3 `gh issue view` per id, so 13 calls and 9.6 s for 4 ids. One aliased GraphQL query does the same in **1 call, 0.62 s**.
- **Generator (B):** 2 GraphQL calls, 1.96 s on CleanTechHub (168 issues).
- **Scoped reads (C), CleanTechHub:**
  - load-memory WIP set: 151 tokens, 1.24 s;
  - 3c candidates with ICE: 1,492 tokens, 1.39 s;
  - single issue: 20–59 tokens.

  Compare a whole-map read: 11,842 tokens.
- **Where C costs more:** `--edges` takes 1 GraphQL call instead of 0. That is why 4a's steps 7–9 must become one invocation (S1 builds the combined mode, S5 wires it into 4a).

## Where ICE and Ref live
- **ICE: drop the column and compute on read** as Impact × Confidence / Effort, from the body metrics 3b already writes plus the `size:` label.
  - It is verified on CleanTechHub BT-241 and BT-243.
  - Bodies in older formats return null, which falls into 3c's existing "recalculate if empty" path.
- **Ref: move it to a `Refs:` line in the issue body (H3).** CleanTechHub uses Ref on 145 of 163 rows (`[[L-…]]`, `[[A-…]]`, `[[DR-…]]`). StratOS uses it on 0 rows.
  - 8 cells "Superseded by BT-n" and 3 other free-text cells are resolved by hand in the one-off dry run.
  - `validate_memory.py` keeps its Ref lint for the local backend only. In GitHub mode, Refs live on GitHub and are not linted offline.

## Tracker backend: selection, record, runtime (H3)
**The record.**
- **For scripts:** the frontmatter key `tracker: github | local` in `.memory/ARCHITECTURE.md`, registered in `okf-protocol.md`.
- **For agents:** a `[LAW]` entry under Structural Rules.
- *Why ARCHITECTURE:* it is a lasting structural fact. `STATUS.md`, where setup records it today, is a per-session hint.

**Resolution when the key is missing** (StratOS gitignores `.memory/`, so clones, worktrees and Jules runs have no key). A small helper resolves the backend deterministically, with no guessing from a transient failure:
1. The key is present → use it.
2. No key and a map exists → `local`. This covers every existing install, so nothing breaks on update.
3. No key and no map, with `gh` authenticated and a GitHub remote → `github`.
4. Otherwise → halt and point to setup's tracker step.

**Runtime rule.** With `github` resolved:
- A `gh` failure is retried 3 times with backoff, as heal does today, so AFK 3z survives transient errors. Then the run halts and says so.
- It **never** writes a local copy instead.
- `pr_body.py` epic detection fails closed in GitHub mode; today it fails open.

**Where the rule lives.** The rule text lives in `tracker-verbs.md`, which is loaded when writing, and is enforced by the scripts. Nothing is added to always-loaded text.

**Setup (`/stratosphere-setup` step 2).** Reword the `gh` question to state the consequence, with **Yes recommended**: "No GitHub connection: issues will be tracked in a local file (`BACKLOG_MAP.md`). Set up GitHub now?"
- **Yes:** `tracker: github`, and no map is created.
- **No:** create the local map, then `tracker: local`.

**`scaffold.py` follows the key.** In GitHub mode it does not place, recreate or lock `BACKLOG_MAP.md`. Without this, the next `/stratosphere-update` would bring the map back.

**Switching later (ongoing, local → GitHub only).** It is a **tested script**, `src/scripts/tracker_switch.py`, which setup's tracker step calls in one line:
- dry run first;
- create GitHub issues from the rows, mapping `BT-LOCAL-n` → `BT-<padded>`;
- rewrite those ids in `.memory/` and `docs/`, and report other hits rather than editing them;
- move ICE metrics and Refs into the bodies;
- archive the map;
- set `tracker: github`.

GitHub → local is not supported. `/stratosphere-update` gets no tracker logic.

**Rules that lived in the map.** The label composition rules, the status lifecycle order, the milestone scheme and the concept exemptions move to `src/references/label-taxonomy.md`, which the local map template then cites. Project-specific lines (area slugs, Project ID) move to ARCHITECTURE.

## Offline (local tracker backend)
- Workflows state each write once as a **tracker verb**, defined in `src/references/tracker-verbs.md` with a GitHub form and a local form.
- **Verbs:** create, set_status (it owns the single-status invariant), set_labels, set_milestone (plus ensure and close), set_parent, add_blocker, clear_blocker, close/reopen, comment, and reads.
- **Local-backend limits, documented rather than solved:**
  - the issue body stays in the existing draft and spec files;
  - claim is a no-op;
  - 0b closes local issues explicitly, since there is no close on merge;
  - ICE and Ref stay as cells.
- PR operations are not tracker verbs.
- **Provisional milestone:** 2a/2b stop writing `v1.0.0` into the map. In GitHub mode the epic has no milestone until 3a assigns one, which is already the GitHub behavior.
- **LEARNINGS TODO sink:** the LEARNINGS template's "TODO → BACKLOG" line points to the tracker instead.

## Deletion list (contract slice, GitHub mode)
- **`reconcile.py`:** the map-vs-GitHub field diffs in `compare`, `heal` and `upsert_cells`, `--summary` and nightly-age.
  - `parse_backlog` and the row-based paths **stay** for the local backend and `pr_body.py`.
  - So the deletion is most of the 377 map-only lines, not all of them.
- **Prose:**
  - about 80% of `terminal-sync-invariant.md`;
  - the mirror-write sentences across the workflows;
  - 0d's map-drift check;
  - `--heal` in 0b/0d;
  - the 789 always-loaded chars in `memory-protocol.md`, which become a pointer to `tracker-verbs.md`.
- **Added:**
  - about 1,060 chars of expected-state prose;
  - about 2,000 chars of scoped-query prose;
  - `tracker-verbs.md` (3,200);
  - `label-taxonomy.md` (moved text, about 1,000);
  - about 600 chars in setup.

  Net: about −10.8k chars (±30%), workflows about −8k.

## Slices: children of BT-190, ordered expand/contract
The order is **S1 → (S2 ∥ S3) → (S4 ∥ S5) → S6**. Slices are numbered S1–S6 so they don't collide with the workflow names 4a and 4b. Each slice owns the files listed, and a parallel pair never shares a file.

**Lead-only files:** implementers never touch `dist/`, `versions.json` or `tests/workflows/test_workflow_script_crosschecks.py`. A crosscheck that a slice's prose change breaks is updated by the lead at that slice's integration, in the slice's own commit.

| # | Slice: files owned | Acceptance criteria (summary) | Blocked by |
|---|---|---|---|
| S1 | **Gate on GitHub:** `src/scripts/reconcile.py`, `src/scripts/pr_body.py`, `src/rules/okf-protocol.md` (the `tracker:` key registry); `tests/workflows/test_reconcile.py`, `tests/scripts/test_pr_body.py`, `tests/lifecycle-harness/shims/gh_shim.py`, `tests/lifecycle/test_l3_gh_shim.py` | backend helper with the 4-step resolution; paginated batched GraphQL fetch; `--expect`/`--expect-file`; a **combined mode** for 4a steps 7–9 (gate + `--edges dependents` in one call, unit-tested); retry 3× then halt; `pr_body.py` fails closed in GitHub mode; gh shim supports the batched GraphQL, `--json parent,blockedBy`, issue create and body edit; the local path unchanged | — |
| S2 | **References and spec writers:** new `src/references/tracker-verbs.md` (incl. the halt rule) and `src/references/label-taxonomy.md` (label list, composition, status order, milestone scheme, concept exemptions and the `concept:map` row rule, plus the registry-vs-GitHub sync rule for local mode); `src/references/github-issue-relations.md`, `src/references/issue-templates.md`; `src/workflows/2a-write-prd.md`, `2b-interface-design.md`, `3b-create-issue.md` (Refs to the body, no provisional milestone in GitHub mode, verb statements, label-registry source); `src/scripts/validate_memory.py` (Ref lint local-only); `src/memory-templates/LEARNINGS.md`; `tests/framework/test_status_label_contract.py` and the validate_memory tests | the verbs doc lists every write kind with both forms and the misfits; 2a/2b/3b state each write once; no new always-loaded text | S1 |
| S3 | **Install:** `src/commands/stratosphere-setup/SKILL.md`, `src/commands/stratosphere-update/SKILL.md` (map mentions only, no tracker logic); `src/scripts/scaffold.py` (no placement, recreation or lock of the map in GitHub mode; `place()` and orphan-guard entries for the new script); `src/memory-templates/ARCHITECTURE.md` (key plus `[LAW]` placeholder); new `src/scripts/tracker_switch.py`; `tests/framework/test_update_flow.py`, `tests/runners/verify_scripts.py` | setup records the key; scaffold never recreates the map when `github`; the switch script passes a dry-run test and a live test against the gh shim; existing installs resolve to `local` and are unchanged | S1 |
| S4 | **Readers, stages 0–1 and planning:** `src/skills/load-memory/SKILL.md`, `src/workflows/0a-start-session.md`, `0b-stop-session.md`, `1b-concept-framing.md`, `1c-concept-map.md`, `3a-version-planning.md`, `3c-sprint-planning.md`, `4b-audit-architecture-drift.md`, `4c-codebase-health-audit.md`; `src/references/concept-map-operations.md`; `src/scripts/okf_view.py` | scoped queries replace whole-map reads in GitHub mode; 3c computes ICE on read; the 3a/3c/0b gates use `--expect` | S1, S2, S3 |
| S5 | **Readers, build and ship loop:** `src/workflows/3d-implement-issue.md`, `3z-afk-loop.md`, `4a-verify-and-ship.md`; `src/references/pr-body-and-ship.md`, `src/references/ci-gate.md`; `tests/lifecycle-harness/assertions.py`, `env.py`, `prompts/3b.txt`, `prompts/3d.txt`; `tests/lifecycle/test_l3_assertions.py`, `test_l3_seed.py` | row lookups become single-issue queries; 4a steps 7–9 use S1's combined mode; the harness runs a GitHub-mode scenario; **measured on CTH: ≤ 10 gh calls and ≤ 9.6 s per 3z slice run** | S1, S2, S3 |
| S6 | **Contract:** map-diff, heal and summary code in `src/scripts/reconcile.py`; `src/references/terminal-sync-invariant.md`; `src/rules/memory-protocol.md` (becomes a pointer); `src/workflows/0d-nightly-consolidation.md`; `src/memory-templates/BACKLOG_MAP.md` (local only, cites `label-taxonomy.md`); `src/memory-templates/STATUS.md`; `src/skills/plan-html/references/micro-app-patterns.md`; `KNOWN_BLOCK_IDS` and the corroboration check in `src/scripts/scaffold.py`; `tests/workflows/test_workflow_script_crosschecks.py` (final pass) | no mirror write, map diff or heal remains on the GitHub path (a grep test); the local backend still passes its tests | S4, S5 |

**Exempt:** `tests/fixtures/legacy/validate_memory.v4.0.0.py` is a frozen legacy fixture and is never edited.

**Release:** S6 changes behavior for GitHub-mode projects, so `release.py` should land a **MAJOR** bump (v5.0.0). BT-194 ships as its own unit from `main` after v4.10.0 (PR #215), so re-run `release.py` at ship and expect v5.0.0.

## Post-merge one-off: CleanTechHub switch (throwaway, not in `src/`)
Run after CleanTechHub installs the release (`/stratosphere-update`), on its own branch from an up-to-date `main`, so it does not run on the long-lived `feat/BT-051` branch. It uses a throwaway script under `.tmp/`:
1. **Back up:** save every target issue body to `.tmp/cth-bodies-backup.json`.
2. **Dry run:** list the planned body edits, the 8 "Superseded by" cells and the 3 free-text Ref cells for a manual call. **The user confirms before any GitHub write.**
3. **Move Refs:** append `Refs: …` to each body. This is idempotent: skip a body that already has a `Refs:` line.
4. **Check ICE:** list open slices without body metrics. Nothing is invented.
5. **Archive the map:** `git mv .memory/BACKLOG_MAP.md .memory/archive/`. Move project-specific registry lines to ARCHITECTURE, then write `tracker: github` and the `[LAW]` entry.
6. **Verify:** run `gen_map.py`, diff it against the archived map (only known drift may differ), then commit once. Merging that branch carries the key to every other branch at its next rebase.

## Follow-ups (candidates, outside this epic)
- **`validate_memory.py:84-98` autofix writes `[[ID]]` into the ICE column** (`parts[8]`) instead of Ref (`parts[9]`). This is a live bug in every consumer, including local mode. Fix it now, independently.
- **`0b:27` cites an undefined map-row "retention" rule.** It is moot in GitHub mode after S6; define it for the local backend or delete it.
- **Port CleanTechHub's label→Project sync Action.** Not needed by this decision.

## Review log
**Review 1** (independent Sonnet reviewer, 2026-10-20): **58/100**. Every finding was verified and addressed in this revision:
- `scaffold.py` recreating the map → S3 and S6;
- the test harness unowned → S1, S5 and S6;
- the false file-disjointness → reordered, with file lists;
- the map's Rules block → `label-taxonomy.md`;
- switch logic as prose → `tracker_switch.py`;
- halting on a missing key → the 4-step resolution;
- net text and criterion (i) overstated → restated, plus the merge AC;
- slice 4 too big → split into S4 and S5;
- AFK retry and `pr_body` fail-open → S1;
- the one-off missing a backup and idempotence → added;
- drift and incident fidelity → corrected.

**Review 2** (focused re-review, 2026-10-20): **82/100**. The remaining gaps were fixed in v1.2.0:
- unowned files → every `src/` and `tests/` file that references BACKLOG now has an owner (checked by a script);
- slice names renamed to S1–S6, away from the workflow names;
- the label list, sync rule and `concept:map` rule moved to `label-taxonomy.md`;
- the measured acceptance criterion moved to S5, which owns 4a;
- `tracker_switch.py` gets its scaffold and `verify_scripts` entries;
- the gh shim gets create and body-edit support;
- always-loaded text restated as ≈ −650.
