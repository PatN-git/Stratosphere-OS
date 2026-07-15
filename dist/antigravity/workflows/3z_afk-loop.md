---
name: 3z_afk-loop
description: Autonomous end-to-end runner for mode:AFK slices — chains 0a→3d→4a→0b across one slice or a sprint queue via isolated subagent sessions, self-healing on audit gaps, opening PRs for fully-passed features (never merges). Sole AFK orchestrator permitted to invoke other workflows.
type: workflow AFK
trigger: User-invoked; runs autonomously after Step 1B scope authorization.
version: "1.0.9"
timestamp: 2026-07-15
---

# AFK END-TO-END LOOP

## Authority & Guardrails
- **Orchestrator rule:** invokes other workflows by command name; never duplicate bodies (AGENTS.md §1). `3z` is sole AFK/autonomous orchestrator; `1c` is user-invoked discovery orchestrator.
- **Subagent isolation:** never run `/3d_implement-issue` and `/4a_verify-and-ship` in same context. Each is fresh subagent bootstrapped by `/0a_start-session`.
- **AFK-only:** never autonomously execute non-`mode:AFK` slices.
- **Ship:** push + open/update PR for fully-passed feature branches when `gh` is connected; never merge (AGENTS.md §4).

## Phase 1: Bootstrap & Scope Intake

### Step 1A: Bootstrap
Run `/0a_start-session` to restore branch and load memory.
_Done when:_ orchestrator context synced.

### Step 1B: Detect & Confirm Scope [HITL gate]
1. Build queue from `.memory/BACKLOG_MAP.md` + `.memory/STATUS.md`:
   - **Single:** active issue. **Batch:** sprint's sequenced slices.
   - **Retry:** Slices marked `status:blocked` are re-queued (preflight excludes only `status:done`).
2. **Preflight checks:**
   - **Unknown/closed check:** For each slice ID, verify it exists in `BACKLOG_MAP.md` and status is not `status:done`. Else halt: `[ERROR] BT-<padded> not found or closed`.
   - **Mode-based pre-flight:** AFK/HITL mode governs execution; primary type is orthogonal:
     - `mode:AFK` → Keep (if `size:large`, add complexity advisory).
     - `mode:HITL` → `[SKIP] BT-<padded> mode:HITL — excluded` and drop (if named single issue → HALT with guidance: "run /3d_implement-issue + /4a_verify-and-ship manually").
     - Neither `mode:AFK` nor `mode:HITL` (missing mode, or `status:needs_spec`) → `[SKIP] BT-<padded> no execution mode — excluded` and drop (if named single issue → HALT with guidance: "requires execution mode mode:AFK or mode:HITL to be run").
3. **Group** slices by parent feature; order by `(parent_feature, dependency_order, slice_id)`.
4. Detect `gh auth status` → set ship mode: `auto-PR` (connected) | `local-only`.
5. **Working file:** if batch run (`count > 1`), delete stale `.tmp/3z-loop.work.md` and initialize ephemeral run log.
6. Present ordered queue + count + ship mode; **halt for confirmation** before execution.
_Done when:_ user authorized slice list and ship mode.

## Phase 2: Sequential Slice Loop
For each confirmed slice `BT-<padded>`; `attempt = 1`, max 3:

### Step 2A: Implement (Subagent)
1. **Set Active Issue:** Set `Active issue = BT-<padded>` in `.memory/STATUS.md`.
2. **Dispatch:** "Run `/0a_start-session` (loads BT-<padded>, sets status to `status:in progress`, restores/creates branch), then `/3d_implement-issue`. If prior gap report is attached, target it. Commit locally. Return JSON: `{\"files_changed\": [], \"tests_added\": [], \"commit_shas\": [], \"ac_self_coverage\": {}, \"needs_manual_qa\": false}`. Do NOT push; do NOT open PR."
_Done when:_ subagent returns valid JSON and git status is clean.

### Step 2B: Verify (Subagent)
1. **Dispatch:** "Run `/0a_start-session` (read-only; do NOT transition status or checkout branch), then `/4a_verify-and-ship` Phases 1–4 ONLY with input issue ID `BT-<padded>` and design-doc path `docs/design/BT-<padded>-interface.md`. Produce coverage map only; do NOT edit code/tests, do NOT commit/push, do NOT run Phase 5. Return JSON: `{\"verdict\": \"[PASS]\" | \"[UNCOVERED]\" | \"[SKIP]\", \"coverage_map\": {}, \"needs_manual_qa\": false}` (confidence ≥ 80)."
_Done when:_ auditor returns valid JSON verdict.

### Step 2C: Decision Gate (Orchestrator)
Evaluate subagent response:
- Verdict `[PASS]` or `[SKIP]` (cosmetic bypass) → mark slice `VERIFIED` (or `VERIFIED-LOCAL` if local-only) and record details; log to `.tmp/3z-loop.work.md` (if batch); next slice.
- Verdict `[UNCOVERED]` with confidence ≥ 80 → `attempt += 1`: if `≤ 3` → Step 2A with coverage map; if `> 3` → mark slice `status:blocked` in BACKLOG_MAP, comment `[UNCOVERED]` rows on GitHub issue, set status label to blocked (`gh issue edit <padded> --remove-label "status:in progress" --add-label "status:blocked"`), log to `.tmp/3z-loop.work.md`, continue.
_Loop done when (exhaustive):_ every queued slice reached a terminal state (`VERIFIED`, `VERIFIED-LOCAL`, or `status:blocked`).

## Phase 3: Ship & Conflict Scan

### Step 3A: Ship Pass (Orchestrator; auto-PR mode only)
For each feature whose queued slices are all `VERIFIED`:
1. **Branch checkout:** Run `git checkout <feature_branch>`.
2. **Execute Ship:** Run `/4a_verify-and-ship` Phase 5: branch-safety + design-drift gate, push, open/update feature PR, comment PR link on slice issues. Design-drift or branch-safety failure → leave local + flag `[BLOCKED-ship]`. Log outcome to `.tmp/3z-loop.work.md`.
_Done when:_ every all-passed feature has open/updated PR (or flagged), and no merge.
- Features with `status:blocked` slices stay local.

### Step 3B: Conflict Scan (Orchestrator; flag only)
- **PR scan (auto-PR mode only):** Per PR: `gh pr view <n> --json mergeStateStatus`; if conflicting → `[CONFLICT] PR #n vs base — needs rebase`.
- **Cross-feature:** Intersect changed file paths across branches; overlaps → `[CONFLICT] branch A & B both touch <path> — merge order matters`. Never auto-resolve. Log flags to `.tmp/3z-loop.work.md`.
_Done when:_ mergeability and path overlaps scanned.

## Phase 4: Final Report [output]
Read `.tmp/3z-loop.work.md` (or in-memory state) and output summary per feature: PR # (or `local`), status (`VERIFIED`/`VERIFIED-LOCAL`/`BLOCKED`), commit shas, test/cosmetic `[SKIP]`, coverage maps, conflict flags, and manual-test checklist for slices with `needs_manual_qa` set to true.
- **Manual QA Gating:** `needs_manual_qa` is advisory; verified by human before merge, does not block push/PR ship.
_Done when:_ final report displayed.
Next step: state which PRs are ready for review/merge and which features stayed local.

## Phase 5: Session Close
Run `/0b_stop-session` to crystallize learnings/glossary, update STATUS + BACKLOG_MAP, run memory lint, and delete `.tmp/3z-loop.work.md`.
_Done when:_ `/0b_stop-session` completes, working file cleaned, and repository memory persisted.
