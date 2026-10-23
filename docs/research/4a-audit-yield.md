---
type: research
title: "Research: 4a audit yield (Spec and Standards auditors) in StratOS and CleanTechHub"
description: "How often the two 4a auditors found issues, in which slice scenarios, and what that implies for audit frequency and cost; corrected after an independent challenge."
status: draft
slug: 4a-audit-yield
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-20
version: "1.0.0"
---

# Research: 4a audit yield

**Question:** can the two 4a auditors (Spec = Strict Business-Logic Auditor, Standards) run less often (risk-gated, or per epic/PR instead of per slice) without losing quality?
**Answer:** not provable yet. Diff-shape gating saves little. The cheaper wins are cutting cost per audit and removing Standards findings nobody reads in AFK runs. Overall confidence: low.

## Method
One extraction script per repo (gh issues/PRs, `git log`, agent session logs) following [4a-audit-scan-prompt.md](4a-audit-scan-prompt.md). Three evidence tiers: A = PR-body `stratos-pr` row (`verdict`, `audit_rounds`); B = git (rework and post-ship commits, epic-audit gaps); C = session-log markers (counts regex-parsed, not hand-graded). Baseline data: [StratOS](4a-audit-yield-data/4a-audit-scan-Stratosphere-OS.json) (53 slices) and [CleanTechHub](4a-audit-yield-data/4a-audit-scan-CleanTechHub.json) (106 slices; Antigravity logs). Schema: one record per slice, 28 fields, `null` = unknown. Scans were run by a Sonnet 5.5 subagent (StratOS) and an Antigravity session (CleanTechHub), reviewed by the lead and challenged by an Opus 5.5 subagent.

## Findings (as corrected by the challenge)
1. **Spec yield is not comparable across repos.** StratOS: 7 of 16 per-slice audit pairs raised a gap of confidence >= 80 on round 1, plus 6 of 7 slices in the BT-162..168 batch/plan audits (PR #161): 13 slices, base 24 truly audited (the JSON's 27 includes BT-188/191/192, graded outside 4a). CleanTechHub reports 3 of 78 (3.8%), probably an undercount: only 13 of 408 transcripts hold a parseable verdict, BT-094's 3z `[UNCOVERED]` return is recorded as 0 findings, and its scan scripts were not kept. "Gap raised" is not "defect fixed" (BT-119 and BT-143 had gaps but passed round 1).
2. **Standards findings have no consumer in AFK.** 3z `audit-only` returns verdict, coverage map, `docs_read`, `needs_manual_qa` and retries only on spec gaps, so Standards output is dropped (60 of 78 audited CleanTech slices were AFK). CleanTech's 335 hard breaches (86% of audited slices) plausibly come from one mechanical rule (A-008: each source directory's `index.md` lists its files), which a lint can check. The CleanTech report's claim that Standards drove 48 of 52 multi-round slices is a parse artifact (PR bodies show a second round on 1 of 17 machine-readable slices, not 7). StratOS HITL runs do use findings: 14 of 15 slices show a follow-up fix (proxy).
3. **Diff-shape gating saves little.** `type:feature OR files>=6` misses no recorded spec blocker in either repo (verified) but skips only about 9-11% of audits (CT 71/78 kept, SO 24/27), since nearly all slices touch 6+ files. Phase 1's keyword triggers are worse: StratOS missed 7 of 13 blockers; CleanTechHub tags 86 of 106 slices. Rules were fitted post hoc on 3 and 13 positives: hypotheses, not findings.
4. **Epic-only audits are unsupported.** Feature Acceptance Audit: N=2-3, run after slice fixes (StratOS 3 runs, 0 gaps; CleanTechHub 2 gaps, dead code and a contract widening). PR #161 is weak evidence for batching: some gaps trace to plan items, not a cumulative code diff.
5. **Cost sits in re-reading and re-auditing.** StratOS median about 493k tokens (+1.78M cache-read) per audit pair; BT-187 spent 1.94M over 3 full rounds; BT-185 on the 3z lean inline path (diff + ACs + named tests) cost 65k, 7.6x below median. CleanTechHub tokens unmeasured (Antigravity logs omit them).
6. **Post-ship defects are runtime/live-data issues** (enum FK, live markup) an AC-to-test auditor cannot see (CleanTechHub: 29/78 audited vs 4/28 bypassed, confounded). The control is integration tests, not more audits.
7. **Root gap:** 4a never persists findings (PR body keeps `verdict` and `audit_rounds`, since PR #145). Every number above is reconstructed from chat logs.

## Known blockers for the replay (spec gap >= 80)
StratOS: BT-118, 119, 120, 122, 139, 143, 162, 163, 165, 166, 167, 168, 187 (BT-162..168 were batch audits). CleanTechHub: BT-061, BT-170, BT-186 (+ BT-094 `[UNCOVERED]` in transcript). Clean controls: pick 4 audited slices with no gap and no rework.

## Decisions
- Standards (revised 2026-10-22): consume the findings in HITL and AFK; Hard breaches are fixed automatically in one bounded round when the fix is behavior-preserving (micro-tdd Direct or Visual route); Judgment findings are never auto-fixed. Replaces "hard and medium issues are fixed automatically within the retry cap" (AFK only).
- One framework-wide audit policy now; a per-repo override only if instrumented data shows a material difference at the decision checkpoint.
- A cheaper model tier for the Standards auditor, mapped per host.
- A one-off blind replay on cheap subagents instead of a shadow PR-level audit (which would add ship-path time and see only residual misses).

Plan: [4a-audit-yield-plan.md](../plans/4a-audit-yield-plan.md).

## BT-205: CleanTechHub Standards hard breaches (2026-10-22)
**Method.** Read the Standards Auditor subagent reports from two stores: Antigravity (`~/.gemini/antigravity/conversations/*.db`, the `send_message` payloads; 38 reports, 36 slices) and Claude Code subagent logs (`~/.claude/projects/*CleanTech*`, BT-168 to BT-176; 11 reports, 8 slices). Together 44 slices, 40 of them among the scan's 78 audited slices (51%): v1.x 0 of 2, v2.x 2 of 7, v3.x 19 of 26, v4.0-4.5 13 of 23, v4.6+ 6 of 20 (BT-003, 101, 168 and 240 are outside the scan's audited set). Each `Hard breach` row was classed by one test: **mechanical** = a script or standard linter decides it without reading intent; **semi** = lintable with an added rule set (jsx-a11y) but the choice needs a read; **judgment** = needs intent, is a defect, or is a baseline smell.

