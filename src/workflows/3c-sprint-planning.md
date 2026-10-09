---
name: 3c-sprint-planning
description: "Sequence 10-day capacity block of leaf slices into GitHub sprint milestone. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "2.4.0"
timestamp: 2026-09-29
---

# Sprint planning

**Hand-off contract:** Assigns leaf slices to sprint milestone `vX.Y.Z` (Z ≥ 1). Reads active release `X.Y` from parent `vX.Y.0` release milestone; defaults to `v1.0`. Sprint planning owns Z. Never invent `X.Y`.

## Phase 0: Load Memory
Run the `load-memory` skill to restore session context (read-only).

## Phase 1: Context Intake & Triage Scan
1. Read `.memory/BACKLOG_MAP.md`.
2. Extract rows with `status != done`.
3. **Audit Strategy:**
   - Candidates: `tier:slice AND status:planned` plus **Template A** = `tier:slice AND status:needs_spec` (parked or high-uncertainty; `src/references/issue-templates.md`). Exclude epics (`tier:epic`), `concept:*` issues, and `scope:deferred`. Template A keeps `status:needs_spec`. **Never auto-flip `needs_spec → planned`** (that promotion is a deliberate re-spec, not a sprint-planning side effect).
   - Verify planned slices belong to current release `vX.Y`. If mismatches exist, flag and ask user. Template A outside `vX.Y`: skip silently, do not prompt.
   - Exclude and print `[NEEDS_SPEC] BT-<padded> - <title>` if a leaf issue (without `concept:*` label) lacks a BACKLOG_MAP entry or any of `type:`, `mode:`, `tier:slice`, and `size:` labels.

## Phase 2: Filter & Sort Engine
1. **Dependency Sorting:** Evaluate dependencies. Batch lookup native GitHub dependencies (e.g., `gh issue list --state open --json number,blockedBy`; read `blockedBy.nodes`) if supported to avoid individual queries; else parse text `Blocked by:` in issue body and the `Blocked by` column in `BACKLOG_MAP.md`.
   - A blocker already at `status:in review` or `status:done` counts as satisfied (not blocking) and should already be cleared from `Blocked by`; treat any stale entry as satisfied.
   - Set `[BLOCKED]` if prereqs not `done` and not in current sprint. `[BLOCKED]` items are listed but do not consume budget.
   - Set `[blocked-but-sequenced-in-sprint]` if prereqs not `done` but in current sprint.
   - **Late-discovered dependency:** if sequencing reveals a genuine prerequisite not yet recorded in a slice's `Blocked by` (a real ordering constraint missed at creation), flag it `[NEW-DEP] BT-<padded> ← BT-<prereq>`. Do **not** write it yet — it is proposed for HITL confirmation in Phase 5.
2. **ICE Prioritization:** Read pre-calculated ICE from `BACKLOG_MAP.md`. Recalculate ICE ONLY if empty or effort weight disagrees with label (ICE = (Impact * Confidence) / Effort weight; small=1, medium=2, large=3). **Template A skips ICE** (per 3b).
   - Sort, in order:
     1. `scope:baseline` before `scope:differentiator`.
     2. Within each scope, planned slices before Template A (so spec work cannot displace build work).
     3. Planned slices: ICE descending.
     4. Template A: `priority:` high → medium → low, then BT number ascending.
3. **Context Grouping:** Cluster by `area:xxx` to minimize context overhead.

## Phase 3: Capacity Calculation & Safeguards
*Max Sprint Budget = 10 engineering days (80 hours), shared by planned slices and Template A. Exclude parent issues and `[BLOCKED]` items.*
- **Weights:** `size:large` = 5h | `size:medium` = 3h | `size:small` = 45min (planned slices).
- **Template A:** flat 5h placeholder, regardless of `size:` (unknown spec and build effort).
- **AFK Check:** Flag planned leaf issues containing `size:large` and `mode:AFK`. Template A is not flagged.
- **Label Check:** Verify labels exist in registry.

## Phase 4: Sequence Proposal
Output compressed readout matching capacity thresholds:

