---
description: Standardize feature ideas into "Implementation-Ready" vertical slices and update the project memory layer.
---

# SKILL: Task Specification & Creation

**Purpose:** Convert (raw) ideas into deterministic, "Implementation-Ready" vertical slices while maintaining absolute sync with the project's memory layer.

## Phase 1: Intake & Memory Audit
1.  **Intake:** Receive raw idea or "Minimum Viable Issue."
1.  **Memory Audit:** If not done before in session run `/start-session` first to familiarize with the project state and architecture.

## Phase 2: The Vertical Slice Quiz
Before creating the task, propose the breakdown to the user:
1.  **Numbered List of Slices:**
    -   **Title:** [Short name]
    -   **Logic/user story:** Why is this a vertical slice? (Briefly explain the end-to-end path).
    -   **Blocked by:** [IDs of prerequisite slices]
2.  **Approval Request:**
    -   Does the granularity feel right? (Too coarse / too fine)
    -   Are the dependency relationships correct?
    -   Are the correct slices marked as `type:hitl` (Human-in-Loop) and `type:afk` (Autonomous)?

*Stop and iterate until the user approves the breakdown.*

## Phase 3: Implementation & Memory Sync
1.  **Generate:** Create the issue in GitHub (if connected, otherwise in local task list) applying the appropriate template below.
2.  **Backlog Sync:** **Immediately** append the entry to `_memory/BACKLOG_MAP.md` using the registry-compliant format.

---

## LABEL REGISTRY
Use these exact labels. Do not invent new ones (always ask user first if critically needed). If Backlog section within `_memory/BACKLOG_MAP.md`is empty verfiy the areas with user and update the label registry accordingly.

- **Area (`area:xxx`)**: `admin`, `ai`, `api`, `auth`, `company`, `data`, `infrastructure`, `jobs`, `map`, `submit-form`, `ux`
- **Type (`type:xxx`)**: `bug`, `content`, `feature`, `improvement`, `maintenance`, `research`, `hitl`, `afk`
- **Priority (`priority:xxx`)**: `high` (Must have), `medium` (Important), `low` (Nice to have)
- **Size (`size:xxx`)**: `large` (Architectural: Multi-feature/major schema), `medium` (Vertical: Standard Data/Logic/UI slice), `small` (Surgical: Local/Single-file)
- **Status (`status:xxx`)**: `planned`, `in progress`, `done`
- **Phase (`phase:xxx`)**: `v0.5`, `v0.8``v1`, `v2`

---

### TEMPLATE A: Discovery & Spikes
*Use for: Rapid capture, "parking" vibes, or high-uncertainty research.*
## Overview
- One sentence: what and why.
- **Mental Model:** 2-3 bullets on core logic or specific question to answer.
## Dependencies
- Relation to existing tasks/files.
## Blockers
- What must be resolved before this can move to a Vertical Slice (Template B)?

---

### TEMPLATE B: Normal Issue (Vertical Slice)
*Use for: Active builds. Must be deterministic.*
## Overview
One paragraph: Business value, no jargon.
## Current state / Problem
Reference current `files:lines`. Why it's broken or missing.
## The Path (Vertical Slice Flow)
- [ ] **Data Layer:** (Schema/RLS updates, Validations)
- [ ] **Logic Layer:** (Hooks/API/Functions/Shared Business Logic)
- [ ] **UI Layer:** (Components/Loading states/Error handling)
## Acceptance Criteria (Verifiable)
- [ ] **Verification:** [Specific test/run command]
- [ ] Feature is demoable end-to-end.
## Dependencies
- **[ID] first** (blocks/blocked-by).
## Notes
Edge cases, trade-offs, and `_memory/LEARNINGS.md` traps.