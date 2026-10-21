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
