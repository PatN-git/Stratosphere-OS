---
name: load-memory
description: Read-only session-context reconstruction from the `.memory/` layer. Invoked inline by lifecycle workflows and /0a to restore context without re-reading the repo. Do not fire autonomously or on general requests; never mutates state.
metadata:
  stratos.layer: execution
version: "1.3.0"
timestamp: 2026-11-06
---

# SKILL: Load Memory

Reconstruct read-only session context from the memory layer. Side-effect-free: never writes branches, issue status, or memory — those belong to `/0a` (Activate) and `3d`.

## Procedure
0. Determine the active task — the issue ID the invoking workflow/prompt passed (its caller resolves it; `/0a` picks from the `status:in progress` set). `.memory/STATUS.md` is folder state only (sessions in this folder), never the task's state. If `.memory/` is absent or no active task → `Session Status: no-active-task`, RETURN.
1. Self-gate: if already loaded this session and the active task is unchanged → `Session Status: cached`, RETURN.
2. Read the active task source — the issue body (github `gh issue view <n>`; local `python .agents/scripts/issues.py get <id>`), the invoking prompt, PRD, or spec: objective, constraints, dependencies. If an issue ID is present, invoke `.agents/scripts/validate_memory.py --index --query-issue <id>` to deterministically extract cited memory handles (`[[L-xxx]]`, `[[A-xxx]]`, `[[DR-xxx]]`, `[[G-xxx]]`) into `.tmp/active-memory-refs.txt` in <5ms with 0 model turns. Then read its latest resume note (`resume_note`; branch, done, open, next step, blockers): github → `gh issue view <n> --json comments --jq '[.comments[] | select(.body | startswith("<!-- stratos:resume -->"))] | last | .body'` (PowerShell 5.1: escape the inner quotes as `\"`); local → `.memory/resume/<id>.md`; empty → no note yet.
3. Hydrate active memory from `.tmp/active-memory-refs.txt` (exact active rules, negative constraints (`Avoid:`, `Never`, `[LAW]`), and learnings cited by the task). If `.tmp/active-memory-refs.txt` is missing or carries no entries for a required memory category, fall back to reading active entries in `.memory/LEARNINGS.md` (Active only; skip `## Superseded`).
4. PRD / discovery / domain feature → read cited terms from `.tmp/active-memory-refs.txt` or fall back to `.memory/GLOSSARY.md` (Active only).
5. Structure / state / boundary / cross-feature task → read cited rules from `.tmp/active-memory-refs.txt` or fall back to `.memory/ARCHITECTURE.md`.
6. WIP conflicts, by backend (`tracker:` in the `.memory/ARCHITECTURE.md` frontmatter; absent → local when the `issues.py branch` branch exists, else github): github → `gh issue list --state open --label "status:in progress" --json number,title,labels`, never a whole-backlog read; local → `python .agents/scripts/issues.py wip`.
7. DB / schema / migration / RLS task → `.memory/DATABASE_SCHEMA.md`.
8. `.tsx` / UI / layout / styling task → `.memory/DESIGN.md` + `.memory/DESIGN_RULES.md`.
9. Read the code files relevant to the active task, if any — never the whole codebase.

## Output
`Session Status: synced` — Objective / Current state / Current branch / Next step (from the resume note) / Needs verification.
