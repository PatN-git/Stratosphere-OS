---
description: Instantiate a lightweight, durable project-memory and session-continuity system so AI sessions don’t cold-start.
---

# Instantiate Memory

Instantiate the minimum durable context an AI agent needs to resume work on a repository without re-reading everything. Two paths: **greenfield** (scaffold empty templates) and **brownfield** (audit first, then write findings into templates).

## Why this exists

Cold starts are expensive. Every new session that has to re-derive architecture, schema, and current task state burns tokens and loses fidelity. A small, durable memory layer (4 docs + 2 SOPs) eliminates that cost. The system stays minimal on purpose — bloated context is its own cold-start problem.

## Path detection

Before any file operations, decide and state the path:

- **Greenfield** if: no `src/`, no committed code beyond scaffolding, fresh init, or no live database.
- **Brownfield** if: existing source code, dependencies present, or a live database connection is configured.

Announce the detected path in one line before proceeding. This anchors every later step.

## Step 0: Preparation (both paths)

Create these files **only if missing**. DO NOT overwrite — re-running this skill must be safe.

**Folders:**
- `_memory/` — durable project docs
- `_memory/` — Project memory layer files
- `.agents/workflows/` — workflow SOPs
- `.agents/rules/` - workspace rules

**Files:**
- `_memory/STATUS.md`
- `_memory/LEARNINGS.md`
- `_memory/ARCHITECTURE.md`
- `_memory/DATABASE_SCHEMA.md`
- `.agents/workflows/start-session.md`
- `.agents/workflows/stop-session.md`
- `.agents/rules/output-mode.md`

> [!TIP]
> Templates for these files are located in `references/templates.md`. Read that file before creation — do not reconstruct templates from memory.

## Step 1: Establish workspace rules (both paths)
- Create`rules/output-mode.md` based on template and use its rules for all following steps.

## Step 2: Database audit

- **Greenfield:** skip. Leave `_memory/DATABASE_SCHEMA.md` as the empty template.
- **Brownfield:** introspect the live schema using the available Supabase/Database skill or tooling.
  1. Map all tables, primary keys, and foreign relationships.
  2. Identify Row Level Security (RLS) policies and non-nullable constraints.
  3. Write authoritative findings into `_memory/DATABASE_SCHEMA.md`.

Why the live DB wins over code: migrations drift, ORMs lie, and stale type files mislead. The running database is the only ground truth for what queries will actually succeed.

## Step 3: Architectural mapping

- **Greenfield:** skip. Leave `_memory/ARCHITECTURE.md` as empty template.
- **Brownfield:** analyze `src/`, `components/`, `lib/`, `execution/`, and similar entry points. 
  1. Map data flow (frontend ↔ backend ↔ database).
  2. Identify feature boundaries
  3. Identify the State Source of Truth — where shared state actually lives.


Why high-level and durable: this doc must survive refactors. If it changes every week, it is too detailed.

## Step 4: Constraint extraction

- **Greenfield:** skip. `LEARNINGS.md` accrues entries over time.
- **Brownfield:** identify "Brownfield Traps" surfaced during the audit (technical debt, inconsistent naming, complex RLS workarounds, framework-specific gotchas). Add as the initial entries in `_memory/LEARNINGS.md`.

Why log them now: traps discovered during audit are the cheapest to capture. Six weeks later, no one remembers why `user_id` is sometimes nullable.

## Step 5: Session sync (both paths)

Update `_memory/STATUS.md` to reflect:
- current version / build state
- open or in-progress GitHub issues
- the immediate next step for the *next* session

## Constraints

- **Minimalism** for all descriptions. Shortest accurate phrasing without filler words. If a sentence adds no value to a future AI agents, delete it.
- **Durable Logic**: Focus on *why* things are the way they are, not just *what* they are.
- **Live DB wins over code** for schema disagreements. Note the conflict in `LEARNINGS.md` so it is not rediscovered later.
- **Never overwrite existing files** in Step 0. Only create what is missing.
- **Never modify the templates** in `references/templates.md` when instantiating files — the structure is the contract.

## References

- `references/templates.md` — verbatim file templates for all six artifacts created in Step 0. Read this before writing any file in Step 0.