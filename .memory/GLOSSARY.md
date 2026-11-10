---
type: glossary
title: Glossary
description: Shared domain vocabulary used across docs and code.
generated:
  by: 1b-concept-framing
  at: 2026-10-20
version: "1.0.4"
---
# GLOSSARY

## Purpose
<!-- SOS:BLOCK id=glossary-guidance v=1.2.0 -->

- **Format:** One `[[G-xxx]]` entry per project-specific term, each with a trust tag (`.agents/rules/memory-protocol.md`).
- **Scope:** Vocabulary only — no code identifiers, file paths, table or column names, formulas, or thresholds (→ `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`).
- **Rules:** Writers follow `references/glossary-entry-rules.md`.

<!-- SOS:/BLOCK id=glossary-guidance -->

## Active Entries
*Note: Once the glossary is large, entries MAY be grouped under `## Domain: <name>` subheadings for navigability. IDs remain a single global `G-xxx` space regardless of grouping.*

- **[[G-001]] [ASSUMED] [2026-10-06]** Orchestrator: user-invoked lifecycle skill that sequences other skills by command name within its run and never copies unit bodies; HITL (`1c`, `2z`) or AFK (`3z`). Source: BT-144, AGENTS.md §1.
- **[[G-002]] [ASSUMED] [2026-10-20]** Tracker backend: where issues live (GitHub or local markdown), chosen once at setup. Avoid: offline mode, BT-LOCAL mode (BT-LOCAL is only an ID prefix). Source: BT-189, docs/discovery/backlog-map-generated-cache.md.
- **[[G-003]] [ASSUMED] [2026-10-20]** Tracker verb: a backend-neutral read or write named in workflow prose (e.g. set status, add blocker), resolved by the chosen tracker backend. Source: BT-189.
- **[[G-004]] [ASSUMED] [2026-10-20]** Mirror write: the second write of a GitHub-owned field (status, labels, milestone, parent, blocked-by) into BACKLOG_MAP. Avoid: dual write, sync write. Source: BT-189.

*`Avoid:` is optional — populate it only when a term was canonicalized over rejected alternatives. Plain text only (never `[[ ]]`), so it is not parsed as a cross-reference.*

## Superseded
> Read only when explicitly asked.

- **G-XXX [SUPERSEDED BY G-YYY] [YYYY-MM-DD]** Example: Original entry preserved. Reason: one line. Version: v0.X → v0.Y.
