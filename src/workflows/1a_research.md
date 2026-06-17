---
name: 1a_research
description: Workflow to conduct market & competitive research for greenfield or domain-heavy features before concept framing. Routes by domain and depth.
type: workflow HITL
trigger: User. Do not run autonomously.
---

# Research

> [!NOTE]
> Optional. Trigger only if problem space is unfamiliar, greenfield, or domain-heavy; otherwise skip to `/1b_concept-framing`. For smaller items, skip `1a` entirely and proceed directly to `1b` (scope-class assigned by user-confirmed judgment in `2a`).


**Hand-off contract:** Writes findings to `docs/research/<slug>.md`. `/1b_concept-framing` detects and cites this file by slug.

---

## Phase 1: Research Brief & Scope Routing

1. Define topic/problem area in one sentence.
2. Derive canonical slug: kebab-case the core problem as 2–5 word noun phrase (strip articles, filler, and "how to"/"we need"). E.g., "We need AI to help review PRs" → `ai-code-review`.
3. Write 3–5 specific research questions to answer.
4. **Route by Domain (Primary + Optional Annex):**
   - **Competitive:** Focuses on direct, indirect, and substitute competitors, feature gaps, and positioning.
   - **Problem-Space:** Focuses on underlying trends, tech approaches, state of the art, and core user pains.
   - Select a **Primary Domain** (Competitive OR Problem-Space).
   - Add an **Optional Annex** of the other type if research is hybrid.
5. **Route by Depth:**
    - **Quick Search:** Linear, fast search. Executes targeted searches to answer Phase 1 questions → applies per-claim citation rules (see Evidence Standards) → runs the **question-coverage gate** (checks that every Phase 1 question is answered or explicitly marked `[Unknown]`, emitting a one-line visible coverage map in the published artifact under the Research Brief, e.g. `Question Coverage: Q1 ✓ · Q2 ✓ · Q3 [Unknown] · …`) → goes straight to Phase 3. Quick mode explicitly skips the Phase 2 deep loop, the `.work.md` file, and non-load-bearing refutation passes. *Note: Since non-load-bearing claims in Quick mode skip refutation, they cannot be labeled `[HIGH]` confidence and top out at `[MEDIUM]`.*
   - **Deep Research:** Execute Phase 2's native procedural loop with a durable working file.
6. **Propose-and-Confirm Gate (Single Exchange):**
   - **Inference:** The agent infers the Primary Domain (and Annex, if any) + Depth from the invocation prompt and states its default choice with a one-line rationale (e.g., "named competitors → competitive", "understand X → problem-space", "quick check on Y → problem-space, quick").
   - **Single Exchange Gating:**
     - **For Deep Research:** Derive the 5–8 targeted sub-queries and present the `## Plan` checklist along with the domain + depth proposal for ONE approval exchange (e.g., "Problem-space, deep. Plan: [6 sub-queries]. Proceed, or adjust?"). Once approved, the loop runs autonomously (ticking off checklist items in the output) without further checkpoints.
     - **For Quick Search:** Propose the domain + depth choice only. The sub-query plan is silent (no checklist shown to user). Confirm and proceed.

---

## Phase 2: Execution (Native Deep-Research Loop)

> [!NOTE]
> Skip Phase 2 if running in **Quick Search** mode. Go straight to Phase 3.

To prevent token loss and ensure progress tracking across model runs, maintain a single lightweight working file.

### 1. Durability Mechanism (The Work File)
- **Start-of-Run Cleanup:** Delete any stale `docs/research/.<slug>.work.md` files at the start of a deep run (primary safety net for orphans).
- **Path:** `docs/research/.<slug>.work.md`
- **Format:**
  ```markdown
  # Research Work File: <slug>
  
  ## Budget
  - Queries issued: 0 / 24

  ## Plan
  - [ ] Sub-query 1
  - [ ] Sub-query 2
  
  ## Findings
  - <Claim> · <URL> · <Source Type (academic|industry|doc|repo|blog)> · <Confidence [HIGH|MED|LOW]>
  
  ## Open
  - <Unanswered Phase-1 Questions>
  ```
- **Incremental Persistence:** Write every finding to the `## Findings` list immediately as each sub-query finishes.
- **Resume Capability:** If interrupted or restarted, read the checklist under `## Plan` and continue from the first uncompleted `[ ]` item.
- **Loop Budget Cap:** Hard cap of $\le$8 sub-queries per round, $\le$3 deepening rounds, and a global hard stop at 24 **search queries issued** (not source fetches) across both Primary and Annex domains. If this search query cap is reached, stop the loop and publish immediately with remaining gaps marked `[Unknown]`.

