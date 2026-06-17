---
type: prd
title: "BT-<padded>: <Feature name>"
description: ""
timestamp: <YYYY-MM-DD>
resource: <GitHub Issue URL>
status: ready-for-design | in-progress | complete
version: "1.0.1"
---

# BT-<padded>: <Feature name>

> [!NOTE]
> **Legend & Marker Definitions:**
> - `[BASELINE]` ↔ `scope:baseline` (high-pain, well-served — build to not lose)
> - `[DIFFERENTIATOR]` ↔ `scope:differentiator` (high-pain, under-served — build to win)
> - `[DEFERRED]` ↔ `scope:deferred` (temporal deferral, mirrored in §9, not sliced in this version)
> - `[unbacked]`: Scope tag or score assigned by judgment without research backing (needs HITL confirmation)
> - `[unverified estimate — confirm]`: A figure stated without a cited research source (needs HITL confirmation)
> - `[Unknown]`: Data/value that is missing or not publicly available


## 1. Problem
- **Current experience:**
- **Who is affected:**
- **Cost of inaction:**

## 2. Solution (user view)
<3–5 sentences. User perspective only. No implementation detail.>

## 3. Goals
<3–6 outcome-oriented bullets. Verifiable. Not solutions.>

- 

## 4. Non-Goals
<≥ 3 bullets. Principled exclusions, not deferrals. Each with one-line rationale.>

- **<Non-goal>:** <rationale>

## 5. Success Signals
<2–4 qualitative or quantitative signals.>

- 

## 6. User Stories
<Numbered, comprehensive, journey-mapped, and deduped. Group stories under journey steps (Jeff Patton mapping). No per-story acceptance criteria. No slice lists.>
<Annotate every story with [BASELINE], [DIFFERENTIATOR], or [DEFERRED] scope tags, and ODI score (e.g., `(ODI: <n> [HIGH|MED|LOW]` or `ODI: -`). Mark judgment-based scores/tags as `[unbacked]` if not backed by 1a research.>

### Journey Step 1: <e.g., Initial setup / entry>
1. **[BASELINE]** As a <actor>, I want <feature>, so that <benefit>. (ODI: <n> [HIGH|MED|LOW])

### Journey Step 2: <e.g., Core interaction>
2. **[DIFFERENTIATOR]** As a <actor>, I want <feature>, so that <benefit>. (ODI: <n> [HIGH|MED|LOW])
3. **[DEFERRED]** As a <actor>, I want <feature>, so that <benefit>. (ODI: - [unbacked])


## 7. Constraints & Direction
<Hard constraints + high-level direction. ADRs fold here — no separate ADR files. No module designs, interfaces, file paths, or code.>

- **Constraint:**
- **Direction:**
- **Refs:** `[L-xx]`, `[A-xx]`, `[DR-xx]`

## 8. Definition of Done
<Feature-level observable end-state. This is the target `create-issue` slices toward.>

- 

## 9. Out of Scope
<Not in this PRD; possible future work. Distinct from §4 (principled) — §9 is temporal. Every [DEFERRED] story from §6 must be mirrored here.>

- **Deferred:** As a <actor>, I want <feature> (from §6 story #x)


## 10. Open Questions
<Resolved questions stay here with resolution noted.>

1. <Question> — owner: <who>, blocking: Y/N

## 11. Further Notes

## 12. Viability & Cost
> **Note:** Summarized and cited from research (`1a` ## Cost & Viability Signals), not generated here. Figures without cited research must be marked `[unverified estimate — confirm]`; missing values marked `[Unknown]`.
> If this feature/direction generates ongoing costs, get explicit user approval before locking the PRD.

- **Complexity Estimate:** <1–10> (Anchors: simple CRUD/to-do list ≈ 2, complex offline sync/Instagram ≈ 9)
- **Cost Table:**
  | Service / Resource | Free Tier Limit | Cost Threshold / Pricing | Source / Citation |
  | :--- | :--- | :--- | :--- |
  | <Service Name> | | | |
- **Architecture Cost Warning:** <e.g., analysis of polling vs. webhooks/events, DB load, API usage pricing risks>
- **"Is There Money Here?" (Market Demand Signals):** <Paid competitor products, freelancer hiring demand, search ad spend; cited from 1a>
- **Profit Alignment:** <Does the product earn when the user wins, or when they lose? Flag parasitic business models or conflict of interest.>
