---
type: discovery-brief
title: "Discovery: Codebase health silently degrades without periodic broad screening"
description: "Implementation-ready concept brief for workflow 4c — a periodic, read-only health audit across security, reliability, maintainability, correctness, performance, and dependency health."
timestamp: 2026-07-27
status: ready-for-prd
slug: codebase-health-audit
linked-prd: —
version: "1.0.0"
---

# Discovery: Codebase health silently degrades without periodic broad screening

## Ask (verbatim)
> I want to build a new workflow 4c that covers the 5 topics below
> 1) Find duplicated code patterns in src and prepare a plan how to refactor them into shared utilities
> 2) Look at my 5 most recent pull requests that I authored in and do a thorough code review of each — take over each PR so you have the full context, then check for bugs, edge cases, and improvements. Only review PRs that I authored, not PRs from other contributors. If I have no pull requests, review my 5 most recent commits instead.
> 3) Scan the codebase for common security issues — hardcoded API keys and secrets, SQL injection, unvalidated user input, insecure dependencies, overly permissive CORS, exposed debug endpoints, and missing authentication checks. Report what you find and fix the critical ones.
> 4) Analyze the test coverage and add unit tests for the modules with the least coverage.
> 5) Review the error handling and improve areas where errors are silently swallowed or not properly propagated.

## Vocabulary

- **Health audit:** A periodic, broad, read-only scan of the full project codebase across multiple quality dimensions (security, reliability, maintainability, correctness, performance, dependency health). Distinct from 4b's targeted structural audit. Avoid: "code review," "linting," "static analysis."
- **Pass:** One of the 6 scan categories within a health audit, each targeting a distinct quality dimension. Avoid: "check," "rule," "test."
- **Recent-change lens:** Cross-cutting prioritization heuristic that feeds recently-changed files (14-day window or delta since last audit) as high-priority targets into all passes. Not a standalone pass. Avoid: "PR review," "change review."
- **Finding:** A single detected issue scored ≥60 confidence, with location, category, and suggested fix. Avoid: "violation," "error," "bug" (implies certainty).
- **Delta window:** The time range used by the recent-change lens — 14 days or since `.last-run.json`, whichever is shorter. Avoid: "lookback period."
- **Audit report:** The durable output artifact (`docs/audits/health-<YYYY-MM-DD>.md`) with ~90-day retention. Contains all findings grouped by impact category, then by pass. Avoid: "proposal" (that's 4b's term).

## Actor
An AI agent running StratosphereOS workflows on behalf of a developer, scanning the developer's consumer project codebase. The developer is the decision-maker who reviews the audit report and initiates fixes.

## Problem
Code health silently degrades between feature cycles. Slice-level verification (4a) catches acute issues in the current diff, and targeted structural audits (4b) catch architectural drift in a single directory, but neither systematically screens the full codebase for chronic, cross-cutting decay: creeping duplication, accumulating security debt, expanding test coverage gaps, silently swallowed errors, performance anti-patterns, and vulnerable dependencies. Without periodic broad screening, latent defects compound until they surface as production incidents — at which point the fix cost is far higher than early detection.

## Chosen Framing
**Preventive health screening** — positions the workflow as periodic diagnostic medicine for the codebase. All 6 passes are dimensions of "health," the recent-change lens is triage (recently-touched code gets priority), and the audit report is the diagnosis. The developer then prescribes treatment via `/3b` → `/3d`.

**Rejected framings:**
- Latent defect mining: Accurate but frames the workflow as reactive extraction rather than proactive prevention. Doesn't explain why the passes belong together.
- Quality drift detection: Too close to 4b's framing (architecture drift). Would blur the boundary between the two workflows.

