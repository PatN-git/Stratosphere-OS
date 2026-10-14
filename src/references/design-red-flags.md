---
description: Named structural red flags screened against a non-UI interface design (2b Path C) so design and audit share one vocabulary; flags already defined elsewhere are pointers.
version: "1.0.0"
timestamp: 2026-10-14
---

# Design Red Flags

Screen each candidate interface; name the flags that apply, skip the rest. A hit means revise or reject the shape. Assume the next contributor is an agent that sees only the files it opened, copies the nearest example and takes the shortest path that compiles: prefer the design where a change that looks right from one file is right for the whole repo.

## Shallow module
Depth and the Deletion Test: `.memory/ARCHITECTURE.md` vocabulary. Depth concentrates capability behind one interface; a deep call chain scatters it across layers.

## Information leakage
Several modules depend on one internal decision (representation, policy, protocol detail), so changing it needs coordinated edits. Re-exporting wire or transport types is leakage: parse external data into domain types and keep storage schemas and framework objects private.

## Temporal decomposition
Modules split by execution order (load, validate, transform, save) instead of owned knowledge, repeating one representation and its invariants at each boundary. Group by knowledge; code that runs at different times can share a module when it protects the same decisions.

## Pass-through method
The Middle Man smell in `code-smell-baseline.md`. Keep a forwarding boundary only when it adds policy, adaptation or a distinct abstraction.

## Split ownership
Several modules write the same state or keep their own copy, so an agent editing one writer cannot see the others. Give each piece of state one owner; others read it or ask the owner to change it.

## Two ways to do one task
An agent copies whichever way it finds first, so both keep gaining callers. Keep one, move callers off the other, delete it in the same change.

## Importable internals
An agent takes the shortest path that compiles, so importable internals become interface. Make them unreachable so an outside import fails the build.

## Hand-synced list
Several places list the same items; an agent that sees one list updates only that one. Keep one list and derive the others; if one cannot be derived, fail the build when they disagree.

---
*Adapted from cursor/plugins pstack `architect` (MIT, Copyright (c) 2026 Lauren Tan); condensed for StratosphereOS.*
