---
name: load-memory
description: Read-only session-context reconstruction from the `.memory/` layer. Invoked inline by lifecycle workflows and /0a to restore context without re-reading the repo. Do not fire autonomously or on general requests; never mutates state.
metadata:
  stratos.layer: execution
version: "1.2.0"
timestamp: 2026-10-22
---

# SKILL: Load Memory

Reconstruct read-only session context from the memory layer. Side-effect-free: never writes branches, issue status, or memory — those belong to `/0a` (Activate) and `3d`.

## Procedure
0. Determine the active task — the issue ID the invoking workflow/prompt passed (its caller resolves it; `/0a` picks from the `status:in progress` set). `.memory/STATUS.md` is folder state only (sessions in this folder), never the task's state. If `.memory/` is absent or no active task → `Session Status: no-active-task`, RETURN.
1. Self-gate: if already loaded this session and the active task is unchanged → `Session Status: cached`, RETURN.
2. Read the active task source — GitHub issue body (`gh issue view <n>`), the invoking prompt, PRD, or spec: objective, constraints, dependencies. Then its latest resume note (`resume_note`; branch, done, open, next step, blockers): github → `gh issue view <n> --json comments --jq '[.comments[] | select(.body | startswith("<!-- stratos:resume -->"))] | last | .body'` (PowerShell 5.1: escape the inner quotes as `\"`); local → `.memory/resume/<id>.md`; empty → no note yet.
3. Read `.memory/LEARNINGS.md` (Active only; skip `## Superseded`).
4. PRD / discovery / domain feature → `.memory/GLOSSARY.md` (Active only).
5. Structure / state / boundary / cross-feature task → `.memory/ARCHITECTURE.md`.
6. WIP conflicts, by backend (`tracker:` in the `.memory/ARCHITECTURE.md` frontmatter; absent → local if `.memory/BACKLOG_MAP.md` exists, else github): github → `gh issue list --state open --label "status:in progress" --json number,title,labels`, never a whole-backlog read; local → read `.memory/BACKLOG_MAP.md`.
7. DB / schema / migration / RLS task → `.memory/DATABASE_SCHEMA.md`.
8. `.tsx` / UI / layout / styling task → `.memory/DESIGN.md` + `.memory/DESIGN_RULES.md`.
9. Read the code files relevant to the active task, if any — never the whole codebase.

## Output
`Session Status: synced` — Objective / Current state / Current branch / Next step (from the resume note) / Needs verification.
