---
name: 3b_sprint-planning
description: Scans BACKLOG_MAP & GitHub, filters by dependencies/priority, sequences a 10-day capacity block into GitHub phases.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.0"
---

# Sprint planning

**Hand-off contract:** Modifies `.memory/BACKLOG_MAP.md` and assigns GitHub issues to a milestone in format `x.yy` (`x` = version, `yy` = sprint). The sprint digit `yy` is assigned here. The release digit `x` represents the active release version and defaults to `1` unless deliberately set by the parked `3x_version-planning` workflow (i.e. skipping `3x` implies `x = 1`, resulting in `1.yy` milestones).


## Phase 1: Context Intake & Triage Scan
1. Read `.memory/BACKLOG_MAP.md` if not already loaded.
2. Extract rows where `status != done`.
3. **Audit Strategy:**
   - Map matching active GitHub issues. Every selected issue must carry a `status:` label; if missing, add `status:planned` before sequencing. Exclude parent issues (defined as any `size:large` issue that has sub-issues/slices in the backlog).
   - If a leaf/non-parent GitHub issue lacks an entry in `BACKLOG_MAP.md` or lacks both `type:xxx` and `size:xxx` labels → immediately exclude and print: `[NEEDS_SPEC] BT-<padded> - <title>`.
   - List all existing leaf issues labeled as `[NEEDS_SPEC]` to surface to user.

## Phase 2: Filter & Sort Engine
1. **Dependency Sorting:** Evaluate dependency chains (`Blocked by`).
   - If prerequisites are not `status: done` AND are NOT being planned/sequenced in this same sprint → tag candidate item `[BLOCKED]`.
   - If prerequisites are NOT `status: done` BUT they are selected/sequenced in this exact sprint → tag as `[blocked-but-sequenced-in-sprint]`.
2. **ICE Prioritization:** Read the pre-calculated ICE score directly from the `ICE` column in `.memory/BACKLOG_MAP.md`.
   - Recalculate the ICE score ONLY IF the ICE cell is empty, OR the size label (e.g. `size:medium`) disagrees with the Effort weight used in the table calculation (`ICE = (Impact * Confidence) / Effort weight` where Effort weight is small=1, medium=2, large=3).
   - Sort and sequence candidate items by their `scope:*` label: `scope:baseline` first (for MVP end-to-end), then `scope:differentiator`. Within each scope group, sort items by their ICE score in descending order.

3. **Context Grouping:** Cluster sequenced tasks matching identical `area:xxx` tags to compress token burn overhead.

## Phase 3: Capacity Calculation & Safeguards
*Max Sprint Budget = 10 engineering days (80 hours total). Exclude parent issues from capacity totals.*
- **Cost Weights:** `size:large` = 12 hours | `size:medium` = 6 hours | `size:small` = 1 hour.
- **Guardrail Protocol:** Identify all leaf issues containing BOTH `size:large` and `type:AFK`. Flag these items explicitly asking for confirmation.
- **Label Validation:** Just-in-time check that any labels to be applied or synced exist in the `.memory/BACKLOG_MAP.md ## Label Registry`.

## Phase 4: Sequence Proposal
Output a compressed structural readout of items matching capacity thresholds and an explicit order if needed:

```markdown
[TARGET SPRINT MILESTONE: <x.yy>]

- [AFK] BT-<padded> | <title> (<size>) | Area: <area> | Type: <type> | ICE Score: <score> | Priority Label: <priority>
- [HITL] BT-<padded> | <title> (<size>) | Area: <area> | Type: <type> | ICE Score: <score> | Priority Label: <priority>

[CRITICAL ALERTS]
⚠️ WARNING: BT-<padded> is size:large but labeled type:AFK. Confirm auto-execution!
🗒️ Note: BT-<padded> labeled as `[NEEDS_SPEC]` needs to be enriched to be included in sprint planning.
```
*Optional Fully-AFK Sprint Advisory:* If the sequenced issues are entirely `type:AFK`, display: *"Note: This sprint is fully-AFK (autonomous). Ensure proper verification hooks are configured."*

Verify all milestone and priority labels to be set exist in the registry before promoting.

## Phase 5: Commit & Sync

Halt execution. Prompt user for confirmation. When confirmed:
1. Update issue metadata directly inside GitHub. Ensure the label registry's `priority:high|medium|low` bucket is correctly applied based on the ICE score (ICE >= 0.5 -> high, 0.15 <= ICE < 0.5 -> medium, ICE < 0.15 -> low).
2. Ensure milestone <x.yy> exists, assign matching issues, set status:planned inside .memory/BACKLOG_MAP.md and GitHub.
3. When changing any issue's priority/milestone/status in GitHub, post a comment on that issue documenting the change and its rationale, e.g.: *'Sprint <x.yy> sync: ICE <score> → priority:high; milestone <x.yy>; status:planned.'* (Mirrors 0b's issue-comment pattern so GitHub history explains every label/milestone change.)
4. Output termination note: Sprint <x.yy> locked. Ready for execution.