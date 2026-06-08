---
name: 1a_research
description: Optional workflow to conduct market & competitive research for greenfield or domain-heavy features before concept framing.
type: workflow HITL
trigger: User. Do not run autonomously.
---

# Research

> [!NOTE]
> Optional. Trigger only if problem space is unfamiliar, greenfield, or domain-heavy; otherwise skip to `/1b_concept-framing`.

**Hand-off contract:** Writes findings to `docs/research/<slug>.md`. `/1b_concept-framing` detects and cites this file by slug during the grill.

---

## Phase 1: Research Brief
1. Define topic/problem area in one sentence.
2. Derive the canonical slug: kebab-case the core problem as a 2–5 word noun phrase (strip articles, filler, and "how to"/"we need"). E.g. "We need AI to help review PRs" → `ai-code-review`.
3. Write 3-5 specific research questions to answer.
4. Categorize competitors:
   - **Direct:** Same audience, same core functionality.
   - **Indirect:** Different product, same customer need.
   - **Substitute:** Status quo (spreadsheets, manual workarounds).
5. Confirm scope with user before proceeding.

## Phase 2: Data Gathering
Load and follow `.agents/workflows/.reference/research-evidence-standards.md`.
- Use ≥2 source types per finding (public docs, reviews, user forums, press).
- Mark confidence: `[HIGH]` (corroborated), `[MEDIUM]` (single credible), `[LOW]` (inferred).
- Mark unknowns explicitly; never fabricate.

## Phase 3: Analysis & Synthesis
1. Build a Feature Comparison Matrix (us vs. top 3-5 competitors).
2. Profile each competitor: positioning, user motivations (why they choose them), key weaknesses, differentiators.
3. Apply Dunford positioning lens: Competitive Alternatives → Unique Attributes → Customer Value → Target Segment → Market Category.
4. Identify landscape patterns (common gaps, trends, white space).

## Phase 4: Publish Research
1. Write `docs/research/<slug>.md` using `.agents/workflows/.reference/research-template.md`.
2. Populate the YAML frontmatter (`slug`, `updated`, `status`).
3. Self-review: check citations, marked unknowns, and matrix completion.
4. Handoff: *"Research compiled at `docs/research/<slug>.md`. Run `/1b_concept-framing` to define the concept."*
