# Template Index

Load ONLY the single template file matching the scenario. Never load all files.

| Template | File | Use when |
|---|---|---|
| `implementation-plan` | `implementation-plan.html` | Multi-phase roadmap, progress tracking, collapsible milestones |
| `trade-off-matrix` | `trade-off-matrix.html` | ≥3 options × ≥3 criteria, color-coded comparison |
| `annotated-flowchart` | `annotated-flowchart.html` | Process/state machine with clickable step annotations |
| `status-report` | `status-report.html` | KPI dashboard, health indicators, metric cards |
| `incident-timeline` | `incident-timeline.html` | Chronological events with severity/impact coloring |
| `decision-record` | `decision-record.html` | ADR-style: context, options considered, final decision, consequences |

## No match?
If content doesn't fit any template, use `custom-composition` mode:
- Select ≥1 components from `references/html-patterns.md` (accordion, tabs, progress bar)
- Compose inline; do NOT force-fit a wrong template
- Still requires all Four-Scenario Gate conditions to pass