## Prior Art
- **4a_verify-and-ship:** Micro-audit of a single slice's diff against PRD acceptance criteria. Per-slice, not codebase-wide.
- **4b_audit-architecture-drift:** Macro-audit of a single targeted directory for structural drift (god modules, leaked seams, dependency inversion). Requires explicit directory scope. Does not cover security, test coverage, duplication, error handling, performance, or dependency health.
- **Overlap with 4b is narrow:** Both may flag the same large file — 4b diagnoses a boundary violation, 4c diagnoses duplicated code or swallowed errors in that file. Different diseases, same symptom. 4c can cross-reference: "For deeper architectural analysis, run `/4b` on this directory."
- **0d_nightly-consolidation:** Provides the artifact retention pattern (`docs/nightly/nightly-<date>.md`, ~90-day cleanup) that 4c adopts for `docs/audits/`.

## Non-Goals
- Does NOT auto-fix anything. 4c is diagnostic-only — it produces a report. The developer drives fixes through `/3b_create-issue` and `/3d_implement-issue` (or micro-tdd, Jules, etc.).
- Does NOT replace 4b. No architectural drift diagnosis — that remains 4b's domain.
- Does NOT replace 4a. No slice-level acceptance-criteria verification.
- Does NOT create GitHub issues. Outputs `docs/audits/health-<date>.md` — the developer runs `/3b` on chosen findings.
- Does NOT review individual PRs for approval/merge decisions. Recent PRs/commits are a prioritization signal (the recent-change lens), not a review target.
- Does NOT integrate with 0d as a scheduled trigger. 4c is manual-only, independent.

## Constraints
- **HITL workflow.** Read-only scan runs autonomously; report presentation halts for user review. No code modifications.
- **Confidence threshold ≥60.** Lower than 4b's ≥80 — a broad health screen should surface medium-confidence findings (especially security).
- **Scan scope:** `src/` (required) + `api/`, `scripts/`, config files, and database migrations — all if they exist. Config and migrations scoped to security and performance passes only. See Phase 1 for full resolution logic.
- **Subagent architecture:** 3 grouped subagents by affinity. Recent-change lens resolved by the parent and fed to all three.
- **Output:** `docs/audits/health-<YYYY-MM-DD>.md` (durable, tracked). `docs/audits/.last-run.json` updated on each run. ~90-day retention.

## Riskiest Assumption
- **Riskiest Assumption:** Developers will manually triage passive markdown audit reports and initiate `/3b` issue creation and `/3d` implementation for non-acute health findings.
- **Why Fatal:** Periodic read-only audits consistently suffer from the "shelfware effect." Non-acute findings (duplication, minor test gaps, swallowed non-critical errors) are easily deferred as low-priority backlog noise. If the workflow relies on manual intervention to bridge reports and executable issues, developers will ignore the reports over time — causing significant token spend with zero realized fixes.
- **Cheapest Test:** Manually construct a realistic 10-item health audit report for the developer's project containing valid ≥60 confidence findings. Deliver it and count how many items the developer converts into `/3b` issues or fixes within 5 working days.
- **Status:** untested
- **Mitigation (built into report format):** Findings are categorized by impact (Critical → Low). Critical and High findings appear first with concrete suggested fixes. The report opens with an executive summary showing the impact distribution — this surfaces urgency without requiring the developer to read the full report.

---

# Implementation Specification

> Everything below this line is the enriched implementation detail derived from the framing session. An implementer picks up this document and builds `.agents/workflows/4c_codebase-health-audit.md` from it.

## Workflow Frontmatter

```yaml
name: 4c_codebase-health-audit
description: Periodic broad health screening of the full codebase across security, reliability, maintainability, correctness, performance, and dependency health.
type: workflow HITL
trigger: manual
```

---

## Phase 0: Load Memory
Run `.agents/skills/load-memory/SKILL.md` to restore session context (read-only).

---

## Phase 1: Scope Resolution

**Inputs:** User trigger prompt (may specify narrowed scope), filesystem, git history.

### 1.1 Discover Scan Targets

Resolve the scan target set in order:

