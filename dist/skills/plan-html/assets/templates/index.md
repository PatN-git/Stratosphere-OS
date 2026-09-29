---
name: index
description: index of plan-html templates
version: "1.3.3"
timestamp: 2026-06-25
---

# Template Index

Load ONLY the single template file matching the scenario. Never load all files.

| Template | File | Use when |
|---|---|---|
| `trade-off-matrix` | `trade-off-matrix.html` | ≥3 options × ≥3 criteria, color-coded comparison |
| `status-report` | `status-report.html` | KPI dashboard, health indicators, metric cards |
| `incident-timeline` | `incident-timeline.html` | Chronological events with severity/impact coloring |
| `decision-record` | `decision-record.html` | ADR-style: context, options considered, final decision, consequences |
| `wireframe-compare` | `wireframe-compare.html` | 3 lo-fi UI direction sketches side-by-side for a pick |
| `plan-document` | `plan-document.html` | Complex plan with sticky TOC, scroll-spy, search filter, and diagrams |
| `board` | `board.html` | Generic draggable board editor (backlog, sprint, or triage) with change payload emitter |

## Composition Rules & No Match
- **Keep nesting flat**: Use one primary component per section. Never nest a widget inside another widget (e.g., no diagram/widget inside a collapsible details/accordion).
- **Inline Read-Only vs Spoke Interactive**: Read-only components (trade-offs, timeline, status, decision, steps, diagrams) MUST render inline as sections. Genuinely interactive components (e.g., a draggable board, config sliders/forms) MUST render a read-only summary inline and link out to a separate interactive spoke file.

If content doesn't fit any template, use `custom-composition` mode:
- Select ≥1 components from `references/html-patterns.md` (accordion, tabs, progress bar)
- Compose inline; do NOT force-fit a wrong template
- Still requires all Four-Scenario Gate conditions to pass
