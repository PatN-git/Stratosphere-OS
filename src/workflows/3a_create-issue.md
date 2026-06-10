---
name: 3a_create-issue
description: Standardize feature ideas into "Implementation-Ready" vertical slices with ICE prioritization.
type: workflow HITL
trigger: User. Do not run autonomously.
---

# Create issue

**Purpose:** Convert (raw) ideas into deterministic, "Implementation-Ready" vertical slices while maintaining absolute sync with the project's memory layer.

**Hand-off contract:** When sourced from a PRD (`BT-<n>` doc in `.memory/BACKLOG_MAP.md`), reads §1/§6/§7/§8 and coverage-checks slices against §6 + §8 (Phase 2). No PRD → checks against captured intent. Template A spikes skip coverage.

## Phase 1: Intake & Memory Audit
1.  **Intake:** Receive raw idea or "Minimum Viable Issue."
2.  **Memory Audit:** If not done before in session run `/0a_start-session` first to familiarize with the project state and architecture.
3.  **Scope source:** PRD-sourced (a `.memory/BACKLOG_MAP.md` row links `docs/prds/BT-<padded>-<name>.md`, or user cites `BT-<padded>`) → load it along with the frozen design document `docs/design/BT-<padded>-interface.md`. The PRD §6 + §8 and the design blueprint/contract are the scope to cover. Else the raw idea / MVI is the scope.

## Phase 2: The Vertical Slice Quiz & Prioritization
Before creating the task, propose the breakdown to the user:
1.  **Numbered List of Slices:**
    -   **Title:** [Short name]
    -   **Logic/user story:** Why is this a vertical slice? (Briefly explain the end-to-end path).
    -   **Blocked by:** [IDs of prerequisite slices]
2.  **Prioritization Metrics (Template A spikes: skip):**
    -   Prompt for **Impact**, **Confidence**, and **Size** (Effort) based on these fixed scales:
        -   **Impact:** ∈ {0.25 (minimal), 0.5 (low), 1.0 (medium), 2.0 (high), 3.0 (critical)}
        -   **Confidence:** ∈ {50% (guess/speculative), 80% (high confidence/known implementation), 100% (absolute certainty/trivial)}
        -   **Size:** ∈ {size:small (Effort weight = 1, ~1h capacity), size:medium (Effort weight = 2, ~6h capacity), size:large (Effort weight = 3, ~12h capacity)}
3.  **Coverage Check** (Template A spikes: skip):
    -   **PRD-sourced:** map every §6 User Story + §8 Definition-of-Done item + Design Blueprint elements to ≥1 slice. Flag gaps:
        -   uncovered item → `[UNCOVERED]`; resolve: add slice / defer to §9 / confirm out-of-scope / mark "covered by construction" (e.g. framework-provided or built into an existing library/primitive).
        -   slice hitting a §4 Non-Goal or §9 Out-of-Scope item → `[SCOPE-CREEP]`.
        -   slice blocked by an open §10 Question → Enforce Template A (spike) rather than Template B if the question blocks implementation.
    -   **No PRD:** restate captured intent as a requirement list; map slices to it. Gaps → `[UNCOVERED?]` (soft) for user confirmation. No §-refs.
    -   Present the map with the slice list.
4.  **Approval Request:**
    -   Is every requirement & end-state covered (no `[UNCOVERED]`)?
    -   Does the granularity feel right? (Too coarse / too fine)
    -   Are the dependency relationships correct?
    -   Are the correct slices marked as `type:HITL` (Human-in-Loop) and `type:AFK` (Autonomous)?
    -   Are the Impact and Confidence scores accurate?

*Stop and iterate until the user approves the breakdown.*

## Phase 3: Implementation & Memory Sync
1.  **Calculate ICE Score (Template A spikes: skip):** Compute `ICE = (Impact * Confidence) / Effort weight` (where Confidence is converted to a decimal: 50% = 0.5, 80% = 0.8, 100% = 1.0; Effort weight is small=1, medium=2, large=3).
2.  **Determine Priority Label (Template A spikes: skip):** Bucket the raw ICE score into a standard controlled label:
    -   **ICE >= 0.5:** `priority:high`
    -   **0.15 <= ICE < 0.5:** `priority:medium`
    -   **ICE < 0.15:** `priority:low`
3.  **Generate:** Create the issue in GitHub (if connected, otherwise in local task list) applying the appropriate template below. Write the raw `ICE`, `Impact`, and `Confidence` inputs directly into the issue body.
4.  **Backlog Sync:** **Immediately** append the entry to `.memory/BACKLOG_MAP.md` using the registry-compliant format. Write the bucketed priority label (e.g. `priority:medium`) to the Labels column, and the raw ICE details (e.g., `ICE: 0.27 (I: 2.0, C: 80%)`) to the ICE column. (If this is the first real entry, perform the example purge to clean BACKLOG_MAP.md of placeholders).

---

## LABEL REGISTRY
Use the registry in `.memory/BACKLOG_MAP.md` as the single source of truth. Always perform a just-in-time check to ensure any label to be applied is defined in the registry.

**If a label is not in the registry:** STOP and do the following:
1. Propose adding it to the `.memory/BACKLOG_MAP.md ## Label Registry`.
2. Await user confirmation.
3. Once approved, create the label in GitHub first, then write it to the registry, and then apply it to the issue.

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
## ICE Priorities
- **Impact:** [Value]
- **Confidence:** [Value]
- **ICE Score:** [Calculated Score]
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