| Directory / Pattern | Required? | Which passes consume it |
|:---|:---|:---|
| `src/` | **Required** — halt if absent | All 6 passes |
| `api/` | If exists | All 6 passes |
| `scripts/` | If exists | All 6 passes |
| Config files: `.env.example`, `next.config.*`, `supabase/config.toml`, `*.config.js/ts` | If exist | Security, Performance |
| Database migrations: `supabase/migrations/`, `prisma/migrations/`, `drizzle/` | If exist | Security, Performance |

If the user's trigger prompt specifies a narrower scope (e.g., "run 4c on src/features/billing"), honor it — but warn that a narrowed scope may miss cross-cutting findings.

### 1.2 Compute Delta Window (Recent-Change Lens)

1. Read `docs/audits/.last-run.json`. If it exists, extract `last_run` timestamp.
2. Delta window = the **shorter** of:
   - 14 calendar days before now
   - Time since `last_run` timestamp
3. If `.last-run.json` does not exist (first run), use 14 days.
4. Resolve recently-changed files: `git log --since="<delta_start>" --name-only --pretty=format:""` deduplicated, filtered to scan targets only.
5. Pass the changed-file set to all 3 subagents as `priority_files` — these files receive additional scrutiny in every pass.

### 1.3 Collision Check
Read `.memory/BACKLOG_MAP.md`. Drop any scan target directory that is actively being implemented (`status:in progress`) to avoid noisy findings on work-in-progress code. Log skipped directories.

---

## Phase 2: Scan Execution (3 Subagents)

**Context Isolation Rule:** Same as 4a/4b — if this session has modified production code, isolate scans into subagents. Since 4c is always read-only and never follows a `/3d` implementation session, native execution is the norm. Subagents are used for parallelism and context separation between pass groups, not for contamination isolation.

The parent resolves all inputs (file lists, priority files, `.memory/LEARNINGS.md`, confidence scale) and passes them explicitly. Subagents must not sweep the repo.

### Subagent A: Safety Auditor

**Passes:** Security & Secrets, Dependency Health
**Guardrail:** "Scan and report findings only. Do not modify any file. Do not commit or push. Return findings to the parent."

#### A1 — Security & Secrets Pass

Scan for:

| Category | What to detect | Examples |
|:---|:---|:---|
| **Hardcoded secrets** | API keys, tokens, passwords, connection strings in source code | `const API_KEY = "sk-..."`, `password = "admin123"`, base64-encoded credentials, private keys in code |
| **SQL injection** | Raw string concatenation/interpolation in database queries | `` `SELECT * FROM users WHERE id = ${id}` ``, `.query("... " + userInput)`, f-strings in SQL |
| **Unvalidated input** | User/request input used directly without sanitization or validation | `req.body.email` passed to DB without schema validation, URL params used in file paths |
| **Permissive CORS** | `Access-Control-Allow-Origin: *` on non-public APIs, overly broad CORS configs | Wildcard origins on authenticated endpoints, credentials + wildcard combination |
| **Exposed debug** | Debug endpoints, verbose error responses, dev-mode flags in production config | `/debug`, `/test`, `console.log` with sensitive data, `DEBUG=true` in production env, stack traces in API responses |
| **Missing auth** | Route handlers / API endpoints without authentication middleware | Express routes without auth middleware, Next.js API routes without session checks, Supabase RPC without RLS |
| **Insecure config** | Weak crypto, disabled security headers, permissive CSP | `algorithm: 'md5'`, missing `helmet()`, `X-Frame-Options` absent |

#### A2 — Dependency Health Pass

Scan for:

