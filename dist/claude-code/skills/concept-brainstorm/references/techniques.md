---
version: "1.0.0"
timestamp: 2026-07-24
---

# Concept Brainstorming - Techniques Reference

## Escape Hatch
If NO technique from the Selection Guide below fits the specific scenario, you (or the subagents) may diverge and use a custom technique. 
**Condition:** You MUST explicitly name the custom technique and define a strict tabular `Output` format for it before generating any ideas (as per Anti-Default Guard #3).

## Selection Guide

| Scenario | Technique | Skip if... |
|---|---|---|
| Default ideation | **Multi-Perspective** | — |
| Iterating existing feature | **SCAMPER** | Greenfield |
| Surfacing risks early | **Reverse Brainstorm** | Low-stakes |
| Cross-domain inspiration | **Analogous Borrowing** | Basic utility |
| Structural innovation | **Assumption Busting** | Minor bug fix |
| Stress-testing a candidate | **Six Thinking Hats** | Early divergence |
| Forecasting adoption risks | **Pre-Mortem** | Zero data dependency |

---

## Technique Reference

### Phase 1 Tools
#### CHAIN Framework
**Purpose:** Pin hard constraints before diverging.
**Steps:** **C**ontext (current stage, audience, stack). **H**one (specific outcomes). **A**sk (clarifying follow-ups). **I**ncorporate (reference benchmarks). **N**arrow (scope boundaries, non-goals).
**Output:** Confirmed constraints block (Context / Outcomes / Boundaries / Non-goals). Await sign-off.

### Phase 2 Tools (Generation)
#### Multi-Perspective Ideation (default)
**Purpose:** Generate breadth fast through standard roles.
**Steps:** Generate 3–5 ideas per lens: PM (business value, market fit), Designer (friction, delight), Engineer (feasibility, reuse).
**Output:** Single combined table: `| Lens | Idea | One-line rationale |`.

#### SCAMPER
**Purpose:** Mutate a known feature/product.
**Steps:** Apply prompts against the baseline: Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse. Skip unproductive lenses.
**Output:** Table: `| Lens | Prompt applied | Concrete idea |`.

#### Reverse Brainstorming
**Purpose:** Risk-first design.
**Steps:** 1. Invert goal ("How to guarantee user fails"). 2. List 5–10 specific failure mechanisms. 3. Flip each into a preventative constraint.
**Output:** Paired table: `| Failure mechanism | Preventative solution |`.

#### Analogous Borrowing
**Purpose:** Lift patterns from unrelated categories.
**Steps:** 1. Identify core interaction challenge. 2. Identify 2–3 products in different industries solving this pattern. 3. Translate their pattern into a candidate concept.
**Output:** Concept table: `| Interaction Challenge | Analogous Model | Borrowed Pattern |`.

#### Assumption Busting
**Purpose:** Break standard implementation tracks.
**Steps:** 1. List 5–8 unstated assumptions. 2. Invert each. 3. Brainstorm a viable concept that thrives under inversion.
**Output:** Paired table: `| Default Assumption | Inversion | Viable Concept |`.

#### Six Thinking Hats
**Purpose:** Stress-test one chosen direction.
**Steps:** Run in order: Blue (process), White (facts), Yellow (upside), Black (caution), Red (gut), Green (creativity), Blue (synthesis).
**Output:** Bulleted summary grouped by hat, ending with Blue synthesis verdict.

#### Pre-Mortem Analysis
**Purpose:** Uncover adoption risks.
**Steps:** 1. Assume feature failed 6 months post-launch. 2. Generate 5–8 reasons. 3. Write specific preventative mitigation for each.
**Output:** Table: `| Failure Mechanism | Upfront Prevention |`.

### Phase 3 & 4 Tools (Synthesis & Validation)
#### Pre-ICE Triage
**Purpose:** Rank candidate ideas without formal estimates.
**Steps:** Score each candidate: Impact (1–5, agent-scored), Confidence (1–5, user-scored). Do NOT compute final ICE score.
**Output:** Ranked table: `| Idea | Impact | Confidence | Note |` (highest first). User picks winner.

#### Opportunity Solution Tree
**Purpose:** Convert chosen idea into a testable structure.
**Steps:** Build top-down: Outcome → Opportunities → Solutions → Experiments (smallest proof for riskiest assumption).
**Output:** Nested list. Carry top 1–2 riskiest assumptions forward.
