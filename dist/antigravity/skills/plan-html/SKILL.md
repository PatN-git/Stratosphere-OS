---
name: plan-html
description: Generates interactive single-file HTML plans/matrices/micro-apps ONLY when human-facing and spatial layout/interaction structurally outperforms markdown. Defaults to markdown.
type: skill
trigger: AFK
version: "1.0.0"
---

# Decision Gate (Four-Scenario)
Generate HTML ONLY if ALL conditions pass:
1. Consumer is Human (not agent loop, not repo doc).
2. Layout requires spatiality: side-by-side comparison, diagram, interactive widget, or multi-section navigation markdown cannot express.
3. Output is self-contained: no CDN, no external fonts/scripts.
4. Estimated HTML size < 5× markdown equivalent.

If any check fails → generate Markdown, prepend: `<!-- plan-html: bypassed (reason: <reason>) -->`

# Template Selection
1. Read `assets/templates/index.md` (lean — ~20 lines).
2. Load ONLY the single matching `.html` template file from `assets/templates/`.
3. Adapt slots: fill `{{placeholders}}` with actual content; never load unused templates.

If no template fits → **custom-composition mode**: compose using primitives from `references/html-patterns.md` (accordion, tabs, progress bar). Gate still applies.

# Output Rules
- Write to a standalone `.html` file.
- First line must be the token header:
  `<!-- plan-html | md-equivalent: ~<N> lines | html: ~<N> lines | ratio: <N>x | justified: <reason> -->`
- Minify CSS/JS inline (remove blank lines/excess whitespace) to stay within token budget.

# State Persistence
Embed current state in `<script id="plan-data" type="application/json">`.
On update runs:
1. Read existing `<script id="plan-data">` to restore context.
2. Merge changes, rewrite file.

# Styling Rules
- System-font stack only (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`).
- CSS custom properties; `prefers-color-scheme` dark/light support required.
- Always include "Copy State" and "Export MD" buttons (see base-template.html).
