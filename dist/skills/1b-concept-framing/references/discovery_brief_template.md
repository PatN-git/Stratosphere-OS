---
description: Template for a discovery brief - locked vocabulary, problem statement, framing, established facts, success state and decoupled follow-ups.
version: "2.1.0"
timestamp: 2026-10-13
---

# Discovery Brief Template

Instantiate into `docs/discovery/<slug>.md`: write the **artifact frontmatter** below
(substituting every `<placeholder>`), then the **artifact body** verbatim, omitting any section or sub-list marked optional.

This file is not itself an OKF document - it carries no `type:`. The `type:` in
the block below is the *artifact's*.

## Artifact frontmatter

```yaml
type: discovery-brief
title: "Discovery: <one-line problem statement>"
description: ""
generated:
  by: <1b-concept-framing | 1c-concept-map>   # the writing workflow picks one
  at: <ISO 8601>
status: ready-for-prd | exit-bug | exit-spike | dropped
slug: <topic-slug> # MUST be semantic slug only. Do NOT include or pre-allocate a BT-<n> ID.
linked-prd: —
concept-map: <#n | path> | —   # 1c sets it; 1b leaves —
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

**Scope facets (optional — views of this one problem, never separate problems):**
- **<Facet>:** <symptom / root cause / preventive dimension>

## Established Facts (as of <YYYY-MM-DD>)
<Optional — omit for greenfield. Current-system facts found by G2 lookups, so downstream phases do not re-investigate them. Each fact names its source. File paths are allowed here as evidence only.>

- <fact> — source: <file / query / doc URL>

## Chosen Framing
<Which framing we committed to and why.>

**Rejected framings:**
- <Framing>: <one-line reason rejected>

**Rejected approaches (brainstorm):**
*(May hold research-derived rejections, or be omitted if Phase 0 was skipped)*
- <Approach>: <one-line reason rejected>

## Success State
<Observable, measurable outcomes: how the maintainer, test suite or user confirms success. No implementation.>

1. <outcome>
2. <behaviour under failure or edge case>

## Prior Art
<Related BT-<n>, memory refs ([L-xx], [G-xx]), prior attempts. Current-system facts go in Established Facts.>

## Non-Goals (early signal)
<Explicitly excluded during grilling. Distinct from PRD §4 — this is verbatim from the conversation.>

- <item>

## Decoupled Follow-ups
<Wanted, but handled separately from this brief. Not non-goals. the writing workflow files nothing.>

- <topic>: <why decoupled> — existing: BT-<n> | candidate

## Constraints & Settled Decisions
<User-locked boundaries and decisions the user confirmed during the grill (G2), each with a one-line reason so the PRD does not reopen them. No solution design.>

- **<Decision>:** <choice> — why: <reason; rejected alternative>

## Open Questions
<Residual ambiguity. write-prd absorbs these into PRD §10.>

1. <Question> — owner: <who>, blocking: Y/N

## Riskiest Assumption
- **Riskiest Assumption:** <The single fatal assumption; e.g., "both sides of marketplace show up">
- **Why Fatal:** <Why the concept fails if this assumption is wrong>
- **Cheapest Test:** <cheapest_test ∈ {landing page + waitlist | N DMs | fake-door button | rough mock shown to 5 | offline sample benchmark | read-only production probe | simulation harness}>
- **Est. setup time:** <≤2 weeks — the cheapest test must not exceed this>
- **Status:** untested | running | survived | failed

## Recommended Next Step
- [ ] `write-prd` — problem is sharp, PRD-worthy
- [ ] `create-issue` Build slice — this is a bug
- [ ] `create-issue` Spike — research needed first
- [ ] Dropped — do not build