---
description: Concludes session by codifying progress, updating memory artifacts, and performing linting to ensure a seamless, state-aware resumption of work.
---

# STOP SESSION

## Goal
Leave next session with enough context to resume immediately. Ensure all new entries are properly tagged, cross-referenced, and lint-clean.

> Trust tags, supersession, cross-reference, and lint protocols → `.agents/rules/memory-protocol.md`.
> Persona handoff convention → `.agents/rules/persona-protocol.md`.

## Procedure
1. Compare completed vs. planned and do the following
    - Update active GitHub issues via comment with plan, completed steps, and open steps (if needed).
    - If the agent or user marks a task `[DONE]`, delete it from `.memory/BACKLOG_MAP.md`.
2. Update `.memory/STATUS.md`: last sync, current branch, active issue, current focus, active persona (if any), completed this session, blockers (if any), next immediate step, suggested next persona (if applicable).
3. Evaluate the internal reasoning loop for this session to minimize token drift:
    - Analyze agent and sub-agent execution behaviors for inefficiencies (e.g., redundant tool executions, loops, loop-breaking errors, or prompt misunderstandings).
    - If an issue stems from systemic tool/agent failure, flag the specific `.agents/skills/` or `.agents/workflows/` path for optimization rather than logging a standard learning.
4. If a durable lesson was discovered, add it to `.memory/LEARNINGS.md`:
   - Assign next available `[[L-xxx]]` ID.
   - Apply trust tag (default `[GUESS]`; see `memory-protocol.md` for promotion rules).
   - Add `Source: [[BT-xxx]]` cross-reference.
5. If a domain term was agreed (during a discover session, while writing a PRD, or surfaced during implementation), add it to `.memory/GLOSSARY.md`:
   - Assign next available `[[G-xxx]]` ID.
   - Apply trust tag (default `[GUESS]`).
   - Add `Source:` pointing to the discovery brief, PRD, or issue where the term was settled.
6. If architecture changed meaningfully:
   - For `[LAW]`-level changes, propose to user. Agent NEVER self-writes to `ARCHITECTURE.md`.
   - On confirmation, add `[[A-xxx]]` entry. If superseding an old rule, follow supersession protocol in `memory-protocol.md`.
7. If schema understanding changed or a DB change landed, update `.memory/DATABASE_SCHEMA.md`. Schema changes are `[LAW]` by default.
8. If a UI structural decision was made (new immortal component, change to a `[[DR-xxx]]` entry), update `.memory/DESIGN_RULES.md`. Propose to user; never self-promote. If brand tokens changed, update `.memory/DESIGN.md` per spec — propose changes to user.
9. **If a persona was active this session,** capture the handoff in `STATUS.md` per `persona-protocol.md`: artifact produced, where it lives, which persona picks up next.
10. **Run lint** by executing `python .agents/scripts/validate_memory.py`. Propose fixes for any reported errors, list any warnings, and await user confirmation.
11. Ensure `.memory/STATUS.md` lets the next session resume without re-discovery.

## Handoff Note Format (Leave blank if nothing applies)
Session complete.
- What changed:
- Files touched:
- Verification run:
- New learnings (with IDs and tags):
- New glossary terms (with IDs and tags):
- Persona artifacts produced (if any):
- Lint results:
- Blockers:
- Next immediate step:
- Suggested next persona:

## Constraints
- **Security:** Redact sensitive information (e.g. API keys, passwords, personally identifiable information).
- **No silent memory rewrites:** all crystallization, supersession, and lint fixes require user confirmation.