**Round check.** The Standards auditor normally runs once per slice (one report in 40 of 44 slices; two only for BT-168, 169, 173, 187). The scan's `audit_rounds` counts Spec re-audits. So each table is the audit a fix round would have seen, not a residue after fixes. Fix commits that match the rows exist for only 9 of the 22 Antigravity slices with hard rows; the rest shipped with them unfixed, as 3z discards the list.

**Finding 1: the scan's 335 is overstated.** On the 33 slices present in both sources the scan reports 192 hard breaches, the transcripts 48. Spot checks: BT-154 scan 10, transcript "0 hard breaches"; BT-191 scan 12, transcript 0; BT-185 scan 18, transcript 1 (A-003, fixed, re-audit PASS); BT-159 scan 14, transcript 1. Read the real rate as about 1.6 per audited slice, with 14 of those 33 slices at 0.

**Finding 2: share of 70 hard rows** (a row is one file and rule; empty rows dropped).

| Class | Rows | Share | Rule IDs |
|---|---:|---:|---|
| Mechanical | 27 | 39% | A-003 file over 400 lines (6), A-008 `index.md` manifest (6), unused import or dead code (6), DR-002/023/005 raw colour, border opacity, arbitrary Tailwind value (4), missing import (2), React array-index key (1), `.env.example` parity (1), commit-message convention (1) |
| Semi-mechanical | 3 | 4% | `span`/`div` with `onClick`, focusable card (a11y rules) |
| Judgment | 40 | 57% | 21 baseline smells labelled Hard (Duplicated Code, Mysterious Name, Middle Man, Data Clumps, Speculative Generality, Repeated Switches, Divergent Change, style); 19 real defects or judgment on a documented rule (unawaited or unhandled promises 4, schema or routing mismatch and false-positive tests 6, prototype-key collision 2, input validation 1, A-009 snapshot pins 2, A-011 1, other 3) |

All shares are for this sample (70 rows, 28 slices with at least one hard row); any extension to the 78 audited slices is an extrapolation. Of the 38 unobserved audited slices, 14 are v4.6+ (the newest) and 7 are v2.x or older, so the newest audits are the least covered.

**Finding 3: where the rules live.** A-003, A-008, A-009, A-011, DR-002/005/023 are CleanTechHub's own `[LAW]` rows in its `.memory/`; none is in `src/references/code-smell-baseline.md`. A-008 is 6 of 70 rows (9%), not "most". A-008 also fails at commit level (BT-170: the index must change in the same commit as the file), which a final-state test cannot see.

