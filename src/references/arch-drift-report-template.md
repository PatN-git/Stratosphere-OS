---
description: Report template for 4b-audit-architecture-drift.
version: "1.0.0"
timestamp: 2026-09-24
---

# Architecture Drift — Report Template

Reference for `4b-audit-architecture-drift` Phase 3. Impact tiers, finding IDs, and the findings row contract: `references/audit-to-slices.md` §1–§3.

---

## Report Structure

Write to `docs/audits/arch-<target-slug>-<YYYY-MM-DD>.md` (`<target-slug>` = target path with `/` → `-`, leading and trailing `-` stripped). Omit empty impact sections.

```markdown
---
type: audit-report
title: "Architecture Drift — <target> — <YYYY-MM-DD>"
status: stable
version: <plugin version>   # stamped at generation (okf-protocol §5)
generated:
  by: 4b-audit-architecture-drift
  at: <ISO 8601>
---

# Architecture Drift — <target> — <YYYY-MM-DD>

## Executive Summary

| | |
|:---|:---|
| Target | <target directory> |
| Files scanned | N |
| Dropped (backlog collision) | <BT-ids or "none"> |

| Impact | Count |
|:---|---:|
| 🔴 Critical | N |
| 🟠 High | N |
| 🟡 Medium | N |
| ⚪ Low | N |
| **Total** | **N** |

---

## 🔴 Critical

| ID | File | Line(s) | Finding | Evidence | Confidence | Law | Recent? | Suggested Direction |
|:---|:---|:---|:---|:---|---:|:---|:---:|:---|
| F-01 | src/billing/charge.ts | 12–40 | Payment mutation bypasses service layer | `db.insert(charges)` in route handler | 90 | [[A-004]] | — | Route through `BillingService.charge()` |

## 🟠 High
(same table)

## 🟡 Medium
(same table)

## ⚪ Low
(same table)

---

## Next Step

Proposal: `.tmp/refactor-proposal-<report-stem>.md` → review, then `/3b-create-issue .tmp/refactor-proposal-<report-stem>.md`.
```
