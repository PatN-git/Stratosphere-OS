---
name: frontier-interview
description: Canonical frontier interview guidelines (G1–G3), approach triangulation, hollow-consent guard, and vocabulary discipline (V1–V3) shared by Stage 1 discovery workflows.
version: "1.0.0"
timestamp: 2026-11-06
---

# Frontier Interview & Vocabulary Protocol

Shared interview mechanics for `/1b-concept-framing` and `/1c-concept-map` (each workflow sets its own question budget and cadence).

## Interview Guidelines (G1–G3)

- **G1 — Grounded Recommendation vs. Approach Triangulation:**
  - *Grounded decision:* When codebase facts, prior art, research, or constraints establish a clear best practice, give one explicit recommendation with rationale, then ask the user to confirm, correct, or choose.
  - *Divergent / structural decision:* When multiple viable paths exist or signal is low, present **Approach Triangulation** — 2–3 concrete options with explicit trade-offs plus one tentative recommendation — or ask open-ended first to let the user frame intent, then reflect a synthesis back to confirm.
  - A recommendation is a proposal to react to, never a silent default that passes unexamined.
- **G2 — Facts vs. Decisions (Silent `grep`/AST/Probe Lookup):**
  - If a codebase exists, look up discoverable facts (constants, configurations, API schemas, file structures, data models) natively and silently via `grep`, AST parsers, or file inspection before asking the user.
  - Never interview the user on discoverable facts; ask only *decisions* (preferences, constraints, trade-offs, desired outcomes). Recommending a candidate (G1) does not make the decision — only the user's confirmation does (also guards an AFK agent against answering its own questions).
  - *Empirical fork:* If a bounded local probe can settle a fact (read-only, <=2 min, in `.tmp/`; no network, installs, cost, secrets, or production), run it, log `probe: <cmd>` in `Established Facts` (or the ticket's resolution/prep comment), and ask only the remaining preference. If too costly, chart a `prototype` ticket (`1c`) or spike follow-up (`1b`); else ask.
- **G3 — Dependency-Ordered Frontier Rounds:**
  - Walk the decision tree resolving dependency edges in order: a decision waits until its prerequisites are settled. Probe high-ambiguity structural axes before local details.
  - *Round discipline:* Every question asked in a single turn must be a mutually independent frontier node; never ask a downstream question in the same turn as its unresolved prerequisite.

## Hollow Consent Guard (Not-Consent Rule)

- Hedges (*"sounds good"*, *"looks reasonable"*, *"lgtm"*), passive delegation (*"whatever you think"*), silence, and off-topic replies are **not consent**.
- Re-ask the open point; on *"whatever you think"*, present two contrasting options with their trade-offs and require an explicit pick.
- Selecting a named option (*"Option A"*) is valid consent.

## Vocabulary Discipline (V1–V3)

Apply V1–V3 to every domain term before locking it:

- **V1 (Vocabulary Stress-Test):** Stress-test candidate terms against scenario edge cases.
- **V2 (Code-Contradiction Check):** Cross-check user terms and stated behavior against actual identifiers and logic in code; surface contradictions explicitly.
- **V3 (Glossary-Conflict Callout):** Verify terms do not clash with existing `.memory/GLOSSARY.md` `[[G-xxx]]` entries or their `Avoid:` lists.
