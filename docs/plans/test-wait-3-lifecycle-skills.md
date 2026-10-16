---
type: plan
title: Test Wait Plan 3 - Lifecycle Skills
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-15
version: "1.0.0"
---

# Plan 3 — Lifecycle skills: fewer accidental full runs, honest suite reuse, no token bloat

Status: v2, 2026-10-15, revised after an Opus (high) review. Tracked as BT-183 under epic BT-181. Edit `src/` (workflows, scripts, references), rebuild; needs its own BT issue and branch, one version bump per PR. Changes reach consumer projects (CleanTechHub) only via a release plus `/stratosphere-update`.

## Goal
At most one full suite run per slice in `/3d`; `/4a` and `/0b` reuse it when nothing relevant changed; a scoped run is never reported as "the suite". Always-loaded text does not grow.

## What the skills already say (checked)
- `/0a`: Zero Test/Build Invariant (`0a-start-session.md:18`). No change.
- `/3d` Phase 2.3 (`3d-implement-issue.md:53`): related tests through `test_gate.py record -- <cmd>` before each incremental commit. Phase 3 step 6: the one full run.
- `micro-tdd` (`SKILL.md:50`): related-tests mode, else touched test files.
- `/4a` step 5 and `/0b` step 9 (`0b-stop-session.md:45`): reuse via `pr_body.py suite`, else run.
- `tests/workflows/test_test_cadence.py` pins the single-full-run text.
The wording is mostly right. The leaks are mechanical.

## Findings
1. **Hook message.** `test_gate.py check()` says only "Run the tests, then commit again: `record -- <test command>`"; agents read that as the full suite. (Whether the observed repeated full runs came from this was not verified; transcripts show 5 full `record -- python -m pytest -q` runs in ~60 min in one session.) The hook is opt-in: CleanTechHub has no `.git/hooks/pre-commit`, so this fix does not reach it.
2. **Release bump trips the hook (verify first).** A `release: prepare` commit stages `build/build.py` and `*.json` (see 4d6ee07); these are gated and not in the record, so the hook blocks and the agent likely re-runs the full suite inside `/4a`. Check transcripts before building the fix.
3. **Scoped records pass as "the suite".** Agents hand-write `.tmp/3d-suite-BT-<n>.json`; 3 of 6 CleanTechHub records (BT-200, 233, 235) are scoped runs. StratOS: 0 of 19.
4. **`/0b` re-runs after sessions that changed no code.** On the default branch after a merge HEAD has moved, `suite` finds no record, and `0b:45` says "else run the suite".

## Changes (deterministic code first; prose only where it replaces prose)
1. **Hook message (zero standing tokens).** In `test_gate.py check()` name the cheap path: run the related tests (not the full suite); the full run is `/3d` Phase 3. Prints only on a block.
2. **Recorder.** `python .agents/scripts/test_gate.py record --suite BT-<n> -- <cmd>`: tees the command's output; on exit 0 **and a clean tree after the run** writes `.tmp/3d-suite-BT-<n>.json` `{head_sha, cmd, observed}` and updates the gate record. `observed` = strip ANSI, take the last line matching `\d+ (passed|failed)`, else the last non-blank line (vitest's last line is `Duration`). Chained commands need `bash -c`; say so in the script's usage. Then `3d` step 6 and `pr-body-and-ship.md:36` shrink: replace the hand-written JSON instruction with the command.
3. **Scope derived from `cmd`, not declared.** A declared `scope: full` gates nothing (the agent that hand-wrote BT-233/235 would pass a scoped command just as easily). In `pr_body.py suite` and in `check_suite()` (so `build --suite-json` cannot bypass it), after stripping a `test_gate.py record --` prefix, a record is **scoped** if any argument is: an existing directory, a test-named file, contains `::`, or one of `related`, `--findRelatedTests`, `-k`, `-t`, `--testNamePattern`, `--testPathPattern`, `--lf`. Scoped records are not reusable. This catches BT-200/233/235 and the current `.tmp/test-gate.json`, keeps `bash scripts/check.sh` and `npm test` as full, and leaves all 19 StratOS legacy records reusable. Print `[NO-SUITE] <scoped|head moved|dirty tree|none>` to **stderr**; stdout stays empty (`test_pr_body.py:380` asserts that).
4. **Release-bump gate fix (only if finding 2 is confirmed).** Zero-token options: `scripts/release.py -y` refreshes the gate record for the files it wrote, or `/4a` commits the bump via `record -- python build/validate.py .`.
5. **`/0b` line (about +70 chars, loaded only on `/0b`).** In `0b-stop-session.md:45` replace "else run the suite" with: "else, only if this session changed code, run it via `test_gate.py record --suite`; otherwise report `suite: not run (no code change)`."
6. **No other prose.** Nothing for `/0a`, `micro-tdd` or the rules; the invariants exist and are test-guarded.

## Dropped after review
- **Reuse by tree diff over DRIFT_OK.** Unsafe: `DRIFT_OK = (".memory/", "docs/", ".tmp/")` (`pr_body.py:40`) contains paths tests read (`docs/status-label-contract.md` in StratOS; `docs/database/schema.sql`, `.memory/DESIGN.md`, `.memory/DATABASE_SCHEMA.md` in CleanTechHub). It could reuse a green suite for a schema change. A merge commit brings code, so a re-run there is correct. Note the existing uncommitted-edit tolerance in `tree_is_clean` (`pr_body.py:135-145`) has the same hole; track it separately.
- `scope: full` field and legacy-record rejection; the project fast/full-command declaration (revisit only if transcripts still show full runs after steps 1–5).

## Budget (corrected)
`test_constitution_stays_within_its_char_budget` bounds only `AGENTS.md` (src 8712 / installed 8911 vs a 9200 cap), which this plan does not touch. Workflows and references are not budgeted but should still shrink: estimated −41 chars in 3d step 6 and −18 in `pr-body-and-ship.md:36`, +~70 in `0b`. Show the before/after in the PR.

## Tests
- `tests/scripts/test_test_gate.py`: block message names related tests; `record --suite` writes `{head_sha, cmd, observed}` only on exit 0 and a clean tree; ANSI/`Duration` parsing; failing command records nothing.
- `tests/scripts/test_pr_body.py:335-441` (where reuse behaviour lives; `test_0b_suite_reuse.py` only checks text): scoped records rejected; legacy full records still reused; reason on stderr, stdout empty; `build --suite-json` rejects scoped. `write_suite` at `:47` writes no scope, so keep it valid.
- Update text pins in `tests/workflows/test_test_cadence.py:27,36-38` and `test_0b_suite_reuse.py`.

## Rollout
One PR, build, `bash scripts/check.sh`, one version bump; release, then `/stratosphere-update` in CleanTechHub (its `pr_body.py` copy is one revision behind). A week later re-scan transcripts: at most one full run per `/3d` session, no scoped records reused.

## Done when
Hook message test passes; a scoped record is rejected by `suite` and a `--suite` full run is accepted; all existing records still behave; `/0b` after a no-code session reports "not run"; char deltas shown.

## Non-goals
No new skill or always-loaded rule, no test-impact tooling, no change to `/3z` orchestration, no retroactive fix of existing scoped records.
