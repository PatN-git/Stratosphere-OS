<!-- stratosphere: version=1.0.0 updated=2026-06-17 -->
# ARCHITECTURE

## Purpose
Crystallized, durable map of how the system is organized. All entries are `[LAW]`-tier.

> Trust tags, supersession, and cross-reference rules → `.agents/rules/memory-protocol.md`.
> If a rule could be debated or overridden, it belongs in `LEARNINGS.md` instead.

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

## Structural Rules
- **[[A-001]] [EXAMPLE (UI-tier)] [LAW]** Keep page/app files focused on top-level state coordination, data flow, and visual composition.
- **[[A-002]] [EXAMPLE (UI-tier)] [LAW]** Extract non-trivial state/effect and complex UI logic into hooks. Keep constants, static mock data, and helpers out of component files.
- **[[A-003]] [LAW]** Do not mix unrelated concerns in large component files. If a code file or logic file exceeds 400 lines, contains multiple distinct layout sections, or mixes multiple concerns, perform a clean structural extraction before writing new code.
- **[[A-004]] [LAW]** Do not rewrite folder structures wholesale. When dealing with legacy or messy codebases, extract one isolated concern at a time, verify functionality remains green, and preserve established style.

## Known Architectural Constraints
- **[[A-XXX]] [LAW]** Example placeholder. Source: BT-XXX.

## Superseded
> Read only when explicitly asked.

- **A-XXX [SUPERSEDED BY A-YYY] [YYYY-MM-DD]** Original rule preserved. Reason: one line. Version: v0.X → v0.Y.
