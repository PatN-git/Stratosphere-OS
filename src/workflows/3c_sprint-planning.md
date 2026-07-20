---
name: 3c_sprint-planning
description: Sequence 10-day capacity block of leaf slices into GitHub sprint milestone.
type: workflow HITL
trigger: manual
version: "2.1.0"
timestamp: 2026-07-17
---

# Sprint planning

**Hand-off contract:** Assigns leaf slices to sprint milestone `vX.Y.Z` (Z ≥ 1). Reads active release `X.Y` from parent `vX.Y.0` release milestone; defaults to `v1.0`. Sprint planning owns Z. Never invent `X.Y`.

## Phase 0: Load Memory
Run `.agents/skills/load-memory/SKILL.md` to restore session context (read-only).

## Phase 1: Context Intake & Triage Scan
1. Read `.memory/BACKLOG_MAP.md`.
2. Extract rows with `status != done`.
3. **Audit Strategy:**
   - Operate on `tier:slice AND status:planned` only. Exclude epics (`tier:epic`), `concept:*` issues, and `status:needs_spec` slices (Template A spikes — same exemption as `concept:*`). **Never auto-flip `needs_spec → planned`** (that promotion is a deliberate re-spec, not a sprint-planning side effect).
   - Verify all slices belong to current release `vX.Y`. If mismatches exist, flag and ask user.
   - Exclude and print `[NEEDS_SPEC] BT-<padded> - <title>` if leaf issue (without `concept:*` label) lacks BACKLOG_MAP entry, or lacks any of `type:`, `mode:`, `tier:slice`, and `size:` labels.
   - List leaf issues labeled `[NEEDS_SPEC]`.

## Phase 2: Filter & Sort Engine
1. **Dependency Sorting:** Evaluate dependencies. Parse native GitHub dependencies (`gh issue view <#> --json blockedBy`) if supported; else parse text `Blocked by:` in issue body and the `Blocked by` column in `BACKLOG_MAP.md`.
   - A blocker already at `status:in review` or `status:done` counts as satisfied (not blocking) and should already be cleared from `Blocked by`; treat any stale entry as satisfied.
   - Set `[BLOCKED]` if prereqs not `done` and not in current sprint.
   - Set `[blocked-but-sequenced-in-sprint]` if prereqs not `done` but in current sprint.
   - **Late-discovered dependency:** if sequencing reveals a genuine prerequisite not yet recorded in a slice's `Blocked by` (a real ordering constraint missed at creation), flag it `[NEW-DEP] BT-<padded> ← BT-<prereq>`. Do **not** write it yet — it is proposed for HITL confirmation in Phase 5.
2. **ICE Prioritization:** Read pre-calculated ICE from `BACKLOG_MAP.md`. Recalculate ICE ONLY if empty or effort weight disagrees with label (ICE = (Impact * Confidence) / Effort weight; small=1, medium=2, large=3).
   - Sort: `scope:baseline` first, then `scope:differentiator`. Within groups, sort by ICE descending.
3. **Context Grouping:** Cluster by `area:xxx` to minimize context overhead.

## Phase 3: Capacity Calculation & Safeguards
*Max Sprint Budget = 10 engineering days (80 hours). Exclude parent issues.*
- **Weights:** `size:large` = 12h | `size:medium` = 6h | `size:small` = 1h.
- **AFK Check:** Flag leaf issues containing `size:large` and `mode:AFK`.
- **Label Check:** Verify labels exist in registry.

## Phase 4: Sequence Proposal
Output compressed readout matching capacity thresholds:

```markdown
[TARGET SPRINT MILESTONE: <vX.Y.Z>]

- [AFK] BT-<padded> | <title> (<size>) | Area: <area> | Type: <type> | ICE Score: <score> | Priority Label: <priority>
- [HITL] BT-<padded> | <title> (<size>) | Area: <area> | Type: <type> | ICE Score: <score> | Priority Label: <priority>

[CRITICAL ALERTS]
⚠️ WARNING: BT-<padded> is size:large but labeled mode:AFK. Confirm auto-execution!
🗒️ Note: BT-<padded> labeled as `[NEEDS_SPEC]` needs to be enriched to be included in sprint planning.
🔗 New dependency: BT-<padded> should be `Blocked by` BT-<prereq> (late-discovered; confirm to record).
```
*Optional Fully-AFK Sprint Advisory:* If sequenced issues are entirely `mode:AFK`, display: *"Note: This sprint is fully-AFK (autonomous). Ensure proper verification hooks are configured."*

Verify labels in registry.

## Phase 5: Commit & Sync

Halt for confirmation. When confirmed:
1. Update issue priority (ICE >= 0.5 -> high, 0.15 <= ICE < 0.5 -> medium, ICE < 0.15 -> low), milestone, and status in GitHub.
2. Create sprint milestone `vX.Y.Z` in GitHub if absent. Assign leaf slices, moving them from `vX.Y.0`. Update Milestone column in `BACKLOG_MAP.md`. Set status to `status:planned`.
3. **Record confirmed dependencies (amend-only, user-confirmed):** for each `[NEW-DEP]` the user confirmed at the halt, add the edge on GitHub (`gh issue edit <n> --add-blocked-by <prereq>`) and append the bare `BT-<prereq>` to that slice's `Blocked by` column in `BACKLOG_MAP.md`. 3c may only **add** a blocker edge here, and only with explicit confirmation — `3b` remains the birth writer for `Blocked by`, and blocker **clearing** stays with 4a (at `in review`) / 0b / merge. Never remove a `Blocked by` entry in 3c. Skip any proposed edge the user declined.
4. Comment on each updated issue: 'Sprint vX.Y.Z sync: ICE <score> → priority:<priority>; milestone vX.Y.Z; status:planned.'
5. Output: 'Sprint vX.Y.Z locked. Run `/3d_implement-issue` to build.'