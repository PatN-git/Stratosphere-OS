---
description: Shared audit-to-slices contract for 4b-audit-architecture-drift and 4c-codebase-health-audit (finding IDs, impact tiers, findings rows, refactor proposal, coverage gate, ICE mapping, retention pin) and its consumers 3b-create-issue and the 4a Feature Acceptance Audit.
version: "1.0.0"
timestamp: 2026-09-24
---

# Audit → Slices Contract

One findings contract for both audits (`4b`, `4c`), one proposal shape for `3b-create-issue` to mint, one spec-of-record rule for audit epics.

---

## §1 Finding IDs
Assign `F-01…F-NN` once per report, after all filtering, ordered Critical → Low, then confidence descending. Never reuse or renumber an ID after the report is written, and never overwrite a report: if its path exists, append `-2`, `-3`… to the stem. External citation form: `docs/audits/<report-stem>.md#F-07` (stem = filename without `.md`) — always the full path, so the §9 retention pin sees every citing issue.

## §2 Impact Tiers

| Impact | Health (`4c`) | Architecture drift (`4b`) |
|:---|:---|:---|
| **🔴 Critical** | Active security vulnerability, auth bypass, data loss risk, hardcoded production secret, critical CVE in direct dependency. | A documented `[[A-xxx]]`/`[[DR-xxx]]` law ignored on an auth, payment, or data-mutation path. |
| **🟠 High** | Reliability failure on critical user path, high-severity CVE, missing error handling on payment/auth/data-mutation flow, zero tests on security-critical module. | A leaked `seam` or domain-boundary violation on a critical user path. |
| **🟡 Medium** | Test gap on important module, significant duplication (≥3 locations or ≥30 lines), performance anti-pattern with measurable latency impact, moderate CVE. | God-module, dependency-inversion violation, or duplicated logic across ≥ 3 modules. |
| **⚪ Low** | Dead code, orphaned files, thin test files, deprecated non-vulnerable dependency, unused imports, commented-out code. | Locality or naming drift with no behavioural risk. |

Impact is independent of confidence — a Critical finding at 65 confidence is still Critical; note uncertainty in suggested fix.

## §3 Findings Row Contract
Every impact section of either report uses one table shape (`4c` adds a `Pass` column after `ID`):

`| ID | File | Line(s) | Finding | Evidence | Confidence | Law | Recent? | Suggested Direction |`

- **Evidence:** the quoted symbol, signature, or ≤ 3-line excerpt that proves the finding. **Never a secret value** — show the symbol and `<REDACTED>` (evidence is copied into issue bodies, which may be public).
- **Law:** `[[A-xxx]]`/`[[DR-xxx]]` IDs that exist in `.memory/`, else `—`. Never a placeholder ID.
- **Recent?:** `✓` or blank in `4c`; always `—` in `4b`.

## §4 Proposal Contract
- **Path:** `.tmp/refactor-proposal-<report-stem>.md`.
- **Line 1, exactly:** `Source: docs/audits/<report-stem>.md`
- **Then, in order:**
  1. `## Epic` — `Title:` (`Maintenance: <scope> — <date>`), `Area:` (one registry `area:` label), `Milestone (proposed):` (§8), `Overview:` one paragraph. Omit the section when the §7 threshold fails.
  2. `## Coverage` — table `| Finding | Impact | Resolution |`, **one row per F-xx in the report**. Resolution is `Slice <N>` (epic child), `Slice <N> (standalone)` (§7), or a §5 exclusion token.
  3. `## Slice <N> — <title>` per slice — a complete Template B body per `references/issue-templates.md`, plus:
     - **Current state / Problem** opens with `Resolves: docs/audits/<report-stem>.md#F-03, docs/audits/<report-stem>.md#F-07`, then each resolved finding's File / Line(s) / Evidence / Law **copied inline**. The issue body is self-sufficient; the report may not exist where the slice is implemented.
     - **ICE Priorities** per §6.
     - **The Path:** mark untouched layers `N/A`.
     - **Acceptance Criteria:** one verifiable check **per resolved F-xx** proving it no longer reproduces (test, command, or grep with expected output), plus the Verification command. Time-to-Value and Stress Cases read `N/A — audit-sourced (no design doc)`.
     - **Dependencies → Parent:** `BT-<epic>` for epic children; `—` for standalone slices. Blocked by: `BT-<slice:N>` for unminted siblings.
- **Clustering:** group findings into slices by module / `seam`. Apply the minimum-slice floor — never one slice per finding by default; never merge findings across unrelated modules to save a slice.

## §5 Coverage Gate
Every F-xx maps to exactly one `Slice <N>` / `Slice <N> (standalone)` or one token: `[OPPORTUNISTIC]` (⚪ default), `[DEFERRED: <reason>]`, `[WONTFIX: <reason>]`. An unmapped finding is `[UNCOVERED]`. A proposal with an open `[UNCOVERED]` is incomplete — never summarise it as "mostly covered".

## §6 ICE Mapping (a rule, not an inference)
- **Impact:** 🔴 `3.0` · 🟠 `2.0` · 🟡 `1.0` · ⚪ `0.5` — a slice takes the **highest** tier among its resolved findings.
- **Confidence:** the **lowest** confidence among its resolved findings → ≥ 90 `100%` · 80–89 `80%` · 60–79 `50%`.
- **Size:** prompted by `3b` as for any slice.
- **Scope label:** every audit slice takes `scope:baseline`.

## §7 Critical Carve-out and Epic Threshold
A slice whose highest resolved tier is 🔴 never takes a parent; its Coverage rows read `Slice <N> (standalone)`. Propose the epic only when ≥ 2 non-🔴 slices exist; otherwise every slice is standalone (all Coverage rows read `Slice <N> (standalone)`) and `## Epic` is omitted.

## §8 Milestone Default
The `vX.Y.0` of the `[ACTIVE]` release in `docs/ROADMAP.md`; if absent, `v1.0.0`. The user confirms it at `3b` approval. A maintenance epic never needs a `3a` MAJOR/MINOR decision.

## §9 Retention Pin
A report is **pinned** while any open issue body cites its path. Resolve the pinned set:
```bash
gh issue list --state open --limit 500 --json body --jq '.[].body' | grep -oE 'docs/audits/[A-Za-z0-9._-]+\.md' | sort -u
```
`gh` absent or unauthenticated → skip retention entirely this run and output `[SKIP] Retention — gh unavailable; no reports deleted.` Never delete a pinned report.

## §10 Epic Spec of Record
An audit epic's issue body is: line 1 the proposal's `Source:` line, then the Overview, then the Coverage table. An **audit epic** is a parent whose body line 1 is `Source: docs/audits/<stem>.md` and which has no PRD at `docs/prds/BT-<padded>-*.md`. Its acceptance input is the epic body plus every child slice body (`Resolves:` lines, inline evidence, ACs) — **never the report file**, which is not committed and may be absent.
