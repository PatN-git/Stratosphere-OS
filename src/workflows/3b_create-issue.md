---
name: 3b_create-issue
description: Standardize feature ideas into vertical slices with ICE prioritization.
type: workflow HITL
trigger: manual
version: "2.0.7"
timestamp: 2026-07-17
---

# Create issue

**Purpose:** Convert ideas into implementation-ready vertical slices synced with memory.

**Hand-off contract:** Upstream: `/3a_version-planning` gates current-release parent features to slice. Sourced from PRD → reads §1, §6, §7, §8 and coverage-checks against §6 + §8. Else checks against captured intent. Template A spikes skip coverage.

## Phase 1: Intake & Memory Audit
1. **Intake:** Receive raw idea or MVI.
2. **Memory Audit:** Run `/0a_start-session` if not done this session.
3. **Scope:** PRD-sourced → load `docs/prds/BT-<padded>-<name>.md` and frozen design doc `docs/design/BT-<padded>-interface.md`. Scope is PRD §6 + §8 and design blueprint. Else raw idea/MVI is scope.

## Phase 2: Vertical Slice Quiz & Prioritization
Propose breakdown to user:
1. **Slices List:**
   - **Title:** [Short name]
   - **Logic/user story:** end-to-end path.
   - **Blocked by:** prerequisite slices.
   - **Inheritance:** inherits scope-class and ODI score from PRD §6. No slices for `[DEFERRED]` stories.
2. **Prioritization Metrics (Template A spikes: skip):**
   - **Impact from ODI:** Map story ODI score to Impact:
     - `ODI < 5` → `0.25`
     - `5 <= ODI <= 8` → `0.5`
     - `9 <= ODI <= 12` → `1.0`
     - `13 <= ODI <= 16` → `2.0`
     - `17 <= ODI <= 20` → `3.0`
     - (Note: scope-class governs ordering; baseline sequenced before differentiator).
   - **Confidence from ODI:** Map story ODI confidence to Confidence:
     - `[HIGH]` → `100%`
     - `[MEDIUM]` → `80%`
     - `[LOW]` → `50%`
    - **Fallback (ODI absent):** Prompt user for Impact and Confidence:
      - **Impact:** ∈ {0.25 (min), 0.5 (low), 1.0 (med), 2.0 (high), 3.0 (crit)}
      - **Confidence:** ∈ {50% (guess), 80% (high), 100% (certain)}
   - Prompt for **Size** (Effort):
     - **Size:** ∈ {size:small (weight 1), size:medium (weight 2), size:large (weight 3)}
3. **Coverage Check (Template A spikes: skip):**
   - **PRD-sourced:** Invoke a Coverage Auditor subagent (via Antigravity `invoke_subagent` or Claude Code `Task` general-purpose). Input: proposed slice list (titles + Path/layer bullets) inline. Reads: `docs/prds/BT-<padded>-<name>.md` (§6 + §8) and, if present, `docs/design/BT-<padded>-interface.md` fresh from the file system. Guardrail: *"Report the coverage map only; do not create issues or edit any file."* Output Contract: return the coverage map only — map **every `[BASELINE]` and `[DIFFERENTIATOR]` §6 story, §8 DoD item, and design blueprint element** to its covering slice or `[UNCOVERED]`, walking the **journey-grouped** §6 stories. `[DEFERRED]` stories / §9 Out-of-Scope items are intentionally out and must be treated as covered/excluded (**not** `[UNCOVERED]`).
   - **Loop Optimization:** Re-spawn the Coverage Auditor *only* when the slice list materially changes (slices added / removed / re-scoped), not on cosmetic edits (renames, ICE tweaks).
   - **Resolution:** Gaps: uncovered → `[UNCOVERED]`; resolve (add slice, defer to §9, confirm out-of-scope, or "covered by construction"). Scope creep (hitting §4 Non-Goal / §9 Out-of-Scope) → `[SCOPE-CREEP]`. Blocker (open §10 Question) → Template A.
   - **No PRD:** restate intent as requirement list; map slices. Gaps → `[UNCOVERED?]` (soft) for user confirmation. No §-refs. Present the map with the slice list.
4. **Approval Request:**
   - Requirements & end-state covered (no `[UNCOVERED]`)?
   - Granularity right?
   - Dependencies correct?
   - Modes (mode:HITL/mode:AFK) correct?
   - ICE scores accurate?

Halt until user approves breakdown.

## Phase 3: Implementation & Memory Sync
1. **Calculate ICE Score (Template A spikes: skip):** `ICE = (Impact * Confidence) / Effort weight` (Confidence as decimal; Effort: small=1, medium=2, large=3).
2. **Determine Priority Label (Template A: skip):**
   - `ICE >= 0.5` → `priority:high`
   - `0.15 <= ICE < 0.5` → `priority:medium`
   - `ICE < 0.15` → `priority:low`
3. **Generate (Atomic Minting):** Execute `gh issue create`. Offline fallback: assign `BT-LOCAL-<n>`. **CRITICAL:** Capture exact returned issue number and zero-pad to 3 digits (e.g. `BT-059`). Never guess issue number; GitHub shares IDs across Issues and PRs. Write raw ICE metrics in issue body. Apply scope label (`scope:baseline` or `scope:differentiator`). Assign canonical labels: Primary Type (e.g. `type:feature`) + Execution Mode (`mode:HITL` or `mode:AFK`) + Tier (`tier:slice`) + Size (`size:small/medium/large`).
   - **Sub-issue Linkage:** If derived from parent epic (`#parent`), link sub-issue (`gh sub-issue add <parent> <N>`).
   - **Dependencies:** If supported, pass `--blocked-by` or run `gh issue edit <N> --add-blocked-by <ids>`. Maintain "Blocked by: [IDs]" in issue body and BACKLOG_MAP.
4. **Backlog Sync:** Append entry (`BT-<padded>`) to `.memory/BACKLOG_MAP.md` adhering to `[[memory-protocol.md#8-backlog-id-minting-late-binding]]` (first real entry: purge placeholders). Write bucketed priority, size, type, execution mode, tier, and scope label to Labels column, and ICE details to ICE. In Dependencies column, record `Sub-issue of BT-<parentPadded>` and sibling blockers. Set milestone to parent feature release `vX.Y.0` (default `v1.0.0`). sprint digit Z assigned by 3c.
5. **Hand-off:** Slices created. Run `/3c_sprint-planning` to sequence, or `/3d_implement-issue` for single ready slice.

---

## LABEL REGISTRY
Use registry in `.memory/BACKLOG_MAP.md`. Do not invent labels. If label missing: propose adding to BACKLOG_MAP registry, await confirmation, create in GitHub, write to registry, then apply.

## Issue Templates
Follow canonical templates in `.agents/workflows/.reference/issue-templates.md`.