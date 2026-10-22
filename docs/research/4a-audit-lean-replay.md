---
type: research
title: "Research: lean audit packet and delta re-audit replay (BT-203)"
description: "Full-file versus lean-packet Spec audits and a delta round-2 audit replayed on four past StratOS slices: tokens saved, gaps found, run-to-run variance."
status: draft
slug: 4a-audit-lean-replay
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-20
version: "1.0.0"
---

# Research: lean audit packet and delta re-audit replay

Evidence for BT-203's second and third acceptance criteria. Method and caveats first, numbers second, verdict last.

## Method
- Four past slices from [4a-audit-yield.md](4a-audit-yield.md): BT-120, BT-139, BT-143 and BT-187, each checked out at its pre-fix commit in a temporary worktree (`da0b40a`, `e1ed8d6`, `f06853c`, `7091e37`). The Spec audit ran as an isolated read-only Sonnet 5.5 subagent in two regimes: **full** (the pre-BT-203 contract: issue, spec docs, implementation and test files in full, `LEARNINGS.md`) and **lean** (the BT-203 packet: issue ACs, the slice diff, test names; files only on demand, see [audit-inputs.md](../../src/references/audit-inputs.md)).
- Round 2 on BT-187: the fix commit `4237cd0` (round-1 fixes) checked out; a **delta** audit (previous coverage map, changed-file list, fix diff) against a **full lean** audit of the same state.
- Tokens are the `subagent_tokens` totals the harness reported per run (cache reads not itemized). One run per cell unless noted. Gap counts are findings with confidence >= 80.

## Caveats
- The "recorded gaps" are proxies: the scan JSON records counts, not texts, so recorded gaps were judged from the fix commits' messages. Three of the four slices produced no gap at >= 80 in any regime, so they cannot discriminate.
- The BT-187 pre-fix state still contains the pre-push `parity` replay that the issue's Overview later says was dropped; some runs treated that as a gap, some as a side note.
- Sonnet-class subagents only; a different model may differ. Small N.

## Results: tokens and gaps
| Slice | Full | Lean | Saving |
|---|---|---|---|
| BT-120 | 83.7k, 0 gaps | 73.0k, 0 gaps | 13% |
| BT-139 | 75.5k, 0 gaps | 71.3k, 0 gaps; repeat 69.1k, 0 gaps | 6% |
| BT-143 | 134.8k, 0 gaps | 79.0k, 0 gaps | 41% |
| BT-187 | 129.8k, 8 gaps; repeat 161.4k, 6 gaps | 108.0k, 7 gaps; with the whole issue body 114.3k, 5 gaps | 17% (24% against the full mean of 145.6k) |

The lean run on BT-187 opened 2 files; the full runs opened 12.

## Results: gaps on BT-187
- Five gaps were found in every regime and every run, all rated 88-92 by the full run: failing log fetch must stay red and big, a `gh` failure after the first read must be pending, unusable `gh` must be `cannot_run` (exit 2), exit 2 must halt `[CI-RED] could not check`, and an untouched-file failure must be big whatever the job is named.
- Three gaps sat at 80-85 and flipped between runs in **both** regimes: `base_stale` untested (found by full 1 and lean 1; withheld by full 2 and lean 2), the host-maximum-tool-timeout instruction (found by full 1, full 2 and lean 1, not lean 2), and "dropped `parity` still built" (found by full 1 only).
- Run-to-run variance exists in the full regime too (8 gaps against 6), so the lean runs' misses at the 80-85 edge are within what two full runs already disagree on. The single measured full-versus-lean miss is one gap (`parity`, 85) that only the first full run counted.

## Results: round 2 (BT-187 at `4237cd0`)
- Delta: 91.5k tokens, 4 gaps, 14 rows re-checked and 9 carried. Full lean: 113.7k tokens, 3 gaps. Saving 20%.
- The delta audit found the one extra gap (job-name classifier case) because it re-checked the earlier failing rows; the carried PASS rows hid nothing.

## Second replay: CleanTechHub (BT-061, BT-170, BT-186)
Same method on snapshots made with `git archive` (no git history for the auditor to read), three regimes: **full**, **lean** (packet plus the whole issue body, as the reference now says) and **lean+watch** (lean, plus a `Watch` list of every finding scored 60-79). One run per cell.

| Slice (recorded in the scan) | Full | Lean | Lean+watch |
|---|---|---|---|
| BT-061 (5 findings, max 90) | 119.3k, 1 gap, 10 files read | 77.0k, 1 gap, 3 files | 80.1k, 1 gap, 5 watch items |
| BT-170 (1 finding, 85) | 118.1k, 0 gaps, 15 files | 85.2k, 0 gaps, 4 files | 86.7k, 0 gaps, 4 watch items |
| BT-186 (2 findings, 95) | 125.3k, 0 gaps, 22 files | 98.6k, 0 gaps, 6 files | 97.2k, 0 gaps, 6 watch items |

Lean saved 35%, 28% and 21%; 28% over the three slices (362.7k full against 260.8k lean).

What the real fix commits show:
- **BT-061.** The fix commits added tests for two classes: deep-link parsing, popstate and pending-detail resolution, and the offline/fetch-failure fallback, the landing state and the single-region redirect. All three regimes reported the first class at 82-85. The second class was seen at 70-75 in the full and lean runs ("near-miss, withheld") and never reported. Gaps present in the output below the threshold are the most actionable finding of this replay.
- **BT-170.** The scan recorded one gap at 85. No regime found it. The fix commit made the drift-guard CI step run when unit tests fail (`if: always()`), which the audits scored as covered because the step exists (PASS 85-88 on the "red build on the same push" criterion). Full and lean are equal here: a reasoning miss, not an input miss.
- **BT-186.** The scan recorded two findings at 95; no regime reported one. The `Watch` lists named untested `React.memo` wrapping, an inline `onClick` that defeats memoization in `DirView`, and a queued badge hard-coding palette classes. The one fix commit on record is mostly frozen default arguments in two hooks, so a match between a watch item and a recorded finding could not be shown.

Reading across both replays: lean and full find the same stable gaps and miss the same ones, so the bigger quality question is not lean against full. On the seven slices with a recorded spec gap, the auditor found all of the highest-rated gaps on BT-187, one of two classes on BT-061 and none on BT-170 and BT-186, in every regime.

## Verdict against BT-203's criteria
1. Lean re-finds every recorded gap and uses fewer tokens: **tokens yes** (lower in all five pairs, 6-41%); **gaps partly**: every gap rated 88 or higher was found in all runs, but a strict reading ("a missed gap fails") is not met because the lean runs missed one or two 80-85 gaps that a single full run found, a spread the full regime shows against itself. Unresolved by this data: whether lean loses signal at the confidence-80 edge; 3 of 4 slices give no signal at all.
2. Round-2 delta re-checks only failed rows and touched carried rows and uses fewer tokens than a full round: **met** (20% fewer, no gap lost).

## Follow-up worth considering
Repeat the full audit more than once per slice on a slice with several known gaps before treating any 80-85 confidence difference as a regression; the default of a single audit run per slice already has this variance.
