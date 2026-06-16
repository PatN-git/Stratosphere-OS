---
version: "1.0.0"
---

# Shadcn Build Guide
> Distilled reference for implementing a frozen design blueprint in shadcn/ui. Consumed by `3c`.

- The blueprint's layout hierarchy (and any Stitch HTML/CSS) is a **layout reference, not copy-source**. Re-express it; never paste generator markup.
- Map each region to shadcn/ui primitives first (Button, Card, Dialog, Input, Sheet, …) before raw elements ([[DR-004]]); use raw HTML only where shadcn lacks a primitive.
- Use semantic landmarks (`<nav>`/`<main>`/`<aside>`/`<article>`) for structure; never reproduce generator `<div>` soup ([[DR-006]]).
- Bind every color to an OKLCH token from `DESIGN.md` ([[DR-002]]); spacing/type to fluid scales ([[DR-003]]); no arbitrary hex/px ([[DR-005]]).
- Compose with compound components / lifted state; avoid boolean-prop proliferation.
- Validation: every visual value must trace to a `DESIGN.md` token — flag orphan colors/sizes.

---
*shadcn/semantic-mapping heuristics adapted from google-labs-code/stitch-skills (Apache-2.0); modified for StratosphereOS.*
