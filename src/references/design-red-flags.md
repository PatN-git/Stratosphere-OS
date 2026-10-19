---
description: Named structural red flags to screen a non-UI interface design (2b Path C) against; one vocabulary for design and audit; flags defined elsewhere are pointers.
version: "1.0.0"
timestamp: 2026-10-14
---

# Design Red Flags

Screen each candidate interface: name flags that apply, skip rest. Hit → revise or reject shape. Next contributor is an agent: sees only opened files, copies nearest example, takes shortest path that compiles. Prefer design where a change right from one file is right repo-wide.

## Shallow module
Depth, Deletion Test: `.memory/ARCHITECTURE.md` vocabulary. Depth concentrates capability behind one interface; deep call chain scatters it across layers.

## Information leakage
Several modules depend on one internal decision (representation, policy, protocol detail): change needs coordinated edits. Re-exported wire or transport types leak. Parse external data into domain types; keep storage schemas and framework objects private.

## Temporal decomposition
Modules split by execution order (load, validate, transform, save) not owned knowledge: one representation and its invariants repeat at each boundary. Group by knowledge; code running at different times may share a module when it protects the same decisions.

## Pass-through method
Middle Man smell: `references/code-smell-baseline.md`. Keep forwarding boundary only if it adds policy, adaptation or distinct abstraction.

## Split ownership
Several modules write or copy same state: agent editing one writer cannot see others. One owner per state; others read it or ask owner to change it.

## Two ways to do one task
Agent copies first way found; both gain callers. Keep one, move callers, delete other in same change.

## Importable internals
Agent takes shortest path that compiles: importable internals become interface. Make unreachable; outside import fails build.

## Hand-synced list
Several places list same items; agent updates only the list it sees. Keep one list, derive others; underivable → fail build on disagreement.

---
*Adapted from cursor/plugins pstack `architect` (MIT, Copyright (c) 2026 Lauren Tan); condensed for StratosphereOS.*
