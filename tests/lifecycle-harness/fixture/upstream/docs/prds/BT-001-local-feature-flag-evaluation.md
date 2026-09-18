---
type: prd
title: "BT-001: Local feature flag evaluation"
description: "In-process evaluation of a flag ruleset against a user context, with no network I/O on the evaluation path."
bt: BT-001
generated:
  by: 2a-write-prd
  at: 2026-09-16T20:30:00Z
resource: https://github.com/l3-harness/throwaway/issues/1
status: stable
version: "3.0.0"
---

# BT-001: Local feature flag evaluation

## 1. Problem

A backend engineer on a small team already keeps a flag ruleset in version control and
wants to evaluate it in-process. Calling a vendor SDK on every request adds a network hop
to the hot path, makes evaluation fail open or closed on the vendor's availability, and
makes the decision unauditable after the fact. The team wants the decision to be a pure
function of data it already holds.

## 2. Solution (user view)

A library with one entry point: hand it a ruleset and a user context, get back a decision
and the reason for it. No client to construct, no background poller, no network.

## 3. Goals

- Evaluation is a pure function: same ruleset plus same context always yields the same
  decision, in-process, with no I/O.
- Percentage rollouts are stable: a user stays in the same bucket across evaluations,
  processes and restarts.
- The decision carries its reason, so a log line explains why a user saw what they saw.

## 4. Non-Goals

- Fetching, polling or caching rulesets. The caller supplies one.
- A management UI, an audit trail service, or anything with a network surface.
- Cross-language bucketing parity in v1 (recorded as an open question, not a commitment).

## 5. Success Signals

- A rollout percentage change moves the expected proportion of users, within sampling error.
- No evaluation path in the library performs I/O — verifiable by test.

## 6. User Stories

### Journey Step 1: Parse a ruleset
As a backend engineer, I hand the library a ruleset document so that it is validated once,
up front, and I learn about a malformed rule at load time rather than at decision time.
- A ruleset with an unknown rule type is rejected with the offending rule identified.
- A valid ruleset parses into an evaluable form with no I/O.
- ODI confidence: [HIGH]

### Journey Step 2: Evaluate a boolean and segment-targeted flag
As a backend engineer, I evaluate a flag for a user context so that the decision reflects
the targeting rules I wrote.
- A flag with no rules returns its default.
- A segment rule matching the context returns the rule's value; a non-matching one falls
  through to the next rule, then to the default.
- The decision names the rule that produced it.
- ODI confidence: [HIGH]

### Journey Step 3: Roll out by percentage
As a backend engineer, I roll a flag out to a percentage of users so that the same user is
always assigned to the same bucket.
- Bucketing is deterministic in (flag key, user key) and stable across processes.
- A 0% rollout is off for every user; 100% is on for every user.
- Assignment is approximately uniform across buckets for a large user sample.
- ODI confidence: [HIGH]

### Journey Step 4: Chain prerequisite flags
As a backend engineer, I make one flag depend on another so that a dependent feature cannot
be on while its prerequisite is off.
- A flag whose prerequisite evaluates off returns its default, with the prerequisite named
  as the reason.
- A prerequisite cycle is rejected at parse time, not at evaluation time.
- ODI confidence: [MEDIUM]

## 7. Constraints & Direction

- Pure Python, standard library only. No dependencies, no network, no credentials.
- The hash used for bucketing is fixed and documented, so a rollout is reproducible.
- Evaluation must not raise on a well-formed ruleset: an unmatched context yields the
  default, never an exception.

## 8. Definition of Done

- Ruleset parsing rejects malformed rules with the offending rule identified.
- Boolean and segment targeting evaluate per the rules, falling through to the default.
- Percentage rollout is deterministic and stable across processes for a fixed seed.
- Prerequisite chains are honoured and cycles are rejected at parse time.
- Every behaviour above is covered by a test that runs with no network.

## 9. Out of Scope

- Ruleset transport, storage, or format migration.
- Any remote decisioning or streaming update mechanism.

## 10. Open Questions

- Is identical cross-language bucketing a committed v1 guarantee or a deferred non-goal?
- Which runtime is the first implementation target, and is a second-language port in scope?

## 11. Further Notes

Derived from `docs/discovery/local-feature-flag-evaluation.md` and
`docs/research/local-feature-flag-evaluation.md`.

## 12. Viability & Cost

| Item | Signal | Confidence |
|:---|:---|:---|
| Vendor per-MAU pricing | Published tiers from free to ~$0.05/MAU at volume; enterprise is quote-only | [MEDIUM] |
| Paid conversion point | Free ceilings published by two of four vendors, paid begins around 10k MAU | [MEDIUM] |
| Ongoing cost of this feature | None at run time: no service, no network, no credentials | [HIGH] |

**Cost Approval Gate:** this feature introduces no ongoing cost. The pricing landscape above
is the alternative being displaced, not a cost being incurred. Complexity score: 4/10.
