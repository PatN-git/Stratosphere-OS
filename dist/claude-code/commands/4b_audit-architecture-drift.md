---
name: 4b_audit-architecture-drift
description: Macro Audit. Scans a targeted directory for high-confidence structural drift and generates syntax-linked refactor proposals.
type: workflow
version: "1.0.5"
timestamp: 2026-06-18
---

TYPE: HITL EXECUTION: Manual trigger only. Do not run autonomously.

## Phase 1: Scope

_INPUT:_ Human trigger prompt.
- IF target directory is undefined in the trigger prompt -> HALT.
- ASK: `Specify target directory to audit. Example: /src/features/billing`

_CONSTRAINTS:_
- Never scan or ingest the entire repository.
- Read files from `.memory/` only as needed to identify architecture rules, historical learnings, active backlog items, and system constraints.
- Do not modify production code.
- Do not write refactored code.

## Phase 2: Deep Scan & Confidence
**Context Isolation Rule:** Before running the audit, decide whether this session authored the code under audit. Execute natively ONLY IF you can positively confirm this session has been read-only with respect to the target code—i.e., you have not authored or modified code within the target directory this session. Otherwise, or if you are at all unsure, isolate: invoke an independent Staff-Level Architect subagent (using Antigravity's `invoke_subagent` or Claude Code's `Task` tool with the `general-purpose` type) for Phase 2.
- **Guardrails:** *"Return findings + confidence only; do not modify production code or write refactor files (matches Phase 1/3 constraints)."*
- **Output Contract:** The subagent returns the findings and confidence mapping. The main agent handles subsequent logic.

_INPUT:_ Target directory files and all files in .`memory/`.
_PERSONA:_ Staff-Level System Architect enforcing structural invariants. Surgically target architectural drift, domain boundary violations, scalability risks, maintainability blockers, and repeated violations of documented system rules

## Deep Scan Matrix
*Note: Best run on settled code; collision check drops findings on in-progress slices.*

### UI-tier Checks (UI projects only; skip for non-UI/headless scopes):
1. [UI-tier] Inline database queries, complex state/effects inside UI render files (must be extracted to hooks/services).
2. [UI-tier] Passing props down >3 levels or sprawling localized useState arrays that should be consolidated.
3. [UI-tier] Heavy client-side filtering (`.filter()`, `.reduce()`) instead of leveraging Supabase/SQL query structures.
4. [UI-tier] Custom component structure or state-management rules ignored.
5. [UI-tier] Structural audit vs. §3 Immortal Components: Scan for layout or structural deviations from the governing Immortal Component specifications (violating [[DR-008]] - UI-tier only, non-UI projects have none).

### Universal / Domain-Neutral Checks (All projects):
6. God-modules and interface depth violations: files exceeding 350 lines of code (heuristic trigger escalating toward a potential [[A-003]] 400-line breach) paired with mixed responsibilities, inline data access, duplicated logic, or ignored extraction rules. Apply the deletion test: would deleting this module concentrate complexity, or just move it?
7. Mixed I/O and leaked seams: mixing database operations, network requests, file system access, and core business math in the same module instead of utilizing clean interfaces and adapters.
8. Leaked side effects: functions or methods mutating global state, mutating parameters, or introducing untracked state mutations that degrade local reasoning.
9. Dependency inversion violations: high-level modules directly depending on low-level utility implementations rather than abstractions. Ensure seams are defined via clean interfaces/adapters to preserve locality.
10. High volumes of cross-domain imports violating system boundaries and locality.
11. Ignores historical learnings in `.memory/LEARNINGS.md`.

## Confidence scale & reporting threshold
Score findings 0–100 per `.agents/workflows/.reference/confidence-scale.md`; report only ≥ 80.


## Clean Exit Rule
- *Collision Check*: Drop any detected issues that collide with in progress issues in `.memory/BACKLOG_MAP.md` if same components/directory is affected.
- IF no architectural issues meet the Confidence >= 80 threshold -> HALT execution.
- OUTPUT: `[HEALTHY] No high-confidence architectural drift detected in [target directory].` Do not generate any intermediate files.

## Phase 3: Output
IF issues >= 80 confidence exist:
1. Generate `.tmp/refactor-proposal.md` formatted strictly as "Template B" from `.agents/workflows/.reference/issue-templates.md`.
2. CONSTRAINT: 
- Generate only after confidence filtering and backlog collision checks complete.
- You MUST use double-bracket syntax to link back to exact system laws violated:
  - Example: Violates [[A-102]] (Architecture rule)
  - Example: Blocks BT-042 (Backlog Task)

## Phase 4: Handoff
HALT execution. Output a 2-line summary of flagged components and confirm `.tmp/refactor-proposal.md` is ready for review. 

Await human instruction:
- Human reviews the proposal.
- IF approved -> Human commands agent to run `/3b_create-issue` workflow to commit issues to the backlog and github.