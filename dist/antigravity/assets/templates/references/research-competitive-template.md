---
type: research
title: "Research: <Topic>"
description: ""
timestamp: <YYYY-MM-DD>
status: active | stale | superseded
slug: <kebab-case-core-topic>
version: "1.0.0"
---

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

## Open Questions & Unknowns
- <Explicitly list any missing info, product trial requirements, or unconfirmed claims.>

## Sources
- <Source URL> (Accessed: <Date>, Source Type: <academic|industry|doc|repo|blog>, Confidence: <HIGH|MEDIUM|LOW>)
> Note: [HIGH] confidence claims require a one-line source-type justification inline (e.g., "Justification: Triangulated across two independent industry reports").
> Note: In Quick mode, non-load-bearing claims top out at [MEDIUM] confidence.
