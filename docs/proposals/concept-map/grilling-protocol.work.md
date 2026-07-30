---
type: reference
name: grilling-protocol
description: Canonical grilling guidelines (G1–G3) and vocabulary discipline (V1–V3) shared by the discovery workflows.
version: "1.0.0"
timestamp: 2026-07-30
---

# Grilling Protocol

Shared by `/1b_concept-framing` (Phase 2) and `/1c_concept-map` (Phase 2). Single source of truth for G1–G3 + V1–V3 — cite this file; never re-paste these rules into a workflow body.

## Grilling guidelines (G1–G3)

- **G1 — Recommend when grounded, open when not:** If you have a defensible basis for an answer (a codebase fact, prior art, research, or a clear best practice), give your recommended answer and the rationale, then ask the user to confirm, correct, or choose. If the answer is a genuine user decision you lack signal on, ask open-ended first and let the user frame it — then reflect a synthesis back to confirm. A recommendation is a proposal to react to, never a default that passes unexamined.
- **G2 — Facts vs Decisions:** If a codebase exists, look up facts (constants, configurations, API schemas, file structures) natively first. Do NOT grill the user on facts that are discoverable in the codebase; only grill them on decisions (preferences, constraints, desired outcomes) — a decision is the user's — put each and wait; recommending a candidate (G1) does not make the decision — only the user's confirmation does. (Also guards an AFK agent against grilling itself.)
- **G3 — Dependency-Ordered Grilling:** Walk the decision tree resolving dependency edges in order (a decision waits until its prerequisites are settled). Probe high-ambiguity axes first to resolve structural questions before grilling on local details.

## Vocabulary discipline (V1–V3)

Apply to every vocabulary term pinned during grilling:

- **V1 (Vocabulary Stress-Test):** Stress-test terms under scenario edge-cases.
- **V2 (Code-Contradiction Check):** Check terms against actual naming in code.
- **V3 (Glossary-Conflict Callout):** Verify terms do not clash with `.memory/GLOSSARY.md` `[[G-xxx]]`.