| Category | What to detect | How |
|:---|:---|:---|
| **Known CVEs** | Dependencies with published vulnerabilities | `npm audit --json` / `pip audit --json` / `pnpm audit --json` (run the package manager's native audit command) |
| **Outdated majors** | Dependencies >1 major version behind | `npm outdated --json` / equivalent |
| **Deprecated packages** | Dependencies marked deprecated in registry | npm audit output flags these; also check for `deprecated` field in package metadata |
| **Unmaintained** | Dependencies with no release in >12 months | Heuristic from registry metadata if available; otherwise note as low-confidence |

---

### Subagent B: Quality Auditor

**Passes:** Reliability, Correctness
**Guardrail:** "Scan and report findings only. Do not modify any file. Do not commit or push. Return findings to the parent."

#### B1 — Reliability Pass (Error Handling)

Scan for:

| Category | What to detect | Examples |
|:---|:---|:---|
| **Empty catch blocks** | Exception caught but nothing done | `catch (e) {}`, `except: pass`, `catch (_) {}` |
| **Swallowed errors** | Error caught, logged, but not propagated or handled meaningfully | `catch (e) { console.log(e) }` with no rethrow, return, or fallback — caller sees success |
| **Missing propagation** | Error caught at a low level that should bubble to the caller | Service function catches DB error and returns `null` instead of throwing — caller can't distinguish "not found" from "DB down" |
| **Unhandled async** | Promises without `.catch()`, async functions without try/catch, missing error event handlers | `fetch(url)` without `.catch()`, `async function` with no try/catch around awaited calls |
| **Missing error boundaries** | React component trees without error boundaries around fallible children | Large component subtrees with data fetching but no `ErrorBoundary` wrapper |
| **Generic catch-all** | Catching `Error` or `Exception` base class when specific types should be handled differently | `catch (e: Error)` when `NetworkError` and `ValidationError` need different paths |
| **Missing finally/cleanup** | Resources opened but not cleaned up in error paths | File handles, DB connections, subscriptions opened without `finally` block or `using` |

#### B2 — Correctness Pass (Test Coverage)

Scan for:

| Category | What to detect | How |
|:---|:---|:---|
| **Zero-test modules** | Source modules with no corresponding test file | For each file in scan targets, check for `*.test.*`, `*.spec.*`, or `__tests__/*` counterpart |
| **Critical untested paths** | Auth, payment, data mutation, RLS policies without tests | Heuristic: files in `auth/`, `billing/`, `payment/` dirs, or containing `createUser`, `deleteUser`, `charge`, `transfer`, RLS policy functions |
| **Skipped/disabled tests** | Test files with `.skip()`, `.todo()`, `@pytest.mark.skip`, `xit()` | Grep for skip/disable patterns in test files |
| **Missing edge cases** | Functions handling nullable/optional inputs without null/empty/boundary tests | Heuristic: functions with `?:`, `| null`, `Optional[]` params — check if tests cover null/empty/boundary |
| **Test-to-source ratio** | Modules where test file is <20% the size of the source file (heuristic for thin tests) | Compare file sizes as a rough signal; flag as low-confidence |

---

### Subagent C: Efficiency Auditor

**Passes:** Maintainability, Performance
**Guardrail:** "Scan and report findings only. Do not modify any file. Do not commit or push. Return findings to the parent."

#### C1 — Maintainability Pass (Duplication + Dead Code)

Scan for:

| Category | What to detect | How |
|:---|:---|:---|
| **Duplicated code blocks** | ≥10 lines of substantially similar logic appearing in 2+ locations | Textual similarity analysis across files in scan targets; normalize whitespace and variable names |
| **Copy-paste patterns** | Functions/methods with near-identical structure differing only in entity names or field names | Structural similarity (same control flow, different identifiers) |
| **Extractable utilities** | Repeated inline patterns that should be shared functions | Common patterns: repeated validation logic, repeated formatting, repeated API call boilerplate |
| **Dead exports** | Exported functions/classes/constants not imported anywhere in the project | Trace import graph; flag exports with zero importers (exclude entrypoints and public API) |
| **Unreachable code** | Code after unconditional return/throw, branches that can never execute | Control flow analysis within functions |
| **Unused imports** | Import statements for symbols not referenced in the file | Per-file import analysis |
| **Commented-out code** | Substantial blocks of commented-out code (>5 lines) | Heuristic: consecutive comment lines that parse as valid code |
| **Orphaned files** | Source files not imported or referenced by any other file in the project | Import graph analysis; exclude entrypoints, config files, scripts |

#### C2 — Performance Anti-Patterns Pass

Scan for:

| Category | What to detect | Examples |
|:---|:---|:---|
| **N+1 queries** | Database calls inside loops | `for (const id of ids) { await db.query(...) }`, `.map(async (item) => await supabase.from(...)...)` |
| **Sync in async** | Synchronous blocking operations in async contexts | `fs.readFileSync` in an async handler, `JSON.parse` on unbounded input in an event loop |
| **Missing indexes** | Queries filtering/sorting on columns without indexes (requires migration files) | `WHERE status = ...` or `ORDER BY created_at` on tables without matching indexes in migration files |
| **Large bundle imports** | Importing entire libraries when only one function is needed | `import _ from 'lodash'` instead of `import debounce from 'lodash/debounce'`, `import * as` on large packages |
| **Unbounded queries** | Database queries without `LIMIT`, pagination, or reasonable bounds | `SELECT * FROM large_table` without `.limit()`, `.range()`, or pagination params |
| **Missing memoization** | Expensive computations or renders without caching | React: large list renders without `React.memo`, `useMemo` on expensive transforms; Backend: repeated identical DB queries without caching |
| **Unnecessary re-renders** | React components re-rendering due to unstable references | Inline objects/arrays in JSX props, functions created in render without `useCallback`, context providers with object literals |
| **Missing streaming** | Large data sets loaded entirely into memory instead of streamed | Loading full file contents for processing, fetching all rows then filtering client-side |

---

## Phase 3: Consolidation

The parent receives findings from all 3 subagents and:

### 3.1 Deduplicate
If the same file+line appears in multiple pass findings (e.g., a swallowed error in a function that also has no tests), keep both findings but link them: `Related: [finding-id]`.

### 3.2 Categorize by Impact

| Impact | Criteria | Examples |
|:---|:---|:---|
| **Critical** | Active security vulnerability, data loss risk, or authentication bypass | Hardcoded production API key, SQL injection on public endpoint, missing auth on mutation endpoint |
| **High** | Reliability failure affecting users, known CVE in dependency, missing error handling on critical path | Empty catch on payment flow, high-severity CVE, unhandled rejection in request handler |
| **Medium** | Test coverage gap on important module, significant duplication, performance anti-pattern affecting response times | Zero tests on auth module, N+1 query in API handler, 50-line duplicated block |
| **Low** | Dead code, minor duplication, cosmetic maintainability, low-confidence findings | Unused export, commented-out code, deprecated but non-vulnerable dependency, thin test file |

### 3.3 Score Confidence
Each finding carries a confidence score (60–100) per `.agents/workflows/.reference/confidence-scale.md`. Findings below 60 are dropped. The impact category is independent of confidence — a finding can be Critical impact at 65 confidence (flag it, note uncertainty).

### 3.4 Enrich with Recent-Change Lens
Findings on files in the `priority_files` set (from Phase 1.2) get a `[RECENT]` tag in the report, surfacing that this code was recently modified and the finding may be a regression.

---

## Phase 4: Report Generation

### 4.1 Write Audit Report

Path: `docs/audits/health-<YYYY-MM-DD>.md`

Structure:

```markdown
---
type: audit-report
title: "Health Audit — <YYYY-MM-DD>"
timestamp: <YYYY-MM-DD>
---

# Health Audit — <YYYY-MM-DD>

## Executive Summary
- **Passes run:** 6/6 (or N/6 if narrowed)
- **Delta window:** <start> → <end> (<N> recently-changed files prioritized)
- **Directories scanned:** src/, api/, scripts/ (as applicable)
- **Directories skipped (in-progress):** <list or "none">

| Impact | Count |
|:---|---:|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| **Total** | **N** |

## Critical Impact

| # | Pass | File | Line(s) | Finding | Confidence | Recent? | Suggested Fix |
|---:|:---|:---|:---|:---|---:|:---|:---|
| 1 | Security | src/api/auth.ts | 42 | Hardcoded JWT secret | 95 | [RECENT] | Move to `.env` variable |

## High Impact
(same table format)

## Medium Impact
(same table format)

## Low Impact
(same table format)

## Pass Summaries

### Security & Secrets
- Files scanned: N
- Findings: N (Critical: N, High: N, Medium: N, Low: N)
- Clean areas: <brief note on what looked good>

### Dependency Health
- Audit command: `npm audit` (or equivalent)
- Findings: N
- Clean areas: ...

### Reliability (Error Handling)
...

### Correctness (Test Coverage)
- Modules with zero tests: <list>
- Estimated coverage gap: <heuristic>
...

### Maintainability (Duplication + Dead Code)
- Duplicated blocks found: N
- Dead exports: N
...

### Performance Anti-Patterns
...

## Recommended Next Steps
For each impact category, recommend:
- **Critical:** Fix immediately — run `/3d` or micro-tdd on these.
- **High:** Create issues via `/3b` for next sprint.
- **Medium:** Batch into a maintenance slice via `/3b`.
- **Low:** Address opportunistically during related work.

## Cross-References
- For architectural analysis of flagged modules, run `/4b_audit-architecture-drift` on the target directory.
- Findings tagged `[RECENT]` may be regressions from the delta window — prioritize review.
```

### 4.2 Update Last-Run Metadata

Path: `docs/audits/.last-run.json`

```json
{
  "last_run": "<ISO-8601 timestamp>",
  "passes_run": ["security", "dependency", "reliability", "correctness", "maintainability", "performance"],
  "scan_targets": ["src/", "api/", "scripts/"],
  "total_findings": 42,
  "by_impact": { "critical": 2, "high": 8, "medium": 20, "low": 12 },
  "report_path": "docs/audits/health-<YYYY-MM-DD>.md"
}
```

### 4.3 Retention Policy
Archive or delete `docs/audits/health-*.md` entries older than ~90 days (same policy as `docs/nightly/` in 0d). `.last-run.json` is always kept (only the most recent run matters for delta window).

---

## Phase 5: Handoff

**HALT.** Present the audit report to the user with a summary:

```
[AUDIT COMPLETE] Health audit written to docs/audits/health-<date>.md.
  Critical: N | High: N | Medium: N | Low: N | Total: N findings.
  Review the report and run /3b on findings you want to fix.
```

If zero findings across all passes:
```
[HEALTHY] No findings ≥60 confidence across 6 passes. Codebase is in good health.
```

Never auto-fix. Never create issues. The developer decides.

---

## Clean Exit Rule (Zero Findings)
If no finding meets the ≥60 confidence threshold across any pass → do not generate the report file. Output `[HEALTHY]` and update `.last-run.json` with `total_findings: 0`. This avoids accumulating empty reports.

---

## Subagent Contract Summary

| Subagent | Passes | Input | Guardrail | Output |
|:---|:---|:---|:---|:---|
| **Safety Auditor** | Security & Secrets, Dependency Health | Explicit file list, priority_files, `.memory/LEARNINGS.md`, confidence scale | Report only; no file modifications, commits, or pushes | Findings list with confidence, impact category, location, suggested fix |
| **Quality Auditor** | Reliability, Correctness | Same | Same | Same |
| **Efficiency Auditor** | Maintainability, Performance | Same | Same | Same |

---

## Recommended Next Step
- [x] `create-issue` — create implementation issue for `4c_codebase-health-audit.md` workflow, then implement via `/3d`.
- [ ] Dropped — do not build
