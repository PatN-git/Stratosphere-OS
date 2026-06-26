---
type: design-rules
title: Design Rules
description: Project structural rules and operational design governance.
timestamp: 2026-06-17
version: "1.0.4"
---
# DESIGN RULES

## Purpose
Project structural rules and operational design governance. Read alongside `DESIGN.md` whenever a task touches `.tsx`, layout, styling, or UI components.

> Trust tags, supersession, and cross-reference rules → `.agents/rules/memory-protocol.md`.

Three sections:
1. **Design Principles** — operational standards. Rarely change.
2. **Design Reference Rules** — how to consume design sources (external generators or references) without inheriting drift.
3. **Immortal Components** — project-specific structural source of truth.

All entries are `[LAW]`-tier with `[DR-xxx]` IDs.

**Default UI stack:** React + Tailwind + shadcn/ui (governs DR-004/DR-005). Non-UI work → Path C. To target another stack, supersede DR-004/DR-005 per `memory-protocol.md` §3 — requires explicit user confirmation; the agent never swaps the stack on its own.

---

## 1. Design Principles

- **[[DR-001]] [LAW]** Kill AI Slop: no generic purple gradients, no *unchosen* or *Inter* default font (Inter is seen as AI slop and often an inherited tool default), no nested-card div soup. If a component looks like an AI built it, rewrite until it looks like a Senior Design Engineer built it.
- **[[DR-002]] [LAW]** Use OKLCH for all color tokens — in `DESIGN.md`, `tailwind.config`, and CSS variables. OKLCH is accepted end-to-end by the tooling (external generators ingest it; the `@google/design.md` linter coerces it); **no hex conversion is needed**. Hex appears only if a generator emits it.
- **[[DR-003]] [LAW]** Use fluid typography and fluid spacing scales — no fixed pixel values for cross-viewport layout. px values in `DESIGN.md` are **desktop anchors**; `design-theme` emits `clamp(min, fluid, max)` (min = max·0.66 floored at 12px; viewports 360→1280px).
- **[[DR-004]] [LAW]** shadcn/ui components are the default. Raw HTML elements only when shadcn does not cover the use case.
- **[[DR-005]] [LAW]** Tailwind tokens preferred over arbitrary values (`bg-[#3b82f6]`, `space-y-[17px]`).
- **[[DR-006]] [LAW]** Semantic HTML over `<div>` soup. Use `<nav>`, `<main>`, `<aside>`, `<article>`, etc.

## 2. Design Reference Rules

**Design Source:** `<stitch | claude-design | native — set during /stratosphere-setup>`
**Design References (native projects):** `<reference URLs/templates used to bootstrap the design system — provenance>`

Treat the external design generator as the **mood board**, not the **source of truth**. When Design Source = `native`, the design system is bootstrapped from human-supplied references + native composition, and the SAME adopt/freeze discipline applies.

**Applicability:** DR-007, DR-008, and DR-014 govern any design source (external generators OR human-supplied references). DR-009–DR-011 are generator-specific; for native (no-generator) projects the analogs are: derive tokens from the references and seed/snap `DESIGN.md` (per the DR-009 greenfield note); treat reference layouts as mood board, not SSOT; and feed the current `DESIGN.md` to the native model as conformance context (the DR-011 analog).

**DESIGN.md round-trip:** `.memory/DESIGN.md` conforms to the open `DESIGN.md` format. It is the SSOT. Flow: on bootstrap or when the design system changes, feed `.memory/DESIGN.md` to the chosen generator as hard constraints. The design files are reconciled by the Token-Snap **script/agent**, not hand-synced.

- **[[DR-007]] [LAW]** Extract data and feature-level layout. Pull content, visual styles, and the feature/page-body layout from the external generator. For GLOBAL structure (chrome: nav/sidebar/footer/page shell), defer to §3 Immortal Components when one exists.
- **[[DR-008]] [LAW]** Structural Shield applies ONLY where an Immortal Component governs the structure — then discard a conflicting generator export. On a net-new page or an explicit full redesign (no governing Immortal Component, or intentional replacement), ADOPT the generator's layout instead of discarding it.
- **[[DR-009]] [LAW]** Token Snap: Token Snap = **script does mechanical conversion, human curates** which tokens to keep. Applies to **any external source (Stitch / Claude Design)**. On a greenfield first-run the direction reverses — the generator/references seed the initial tokens (see the DESIGN.md round-trip note above). When `DESIGN.md` is supplied to the generator, output already conforms, so snap is only a fallback for un-tokened values.
- **[[DR-010]] [LAW]** When any external design generator (Stitch / Claude Design) suggests a structural change to a global component (Navbar, Sidebar, Footer), this is drift, not intent. Do not propagate.
- **[[DR-011]] [LAW]** Feed the chosen generator a current `DESIGN.md` as input context whenever possible. Name the exact **Google Fonts** family so it renders as a hard constraint ([[DR-016]]).
- **[[DR-014]] [LAW]** Adopt-and-Register: A first-time or full-redesign layout accepted from the chosen generator is registered/updated as a §3 Immortal Component ([LAW]-tier, propose to user at design time in 2b, or via 0b/setup; register on user confirmation). Thereafter it shields future feature work (DR-008/010).
- **[[DR-015]] [LAW]** Freeze-and-Read-from-Repo: Generator output is ingested once at 2b time (MCP if connected, else export/paste) and frozen into the repo; no lifecycle step reads live generator. The MCP is an optional ingest accelerator, never a runtime dependency. Claude Design's two-way Claude Code sync is **frozen** (ingest → snap → reconcile into the one SSOT; never live).
- **[[DR-016]] [LAW]** Typography source — Google Fonts. Author every `DESIGN.md` `fontFamily` from the Google Fonts catalog (renderable by generators as a hard constraint; self-hostable via `next/font/google` / `@fontsource`). Non-GF brand fonts: keep the real family in the SSOT and declare a Google Fonts **stand-in for mockups only**, applying the real font at implementation. Pair wide choice with restraint: one display/serif + one neutral/sans.

## 3. Immortal Components

Structural source of truth. External generators MUST conform to these.

### Active Entries

*Note: The first real Immortal Components registered will trigger the removal/purge of the examples below (DR-012/DR-013).*

- **[[DR-XXX]] [LAW]** Example placeholder — replace during brownfield audit or as components are built. Source: BT-XXX.
  - **Component:** `components/layout/Navbar.tsx`
  - **Desktop pattern:** Top-fixed, horizontal links
  - **Mobile pattern:** Hamburger trigger, right-side drawer
  - **Drift protection:** If the generator suggests a sidebar or alternative mobile pattern, ignore it.

- **[[DR-YYY]] [LAW]** Example: `components/layout/Sidebar.tsx`
  - **Use scope:** Admin dashboard only
  - **Pattern:** Collapsible (64px collapsed, 240px expanded)
  - **Drift protection:** Never appears in user-facing views.

### Superseded
> Read only when explicitly asked.

- **DR-XXX [SUPERSEDED BY DR-YYY] [YYYY-MM-DD]** Original entry preserved. Reason: one line. Version: v0.X → v0.Y.
