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
   - Candidates: `tier:slice AND status:planned|needs_spec`, excluding `concept:*` and `scope:deferred`. A `needs_spec` slice is a Spike (`references/issue-templates.md`): closed on its Exit Criteria, follow-up minted via `/3b-create-issue`. **Never flip `needs_spec → planned`.**
   - Verify Build slices belong to current release `vX.Y`. If mismatches exist, flag and ask user. Spike outside `vX.Y` (incl. legacy milestone `—`): list as `[SPIKE-UNSCHEDULED] BT-<padded>` (set milestone `vX.Y.0` to schedule); do not sequence it.
   - Exclude and print `[MISSING-LABELS] BT-<padded> - <title>` if a leaf issue (without `concept:*` label) lacks a BACKLOG_MAP entry or a required label: `type:`, `mode:`, `tier:slice`, `size:`.

## Phase 2: Filter & Sort Engine
1. **Dependency Sorting:** Evaluate dependencies. Batch lookup native GitHub dependencies (e.g., `gh issue list --state open --json number,blockedBy`; read `blockedBy.nodes`) if supported to avoid individual queries; else parse text `Blocked by:` in issue body and the `Blocked by` column in `BACKLOG_MAP.md`.
   - A blocker already at `status:in review` or `status:done` counts as satisfied (not blocking) and should already be cleared from `Blocked by`; treat any stale entry as satisfied.
   - Set `[BLOCKED]` if prereqs not `done` and not in current sprint.
   - Set `[blocked-but-sequenced-in-sprint]` if prereqs not `done` but in current sprint.
   - **Late-discovered dependency:** if sequencing reveals a genuine prerequisite not yet recorded in a slice's `Blocked by` (a real ordering constraint missed at creation), flag it `[NEW-DEP] BT-<padded> ← BT-<prereq>`. Do **not** write it yet — it is proposed for HITL confirmation in Phase 5.
2. **ICE Prioritization:** Read pre-calculated ICE from `BACKLOG_MAP.md`. Recalculate ICE ONLY if empty or effort weight disagrees with label (ICE = (Impact * Confidence) / Effort weight; small=1, medium=2, large=3). **Spikes skip ICE** (per 3b).
   - Sort, in order:
     1. `scope:baseline` before `scope:differentiator`; unlabelled scope last.
     2. Within each scope, a blocker precedes its dependents (Spike or not); otherwise Build slices before Spikes.
     3. Build slices: ICE descending.
     4. Spikes: BT number ascending.
3. **Context Grouping:** Cluster by `area:xxx` to minimize context overhead.

## Phase 3: Capacity Calculation & Safeguards
*Max Sprint Budget = 10 engineering days (80 hours). Exclude parent issues and `[BLOCKED]` items (listed, not budgeted). Fill in sort order until the next item exceeds 80h; list the rest as `[NEXT]`.*
- **Weights (all leaves):** `size:large` = 5h | `size:medium` = 3h | `size:small` = 45min. Spikes are always `size:medium`.
- **Spikes:** `size:medium` (3h), like any leaf.
- **AFK Check:** Flag leaves containing `size:large` and `mode:AFK`.
- **Label Check:** Verify labels exist in registry.

## Phase 4: Sequence Proposal
Output compressed readout matching capacity thresholds:

```markdown
[TARGET SPRINT MILESTONE: <vX.Y.Z>]

- [AFK] BT-<padded> | <title> (<size>) | Area: <area> | Type: <type> | ICE Score: <score> | Priority Label: <priority>
- [HITL] BT-<padded> | <title> (<size>) | Area: <area> | Type: <type> | ICE Score: <score> | Priority Label: <priority>
- [SPIKE] BT-<padded> | <title> | (<size>) | close on Exit Criteria; follow-up via /3b
- [NEXT] BT-<padded> | <title> (<size>) | over budget; next sprint

[BUDGET] Build <b>h | Spike <s>h | total <t>/80h

[CRITICAL ALERTS]
⚠️ WARNING: BT-<padded> is size:large but labeled mode:AFK. Confirm auto-execution!
🗒️ Note: BT-<padded> labeled as `[MISSING-LABELS]` lacks required labels or a BACKLOG_MAP entry; fix before it can be sequenced.
🔗 New dependency: BT-<padded> should be `Blocked by` BT-<prereq> (late-discovered; confirm to record).
```
*Optional Fully-AFK Sprint Advisory:* If all sequenced Build slices are `mode:AFK`, display: *"Note: This sprint is fully-AFK (autonomous). Ensure proper verification hooks are configured."*

## Phase 5: Commit & Sync

Halt for confirmation. When confirmed:
1. **Build slices only:** update priority (ICE >= 0.5 -> high, 0.15 <= ICE < 0.5 -> medium, ICE < 0.15 -> low). If ICE recalculation shifted the band, mirror the new `priority:*` into the `BACKLOG_MAP.md` Labels column — it is gate-checked in step 5.
2. Create sprint milestone `vX.Y.Z` in GitHub if absent, then assign every sequenced item (Build slices and Spikes; not `[NEXT]` or `[BLOCKED]`) to it, moving it from `vX.Y.0` or an earlier sprint milestone. Update Milestone column in `BACKLOG_MAP.md`. Refresh `generated.at` (and `generated.by`) on any `.memory/` document this step mutates. Set status to `status:planned` for Build slices only; **Spikes keep `status:needs_spec`** (never set `planned`).
3. **Record confirmed dependencies (amend-only, user-confirmed):** for each `[NEW-DEP]` the user confirmed at the halt, add the edge on GitHub (`addBlockedBy` mutation per `references/github-issue-relations.md`) and append the bare `BT-<prereq>` to that slice's `Blocked by` column in `BACKLOG_MAP.md`. 3c may only **add** a blocker edge here, and only with explicit confirmation — `3b` remains the birth writer for `Blocked by`, and blocker **clearing** stays with 4a (at `in review`) / 0b / merge. Never remove a `Blocked by` entry in 3c. Skip any proposed edge the user declined.
4. Comment on each updated issue: 'Sprint vX.Y.Z sync: ICE <score> → priority:<priority>; milestone vX.Y.Z; status:planned.' Spike: 'Sprint vX.Y.Z sync: Spike; milestone vX.Y.Z; status:needs_spec; close on Exit Criteria.'
5. **Terminal sync gate:** run `python .agents/scripts/reconcile.py --require-gh --ids <comma-list of all sequenced BT-<padded>, Spikes included> --fields status,milestone,labels,blocked_by` per `references/terminal-sync-invariant.md`. Non-zero → heal per the reference and re-run, **at most 3 attempts**; still non-zero, or `[MIRROR-UNVERIFIED]` → halt and surface the drift. Never loop unbounded.
6. Output: 'Sprint vX.Y.Z locked. Build slices: `/3d-implement-issue` or `/3z-afk-loop`.' If the sprint holds Spikes, add: 'Spikes in vX.Y.Z stay `needs_spec` and are not runnable by `/3d`, `/3z`, or `/3x`. Close each on its Exit Criteria; mint follow-up Build slices with `/3b-create-issue`. Unfinished Spikes are re-sequenced by the next 3c run.'
