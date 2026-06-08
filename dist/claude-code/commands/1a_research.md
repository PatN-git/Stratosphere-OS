---
name: 1a_research
description: Optional workflow to conduct market & competitive research for greenfield or domain-heavy features before concept framing.
type: workflow HITL
trigger: User. Do not run autonomously.
---

# Research

> [!NOTE]
> This workflow is optional. Only trigger `/1a_research` when the feature's problem space is unfamiliar, greenfield, or requires domain-heavy investigation. Most routine features bypass this and start directly at `/1b_concept-framing`.

**Hand-off contract:** Writes findings to `docs/research/<topic>.md` (managed by scaffolding step). The `/1b_concept-framing` workflow reads this file as prior-art/external research input.

---

## Phase 1: Context Definition
1. Define the topic/problem area for research.
2. Search external documentation, competitor implementations, and industry standard practices.

## Phase 2: Analysis & Synthesis
1. Gather core observations and patterns.
2. Compile competitor strengths/weaknesses and technical constraints.

## Phase 3: Publish Research
1. Write findings to `docs/research/<topic>.md`.
2. Handoff to `/1b_concept-framing`: *"Research compiled at `docs/research/<topic>.md`. Run `/1b_concept-framing` to define the concept."*
