---
description: Template for a problem-space research brief under docs/research/.
version: "2.1.0"
timestamp: 2026-09-15
---

# Research Problem Template

Instantiate into `docs/research/<slug>.md`: write the **artifact frontmatter** below
(substituting every `<placeholder>`), then the **artifact body** verbatim.

This file is not itself an OKF document - it carries no `type:`. The `type:` in
the block below is the *artifact's*.

## Artifact frontmatter

```yaml
type: research
title: "Research: <Problem Space / Topic>"
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

# Research: <Problem Space / Topic>

## Research Brief
- **Scope:** <1-sentence definition of the topic or problem area>
- **Slug:** <kebab-cased-restated-ask>
- **Questions:**
  1. <Specific research question 1>
  2. <Specific research question 2>
  3. <Specific research question 3>

## Core Problem & Trend
<Detailed description of the core problem, why it is important now, macro trends, and drivers of this problem space.>

## User Pains & Needs
<Synthesized insights about user pains, challenges, motivations, and unmet needs. What are users trying to accomplish and where do they fail or experience friction?>
Score each unmet **Need** with a **Pain** value 1-10 ("how much does it hurt?", read from forum signal — recurring complaints/"me too" = high; one-off = low) and a confidence tag using the `[HIGH]/[MEDIUM]/[LOW]` vocabulary (e.g., `Need: <unmet need> | Pain: <1-10> [HIGH|MEDIUM|LOW]`). A lone forum post is `[LOW]`. Do not use "seen it / hunch / guess" tags.


## Current State of the Art
<Overview of how this problem is solved today by users. Existing workflows, status quo, or manual workarounds.>

## Technological Approaches
<Technical analysis of potential/existing solutions. Detail different architectures, libraries, APIs, or algorithms that solve or address this problem.>

## Open Unknowns
- <Explicitly list any missing info, outstanding technical questions, or gaps in understanding.>

## Sources
> Superseded by the frontmatter `sources:` list. Record every source there;
> keep per-claim confidence inline in the body where the claim appears.
> Note: [HIGH] confidence claims require a one-line source-type justification inline (e.g., "Justification: Triangulated across two independent industry reports").
> Note: In Quick mode, non-load-bearing claims top out at [MEDIUM] confidence.
