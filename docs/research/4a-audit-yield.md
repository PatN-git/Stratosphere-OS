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
- AFK Standards: consume the findings; hard and medium issues are fixed automatically within the retry cap.
- One framework-wide audit policy now; a per-repo override only if instrumented data shows a material difference at the decision checkpoint.
- A cheaper model tier for the Standards auditor, mapped per host.
- A one-off blind replay on cheap subagents instead of a shadow PR-level audit (which would add ship-path time and see only residual misses).

Plan: [4a-audit-yield-plan.md](../plans/4a-audit-yield-plan.md).
