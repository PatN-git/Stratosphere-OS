---
description: Distilled reference for creating effective Stitch briefs and bootstrapping design tokens.
version: "1.0.1"
timestamp: 2026-06-17
---

# Stitch Brief Guide
> Distilled reference. §A consumed by `2b` Phase 3 (brief assembly); §B by brownfield bootstrap.

## A. Effective Stitch Brief
- Lead with the concrete artifact: the one page/feature, its purpose, the primary user action.
- State scope explicitly (whole-page A1 vs feature-region A2) and name what NOT to touch (shielded chrome / governing Immortal Components as hard constraints).
- Enumerate the states to design: default, loading, empty, error, success — plus breakpoints.
- Give a concrete style descriptor (mood, density, motion), not adjectives alone.
- Do NOT inline `DESIGN.md` token values — `DESIGN.md` is supplied to Stitch as the Design System.

## B. Derive DESIGN.md from existing code (brownfield bootstrap)
- Scan the codebase for existing color/type/spacing values and recurring component patterns.
- Consolidate into semantic tokens (primary/surface/accent; type scale; spacing scale; radius; shadows) in the `DESIGN.md` shape.
- Propose the resulting `DESIGN.md` to the user (propose-only); it becomes the SSOT.

---
*Brief and extraction heuristics adapted from google-labs-code/stitch-skills (Apache-2.0); modified for StratosphereOS.*
