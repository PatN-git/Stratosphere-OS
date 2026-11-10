---
type: research
title: "Research: Lifecycle Interaction Streamlining & Single-Gate Recommendations"
description: "Empirical review of conversational friction across 194 CleanTechHub and StratOS sessions, establishing intelligent defaults and consolidated single-gate interaction patterns across lifecycle skills."
status: stable
slug: lifecycle-interaction-streamlining-recommendations
generated:
  by: 1a-research
  at: "2026-11-09T22:35:00Z"
sources:
  - resource: "repo:Stratosphere-OS"
    title: "Stratosphere-OS Lifecycle Skills Specification & Transcripts"
  - resource: "repo:CleanTechHub"
    title: "CleanTechHub Production Session History (194 sessions)"
version: "2.0.0"
epic: BT-255
slices:
  - BT-256
  - BT-253
---

# Research: Lifecycle Interaction Streamlining & Single-Gate Recommendations

## Research Brief & Problem Statement
- **Epic:** [BT-255](https://github.com/PatN-git/Stratosphere-OS/issues/255) (*Streamline user interaction across lifecycle skills*)
- **Spike Slice:** [BT-256](https://github.com/PatN-git/Stratosphere-OS/issues/256) (*Spike: Review lifecycle skills for interaction streamlining and formulate single-gate recommendations*)
- **Core Problem:** Across several StratosphereOS lifecycle skills, agents halt repeatedly to ask users for inputs, metrics, or intermediate approvals that can be deterministically computed or safely defaulted. In other skills, agents trigger runaway full-repository test suites or disjointed multi-gate confirmations, causing user friction, context bloat, and quota exhaustion.
- **Objective:** Audit empirical session histories (StratOS + CleanTechHub) across all lifecycle skills (`0a` through `4c`), distinguish real conversational friction from theoretical workflow prose, and formulate concrete single-gate recommendations with smart defaults.

---

## 1. Empirical Findings: StratOS & CleanTechHub Session Logs

An empirical scan of **194 CleanTechHub sessions** and recent StratOS trajectories revealed clear usage patterns and friction concentrations:

| Lifecycle Skill | Empirical Invocations | Tool Questions (`ask_question`) | Content Halts / Prompts | Empirical Assessment |
|:---|:---:|:---:|:---:|:---|
| **`0a-start-session`** | 45 | 0 | 0 | **No real friction.** Chained commands (`/0a` then `/1b`) caused tool calls; `0a` itself ran with 0 questions. |
| **`0b-stop-session`** | 47 | 34 | 147 | **Batched by LLMs.** Outputs a single consolidated closeout summary at the end; real issue was board desync, not multi-halt ping-pong. |
| **`0c-handoff`** | 0 | 0 | 0 | Unused in product repo; minimal generator. |
| **`0d-nightly`** | 9 | 0 | 10 | Routine consolidation; forces manual R-number selection for safe fixes. |
| **`0e-plain-english`** | 0 | 0 | 0 | Read-only explainer. |
| **`0f-walk-me-through`**| 0 | 0 | 0 | Explainer utility. |
| **`1a-research`** | 1 | 0 | 0 | Single deliberate Step 6 plan gate; Phase 3 handoff is non-interactive notification. |
| **`1b-concept-framing`**| 13 | 10 | 80 | **Sacred HITL.** Deep interactive grilling across Rounds 1–3 is its explicit design goal. |
| **`1c-concept-map`** | 1 | 0 | 0 | **Sacred HITL.** Visual diagramming and mapping. |
| **`2a-write-prd`** | 3 | 5 | 15 | Low friction; drafting is smooth. |
| **`2b-interface-design`**| 3 | 5 | 15 | **Sacred HITL.** Collaborative UI design, mockups, and directions require human aesthetic taste. |
| **`2c-reconcile-specs`** | 5 | 1 | 20 | Useful cross-feature consistency check; can auto-apply high-confidence fixes. |
| **`2z-write-spec`** | 7 | 4 | 40 | Low friction; orchestrates specs effectively. |
| **`3a-version-planning`**| 1 | 0 | 5 | Infrequent; roadmap allocation. |
| **`3b-create-issue`** | **32** | **19** | **109** | **High friction.** Multi-round interrogation: halts for Impact/Confidence, prompts for Size, then halts *again* for draft approval (`Session 2a9e7a95`). |
| **`3c-sprint-planning`** | 4 | 8 | 12 | Topological sort validation; label & AFK warnings can be consolidated inline. |
| **`3d-implement-issue`** | **46** | 16 | 90 | **High friction.** Runaway full-suite pytest executions (`Session 7c1f4206`) cause stalls and token drain. |
| **`3z-afk-loop`** | 3 | 2 | 15 | Autonomous loop; functions cleanly. |
| **`4a-verify-and-ship`** | **93** | **28** | **114** | **High friction.** Duplicate test suite execution (re-running full suite after 3d) and double gating (Phase 4 audit review + Phase 5 ship confirmation). |
| **`4b-audit-architecture-drift`** | 8 | 7 | 3 | Targeted drift audits; halt on missing target directory is safety-critical. |
| **`4c-codebase-health-audit`** | 2 | 4 | 0 | Minimal usage. |

---

## 2. Theoretical vs. Empirical Friction Analysis

A key breakthrough of this research is separating **theoretical friction written in workflow documentation** from **real friction experienced by users in practice**:

1. **`0a-start-session` (Theoretical Edge Case):**
   * *Workflow Text:* States that if multiple branches match a glob, the agent should ask the user which branch to use.
   * *Empirical Reality:* In 45 CleanTechHub runs and dozens of StratOS sessions, branch collisions essentially never happen. The agent prints the banner and resolves the task immediately.
   * *Conclusion:* **Keep intact.** No code or workflow change required.

2. **`0b-stop-session` (Theoretical Multi-Halt vs Real Board Desync):**
   * *Workflow Text:* Steps 3, 4, 5, 6 read sequentially ("propose learning... write on confirmation... propose glossary... write on confirmation...").
   * *Empirical Reality:* Modern LLMs automatically batch these into a single closing turn. The user is not grilled one by one.
   * *Real Problem Identified:* GitHub Projects board cards and issue statuses frequently lagged behind (`Session 89eae076`).
   * *Conclusion:* Do not rewrite `0b` interaction; ensure tracker state syncing runs deterministically.

3. **`1a-research` (Deliberate Gating & Zero Second Halt):**
   * *Workflow Text:* Step 6 contains a deliberate "Propose-and-Confirm Gate" to lock the search queries and domain scope. Phase 3 Step 5 is a passive handoff: `Notify user: "Research compiled at docs/research/<slug>.md..."`.
   * *Empirical Reality:* The Step 6 gate prevents runaway web scraping. There is no second question halt at deliverable.
   * *Conclusion:* **Keep intact.** Step 6 is well-designed.

4. **Sacred HITL Workflows (`1b`, `1c`, `2b`):**
   * *Analysis:* These skills exist specifically to provide rich, collaborative human-agent interaction (exploring vague product ideas, establishing mental models, debating UI styling and design directions).
   * *Conclusion:* **Preserve interaction.** Forcing autonomous defaults onto concept framing or visual design defeats their fundamental purpose.

5. **`4b-audit-architecture-drift` (Load-Bearing Safety Guard):**
   * *Analysis:* Halting when a target directory is omitted is essential. If the agent defaulted to scanning `src/`, it would trigger a massive, slow, context-saturating scan.
   * *Conclusion:* **Preserve the halt on missing directory.**

---

## 3. High-Yield Streamlining Scope (The 6 Target Skills)

Real conversational friction and token waste are concentrated in 6 specific lifecycle skills:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   IN-SCOPE STREAMLINING SUITE                          │
├────────────────────┬───────────────────────────────────────────────────┤
│ 1. 3b-create-issue │ Single final verification gate + smart defaults   │
│ 2. 4a-verify-and-ship│ Unified Ship Gate + cached test receipts        │
│ 3. 3d-implement-issue│ Diff-scoped micro-tdd (no runaway test suites)  │
│ 4. 3c-sprint-planning│ Consolidated DAG execution gate + inline alerts │
│ 5. 0d-nightly      │ Single-click batch approval for cleanups          │
│ 6. 2c-reconcile-specs│ User-provided epic; auto-apply structural boiler│
└────────────────────┴───────────────────────────────────────────────────┘
```

### Detailed Skill-by-Skill Streamlining Specifications

#### 1. `3b-create-issue` (Direct Target of BT-253)
* **Fast-Path Metric Inference & Balanced Defaults:**
  - `Impact`: Default by slice type (`bug` $\to$ 1.0, `feature` $\to$ 1.0/2.0, `maintenance` $\to$ 0.5/1.0; unbacked default $\to$ 1.0).
  - `Confidence`: Default to `80%` when ODI is absent (preserves `100%` only for frozen PRD/design contracts; prevents systematic ICE inflation).
  - `Size`: Inferred from file count/AST scope (`small` = 1-2, `medium` = 3-5, `large` = >5).
* **Single Final Verification Gate:**
  - Render a compact, high-visibility table at the top of Phase 2 Step 5 showing inferred metrics and assigned priority.
  - Single prompt: `[Approve & Mint via gh issue create] / [Adjust: reply with set <field>=<value>]`.

#### 2. `4a-verify-and-ship`
* **Test Receipt Reuse via `pr_body.py suite`:**
  - Check `.tmp/3d-suite-BT-<padded>.json` (recorded by `test_gate.py record --suite` at `3d` completion).
  - If valid for current `HEAD`: **Skip the full repository test suite in `4a` entirely**.
  - Eliminates duplicate test runs while preserving full `pr_body.py` and `test_gate.py` compatibility.
* **Unified Ship Gate:**
  - Consolidate Phase 4 (audit review) and Phase 5 (ship confirmation) into a single closing gate.

#### 3. `3d-implement-issue`
* **Strictly Scoped `micro-tdd` Inner Loop:**
  - Restrict test execution during active coding strictly to unit tests covering the slice's touchpoints (`pytest tests/<domain>/test_<slice>.py`).
  - Forbid repo-wide test sweeps during 3d feature iteration.
* **Single Suite Execution at Completion:**
  - At Phase 3 Step 6 clean `HEAD`, run the full suite once through `test_gate.py record --suite BT-<padded>`. This provides the verified proof that `4a` reuses.

#### 4. `3c-sprint-planning`
* **Consolidated Sprint Gate:**
  - Surface all warnings (AFK size mismatch, new dependencies) inline within the topological DAG table.
  - Confirm sequence and priority updates in a single prompt: `[Activate Sprint Queue]`.

#### 5. `0d-nightly-consolidation`
* **Constitutional Compliance (`memory-protocol.md` §5):**
  - Never silently rewrite `.memory/` files.
  - Consolidate routine cleanups (dead links, formatting, index syncing) into a single batch recommendation with one-click approval: `[Apply Recommended Cleanups] / [Decline]`.

#### 6. `2c-reconcile-specs`
* **Exception-Only Reconciliation:**
  - User supplies the epic/context.
  - Automatically prepare unified patches for structural boilerplate; halt only on low-confidence or semantic conflicts between PRD and interface contracts.

---

## 4. Hardened Slicing Recommendation

To prevent the producer-consumer trap where changes to `3d` cause `pr_body.py build` in `4a` to fail during shipment, work is sliced by **system boundary**:

* **Slice 1 ([BT-253](https://github.com/PatN-git/Stratosphere-OS/issues/253)): Backlog & Planning Pipeline Streamlining (`3b`, `3c`)**
  - Focus: Single final verification gate in `3b`, balanced ICE inference, and consolidated DAG queue activation in `3c`.
  - Blast Radius: Zero code execution or shipping risk. Isolated to issue authoring and prioritization.
  - Size: `size:small` / `tier:slice`.
* **Slice 2 (Follow-up BT-263): Execution & Shipping Pipeline Streamlining (`3d`, `4a`, `0d`, `2c`)**
  - Focus: Scoped micro-tdd in `3d`, suite receipt reuse in `4a`, unified ship gate, and single-click maintenance approvals.
  - Blast Radius: Atomic update of the test execution and verification pipeline. Both sides of the receipt contract stay in lockstep.
  - Size: `size:medium` / `tier:slice`.

---

## 5. Conclusion & Exit Criteria Status for Spike BT-256
- Comprehensive research report compiled in `docs/research/lifecycle-interaction-streamlining-recommendations.md`.
- Adversarial systems critique completed and addressed: tooling collisions eliminated, priority distortion prevented, and constitutional compliance restored.
- **Spike BT-256 is complete and closed.**
