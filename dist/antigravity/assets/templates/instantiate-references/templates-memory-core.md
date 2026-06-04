---
description: Verbatim templates for the core .memory/* files — STATUS, LEARNINGS, GLOSSARY, ARCHITECTURE, DATABASE_SCHEMA, BACKLOG_MAP.
---

# Memory Layer Templates — Core

Verbatim templates for the six core files in `.memory/`. Use these exactly.

Companion files: `templates-agents-design.md` for DESIGN.md + DESIGN_RULES.md, `templates-agents-workflows.md` and `templates-agents-rules.md` for `.agents/*`.

## Table of contents

1. `.memory/STATUS.md`
2. `.memory/LEARNINGS.md`
3. `.memory/GLOSSARY.md`
4. `.memory/ARCHITECTURE.md`
5. `.memory/DATABASE_SCHEMA.md`
6. `.memory/BACKLOG_MAP.md`

> [!NOTE]
> Trust tags (`[LAW]`, `[PATTERN]`, `[GUESS]`), supersession protocol, cross-reference rules, and lint procedure are defined in `.agents/rules/memory-protocol.md`. Memory files reference that protocol; they do not redefine it.

---

## 1. `.memory/STATUS.md`

```markdown
# STATUS

- **Last Sync:**
- **Current Branch:**
- **Active Issue / PRD:**
- **Current Focus:**
- **Active Persona (this session, if any):**
- **Completed This Session:**
- **Open/Active Task Brief:**
- **Blocker (if any):**
- **Next Immediate Step:**
- **Suggested Next Persona (if applicable):**
```

---

## 2. `.memory/LEARNINGS.md`

```markdown
# LEARNINGS

## Purpose
Episodic memory for project-specific lessons likely to matter again. Each entry carries a unique `[[L-xxx]]` ID, a trust tag, and (where applicable) a `Source: [[BT-xxx]]` cross-reference.

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

- **[[L-001]] [GUESS] [YYYY-MM-DD]** Example placeholder. Source: [[BT-XX]].
- **[[L-002]] [PATTERN] [YYYY-MM-DD]** Example: Detail drawer state must remain outside map marker components to avoid rerender loop. Source: [[BT-XX]], [[BT-XX]].

## Superseded
> Read only when explicitly asked.

- **[[L-XXX]] [SUPERSEDED BY [[L-YYY]]] [YYYY-MM-DD]** Original entry preserved. Reason: one line. Version: v0.X → v0.Y.
```

---

## 3. `.memory/GLOSSARY.md`

```markdown
# GLOSSARY

## Purpose
Shared domain vocabulary. Terms used across discovery briefs, PRDs, sub-issues, and code. Each entry carries a `[[G-xxx]]` ID and trust tag.

> Trust tags, supersession, and cross-reference rules → `.agents/rules/memory-protocol.md`.
> GLOSSARY follows the same protocol as `LEARNINGS.md` — not exempt from trust tags.

## What belongs here
- Names of user segments and roles
- Business-state vocabulary
- Domain-specific terms with project-specific or non-obvious meanings
- Categorization terms used across features and PRDs

## What does NOT belong here
- Code identifiers, function names, file paths → `ARCHITECTURE.md`
- Brand tokens → `DESIGN.md`
- One-off terms not expected to recur across docs
- Technical/framework terms with standard industry meanings

## Active Entries

- **[[G-001]] [GUESS] [YYYY-MM-DD]** Term: definition. Source: docs/discovery/<slug>.md or [[BT-xx]].

## Superseded
> Read only when explicitly asked.

- **[[G-XXX]] [SUPERSEDED BY [[G-YYY]]] [YYYY-MM-DD]** Original entry preserved. Reason: one line. Version: v0.X → v0.Y.
```

---

## 4. `.memory/ARCHITECTURE.md`

```markdown
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
- **[[A-001]] [LAW]** Keep page/app files focused on top-level state coordination, data flow, and visual composition.
- **[[A-002]] [LAW]** Extract non-trivial state/effect and complex UI logic into hooks. Keep constants, static mock data, and helpers out of component files.
- **[A-003] [LAW]** Do not mix unrelated concerns in large component files. If a code file or logic file exceeds 400 lines, contains multiple distinct layout sections, or mixes multiple concerns, perform a clean structural extraction before writing new code.
- **[[A-004]] [LAW]** Do not rewrite folder structures wholesale. When dealing with legacy or messy codebases, extract one isolated concern at a time, verify functionality remains green, and preserve established style.

## Known Architectural Constraints
- **[[A-XXX]] [LAW]** Constraint:

## Superseded
> Read only when explicitly asked.

- **[[A-XXX]] [SUPERSEDED BY [[A-YYY]]] [YYYY-MM-DD]** Original rule preserved. Reason: one line. Version: v0.X → v0.Y.
```

---

## 5. `.memory/DATABASE_SCHEMA.md`

```markdown
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
```

---

## 6. `.memory/BACKLOG_MAP.md`

```markdown
# BACKLOG MAP

## Purpose
Authoritative, high-density reference for project issues and their status.

> Cross-reference rules → `.agents/rules/memory-protocol.md`.

## Rules
- When writing the first entry, populate the Label Registry with all labels used in this GitHub project.
- Update when GitHub issues are created, closed, or change status.
- Include only ID, Title, Status, Labels, Milestone, Dependencies, Ref — nothing else.
- Use the Label Registry; do not invent labels.
- The `Ref` column links to learnings, architecture rules, design rules, or glossary terms (e.g., `[[L-012]], [[A-003]], [[DR-020]], [[G-005]]`).
- **Label source of truth:** After installation (Step 6a), the Label Registry here reflects the live GitHub label set.
  - If a label appears in **GitHub but not the registry** → add it to the registry (with user confirmation).
  - If a label appears in the **registry but not GitHub** → create it in GitHub before using it in any issue.
  - Never use a label in the Backlog table that is not in both the registry and GitHub.

## Label Registry
- **Area (`area:xxx`)**: `area:BE-ai`, `area:BE-api`, `area:BE-auth`, `area:BE-data`, `area:BE-infrastructure`, `area:FE-<page_name>` (where `<page_name>` is replaced with the page's slug during audit or page creation, e.g., `area:FE-login`, `area:FE-dashboard`)
- **Type (`type:xxx`)**: `type:bug`, `type:content`, `type:feature`, `type:improvement`, `type:maintenance`, `type:research`, `type:HITL`, `type:AFK`, `type:NEEDS_SPEC`
- **Priority (`priority:xxx`)**: `priority:high` (Must have), `priority:medium` (Important), `priority:low` (Nice to have)
- **Size (`size:xxx`)**: `size:large` (Architectural: Multi-feature/major schema), `size:medium` (Vertical: Standard Data/Logic/UI slice), `size:small` (Surgical: Local/Single-file)
- **Status (`status:xxx`)**: `status:planned`, `status:in progress`, `status:done`
- **Milestone**: `x.yy` (where `x` is the release version, `yy` is the sprint number; `x.00` is targeted but not yet sprinted). Mirrors the GitHub milestone.

## Backlog

| ID | Title | Status | Labels | Milestone | Dependencies | Ref |
|:---|:---|:---|:---|:---|:---|:---|
| BT-001 | Example task title | planned | area:FE-dashboard, type:feature | v0.8 | — | [[L-002]], [[A-003]], [[DR-020]] |
```