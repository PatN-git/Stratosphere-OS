---
name: 0a_start-session
description: Initialize session and load context from memory layer.
type: workflow HITL
trigger: manual
version: "1.0.7"
timestamp: 2026-07-17
---

# START SESSION

## Goal
Reconstruct necessary context without reading full repository. Surface crystallization opportunities before starting.

## Procedure
1. Read `.memory/STATUS.md`. If no active task, output "No active task — next: /1a_research or /1b_concept-framing" and "Needs verification: none", then halt.
2. Read STATUS `Current Branch`. If active/unmerged feature branch and repo not on it → check it out; if merged/unset → checkout default and pull. (Note: Defer branch creation to 3c; only restore existing branches).
3. Read active task source (prompt, issue, PRD, spec) for objective, constraints, dependencies (unless from 3b_create-issue.md).
   - **State Transition:** Set target issue (`BT-XXX`) to `status:in progress` in `.memory/BACKLOG_MAP.md` and GitHub (`gh issue edit <n> --remove-label "status:planned" --remove-label "status:needs_spec" --remove-label "status:blocked" --add-label "status:in progress"`). If sub-issue, also set parent epic (`BT-<parent>`) to `status:in progress` (removing prior statuses). Update `Active issue` in `.memory/STATUS.md`.
4. Read `.memory/LEARNINGS.md` (Active only — skip ## Superseded).
5. If task involves PRD, discovery brief, or domain feature — read `.memory/GLOSSARY.md` (Active only).
6. Read `.memory/ARCHITECTURE.md` if task affects structure, state flow, boundaries, or cross-feature behavior.
7. Read `.memory/BACKLOG_MAP.md` to check conflicts with work-in-progress.
8. Only if task touches DB queries, schema, migrations, or RLS — read `.memory/DATABASE_SCHEMA.md`.
9. Only if task touches `.tsx`, UI, layout, or styling — read `.memory/DESIGN.md` (brand tokens) and `.memory/DESIGN_RULES.md` (structural rules).
10. Read only relevant code files — not whole codebase.

## Output Pattern
Context synced.
- Objective:
- Current state:
- Next step:
- Needs verification: