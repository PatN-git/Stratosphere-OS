---
name: 2z-write-spec
description: "Chain the spec phase (PRD, interface design, spec reconciliation) in one invocation. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.0.1"
timestamp: 2026-10-06
---

# Write Spec (orchestrator)

**Purpose:** Run `/2a-write-prd` → `/2b-interface-design` → `/2c-reconcile-specs` for one feature with one memory load and one decision log. Units stay standalone and unchanged; 2z only sequences them.

**Orchestrator rule:** AGENTS.md §1 Orchestrators. Each unit still commits its own document (one document per run, AGENTS.md §4).

**Context protection:** main thread keeps HITL, commits, decision log. Read-heavy, non-HITL steps run in subagents: write only to `.tmp/`, never commit, return the path + ≤10-line summary. A subagent never asks the user; it returns every decision as a gate list. Inline when host has no subagents (AGENTS.md §8).
- **PRD Drafter** (2a Phase 3). Input: decision log, discovery brief, memory paths; follows Phase 3 of `.agents/skills/2a-write-prd/SKILL.md`. Guardrail: "Write the draft to `.tmp/2z-BT-<padded>-prd-draft.md` only; no other file, no commit. Return the path, a ≤10-line summary and every user gate: cost approval, `[unbacked]` scope tags, ADR flag, `> open:`." Main puts the gates to user, applies answers as surgical edits, then runs 2a Phases 4–5.
- **Direction Drafter** (2b Phase 2.5 steps 1–3). Input: PRD path, 2b gate result. Guardrail: "Write the 3 directions and 5-Lens notes to `.tmp/2z-BT-<padded>-directions.md` only; no other file, no commit." Main renders via `plan-html` and runs the HITL pick.
- **Stress Tester** (2b) and **Spec-Reconciliation Auditor** (2c): dispatch as subagents per the unit, never inline.

---

## Phase 0: Load & Resume
1. **Hydrate once:** run `load-memory` (read-only). Units' Phase 0 `load-memory` self-gates on `cached` (no-op).
2. **Resume detection** (input: a feature `BT-<n>` or a new idea):
   - Design doc `docs/design/BT-<padded>-interface.md` is `status: stable`, or 2b's skip path already promoted the epic to `planned` → start at Phase 3.
   - PRD `docs/prds/BT-<padded>-*.md` exists → start at Phase 2.
   - Otherwise → Phase 1.
3. **Decision log:** create or reopen `.tmp/2z-BT-<padded>-decisions.md` (`.tmp/2z-<slug>-decisions.md` until 2a mints the ID, then 2z renames it; offline ID `BT-LOCAL-<slug>`; resume checks both names). Append one line per HITL decision; on resume print its last 5 lines. The hand-off reads it too.

## Phase 1: PRD
Run `/2a-write-prd`. Its HITL interview and cost gate stay in main thread; draft via PRD Drafter; append each decision to the log.

## Phase 2: Interface Design
Run `/2b-interface-design`.
- If 2b takes its no-surface skip path, no design doc is produced; continue to Phase 3.
- **Path A pause:** 2b halts for the generator. 2z halts too, with a resume note: re-invoke `/2z-write-spec BT-<n>` to resume at 2b (Phase 0 detection, then 2b's own Phase 1 resume check).
- The HITL direction pick stays in main thread; draft the directions via Direction Drafter.

## Phase 3: Reconcile
Run `/2c-reconcile-specs` in main thread. Its Context Isolation Rule detects session-authored artifacts and isolates the scan to its Spec-Reconciliation Auditor. Do **not** wrap 2c in a subagent: it cannot run Phase 4 HALT for user Skips.
- 2c's Phase 4 HITL (present, Skip, apply) stays in main thread. If 2c emits `[SKIP]`, pass it to Phase 4.
- 2c's spec edits stay uncommitted on the default branch (unchanged 2c behaviour; AGENTS.md §4 permits only 2a/2b/3a document commits). Say so in the hand-off.

## Phase 4: Hand-off
Same routing as 2b: `/3a-version-planning` only when 3a would act on this feature, otherwise `/3b-create-issue` to slice. Name the documents committed this run, the uncommitted 2c edits, and the decision log path. Optionally commit 2c's edits, adding each document this run wrote or edited by path, never a directory (AGENTS.md §4: no swept drift): `git add docs/prds/BT-<padded>-<name>.md docs/design/BT-<padded>-interface.md docs/research/<doc>.md && git commit -m "docs(BT-<n>): reconcile specs"` (drop the paths this run did not touch).

**Depth:** at most 2 levels below the 2z session (AGENTS.md §8).
