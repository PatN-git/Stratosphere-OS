---
description: Template for a competitive research brief under docs/research/.
version: "2.1.1"
timestamp: 2026-09-15
---

# Research Competitive Template

Instantiate into `docs/research/<slug>.md`: write the **artifact frontmatter** below
(substituting every `<placeholder>`), then the **artifact body** verbatim.

This file is not itself an OKF document - it carries no `type:`. The `type:` in
the block below is the *artifact's*.

## Artifact frontmatter

```yaml
type: research
title: "Research: <Topic>"
description: ""
generated:
  by: 1a-research
  at: <ISO 8601>
sources:
  - resource: <URL>
    title: <title>
    author: <author or org>
    last_modified: <ISO 8601>
status: stable | deprecated   # deprecated once superseded or past its freshness window
slug: <kebab-case-core-topic>
version: <plugin version>   # stamped at generation (okf-protocol §5)
```

## Artifact body

# Research: <Topic>

## Research Brief
- **Scope:** <1-sentence definition of the topic or problem area>
- **Slug:** <kebab-cased-restated-ask>
- **Questions:**
  1. <Specific research question 1>
  2. <Specific research question 2>
  3. <Specific research question 3>
- **Competitors Identified:** <List of Direct, Indirect, and Substitute competitors>

## Market Overview
<Brief summary of market size, growth, macro trends, and maturity of the space.>

## Competitor Profiles

### <Competitor Name>
- **Type:** <Direct | Indirect | Substitute>
- **Positioning:** <1-sentence summary of how they position themselves in the market>
- **Why Users Choose Them:** <Customer motivations, workflows, or friction solved—not just a list of features>
- **Key Weaknesses:** <Sourced gaps, common customer complaints, pricing friction, or architectural limits>
- **Differentiators vs. Us:** <What they can/cannot do compared to our candidate capabilities>

## Competitor Gap Matrix
> **Note:** This is a needs×solutions, product-agnostic matrix to identify market gaps. For mapping specific capabilities once a candidate exists, see [Feature Comparison Matrix](#feature-comparison-matrix).

Identify top unmet Needs and evaluate how 3–7 real solutions people use today (including ugly substitutes like spreadsheets or "I don't bother") handle them. Sourced from user reviews (e.g., G2, Capterra, app stores) and evidence-backed; never guess.

| Unmet Need | Solution 1 (e.g., Competitor A) | Solution 2 (e.g., Excel) | Solution 3 (e.g., "Do nothing") | Notes / Evidence |
| :--- | :--- | :--- | :--- | :--- |
| <Need 1> | `does it well` / `does it poorly` / `doesn't do it` | | | |
| <Need 2> | | | | |

**Reading Rule:**
- If **every** solution is weak in a row (`does it poorly` or `doesn't do it`), it is a **Gap** (Differentiator Candidate).
- If **any** solution is strong in a row (`does it well`), it is **Table Stakes** (Baseline Candidate).

## Opportunity Scoring
For each Need listed above, assign a **Served** score (1-10) indicating how well today's tools address the need (bitter reviews = low, "it does that fine" = high). Use the **Pain** score (1-10) from the problem research to calculate the Opportunity score:
\[\text{Opportunity} = \text{Pain} + \max(0, \text{Pain} - \text{Served})\]
*(Formula Range: ~5 to 20. Top-ranked items represent the most underserved needs.)*

| Need | Pain (1-10) | Served (1-10) | Opportunity (5-20) | Evidence / Citation | Confidence [HIGH/MEDIUM/LOW] |
| :--- | :--- | :--- | :--- | :--- | :--- |
| <Need 1> | | | | | |
| <Need 2> | | | | | |

*Rank by Opportunity score descending.*

## Feature Comparison Matrix
> **Note:** This is a capability×competitor positioning view used once a candidate product exists. For identifying broader market gaps and opportunity scoring, see [Competitor Gap Matrix](#competitor-gap-matrix).

| Capability / Feature | Us (Candidate) *(If running before concept framing (no defined product), mark as `[To be defined in concept framing]`)* | <Competitor 1> | <Competitor 2> | Notes |
| :--- | :--- | :--- | :--- | :--- |
| <Capability A> | | | | |
| <Capability B> | | | | |

## Dunford Positioning Lens
*Strategic evaluation using April Dunford's framework to orient the product framing:*
- **Competitive Alternatives:** <What would customers do if we didn't exist? (e.g., manual Excel sheets, status quo, specific competitor)>
- **Our Unique Attributes:** <What capabilities or features do we have that the competitive alternatives lack?> *(If running before concept framing (no defined product), mark as `[To be defined in concept framing]` rather than inventing attributes)*
- **Value for Customers:** <What business or user value do those unique attributes unlock for customers?>
- **Target Segment:** <Which sub-segment of customers cares the absolute most about that unique value?>
- **Market Category:** <What frame of reference/context do we use to make our value obvious? (e.g., CRM for X, Email tool for Y)>

## Landscape Patterns
<Patterns identified across the landscape: common gaps, emerging standards, or white space we can capture.>

## Cost & Viability Signals
<Pricing and market signals: paid products and their tiers, freelancer hires, keyword ad
spend, anything indicating people already pay to solve this. Mark a signal you could not
find as [Unknown] rather than omitting it - `/2a-write-prd` section 12 cites this section
and its Cost Approval Gate cannot fire on a section that is not here.>

## Open Questions & Unknowns
- <Explicitly list any missing info, product trial requirements, or unconfirmed claims.>

