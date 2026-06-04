---
name: 3a_create-issue
description: Standardize feature ideas into "Implementation-Ready" vertical slices.
---

# SKILL: Create issue

**Purpose:** Convert (raw) ideas into deterministic, "Implementation-Ready" vertical slices while maintaining absolute sync with the project's memory layer.

**Hand-off contract:** When sourced from a PRD (`BT-<n>` doc in `.memory/BACKLOG_MAP.md`), reads §1/§6/§7/§8 and coverage-checks slices against §6 + §8 (Phase 2). No PRD → checks against captured intent. Template A spikes skip coverage.

## Phase 1: Intake & Memory Audit
1.  **Intake:** Receive raw idea or "Minimum Viable Issue."
2.  **Memory Audit:** If not done before in session run `/0a_start-session` first to familiarize with the project state and architecture.
3.  **Scope source:** PRD-sourced (a `.memory/BACKLOG_MAP.md` row links `docs/prds/BT-<n>-<name>.md`, or user cites `BT-<n>`) → load it; §6 + §8 are the scope to cover. Else the raw idea / MVI is the scope.

## Phase 2: The Vertical Slice Quiz
Before creating the task, propose the breakdown to the user:
1.  **Numbered List of Slices:**
    -   **Title:** [Short name]
    -   **Logic/user story:** Why is this a vertical slice? (Briefly explain the end-to-end path).
    -   **Blocked by:** [IDs of prerequisite slices]
2.  **Coverage Check** (Template A spikes: skip):
    -   **PRD-sourced:** map every §6 User Story + §8 Definition-of-Done item to ≥1 slice. Flag gaps:
        -   uncovered item → `[UNCOVERED]`; resolve: add slice / defer to §9 / confirm out-of-scope.
        -   slice hitting a §4 Non-Goal or §9 Out-of-Scope item → `[SCOPE-CREEP]`.
        -   slice blocked by an open §10 Question → Template A (spike), not B.
    -   **No PRD:** restate captured intent as a requirement list; map slices to it. Gaps → `[UNCOVERED?]` (soft) for user confirmation. No §-refs.
    -   Present the map with the slice list.
3.  **Approval Request:**
    -   Is every requirement & end-state covered (no `[UNCOVERED]`)?
    -   Does the granularity feel right? (Too coarse / too fine)
    -   Are the dependency relationships correct?
    -   Are the correct slices marked as `type:HITL` (Human-in-Loop) and `type:AFK` (Autonomous)?

*Stop and iterate until the user approves the breakdown.*

## Phase 3: Implementation & Memory Sync
1.  **Generate:** Create the issue in GitHub (if connected, otherwise in local task list) applying the appropriate template below.
2.  **Backlog Sync:** **Immediately** append the entry to `.memory/BACKLOG_MAP.md` using the registry-compliant format.

---

## LABEL REGISTRY
Use the registry in `.memory/BACKLOG_MAP.md`. Do not invent labels — ask user first if one seems genuinely needed.

**If a required label does not exist in GitHub yet:** STOP before creating the issue. Surface the gap clearly:
```
Label gap detected: `<label-name>` is in the registry but not in GitHub.
Options:
  a) Create the label in GitHub now, then proceed.
  b) Use the nearest existing GitHub label with a `// pending` note in the issue body.
```
Await user choice. Never silently apply a label that doesn't exist in GitHub.

---

### TEMPLATE A: Discovery & Spikes
*Use for: Rapid capture, "parking" vibes, or high-uncertainty research. always label as `type:NEEDS_SPEC`*
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
- One paragraph: Business value, no jargon.
- **Mental Model:** 2-3 bullets on core logic or specific question to answer.
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
- **[[ID]] first** (blocks/blocked-by).
## Notes
Edge cases, trade-offs, and `.memory/LEARNINGS.md` traps.