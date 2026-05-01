---
description: Standardize feature ideas into "Implementation-Ready" vertical slices and update the project memory layer.
---

# SKILL: Task Specification & Creation
**Purpose:** Standardize feature ideas into "Implementation-Ready" vertical slices and update the project memory layer.

## Phase 1: Intake & Audit
1. **Intake:** Receive raw idea or "Minimum Viable Issue."
2. **Surgical Audit:** Check `_memory/DATABASE_SCHEMA.md` and `_memory/ARCHITECTURE.md` for technical collisions.
3. **Collision Check:** Reference `_memory/BACKLOG_MAP.md` for overlapping IDs.

## Phase 2: The Vertical Slice Quiz
Before creating the task, propose the breakdown to the user:
1. **Numbered List of Slices:**
   - **Title:** [Short name]
   - **Type:** [HITL (Human in the Loop) / AFK (Away from Keyboard)]
   - **Blocked by:** [IDs of prerequisite slices]
   - **User Stories:** [Value addressed]
2. **Approval Request:**
   - Does the granularity feel right? (Too coarse / too fine)
   - Are the dependency relationships correct?
   - Should any slices be merged or split further?
   - Are the correct slices marked as HITL and AFK?
*Stop and iterate until the user approves the breakdown.*

## Phase 3: Implementation & Memory Sync
Once approved, generate the issue using the appropriate template and **immediately** append the ID and Title to `docs/BACKLOG_MAP.md`.

---

### TEMPLATE A: Minimum Viable Issue (Quick Capture)
*Use for: Rapid discovery or saving vibes for later.*
## Overview
One sentence: what and why.
## Rough approach
- 2-3 bullets on the mental model.
## Open questions
- Blockers to solve before moving to Template B.
## Dependencies
- Relation to existing tasks/files.

---

### TEMPLATE B: Normal Issue (Vertical Slice)
*Use for: Active builds. Must be deterministic.*
## Overview
One paragraph: Business value, no jargon. [AFK] or [HITL] in title.
## Current state / Problem
Reference current files:lines. Why it's broken/missing.
## Requirements / Steps (Tracer Bullet Flow)
- [ ] **Data Layer:** (Schema/RLS updates)
- [ ] **Logic Layer:** (Hooks/API/Functions)
- [ ] **UI Layer:** (Components/Loading states)
## Technical notes / Implementation
Specific files/schemas. Include SQL or Prompt snippets.
## Dependencies
- **[ID] first** (blocks/blocked-by).
## Notes
Edge cases, trade-offs, `_memory/LEARNINGS.md` traps.
## Acceptance criteria
- [ ] Feature is demoable end-to-end.
- [ ] [DONE] npm run build passes.