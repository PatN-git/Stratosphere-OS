---
name: 4b_audit-architecture-drift
description: Macro Audit. Scans a targeted directory for high-confidence structural drift and generates syntax-linked refactor proposals.
type: workflow
trigger: manual
version: "1.0.10"
timestamp: 2026-07-17
---

TYPE: HITL EXECUTION: Manual trigger only. Do not run autonomously.

## Phase 0: Load Memory
Run `.agents/skills/load-memory/SKILL.md` to restore session context (read-only).

## Phase 1: Scope

_INPUT:_ Human trigger prompt.
- If the target directory is undefined in the trigger prompt → HALT.
- ASK: `Specify target directory to audit. Example: /src/features/billing`

_CONSTRAINTS:_
- Never scan or ingest the entire repository.
- Read `.memory/` only as needed for architecture rules, historical learnings, active backlog items, and system constraints.
- Do not modify production code.
- Do not write refactored code.

## Phase 2: Deep Scan & Confidence
**Context Isolation Rule:** Execute natively ONLY IF you can positively confirm this session has been read-only with respect to the target code (you have not authored or modified code within the target directory this session). Otherwise, or if unsure, isolate: invoke an independent Staff-Level Architect subagent (Antigravity `invoke_subagent` or Claude Code `Task` general-purpose) for Phase 2.
- **Guardrails:** *"Return findings + confidence only; do not modify production code or write refactor files (matches Phase 1/3 constraints)."*
- **Output Contract:** the subagent returns the findings + confidence mapping; the main agent handles subsequent logic.

_INPUT:_ Target directory files, all files in `.memory/`, and `.agents/workflows/.reference/confidence-scale.md`.
_PERSONA:_ Staff-Level System Architect enforcing structural invariants. Surgically target architectural drift, domain-boundary violations, scalability risks, maintainability blockers, and repeated violations of documented system rules.

## Deep Scan Matrix
*Note: Best run on settled code; the collision check drops findings on in-progress slices.*

### UI-tier Checks (UI projects only; skip for non-UI/headless scopes):
1. [UI-tier] Inline database queries or complex state/effects inside UI render files (must extract to hooks/services).
2. [UI-tier] Props drilled >3 levels, or sprawling local `useState` arrays that should be consolidated.
3. [UI-tier] Heavy client-side filtering (`.filter()`, `.reduce()`) instead of Supabase/SQL query structures.
4. [UI-tier] Custom component structure or state-management rules ignored.
5. [UI-tier] Structural audit vs. §3 Immortal Components: layout/structural deviations from the governing Immortal Component specs (violating [[DR-008]] — UI-tier only; non-UI projects have none).

### Universal / Domain-Neutral Checks (All projects):
6. God-modules and interface depth violations: files exceeding 350 lines (heuristic escalating toward a potential [[A-003]] 400-line breach) paired with mixed responsibilities, inline data access, duplicated logic, or ignored extraction rules. Apply the deletion test: would deleting this module concentrate complexity, or just move it?
7. Mixed I/O and leaked seams: database operations, network requests, file-system access, and core business math in the same module instead of clean interfaces and adapters.
8. Leaked side effects: functions mutating global state, mutating parameters, or introducing untracked state mutations that degrade local reasoning.
9. Dependency-inversion violations: high-level modules depending directly on low-level utility implementations rather than abstractions. Ensure seams are defined via clean interfaces/adapters to preserve locality.
10. High volumes of cross-domain imports violating system boundaries and locality.
11. Ignores historical learnings in `.memory/LEARNINGS.md`.

## Confidence scale & reporting threshold
**Audit scope:** structural architectural drift, domain-boundary violations, scalability/maintainability risks, and repeated violations of documented system rules. A Report-grade (≥80) finding looks like structural drift, a leaked seam, or an ignored documented architecture rule (`[[A-xxx]]`/`[[DR-xxx]]`).
Score findings 0–100 per the **Audit scope** above and `.agents/workflows/.reference/confidence-scale.md`; report only ≥ 80.

## Clean Exit Rule
- *Collision Check:* Drop any detected issue that collides with an in-progress issue in `.memory/BACKLOG_MAP.md` (same components/directory affected).
- If no architectural issue meets the Confidence ≥ 80 threshold → HALT.
- OUTPUT: `[HEALTHY] No high-confidence architectural drift detected in [target directory].` Do not generate any intermediate files.

## Phase 3: Output
If issues ≥ 80 confidence exist:
1. Generate `.tmp/refactor-proposal.md` formatted strictly as "Template B" from `.agents/workflows/.reference/issue-templates.md`.
2. CONSTRAINT:
- Generate only after confidence filtering and backlog collision checks complete.
- Use double-bracket syntax to link back to the exact system laws violated:
  - Example: Violates [[A-102]] (Architecture rule)
  - Example: Blocks BT-042 (Backlog Task)

## Phase 4: Handoff
HALT. Output a 2-line summary of flagged components and confirm `.tmp/refactor-proposal.md` is ready for review.

Await human instruction:
- Human reviews the proposal.
- If approved → Human commands the agent to run `/3b_create-issue` to commit issues to the backlog and GitHub.