### 2. The Loop Steps
1. **Query Decomposition:** Derive 5–8 distinct, targeted sub-queries from the Phase-1 research questions and populate the `## Plan` checklist in the work file. Search each one sequentially.
2. **Gather & Tag:** For each sub-query, read the returned sources, extract findings, assign a confidence level `[HIGH|MED|LOW]`, and append each to the `## Findings` section of the work file (incremental persistence). Increment the "Queries issued" count under `## Budget` each time a sub-query search is run.
3. **Verify/Refute:** For any findings labeled `[HIGH]` confidence OR identified as decision-driving/load-bearing claims, perform a skeptical pass to actively try to REFUTE the claim and verify citation URLs.
   - **Budget Tracking:** Read the work file's issued-query count and compute `remaining = 24 - issued`. If `remaining <= 0` → skip refutation, mark affected claims per the Loop Budget Cap rule, and do not spawn a subagent.
   - **Invocation & Input:** Invoke a subagent (using Antigravity's `invoke_subagent` or Claude Code's `Task` tool with the `general-purpose` type) to perform the skeptical pass. Provide the list of `[HIGH]`/load-bearing claims + their current sources, and the strict constraint: *"You may issue at most `remaining` search queries. For each claim's citation URL, you must fetch the URL (via WebFetch or equivalent browser tools) to confirm it resolves AND its content supports the claim. Return verdicts + queries_used; do not write any file (parent owns the work file)."*
   - **Output Contract:** The subagent must return a specific format per claim: `{verdict: survived|refuted|downgraded, url_resolves: true|false, content_supports_claim: yes|partial|no, supporting_excerpt: "text", contradicting/confirming sources, queries_used}`, plus a `total_queries_used`.
   - **Reconciliation:** Increment the work-file counter by the returned `total_queries_used`, and write the verdicts back to the `## Findings` list. URLs that 404, cross-redirect to unrelated content, or whose content does not support the claim are removed or downgraded to `[LOW]`/`[Unknown]`; paywalled/403 → `[Requires trial]`. No URL is published without a successful fetch. Report the `queries_used` (scoping to `[HIGH]`/load-bearing only, respecting the 24-query budget).
   - **Definition (Decision-Driving / Load-Bearing Claim):** A claim that, if wrong, would change the research conclusion or the recommended next step.
   - **Triangulation requirement:** Verify at least 2 independent, different-type sources after collapsing common origins. The compute budget must be spent on surviving this refutation pass rather than raw source count.


### 3. Stop Conditions
Terminate the loop only when one of the following occurs:
- **Question-coverage:** Every Phase-1 research question is answered or explicitly marked `[Unknown]` in the `## Open` section of the work file.
- **Saturation (Loop-until-dry):** Additional searches only surface already-seen facts.
- **Survived-refutation:** Every claim marked `[HIGH]` confidence or decision-driving/load-bearing has survived active disproving passes.
- **Loop Budget Cap:** The cap (3 rounds / 24 search queries issued) is reached.

---

## Phase 3: Synthesis & Publication

1. **Read Working File:** If Deep Research was run, read `docs/research/.<slug>.work.md` exactly once.
2. **Select Template:**
   - If Primary Domain is **Competitive**: Use `.agents/workflows/.reference/research-competitive-template.md`.
   - If Primary Domain is **Problem-Space**: Use `.agents/workflows/.reference/research-problem-template.md`.
3. **Format & Write:** Create the single clean synthesis file at `docs/research/<slug>.md`.
   - Prepend OKF frontmatter per `.agents/rules/okf-protocol.md` using `type: research`.
   - **Question Coverage Map:** Include a one-line visible question-coverage map under the Questions list in the Research Brief (e.g., `Question Coverage: Q1 ✓ · Q2 ✓ · Q3 [Unknown] · …`) to demonstrate the gate outcome for both Quick and Deep research paths.
   - **Opportunity Scoring & Gap Matrix:** When the Primary or Annex domain is Competitive, build the Gap Matrix and the Opportunity table into `docs/research/<slug>.md`. The Problem template supplies Pain; the Competitive template supplies Served. A pure problem-space run records Pain + `Served: [Unknown]`, yielding an Opportunity lower bound. Sourced only from reviews/docs, cited, and confidence-tagged `[HIGH/MED/LOW]` in the work file before synthesis. (Consumer: `2a` lifts Opportunity scores and matrix verdicts onto §6 stories).
   - **Cost & Viability Signals:** If the feature/topic is cost-sensitive, capture per-service pricing / free-tier data and the "is-there-money-here" market signals (paid products exist, freelancers hired, ad spend on keywords) into a `## Cost & Viability Signals` section of `docs/research/<slug>.md` — evidence-backed and cited per the evidence standards. (Consumer: `2a` summarizes/cites this in PRD §12; never generates pricing).
   - **Synthesis Contract (Durable spine):** The published `docs/research/<slug>.md` is synthesized from the cited `.work.md` (read once, then deleted) and must **not** introduce un-persisted or uncited claims from the live session (citation-bound).
   - **Annex Output Mechanism:** If an **Optional Annex** was specified, render it as a section appended **within** that single output file `docs/research/<slug>.md` (using the structure of the other template), NOT as a second file. When the annex is Competitive but no candidate product exists yet (research precedes concept framing), OMIT the Dunford Positioning Lens and the 'Us (Candidate)' matrix column from the annex — include only the product-agnostic sections (Market Overview, Competitor Profiles, Landscape Patterns).

   - Enforce the evidence rules in `.agents/workflows/.reference/research-evidence-standards.md` (e.g., citation for every claim, high-confidence source triangulation, independence collapsing). Paywalled/403 sources: cite at `[MEDIUM]` max from abstract-level access unless the full text is reachable. Quick-mode `[HIGH]` requires a load-bearing claim triangulated across ≥2 distinct source types, justified inline.
   - **Synthesis-Time Verification:** For every `[HIGH]` claim in the artifact, confirm its two sources are different types; downgrade any that aren't before writing the file.
4. **Cleanup:** Delete or archive the temporary `docs/research/.<slug>.work.md` file.
5. **Handoff:** Notify the user: *"Research compiled at `docs/research/<slug>.md`. Run `/1b_concept-framing` to define the concept."*
