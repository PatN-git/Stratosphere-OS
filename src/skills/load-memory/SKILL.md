---
name: load-memory
type: skill
description: Read-only session-context reconstruction from the `.memory/` layer. Invoked inline by lifecycle workflows (Phase 0) and /0a to restore context without re-reading the repo. Do not fire autonomously or on general requests; never mutates state.
version: "1.0.0"
timestamp: 2026-07-17
---

# SKILL: Load Memory

## Purpose
Reconstruct read-only session context from the memory layer without reading the whole
repo. Mechanical, side-effect-free. Invoked inline by lifecycle workflows (Phase 0) and
`/0a`. NEVER mutates state.

## Invocation modes
- **default:** memory context + relevant code (steps 1-9).
- **`memory-only`:** skip step 9 (code reads). Used by `4a` and `1a`/`1b`/`1c`.

## Procedure
0. **Always** read `.memory/STATUS.md` (cheap). Determine `Active issue`.
   - If `.memory/` or `STATUS.md` is absent (unscaffolded project) OR no active task → output `HYDRATE_STATUS: no-active-task`, "Needs verification: none", RETURN. (Graceful degrade: the skill may fire in a project that was never scaffolded — never error on a missing memory layer.)
1. **Self-gate:** if already hydrated this session AND `Active issue` unchanged → `HYDRATE_STATUS: cached`, RETURN.
2. Read active task source (prompt/issue/PRD/spec): objective, constraints, deps.
3. Read `.memory/LEARNINGS.md` (Active only; skip `## Superseded`).
4. If PRD/discovery/domain feature → `.memory/GLOSSARY.md` (Active only).
5. If task affects structure/state/boundaries/cross-feature → `.memory/ARCHITECTURE.md`.
6. Read `.memory/BACKLOG_MAP.md` (WIP conflicts).
7. If DB/schema/migrations/RLS → `.memory/DATABASE_SCHEMA.md`.
8. If `.tsx`/UI/layout/styling → `.memory/DESIGN.md` + `.memory/DESIGN_RULES.md`.
9. (default only) Read only relevant code files for the active task — never the whole codebase. Skip in `memory-only`.

## NON-GOALS
- No branch checkout/pull. No `gh` label/status changes. No memory writes. Those side effects belong to `/0a` (Activate) and `3d` (Phase 0).

## Output
`HYDRATE_STATUS: synced` — Objective / Current state / Current branch / Next step / Needs verification.
