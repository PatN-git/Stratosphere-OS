---
name: 2b_ux-design
description: Design UX flows, interface hierarchy, and interaction requirements post-PRD and pre-slicing.
type: workflow HITL
trigger: User. Do not run autonomously.
---

# UX Design

**Hand-off contract:** Appends the path to `docs/design/BT-<n>-ux.md` (or Stitch prompt) to the parent GitHub Issue body and the `Ref` column of `.memory/BACKLOG_MAP.md`. Downstream workflow `/3c_implement-issue` reads this parent-level document for sub-issue implementation.

---

## Phase 1: Objectives & Scope
1. Load PRD from `docs/prds/BT-<n>-<feature>.md`.
2. Define the core user flows, states (empty, loading, error, success), and information architecture.

## Phase 2: Execution Path (Stitch vs. Manual)

Choose the execution path based on whether Google Stitch is used for this project:

### PATH A: Using Google Stitch
1. Generate structural component skeletons, user flows, and interaction rules.
2. **Output Artifact:** Write a structured **prompt** (Stitch Prompt) designed specifically to be copied and pasted into Stitch to generate the UI components based on your tokens.
3. Save this prompt in the parent issue body or as `docs/design/BT-<n>-ux.md`.

### PATH B: No Google Stitch
1. Define strict UI blueprints:
   - DOM hierarchy and component tree.
   - Spatial layout rules (e.g. flex/grid arrangements).
   - Responsive breakpoints.
2. **Output Artifact:** Create the file `docs/design/BT-<n>-ux.md`. This parent-level document covers the UX specs for all downstream slices.

## Phase 3: Publish & Sync
1. Append the reference path (`docs/design/BT-<n>-ux.md` or Stitch prompt reference) to the parent GitHub Issue body.
2. Append the design reference to the `Ref` column in `.memory/BACKLOG_MAP.md` alongside the PRD link.
3. Handoff to `/3a_create-issue`: *"UX Design completed. Run `/3a_create-issue` to slice requirements."*

---

## Archive Lifecycle
- Archive `docs/design/BT-<n>-ux.md` to `docs/design/archive/BT-<n>-ux.md` when the parent feature `BT-<n>` closes.
