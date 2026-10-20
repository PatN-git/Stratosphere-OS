---
type: reference
title: "4a audit-yield scan prompt"
description: "Host-neutral, read-only prompt that extracts per-slice 4a auditor yield from GitHub, git and agent logs; rerun at the audit-policy checkpoint."
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-20
version: "1.0.0"
---

# TASK: 4a audit-yield scan (READ-ONLY research, no repo changes)

Goal: measure how often the two 4a auditors find real issues, and under which slice conditions, to decide whether audits can run less often (per epic / risk-gated) instead of on every slice.
The two auditors (4a Phase 2): **Spec** (Strict Business-Logic Auditor, AC<->test gaps >= 80 confidence, ship-blocking) and **Standards** (code smells, advisory, plus `Dismissed`).
Related third audit: epic-level **Feature Acceptance Audit** (4a Phase 5 step 8) - use it as the "what did slice audits miss" signal.

## Rules
- Read-only on the repo: no commits, no branches, no pushes, no PR/issue edits, no skill/rule changes.
- Put the extraction script and all outputs in `.tmp/` (gitignored). Write the script with the file-write tool; never inline multi-line code in a shell command.
- Token-efficient: extract with ONE deterministic script (gh/git/jsonl parsing). Do not read transcripts or PR bodies into context beyond a small sample used to validate the parser.
- No fabrication: every number comes from data; unknowns are `null`/"not recorded", listed under Data Gaps.
- Repo = the current working repo. Set `REPO=<name>` from the folder name.

## Step 1 - Slice inventory (GitHub + git)
For every closed or in-review slice issue (labels `status:done|in review`, any parent) plus its PR:
- `gh issue list --state all --json number,title,labels,body,parent,milestone,closedAt` (fall back to `gh api` if `parent` is unavailable) and `gh pr list --state all --json number,title,body,commits,mergedAt`.
- PR bodies carry a slice block: `{id: BT-n, parent, summary, verdict: PASS|WAIVED|SKIP|DROPPED|PENDING, audit_rounds: n}`. Parse it (see `src/references/pr-body-and-ship.md` or `.agents/skills/4a-verify-and-ship/references/pr-body-and-ship.md`). Older PRs may use another format - detect, don't assume.
- Record the 4a version in force per slice: `git log --follow` on the 4a workflow/skill file (`src/workflows/4a-verify-and-ship.md` or `.agents/skills/4a-verify-and-ship/SKILL.md`) vs the slice's ship date. Behavior changed over time (Phase 1 bypass rules), so bucket by version era.

## Step 2 - Per-slice features (the "scenarios")
For each slice: `size` label, `mode` label (HITL/AFK), `type` label, number of AC bullets in `### Acceptance Criteria`, files changed and +/- LOC (`git log --grep "BT-<n>" --numstat`), test files touched (y/n), spec completeness (`full` = parent PRD in `docs/prds/` AND design doc `docs/design/BT-<parent>-interface.md` exist; `prd-only`; `standalone`), parent epic and slice count, position in epic (first/middle/last), part of a 3z AFK run (y/n), Phase 1 trigger that applied (security/RLS/auth/billing/core-math/PRD-8-DoD/size:large/AFK vs cosmetic bypass vs plain bypass), number of 3d `## Deviations` if recorded.

## Step 3 - Audit outcomes (three evidence tiers; label each datum with its tier)
- **Tier A (structured):** PR-body `verdict` and `audit_rounds`. `audit_rounds > 1` = audit found something that forced rework. Was the audit run at all (PASS vs SKIP/WAIVED)?
- **Tier B (git):** commits after the slice's last 3d commit and before ship that look like audit fallout (`fix(BT-n)`, `test(BT-n)`, `ci` fixes); post-ship `fix` commits referencing the slice or its epic; Feature Acceptance Audit gaps per epic (search PR comments, issue comments, `.memory/LEARNINGS.md`, `docs/` for the epic-audit result) and which slice's AC they trace to.
- **Tier C (transcripts, best effort):** search agent session logs for 4a runs. Claude Code: `%USERPROFILE%\.claude\projects\<project-slug>\*.jsonl` (also `…\Packages\Claude_*\LocalCache\Roaming\Claude` if virtualized). Antigravity: discover under `~/.gemini/` (e.g. `antigravity/brain`, conversations); if no logs are reachable, say so and skip Tier C. Match markers: `[PASS] Slice verified`, `Spec / Business-Logic (Ship-Blocking)`, `Standards / Code Smells`, `[UNCOVERED]`, `Hard breach`, `Judgment`, `Dismissed`, `sub-threshold findings were withheld`. Per run extract: slice id, per-auditor finding count, confidence values, hard vs judgment, whether findings were fixed (matching commit) or waived. If `usage`/token fields exist in the logs, sum tokens per audit run; otherwise mark cost "unmeasured".

## Step 4 - Analysis (answer each with the number and N)
1. Overall yield per auditor: slices audited, slices with >= 1 finding, rate. Spec findings >= 80 confidence vs withheld sub-threshold. Standards: hard breach vs judgment, share actually fixed vs ignored, `Dismissed` noise ratio.
2. Yield by scenario: size, mode, type, AC count bucket, LOC/files bucket, spec completeness, position in epic, Phase 1 trigger, 4a version era. Show a table per dimension; flag cells with N < 5 as anecdotal.
3. Interaction: do full specs (PRD + design + AC) lower Spec-auditor yield? Do small / cosmetic / first-slice cases ever yield?
4. Epic counterfactual: for each epic, which findings would a single epic-level audit on the cumulative diff still have caught, and which were only cheap to fix because found at slice level (rework size: commits/LOC to fix)? How many audit runs would epic-level auditing eliminate (runs_now vs runs_epic_only)?
5. Misses: findings caught by the epic Feature Acceptance Audit or post-ship fixes that the slice audits passed (false negatives), and slices where the Phase 1 bypass skipped the audit and a defect later surfaced.
6. Predictor: find the smallest rule over observable fields (e.g. `size:large OR touches auth/RLS/math OR AC>=N OR spec!=full`) that would have kept every real blocker while skipping the most audits. Report audits saved, blockers missed (must be listed by id).

## Step 5 - Deliverables (write to `.tmp/`)
- `4a-audit-scan-<REPO>.json` - one record per slice with fields: `repo, slice, parent, size, mode, type, ac_count, files, loc, spec_completeness, epic_position, afk_run, phase1_trigger, version_era, audit_ran, verdict, audit_rounds, spec_findings, spec_max_conf, standards_hard, standards_judgment, standards_fixed, dismissed, rework_commits, epic_audit_gap, post_ship_fix, tokens, tiers` (use `null` for unknown). Keep this schema exactly so two repos can be merged later.
- `4a-audit-scan-<REPO>.md` - report: method (one paragraph), headline numbers, the tables from Step 4, Data Gaps (what is not recorded and would need to be logged going forward, e.g. persist auditor findings in the PR body), and a recommendation chosen from: (a) keep per-slice, (b) risk-gated per-slice with the rule from Step 4.6, (c) epic-level only, (d) hybrid. State confidence (low/med/high) given N and tier mix. Max ~2 pages.
- Do not apply any change to 4a. End by printing the two file paths and the 5 most decision-relevant numbers.