**Finding 4: the severity label is unreliable.** 21 of 70 hard rows (30%) are baseline heuristic smells, which the baseline defines as judgment calls. About 19 rows (27%) are real defects or documented-rule judgment, including runtime bugs the Spec audit did not catch.

**Follow-ups.**
An independent Opus 5.5 review (2026-10-22) split the follow-ups differently: the checks stay project-local, the governance becomes a framework feature. Design in the plan, "Rule bindings (R)".
1. **R, rule bindings (StratOS, epic BT-212):** a `[LAW]` entry may name its check (`Check: <path>`), exceptions reuse `## Floor exceptions` with rule IDs, and the Standards auditor skips bound rules, honours exception rows and uses the corrected label (`Hard breach` only for a cited rule ID or an objective defect; baseline smells always `Judgment`). Checked on 8 replayed slices before the auditor wording ships.
2. **L, CleanTechHub-local checks** (vitest tests run by `npm test`, a minimal ESLint because unused or undefined imports are 8 of the 27 mechanical rows, markers, human-merged exception rows), minted in CleanTechHub's own backlog after R is released and vendored.
3. **BT-207, the auto-fix round, becomes conditional:** after R and L, replay this sample and count Hard rows a Direct or Visual fix can still reach; under 0.2 per audited slice, drop it.

## BT-214 E2: Standards auditor wording (2026-10-22)
**Test.** The drafted "4a Standards auditor: severity and skips" block (Hard only for a cited rule ID or an objective defect; every baseline smell is Judgment; skip rules on `info: bound` lines; drop findings on `info: exception` lines) was run on 8 replayed CleanTechHub slices, one isolated subagent each on the `small` tier (`model: haiku`), with the diff, changed-file line counts, CleanTechHub's `[LAW]` rule lines and the seeded `info:` lines inline. Expected labels and the pass rule were written before any run (`.tmp/e2-labels.json`: no baseline smell labelled Hard; both defect slices keep a Hard row on the named defect; no finding on a seeded rule; fail on any of these in 2 of 8 runs or a lost real defect). BT-185 was swapped for BT-114 before running (BT-185's head file is 397 lines, so A-003 was not visible). Diffs are rebuilt from the slice's build commits, not the original audit's exact range.

| Slice | Class | Result |
|---|---|---|
| BT-173, 172, 189, 193 | baseline smells | Pass: every Mysterious Name, Duplicated Code, Middle Man, Data Clumps, Divergent Change row came back `Judgment`; Hard rows were A-003 or objective defects |
| BT-114 | bound A-003 | Pass: no A-003 finding on `adapters.js` (617 lines); the auditor listed it under Dismissed as bound |
| BT-159 | excepted A-008 | Pass but weak: no A-008 finding, yet the manifest breach may not have been visible in the rebuilt range |
| BT-187 | real defect | **Fail**: the missing `fetchAndExtractHtml` import and the unawaited async calls were not reported |
| BT-222 | real defect | **Fail**: the prototype-key collision (`'toString'`) TypeError was not reported |

**Control.** The old wording, same packets, same tier, on the two defect slices: BT-187 and BT-222 lost the same defects. So the loss is not caused by the new wording: a small-tier audit of a 70k-character diff does not find these cross-file or runtime-key defects either way. The old wording also labelled most smells `Judgment` on BT-187, so this test does not show that the new label wording improves on it (the old-wording baseline was not run on the four smell slices).

**Outcome by the rule fixed in advance: not passed** (a real defect lost in 2 of 2 defect slices). Read against the control: no regression attributable to the wording, no measured gain either.

**Second control (label wording).** The old wording on the four smell slices (BT-173, 172, 189, 193), same packets and tier: 0 baseline smells labelled Hard in 4 of 4 runs, the same as the new wording (0 of 4). On this tier and these inputs the strengthened label sentences show no measured gain; the old intro already makes the small-tier auditor label smells `Judgment`. The BT-205 mislabels came from audits run before BT-204's `small` tier and on other hosts and models, so they cannot be reproduced here.

**Decision (2026-10-22).** BT-214 ships the skip and drop mechanism only (rules on `info: bound` lines are skipped, findings matching `info: exception` lines are dropped; supported by BT-114 and, weakly, BT-159). The severity-label sentences are not shipped: no measured gain, and the handoff rule says no auditor prompt change without an experiment that passes. The label question moves to production data (the `audit:` line records `std_hard` counts per slice); revisit it at BT-208. The "defect stays Hard" criterion is recorded as not passed and unattributable to the wording (the old wording lost the same two defects).
