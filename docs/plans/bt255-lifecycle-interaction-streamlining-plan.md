---
type: plan
title: "Implementation Plan: BT-255 Lifecycle Interaction Streamlining"
generated:
  by: 1a-research
  at: "2026-11-09T22:35:00Z"
version: "2.0.0"
epic: BT-255
slices:
  - BT-253
---

# Hardened Implementation Plan: BT-255 Lifecycle Interaction Streamlining

## 1. Executive Summary & Review Verdict
Following an adversarial systems critique by an independent reviewer, the implementation plan for Epic **BT-255** has been hardened. The refined architecture eliminates conversational friction while preserving:
1. **Tooling Compatibility:** Full adherence to `pr_body.py` and `test_gate.py` contracts (no ad-hoc receipt files).
2. **Regression Rigor:** Guaranteed full regression coverage before push without redundant duplicate test runs.
3. **Constitutional Invariants:** Full compliance with `memory-protocol.md` §5 (no silent `.memory/` mutation; single-click batch approval instead).
4. **Balanced Priority Scoring:** Mathematical rebalancing of default ICE metrics to prevent systematic `priority:high` inflation.

---

## 2. Hardened Slicing Architecture

To eliminate the producer-consumer trap (where modifying `3d` independently breaks `4a` during the slice's own shipment), the work is partitioned by **system boundary**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   HARDENED 2-SLICE IMPLEMENTATION                      │
├────────────────────────────────────────────────────────────────────────┤
│ 🚀 SLICE 1: BT-253 (Backlog & Planning Pipeline Streamlining)          │
│    • 3b-create-issue: Fast-path inference + Single Final Gate          │
│    • 3c-sprint-planning: Inline DAG warnings + Consolidated Gate       │
│    • Blast Radius: Zero shipping risk. Ships cleanly via existing 4a.  │
├────────────────────────────────────────────────────────────────────────┤
│ 🚢 SLICE 2: BT-263 (Execution & Shipping Pipeline Streamlining)        │
│    • 3d-implement-issue: Scoped micro-tdd loop + single suite record   │
│    • 4a-verify-and-ship: Suite receipt reuse + Unified Ship Gate       │
│    • 0d-nightly & 2c-reconcile: Single-click batch approval gates      │
│    • Blast Radius: Atomic update of producer (3d) & consumer (4a).    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Specifications per Skill

### Skill 1: `src/workflows/3b-create-issue.md` (Slice 1: BT-253)
* **Goal:** Eliminate intermediate parameter halts; consolidate into a single final verification gate before issue minting.
* **Phase 2 Step 2 (Deterministic Metric Defaults):**
  - Replace lines 55–59 (ODI fallback halt) with calibrated inference rules:
    - **Impact:**
      - `type:bug`: Default to `1.0 (med)`. Elevate to `2.0 (high)` only if title/brief specifies critical system crash, data loss, or security.
      - `type:feature`: Default to `1.0 (med)` for secondary/incremental; `2.0 (high)` for core user flows.
      - `type:improvement`: Default to `1.0 (med)`.
      - `type:maintenance` / `type:refactor`: Default to `0.5 (low)` or `1.0 (med)`.
      - Explicit default when unbacked: `1.0 (med)`.
    - **Confidence:**
      - Default to `80% (high)` when ODI is absent (prevents automatic jump to 100%).
      - Default to `100% (certain)` only when referencing frozen PRD/design contracts.
      - Default to `50% (guess)` for exploratory spikes.
    - **Size:**
      - Infer from file touchpoints: `small` (1–2 files), `medium` (3–5 files), `large` (>5 files).
* **Phase 2 Step 3:** Draft silently to `.tmp/BT-<padded>-issue-drafts.md`.
* **Phase 2 Step 5 (Single Final Verification Gate):**
  - Render a high-density compact summary table before the full draft bodies:
    ```markdown
    ### Slices Proposed for Minting
    | Slice | Type | Inferred Impact | Conf | Size | Calculated ICE | Assigned Priority |
    |:---|:---|:---:|:---:|:---:|:---:|:---:|
    | BT-<padded> | feature | 1.0 (med) | 80% | med (2) | 0.40 | priority:medium |

    [Approve & Mint via gh issue create]
    To adjust: reply with `set <field>=<value>` (e.g. `set impact=2.0`)
    ```
  - Single approval confirms minting without preliminary interrogation turns.

---

### Skill 2: `src/workflows/3c-sprint-planning.md` (Slice 1: BT-253)
* **Goal:** Eliminate fragmented warning halts during queue planning.
* **Phase 4 & 5 Consolidation:**
  - Embed warnings (`size:large` on `mode:AFK`, late-discovered dependencies) directly as annotated rows inside the topological DAG sequence table.
  - Consolidate priority flips and dependency recording into a single prompt:
    `[Activate Sprint Queue] / [Edit Queue]`.

---

### Skill 3: `src/workflows/3d-implement-issue.md` (Slice 2: BT-263)
* **Goal:** Prevent runaway full test sweeps during iterative coding while preserving `test_gate.py` compatibility.
* **Phase 1 / Step 3 (Inner Loop):**
  - Strictly enforce scoped unit testing (`micro-tdd`):
    `pytest tests/<domain>/test_<slice>.py`
  - Explicit constraint: *Never run repo-wide test suites during 3d feature iteration.*
* **Phase 3 Step 6 (Completion Gate):**
  - Run the full repository test suite **EXACTLY ONCE** at clean `HEAD`:
    `python .agents/scripts/test_gate.py record --suite BT-<padded> -- <test-cmd>`
  - This populates `.tmp/3d-suite-BT-<padded>.json` and verifies working tree cleanliness, preserving 100% compatibility with `pr_body.py`.

---

### Skill 4: `src/workflows/4a-verify-and-ship.md` (Slice 2: BT-263)
* **Goal:** Eliminate duplicate full test runs and collapse Phase 4 & Phase 5 into a Unified Ship Gate.
* **Phase 3 (Suite Verification):**
  - Check `.tmp/3d-suite-BT-<padded>.json` via `pr_body.py suite`.
  - If valid for current `HEAD`, **SKIP the full repository test suite in 4a entirely**.
  - If missing or HEAD has moved, execute the suite once through `test_gate.py record --suite`.
* **Phases 4 & 5 Consolidation (Unified Ship Gate):**
  - Merge the audit findings report, test proof summary, and PR metadata into one closing confirmation:
    ```markdown
    ### Unified Ship Verification Gate
    - **Audit Verdict:** [PASS] (0 Spec gaps, 0 hard Standards breaches)
    - **Test Proof:** Reused passing suite receipt (SHA: <sha>)
    - **Branch & PR Target:** <branch> -> PR #<n> (<title>)
    - **Post-Ship Status:** BT-<slice> -> status:done (closed), Epic -> in review

    Confirm to push branch, open/update PR, and advance issue state?
    [Confirm & Ship] / [Abort]
    ```

---

### Skill 5: `src/workflows/0d-nightly-consolidation.md` (Slice 2: BT-263)
* **Goal:** Streamline maintenance approvals without violating `memory-protocol.md` §5.
* **Constitutional Rule:** Never silently rewrite `.memory/`.
* **Single-Click Batch Approval:**
  - Group routine cleanups (dead links, formatting, index syncing) under a pre-selected batch recommendation `R-ALL-CLEAN`.
  - Prompt once: `[Apply Recommended Cleanups] / [Decline]`.

---

### Skill 6: `src/workflows/2c-reconcile-specs.md` (Slice 2: BT-263)
* **Goal:** Streamline spec reconciliation into an exception-only review.
* **Context Rule:** Keep user-supplied context/epic.
* **Exception Gate:**
  - Auto-generate unified patch for structural boilerplate.
  - Present semantic conflicts in a single-turn exception table for approval.

---

## 4. Verification & Testing Strategy
1. **Schema & Build Gate:**
   - Run `python build/build.py` and `python build/validate.py`.
2. **Pipeline Contract Check:**
   - Confirm `pr_body.py build` succeeds with cached suite records.
   - Confirm `test_gate.py verify` passes before ship authorization.
3. **Dry-Run Validation:**
   - Execute `/3b-create-issue` on a sample issue to verify zero intermediate halts and compact table presentation.
