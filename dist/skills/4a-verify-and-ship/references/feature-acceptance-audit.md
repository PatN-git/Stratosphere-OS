---
description: Feature-level acceptance audit run once per epic, when it completes, at 4a Phase 5 Step 8, immediately before `gh pr ready`. Closes the gap where N slice-scoped audits never ask whether the assembled feature satisfies the parent PRD.
version: "1.1.2"
timestamp: 2026-11-03
---

# Feature Acceptance Audit

Slice audits resolve their inputs per slice: slice diff, slice AC. A PRD cut into N slices therefore passes N slice-scoped audits and zero feature-scoped ones, and the Epic Check flips the PR ready on a **label count**. Cross-slice integration AC, and PRD criteria no single slice claimed, are unreachable that way.

Regression is already covered — the repo-wide suite runs on the full feature branch at every ship. This gate covers **conformance**.

## When
`4a` Phase 5 Step 8 only, once the Epic Check is already true, before `gh pr ready`. Once per epic when it becomes complete (several may complete in one release PR), never per slice — an `audit-only` run never reaches it.

## Run
One **Strict Business-Logic Auditor** subagent under the Phase 2 guardrail: audit and format the table only; no edits, commits, or pushes.

- **Input:** the parent PRD (`docs/prds/<parentId>*.md`; `<parentId>` = the slice's Parent as `get` returns it) §8 Definition of Done, §5 Success Signals and the `[BASELINE]`/`[DIFFERENTIATOR]` §6 stories, the interface design doc, and the whole-feature diff — base ref `git merge-base HEAD origin/<default>`. The parent resolves changed paths and passes them explicitly; the subagent never runs repo-wide discovery. Hand the auditor this file and `.agents/skills/4a-verify-and-ship/references/confidence-scale.md` with the inputs: 60-79 is Watch, and an item the PRD does not settle is at most 79.
- **Audit epic** (per `references/audit-to-slices.md` §10 — parent body line 1 `Source: docs/audits/<stem>.md`, no PRD; replaces Input and Scope): input is the epic body's Coverage table and every child slice body (`Resolves:` lines, inline evidence, ACs), plus the whole-feature diff. Never read the report file. Scope: every finding resolved by a child slice no longer reproduces in the diff.
- **Scope:** every PRD §8/§5/§6 item. Probe (run code) only cross-slice integration AC and items no slice AC claims; an item a slice AC already maps to a named passing test is PASS on that test, no re-probe.
- **Output:** the Phase 3 §1 table, one row per item (Status PASS | FAIL | UNVERIFIED), gaps ≥ 80 only as FAIL; then `Watch` (60-79, one line each, user decisions, never halt the ship) and a footnote count of withheld 40-59 findings.

## Verdict
The word **Clean** (no FAIL row ≥ 80) or **Gaps**, in prose: no bracket token.
- **Clean** → continue Step 8 (`gh pr ready`); Watch lines go in the ship output.
- **Gaps** → halt. Leave the PR in draft, leave the epic at `status:in progress`, surface the table, and route to `/3b-create-issue` (new slice) or `/3d-implement-issue` (extend).

Never flip `gh pr ready` over an open feature-level gap, and never re-run the audit to clear one.
