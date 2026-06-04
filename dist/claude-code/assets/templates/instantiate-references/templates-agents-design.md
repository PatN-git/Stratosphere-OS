---
description: Verbatim templates for .memory/DESIGN.md (Google Labs spec) and .memory/DESIGN_RULES.md (project structural rules).
---

# Memory Layer Templates — Design

Verbatim templates for the two design files in `.memory/`.

> [!IMPORTANT]
> `DESIGN.md` follows the **Google Labs DESIGN.md spec** (`github.com/google-labs-code/design.md`). Trust tags and `[DR-xxx]` IDs do NOT apply to it. Validate with `npx @google/design.md lint DESIGN.md`.
> `DESIGN_RULES.md` is trust-tagged with `[DR-xxx]` IDs and follows the standard memory protocol.

## Table of contents

1. `.memory/DESIGN.md`
2. `.memory/DESIGN_RULES.md`

---

## 1. `.memory/DESIGN.md`

```markdown
---
version: alpha
name: <Project Name>
description: <One-line product description>
colors:
  primary: "oklch(0.205 0 0)"
  secondary: "oklch(0.554 0.046 257)"
  tertiary: "oklch(0.55 0.15 35)"
  neutral: "oklch(0.985 0.005 80)"
typography:
  h1:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: -0.02em
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1
    letterSpacing: 0.1em
rounded:
  sm: 4px
  md: 8px
  lg: 12px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 32px
  xl: 64px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral}"
    rounded: "{rounded.md}"
    padding: 12px
---

## Overview
<Brand personality, target audience, emotional response. 2-4 sentences.>

## Colors
<Rationale for the palette. Name each color semantically.>

## Typography
<Rationale for type system. Describe role of each level.>

## Layout
<Spacing strategy, grid model, responsive approach.>

## Elevation & Depth
<How visual hierarchy is conveyed. Shadows, borders, tonal layers.>

## Shapes
<Corner radius philosophy and rationale.>

## Components
<Style guidance for component atoms beyond the YAML tokens.>

## Do's and Don'ts
- Do <prescriptive rule>
- Don't <prohibition>
```

> [!NOTE]
> Sections must appear in the order above per spec. Sections may be omitted if not relevant.

---

## 2. `.memory/DESIGN_RULES.md`

```markdown
# DESIGN RULES

## Purpose
Project structural rules and operational design governance. Read alongside `DESIGN.md` whenever a task touches `.tsx`, layout, styling, or UI components.

> Trust tags, supersession, and cross-reference rules → `.agents/rules/memory-protocol.md`.

Three sections:
1. **Design Principles** — operational standards. Rarely change.
2. **Stitch Harmonization Rules** — how to consume Google Stitch without inheriting drift.
3. **Immortal Components** — project-specific structural source of truth.

All entries are `[LAW]`-tier with `[DR-xxx]` IDs.

---

## 1. Design Principles

- **[[DR-001]] [LAW]** Kill AI Slop: no generic purple gradients, no default Inter font, no nested-card div soup. If a component looks like an AI built it, rewrite until it looks like a Senior Design Engineer built it.
- **[[DR-002]] [LAW]** Use OKLCH for all color tokens — in `DESIGN.md`, `tailwind.config`, and CSS variables. Hex only when interfacing with tools that don't yet support OKLCH.
- **[[DR-003]] [LAW]** Use fluid typography and fluid spacing scales — no fixed pixel values for cross-viewport layout.
- **[[DR-004]] [LAW]** shadcn/ui components are the default. Raw HTML elements only when shadcn does not cover the use case.
- **[[DR-005]] [LAW]** Tailwind tokens preferred over arbitrary values (`bg-[#3b82f6]`, `space-y-[17px]`).
- **[[DR-006]] [LAW]** Semantic HTML over `<div>` soup. Use `<nav>`, `<main>`, `<aside>`, `<article>`, etc.

## 2. Stitch Harmonization Rules

Treat Stitch as the **mood board**, not the **source of truth**.

- **[[DR-007]] [LAW]** Extract data, not structure. Pull content and visual styles from Stitch. Discard global structural decisions.
- **[[DR-008]] [LAW]** Structural Shield: if a Stitch export differs structurally from §3 Immortal Components, DISCARD the Stitch version.
- **[[DR-009]] [LAW]** Token Snap: map Stitch hex codes to Tailwind tokens. Map Stitch px to Tailwind scale.
- **[[DR-010]] [LAW]** When Stitch suggests a structural change to a global component (Navbar, Sidebar, Footer), this is drift, not intent. Do not propagate.
- **[[DR-011]] [LAW]** Feed Stitch a current `DESIGN.md` as input context whenever possible.

## 3. Immortal Components

Structural source of truth. Stitch and other generators MUST conform to these.

### Active Entries

- **[[DR-012]] [LAW]** Example placeholder — replace during brownfield audit or as components are built.
  - **Component:** `components/layout/Navbar.tsx`
  - **Desktop pattern:** Top-fixed, horizontal links
  - **Mobile pattern:** Hamburger trigger, right-side drawer
  - **Drift protection:** If Stitch suggests a sidebar or alternative mobile pattern, ignore it.

- **[[DR-013]] [LAW]** Example: `components/layout/Sidebar.tsx`
  - **Use scope:** Admin dashboard only
  - **Pattern:** Collapsible (64px collapsed, 240px expanded)
  - **Drift protection:** Never appears in user-facing views.

### Superseded
> Read only when explicitly asked.

- **[[DR-XXX]] [SUPERSEDED BY [[DR-YYY]]] [YYYY-MM-DD]** Original entry preserved. Reason: one line. Version: v0.X → v0.Y.
```