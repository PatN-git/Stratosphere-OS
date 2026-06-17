<!-- stratosphere: version=1.0.0 updated=2026-06-17 -->
# LEARNINGS

## Purpose
Episodic memory for project-specific lessons likely to matter again. Each entry carries a unique `L-xxx` ID, a trust tag, and (where applicable) a `Source: BT-xxx` cross-reference.

> Trust tags, supersession, and cross-reference rules → `.agents/rules/memory-protocol.md`.

## What belongs here
- API constraints discovered the hard way
- Auth / RLS gotchas
- Setup pitfalls
- Recurring edge cases
- Framework-specific traps

## What does NOT belong here
- Temporary TODOs → `BACKLOG_MAP.md`
- Current task status → `STATUS.md`
- One-off debugging logs unless they reveal a reusable rule
- `[LAW]`-tier rules → `ARCHITECTURE.md` or `DESIGN_RULES.md`
- Domain vocabulary → `GLOSSARY.md`

## Active Entries

- **[[L-XXX]] [ASSUMED] [YYYY-MM-DD]** Example placeholder. Source: BT-XXX.
- **[[L-YYY]] [PATTERN] [YYYY-MM-DD]** Example: Detail drawer state must remain outside map marker components to avoid rerender loop. Source: BT-XXX.

## Superseded
> Read only when explicitly asked.

- **L-XXX [SUPERSEDED BY L-YYY] [YYYY-MM-DD]** Original entry preserved. Reason: one line. Version: v0.X → v0.Y.
