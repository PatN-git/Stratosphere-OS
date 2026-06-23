---
type: glossary
title: Glossary
description: Shared domain vocabulary used across docs and code.
timestamp: 2026-06-23
version: "1.0.3"
---
# GLOSSARY

## Purpose
Shared domain vocabulary. Terms used across discovery briefs, PRDs, sub-issues, and code. Each entry carries a `G-xxx` ID and trust tag.

> Trust tags, supersession, and cross-reference rules → `.agents/rules/memory-protocol.md`.
> GLOSSARY follows the same protocol as `LEARNINGS.md` — not exempt from trust tags.

## What belongs here
- Names of user segments and roles
- Business-state vocabulary
- Domain-specific terms with project-specific or non-obvious meanings
- Categorization terms used across features and PRDs

## What does NOT belong here
- Code identifiers, function names, file paths, or domain/structural relationships between concepts → `ARCHITECTURE.md` (Depends-on / data-flow). The GLOSSARY is vocabulary only.
- Brand tokens → `DESIGN.md`
- One-off terms not expected to recur across docs
- Technical/framework terms with standard industry meanings

## Active Entries
*Note: Once the glossary is large, entries MAY be grouped under `## Domain: <name>` subheadings for navigability. IDs remain a single global `G-xxx` space regardless of grouping.*

- **[[G-XXX]] [ASSUMED] [YYYY-MM-DD]** Example Term: definition. Avoid: banned-synonym-1, banned-synonym-2. Source: docs/discovery/<slug>.md or BT-XXX.

*`Avoid:` is optional — populate it only when a term was canonicalized over rejected alternatives. Plain text only (never `[[ ]]`), so it is not parsed as a cross-reference.*

## Superseded
> Read only when explicitly asked.

- **G-XXX [SUPERSEDED BY G-YYY] [YYYY-MM-DD]** Example: Original entry preserved. Reason: one line. Version: v0.X → v0.Y.