```markdown
[TARGET SPRINT MILESTONE: <vX.Y.Z>]

- [AFK] BT-<padded> | <title> (<size>) | Area: <area> | Type: <type> | ICE Score: <score> | Priority Label: <priority>
- [HITL] BT-<padded> | <title> (<size>) | Area: <area> | Type: <type> | ICE Score: <score> | Priority Label: <priority>
- [TEMPLATE-A] BT-<padded> | <title> | 5h placeholder | Priority: <priority> | next: `1a-research` (type:research) or manual re-spec (other types)

[BUDGET] Build <X>h | Template A <Y>h | total <Z>/80h
⚠️ Template A is over 50% of the sprint (Y > 40h): the sprint is mostly spec work. Confirm before locking.

[CRITICAL ALERTS]
⚠️ WARNING: BT-<padded> is size:large but labeled mode:AFK. Confirm auto-execution!
🗒️ Note: BT-<padded> labeled as `[NEEDS_SPEC]` lacks required labels or a BACKLOG_MAP entry; fix before it can be sequenced.
🔗 New dependency: BT-<padded> should be `Blocked by` BT-<prereq> (late-discovered; confirm to record).
```
*Optional Fully-AFK Sprint Advisory:* If all sequenced planned slices are `mode:AFK`, display: *"Note: This sprint is fully-AFK (autonomous). Ensure proper verification hooks are configured."*

Verify labels in registry.

## Phase 5: Commit & Sync

Halt for confirmation. When confirmed:
1. Update issue priority (ICE >= 0.5 -> high, 0.15 <= ICE < 0.5 -> medium, ICE < 0.15 -> low) and milestone for planned slices. Template A: skip ICE and priority. Status handling is in step 2. If ICE recalculation shifted the priority band, mirror the new `priority:*` into the `BACKLOG_MAP.md` Labels column — it is gate-checked in step 5.
2. Create sprint milestone `vX.Y.Z` in GitHub if absent. Assign all sequenced items (planned slices and Template A), moving them from `vX.Y.0`. A Template A item already in an earlier sprint milestone and still `needs_spec` is moved to the new Z. Update Milestone column in `BACKLOG_MAP.md`. Refresh `generated.at` (and `generated.by`) on any `.memory/` document this step mutates. Set status to `status:planned` for planned slices only; **Template A keeps `status:needs_spec`** (never set `planned`). For Template A, the Labels cell must hold no `status:*` token; remove one if present before the gate.
3. **Record confirmed dependencies (amend-only, user-confirmed):** for each `[NEW-DEP]` the user confirmed at the halt, add the edge on GitHub (`addBlockedBy` mutation per `references/github-issue-relations.md`) and append the bare `BT-<prereq>` to that slice's `Blocked by` column in `BACKLOG_MAP.md`. 3c may only **add** a blocker edge here, and only with explicit confirmation — `3b` remains the birth writer for `Blocked by`, and blocker **clearing** stays with 4a (at `in review`) / 0b / merge. Never remove a `Blocked by` entry in 3c. Skip any proposed edge the user declined.
4. Comment on each updated issue: 'Sprint vX.Y.Z sync: ICE <score> → priority:<priority>; milestone vX.Y.Z; status:planned.' Template A: 'Sprint vX.Y.Z sync: Template A; milestone vX.Y.Z; status:needs_spec; next: <1a-research | manual re-spec>.'
5. **Terminal sync gate:** run `python .agents/scripts/reconcile.py --require-gh --ids <comma-list of all sequenced BT-<padded>, Template A included> --fields status,milestone,labels,blocked_by` per `references/terminal-sync-invariant.md`. Non-zero → heal per the reference and re-run, **at most 3 attempts**; still non-zero, or `[MIRROR-UNVERIFIED]` → halt and surface the drift. Never loop unbounded.
6. Output: 'Sprint vX.Y.Z locked. Run `/3d-implement-issue` to build.' If the sprint holds Template A items, add: 'Template A items in vX.Y.Z stay `needs_spec` and are not runnable by `/3z`: research spikes go to `1a-research`; others need a manual re-spec, after which a deliberate manual status change moves them to planned. Unfinished Template A items are re-sequenced by the next 3c run.'
