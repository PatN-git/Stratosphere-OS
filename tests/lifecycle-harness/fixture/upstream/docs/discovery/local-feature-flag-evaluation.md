---
type: discovery-brief
title: "Discovery: deciding a feature flag's state for a user in-process, with no network I/O"
description: "Locked vocabulary, problem statement and framing for local flag evaluation."
generated:
  by: 1b-concept-framing
  at: 2026-09-16T20:20:00Z
status: ready-for-prd
slug: local-feature-flag-evaluation
linked-prd: BT-001
version: "3.0.0"
---

# Discovery: deciding a feature flag's state for a user in-process, with no network I/O

## Ask (verbatim)

A library that decides, locally and without a network call, whether a given feature flag is
on for a given user.

## Vocabulary

- **Evaluation:** resolving one flag key against one user context to a value. Bounded to a
  single in-process function call. Avoid: flag check, lookup.
- **Ruleset:** the full set of flag definitions and their targeting rules, held in memory as
  data the evaluator reads. The evaluator is handed a ruleset; it never fetches one.
  Avoid: config, flag config.
- **User context:** the attribute bag identifying who is being evaluated (stable user key
  plus arbitrary attributes), supplied per evaluation by the caller. Avoid: user, profile.
- **Bucketing:** deterministically mapping (flag key, user key) to a position in a fixed
  range, so percentage rollouts assign the same user to the same bucket every time.
  Avoid: sampling, randomization.

## Actor

A backend engineer on a team of four to eight, who already keeps a flag ruleset in version
control and wants to evaluate it in-process rather than calling a vendor SDK per request.

## Problem

Evaluation currently costs a network hop on the hot path, fails with the vendor, and leaves
no local explanation of why a user saw what they saw.

## Chosen Framing

**Evaluation is a pure function of (ruleset, context).** The caller owns fetching; the
library owns deciding. Rejected: an evaluator that also loads rulesets (couples the decision
path to a file format), and a client with background refresh (reintroduces the network).

## Prior Art

Established engines already evaluate locally against a cached ruleset; the fetch is what
carries the network, not the decision.

## Non-Goals (early signal)

- Fetching, polling or caching rulesets.
- Any network surface, management UI or audit service.

## Constraints

Pure standard library. Deterministic bucketing with a documented hash. No exception on a
well-formed ruleset.

## Open Questions

- Is identical cross-language bucketing a committed v1 guarantee? [blocking]
- Which runtime is the first implementation target? [blocking]

## Riskiest Assumption

That deterministic bucketing on a stable user key is sufficient for teams to trust a rollout
percentage without a central service. Cheapest test: implement the bucketing function alone
and check distribution uniformity plus cross-process stability - under a day.

## Recommended Next Step

`/2a-write-prd`.
