---
type: database-schema
title: Database Schema
description: Authoritative schema layout, constraints, and relationships.
timestamp: 2026-06-16
version: "1.0.0"
---

# DATABASE SCHEMA

## Purpose
Authoritative reference for tables, columns, relationships, and constraints. All entries are `[LAW]`-tier — sourced from live database introspection.

> Trust tags and supersession rules → `.agents/rules/memory-protocol.md`.

## Rules
- Check this file before proposing schema changes, writing migrations, or changing queries.
- If code and this file disagree, verify the real schema first. Note conflicts as `[LAW]` learnings.
- Update when schema changes are finalized.

## Tables

### `table_name`
**Purpose:**
**Primary key:**
**Important columns:**
- `id`:
- `created_at`:

**Relationships:**
- Belongs to:
- References:
- Used by:

**Notes / constraints:**
- RLS notes:
- Nullable / required notes:
- Query caveats:

## Superseded
> Read only when explicitly asked.

- **[YYYY-MM-DD]** Removed table / column / constraint preserved here with reason and version.
