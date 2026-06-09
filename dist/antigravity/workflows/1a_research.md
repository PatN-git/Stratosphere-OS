---
name: 1a_research
description: Workflow to conduct market & competitive research for greenfield or domain-heavy features before concept framing. Routes by domain and depth.
type: workflow HITL
trigger: User. Do not run autonomously.
---

# Research

> [!NOTE]
> Optional. Trigger only if problem space is unfamiliar, greenfield, or domain-heavy; otherwise skip to `/1b_concept-framing`.

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
    - **Quick Search:** Linear, fast search. Executes targeted searches to answer Phase 1 questions → applies per-claim citation rules (see Evidence Standards) → runs the **question-coverage gate** (checks that every Phase 1 question is answered or explicitly marked `[Unknown]`) → goes straight to Phase 3. Quick mode explicitly skips the Phase 2 deep loop, the `.work.md` file, and non-load-bearing refutation passes. *Note: Since non-load-bearing claims in Quick mode skip refutation, they cannot be labeled `[HIGH]` confidence and top out at `[MEDIUM]`.*
   - **Deep Research:** Execute Phase 2's native procedural loop with a durable working file.
6. **Propose-and-Confirm Gate (Single Exchange):**
   - **Inference:** The agent infers the Primary Domain (and Annex, if any) + Depth from the invocation prompt and states its default choice with a one-line rationale (e.g., "named competitors → competitive", "understand X → problem-space").
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
2. **Gather & Tag:** For each sub-query, read the returned sources, extract findings, assign a confidence level `[HIGH|MED|LOW]`, and append each to the `## Findings` section of the work file (incremental persistence).
3. **Verify/Refute:** For any findings labeled `[HIGH]` confidence OR identified as decision-driving/load-bearing claims, perform a skeptical pass to actively try to REFUTE the claim.
   - **Definition (Decision-Driving / Load-Bearing Claim):** A claim that, if wrong, would change the research conclusion or the recommended next step.
   - Triangulation requirement: Verify at least 2 independent, different-type sources after collapsing common origins. The compute budget must be spent on surviving this refutation pass rather than raw source count.

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
   - Ensure it includes the shared YAML frontmatter:
     ```yaml
     ---
     slug: <canonical-slug>
     updated: <YYYY-MM-DD>
     status: active
     ---
     ```
   - **Annex Output Mechanism:** If an **Optional Annex** was specified, render it as a section appended **within** that single output file `docs/research/<slug>.md` (using the structure of the other template), NOT as a second file.
   - Enforce the evidence rules in `.agents/workflows/.reference/research-evidence-standards.md` (e.g., citation for every claim, high-confidence source triangulation, independence collapsing).
4. **Cleanup:** Delete or archive the temporary `docs/research/.<slug>.work.md` file.
5. **Handoff:** Notify the user: *"Research compiled at `docs/research/<slug>.md`. Run `/1b_concept-framing` to define the concept."*
