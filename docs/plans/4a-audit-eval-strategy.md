---
type: plan
title: 4a Audit Improvement Test Strategy
description: "How to test four ideas for catching more of what the 4a Spec auditor misses (watch rows, AC-literal lint, effort split, a labeled corpus) before any of them changes the production gate."
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-20
version: "1.1.0"
---

# Plan: how to test the ideas for the 4a auditors

Follow-up to epic BT-201 ([plan](4a-audit-yield-plan.md), [replay evidence](../research/4a-audit-lean-replay.md)). **The Spec and Standards auditors stay as they are.** This plan only says how each new idea is tested offline; production behavior changes only when an idea clears its pass rule. Nothing here is implemented. Edit `src/` for anything shipped, never `.agents/` or `dist/`.

## What the replays say (the reason for each test)
- Lean and full find the same stable gaps and miss the same ones. On the seven slices with a recorded spec gap: BT-187 all of the highest-rated gaps (88-92), BT-061 one of two classes, BT-170 and BT-186 none, in every regime. The weak spot is the auditor's recall, not the packet.
- Many misses were **seen and suppressed**: BT-061's second class of real gaps (offline fallback, fetch failure, redirect, landing) scored 70-75 and was withheld; `base_stale` scored 65; "dropped feature still built" was a side note.
- Some gaps were **never seen**: BT-170's CI step that must run when tests fail was scored covered (85-88) in all three regimes.
- Gaps at confidence 80-85 flip between identical runs, so any test needs repeats.
- Cost per Spec audit (Sonnet-class subagent tokens): lean 69-115k, full 75-161k.

## Shared test method
- **Cases:** a snapshot of the slice before its fix (`git archive`, so the auditor cannot read the fix), the issue body, spec docs, a lean packet, and **labels**: the gap, the AC row it breaks, 1-3 key terms, the class (missing test, text absent, unhandled error path, unpinned case, scope drift, wiring omission, reasoning miss), taken from the real fix commit. Eight cases already have snapshots and packets (StratOS BT-120, 139, 143, 187; CleanTech BT-061, 170, 186, plus BT-187's post-fix state).
- **Matching is mechanical:** the auditor's table has one row per AC, so a FAIL (or watch) row on the labeled AC that contains a key term counts as found. No LLM judge.
- **Arms and repeats:** every idea is a pair of arms on the same snapshots (paired by case). Gaps at 80-85 flip run to run, so each arm runs k=3 where a model is involved; report per-gap detection probability, not one yes/no.
- **Controls:** at least 3 clean slices (audited, no gap, no rework) so precision is measured, not assumed.
- **Hold-out:** tune an idea on two thirds of the cases, judge it on the rest.
- **Rules are written before the run** (below). A failed idea is recorded, not tuned until it passes.

## Test 1: watch rows (findings scored 60-79 listed, not blocking)
- **Hypothesis:** gaps the auditor already sees at 60-79 include real ones, and a short list the lead can check with one grep recovers a useful share at an acceptable noise cost.
- **Arms:** A = lean as shipped. B = lean plus the instruction to list 60-79 findings as `Watch`. Same snapshots, same model.
- **Measure:** *suppression recovery* = labeled gaps missed in A that appear in B's watch list; *watch precision* = watch items matching a label / watch items; *noise per audit* = watch items per slice; *triage cost* = tokens for a second, cheap pass that checks each watch item against the code (the lead's grep, simulated by a small-tier subagent) and what fraction of true items it confirms.
- **Pass rule:** recovers at least a third of the labeled gaps that A missed, watch precision at least 25%, no more than 6 watch items per slice, triage under 10% of the audit's tokens.
- **Evidence so far (one run each):** CleanTech lean+watch produced 5, 4 and 6 items; BT-061's second gap class was visible at 70-75 in the no-watch runs; no watch item could be matched to a recorded finding on BT-170 or BT-186 (the recorded texts are not in the data). The test needs labels first.
- **Cost:** B reuses the lean packet: about 90k tokens per run; 8 cases x k=3 is about 2.2M, triage about 0.2M.

