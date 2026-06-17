---
name: brainstorm-techniques
description: brainstorm-techniques
version: "1.0.0"
updated: 2026-06-17
---

# Brainstorm Technique Library

Techniques for Phase 0 concept framing, organized by the brainstorm pass they serve. The orchestrator (`1b_concept-framing.md` Phase 0) sets the default path; consult this file for depth or to pick a situational technique. Pick ONE optional technique per pass — do not run all.

## Selection Guide

| When the situation is... | Use | Pass | Skip if... |
|---|---|---|---|
| Gathering hard limits before ideating | CHAIN | Extract | Constraints already explicit |
| Every Generate pass (default ideation) | Multi-Perspective | Diverge | — (always run) |
| Iterating on an existing feature/product | SCAMPER | Diverge | Greenfield, no baseline to modify |
| Surfacing risks or failure modes early | Reverse Brainstorming | Diverge | Low-stakes / easily reversible |
| Lifting design patterns from unrelated categories | Analogous Borrowing | Diverge | Basic utility tool with no UX depth |
| Breaking out of standard/incremental loops | Assumption Busting | Diverge | Standard bug fix or minor maintenance task |
| Stress-testing a single chosen candidate | Six Thinking Hats | Converge | Still in early divergence |
| Uncovering blind spots and adoption risks | Pre-Mortem Analysis | Converge | Minimal complexity or zero data dependency |
| Selecting among candidates | Pre-ICE Triage | Converge | — (always, before naming a winner) |
| Bridging the winner into the grill phase | Opportunity Solution Tree | Bridge | — (do this last) |

---

## Pass 1 — Extract Constraints

### CHAIN Framework
Purpose: pin hard constraints before diverging, so ideas stay inside the real solution space.
Steps:
- **C**ontext — current product stage, target audience, business model, existing stack.
- **H**one — the specific outcomes this brainstorm must serve.
- **A**sk — iterative clarifying follow-ups until the goal is unambiguous.
- **I**ncorporate — reference comparable successful patterns or benchmarks.
- **N**arrow — explicit scope boundaries and non-goals.
Output: a confirmed constraints block (Context / Outcomes / Scope boundaries / Non-goals) the user signs off before divergence begins.

---

## Pass 2 — Diverge

### Multi-Perspective Ideation (default)
Purpose: generate breadth fast by viewing the opportunity through three standard roles.
Steps — generate 3–5 ideas per lens:
- **PM lens** — business value, viability, target outcomes, revenue, market fit, retention.
- **Designer lens** — desirability, friction reduction, delight, accessibility, workflow fit.
- **Engineer lens** — technical feasibility, architectural leverage, scalability, reuse, novel capability.
Output: a single combined table — `| Lens | Idea | One-line rationale |` — 3–5 rows per lens.

