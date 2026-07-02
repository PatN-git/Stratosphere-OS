---
name: 3z_afk-loop
description: Autonomous end-to-end runner for type:AFK slices — chains 0a→3d→4a→0b across one slice or a sprint queue via isolated subagent sessions, self-healing on audit gaps and opening PRs for fully-passed features (never merges). The sole orchestrator permitted to invoke other workflows.
type: workflow AFK
trigger: User-invoked; runs autonomously after Step 1B scope authorization.
version: "1.0.5"
timestamp: 2026-07-02
---

# AFK END-TO-END LOOP

## Authority & Guardrails
- **Sole orchestrator:** invokes other workflows by command name only — never duplicate their bodies (AGENT.md §1).
- **Subagent isolation:** never run `/3d_implement-issue` and `/4a_verify-and-ship` in the same context. Each is a fresh subagent bootstrapped by `/0a_start-session`.
- **AFK-only:** never autonomously executes a non-`type:AFK` slice.
- **Ship:** push + open/update PR only for fully-passed feature branches, only when `gh` is connected; **never merge** (AGENT.md §4).

## Phase 1: Bootstrap & Scope Intake

### Step 1A: Bootstrap
Run `/0a_start-session` to restore branch + load memory.
_Done when:_ orchestrator context synced.

### Step 1B: Detect & Confirm Scope  [HITL gate]
1. Build the queue from `.memory/BACKLOG_MAP.md` + `.memory/STATUS.md` (or an explicit issue list in the prompt):
   - **Single:** the active issue. **Batch:** the sprint's sequenced slices.
   - **Retry behavior:** Slices previously marked `status:blocked` are included/re-queued for execution on subsequent runs (preflight excludes only `status:done`).
2. **Preflight checks:**
   - **Unknown/closed check:** For each requested slice ID, verify it exists in `BACKLOG_MAP.md` and its status is not `status:done`. If not found, closed, or nonexistent → halt and print: `[ERROR] BT-<padded> not found or closed`.
   - **Mode-based pre-flight:** Execution mode (`type:AFK` or `type:HITL`) governs the keep/skip decision; primary type (`type:feature`, `type:bug`, etc.) is orthogonal:
     - `type:AFK` $\rightarrow$ Keep (if `size:large`, add complexity advisory).
     - `type:HITL` $\rightarrow$ `[SKIP] BT-<padded> type:HITL — excluded` and drop (if named single issue $\rightarrow$ HALT with guidance: "run /3d_implement-issue + /4a_verify-and-ship manually").
     - Neither `type:AFK` nor `type:HITL` (e.g. missing mode, or a `status:needs_spec` item) $\rightarrow$ `[SKIP] BT-<padded> no execution mode — excluded` and drop (if named single issue $\rightarrow$ HALT with guidance: "requires execution mode type:AFK or type:HITL to be run").
3. **Group** kept slices by parent feature; order by `(parent_feature, dependency_order, slice_id)`.
4. Detect `gh auth status` → set ship mode: `auto-PR` (connected) | `local-only`.
5. **Working file (volume guard):** if batch run (`count > 1`), delete any stale `.tmp/3z-loop.work.md` and initialize an ephemeral run log to persist intermediate subagent outputs and verdicts across steps.
6. Present ordered queue + count + ship mode; **HALT for one confirmation** before autonomous execution.
_Done when:_ user has authorized a concrete, ordered slice list and ship mode.

## Phase 2: Sequential Slice Loop
For each confirmed slice `BT-<padded>` (feature-grouped order); `attempt = 1`, max 3:

### Step 2A: Implement (Subagent)
1. **Set Active Issue:** Set `Active issue = BT-<padded>` in `.memory/STATUS.md`.
2. **Dispatch (self-contained):** "Run `/0a_start-session` (loads BT-<padded>, sets status to `status:in progress`, restores/creates branch), then `/3d_implement-issue`. If a prior gap report is attached, target it. Commit locally on the feature branch. Return JSON: `{\"files_changed\": [], \"tests_added\": [], \"commit_shas\": [], \"ac_self_coverage\": {}, \"needs_manual_qa\": false}`. Do NOT push; do NOT open a PR."
_Done when:_ subagent returns valid JSON and `git status` is clean.

### Step 2B: Verify (Subagent)
1. **Dispatch (self-contained guardrail — read-only auditor):** "Run `/0a_start-session` (read-only; do NOT re-transition status or re-checkout branch), then `/4a_verify-and-ship` **Phases 1–4 ONLY** with input issue ID `BT-<padded>` and design-doc path `docs/design/BT-<padded>-interface.md`. Produce the **coverage map** (AC/requirement → covering test) only; do NOT edit code/tests, do NOT commit/push, do NOT run Phase 5. Return JSON: `{\"verdict\": \"[PASS]\" | \"[UNCOVERED]\" | \"[SKIP]\", \"coverage_map\": {}, \"needs_manual_qa\": false}` (confidence ≥ 80)."
_Done when:_ auditor returns valid JSON verdict.

### Step 2C: Decision Gate (Orchestrator)
Evaluate the subagent response:
- Verdict `[PASS]` or `[SKIP]` (cosmetic bypass) → mark slice terminal state `VERIFIED` (or `VERIFIED-LOCAL` if ship mode is local-only) and record details (including if it was a cosmetic `[SKIP]`); log to `.tmp/3z-loop.work.md` (if batch); next slice.
- Verdict `[UNCOVERED]` with confidence ≥ 80 → `attempt += 1`: if `≤ 3` → Step 2A with the coverage map attached; if `> 3` → mark slice terminal state `status:blocked` in BACKLOG_MAP, comment `[UNCOVERED]` rows on the GitHub issue, update the issue label in GitHub (using `gh issue edit <padded> --remove-label "status:in progress" --add-label "status:blocked"`), log to `.tmp/3z-loop.work.md` (if batch), continue.
_Loop done when (exhaustive):_ every queued slice reached a terminal state (`VERIFIED`, `VERIFIED-LOCAL`, or `status:blocked`).

## Phase 3: Ship & Conflict Scan

### Step 3A: Ship Pass (Orchestrator; auto-PR mode only)
For each feature whose queued slices are **all** `VERIFIED`:
1. **Branch checkout:** Run `git checkout <feature_branch>` to switch to the parent feature branch before shipping.
2. **Execute Ship:** Run `/4a_verify-and-ship` **Phase 5** (pre-authorized by Step 1B): branch-safety + design-drift gate, push, open/update the single feature PR, comment the PR link on each slice issue. A design-drift or branch-safety failure → leave that feature local + flag `[BLOCKED-ship]`. Log feature ship outcome to `.tmp/3z-loop.work.md` (if batch).
- Any feature with a `status:blocked` slice stays **local** (unpushed).
_Done when:_ every all-passed feature has an open/updated PR (or is flagged), and no feature was merged.

### Step 3B: Conflict Scan (Orchestrator; flag only)
- **PR scan (auto-PR mode only):** Per PR: `gh pr view <n> --json mergeStateStatus`; if conflicting → `[CONFLICT] PR #n vs base — needs rebase`.
- **Cross-feature (both modes):** Intersect changed file paths across shipped/local branches; overlaps → `[CONFLICT] branch A & B both touch <path> — merge order matters`. Never auto-resolve. Log flags to `.tmp/3z-loop.work.md` (if batch).
_Done when:_ mergeability and path overlaps scanned across all processed branches and logged.

## Phase 4: Final Report  [output]
Read `.tmp/3z-loop.work.md` (or in-memory state for single slice) and output aggregate summary per feature: PR # (or `local`), per-slice status (`VERIFIED`/`VERIFIED-LOCAL`/`BLOCKED`), commit shas, whether verified by test or cosmetic `[SKIP]`, coverage maps, conflict flags, and an aggregate manual-test checklist for slices with `needs_manual_qa` set to true.
- **Manual QA Gating:** Note that `needs_manual_qa` is an advisory flag that is accumulated in the PR body and must be verified by a human reviewer before merging, rather than blocking the automated push/PR ship pass.
Next step: state explicitly which PRs are ready for human review/merge and which features stayed local and why.
_Done when:_ final formatted report is displayed to the user.

## Phase 5: Session Close
Run `/0b_stop-session` to crystallize learnings/glossary, update STATUS + BACKLOG_MAP, run memory lint, and delete temporary `.tmp/3z-loop.work.md`.
_Done when:_ `/0b_stop-session` completes, working file is cleaned up, and repository memory state is persisted.
