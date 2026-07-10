---
name: 1a_research
description: Conduct market and competitive research to produce brief on findings, trade-offs, and recommendations.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.3"
timestamp: 2026-07-09
---

# Research

> [!NOTE]
> Optional. Trigger if problem space is unfamiliar, greenfield, or domain-heavy; else skip to `/1b_concept-framing`. Skip for small items.

**Hand-off contract:** Writes findings to `docs/research/<slug>.md` (including Opportunity scores, Served/Pain matrices, and Cost & Viability signals). Downstream: `/1b_concept-framing` detects and cites file; `/2a_write-prd` lifts scores and cost signals.

---

## Phase 1: Research Brief & Scope Routing

1. Define topic in one sentence.
2. Derive canonical slug: kebab-case core problem as 2–5 word noun phrase (strip articles, fillers, "how to", "we need").
3. Write 3–5 research questions.
4. **Route by Domain (Primary + Optional Annex):**
   - **Competitive:** focus on competitors, feature gaps, and positioning.
   - **Problem-Space:** focus on trends, tech approaches, and core pains.
   - Select **Primary Domain** (Competitive or Problem-Space).
   - Add **Optional Annex** of other type if hybrid.
5. **Route by Depth:**
    - **Quick Search:** single-iteration search. Applies citation rules; bypasses Phase 2 deep loop, work file, and refutation. Quick claims cap at `[MEDIUM]` (no refutation pass) unless load-bearing and triangulated across ≥2 source types, justified inline.
    - **Deep Research:** execute Phase 2 native loop with working file.
6. **Propose-and-Confirm Gate:**
   - **Inference:** Agent infers domain and depth from prompt; states choice with one-line rationale.
   - **Single Exchange Gating:**
     - **Deep:** derive 5–8 sub-queries and present `## Plan` checklist + proposal for approval.
     - **Quick:** propose domain + depth choice only. Plan checklist is silent.

---

## Phase 2: Execution (Native Deep-Research Loop)

> [!NOTE]
> Skip Phase 2 if running in Quick Search mode.

Maintain work file to track progress.

### 1. Durability Mechanism (The Work File)
- **Start-of-Run Cleanup:** Delete stale `docs/research/.<slug>.work.md` at start.
- **Path:** `docs/research/.<slug>.work.md`
- **Format:**
  ```markdown
  # Research Work File: <slug>
  
  ## Budget
  - Queries issued: 0 / 24

  ## Plan
  - [ ] Sub-query 1
  
  ## Findings
  - <Claim> · <URL> · <Source Type> · <Confidence [HIGH|MED|LOW]>
  
  ## Open
  - <Unanswered Questions>
  ```
- **Incremental Persistence:** Write findings immediately as each sub-query finishes.
- **Resume:** If restarted, continue from first uncompleted checklist item.
- **Loop Budget Cap:** Max 8 sub-queries per round, 3 deepening rounds, global stop at 24 search queries (not source fetches) issued across primary and annex domains. Stop loop and publish with gaps marked `[Unknown]` if cap hit.

### 2. The Loop Steps
1. **Query Decomposition:** derive 5–8 sub-queries and populate `## Plan`. Search sequentially.
2. **Gather & Tag:** per sub-query: read sources, extract findings, assign confidence, append to `## Findings`, increment queries count.
3. **Verify/Refute:** for `[HIGH]` confidence or decision-driving claims, verify citation URLs.
   - **Budget Tracking:** compute `remaining = 24 - issued`. If `remaining <= 0` → skip refutation, mark affected claims per the Loop Budget Cap rule, and do not spawn a subagent.
   - **Audit:** invoke subagent (via Antigravity invoke_subagent or Claude Code Task general-purpose) for skeptical pass. Input: `[HIGH]`/decision-driving claims, sources. Constraint: "Use at most `remaining` search queries. Fetch URLs to confirm they resolve and support claims. Return JSON per-claim: {verdict: survived|refuted|downgraded, url_resolves: bool, content_supports_claim: yes|partial|no, supporting_excerpt: str, sources, queries_used} + total_queries_used. Do not write any file (parent owns the work file)."
   - **Reconciliation:** increment work file query counter by `queries_used`; write verdicts to Findings. Downgrade unresolved/404/redirected/unsupported URLs to `[LOW]`/`[Unknown]` (paywalled/403 to `[Requires trial]`). Never publish unfetched/un-persisted URLs.
   - **Decision-Driving Claim:** claim that, if wrong, changes recommendations.
   - **Triangulation:** verify ≥2 independent source types after collapsing common origins.

### 3. Stop Conditions
Terminate loop when:
- **Question-coverage:** all Phase-1 questions answered or marked `[Unknown]`.
- **Saturation:** additional searches only surface existing facts.
- **Survived-refutation:** `[HIGH]` or decision-driving claims survived disproving passes.
- **Loop Budget Cap:** cap hit.

---

## Phase 3: Synthesis & Publication

1. **Read Working File:** If Deep Research run, read `docs/research/.<slug>.work.md` once.
2. **Select Template:** Use `.agents/workflows/.reference/research-competitive-template.md` (Competitive) or `.agents/workflows/.reference/research-problem-template.md` (Problem-Space).
3. **Format & Write:** Create `docs/research/<slug>.md`.
   - Prepend OKF frontmatter per `.agents/rules/okf-protocol.md` using `type: research`.
   - **Question Coverage Map:** include one-line map (e.g., `Question Coverage: Q1 ✓ · Q2 ✓ · Q3 [Unknown]`).
   - **Opportunity Scoring & Gap Matrix:** for Competitive runs (or Annex), build Gap Matrix and Opportunity table. A pure problem-space run records Pain + Served: [Unknown] (Opportunity lower bound). Sourced only from reviews/docs and confidence-tagged before synthesis.
   - **Cost & Viability Signals:** capture pricing and market signals (e.g., paid products, freelancer hires, keyword ad spend) under `## Cost & Viability Signals`.
   - **Synthesis Contract:** synthesize strictly from `.work.md`; no uncited/un-persisted claims.
   - **Annex:** render Optional Annex within same file (structure of the other template), not a second file. When it precedes concept framing (no candidate product yet), omit the Dunford Positioning Lens and the Us (Candidate) matrix column; include only the product-agnostic sections (Market Overview, Competitor Profiles, Landscape Patterns).
   - Enforce evidence standards. Before writing, verify every [HIGH] claim has ≥2 different-type sources; downgrade if not. Enforce `.agents/workflows/.reference/research-evidence-standards.md` rules.
4. **Cleanup:** Delete `docs/research/.<slug>.work.md`.
5. **Handoff:** Notify user: *"Research compiled at `docs/research/<slug>.md`. Run `/1b_concept-framing` to define concept."*