### SCAMPER — iterate on an existing concept
Purpose: systematically mutate a known feature/product to surface adjacent ideas.
Steps — apply each lens as a prompt against the baseline; skip lenses that yield nothing (don't force all 7):
- **S**ubstitute — swap a component, material, or rule.
- **C**ombine — merge with another feature, flow, or dataset.
- **A**dapt — borrow an analogous solution from another domain.
- **M**odify/Magnify — scale up, emphasize, or exaggerate.
- **P**ut to another use — serve a new audience or job.
- **E**liminate — remove or strip to the core.
- **R**everse — invert order, flow, or assumption.
Output: a table — `| Lens | Prompt applied | Concrete idea |` — one row per productive lens.

### Reverse Brainstorming — risk-first design
Purpose: find failure modes by designing for failure, then inverting.
Steps:
1. State the inverted goal: *"How would we guarantee the user completely fails at [X]?"*
2. List 5–10 concrete failure mechanisms (specific — "no error on bad input", not "bad UX").
3. Flip each into a preventative feature or constraint.
Output: a paired table — `| Failure mechanism | Preventative solution |`. Any mechanism with no clean preventative becomes an Open Question for the grill phase.

### Analogous Borrowing — cross-domain design
Purpose: lift proven paradigms from best-in-class, unrelated categories.
Steps:
1. Identify the core user interaction challenge (e.g., onboarding, visual configuration, database schema editing).
2. Identify 2–3 products in entirely different industries famous for solving this pattern (e.g., Figma for collaboration, Duolingo for progression, Stripe for friction-free setup).
3. Ask: *"How would [Product] solve our challenge?"* Translate their pattern into a candidate concept.
Output: a concept table — `| Interaction Challenge | Analogous Model | Borrowed Pattern |`.

### Assumption Busting — structural innovation
Purpose: break out of standard implementation tracks by identifying and intentionally inverting default industry or product assumptions.
Steps:
1. List 5–8 unstated assumptions about the problem or solution space (e.g., "Users must log in to view reports", "We need a standard SQL database for transaction logs", "We must build a setting configuration page").
2. Invert each assumption (e.g., "Reports are sent via magic links in email without login", "Transaction logs write to an append-only text file", "Features auto-configure based on context with zero settings").
3. Brainstorm a viable concept that thrives under the inverted assumption.
Output: a paired table — `| Default Assumption | Inversion | Viable Concept |`.

---

## Pass 3 — Converge / Evaluate

### Six Thinking Hats — stress-test a candidate
Purpose: pressure-test one chosen direction from six fixed angles so none is skipped.
Run in order (Blue bookends):
1. **Blue** (process) — state the decision this session must reach.
2. **White** (facts) — known data/constraints; what's missing.
3. **Yellow** (upside) — best-case value if it works.
4. **Black** (caution) — risks, failure modes, what breaks.
5. **Red** (gut) — instinctive reaction, delight/friction signals (no justification needed).
6. **Green** (creativity) — given the above, what variations or escapes exist.
7. **Blue** (synthesis) — decide: proceed, pivot, or drop.
Output: a bulleted summary grouped by hat, ending with the Blue synthesis verdict.

### Pre-Mortem Analysis — failure forecasting
Purpose: uncover project blind spots and adoption risks by working backward from assumed future failure.
Steps:
1. Set the premise: *"Assume the feature launched and was a complete disaster 6 months post-launch."*
2. Generate 5–8 concrete reasons for the catastrophe (e.g., database lockups, high user friction, API billing overrun).
3. For each reason, write a specific preventive mitigation to build in upfront.
Output: a table — `| Failure Mechanism | Upfront Prevention |`. Mechanisms with high likelihood/impact and no clean mitigation become Open Questions for the grill phase.

### Pre-ICE Triage — select the winner
Purpose: rank candidate ideas with coarse ICE vocabulary without over-formalizing.
Steps — score each candidate:
- **Impact (1–5, agent-scored):** how strongly it moves the target outcomes if it succeeds.
- **Confidence (1–5, user-scored):** how sure we are the approach works and is buildable.
Do NOT compute a final ICE score — ideas aren't sized yet (no Effort estimate). The formal ICE score is assigned later when the winner becomes a `BT-<n>` in `/3a_create-issue`.
Output: a ranked table — `| Idea | Impact | Confidence | Note |` — highest first; user picks the winner.

---

## Pass 4 — Bridge to Grill

### Opportunity Solution Tree — hand the winner to the grill phase
Purpose: convert the chosen idea into a testable structure that feeds 1b's grill phase.
Build top-down:
- **Outcome** — the measurable result we want (not a feature).
- **Opportunities** — customer pains/needs that, solved, drive the outcome.
- **Solutions** — candidate features under each opportunity.
- **Experiments** — the smallest proof that validates the riskiest assumption per solution.
Output: a nested list (Outcome → Opportunities → Solutions → Experiments). Carry the top 1–2 riskiest assumptions forward as grill-phase focus areas.
