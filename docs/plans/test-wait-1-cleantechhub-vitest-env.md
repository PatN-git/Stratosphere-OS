# Plan 1 — CleanTechHub: stop paying jsdom startup for non-DOM tests

Executor: an Antigravity agent working in `C:\Users\patri\Dev\CleanTechHub` (PowerShell, Windows). Self-contained: no other plan needed.
Status: v2, 2026-10-15, revised after an Opus (high) review. Plans 2 and 3 cover StratOS and are independent of this one.

## Goal
Same pass count, lower cumulative `environment` time and lower best-of-3 `Duration` for `npm test`, by making `node` the default vitest environment and keeping jsdom only for files that need it.

## Evidence, and how much to trust it
- 49 files already carry `// @vitest-environment jsdom` (31 use `//`, 18 a docblock; vitest accepts either). Exactly 3 files need it added: `TaxonomyPill`, `MultiDrop`, `BT182` (imports leaflet). Confirmed by the review.
- Cumulative `environment` time: 226s (jsdom default) vs 97s (`--environment node`), a 57% cut. Confirmed.
- Wall time is **not** settled. Two measurements disagree: 204s vs 47s (first review) and 64s vs 53s (second review, run while the machine was ~69% busy). Wall time depends heavily on machine load, so the gain is somewhere between ~17% and ~75%. Do not promise a number: Step 1 measures best-of-3 on a quiet machine and Step 6 compares like with like.
- `pool: 'forks'` was slower than `threads`. Do not change `pool`.
- Separate existing risk, not fixed by this plan: under load, 3 ingestion tests that `await import(...)` a heavy script time out at 15s (`BT164_GeminiLiveBenchmark`, `BT164_StuttgartShootoutIngest`, `BT235_IngestionOfflineFallback`). That is load noise, not an environment problem.

## Scope
Change: `vite.config.js` (`test.environment`), the 3 DOM test files (one pragma line each), and — after the user says yes — one `.memory/LEARNINGS.md` entry.
Do not touch: `pool`, `isolate`, `setupFiles`, test logic, any other file.

## Preconditions
- Close other heavy processes (other agents, builds) before measuring; note in the report if you could not.
- `git status` clean. This is a direct user request, so `/3d` is not required to create the branch. Run:
  `git switch main; git pull; git switch -c chore/BT-<n>-vitest-node-env` (ask the user for `<n>`; do not invent one). Scratch output only in `.tmp/`.

## Steps
1. **Baseline.** Run `npx vitest run` three times. For each, record `Test Files`, `Tests`, `Duration` (wall and `environment`). Baseline = the best `Duration`. Expected 110 files / 1229 tests; if counts differ, use the observed counts.
2. **Find the DOM files.** Run `npx vitest run --environment node`. A failure qualifies a file for the pragma **only** if the error is `window is not defined` or `document is not defined`. A `Test timed out` failure is load noise: rerun that file alone with `npx vitest run <file> --environment node`. Any other failure: stop and report, never paper over it. Expected: exactly the 3 files above.
3. **Flip the default.** In `vite.config.js` set `test.environment` to `'node'`.
4. **Add the pragma** as the first line of each of the 3 files: `// @vitest-environment jsdom`.
5. **Check the setup file.** `vitest.setup.js` guards `window` with `typeof window !== 'undefined'`; leave it. If it now imports anything needing a DOM at the top level, stop and report (it does not today).
6. **Verify.** Run `npx vitest run` three times. Every run: baseline test count, all passing. Best `Duration` is below the baseline best, and cumulative `environment` time is at least 50% lower. If wall time is not lower, report it; the environment-time cut still stands.
7. **Learning entry (proposal only).** The memory protocol requires proposing a `.memory/` write and waiting for a yes. Propose this entry to the user: `- **[[L-018]] [ASSUMED] [<today>]** Vitest's default environment is `node`. A test that renders React, touches `window`/`document`, or imports leaflet needs `// @vitest-environment jsdom` on its first line, or it fails with `document is not defined` / `window is not defined`. Source: BT-<n>.` On a yes, insert it after L-017 and run `python .agents/scripts/validate_memory.py` (expect exit 0).
8. **Commit** with explicit paths: `vite.config.js`, the 3 test files, and `.memory/LEARNINGS.md` if step 7 was accepted. Message: `chore(BT-<n>): default vitest environment to node, jsdom per file`. Do not push; the user ships via `/4a-verify-and-ship`.

## Done when
- Three runs, each with the baseline test count all passing; best `Duration` lower than baseline best; `environment` time at least 50% lower.
- `git diff --stat main...HEAD` shows only files listed in Scope.
- Report the before/after best-of-3 numbers in two lines.

## Rollback
`git revert <sha>`.

## Risks
- A future DOM test added without the pragma fails loudly, not silently. Verified: no test without the pragma imports a module that branches on `typeof window` (except MultiDrop, which gets the pragma), so no test silently changes which code path it exercises.
