---
name: 3c_sprint-planning
description: Sequence 10-day capacity block of leaf slices into GitHub sprint milestone.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "2.0.6"
timestamp: 2026-07-09
---

# Sprint planning

**Hand-off contract:** Assigns leaf slices to sprint milestone `vX.Y.Z` (Z ≥ 1). Reads active release `X.Y` from parent `vX.Y.0` release milestone; defaults to `v1.0`. Sprint planning owns Z. Never invent `X.Y`.

## Phase 1: Context Intake & Triage Scan
1. Read `.memory/BACKLOG_MAP.md`.
2. Extract rows with `status != done`.
3. **Audit Strategy:**
   - Map active GitHub issues. Set `status:planned` if missing. Exclude epics/parents (`size:large` with children). Exclude `concept:*` issues.
   - Verify all slices belong to current release `vX.Y`. If mismatches exist, flag and ask user.
   - Exclude and print `[NEEDS_SPEC] BT-<padded> - <title>` if leaf issue (without `concept:*` label) lacks BACKLOG_MAP entry or both `type:xxx` and `size:xxx` labels.
   - List leaf issues labeled `[NEEDS_SPEC]`.

## Phase 2: Filter & Sort Engine
1. **Dependency Sorting:** Evaluate dependencies. Parse native GitHub dependencies (`gh issue view <#> --json blockedBy`) if supported; else parse text `Blocked by:` in issue body and `Dependencies` column in `BACKLOG_MAP.md`.
   - Set `[BLOCKED]` if prereqs not `done` and not in current sprint.
   - Set `[blocked-but-sequenced-in-sprint]` if prereqs not `done` but in current sprint.
2. **ICE Prioritization:** Read pre-calculated ICE from `BACKLOG_MAP.md`. Recalculate ICE ONLY if empty or effort weight disagrees with label (ICE = (Impact * Confidence) / Effort weight; small=1, medium=2, large=3).
   - Sort: `scope:baseline` first, then `scope:differentiator`. Within groups, sort by ICE descending.
3. **Context Grouping:** Cluster by `area:xxx` to minimize context overhead.

## Phase 3: Capacity Calculation & Safeguards
*Max Sprint Budget = 10 engineering days (80 hours). Exclude parent issues.*
- **Weights:** `size:large` = 12h | `size:medium` = 6h | `size:small` = 1h.
- **AFK Check:** Flag leaf issues containing `size:large` and `type:AFK`.
- **Label Check:** Verify labels exist in registry.

## Phase 4: Sequence Proposal
Output compressed readout matching capacity thresholds:

```markdown
[TARGET SPRINT MILESTONE: <vX.Y.Z>]

- [AFK] BT-<padded> | <title> (<size>) | Area: <area> | Type: <type> | ICE Score: <score> | Priority Label: <priority>
- [HITL] BT-<padded> | <title> (<size>) | Area: <area> | Type: <type> | ICE Score: <score> | Priority Label: <priority>

[CRITICAL ALERTS]
⚠️ WARNING: BT-<padded> is size:large but labeled type:AFK. Confirm auto-execution!
🗒️ Note: BT-<padded> labeled as `[NEEDS_SPEC]` needs to be enriched to be included in sprint planning.
```
*Optional Fully-AFK Sprint Advisory:* If sequenced issues are entirely `type:AFK`, display: *"Note: This sprint is fully-AFK (autonomous). Ensure proper verification hooks are configured."*

Verify labels in registry.

## Phase 5: Commit & Sync

Halt for confirmation. When confirmed:
1. Update issue priority (ICE >= 0.5 -> high, 0.15 <= ICE < 0.5 -> medium, ICE < 0.15 -> low), milestone, and status in GitHub.
2. Create sprint milestone `vX.Y.Z` in GitHub if absent. Assign leaf slices, moving them from `vX.Y.0`. Update Milestone column in `BACKLOG_MAP.md`. Set status to `status:planned`.
3. Comment on each updated issue: 'Sprint vX.Y.Z sync: ICE <score> → priority:<priority>; milestone vX.Y.Z; status:planned.'
4. Output: 'Sprint vX.Y.Z locked. Run `/3d_implement-issue` to build.'