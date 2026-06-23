<!-- stratosphere: version=1.0.0 updated=2026-06-17 -->
---
version: alpha
name: SkyCast Weather App
description: A clean, modern weather forecasting web application.
colors:
  primary: "oklch(0.68 0.15 240)"
  secondary: "oklch(0.85 0.08 240)"
  tertiary: "oklch(0.75 0.18 65)"
  neutral: "oklch(0.98 0.01 240)"
typography:
  h1:
    fontFamily: "'SF Pro Display', sans-serif"
    fontSize: 48px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: -0.02em
  body-md:
    fontFamily: "'Inter', sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  label-caps:
    fontFamily: "'Inter', sans-serif"
    fontSize: 12px
    fontWeight: 600
    lineHeight: 1
    letterSpacing: 0.1em
rounded:
  sm: 4px
  md: 8px
  lg: 16px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral}"
    rounded: "{rounded.full}"
    padding: 16px
---

## Overview
SkyCast provides users with hyper-local, accurate weather forecasting in a clean, distraction-free interface. The design language evokes the sky and elements, promoting clarity and high visibility.

## Colors
The palette relies on clear, airy blues to represent the core domain of weather. The tertiary color (a warm amber/gold) is used strictly for sunny indicators and critical alerts, while neutral colors keep the interface uncluttered.

## Typography
The type system uses SF Pro Display for bold, highly readable temperature and weather condition headings. Inter is used for supporting body text due to its excellent legibility in complex data tables (like 10-day forecasts).

## Layout
The layout employs a modular, card-based grid model. Weather widgets are presented as distinct, elevated cards with ample padding to prevent data density from feeling overwhelming.

## Elevation & Depth
Elevation is used sparingly to lift primary interactive elements (like the search bar) and the current-day weather card above the background. Shadows are soft and diffused, matching the airy aesthetic.

## Shapes
Corner radii are generously rounded (`lg: 16px`) to create a friendly, approachable, and modern feel, contrasting with harsh edges.

## Components
All buttons and interactive pills use fully rounded edges (`full: 9999px`). Weather condition icons must maintain a consistent 2px stroke width.

## Do's and Don'ts
- Do use high-contrast text against the primary blue backgrounds.
- Do ensure weather data is the focal point, not the chrome of the app.
- Don't ship the default Inter or any unchosen system default — pick a deliberate, brand-justified font ([[DR-001]]).
- Don't use heavy, dark shadows; keep depth light and ambient.
