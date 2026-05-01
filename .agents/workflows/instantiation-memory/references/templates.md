---
description: 
---

# File Templates

Verbatim templates for the six files created during Step 0 of the instantiation-memory skill. Use these exactly — do not modify the structure when creating files. Each template is wrapped in a fenced block; copy the contents inside the fence into the target file.

## Table of contents

1. `_memory/STATUS.md`
2. `_memory/LEARNINGS.md`
3. `_memory/ARCHITECTURE.md`
4. `_memory/DATABASE_SCHEMA.md`
5. `_memory/BACKLOG_MAP.md
6. `.agents/workflows/start-session.md`
7. `.agents/workflows/stop-session.md`
8. `.agents/rules/output-mode.md`

---

## 1. `_memory/STATUS.md`

```markdown
# STATUS

- **Last Sync:**
- **Current Branch:**
- **Active Issue / PRD:**
- **Current Focus:**
- **Completed This Session:**
- **Open/Active Task Brief:**
- **Blocker (if any):**
- **Next Immediate Step:**
```

---

## 2. `_memory/LEARNINGS.md`

```markdown
# LEARNINGS

## Durable Constraints
Add only project-specific lessons likely to matter again.

Good examples:
- API constraints
- Auth / RLS gotchas
- Setup pitfalls
- Recurring edge cases
- Framework-specific traps

Do not add:
- Temporary TODOs
- Current task status
- One-off debugging logs unless they reveal a reusable rule

## Entries [Placeholders replace with real learnings]
- [YYYY-MM-DD] Example: Supabase RLS requires X for Y query path.
- [YYYY-MM-DD] Example: Detail drawer state must remain outside map marker components to avoid rerender loop.
```

---

## 3. `_memory/ARCHITECTURE.md`

```markdown
# ARCHITECTURE

## Purpose
Short, durable map of how the system is organized. Cross-feature reference for new sessions.

## Tech Stack
- Frontend:
- Backend / APIs:
- Database:
- Auth:
- Hosting / Deployment:

## High-Level Structure
- `src/...`:
- `components/...`:
- `hooks/...`:
- `lib/...`:
- `execution/...`:
- `directives/...`:

## Major Feature Areas
- Feature A:
  - Responsibility:
  - Key files:
  - Depends on:
- Feature B:
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
- Where schema assumptions must be checked:
- Any RLS / auth assumptions:

## Structural Rules
- Keep page/app files focused on composition.
- Extract non-trivial state/effect logic into hooks.
- Do not mix unrelated concerns in large component files.
- Prefer small, safe extractions over wholesale rewrites in brownfield areas.

## Known Architectural Constraints
- Constraint:
- Constraint:
```

---

## 4. `_memory/DATABASE_SCHEMA.md`

```markdown
# DATABASE SCHEMA

## Purpose
Authoritative reference for tables, columns, relationships, and important constraints (if relevant for project).

## Rules
- Check this file before proposing schema changes, writing migrations, or changing queries.
- If code and this file disagree, verify the real schema before proceeding.
- Update this file when schema changes are finalized.

## Tables

### `table_name`
**Purpose:**
**Primary key:**
**Important columns:**
- `id`:
- `created_at`:
- `...`:

**Relationships:**
- Belongs to:
- References:
- Used by:

**Notes / constraints:**
- RLS notes:
- Nullable / required notes:
- Query caveats:

### `another_table`
```

---

## 6. `._memory/BACKLOG_MAP.md`

```markdown
# BACKLOG MAP

## Purpose
Authoritative, high-desnity reference for project issues and their status.

## Rules
- When writing the first entry in this file update the Label Registry with all labels used in this GitHub project.
- Update this file when github issues are created, closed, or their status changes.
- When adding an issue to the ## Backlog, always add the ID, Title, Status, Labels, Milestone, and Dependencies, nothing else.
- Do not add detailed descriptions here; Title and lables is enough.
- Use the Label Registry defined below, don't invent your own labels.
- When adding a issue from github that has a new label update the ## Label Registry with the new label.

