---
description: Template for a discovery brief - locked vocabulary, problem statement and framing.
version: "2.0.0"
timestamp: 2026-09-15
---

# Discovery Brief Template

Instantiate into `docs/discovery/<slug>.md`: write the **artifact frontmatter** below
(substituting every `<placeholder>`), then the **artifact body** verbatim.

This file is not itself an OKF document - it carries no `type:`. The `type:` in
the block below is the *artifact's*.

## Artifact frontmatter

```yaml
type: discovery-brief
title: "Discovery: <one-line problem statement>"
description: ""
generated:
  by: 1b-concept-framing
  at: <ISO 8601>
status: ready-for-prd | exit-bug | exit-spike | dropped
slug: <topic-slug> # MUST be semantic slug only. Do NOT include or pre-allocate a BT-<n> ID.
linked-prd: —
version: <plugin version>   # stamped at generation (okf-protocol §5)
```

## Artifact body

# Discovery: <one-line problem statement in agreed vocabulary>

## Ask (verbatim)
> <user's original words, unedited>

## Vocabulary
<Every term used in this brief must be defined here first.>

- **<Term>:** <definition>
- **<Term>:** <definition>

## Actor
<Specific role/segment/context. Not "users.">

## Problem
<2–3 sentences. What hurts, who is affected, cost of inaction. Agreed vocabulary only. No solutions.>

## Chosen Framing
<Which framing we committed to and why.>

**Rejected framings:**
- <Framing>: <one-line reason rejected>

**Rejected approaches (brainstorm):**
*(May hold research-derived rejections, or be omitted if Phase 0 was skipped)*
- <Approach>: <one-line reason rejected>

## Prior Art
<Related BT-<n>, existing code areas, memory refs ([L-xx], [G-xx]), prior attempts.>

## Non-Goals (early signal)
<Explicitly excluded during grilling. Distinct from PRD §4 — this is verbatim from the conversation.>

- <item>

## Constraints
<User-locked technical decisions, e.g. platform, stack. No solution design.>

## Open Questions
<Residual ambiguity. write-prd absorbs these into PRD §10.>

1. <Question> — owner: <who>, blocking: Y/N

## Riskiest Assumption
- **Riskiest Assumption:** <The single fatal assumption; e.g., "both sides of marketplace show up">
- **Why Fatal:** <Why the concept fails if this assumption is wrong>
- **Cheapest Test:** <cheapest_test ∈ {landing page + waitlist | N DMs | fake-door button | rough mock shown to 5}>
- **Est. setup time:** <≤2 weeks — the cheapest test must not exceed this>
- **Status:** untested | running | survived | failed

## Recommended Next Step
- [ ] `write-prd` — problem is sharp, PRD-worthy
- [ ] `create-issue` Template B — this is a bug
- [ ] `create-issue` Template A — spike needed first
- [ ] Dropped — do not build