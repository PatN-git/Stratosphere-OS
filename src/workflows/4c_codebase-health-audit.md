---
name: 4c_codebase-health-audit
description: Periodic broad health screening of the full codebase across security, reliability, maintainability, correctness, performance, and dependency health. Produces a durable audit report categorized by impact; the developer drives fixes via /3b and /3d.
type: workflow HITL
trigger: manual
version: "1.0.0"
timestamp: 2026-07-27
---

# Codebase Health Audit

Broad periodic health screen — covers full codebase, produces impact-categorized report, halts for user review. Developer drives fixes.

> [!IMPORTANT]
> **Read-only.** Never modify production code, create issues, commit, or push. Single artifact: `docs/audits/health-<YYYY-MM-DD>.md`.

---

## Phase 0: Load Memory
Run `.agents/skills/load-memory/SKILL.md` to restore session context (read-only).

---

## Phase 1: Scope Resolution

### 1.1 Discover Scan Targets

| Directory / Pattern | Required? | Passes |
|:---|:---|:---|
| `src/` | **Required** — HALT if absent | All 6 |
| `api/` | If exists | All 6 |
| `scripts/` | If exists | All 6 |
| Config: `.env.example`, `next.config.*`, `supabase/config.toml`, `*.config.js/ts` | If exist | Security, Performance |
| Migrations: `supabase/migrations/`, `prisma/migrations/`, `drizzle/` | If exist | Security, Performance |

Trigger prompt may narrow scope (e.g. `4c src/features/billing`) — honor it, warn:
```
[WARN] Narrowed scope: <path>. Cross-cutting findings outside this directory will be missed.
```

### 1.2 Compute Delta Window (Recent-Change Lens)

Recent-change lens feeds recently-modified files as priority targets into all passes. Findings on these files are tagged `[RECENT]`.

1. Read `docs/audits/.last-run.json` → extract `last_run` timestamp if present.
2. Delta start = **earlier** of: `last_run` or 14 days ago. First run → 14 days.
3. Resolve changed files:
   ```bash
   git log --since="<delta_start>" --name-only --pretty=format:"" | sort -u
   ```
   Filter to resolved scan targets. This is `priority_files`.

### 1.3 Backlog Collision Check
Read `.memory/BACKLOG_MAP.md`. Skip directories where modules are `status:in progress`:
```
[SKIP] <path> — BT-<padded> in progress. Findings omitted.
```

---

## Phase 2: Scan Execution

Invoke 3 subagents in parallel. Parent resolves all inputs and passes explicitly — subagents never sweep the repo.

**Input to each subagent:**
- Explicit file list for assigned scan targets
- `priority_files` from Phase 1.2
- `.memory/LEARNINGS.md`
- Confidence threshold: **≥60** (overrides default ≥80 in `.agents/workflows/.reference/confidence-scale.md`)

**Guardrail (inject into every subagent):**
> "Scan and report findings only. Do not modify any file. Do not create, commit, or push. Return findings to parent."

**Scan matrix:** `.agents/workflows/.reference/health-audit-scan-matrix.md`

| Subagent | Passes |
|:---|:---|
| **Safety Auditor** | Security & Secrets (A1), Dependency Health (A2) |
| **Quality Auditor** | Reliability / Error Handling (B1), Correctness / Test Coverage (B2) |
| **Efficiency Auditor** | Maintainability / Duplication + Dead Code (C1), Performance Anti-Patterns (C2) |

Each subagent reads its assigned sections from the scan matrix and returns findings as: `file, line(s), category, description, confidence (60–100), suggested fix`.

---

## Phase 3: Consolidation

Parent merges findings from all 3 subagents:

### 3.1 Deduplicate
Same file + approximate line range across passes → keep both (different diagnoses), link: `Related: [pass] finding at <file>:<line>`.

### 3.2 Categorize by Impact
Apply impact categories from `.agents/workflows/.reference/health-audit-report-template.md` (Critical → High → Medium → Low).

### 3.3 Apply Recent-Change Lens
Tag findings on `priority_files` with `[RECENT]`.

### 3.4 Confidence Filter
Drop findings below 60.

---

## Phase 4: Report Generation

Follow `.agents/workflows/.reference/health-audit-report-template.md` for report structure, impact table, and `.last-run.json` schema.

### 4.1 Write Report
Path: `docs/audits/health-<YYYY-MM-DD>.md`

### 4.2 Update Last-Run
Write `docs/audits/.last-run.json` per template schema.

### 4.3 Retention
Delete `docs/audits/health-*.md` where the filename date `<YYYY-MM-DD>` is older than 90 days. Keep `.last-run.json` always.

---

## Phase 5: Handoff

**HALT.** Output:

```
[AUDIT COMPLETE] docs/audits/health-<date>.md
  🔴 Critical: N  🟠 High: N  🟡 Medium: N  ⚪ Low: N  (Total: N)
  Delta window: <start> → <end> | <N> priority files.

  Fix Critical now via /3d or micro-tdd.
  Create issues for High/Medium via /3b.
  Low: address opportunistically.
```

Await user direction. No further action.

---

## Clean Exit (Zero Findings)

If no finding ≥60 confidence across any pass:
1. Do NOT write report (avoid empty artifacts).
2. Update `.last-run.json` with `total_findings: 0`.
3. Output:
```
[HEALTHY] No findings ≥60 confidence across 6 passes.
  Scanned: <dirs>. Delta: <start> → <end>. .last-run.json updated.
```