## Backlog
| ID | Title | Status | Labels | Milestone | Dependencies |
|:---|:---|:---|:---|:---|

## Label Registry
- **Area**: area:xxx, 
- **Type**: type:xxx,
- **State**: state:xxx,
- **Priority**: priority:xxx,
- **Size**: size:xxx
---

## 6. `.agents/workflows/start-session.md`

```markdown
# START SESSION

## Goal
Reconstruct minimum necessary context quickly without re-reading whole repository.

## Steps
1. Read `_memory/STATUS.md`.
2. Read active task source (prompt, issue, PRD, spec) for objective, constraints, dependencies.
3. Read `_memory/LEARNINGS.md` for durable constraints relevant to current task.
4. Read `_memory/ARCHITECTURE.md` if task affects structure, state flow, feature boundaries, or cross-feature behavior.
5. Read `_memory/BACKLOG_MAP.md to ensure the current task doesn't conflict with other work-in-progress.
6. Only if task touches DB queries, schema, migrations, or RLS eead `_memory/DATABASE_SCHEMA.md`.
7. Read only most relevant code files next — not whole codebase.
8. Confirm working context in brief summary.

## Output Pattern
Context synced.
- Objective:
- Current state:
- Next step:
- Needs verification:
```

---

## 7. `.agents/workflows/stop-session.md`

```markdown
# STOP SESSION

## Goal
Leave next session with enough context to resume immediately.

## Steps
1. Compare completed vs. planned.
2. Update `_memory/STATUS.md` with: last sync, current branch, active issue, current focus, completed this session, blocker (if any), next immediate step.
3. If durable lesson was discovered, add to `_memory/LEARNINGS.md`.
4. If architecture changed meaningfully, update `_memory/ARCHITECTURE.md`.
5. If schema understanding changed or a DB change landed, update `_memory/DATABASE_SCHEMA.md`.
6. Update the active github issues via comment with the plan, completed and open steps.
7. If user marks the task in github as [DONE] delete this task in `_memory/BACKLOG_MAP.md`.
8. Ensure `_memory/STATUS.md` lets next session resume without re-discovery.

## Handoff Note Format
Session complete.
- What changed:
- Files touched:
- Verification run:
- Blockers:
- Next immediate step:

## Constraints
- **Security** never expose any API keys
```

## 8. `.agents/rules/output-mode.md`

```markdown 

# Output Mode Protocol

## 1. Goal
Maximize information density while minimizing token waste. Focus on *what was done* and *what changed* rather than narrating the process.

## 2. Decision Matrix
Choose the mode based on the current turn's intent:

| Mode | Task Type | Output Structure |
| :--- | :--- | :--- |
| **Routine** | Trivial, cosmetic, or repetitive mechanical tasks (moves, copies, renames). | Skip plan. Execute immediately. Max 1 line of keyword-only status. |
| **Standard** | Any non-trivial functional change. | 5-point brief: Assumptions, Plan, Execution, Verification, Updates. |
| **Complex** | Impacts `ARCHITECTURE.md` or `DATABASE_SCHEMA.md`. | **Trade-off Brief** (Choice/Consequence) + Standard structure. |

---

## 3. Mode Specifications

### Routine Mode
- No preamble. No "I will now...". 
- Response: Optional 1-line status if tool feedback is insufficient. 
- Example: `[DONE] Created /scratch. Moved verify_fix.py.`

### Complex (Trade-off Brief)
If a decision affects the long-term build, append this brief:
- **Choice:** [1-sentence technical description]
- **Consequence:** [Direct impact on future build/logic]

### Standard Mode
Keep each point to one line if possible:
1. **Assumptions**: [Short context]
2. **Plan**: [Surgical steps]
3. **Execution**: [The work]
4. **Verification**: [Results]
5. **Updates**: [Changes to docs/scripts]

---

## 4. General Constraints
- **No Fillers**: Avoid "I understand," "Sure," "Great," or "I'll get right on that."
- **Surgical Narrative**: If you must explain, explain the *why*, not the *how*.
- **Direct Verification**: If you run a test, just show the result.