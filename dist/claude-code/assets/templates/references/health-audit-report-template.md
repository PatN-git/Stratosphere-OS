---
description: Report template and impact categorization for 4c_codebase-health-audit.
version: "1.0.0"
timestamp: 2026-07-27
---

# Health Audit — Report Template

Reference for `4c_codebase-health-audit` Phase 4.

---

## Impact Categories

| Impact | Criteria |
|:---|:---|
| **🔴 Critical** | Active security vulnerability, auth bypass, data loss risk, hardcoded production secret, critical CVE in direct dependency. |
| **🟠 High** | Reliability failure on critical user path, high-severity CVE, missing error handling on payment/auth/data-mutation flow, zero tests on security-critical module. |
| **🟡 Medium** | Test gap on important module, significant duplication (≥3 locations or ≥30 lines), performance anti-pattern with measurable latency impact, moderate CVE. |
| **⚪ Low** | Dead code, orphaned files, thin test files, deprecated non-vulnerable dependency, unused imports, commented-out code. |

Impact is independent of confidence — a Critical finding at 65 confidence is still Critical; note uncertainty in suggested fix.

---

## Report Structure

Write to `docs/audits/health-<YYYY-MM-DD>.md`:

```markdown
---
type: audit-report
title: "Health Audit — <YYYY-MM-DD>"
timestamp: <YYYY-MM-DD>
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

| # | Pass | File | Line(s) | Finding | Confidence | Recent? | Suggested Fix |
|---:|:---|:---|:---|:---|---:|:---:|:---|
| 1 | Security | src/api/auth.ts | 42 | Hardcoded JWT secret | 95 | ✓ | Move to `.env`; rotate key |

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

- **🔴 Critical** → Fix now via `/3d` or micro-tdd.
- **🟠 High** → `/3b` → next sprint.
- **🟡 Medium** → Batch into maintenance slice via `/3b`.
- **⚪ Low** → Address opportunistically.

For architectural analysis of flagged modules → `/4b_audit-architecture-drift`.
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
