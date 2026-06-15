---
name: 4b_audit-architecture-drift
description: Macro Audit. Scans a targeted directory for high-confidence structural drift and generates syntax-linked refactor proposals.
---

TYPE: HITL EXECUTION: Manual trigger only. Do not run autonomously.

## Phase 1: Scope

_INPUT:_ Human trigger prompt.
- IF target directory is undefined in the trigger prompt -> HALT.
- ASK: `Specify target directory to audit. Example: /src/features/billing`

_CONSTRAINTS:_
- Never scan or ingest the entire repository.
- Restrict token scope to the specified target directory.
- Read files from `.memory/` only as needed to identify architecture rules, historical learnings, active backlog items, and system constraints.
- Do not modify production code.
- Do not write refactored code.

## Phase 2: Deep Scan & Confidence
**Context Isolation Rule:** Before running the audit, decide whether this session authored the code under audit. Execute natively ONLY IF you can positively confirm this session has been read-only with respect to the target code—i.e., you have not authored or modified code within the target directory this session. Otherwise, or if you are at all unsure, isolate: invoke an independent Staff-Level Architect subagent (using Antigravity's `invoke_subagent` or Claude Code's `Task` tool with the `general-purpose` type) for Phase 2.
- **Guardrails:** *"Return findings + confidence only; do not modify production code or write refactor files (matches Phase 1/3 constraints)."*
- **Output Contract:** The subagent returns the findings and confidence mapping. The main agent handles subsequent logic.

_INPUT:_ Target directory files and all files in .`memory/`.
_PERSONA:_ Staff-Level System Architect enforcing structural invariants. Focus on architectural drift, domain boundary violations, scalability risks, maintainability blockers, and repeated violations of documented system rules

## Deep Scan Matrix
*Note: Best run on settled code; collision check drops findings on in-progress slices.*

### UI-tier Checks (UI projects only; skip for non-UI/headless scopes):
1. [UI-tier] Inline database queries, complex state/effects inside UI render files (must be extracted to hooks/services).
2. [UI-tier] Passing props down >3 levels or sprawling localized useState arrays that should be consolidated.
3. [UI-tier] Heavy client-side filtering (`.filter()`, `.reduce()`) instead of leveraging Supabase/SQL query structures.
4. [UI-tier] Custom component structure or state-management rules ignored.
5. [UI-tier] Structural audit vs. §3 Immortal Components: Scan for layout or structural deviations from the governing Immortal Component specifications (violating [[DR-008]] - UI-tier only, non-UI projects have none).

### Universal / Domain-Neutral Checks (All projects):
6. God-modules and Single Responsibility Principle (SRP) violations: files exceeding 350 lines of code (heuristic trigger escalating toward a potential [[A-003]] 400-line breach) paired with mixed responsibilities, inline data access, duplicated logic, complex side effects, or ignored extraction rules.
7. Mixed I/O and domain boundary violations: mixing database operations, network requests, file system access, and core business math in the same module.
8. Leaked side effects: functions or methods mutating global state, mutating parameters, or introducing untracked state mutations.
9. Dependency inversion violations: high-level modules directly depending on low-level utility implementations rather than abstractions.
10. High volumes of cross-domain imports violating system boundaries.
11. Ignores historical learnings in `.memory/LEARNINGS.md`.

## Confidence scale & reporting threshold
Confidence is not certainty alone. It is the combined score for:
1. **Evidence strength** — Is the issue directly visible in the target directory files or `.memory/` guidance?
2. **Scope relevance** — Is it structural architectural drift, a domain boundary violation, scalability risk, or repeated violation of documented system rules?
3. **Practical impact** — Would this materially affect maintainability, scalability, domain separation, implementation safety, or future feature delivery?
4. **Actionability** — Can the issue be converted into a clear refactor proposal with a specific component, root cause, and remediation direction?

Assign a confidence score from 0–100 using these anchors:
- **0–39: Discard**
  - Speculative, stylistic, linter-level, pre-existing without current impact, already tracked in backlog, or outside the target directory/scope.
  - Do not mention in output.
- **40–69: Weak Signal**
  - Possibly valid, but isolated, low-impact, or lacking connection to documented architectural rules.
  - Do not report unless explicitly asked for exploratory findings.
- **70–79: Near Miss**
  - Likely architectural concern, but missing repeated evidence, explicit rule violation, clear scalability impact, or actionable remediation.
  - Do not report in final output. Use internally only.
- **80–89: Report**
  - Strong evidence of structural drift, domain boundary violation, repeated anti-pattern, ignored documented rule, or unmanaged debt likely to block maintainability/scalability.
  - Include in final out
- **90–100: Critical / Confirmed**
  - Directly proven violation of documented architecture rules or repeated historical failure pattern with clear downstream impact.
  - The issue materially increases implementation risk, feature delivery cost, or system coupling.
  - Include in final output.

When in doubt, lower the score and discard.


## Clean Exit Rule
- *Collision Check*: Drop any detected issues that collide with in progress issues in `.memory/BACKLOG_MAP.md` if same components/directory is affected.
- **Only report issues with confidence ≥ 80.** Focus on issues that truly matter - quality over quantity. IF no architectural issues meet the Confidence >= 80 threshold -> HALT execution.
- OUTPUT: `[HEALTHY] No high-confidence architectural drift detected in [target directory].` Do not generate any intermediate files.

## Phase 3: Output
IF issues >= 80 confidence exist:
1. Generate `.tmp/refactor-proposal.md` formatted strictly as "Template B" from `.agents/workflows/3a_create-issue.md`.
   - **Skeleton format:**
     ```markdown
     ## Overview
     - One sentence: what and why.
     - **Mental Model:** 2-3 bullets on core logic or specific question to answer.
     ## ICE Priorities
     - **Impact:** [Value]
     - **Confidence:** [Value]
     - **ICE Score:** [Calculated Score]
     ## Current state / Problem
     Reference current `files:lines`. Why it's broken or missing. Violates [[A-xxx]] or [[DR-xxx]].
     ## The Path (Vertical Slice Flow)
     - [ ] **Data Layer:**
     - [ ] **Logic Layer:**
     - [ ] **UI Layer:**
     ## Acceptance Criteria (Verifiable)
     - [ ] **Verification:** [Specific test/run command]
     - [ ] Feature is demoable end-to-end.
     ## Dependencies
     - **[[ID]] first** (blocks/blocked-by).
     ## Notes
     Edge cases, trade-offs, and `.memory/LEARNINGS.md` traps.
     ```
2. CONSTRAINT: 
- Generate only after confidence filtering and backlog collision checks complete.
- You MUST use double-bracket syntax to link back to exact system laws violated:
  - Example: Violates [[A-102]] (Architecture rule)
  - Example: Blocks BT-042 (Backlog Task)
3. Do not modify any production codebase files. Do not write refactored code.

## Phase 4: Handoff
HALT execution. Output a 2-line summary of flagged components and confirm `.tmp/refactor-proposal.md` is ready for review. 

Await human instruction:
- Human reviews the proposal.
- IF approved -> Human commands agent to run `/3a_create-issue` workflow to commit issues to the backlog and github.