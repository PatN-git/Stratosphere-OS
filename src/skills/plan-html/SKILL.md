---
name: plan-html
description: Use when presenting a complex or spatial plan to a human — roadmap, trade-off matrix, status dashboard, multi-section plan document, decision record, side-by-side comparison. Generates one self-contained interactive HTML file; fires on ≥~100-line or spatial human-facing output. Defaults to markdown for agent-loop content, repo docs, model input, and short/simple output.
type: skill
version: "1.1.1"
timestamp: 2026-06-24
---

# Decision Gate (Four-Scenario)
Generate HTML ONLY if ALL conditions pass:
1. Consumer is Human (not agent loop, not repo doc, not model input).
2. Layout requires spatiality or scale:
   - Side-by-side comparison, diagram component, interactive widget, or multi-section navigation.
   - Total content length is ≥ ~100 lines (markdown equivalent).
3. Output is self-contained: zero CDN, zero external fonts/scripts, single-file.
4. Estimated HTML size < 5× markdown equivalent.

| Consumer | Content | → Format |
|:--|:--|:--|
| Agent loop / repo doc / human→model input | any | **Markdown** |
| Human | < ~100 lines **and** not spatial | **Markdown** |
| Human | ≥ ~100 lines **or** spatial (comparison/dashboard/multi-section) | **HTML** |
| Human | needs to *edit* structured content | **HTML micro-app** |

A diagram on its own does NOT trigger HTML — it is only a component inside a complex-plan document. `<5×` size is a sanity ceiling, not the trigger.

If any check fails → generate Markdown, prepend: `<!-- plan-html: bypassed (reason: <reason>) -->`

# Template Selection
1. Read `assets/templates/index.md` (lean — ~20 lines).
2. Load ONLY the single matching `.html` template file from `assets/templates/`.
3. Adapt slots: fill `{{placeholders}}` with actual content; never load unused templates.

If no template fits → **custom-composition mode**: compose using primitives from `references/html-patterns.md` (accordion, tabs, progress bar). Gate still applies.

# Output Rules
- Write to a standalone `.html` file at the path the caller specifies.
- Convention by lifespan:
  - **ephemeral** artifacts (decision aids, editors, throwaway comparisons) → `.tmp/` (gitignored) or OS temp;
  - **durable** artifacts (tied to a feature/decision) → beside the artifact they document (e.g. `docs/design/…`).
  - Invoking workflows set the concrete path (e.g. `2b` → `docs/design/BT-<n>-directions.html`). The skill stays path-agnostic.
- First line must be the token header:
  `<!-- plan-html | md-equivalent: ~<N> lines | html: ~<N> lines | ratio: <N>x | justified: <reason> -->`
- Minify CSS/JS inline (remove blank lines/excess whitespace) to stay within token budget.

# State Persistence
- Embed current state in `<script id="plan-data" type="application/json">` as the single source of truth.
- On load: `renderBody(planData())` constructs the DOM dynamically. Do not duplicate state in DOM and script.
- On update:
  1. Read existing `<script id="plan-data">` to restore context.
  2. Merge changes, rewrite file.

# Styling Rules
- System-font stack only (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`).
- CSS custom properties; `prefers-color-scheme` dark/light support required.
- Always include "Copy JSON State" and "Export Markdown" buttons calling `copyState()` and `exportMd()`.
