---
description: Template for a concept map - a foggy multi-session idea charted into decision tickets.
version: "2.0.0"
timestamp: 2026-09-15
---

# Concept Map Template

Instantiate into `docs/discovery/<slug>.map.md`: write the **artifact frontmatter** below
(substituting every `<placeholder>`), then the **artifact body** verbatim.

This file is not itself an OKF document - it carries no `type:`. The `type:` in
the block below is the *artifact's*.

## Artifact frontmatter

```yaml
type: concept-map
title: "Concept Map: <one-line destination statement>"
description: "Maps a foggy, multi-session idea into decision tickets on the tracker."
generated:
  by: 1c-concept-map
  at: <ISO 8601>
status: draft | stable   # draft while the map is open; stable once converged
slug: <topic-slug>
version: <plugin version>   # stamped at generation (okf-protocol §5)
```

## Artifact body

# Concept Map: <one-line destination statement>

## Destination
<Define the concrete boundary of what this concept is aiming to accomplish. This fixes the scope of the discovery phase.>

## Notes
<Domain context, relevant code areas, key resources, and lists of skills or experts to consult.>

## Not yet specified (fog)
<Enumerate the open, ambiguous areas that are not yet sharp enough to turn into precise decision tickets. As details become clear, graduate them into decision tickets below.>

## Out of scope
<Explicitly document decisions, features, or paths ruled out of scope for this concept to prevent scope creep.>

## Decisions so far
<An index of all closed decision tickets resolved during this concept map lifecycle. Note that the actual answers and resolutions live as comments on the closed tickets themselves.>

- [<ticket title>](<#/link>) — <gist of the decision>
