---
type: research
title: "Research: first results of the 4a audit test plan"
description: "Recall of the shipped lean Spec audit on 43 labeled gaps from 13 real slices, plus the first verdicts on watch rows, the AC-literal lint and small-model triage."
status: draft
slug: 4a-audit-eval-results
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-20
version: "1.0.0"
---

# Research: first results of the 4a audit test plan

Runs of [the plan](../plans/4a-audit-eval-strategy.md) on the [corpus](4a-audit-eval/README.md). Earlier replays: [lean replay](4a-audit-lean-replay.md).

## Setup
- 13 real slices (7 StratOS, 6 CleanTechHub), 43 labeled spec gaps taken from the audit-fix commits; 4 clean controls. Snapshots are `git archive` of the state before the fixes.
- One arm, **lean+watch**: the shipped lean packet (whole issue body included) with an instruction to list every finding at confidence 60 or above. Findings at 80+ are the blocking set; 60-79 are watch items. One run on all 17 cases and a second on 5 (BT-187, BT-061, BT-198, BT-169, BT-118). Sonnet-class subagents, about 96k tokens per run.
- Matching is mechanical: a finding matches a label when at least `min_terms` of its key terms appear in the finding.
- Spend for this phase: about 4.8M subagent tokens (labelers 0.9M, 22 audit runs 2.2M, triage 1.7M).

## Test 4 baseline: what the shipped auditor finds
| Measure | Value |
|---|---|
| Labels found at 80+ in every run | 10 of 43 (23%) |
| Found in some runs only (flaky) | 4 |
| Never at 80+ | 29 |
| Seen at 60+ in at least one run | 30 of 43 (70%) |
| Never seen even at 60 | 13 of 43 (30%) |
| High-confidence labels only (19, first run) | 42% found at 80+, 79% seen at 60+ |
| Clean controls: findings at 80+ | 0 on 4 of 4 |
| Detection by class (found at 80+) | unhandled error path 0.50 (n=9), reasoning miss 0.40 (5), missing test 0.27 (11), wiring omission 0.17 (6), text absent 0.14 (7), unpinned case 0.10 (5) |

By case: BT-198 and BT-006 found every label; BT-187 four of ten stably; BT-061 two of five with the rest flaky; nine cases (BT-118, 119, 120, 122, 139, 143, 169, 170, 171) found none at 80+. The earlier replays said lean and full miss the same gaps; this confirms the gap is the auditor's recall, not the packet.

## Yardstick check (2026-10-21)
I read the 6 low-confidence labels against their ACs and fix commits, and skimmed the 18 medium ones. Three low labels are not spec gaps by the AC (BT-118 g3 stale pointer in a sync-skills doc, BT-139 g5 a skip-clause wording fix, BT-143 g1 BOM handling beyond the AC) and the other three are thin (BT-169 g4, BT-171 g1, BT-143 g2: deep reasoning about data or an output kind). The medium labels are mostly real test-coverage gaps; a few are robustness cases outside the AC (BT-120 g2, BT-122 g2, BT-169 g3, BT-119 g3).

Recall by label confidence (mean detection at 80+ over all runs; share seen at 60+ in some run):
| Labels used | n | Found at 80+ | Seen at 60+ |
|---|---|---|---|
| all | 43 | 0.28 | 0.70 |
| medium and high | 37 | 0.32 | 0.73 |
| high only | 19 | 0.45 | 0.84 |

So the headline 23% is pessimistic by about a factor of two on the solid labels: the auditor finds about 45% of high-confidence gaps at the blocking threshold and sees 84% in some form. The classes stay in the same order (text absent and unpinned case weakest). Use the high and medium sets as the yardstick from here on.

## Test 5: evidence rule prompt (arm P), first run (2026-10-21)
**Change tested:** the lean+watch prompt plus one paragraph: "do not accept a test as proof because of its name; for every AC and each sub-requirement it names, find the exact assertion or text that would fail if the behavior regressed; partial, existence-only, wrong-input or missing assertion is a gap (80+ when the AC states it, 60-79 when inferred); grep the snapshot for required literals." Same packet, same model, same cases. One run per case; 9 real cases with labels plus 2 clean controls (BT-142, BT-185); medium and high labels only (n=33). Result files are `results/<case>__P__1.json`.

