---
type: research
title: "Research: Local (no-network) feature flag evaluation"
description: "Problem-space scan of how libraries decide in-process, without a network call, whether a flag is on for a user."
generated:
  by: 1a-research
  at: 2026-09-16T20:10:00Z
sources:
  - resource: https://docs.getunleash.io/reference/activation-strategies
    title: Activation strategies
    author: Unleash
    last_modified: [Unknown]
  - resource: https://openfeature.dev/docs/reference/concepts/provider/
    title: "Providers | OpenFeature"
    author: OpenFeature (CNCF)
    last_modified: [Unknown]
  - resource: https://docs.developers.optimizely.com/feature-experimentation/docs/how-bucketing-works-feature-experimentation
    title: How bucketing works
    author: Optimizely
    last_modified: [Unknown]
version: "3.0.0"
---

# Research: Local (no-network) feature flag evaluation

Question Coverage: Q1 ✓ · Q2 ✓ · Q3 [Unknown]

## Research Brief

Whether a flag ruleset can be evaluated in-process, and what the established engines do
about bucketing stability, segment targeting and prerequisite chains. [MEDIUM]

## Core Problem & Trend

Vendor SDKs put a network dependency on the decision path, and teams that already keep
rulesets in version control want the decision to be a pure function of data they hold.
Local evaluation is the direction the established engines have moved toward. [MEDIUM]

## User Pains & Needs

- A network hop per decision, on the hot path. [HIGH] Justification: stated as the motivating
  constraint in both Unleash's and Optimizely's local-evaluation documentation.
- Unstable bucketing across restarts, so a user flips in and out of a rollout. [MEDIUM]
- Decisions that cannot be explained after the fact. [MEDIUM]

## Current State of the Art

Established engines evaluate locally against a ruleset they fetch and cache, keeping the
decision itself in-process. The fetch, not the decision, is what carries the network. [MEDIUM]

## Technological Approaches

Deterministic bucketing by hashing (flag key, user key) into a fixed range; segment rules
over an attribute bag; prerequisite flags evaluated before the dependent flag. [MEDIUM]

## Cost & Viability Signals

Per-MAU pricing is published across the category: free tiers with explicit ceilings, paid
tiers from roughly $0.01 to $0.05/MAU at volume, and quote-only enterprise tiers above that.
Two of the four vendors examined publish a free ceiling, with paid conversion beginning
around 10k MAU. Sustained keyword ad spend on the category indicates a funded market rather
than a hobbyist one. A local evaluator displaces that spend rather than incurring it: no
service, no network, no credentials at run time. [MEDIUM]

## Open Unknowns

- Whether cross-language bucketing parity is expected by default. [Unknown]
- How often rulesets change in practice, which bounds the staleness question. [Unknown]

## Sources
> Superseded by the frontmatter `sources:` list.
