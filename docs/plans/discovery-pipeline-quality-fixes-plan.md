# Plan — Discovery→Design pipeline quality fixes (tracker)

**Status:** Scoped, not implemented. Awaiting per-item go/no-go (see Open Decisions).
**Target:** Branch `claude/v3-polish-discovery-pipeline-kn3h6l` (base `main`), v3.0.x line.
**Source of truth:** [`docs/proposals/FEAT-discovery-pipeline-quality-fixes-proposal.md`](../proposals/FEAT-discovery-pipeline-quality-fixes-proposal.md) (v1.1.0). This plan is a *tracker* — it references the proposal for the analysis and evidence rather than duplicating it (per the "reference, don't duplicate" handover principle the proposal itself adopts). Read the proposal for the *why*; use this file for *state + decisions*.

> **Do not lose track:** the proposal is the spec; this is the checklist that survives across sessions. Update the status column here as items land. Line numbers drift — re-anchor every edit by content.

---

## 1. Work items — status

Ordered by the proposal's lowest-risk-first sequencing.

| # | Item | File(s) | Sev | Ready? | Status |
|---|------|---------|-----|--------|--------|
| F4 | `[MEDIUM]` → `[MED]` tag | `1a` | P3 | ✅ unambiguous | ☐ not started |
| F5 | add `Est. setup time` to brief template | `discovery_brief_template.md` (+`1b` if contract touched) | P3 | ✅ unambiguous | ☐ not started |
| F1 | freshness gate `updated:` → `timestamp:` | `1b:73` | **P1** | ✅ unambiguous | ☐ not started |
| F2 | `1c` glossary write needs confirmation gate | `1c:74` | P2 | ✅ unambiguous | ☐ not started |
| F3 | `1c` Converge self-review + user gate | `1c:68–76` | P2 | ⚠ **blocked** on intent (D1) | ☐ not started |
| Q3 | `1b`→`2a` handover fidelity (4 fixes) | `2a` (+`1b`/brief link) | — | ✅ additive, safe | ☐ not started |
| Q2 | `1b` grill stop-conditions (confirmation gate) | `1b` | — | ⚠ scope choice (D2) | ☐ not started |
| Q1 | `2b` full-stack path coverage | `2b` (+readers `3b`/`3d`/`4a`) | — | ⚠ highest blast radius | ☐ not started |
| Q4 | **NEW** — optional batched-grill mode for `1b` | `1b` | — | ⚠ new, needs decision (D3) | ☐ proposed below |

**Recommended first cut (all unambiguous, low blast radius):** F4 + F5 + F1 + F2. One commit, `1a`/`1b`/`1c`/template only. F3/Q1/Q2/Q4 follow once their decisions resolve.

---

## 2. Benchmark research findings (2026-07-24 session)

Answers to the three follow-up questions, benchmarked against Matt Pocock's current + in-progress skills. Sources at the bottom.

### B1 — how Pocock batches questions, and what we should implement (→ Q4)

**His mechanic (`batch-grill-me`, in-progress):** grills in **rounds** instead of one-at-a-time. Each round asks the whole **frontier** — *"every decision whose prerequisites are already settled — the questions you can ask now without guessing at answers you haven't heard yet"* — numbered, each with a recommended answer. After answers, *"settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round."* Environmental facts are dispatched to a sub-agent in parallel (*"a running exploration is an unsettled prerequisite, so only the questions downstream of it wait"*). Done when *"the frontier is empty: every branch of the design tree visited, nothing left silently assumed,"* then user confirms shared understanding. Note: the **stable** `grill-me` is still one-at-a-time (*"asking multiple questions at once is bewildering"*); batching is his experimental evolution.

**Why this fits StratOS unusually well:** `1c_concept-map` **already** computes a "frontier" (`1c:46` *"Calculate Frontier: the set of open, unblocked, unassigned decision tickets"*) and already allows batching (`1c:64` *"independent, cheap frontier tickets may be batched if they fit the context limit"*). So the frontier vocabulary is native to StratOS — it just lives in `1c` (map layer), not in `1b`'s grill loop, which is strictly one-at-a-time (G3 dependency-ordered).

