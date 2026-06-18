---
name: ROADMAP-template
type: roadmap
description: Release roadmap mapping product releases to parent features with MVP cut-line rationale and shipped history.
version: "1.0.0"
updated: 2026-06-18
---
# Product Roadmap

> Maintained by `/3a_version-planning`. Milestone format `vX.Y.Z` (MAJOR.MINOR.sprint). This file owns the release rows (`vX.Y`); sprint numbers (`Z`) are assigned by `/3c_sprint-planning`. Active/planned releases first; shipped releases collapse into `## Shipped` at the bottom.
>
> **Status** per release: `[PLANNED]` (no milestone yet / empty) · `[ACTIVE]` (current build target — its `vX.Y.0` milestone is open with all predecessors shipped) · `[SHIPPED <date>]` (its `vX.Y.*` milestones are all closed). Derive status from GitHub milestone open/closed state on each re-run; if GitHub is absent, set it manually.

**Live product:** `vX.Y` &nbsp;<!-- highest [SHIPPED] release, or [ACTIVE] if none shipped yet -->

## vX.Y — <release name> [ACTIVE] [MAJOR | MINOR]
> **Rationale / MVP cut-line:** <why these features, why now, what is deferred and why>

- BT-<padded> — <feature title> (`scope:baseline` | `scope:differentiator`, `size:large`)
- BT-<padded> — <feature title> (...)

## vX.(Y+1) — <next release> [PLANNED] [MINOR]
> **Rationale:** <...>

- BT-<padded> — <feature title> (...)

---

## Shipped
<!-- Token-efficient history (mirrors the `## Superseded` convention in memory docs): one terse line per shipped release; do not retain full feature detail here. Newest first. Never delete — this is the product changelog. -->
- vX.(Y-1) — <release name> — shipped <YYYY-MM-DD> — <N features>, [MAJOR | MINOR]