| Measure | Baseline B | Arm P |
|---|---|---|
| Labels found at 80+ | 6 of 33 (18%) | 15 of 33 (45%) |
| Labels seen at 60+ | 21 of 33 | 23 of 33 |
| Findings at 80+ not matching a label (labeled cases) | 1 | 2 |
| Watch items not matching a label (labeled cases) | 10 | 21 |
| Controls: findings at 80+ / watch items | 0 / 4 | 0 / 5 |
| Subagent tokens, 11 runs | 1.08M | 1.10M (+2%) |

By class (found at 80+, n in brackets): missing test 1 to 6 [9], reasoning miss 1 to 3 [3], text absent 1 to 2 [6], unhandled error path 3 to 4 [7]; unpinned case 0 [4] and wiring omission 0 [4] did not move. Examples that crossed the threshold: BT-120 default target never exercised (64 to 82), BT-061 fallback and landing paths, BT-187 `base_stale` and the host-maximum-timeout line, BT-118 missing-reference test. Two labels went from watch to missed (BT-118 g2, BT-122 g1), so one run is noisy; it needs repeats.

**Verdict, provisional:** meets the plan's rule for a quality raise (recall up well over 5 points at about 1.0x tokens), and no new false flags at 80 on the controls. Caveats: one run per case; the paragraph was written after the earlier replays, which showed these same weak-assertion misses, so these 11 cases are not a clean hold-out; watch noise roughly doubled (about 2 per slice more), which supports showing watch items as a short list, not acting on them. Next: repeat on the biggest-gain cases, then a held-out set (new slices or seeded defects).

## Test 1: watch rows
- Of the 33 labels missed at 80+ in the first run, 17 (52%) appear in the watch band. Pass rule (recover at least a third): met.
- Watch items per slice: 2.7 on average (maximum 9, BT-198); 46% match a label (33% on high-confidence labels; unmatched is not necessarily false, since labels cover only fixed gaps). Pass rule (precision at least 25%, no more than 6 per slice on average): met.
- Controls: 2.5 watch items per run, none at 80+.
- **Triage by a second agent fails.** A small-model verifier checked every 60-79 item against the snapshot: it confirmed 30 of 39 on real cases (77%) and 9 of 10 on controls (90%), because "no test proves X" is literally true of almost any slice, so it cannot tell a real gap from noise. It promoted 11 of the 17 watch-only labels and lost 6 (refuted or unclear). Cost was about 106k tokens per case, about one more audit, against a rule of under 10%.
- Reading: watch rows have value as a **list for the human who already reads the report at the ship halt** (about three lines, no extra tokens), not as an input to an automated second look. Not tested: whether a human acts on them.

## Test 2: AC-literal lint
Tightened (skips commands, prose fragments, path and file names): it caught 6 of 43 labels on a generous reading, 2 of the 7 text-absent ones, and only one of those is real (`[CI-RED] could not check`, BT-187). It raised 24 flags, 19 not tied to any label (1.5 per case). Pass rule (30% of the text-absent class, at most 2 false flags per case) not met. **Drop.**

## Not yet run
Test 3 (effort split). The baseline gives the numbers it must beat: 23% found at 80+, 30% never seen at 60. Measured cost per Spec audit is 75-131k tokens, so five cases x two repeats at high effort, assuming 1.5-2.5x per run, is about 1.5-2.5M tokens.

## Limits
- Labels come from fix commits via a labeler subagent: gaps the fixes did not address are missing, and 6 labels are low confidence. Many labels are test-pin tightening, which depresses "found" for an auditor that reasonably passes a covered AC.
- Single runs (two on five cases); Sonnet only; key-term matching can miss a correct finding worded differently.
- The triage verifiers were given a relative path some could not resolve, which turned a few verdicts into weaker checks.
