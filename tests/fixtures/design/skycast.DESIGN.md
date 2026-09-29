---
type: design
version: "1.0.1"
name: SkyCast
description: A beautiful weather application.
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
    fontFamily: "Outfit"
    fontSize: 48px
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: -0.02em
  body-md:
    fontFamily: "Outfit"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  label-caps:
    fontFamily: "Outfit"
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
