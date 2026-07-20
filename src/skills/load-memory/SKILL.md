---
name: load-memory
type: skill
description: Read-only session-context reconstruction from the `.memory/` layer. Invoked inline by lifecycle workflows and /0a to restore context without re-reading the repo. Do not fire autonomously or on general requests; never mutates state.
version: "1.1.0"
timestamp: 2026-07-17
---

# SKILL: Load Memory

Reconstruct read-only session context from the memory layer. Side-effect-free: never writes branches, issue status, or memory — those belong to `/0a` (Activate) and `3d`.

## Procedure
0. Read `.memory/STATUS.md`; determine the active task (`Active Issue`, or the issue ID the invoking workflow passed). If `.memory/` is absent or there is no active task → `Session Status: no-active-task`, RETURN.
1. Self-gate: if already loaded this session and the active task is unchanged → `Session Status: cached`, RETURN.
2. Read the active task source — GitHub issue body (`gh issue view <n>`), the invoking prompt, PRD, or spec: objective, constraints, dependencies.
3. Read `.memory/LEARNINGS.md` (Active only; skip `## Superseded`).
4. PRD / discovery / domain feature → `.memory/GLOSSARY.md` (Active only).
5. Structure / state / boundary / cross-feature task → `.memory/ARCHITECTURE.md`.
6. Read `.memory/BACKLOG_MAP.md` (WIP conflicts).
7. DB / schema / migration / RLS task → `.memory/DATABASE_SCHEMA.md`.
8. `.tsx` / UI / layout / styling task → `.memory/DESIGN.md` + `.memory/DESIGN_RULES.md`.
9. Read the code files relevant to the active task, if any — never the whole codebase.

## Output
`Session Status: synced` — Objective / Current state / Current branch / Next step / Needs verification.
