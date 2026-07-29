---
name: 3b_create-issue
description: Standardize feature ideas into vertical slices with ICE prioritization.
type: workflow HITL
trigger: manual
version: "2.3.0"
timestamp: 2026-07-28
---

# Create issue

**Purpose:** Convert ideas into implementation-ready vertical slices synced with memory.

**Hand-off contract:** Upstream: `/3a_version-planning` gates current-release parent features to slice. PRD-sourced → reads §1, §6, §7, §8; drafts full Template B slices to `.tmp/BT-<padded>-issue-drafts.md`, audits coverage + fidelity against §6 + §8, mints the approved drafts verbatim. Else checks against captured intent. Template A spikes skip drafting/audit.

## Phase 0: Load Memory
Run `.agents/skills/load-memory/SKILL.md` to restore session context (read-only).

## Phase 1: Intake & Scope
1. **Intake:** Receive raw idea or MVI.
2. **Defensive epic promotion (idempotent guard):** If the parent epic is still `status:needs_spec` (a 2b promotion was missed or 2b was skipped), promote it `needs_spec → planned` now: `gh issue edit <parent> --remove-label "status:needs_spec" --add-label "status:planned"` and update its BACKLOG Status. No-op if already `planned` or further; skip for standalone slices with no parent.
3. **Scope:** PRD-sourced → load `docs/prds/BT-<padded>-<name>.md` and frozen design doc `docs/design/BT-<padded>-interface.md`. Scope is PRD §6 + §8 and design blueprint. Else raw idea/MVI is scope.

## Phase 2: Slice, Draft & Audit
1. **Slices List:** propose breakdown per slice:
   - **Title:** short name.
   - **Logic/user story:** end-to-end path.
   - **Blocked by:** prerequisite slices.
   - **Inheritance:** inherit scope-class + ODI score from PRD §6. No slices for `[DEFERRED]` stories.
   - **Minimum-slice floor (value, not LOC):** do not emit a slice with no independent verification/demo value beyond its sibling — fold it into the sibling or keep the feature whole (a one-line change is rarely its own slice). Judge by vertical value, never line count. **Do not over-fold across surfaces** (e.g. merging a backend slice with its UI slice to save cost) — that yields a multi-file/UI slice that triggers the full independent audit anyway and erodes isolation; fold only a child that has no standalone verification value.
2. **Prioritization Metrics (Template A spikes: skip):**
   - **Impact from ODI:** Map story ODI score to Impact:
     - `ODI < 5` → `0.25`
     - `5 <= ODI <= 8` → `0.5`
     - `9 <= ODI <= 12` → `1.0`
     - `13 <= ODI <= 16` → `2.0`
     - `17 <= ODI <= 20` → `3.0`
     - (Note: scope-class governs ordering; baseline sequenced before differentiator).
   - **Confidence from ODI:** Map story ODI confidence to Confidence:
     - `[HIGH]` → `100%`
     - `[MEDIUM]` → `80%`
     - `[LOW]` → `50%`
    - **Fallback (ODI absent):** Prompt user for Impact and Confidence:
      - **Impact:** ∈ {0.25 (min), 0.5 (low), 1.0 (med), 2.0 (high), 3.0 (crit)}
      - **Confidence:** ∈ {50% (guess), 80% (high), 100% (certain)}
   - Prompt for **Size** (Effort):
     - **Size:** ∈ {size:small (weight 1), size:medium (weight 2), size:large (weight 3)}
3. **Draft full specs to scratch (Template A spikes: skip):** expand each slice into a complete, self-contained Template B in `.tmp/BT-<padded>-issue-drafts.md`, every field inline: contracts/invariants (e.g. Zod/Pydantic/TS types), selectors/patterns, and edge cases from PRD §6/§8 + the frozen design blueprint; governing `[[A-xxx]]`/`[[DR-xxx]]` citations; verifiable AC incl. time-to-value + stress cases from the design doc; Parent/Blocked-by. This draft is the issue body minted verbatim in Phase 3.
4. **Slice Draft Audit (Template A spikes: skip):** invoke an independent Slice Draft Auditor subagent (Antigravity `invoke_subagent` / Claude Code `Task` general-purpose). Reads (fresh from disk, all if present): `.tmp/BT-<padded>-issue-drafts.md`; the **full** PRD `docs/prds/BT-<padded>-<name>.md`, interface design `docs/design/BT-<padded>-interface.md`, and research `docs/research/*<slug>*.md`. **Precedence:** PRD + interface design are authoritative; research is supplementary — on conflict, PRD/interface win. Guardrail: *"Report findings + one proposed fix each; do not create issues or edit any file."* Score 0–100 per `.agents/workflows/.reference/confidence-scale.md` (audit scope: slice-draft coverage + fidelity to specs); report ≥ 80 across two dimensions:
   - **Breadth:** map **every `[BASELINE]` and `[DIFFERENTIATOR]` §6 story, §8 DoD item, and design blueprint element** to its covering slice or `[UNCOVERED]`, walking the **journey-grouped** §6 stories. `[DEFERRED]` stories / §9 Out-of-Scope are covered/excluded (**not** `[UNCOVERED]`).
   - **Depth:** each draft is Template B-complete, faithfully captures the named contracts/invariants + edge cases, cites the governing `[[A-xxx]]`/`[[DR-xxx]]`, and carries verifiable AC (incl. time-to-value + stress cases).
   - **Loop optimization:** re-spawn *only* on material change (slices added / removed / re-scoped, or bodies materially edited) — not cosmetic edits (renames, ICE tweaks).
   - **Resolution:** `[UNCOVERED]` → add slice / defer to §9 / confirm out-of-scope / "covered by construction". Scope creep (hits §4 Non-Goal / §9 Out-of-Scope) → `[SCOPE-CREEP]` cut. Blocker (open §10 Question) → Template A. Apply ≥ 80 draft-fixes to `.tmp`. **Spec defect** (the PRD/design itself is ambiguous or self-contradictory, not the draft) → do not patch the draft; surface it and route to `/2c_reconcile-specs` or convert the slice to a Template A spike. **Research-only finding** (a requirement/constraint present in research but absent from PRD + interface) → flag `[RESEARCH-GAP]` for HITL before implementing; never fold it into the draft unilaterally.
   - **No PRD:** restate intent as a requirement list; map slices; gaps → `[UNCOVERED?]` (soft) for user confirmation; no §-refs.
