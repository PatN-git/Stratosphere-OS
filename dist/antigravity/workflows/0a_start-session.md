---
name: 0a_start-session
type: workflow
description: Initializes session to avoid cold start by reviewing necessary project context from memory layer/protocol.
---

# START SESSION

## Goal
Reconstruct minimum necessary context quickly without re-reading the whole repository. Surface crystallization opportunities before work begins.

## Procedure
1. Read `.memory/STATUS.md`. Note any "Suggested Next Persona" — the user may invoke it directly after `/0a_start-session`.
2. Read active task source (prompt, issue, PRD, spec) for objective, constraints, dependencies — unless invoked by `SKILL_create-issue.md`.
3. Read `.memory/LEARNINGS.md` (Active Entries only — skip `## Superseded` unless the task explicitly requires history).
4. If the task involves a PRD, discovery brief, or domain-heavy feature — read `.memory/GLOSSARY.md` (Active Entries only).
5. Read `.memory/ARCHITECTURE.md` if the task affects structure, state flow, feature boundaries, or cross-feature behavior.
6. Read `.memory/BACKLOG_MAP.md` to ensure the current task doesn't conflict with other work-in-progress.
7. Only if the task touches DB queries, schema, migrations, or RLS — read `.memory/DATABASE_SCHEMA.md`.
8. Only if the task touches `.tsx`, layout, styling, or UI components — read `.memory/DESIGN.md` (brand tokens) AND `.memory/DESIGN_RULES.md` (structural rules).
9. Read only the most relevant code files next — not the whole codebase.

## Output Pattern
Context synced.
- Objective:
- Current state:
- Next step:
- Suggested persona (from STATUS.md, if any):
- Needs verification: