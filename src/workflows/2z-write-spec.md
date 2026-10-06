---
name: 2z-write-spec
description: "Chain the spec phase (PRD, interface design, spec reconciliation) in one invocation. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.0.0"
timestamp: 2026-10-05
---

# Write Spec (orchestrator)

**Purpose:** Run `/2a-write-prd` → `/2b-interface-design` → `/2c-reconcile-specs` back-to-back for one feature, with one memory load and one decision log. The three units stay standalone and unchanged; 2z only sequences them.

**Orchestrator rule:** AGENTS.md §1 Orchestrators. Each unit still commits its own document (one document per run, AGENTS.md §4).

---

## Phase 0: Load & Resume
1. **Hydrate once:** run the `load-memory` skill (read-only) once. The units' own Phase 0 `load-memory` self-gates on `cached` (a no-op here).
2. **Resume detection** (input: a feature `BT-<n>` or a new idea):
   - Design doc `docs/design/BT-<padded>-interface.md` is `status: stable`, or 2b's skip path already promoted the epic to `planned` → start at Phase 3.
   - PRD `docs/prds/BT-<padded>-*.md` exists → start at Phase 2.
   - Otherwise → Phase 1.
3. **Decision log:** create or reopen `.tmp/2z-BT-<padded>-decisions.md` (`.tmp/2z-<slug>-decisions.md` until 2a mints the ID, then 2z renames it; offline ID `BT-LOCAL-<slug>`; resume checks both names). Append one line per HITL decision; on resume print its last 5 lines. The hand-off reads it too.

## Phase 1: PRD
Run `/2a-write-prd`. Its HITL interview and cost gate stay in the main thread; append each decision to the log.

## Phase 2: Interface Design
Run `/2b-interface-design`.
- If 2b takes its no-surface skip path, no design doc is produced; continue to Phase 3.
- **Path A pause:** 2b halts for the generator. 2z halts too, with a resume note: re-invoke `/2z-write-spec BT-<n>` to resume at 2b (Phase 0 detection, then 2b's own Phase 1 resume check).
- The HITL direction pick stays in the main thread.

## Phase 3: Reconcile
Run `/2c-reconcile-specs` in the main thread. Its own Context Isolation Rule sees that this session authored the artifacts and isolates the scan to its Spec-Reconciliation Auditor subagent. Do **not** wrap 2c itself in a subagent: a subagent cannot run its Phase 4 HALT for user Skips.
- 2c's Phase 4 HITL (present, Skip, apply) stays in the main thread. If 2c emits `[SKIP]`, pass it to Phase 4.
- 2c's spec edits stay uncommitted on the default branch (unchanged 2c behaviour; AGENTS.md §4 permits only 2a/2b/3a document commits). Say so in the hand-off.

## Phase 4: Hand-off
Same routing as 2b: `/3a-version-planning` only when 3a would act on this feature, otherwise `/3b-create-issue` to slice. Name the documents committed this run, the uncommitted 2c edits, and the decision log path. Optionally commit 2c's edits: `git add docs/prds docs/design docs/research && git commit -m "docs(BT-<n>): reconcile specs"`.

**Depth:** at most 2 levels below the 2z session (AGENTS.md §8). Each subagent step runs inline when the host has none.