**Proposed implementation (Q4) — optional batched mode for `1b`, opt-in, not a default:**
- Add a batched variant to `1b` Phase 2, gated to the **generate/longer path where a work file already exists** (the `## Coverage checklist` *is* the frontier substrate) and to explicit user opt-in or AFK runs.
- Round mechanic: ask every currently-answerable focus-area question in one numbered batch, each with a recommended answer (reuse G1's recommend-when-grounded); collect; mark settled items on the coverage checklist; recompute; next round.
- Keep **one-at-a-time as the default** for high-ambiguity structural questions — G3 still resolves structure first (matches Pocock keeping batching experimental and his "bewildering" caveat).
- Reuse the word "frontier" for consistency with `1c`; do not invent a new term.
- **Interaction:** the batch stop condition (frontier empty + confirm) is the *same* gate Q2 wants to make primary — implement Q2 first so Q4's stop lands on the confirmation gate, not the coverage checkboxes.

**Recommendation:** adopt Q4 as an **opt-in mode only** (not a rewrite of the default loop). Rationale: Pocock himself keeps it experimental; one-at-a-time protects the high-ambiguity structural phase; StratOS already has the frontier machinery to make the opt-in cheap. If rejected, the fallback is to do nothing (1b stays one-at-a-time) — no loss.

### B2 — how his skill knows *what* to question

The `grilling` skill derives a **decision tree from the concept/plan in context** and walks it in dependency order (*"walk down each branch of the decision tree, resolving dependencies between decisions one-by-one"*). It does **not** consult a concept map inside the grilling skill — the *map* is a separate layer (`/wayfinder`: *"a central map that grows as I learn more about the problem and shrinks as I find answers"*). Facts are looked up (explore the codebase); decisions are put to the human.

**Implication for StratOS (validation, no change needed):** StratOS already splits these the same way — `1b`/G3 is the decision-tree walk, `1c` is the concept-map layer. The architecture is aligned with the role model. The only actionable pull-through is B1/Q4 (bring `1c`'s frontier idea into `1b`'s loop as an option).

### B3 — did `to-prd` → `to-spec` add content, or just rename? (→ possible D4, low priority)

Per the v1.1.0 changelog it is framed as a **rename + conceptual reframe, not a documented section expansion**: *"`to-prd` is renamed to `to-spec` — 'spec' is now the single through-line term (it still opens with 'you may know this document as a PRD' for discoverability)."* The driver was scope-leak: a "PRD" implies product-only, but the artifact was absorbing non-product (technical/process) content, so "spec" (technical, non-technical, or a blend) is the broader honest term. The separate v1.1 structural change was a *different* merge (`to-plan` + `to-issues` → `to-tickets`, tracer-bullet vertical slices with blocking edges).

Current `to-spec` artifact sections: Problem Statement · Solution · User Stories (long numbered list) · Implementation Decisions · Testing Decisions · Out of Scope · Further Notes. It **synthesizes from the existing conversation only** (*"Do NOT interview the user — just synthesize what you already know"*) — the same non-re-interview principle behind Q3.

**Implication for StratOS:** `2a_write-prd` keeps the "PRD" name. Not a defect — StratOS separates PRD (`2a`, product/requirements) from the design doc (`2b`, technical), so the scope-leak Pocock hit is already structurally avoided. **Optional, low-priority** consideration only: adopt the "you may know this as a PRD" framing if StratOS PRDs ever start absorbing non-product content. No action unless that leak is observed. Not added to the work-item table.

---

## 3. Open Decisions (C)

Blocking-first. These gate the ⚠ items above; the ✅ items (F1/F2/F4/F5, Q3) need none.

- **D1 (blocks F3):** Should `1c` convergence be a **hard HITL stop** like `1b` Phase 6 (recommended), or was it intentionally auto-closing for AFK runs? If AFK-auto-close is intended, F3 becomes *"log the skip as residual risk"* (the `1b:99` AFK-RAT-decline pattern) instead of a blocking gate.
- **D2 (scopes Q2):** Full rewrite of `1b` Phase 2 stop conditions (all 4 fixes: confirmation gate primary + delete stop-cond-2 + reframe check-in + "no fixed budget" norm), or minimal (fixes 1–2 only)?
- **D3 (gates Q4 — new):** Adopt the optional batched-grill mode for `1b`? Recommended as **opt-in / AFK-only**, default stays one-at-a-time. Or reject (no change).
- **D4 (optional, low priority):** Adopt Pocock's "spec" reframe hint in `2a` PRDs? Default: **no** — StratOS's `2a`/`2b` split already avoids the scope-leak. Revisit only if leak observed.
- **D5 (packaging):** One PR for the unambiguous first cut (F1/F2/F4/F5), then follow-ups? Or split by risk tier (defects / handover / grill-depth / 2b) into separate PRs?
- **D6 (ship path):** Confirm `improve-workflows-skills` discipline → edit `src/`, one OKF version bump per touched file per PR, rebuild `dist/`, then `/4a_verify-and-ship`. (Do NOT hand-edit `dist/` or `.agents/`.)

---

## 4. Sources (benchmark research)

- [The /grilling Skill](https://www.aihero.dev/skills-grilling) · [grilling/SKILL.md](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)
- [batch-grill-me (in-progress)](https://github.com/mattpocock/skills/tree/main/skills/in-progress/batch-grill-me)
- [The /to-spec Skill](https://www.aihero.dev/skills-to-spec) · [to-spec/SKILL.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md)
- [v1.1.0 CHANGELOG](https://github.com/mattpocock/skills/blob/main/CHANGELOG.md) · [Release v1.1.0](https://github.com/mattpocock/skills/releases/tag/v1.1.0)
- [/wayfinder](https://www.aihero.dev/skills-wayfinder) (the map layer) · [Pocock on wayfinder + central map](https://x.com/mattpocockuk/status/2072716979195326905)
