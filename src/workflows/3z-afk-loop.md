---
name: 3z-afk-loop
description: "Autonomous end-to-end runner for mode:AFK slices — chains 0a→3d→4a→0b across one slice or a sprint queue via isolated subagent sessions, self-healing on audit gaps, opening PRs for fully-passed ship units (never merges). Sole AFK orchestrator permitted to invoke other workflows. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: AFK
version: "1.8.0"
timestamp: 2026-10-20
---

# AFK END-TO-END LOOP

## Authority & Guardrails
- **Orchestrator rule:** AGENTS.md §1 Orchestrators. `3z` is the sole `AFK` orchestrator.
- **Subagent isolation:** never run `/3d-implement-issue` and `/4a-verify-and-ship` in same context. Each is a fresh subagent that self-hydrates via `load-memory` (no `/0a`, see Step 2A).
- **Workspace:** dispatch 3d/4a subagents with workspace `shared/inherit`, never a worktree — 3d's commits and the `.tmp/` plan and suite files must be visible to the next step, and a worktree lacks untracked deps (e.g. `node_modules`) and branches from the default branch.
- **Depth:** 3z → 3d/4a subagent → at most one further level (AGENTS.md §8 Subagent nesting). Where the host has no subagents, run each step inline.
- **AFK-only:** never autonomously execute non-`mode:AFK` slices.
- **Ship:** push + open/update PR for fully-passed unit branches when `gh` is connected; never merge (AGENTS.md §4; one capped CI-fix round may follow the push).

## Phase 1: Bootstrap & Scope Intake

### Step 1A: Bootstrap
Run `/0a-start-session` to restore branch and load memory.
_Done when:_ orchestrator context synced.

### Step 1B: Detect & Confirm Scope [HITL gate]
1. Build queue from `.memory/BACKLOG_MAP.md`:
   - **Single:** the issue this run targets (named at invocation, or the sole `status:in progress` slice). **Batch:** the sprint's sequenced slices.
   - **Retry:** Slices marked `status:blocked` are re-queued (preflight excludes `status:in review` and `status:done` — both are terminal for the loop: shipped; `in review` is a standalone issue awaiting merge).
2. **Preflight checks:**
   - **Unknown/closed check:** For each slice ID, verify it exists in `BACKLOG_MAP.md` and status is neither `status:in review` nor `status:done`. Else halt/skip: `[ERROR] BT-<padded> not found, already in review, or closed`.
   - **Mode-based pre-flight:** AFK/HITL mode governs execution; primary type is orthogonal:
     - `status:needs_spec` (Spike), any mode → `[SKIP] BT-<padded> Spike (needs_spec) — excluded` and drop (if named single issue → HALT with guidance: "Spike is not buildable: close it on its Exit Criteria, or mint a Build slice with /3b-create-issue").
     - `mode:AFK` → Keep (if `size:large`, add complexity advisory).
     - `mode:HITL` → `[SKIP] BT-<padded> mode:HITL — excluded` and drop (if named single issue → HALT with guidance: "run /3d-implement-issue + /4a-verify-and-ship manually").
     - Neither `mode:AFK` nor `mode:HITL` (missing mode) → `[SKIP] BT-<padded> no execution mode — excluded` and drop (if named single issue → HALT with guidance: "requires execution mode mode:AFK or mode:HITL to be run").
