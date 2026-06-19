---
name: 0a_start-session
description: Initializes session to avoid cold start by reviewing necessary project context from memory layer/protocol.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.2"
timestamp: 2026-06-18
---

# START SESSION

## Goal
Reconstruct minimum necessary context quickly without re-reading the whole repository. Surface crystallization opportunities before work begins.

## Procedure
1. Read `.memory/STATUS.md`. If STATUS shows no active task (e.g. post-bootstrap), output "No active task — next: /1a_research or /1b_concept-framing" and "Needs verification: none", then halt.
2. Read STATUS `Current Branch`. If it's an active/unmerged feature branch and the repo isn't on it → check it out; if merged/unset → checkout default and pull. (Note: Defer all branch CREATION to 3c, only restore existing branches here).
3. Read active task source (prompt, issue, PRD, spec) for objective, constraints, dependencies — unless invoked by 3b_create-issue.md.
4. Read `.memory/LEARNINGS.md` (Active Entries only — skip `## Superseded` unless the task explicitly requires history).
5. If the task involves a PRD, discovery brief, or domain-heavy feature — read `.memory/GLOSSARY.md` (Active Entries only).
6. Read `.memory/ARCHITECTURE.md` if the task affects structure, state flow, feature boundaries, or cross-feature behavior.
7. Read `.memory/BACKLOG_MAP.md` to ensure the current task doesn't conflict with other work-in-progress.
8. Only if the task touches DB queries, schema, migrations, or RLS — read `.memory/DATABASE_SCHEMA.md`.
9. Only if the task touches `.tsx`, layout, styling, or UI components — read `.memory/DESIGN.md` (brand tokens) AND `.memory/DESIGN_RULES.md` (structural rules).
10. Read only the most relevant code files next — not the whole codebase.

## Output Pattern
Context synced.
- Objective:
- Current state:
- Next step:
- Needs verification: