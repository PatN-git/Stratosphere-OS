---
name: 3c-sprint-planning
description: "Sequence 10-day capacity block of leaf slices into GitHub sprint milestone. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "2.9.0"
timestamp: 2026-11-10
---

# Sprint planning

**Hand-off contract:** Writes sprint milestone `vX.Y.Z` (Z ≥ 1) on leaf slices. Read by: `/3z-afk-loop`.

## Phase 0: Load Memory
Run the `load-memory` skill to restore session context (read-only).

## Phase 1: Context Intake & Triage Scan
1. Read the candidates: `python .agents/scripts/ice_read.py candidates` (the `candidates` read, `.agents/scripts/tracker.py`: scoped, open issues only, ICE already computed; both backends; local backend: the user may reorder statuses on `issues.py board --web`, apply the pasted payload with `issues.py apply-moves`).
2. **Audit Strategy:**
   - Candidates: `tier:slice AND status:planned|needs_spec`, excluding `concept:*` and `scope:deferred`. `needs_spec` slices are Spikes (definition: `references/issue-templates.md`). **Never flip `needs_spec → planned`.**
   - Verify Build slices belong to current release `vX.Y` (read from the parent `vX.Y.0` milestone; default `v1.0`; never invent `X.Y` — 3c owns only Z). If mismatches exist, flag and ask user. Spike outside `vX.Y` (incl. legacy milestone `—`): list as `[SPIKE-UNSCHEDULED] BT-<padded>` (set milestone `vX.Y.0` to schedule); do not sequence it.
   - Exclude and print `[MISSING-LABELS] BT-<padded> - <title>` if a leaf issue (without `concept:*` label) lacks a required label: `type:`, `mode:`, `tier:slice`, `size:` (`ice_read.py` prints these lines).

## Phase 2: Filter & Sort Engine
1. **Dependency Sorting:** Evaluate dependencies. If GitHub has no native dependencies, parse the text `Blocked by:` in the issue body.
   - Run `python .agents/scripts/reconcile.py --edges blockers --ids <candidate slices>` once (one batched read); effective blockers include the parent epic's. `[BLOCKER-OK]` is not blocking.
   - **Deterministic DAG Validation:** Reject Self-Consistency path voting or stochastic permutations. Validate sprint dependency acyclicity and execution sequence via `cat .tmp/3c-edges.txt | python .agents/scripts/reconcile.py --topo-sort` (or stdin). If a cycle is detected (`[CYCLE-DETECTED ...]`), halt immediately and notify user. Valid order (`[TOPO-ORDER ...]`) establishes strict dependency sequence in <5ms.
   - Set `[BLOCKED]` on `[BLOCKER-UNMET]`/`[BLOCKER-UNKNOWN]` when the blocker is not in the current sprint.
   - Set `[blocked-but-sequenced-in-sprint]` on the same when the blocker is in the current sprint.
   - **Late-discovered dependency:** if sequencing reveals a genuine prerequisite not yet recorded in a slice's `Blocked by` (a real ordering constraint missed at creation), flag it `[NEW-DEP] BT-<padded> ← BT-<prereq>`. Do **not** write it yet — it is proposed for HITL confirmation in Phase 5.
