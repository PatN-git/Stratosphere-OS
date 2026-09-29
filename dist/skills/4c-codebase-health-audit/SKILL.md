---
name: 4c-codebase-health-audit
description: "Periodic broad health screening of the full codebase across security, reliability, maintainability, correctness, performance, and dependency health. Produces a durable audit report in docs/audits/ and a slice proposal for /3b-create-issue. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.1.0"
timestamp: 2026-09-24
---

# Codebase Health Audit

Broad periodic health screen — covers full codebase, produces impact-categorized report + slice proposal, halts for user review.

> [!IMPORTANT]
> **Read-only outside `docs/audits/`.** Never modify production code, create issues, commit, or push. It owns exactly one directory: it writes `docs/audits/health-<YYYY-MM-DD>.md` and prunes unpinned reports there past the retention window (Phase 4.3). It also writes one `.tmp/refactor-proposal-<report-stem>.md` (Phase 5). Do not describe this skill as purely read-only — it deletes files.

---

## Phase 0: Load Memory
Run the `load-memory` skill to restore session context (read-only).

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
- Confidence threshold: **≥60** (overrides default ≥80 in `.agents/skills/4c-codebase-health-audit/references/confidence-scale.md`)

**Guardrail (inject into every subagent):**
> "Scan and report findings only. Do not modify any file. Do not create, commit, or push. Return findings to parent."

**Scan matrix:** `.agents/skills/4c-codebase-health-audit/references/health-audit-scan-matrix.md`

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
Apply impact tiers from `references/audit-to-slices.md` §2 (Critical → High → Medium → Low).

### 3.3 Apply Recent-Change Lens
Tag findings on `priority_files` with `[RECENT]`.

### 3.4 Confidence Filter
Drop findings below 60.

### 3.5 Assign IDs
Assign `F-01…F-NN` per `references/audit-to-slices.md` §1.

---

## Phase 4: Report Generation

Follow `references/health-audit-report-template.md` for report structure and `.last-run.json` schema; findings rows per `references/audit-to-slices.md` §3.

### 4.1 Write Report
Path: `docs/audits/health-<YYYY-MM-DD>.md`

### 4.2 Update Last-Run
Write `docs/audits/.last-run.json` per template schema.

### 4.3 Retention
Resolve the pinned set (`references/audit-to-slices.md` §9):
```bash
gh issue list --state open --limit 500 --json body --jq '.[].body' | grep -oE 'docs/audits/[A-Za-z0-9._-]+\.md' | sort -u
```
Delete `docs/audits/health-*.md` where the filename date `<YYYY-MM-DD>` is older than 90 days **and** the path is not in the pinned set. `gh` absent or unauthenticated → delete nothing and output `[SKIP] Retention — gh unavailable; no reports deleted.` Keep `.last-run.json` always.

---

## Phase 5: Refactor Proposal

1. **Scope:** 🔴 + 🟠 + 🟡 findings; ⚪ → `[OPPORTUNISTIC]`. The trigger prompt may widen or narrow tiers.
2. **Write proposal:** cluster findings into slices and write `.tmp/refactor-proposal-<report-stem>.md` per `references/audit-to-slices.md` §4–§8.
3. **Completion criterion:** every F-xx in the report appears in `## Coverage`; zero `[UNCOVERED]`.

---

## Phase 6: Handoff

**HALT.** Output:

```
[AUDIT COMPLETE] docs/audits/health-<date>.md
  🔴 Critical: N  🟠 High: N  🟡 Medium: N  ⚪ Low: N  (Total: N)
  Delta window: <start> → <end> | <N> priority files.

  Proposal: .tmp/refactor-proposal-<report-stem>.md  (<S> slices, epic: yes|no)
  Review it, then run /3b-create-issue .tmp/refactor-proposal-<report-stem>.md
```

Await user direction. No further action.

---

## Clean Exit (Zero Findings)

If no finding ≥60 confidence across any pass:
1. Do NOT write report or proposal (avoid empty artifacts).
2. Update `.last-run.json` with `total_findings: 0`.
3. Output:
```
[HEALTHY] No findings ≥60 confidence across 6 passes.
  Scanned: <dirs>. Delta: <start> → <end>. .last-run.json updated.
```