5. **Approval Request:** present the audited drafts + coverage map. Confirm: requirements & end-state covered (no `[UNCOVERED]`); granularity; dependencies; modes (`mode:HITL`/`mode:AFK`); ICE scores. Halt until user approves.

## Phase 3: Implementation & Memory Sync
1. **Calculate ICE Score (Template A spikes: skip):** `ICE = (Impact * Confidence) / Effort weight` (Confidence as decimal; Effort: small=1, medium=2, large=3).
2. **Determine Priority Label (Template A: skip):**
   - `ICE >= 0.5` → `priority:high`
   - `0.15 <= ICE < 0.5` → `priority:medium`
   - `ICE < 0.15` → `priority:low`
3. **Generate (Atomic Minting):** Execute `gh issue create`. Body source: Template B slice → the approved `.tmp/BT-<padded>-issue-drafts.md` draft **verbatim** (never regenerate); Template A spike → compose the Template A body. Offline fallback: assign `BT-LOCAL-<n>`. **CRITICAL:** Capture exact returned issue number and zero-pad to 3 digits (e.g. `BT-059`). Never guess issue number; GitHub shares IDs across Issues and PRs. Write raw ICE metrics in issue body. Apply scope label (`scope:baseline` or `scope:differentiator`). Assign canonical labels: Primary Type (e.g. `type:feature`) + Execution Mode (`mode:HITL` or `mode:AFK`) + Tier (`tier:slice`) + Size (`size:small/medium/large`) + Priority (`priority:high/medium/low` from the step-2 bucket; Template A spike: skip) + **Status: `status:planned` for a normal Template B slice; `status:needs_spec` for a Template A spike** (milestone-exempt and `/3c`-excluded until re-specced).
   - **Sub-issue Linkage:** If derived from parent epic, link via the `addSubIssue` mutation per `.agents/workflows/.reference/github-issue-relations.md` (native `gh api graphql`; no `gh-sub-issue` extension).
   - **Dependencies:** Wire blockers via the `addBlockedBy` mutation (same reference). Mirror "Blocked by: [IDs]" in the issue body and BACKLOG_MAP.
4. **Backlog Sync:** Append entry (`BT-<padded>`) to `.memory/BACKLOG_MAP.md` adhering to `[[memory-protocol.md#8-backlog-id-minting-late-binding]]` (first real entry: purge placeholders) — 9-column schema. Write bucketed priority, size, type, execution mode, tier, and scope label to the Labels column (never the status), the bare status token (`planned`/`needs_spec`) to the Status column, and ICE details to ICE. In the **`Parent`** column write the single `BT-<parentPadded>` (or `—` for a standalone slice); in the **`Blocked by`** column write the comma-list of bare sibling blocker IDs (or `—`). Set milestone to parent feature release `vX.Y.0` (default `v1.0.0`; Template A spikes are milestone-exempt → `—`). sprint digit Z assigned by 3c.
5. **Terminal sync gate:** run `python .agents/scripts/reconcile.py --ids <comma-list of created BT-<padded>>` (all fields — these are freshly created rows) per `.agents/workflows/.reference/terminal-sync-invariant.md`. Non-zero → heal per the reference and re-run until `[MIRROR-OK]` before hand-off.
6. **Hand-off:** Slices created. Run `/3c_sprint-planning` to sequence, or `/3d_implement-issue` for single ready slice.

---

## LABEL REGISTRY
Use registry in `.memory/BACKLOG_MAP.md`. Do not invent labels. If label missing: propose adding to BACKLOG_MAP registry, await confirmation, create in GitHub, write to registry, then apply.

## Issue Templates
Follow canonical templates in `.agents/workflows/.reference/issue-templates.md`.