2. **ICE Prioritization:** Take ICE from the `candidates` output (computed on read from the body's Impact and Confidence and the `size:` label). Recalculate ICE ONLY if empty or effort weight disagrees with label (ICE = (Impact * Confidence) / Effort weight; small=1, medium=2, large=3). **Spikes skip ICE** (per 3b).
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
- **Label Check:** Verify labels exist in registry; list each `priority:*` band Phase 5 step 1 will set that is missing (github: `ensure_label` there, after the user confirms; local: `priority:*` needs none).

## Phase 4: Sequence Proposal & Consolidated Verification Gate
Output compressed readout matching capacity thresholds, displaying all alerts and warnings inline directly within the topological sequence table:

```markdown
[TARGET SPRINT MILESTONE: <vX.Y.Z>]

### Topological Sprint Sequence & Verification Gate
| Seq | Mode | Issue | Title (Size) | Area | Type | ICE | Priority | Inline Warnings & Notes |
|:---:|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|
| 1 | AFK | BT-<padded> | <title> (<size>) | <area or —> | <type> | <score> | <priority> | — |
| 2 | AFK | BT-<padded> | <title> (<size>) | <area or —> | <type> | <score> | <priority> | ⚠️ WARN: size:large on mode:AFK |
| 3 | HITL | BT-<padded> | <title> (<size>) | <area or —> | <type> | <score> | <priority> | 🔗 NEW-DEP: Blocked by BT-<prereq> |
| 4 | HITL | BT-<padded> | <title> (med) | <area or —> | spike | — | — | [SPIKE] close on Exit Criteria |
| — | — | BT-<padded> | <title> (<size>) | <area or —> | <type> | <score> | <priority> | [NEXT] Over budget; next sprint |

[BUDGET] Build <b>h | Spike <s>h | total <t>/80h

Prompt: `[Activate Sprint Queue] / [Edit Queue]`
```

Prompt user via native question tool (`ask_question` on Antigravity; `AskUserQuestion` on Claude Code) with options `["(Recommended) Activate Sprint Queue", "Edit Queue", "Abort"]`. If native question tools are unavailable in the host, output `[Activate Sprint Queue] / [Edit Queue]` in markdown and halt for user response.

*Optional Fully-AFK Sprint Advisory:* If all sequenced Build slices are `mode:AFK`, display: *"Note: This sprint is fully-AFK (autonomous). Ensure proper verification hooks are configured."*

## Phase 5: Commit & Sync

Single activation confirmation authorizes sequence, priority updates, milestone assignment, and dependency recording in one atomic execution:
1. **Build slices only:** update priority (ICE >= 0.5 -> high, 0.15 <= ICE < 0.5 -> medium, ICE < 0.15 -> low). If ICE recalculation shifted the band, github: `ensure_label` the new `priority:*` first when the registry lacks it (user confirms; GitHub rejects an unknown label); local: `priority:*` needs none; then `set_labels` it in place of the old one (`.agents/scripts/tracker.py`) — it is gate-checked in step 5.
2. `ensure_milestone` `vX.Y.Z`, then `set_milestone` on every sequenced item (Build slices and Spikes; not `[NEXT]` or `[BLOCKED]`), moving it from `vX.Y.0` or an earlier sprint milestone. Refresh `generated.at` (and `generated.by`) on any `.memory/` document this step mutates. `set_status` `planned` for Build slices only; **Spikes keep `status:needs_spec`** (never set `planned`).
3. **Record confirmed dependencies (add-only):** for each `[NEW-DEP]` the user confirmed at the halt, `add_blocker` (`.agents/scripts/tracker.py`). 3c only adds, only on explicit confirmation (`3b` births `Blocked by`; clearing is 4a at ship / 0b at merge); never remove an entry. Skip declined edges.
4. Comment on each updated issue: 'Sprint vX.Y.Z sync: ICE <score> → priority:<priority>; milestone vX.Y.Z; status:planned.' Spike: 'Sprint vX.Y.Z sync: Spike; milestone vX.Y.Z; status:needs_spec; close on Exit Criteria.'
5. **Terminal sync gate** (`references/terminal-sync-invariant.md`), over all sequenced `BT-<padded>`, Spikes included:
   - As steps 1-3 land, write the intended end state to `.tmp/3c-expect.txt`, one line per field (`BT-<n>:status=planned`, or `status=needs_spec` for a Spike; `BT-<n>:milestone=vX.Y.Z`, `BT-<n>:labels=<its full non-status label set>`, `BT-<n>:blocked_by=<its full blocker set>`), then run `python .agents/scripts/reconcile.py --ids <comma-list> --expect-file .tmp/3c-expect.txt`.
   - Non-zero → re-apply the missing write and re-run, **at most 3 attempts**; still non-zero, or `[GH-UNAVAILABLE]` (exit 3) → halt and surface the drift. Never loop unbounded.
6. Output: 'Sprint vX.Y.Z locked. Build slices: `/3d-implement-issue` or `/3z-afk-loop`.' If the sprint holds Spikes, add: 'Spikes in vX.Y.Z stay `needs_spec` and are not runnable by `/3d` or `/3z`. Close each on its Exit Criteria; mint follow-up Build slices with `/3b-create-issue`. Unfinished Spikes are re-sequenced by the next 3c run.'
