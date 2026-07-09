---
type: reference
name: Code Smell Baseline
description: Universal code-smell checklist for slice-level review
version: "1.0.0"
timestamp: 2026-07-09
---

# Code Smell Baseline

A universal code-smell checklist for slice-level review. Each applies unless a repo standards doc (`CODING_STANDARDS.md`, or `.memory/ARCHITECTURE.md` `[[A-xxx]]` rules) explicitly overrides it. Distinguish **hard breaches** (violate a documented rule) from **judgment calls** (heuristic smells) when reporting.

1. **Mysterious Name** — an identifier that doesn't reveal its intent or role.
2. **Duplicated Code** — the same structure repeated instead of shared/extracted.
3. **Feature Envy** — a function more interested in another module's data than its own.
4. **Data Clumps** — the same group of fields/args travelling together; should be one object.
5. **Primitive Obsession** — primitives used where a small domain type belongs.
6. **Repeated Switches** — the same `switch`/if-cascade on a type in several places.
7. **Divergent Change** — one module edited for many unrelated reasons (low cohesion).
8. **Speculative Generality** — abstraction/params/hooks added for imagined future needs.
9. **Message Chains** — `a.b().c().d()` coupling the caller to a deep object graph.
10. **Middle Man** — a unit that only delegates and adds nothing.
