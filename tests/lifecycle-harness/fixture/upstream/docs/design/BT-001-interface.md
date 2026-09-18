---
type: interface-design
title: "Design: BT-001 - Local feature flag evaluation"
description: "The evaluation contract and ruleset schema. Non-UI (Path C)."
generated:
  by: 2b-interface-design
  at: 2026-09-16T20:40:00Z
status: stable
slug: local-feature-flag-evaluation
bt: BT-001
prd: docs/prds/BT-001-local-feature-flag-evaluation.md
surface: non-ui
version: "3.0.0"
---

# Design: BT-001 - Local feature flag evaluation

## Surface & Scope

No user interface. The surface is a library contract consumed by other code: one
evaluation function plus the ruleset schema it reads. Path C (non-UI contract).

## Actors & Core Flows

A backend engineer loads a ruleset once at start-up, then evaluates it per request. The
library never fetches anything; the caller owns the ruleset's lifecycle.

## Aha Moment & Time-to-Value

First correct decision from a hand-written ruleset in under five minutes, with no client to
construct and nothing to configure.

## Direction Alternatives (Considered)

- **Chosen: pure evaluator, caller owns the ruleset.** Smallest surface; no I/O anywhere.
- Rejected: an evaluator that also loads rulesets from disk — couples the decision path to
  a file format and puts I/O back on the hot path.
- Rejected: a client object with a background refresh — reintroduces the network hop and
  the staleness question the discovery brief rules out.

## States / Edge Classes

- Empty ruleset → every flag returns its default.
- Unknown rule type → rejected at parse time, naming the rule.
- Prerequisite cycle → rejected at parse time.
- Missing attribute in the user context → the rule does not match; evaluation continues.

### UX / System Stress Matrix

| Stress | Expected behaviour |
|:---|:---|
| 10k evaluations per second | No allocation-heavy work per call; no I/O |
| Malformed ruleset | Parse fails once, loudly, before any evaluation |
| Context missing the bucketing key | Percentage rules do not match; default returned |

## Handoff Notes for 3c/4a

Deterministic throughout: a fixed hash and a fixed seed, so tests need no tolerance
windows. No CSS, no theme tokens, no UI surface of any kind.

### [Path C · Non-UI] Interface Contract

```
evaluate(ruleset: Ruleset, flag_key: str, context: Context) -> Decision
```

- `Ruleset` — parsed flag definitions. Built by `parse_ruleset(document) -> Ruleset`,
  which raises `RulesetError` naming the offending rule.
- `Context` — `{"key": str, **attributes}`. `key` is the stable bucketing identity.
- `Decision` — `{"value": Any, "reason": str, "rule": str | None}`. `reason` is one of
  `default`, `rule_match`, `percentage`, `prerequisite_off`.
- Evaluation performs no I/O and raises nothing for a well-formed ruleset.
