---
name: 2c_reconcile-specs
description: Pre-slicing spec audit. Reconciles Research/Discovery/PRD/Interface-Design (and any declared schema source) for cross-artifact contradictions; proposes resolutions, applies the spec edits the user does not skip.
type: workflow HITL
trigger: manual
version: "1.0.0"
timestamp: 2026-07-28
---

TYPE: HITL EXECUTION: Manual trigger only. Do not run autonomously.

**Hand-off contract:** Gate between `2b_interface-design` and `3b_create-issue`. Audit a feature's spec artifacts for mutual consistency; report to `.tmp/BT-<padded>-slicing-readiness.md` (ephemeral; no workflow reads it), then apply the spec edits the user does not skip. Spec edits are the only durable output — `3b` reads PRD/design docs, never `.tmp/`.

## Phase 0: Load Memory
Run `.agents/skills/load-memory/SKILL.md` (read-only).

## Phase 1: Scope
_INPUT:_ trigger naming the feature (`BT-<padded>`). Absent → HALT, ASK: `Specify the feature. Example: /2c_reconcile-specs BT-003`.
_Resume:_ report exists → recover findings, resume Phase 4 (re-scan only on request).

**Resolve target artifacts** (missing file = a finding, not an error):
- Research `docs/research/*<slug>*.md`; Discovery `docs/discovery/BT-<padded>-*.md`; PRD `docs/prds/BT-<padded>-<feature>.md`; Interface design `docs/design/BT-<padded>-interface.md`.
- Schema source `.memory/DATABASE_SCHEMA.md` + any live introspection source the project declares (assume none unless declared).

**Gate** (after resolution):
- < 2 spec artifacts beyond the PRD → SKIP: `[SKIP] BT-<padded>: too few artifacts; proceed to /3b_create-issue.`
- Epic not pre-slicing (`status:needs_spec`/`status:planned`) → HALT; reconciliation runs before slices exist.

_CONSTRAINTS:_ read only resolved artifacts + `.memory/`; never ingest the repo. No spec edits in Phases 2–3.

## Phase 2: Consistency Scan
**Context Isolation Rule:** Execute natively ONLY IF this session has not authored or modified any target artifact. Otherwise, or if unsure, isolate to an independent Spec-Reconciliation Auditor subagent; resolve targets in the parent and pass the explicit file list (subagent reads only named files, never sweeps).
- **Guardrail:** *"Return findings + one proposed resolution each; do not modify, create, or delete any spec document, and do not apply any resolution."*

Surface contradictions and blocking gaps only — not stylistic drift.

### Scan Matrix
1. **Contract existence:** every contract the PRD/design references (table, field, enum, type, endpoint, key) exists in the schema source. Check mechanically; reason only where the schema can't answer literally.
2. **Semantic contradiction:** behavioral claims agree across Research → PRD → Interface-Design (state transitions, timing/ordering, fallbacks, batching, rate/quota). Flag prose ↔ typed-contract ↔ stress-matrix disagreement.
3. **Attribute rules:** each attribute is extracted or inherited, with an explicit missing-value rule — required-missing (reject) vs optional-missing (degrade/default).
4. **Boundary record:** auth/access and runner/quota constraints a slice must honor are recorded (e.g. service-role secret, timeout, quota).

**Coverage:** examine every resolved artifact and referenced contract; tag any unexamined item `[UNCOVERED]`. Do not exit with an open `[UNCOVERED]`.

### Confidence & Severity
Score each finding 0–100 per `.agents/workflows/.reference/confidence-scale.md`. **Audit scope:** cross-artifact spec inconsistency — a referenced contract absent, or two artifacts stating a claim incompatibly. Report only ≥ 80. Assign severity:
- **P0:** contract missing, or two specs impose incompatible hard requirements — blocks slicing.
- **P1:** artifacts disagree or leave a decision unstated.
- **P2:** incomplete but non-blocking (missing optional rule, inferable default).

## Phase 3: Readiness Report
- No finding ≥ 80 → HALT: `[READY] BT-<padded>: specs consistent; proceed to /3b_create-issue.` Write no file.
- Else write `.tmp/BT-<padded>-slicing-readiness.md`, grouped P0 → P1 → P2. Per finding: **Contradiction** (conflicting claims, each quoted with source path + section/line) and **`PROPOSAL`** (the single reconciling change — which artifact wins and why, or the value/rule to add; recommendation only). Link the governing law where one applies (`[[A-xxx]]`/`[[DR-xxx]]`/`[[G-xxx]]`).

## Phase 4: Resolve & Apply
1. **Present** the report; HALT. All findings apply by default; the user **Skips** exceptions (a skipped finding dies with the ephemeral report).
2. **Apply** each non-skipped `PROPOSAL` as a surgical edit — change only the reconciled claim, never adjacent prose. A finding needing investigation rather than a spec correction → write into the PRD as an **Open Question** (durable; `3b` slices it as a Template A spike). A missing-contract P0 → record as a required pre-Slice-1 migration in the PRD, never silently write the schema.
3. **Version:** bump each edited doc's OKF `version` + `timestamp` once (patch = wording; minor = behavioral change) — per `.agents/rules/okf-protocol.md` §5, not per finding.
4. **Exit criteria:** zero P0 unaddressed; every finding applied, written as an Open Question, or skipped; no open `[UNCOVERED]`. Never mark complete on a "looks consistent" judgment.

## Phase 5: Handoff
HALT. Output a 2-line summary (findings by severity; docs edited with new versions). Hand to `/3b_create-issue`.
