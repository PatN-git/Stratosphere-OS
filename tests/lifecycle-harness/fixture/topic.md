# L3 fixture topic — feature-flag evaluation engine

The single subject every L3 phase carries end to end. Pinned, versioned with the harness,
never retyped per run. The User Proxy (Slice 0) sees **only this file** and the question it
is answering — never the draft brief — so these positions are the whole of what it knows.

Positions are deliberately opinionated. A proxy that hedges produces a brief with nothing
in it, and `1b` is designed to keep digging until something is there.

## One-line ask

A library that decides, locally and without a network call, whether a given feature flag is
on for a given user.

## Actor

A backend engineer on a small product team (4–8 engineers) who already has a flag ruleset
in version control and wants to evaluate it in-process, rather than calling a vendor SDK on
every request.

## Problem

Flag evaluation today means a network hop to a vendor, or a hand-rolled `if` ladder that
drifts from the ruleset. The hop costs latency on every request and fails badly when the
vendor is unreachable; the `if` ladder is untestable and silently diverges. The engineer
wants one evaluation function whose behaviour is identical everywhere and reproducible in a
test.

## Chosen framing

**Local evaluation of a declarative ruleset**, not a client for a remote decision service.
The ruleset is data the team already versions; the library only interprets it. Distribution
of the ruleset is explicitly somebody else's problem.

## Scope — in

- Boolean flags with a default fallback.
- Segment targeting on attributes supplied by the caller.
- Percentage rollout, bucketed by a hash of a caller-supplied key.
- Prerequisite flags (flag B only evaluates when flag A is on).
- Deterministic evaluation: identical ruleset + identical input → identical answer, always.

## Scope — out (non-goals)

- Fetching, polling, caching or streaming the ruleset from anywhere.
- A management UI, an admin API, or any authoring experience.
- Analytics, exposure events, experiment/metric analysis.
- Multivariate or JSON-valued flags in v1. Boolean only.
- Time-based or schedule-based activation.

## Constraints

- Pure Python, standard library only. No runtime dependencies.
- No network and no credentials at evaluation time.
- Evaluation must be deterministic against a fixed hash seed so tests cannot flake.
- Evaluation is called on the request path, so it must not do I/O.

## Prior art and how this differs

LaunchDarkly, Flagsmith, Unleash and Split all publish per-MAU pricing and all centre on a
hosted decision service with an SDK that syncs state. Unleash and Flagsmith can be
self-hosted, which removes the vendor but not the service. The difference here is that
there is no service at all: the ruleset is a file the team already has, and the library is
a pure function over it.

## Vocabulary the brief should crystallize

- **Flag** — a named boolean decision, with a default used when no rule matches.
- **Ruleset** — the declarative document holding all flags and their rules.
- **Rule** — one condition inside a flag, evaluated in order; first match wins.
- **Segment** — a named, reusable set of attribute conditions.
- **Bucketing key** — the caller-supplied string hashed to place a user in a rollout
  percentage. Avoid calling this a "user ID": it is frequently an account or device.
- **Evaluation** — one call producing one boolean plus the reason it was reached.

Avoid: "toggle" (ambiguous between the flag and the act of flipping it), "experiment"
(implies metric analysis, which is out of scope), "targeting" used bare (say segment
targeting or percentage rollout — they behave differently).

## Riskiest assumption

That a team will accept **eventual** consistency of the ruleset in exchange for zero
latency and zero runtime dependency. If flag changes must take effect within seconds, local
evaluation over a versioned file is the wrong shape and the whole framing collapses.

- **Why fatal:** the entire design exists to avoid the network hop. If freshness must be
  guaranteed, the hop returns and there is nothing left.
- **Cheapest test:** N DMs — ask 5 engineers who run flags in production what staleness they
  actually tolerate for a kill-switch versus a rollout.
- **Est. setup time:** under one week.

## Positions on questions the grill is likely to reach

- **Why not just use a vendor SDK?** The SDK is the network hop. It also makes local tests
  depend on vendor state, which is the thing that makes flag code untestable today.
- **What happens when the ruleset is missing or malformed?** Evaluation returns each flag's
  default and reports the reason. It never raises on the request path.
- **Who writes the ruleset?** The team, by hand, in the repo. Authoring is out of scope.
- **How do flags get updated in production?** By shipping a new ruleset — deploy, config
  map, whatever the team already does. Explicitly not this library's job.
- **Why bucket by hash rather than random?** Determinism. The same key must land in the same
  bucket on every host and every process, or a rollout flickers per request.
- **What is success?** A team replaces their `if` ladder with a ruleset and their flag tests
  stop being flaky. Not adoption numbers.
- **What about audit / who saw what?** Evaluation returns a reason alongside the boolean, so
  the caller can log it. The library itself stores nothing.
- **Single-tenant or multi-tenant?** Irrelevant — it is a pure function. The caller supplies
  whatever attributes it wants matched.