3. **Group** slices by ship unit (`pr_body.py unit` per slice: Milestone, Parent and the parent's Milestone (`--parent-milestone`) from the BACKLOG rows, as 3d step 1; unit = its `unit` key); order by `(unit, dependency_order, slice_id)`. Blocker satisfaction comes from `python .agents/scripts/reconcile.py --edges blockers --ids <slices>`, never from status words.
4. Detect `gh auth status` → set ship mode: `auto-PR` (connected) | `local-only`.
5. **Decision log:** `.tmp/3z-loop.work.md`, append-only, on every run: one line per decision `ts | phase | decision | why | evidence pointer | result`. Each run appends a `start` row first and never deletes or edits earlier rows.
6. Present ordered queue + count + ship mode; **halt for confirmation** before execution.
_Done when:_ user authorized slice list and ship mode.

## Phase 2: Sequential Slice Loop
For each confirmed slice `BT-<padded>`; `attempt = 1`, max 3:

### Step 2A: Implement
0. **Frontier check (Orchestrator):** run `python .agents/scripts/reconcile.py --edges blockers --ids BT-<padded>`. Every `[BLOCKER-OK]` passes, and so does a `[BLOCKER-UNMET] same-unit` blocker that is `VERIFIED`/`VERIFIED-LOCAL` in this run. Any cross-unit unmet/unknown, or a same-unit blocker not verified, → emit `[SKIP-DEP] BT-<padded> waits on BT-<blocker>`, leave the slice's status unchanged (do **not** mark it blocked), log to `.tmp/3z-loop.work.md`, and continue to the next slice.
1. **Activate Slice (Orchestrator):** Set the target slice `BT-<padded>` to `status:in progress` in `.memory/BACKLOG_MAP.md` and on GitHub:
   `gh issue edit <n> --remove-label "status:planned" --remove-label "status:blocked" --remove-label "status:in review" --add-label "status:in progress"` (if connected; else skip remote).
   Promote parent epic `planned → in progress` in `.memory/BACKLOG_MAP.md` and GitHub **only if the epic is not already at `in progress`, `in review`, or `done`**. Update `.memory/STATUS.md` (`Active issue`, `Current Branch`). Refresh `generated.at` (and `generated.by`) on any mutated `.memory/` document.
2. **Dispatch Implementer (Subagent):**
   (the subagent's active task is the `BT-<padded>` passed here — not `.memory/STATUS.md`, so concurrent runs never collide on it):
   > "Run `/3d-implement-issue` for `BT-<padded>` (its Phase 0 self-hydrates via `load-memory` and creates/restores the ship-unit branch — no `/0a` prefix needed). If prior gap report is attached, target it. Commit locally. The blocker guard is already satisfied by the frontier check; skip it.
   > Return JSON: `{\"files_changed\": [], \"tests_added\": [], \"commit_shas\": [], \"ac_self_coverage\": {}, \"red_confirmed\": [], \"docs_read\": [], \"needs_manual_qa\": false, \"plan_path\": \"\", \"branch\": \"\", \"stuck\": null}` (`docs_read` = the reference docs actually opened — PRD, design doc, LEARNINGS, ARCHITECTURE, etc.; `red_confirmed` = the observed RED per micro-tdd; `plan_path` = the 3d plan file `.tmp/3d-plan-BT-<padded>.md`, empty if 3d skipped Phase 0.5; `branch` = `git branch --show-current` after 3d's last commit; `stuck` = micro-tdd's `{reason, options}` when it froze, else null).
   > Do NOT push; do NOT open PR."

_Done when:_ subagent returns valid JSON and git status is clean. Then the Orchestrator (never the implementer) runs `python .agents/scripts/floor_guard.py`; exit 1 or 2 (could not run) is not passing → skip Step 2B; go to Step 2C. `stuck` set → skip Step 2B; go to Step 2C.

### Step 2B: Verify (Subagent)
1. **Dispatch** (`BT-<parentPadded>` = the slice's Parent: BACKLOG `Parent`, else `gh issue view <n> --json parent`):
   > "Run `/4a-verify-and-ship` gate **`audit-only`** (its Phase 0 self-hydrates via `load-memory` — no `/0a` prefix) with input issue ID `BT-<padded>` and design-doc path `docs/design/BT-<parentPadded>-interface.md` (no PRD/design doc at that path (standalone slice) → omit the path).
   > Keep the auditor independent (fresh context), but for a clearly small slice pass the slice diff + ACs + named test files inline and skip broad re-reads.
   > Produce coverage map only; do NOT edit code/tests, do NOT commit/push, do NOT run the `ship-only` gate.
   > Return JSON: `{\"verdict\": \"[PASS]\" | \"[UNCOVERED]\" | \"[SKIP]\", \"coverage_map\": {}, \"docs_read\": [], \"needs_manual_qa\": false}` (`docs_read` = the reference docs opened to audit — issue/PRD, design doc, tests, impl; confidence ≥ 80)."

_Done when:_ auditor returns valid JSON verdict.

### Step 2C: Decision Gate (Orchestrator)
Evaluate subagent response:
- Implementer returned `stuck` (Step 2A) → no retry (needs a human design call): mark slice `status:blocked` in BACKLOG_MAP, set status label to blocked (`gh issue edit <n> --remove-label "status:in progress" --add-label "status:blocked"`), post the reason and both options (`gh issue comment <n> --body "[STUCK] <reason> — options: 1) <a> 2) <b>"`), log to `.tmp/3z-loop.work.md`, continue.
- Floor guard failed (`[FLOOR]`, Step 2A) → not passing: same retry and `status:blocked` path as `[UNCOVERED]` below, the guard's findings as the gap report (comment the `[FLOOR]` rows when blocking). The retry fixes the code; a new `## Floor exceptions` row never counts.
- `tests_added` non-empty and `red_confirmed` empty (Step 2A) → `[NO-RED]`: not passing, same retry and `status:blocked` path as `[UNCOVERED]` below; gap report: record the observed RED per micro-tdd (a characterization test names the wrong value it fails on).
- Verdict `[PASS]` or `[SKIP]` (cosmetic bypass) → mark slice `VERIFIED` (or `VERIFIED-LOCAL` if local-only) and record details, including the `## Deviations` lines read now from the implementer's `plan_path` (4a's ship step deletes the plan; empty `plan_path` or `none` → none); log to `.tmp/3z-loop.work.md`; next slice.
- Verdict `[UNCOVERED]` with confidence ≥ 80 → `attempt += 1`: if `≤ 3` → Step 2A with coverage map; if `> 3` → mark slice `status:blocked` in BACKLOG_MAP, comment `[UNCOVERED]` rows on GitHub issue, set status label to blocked (`gh issue edit <n> --remove-label "status:in progress" --add-label "status:blocked"`), log to `.tmp/3z-loop.work.md`, continue.
_Loop done when (exhaustive):_ every queued slice reached a terminal state (`VERIFIED`, `VERIFIED-LOCAL`, `SKIP-DEP`, or `status:blocked`).

## Phase 3: Ship & Conflict Scan

### Step 3A: Ship Pass (Orchestrator; auto-PR mode only)
For each ship unit whose queued slices are all `VERIFIED`:
1. **Branch checkout:** Run `git checkout <branch>` (the `branch` from the unit's slices' Step 2A JSON).
2. **Execute Ship (once per slice):** For **each** `VERIFIED` slice in the unit, run `/4a-verify-and-ship` gate **`ship-only`** passing that slice's `BT-<padded>`: branch-safety + design-drift gate, push, open/update unit PR, ship-status the slice (child `done` + closed; standalone `in review`), comment PR link on its issue.
   - The `ship-only` gate is single-slice — its Epic Check flips each epic `status:in review` when that epic's last slice is shipped and the PR ready when every epic in it is complete, so every VERIFIED slice must get its own Phase-5 pass.
   - Pass each dispatch the slice's audit result — `verdict` (Step 2C), `audit_rounds` (the final `attempt`) and `needs_manual_qa` (becomes a `post_merge` item in the PR body); `ship-only` never audited, so it cannot derive them.
   - Any `ship-only` halt (`[UNCOMMITTED]`, `[FLOOR]`, `[DRAFT-RULE]`, `[MIRROR-UNVERIFIED]`, `[CI-RED]`, terminal-gate failure, Feature Acceptance Audit gaps, branch-safety, design drift) → flag `[BLOCKED-ship] <the halt message>`, continue the frontier; slice stays local, except `[CI-RED]`: slice pushed, unit PR held draft.
   - **CI gate** (last `ship-only` of a unit, never per intermediate slice; `references/ci-gate.md`):
     - `ship-only` returns `[CI-FIX]` + `log_tail`, commits nothing.
     - Orchestrator dispatches a fresh 3d implementer: "Run `/3d-implement-issue` for `BT-<padded>` as a CI fix: gap report = the `log_tail`; skip the Phase 0 status flip (keeps its shipped status); record the full suite (`test_gate.py record --suite`) before the commit; commit `fix(BT-<padded>): ci - <step>`; do NOT push."
     - Orchestrator runs `ci_gate.py cap --commit HEAD` and `floor_guard.py`, then re-runs `ship-only` with `--attempt 2`.
     - At most 2 fix commits per unit PR, one round. `[CI-RED]`: implementer `stuck` or red suite, failed cap or floor guard, second red, exit 2 from `ci_gate.py` (`[CI-RED] could not check`), or big: brief → `.tmp/`, comment `[CI-RED]` on PR and slice issue; 3z never mints issues (3b is HITL).
   - Step 1B's confirmation is the ship pre-authorization for 4a Phase 5 step 3.
   - Log each outcome to `.tmp/3z-loop.work.md`.
_Done when:_ every all-passed ship unit has all its slices shipped on an open/updated PR (or flagged), and no merge.
- Ship units with `status:blocked` or `SKIP-DEP` slices stay local.

### Step 3B: Conflict Scan (Orchestrator; flag only)
- **PR scan (auto-PR mode only):** Per PR: `gh pr view <n> --json mergeStateStatus`; if conflicting → `[CONFLICT] PR #n vs base — needs rebase`.
- **Cross-unit:** Intersect changed file paths across branches; overlaps → `[CONFLICT] branch A & B both touch <path> — merge order matters`. Never auto-resolve. Log flags to `.tmp/3z-loop.work.md`.
_Done when:_ mergeability and path overlaps scanned.

## Phase 4: Final Report [output]
Read `.tmp/3z-loop.work.md` and output summary per ship unit:
- PR # (or `local`).
- Status (`VERIFIED`/`VERIFIED-LOCAL`/`BLOCKED`/`SKIP-DEP` — list each `[SKIP-DEP]` slice with the blocker it waits on and "re-run /3z after BT-<blocker> ships (same-unit) or merges (cross-unit)").
- Commit shas, test/cosmetic `[SKIP]`, coverage maps, conflict flags.
- **The reference docs each slice read (`docs_read` — PRD/design/etc.) so the user can confirm the right artifacts were used (and spot a skipped frozen design doc).**
- **Each slice's plan deviations (recorded at Step 2C; `none` when none, `n/a` for `status:blocked`/stuck slices, which never reach it) next to `docs_read`.**
- Manual-test checklist for slices with `needs_manual_qa` set to true.

**Manual QA Gating:** `needs_manual_qa` is advisory; verified by human before merge, does not block push/PR ship.
_Done when:_ final report displayed.
Next step: state which PRs are ready for review/merge and which ship units stayed local.

## Phase 5: Session Close
Run `/0b-stop-session` to crystallize learnings/glossary, update STATUS + BACKLOG_MAP and run memory lint. The decision log is retained (gitignored).
_Done when:_ `/0b-stop-session` completes and repository memory persisted.
