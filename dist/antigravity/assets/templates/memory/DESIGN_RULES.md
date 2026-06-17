<!-- stratosphere: version=1.0.0 updated=2026-06-17 -->
# DESIGN RULES

## Purpose
Project structural rules and operational design governance. Read alongside `DESIGN.md` whenever a task touches `.tsx`, layout, styling, or UI components.

> Trust tags, supersession, and cross-reference rules → `.agents/rules/memory-protocol.md`.

Three sections:
1. **Design Principles** — operational standards. Rarely change.
2. **Design Reference Rules** — how to consume design sources (Stitch or references) without inheriting drift.
3. **Immortal Components** — project-specific structural source of truth.

All entries are `[LAW]`-tier with `[DR-xxx]` IDs.

**Default UI stack:** React + Tailwind + shadcn/ui (governs DR-004/DR-005). Non-UI work → Path C. To target another stack, supersede DR-004/DR-005 per `memory-protocol.md` §3 — requires explicit user confirmation; the agent never swaps the stack on its own.

---

## 1. Design Principles

- **[[DR-001]] [LAW]** Kill AI Slop: no generic purple gradients, no default Inter font, no nested-card div soup. If a component looks like an AI built it, rewrite until it looks like a Senior Design Engineer built it.
- **[[DR-002]] [LAW]** Use OKLCH for all color tokens — in `DESIGN.md`, `tailwind.config`, and CSS variables. Hex only when interfacing with tools that don't yet support OKLCH.
- **[[DR-003]] [LAW]** Use fluid typography and fluid spacing scales — no fixed pixel values for cross-viewport layout.
- **[[DR-004]] [LAW]** shadcn/ui components are the default. Raw HTML elements only when shadcn does not cover the use case.
- **[[DR-005]] [LAW]** Tailwind tokens preferred over arbitrary values (`bg-[#3b82f6]`, `space-y-[17px]`).
- **[[DR-006]] [LAW]** Semantic HTML over `<div>` soup. Use `<nav>`, `<main>`, `<aside>`, `<article>`, etc.

## 2. Design Reference Rules

**Stitch Status:** `<yes | no — set during /stratosphere-setup>`
**Design References (no-Stitch projects):** `<reference URLs/templates used to bootstrap the design system — provenance>`

Treat Stitch as the **mood board**, not the **source of truth**. When Stitch Status = `no`, the design system is bootstrapped from human-supplied references + native composition, and the SAME adopt/freeze discipline applies.

**Applicability:** DR-007, DR-008, and DR-014 govern any design source (Stitch OR human-supplied references). DR-009–DR-011 are Stitch-specific; for reference-driven (no-Stitch) projects the analogs are: derive tokens from the references and seed/snap `DESIGN.md` (per the DR-009 greenfield note); treat reference layouts as mood board, not SSOT; and feed the current `DESIGN.md` to the native model as conformance context (the DR-011 analog).

**DESIGN.md round-trip:** `.memory/DESIGN.md` IS a Stitch-spec `DESIGN.md` (open-source format). It is the SSOT. Flow: on bootstrap or when the design system changes, export Stitch's `DESIGN.md` → `.memory/DESIGN.md`; on every generation, provide `.memory/DESIGN.md` to Stitch (UI → Modify → Design System) as hard constraints. The two locations are one artifact — never hand-resync tokens.

- **[[DR-007]] [LAW]** Extract data and feature-level layout. Pull content, visual styles, and the feature/page-body layout from Stitch. For GLOBAL structure (chrome: nav/sidebar/footer/page shell), defer to §3 Immortal Components when one exists.
- **[[DR-008]] [LAW]** Structural Shield applies ONLY where an Immortal Component governs the structure — then discard a conflicting Stitch export. On a net-new page or an explicit full redesign (no governing Immortal Component, or intentional replacement), ADOPT Stitch's layout instead of discarding it.
- **[[DR-009]] [LAW]** Token Snap: map generator hex/px to the project's tokens/scale. On a greenfield first-run the direction reverses — the generator/references seed the initial tokens (see the DESIGN.md round-trip note above). When `DESIGN.md` is supplied to the generator, output already conforms, so snap is only a fallback for un-tokened values.
- **[[DR-010]] [LAW]** When Stitch suggests a structural change to a global component (Navbar, Sidebar, Footer), this is drift, not intent. Do not propagate.
- **[[DR-011]] [LAW]** Feed Stitch a current `DESIGN.md` as input context whenever possible.
- **[[DR-014]] [LAW]** Adopt-and-Register: A first-time or full-redesign layout accepted from Stitch is registered/updated as a §3 Immortal Component ([LAW]-tier, propose to user at design time in 2b, or via 0b/setup; register on user confirmation). Thereafter it shields future feature work (DR-008/010).
- **[[DR-015]] [LAW]** Freeze-and-Read-from-Repo: Stitch output is ingested once at 2b time (MCP if connected, else export/paste) and frozen into the repo; no lifecycle step reads live Stitch. The MCP is an optional ingest accelerator, never a runtime dependency.

## 3. Immortal Components

Structural source of truth. Stitch and other generators MUST conform to these.

### Active Entries

*Note: The first real Immortal Components registered will trigger the removal/purge of the examples below (DR-012/DR-013).*

- **[[DR-XXX]] [LAW]** Example placeholder — replace during brownfield audit or as components are built. Source: BT-XXX.
  - **Component:** `components/layout/Navbar.tsx`
  - **Desktop pattern:** Top-fixed, horizontal links
  - **Mobile pattern:** Hamburger trigger, right-side drawer
  - **Drift protection:** If Stitch suggests a sidebar or alternative mobile pattern, ignore it.

- **[[DR-YYY]] [LAW]** Example: `components/layout/Sidebar.tsx`
  - **Use scope:** Admin dashboard only
  - **Pattern:** Collapsible (64px collapsed, 240px expanded)
  - **Drift protection:** Never appears in user-facing views.

### Superseded
> Read only when explicitly asked.

- **DR-XXX [SUPERSEDED BY DR-YYY] [YYYY-MM-DD]** Original entry preserved. Reason: one line. Version: v0.X → v0.Y.
