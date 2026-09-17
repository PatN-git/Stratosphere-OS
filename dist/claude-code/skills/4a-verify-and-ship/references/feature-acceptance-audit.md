---
description: Feature-level acceptance audit run once per feature at 4a Phase 5 Step 7, immediately before `gh pr ready`. Closes the gap where N slice-scoped audits never ask whether the assembled feature satisfies the parent PRD.
version: "1.0.0"
timestamp: 2026-09-17
---

# Feature Acceptance Audit

Slice audits resolve their inputs per slice: slice diff, slice AC. A PRD cut into N slices therefore passes N slice-scoped audits and zero feature-scoped ones, and the Epic Check flips the PR ready on a **label count**. Cross-slice integration AC, and PRD AC no single slice claimed, are unreachable that way.

Regression is already covered — the repo-wide suite runs on the full feature branch at every ship. This gate covers **conformance**.

## When
`4a` Phase 5 Step 7 only, once the Epic Check is already true, before `gh pr ready`. Once per feature, never per slice — an `audit-only` run never reaches it.

## Run
One **Strict Business-Logic Auditor** subagent under the Phase 2 guardrail: audit and format the table only; no edits, commits, or pushes.

- **Input:** the parent PRD (`docs/prds/BT-<parentPadded>-<name>.md`) full AC set, the interface design doc, and the whole-feature diff — base ref `git merge-base HEAD origin/<default>`. The parent resolves changed paths and passes them explicitly; the subagent never runs repo-wide discovery.
- **Scope:** cross-slice integration AC, and PRD AC unclaimed by any single slice. Do not re-litigate AC already mapped PASS in a shipped slice's table.
- **Output:** the Phase 3 §1 AC↔test table, gaps ≥ 80 confidence.

## Verdict
- **Clean** → continue Step 7.
- **Gaps** → halt. Leave the PR in draft, leave the epic at `status:in progress`, surface the table, and route to `/3b-create-issue` (new slice) or `/3d-implement-issue` (extend).

Never flip `gh pr ready` over an open feature-level gap, and never re-run the audit to clear one.
