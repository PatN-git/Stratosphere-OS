---
name: 0b_stop-session
description: Conclude session by codifying progress, updating memory, and linting.
type: workflow HITL
trigger: manual
version: "1.2.0"
timestamp: 2026-07-17
---

# STOP SESSION

## Goal
Leave next session with context to resume immediately. Ensure new entries are tagged, cross-referenced, and lint-clean.

> Trust tags, supersession, cross-reference, and lint protocols → `.agents/rules/memory-protocol.md`.

## Phase 0: Context Hydration (self-gated, read-only)
Run `.agents/skills/load-memory/SKILL.md` to restore session context. Self-gated (no-op if already loaded this session). Read-only: never transitions issue state or touches branches.

## Procedure

**First entry rule:** On first entry in `STATUS.md`, `LEARNINGS.md`, `GLOSSARY.md`, `ARCHITECTURE.md`, or `DESIGN_RULES.md`, delete placeholders only; preserve structure, guidelines, and format examples under `## Superseded`.

1. Compare completed vs. planned:
    - Comment plan, completed, and open steps on active GitHub issues, and note which issues were updated/closed.
    - **Done detection (no forcing):** a slice/epic is `done` only once its PR has **merged** and the issue auto-closed. For each issue **closed/merged** this session: mark its BACKLOG Status `done` (or delete the row per retention) and **clear its bare ID from every dependent's `Blocked by`** in `.memory/BACKLOG_MAP.md` and GitHub (safety net for the 4a in-review clearing). Do **not** force `status:done` on a slice still at `status:in review` (code shipped but unmerged) — leave it for the human merge. If all sibling sub-issues under `#parent` are closed/merged, prompt to confirm the parent epic `done` and reconcile `BT-<parent>` in `BACKLOG_MAP.md`.
2. Update `.memory/STATUS.md` (last sync, current branch, active issue, current focus, completed, blockers, next step).
3. Evaluate session reasoning for inefficiencies. If systemic tool/agent failure, flag the specific `.agents/skills/` or `.agents/workflows/` path for optimization (do not log learning).
4. If durable lesson discovered, add to `.memory/LEARNINGS.md` (assign next `[[L-xxx]]`, apply default tag `[ASSUMED]`, cross-reference `Source: BT-xxx`).
5. If term agreed, add to `.memory/GLOSSARY.md` (assign next `[[G-xxx]]`, default tag `[ASSUMED]`, record rejected synonyms in `Avoid:` — same as 1b; if an `Avoid:` synonym likely already appears in code, offer the same one-time, module-scoped retrofit (propose-only); cross-reference `Source`).
6. If architecture changed:
   - Propose structural `[LAW]` changes; never self-write to `ARCHITECTURE.md`.
   - On confirmation, add `[[A-xxx]]` entry (follow supersession protocol).
7. If DB schema or understanding changed, update `.memory/DATABASE_SCHEMA.md` (always `[LAW]`).
8. Propose UI structural (`[[DR-xxx]]`/immortal component) or brand token changes before updating `DESIGN_RULES.md`/`DESIGN.md`.
9. Run codebase verification tests, then run memory lint: `python .agents/scripts/validate_memory.py`. Propose fixes for any reported errors, list warnings, and await confirmation.
10. Regenerate OKF Visualizer: `python .agents/scripts/okf_view.py` after lint passes.
11. Ensure `.memory/STATUS.md` allows resuming without re-discovery.

## Handoff Note Format
Session complete.
- What changed:
- Files touched:
- GitHub issues touched:
- Verification & Lint results:
- New learnings (with IDs and tags):
- New glossary terms (with IDs and tags):
- Blockers:
- Next immediate step:

## Constraints
- **Security:** Redact sensitive information (e.g. API keys, passwords, personally identifiable information).
- **No silent memory rewrites:** crystallization, supersession, and lint fixes require user confirmation.