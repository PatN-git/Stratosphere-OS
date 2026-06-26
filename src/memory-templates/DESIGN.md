---
type: design
version: "1.0.2"
name: <Project Name>
description: <One-line product description>
colors:
  primary: "oklch(0.205 0 0)"
  secondary: "oklch(0.554 0.046 257)"
  tertiary: "oklch(0.55 0.15 35)"
  neutral: "oklch(0.985 0.005 80)"
  surface: "oklch(0.985 0 0)"
  on-surface: "oklch(0.205 0 0)"
  error: "oklch(0.577 0.228 27.3)"
typography:
  h1:
    fontFamily: "<Google Fonts family>"  # DR-016: must be a Google Fonts family
    fontSize: 48px
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: -0.02em
  body-md:
    fontFamily: "<Google Fonts family>"  # DR-016: must be a Google Fonts family
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  label-caps:
    fontFamily: "<Google Fonts family>"  # DR-016: must be a Google Fonts family
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

<!-- shadcn variable names are generated from these tokens by design-theme (see .agents/scripts/design) -->
<!-- optional dark overrides: add a top-level colorsDark block; omitted tokens are derived. Example:
colorsDark:
  primary: "oklch(0.4 0.1 120)"
-->

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
- Don't ship the default Inter or any unchosen system default — pick a deliberate, brand-justified font ([[DR-001]]).