## Test 2: AC-literal lint (deterministic)
- **Hypothesis:** literals an AC names in backticks that appear in none of the changed files signal a "text absent" gap for free.
- **Arms:** the script (extract backticked literals from `### Acceptance Criteria`, report those absent from the changed files) against the labels. No model.
- **Measure:** recall on labeled "text absent" gaps; false flags per slice. Tighten first: skip shell commands, match path-like literals against paths, skip fragments from mismatched backticks.
- **Pass rule:** at least 30% recall on the text-absent class and at most 2 false flags per slice; otherwise drop the idea, since the cost of keeping it is a packet row nobody trusts.
- **Evidence so far (untightened prototype):** BT-187 flagged 7 literals, one of them a real gap (`[CI-RED] could not check`); BT-061's ACs have no backticked literals; BT-170 none absent; BT-186 six flagged, none real. Likely drop unless tightening and more labels change that.
- **Cost:** free; runs as a unit test over the corpus.

## Test 3: effort split (Spec auditor high effort, Standards auditor small tier with low effort)
- **Hypothesis:** a higher reasoning effort on the Spec auditor raises detection of flaky gaps and may find reasoning misses like BT-170's, and low effort on the Standards auditor loses no hard breaches.
- **Arms:** Spec auditor at default, high and max effort (Claude Code `effort`, Codex `model_reasoning_effort`; Antigravity only its model tier); Standards auditor default against small tier plus low effort. Same lean packet, same cases.
- **Cases:** the ones with labeled flaky or missed gaps: BT-187 (three flaky), BT-061 (fallback class), BT-170 (`if: always()`), BT-186; for Standards, seeded smells (a mutation adds a known smell to a clean slice) plus clean controls.
- **Measure:** per-gap detection probability and recall@80 by arm; tokens and wall time by arm; for Standards, hard-breach recall and false-positive rate.
- **Pass rule:** Spec: flaky-gap detection up by at least 0.2, or recall up by 5 points, at no more than 1.5x the tokens. Standards: no hard breach lost, false positives not up by more than 3 points, tokens lower.
- **Cost:** the largest: 4 flaky/missed cases x 3 effort levels x k=3 at roughly 100-250k per run is about 1.2-2.7M tokens; the Standards arms are small. Owner approves the spend first; start with BT-187 and BT-061 only.

## Test 4: a labeled corpus with real recall numbers
- **Why:** every other test is only as good as its labels, and the replays so far had three slices with no recorded gap in any run.
- **Work:** label the eight existing cases from their fix commits (BT-187 has seven written down), add the remaining known blockers (StratOS BT-118, 119, 122, 162-168 and CleanTech BT-094) and 3 clean controls, then add **seeded defects**: one scripted mutation to a clean slice per case (delete the test covering an AC, remove a literal an AC names, drop an error branch, weaken a parametrized case, leave behind a feature the issue says is not built, delete a workflow step), which gives labeled gaps in any number.
- **Output:** a baseline recall@80, precision and flip rate for the shipped lean setup, the number every test above is compared with.
- **Cost:** labeling is reading work; baseline run on about 16 cases x k=3 at about 90k is roughly 4.3M tokens, so run a 6-case subset first.

## Order
1. Test 4's labeling for the eight cases that already have snapshots (no model cost).
2. Test 2 (free) and a packet-completeness unit test: every changed path has hunks or an explicit "no diff" line, and the whole issue body is present (the BT-143 lean packet listed four changed files with no hunks).
3. Test 1 on the labeled cases.
4. Test 3, starting with BT-187 and BT-061.
5. Only after an idea ships: compare production numbers (BT-202's `audit:` line already records counts, `std_tier` and `input`; add a `cfg` stamp for the idea in use) and, if wanted, shadow-audit one slice in ten off the ship path.

## Slices to mint (via `/3b-create-issue`, none minted yet)
1. Corpus: snapshot builder, labels for eight cases, then seeded-defect scripts.
2. Test runner: arms x cases x repeats, the matching rule and the pass rules above, dev-only (`src/dev-skills/` or `scripts/dev/`), not shipped to consumers.
3. Packet-completeness test and the AC-literal lint experiment.
4. Watch-row experiment.
5. Effort-split experiment.

## Not doing
Changing the 80 threshold, the auditors' prompts or the production gate before an idea passes its rule; an LLM judge for matching; running these tests on every PR; a second audit on the ship path.
