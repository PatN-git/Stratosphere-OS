---
type: architecture
title: Architecture
description: Tech stack, structure, data flow, and architectural laws.
generated:
  by: stratosphere-setup
  at: 2026-09-29
version: "1.0.7"
tracker: local
---
# ARCHITECTURE

## Purpose
<!-- SOS:BLOCK id=arch-guidance v=1.0.4 -->
Crystallized, durable map of how the system is organized. All entries are `[LAW]`-tier.

> Trust tags, supersession, and cross-reference rules → `.agents/rules/memory-protocol.md`.
> If a rule could be debated or overridden, it belongs in `LEARNINGS.md` instead.
> **PRESERVATION RULE:** Do NOT delete placeholder sections (`## Major Feature Areas`, `## State / Data Flow`, `## Backend / Database Boundaries`) or the format example line under `## Superseded` if there are no immediate entries during setup or updates. Keep them as placeholders until needed.
<!-- SOS:/BLOCK id=arch-guidance -->

## Architectural Vocabulary
<!-- SOS:BLOCK id=arch-vocabulary v=1.0.4 -->
- **Module:** A self-contained code unit (file, folder, component).
- **Interface:** The contract surface exposed by a module.
- **Depth (Deep/Shallow):** A deep module has a simple interface that hides significant complexity. A shallow module exposes all its internal details, increasing overall system complexity. We aim for deep modules.
- **Seam:** An interface boundary separating two parts of the system, allowing them to be developed, tested, or mocked independently.
- **Adapter:** A layer that maps between distinct domain interfaces, preserving the boundaries of each.
- **Leverage:** Maximizing reuse of clean primitives to reduce codebase surface area.
- **Locality:** Ensuring related data and operations stay close together to maximize readability and reasoning.
- **Deletion Test:** A metric to test coupling: would deleting or replacing this module concentrate complexity elsewhere, or just move it? If it concentrates complexity, the module is not fully decoupled.
<!-- SOS:/BLOCK id=arch-vocabulary -->

## Tech Stack
- Frontend:
- Backend / APIs:
- Database:
- Auth:
- Hosting / Deployment:
- **UI/UX standards:** see `.memory/DESIGN.md` (brand tokens) and `.memory/DESIGN_RULES.md` (structural rules)

## High-Level Structure
- `src/...`:
- `components/...`:
- `hooks/...`:
- `lib/...`:
- `execution/...`:

## Major Feature Areas
- Feature A:
  - Responsibility:
  - Key files:
  - Depends on:

## State / Data Flow
- Top-level state lives in:
- Shared state lives in:
- Data-fetching boundaries:
- Form state boundaries:
- Important async flows:

## Backend / Database Boundaries
- Which areas talk to the database:
- Where queries should live:
- Any RLS / auth assumptions:

## Tracker Registry
<!-- `tracker: github` only: the project-specific lines a local BACKLOG_MAP.md would hold. Setup fills them; under `tracker: local` leave them empty (the map holds them). -->
- Area labels (`area:xxx`):
- GitHub Project ID:

## Structural Rules
- **[[A-001]] [EXAMPLE (UI-tier)] [LAW]** Keep page/app files focused on top-level state coordination, data flow, and visual composition.
- **[[A-002]] [EXAMPLE (UI-tier)] [LAW]** Extract non-trivial state/effect and complex UI logic into hooks. Keep constants, static mock data, and helpers out of component files.
- **[[A-003]] [LAW]** Do not mix unrelated concerns in large component files. If a code file or logic file exceeds 400 lines, contains multiple distinct layout sections, or mixes multiple concerns, perform a clean structural extraction before writing new code.
- **[[A-004]] [LAW]** Do not rewrite folder structures wholesale. When dealing with legacy or messy codebases, extract one isolated concern at a time, verify functionality remains green, and preserve established style.

## Known Architectural Constraints
- **[[A-XXX]] [LAW]** Example placeholder. Source: BT-XXX.
- **[[A-XXX]] [LAW]** Issue tracker backend: `<github|local>` (frontmatter `tracker:`). `github`: GitHub issues are the only store, there is no `.memory/BACKLOG_MAP.md`, and nothing writes a local copy. `local`: the map is the store (`/stratosphere-setup` records the choice; `tracker_switch.py` moves a local project to GitHub). Source: BT-197.

## Floor exceptions
<!-- Rows a human merges to the default branch, `<rule> <glob> — <reason>`, e.g. `A-003 src/legacy.js — legacy, split in BT-nnn`. The rule is a floor rule or a rule ID above. -->

## Superseded
> Read only when explicitly asked.

- **A-XXX [SUPERSEDED BY A-YYY] [YYYY-MM-DD]** Original rule preserved. Reason: one line. Version: v0.X → v0.Y.
