---
name: 0b_stop-session
description: Concludes session by codifying progress, updating memory artifacts, and performing linting to ensure a seamless, state-aware resumption of work.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.2"
timestamp: 2026-06-23
---

# STOP SESSION

## Goal
Leave next session with enough context to resume immediately. Ensure all new entries are properly tagged, cross-referenced, and lint-clean.

> Trust tags, supersession, cross-reference, and lint protocols → `.agents/rules/memory-protocol.md`.

## Procedure
1. Compare completed vs. planned and do the following
    - Update active GitHub issues via comment with plan, completed steps, and open steps (if needed).
    - If the agent or user marks a task `[DONE]`, delete it from `.memory/BACKLOG_MAP.md`.
2. Update `.memory/STATUS.md`: last sync, current branch, active issue, current focus, completed this session, blockers (if any), next immediate step. (When writing the first real content to STATUS.md, delete the shipped example placeholders).
3. Evaluate the internal reasoning loop for this session to minimize token drift:
    - Analyze agent and sub-agent execution behaviors for inefficiencies (e.g., redundant tool executions, loops, loop-breaking errors, or prompt misunderstandings).
    - If an issue stems from systemic tool/agent failure, flag the specific `.agents/skills/` or `.agents/workflows/` path for optimization rather than logging a standard learning.
4. If a durable lesson was discovered, add it to `.memory/LEARNINGS.md`:
   - Assign next available `[[L-xxx]]` ID.
   - Apply trust tag (default `[ASSUMED]`; see `memory-protocol.md` for promotion rules).
   - Add `Source: BT-xxx` cross-reference.
   - When writing the first real `[[L-xxx]]`, delete ONLY the shipped example dummy items (e.g., L-XXX/L-YYY); do NOT delete the format example line under `## Superseded`.
5. If a domain term was agreed (during a discover session, while writing a PRD, or surfaced during implementation), add it to `.memory/GLOSSARY.md`:
   - Assign next available `[[G-xxx]]` ID.
   - Apply trust tag (default `[ASSUMED]`).
   - Capture rejected synonyms as the entry's `Avoid:` list (plain text), same as 1b. If a new `Avoid:` synonym likely already appears in code, offer the same one-time, module-scoped retrofit (propose-only).
   - Add `Source:` pointing to the discovery brief, PRD, or issue where the term was settled.
   - When writing the first real `[[G-xxx]]`, delete ONLY the shipped example dummy item (e.g., G-XXX); do NOT delete the format example line under `## Superseded` or the protocol/Avoid guidelines.
6. If architecture changed meaningfully:
   - For `[LAW]`-level changes, propose to user. Agent NEVER self-writes to `ARCHITECTURE.md`.
   - On confirmation, add `[[A-xxx]]` entry. If superseding an old rule, follow supersession protocol in `memory-protocol.md`.
   - When writing the first real `[[A-xxx]]` rule, delete ONLY the shipped example dummy item (e.g., A-XXX); do NOT delete empty structural sections (`## Major Feature Areas`, etc.) or the format example line under `## Superseded`.
7. If schema understanding changed or a DB change landed, update `.memory/DATABASE_SCHEMA.md`. Schema changes are `[LAW]` by default.
8. If a UI structural decision was made (new immortal component, change to a `[[DR-xxx]]` entry), update `.memory/DESIGN_RULES.md`. Propose to user; never self-promote. If brand tokens changed, update `.memory/DESIGN.md` per spec — propose changes to user. When registering the first real Immortal Components, delete ONLY the shipped example dummy items (e.g., DR-XXX/DR-YYY); do NOT delete §1 Principles, §2 Design Reference Rules, Applicability/round-trip paragraphs, or the format example line under `## Superseded`.
9. **Run lint** by executing `python .agents/scripts/validate_memory.py`. Propose fixes for any reported errors, list any warnings, and await user confirmation.
10. **Regenerate OKF Visualizer** by running `python .agents/scripts/okf_view.py` after the memory lint checks pass.
11. Ensure `.memory/STATUS.md` lets the next session resume without re-discovery.

## Handoff Note Format (Leave blank if nothing applies)
Session complete.
- What changed:
- Files touched:
- Verification run:
- New learnings (with IDs and tags):
- New glossary terms (with IDs and tags):
- Lint results:
- Blockers:
- Next immediate step:

## Constraints
- **Security:** Redact sensitive information (e.g. API keys, passwords, personally identifiable information).
- **No silent memory rewrites:** all crystallization, supersession, and lint fixes require user confirmation.