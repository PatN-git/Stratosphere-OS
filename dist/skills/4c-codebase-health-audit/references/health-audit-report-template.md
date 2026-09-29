---
description: Report template for 4c-codebase-health-audit.
version: "2.0.0"
timestamp: 2026-09-24
---

# Health Audit — Report Template

Reference for `4c-codebase-health-audit` Phase 4. Impact categories, finding IDs, and the findings row contract: `references/audit-to-slices.md` §1–§3.

---

## Report Structure

Write to `docs/audits/health-<YYYY-MM-DD>.md`:

```markdown
---
type: audit-report
title: "Health Audit — <YYYY-MM-DD>"
status: stable
version: <plugin version>   # stamped at generation (okf-protocol §5)
generated:
  by: 4c-codebase-health-audit
  at: <ISO 8601>
---

# Health Audit — <YYYY-MM-DD>

## Executive Summary

| | |
|:---|:---|
| Passes run | 6/6 |
| Delta window | <start_date> → <end_date> (<N> recently-changed files prioritized) |
| Scanned | src/, api/, scripts/ (list actuals) |
| Skipped (in-progress) | <list or "none"> |

| Impact | Count |
|:---|---:|
| 🔴 Critical | N |
| 🟠 High | N |
| 🟡 Medium | N |
| ⚪ Low | N |
| **Total** | **N** |

---

## 🔴 Critical

| ID | Pass | File | Line(s) | Finding | Evidence | Confidence | Law | Recent? | Suggested Direction |
|:---|:---|:---|:---|:---|:---|---:|:---|:---:|:---|
| F-01 | Security | src/api/auth.ts | 42 | Hardcoded JWT secret | `const JWT_SECRET = "<REDACTED>"` | 95 | — | ✓ | Move to `.env`; rotate key |

## 🟠 High
(same table)

## 🟡 Medium
(same table)

## ⚪ Low
(same table)

---

## Pass Summaries

### Security & Secrets
- Files scanned: N
- Findings: N (🔴 N, 🟠 N, 🟡 N, ⚪ N)

### Dependency Health
- Audit command: `<command run>`
- Findings: N

### Reliability (Error Handling)
- Files scanned: N
- Findings: N

### Correctness (Test Coverage)
- Zero-test modules: N
- Skipped/disabled tests: N
- Findings: N

### Maintainability (Duplication + Dead Code)
- Duplicated blocks: N (across N file pairs)
- Dead exports: N | Orphaned files: N
- Findings: N

### Performance Anti-Patterns
- Files scanned: N
- Findings: N

---

## Recommended Next Steps

Proposal: `.tmp/refactor-proposal-<report-stem>.md` → review, then `/3b-create-issue .tmp/refactor-proposal-<report-stem>.md`.

For architectural analysis of flagged modules → `/4b-audit-architecture-drift`.
Findings tagged ✓ Recent may be regressions from delta window — prioritize.
```

---

## `.last-run.json` Schema

Write to `docs/audits/.last-run.json`:

```json
{
  "last_run": "<ISO-8601>",
  "passes_run": ["security", "dependency", "reliability", "correctness", "maintainability", "performance"],
  "scan_targets": ["src/", "api/", "scripts/"],
  "skipped_targets": [],
  "total_findings": 0,
  "by_impact": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
  "report_path": "docs/audits/health-<YYYY-MM-DD>.md",
  "delta_window_start": "<ISO-8601>",
  "priority_files_count": 0
}
```
