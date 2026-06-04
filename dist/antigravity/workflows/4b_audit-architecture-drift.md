---
name: 4b_audit-architecture-drift
type: workflow
description: Macro Audit. Scans a targeted directory for high-confidence structural drift and generates Foam-linked refactor proposals.
---

TYPE: HITL EXECUTION: Manual trigger only. Do not run autonomously.

# PHASE 1: SCOPE

_INPUT:_ Human trigger prompt.
- IF target directory is undefined in the trigger prompt -> HALT.
- ASK: `Specify target directory to audit. Example: /src/features/billing`

_CONSTRAINTS:_
- Never scan or ingest the entire repository.
- Restrict token scope to the specified target directory.
- Read files from `.memory/` only as needed to identify architecture rules, historical learnings, active backlog items, and system constraints.
- Do not modify production code.
- Do not write refactored code.

# PHASE 2: DEEP SCAN & CONFIDENCE
_INPUT:_ Target directory files and all files in .`memory/`.
_PERSONA:_ Staff-Level System Architect enforcing structural invariants. Focus on architectural drift, domain boundary violations, scalability risks, maintainability blockers, and repeated violations of documented system rules

## Deep Scan Matrix
1. Inline database queries, complex state/effects inside UI render files (must be extracted to hooks/services).
2. Passing props down >3 levels or sprawling localized useState arrays that should be consolidated.
3. Heavy client-side filtering (`.filter()`, `.reduce()`) instead of leveraging Supabase/SQL query structures.
4. Custom component structure or state-management rules ignored.
5. High volumes of cross-domain imports violating system boundaries.
6. Files exceeding 350 lines of code when paired with additional evidence such as mixed responsibilities, inline data access, duplicated logic, complex effects, or ignored extraction rules.
7. Ignores historical learnings.

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

# PHASE 3: OUTPUT
IF issues >= 80 confidence exist:
1. Generate `.tmp/refactor-proposal.md` formatted strictly as "Template B" from `.agents\workflows\3a_create-issue.md`
2. CONSTRAINT: 
- Generate only after confidence filtering and backlog collision checks complete.
- You MUST use double-bracket Foam syntax to link back to exact system laws violated:
- Example: Violates [[A-102]] (Architecture rule)
- Example: Blocks [[BT-042]] (Backlog Task)
3. Do not modify any production codebase files. Do not write refactored code.

# PHASE 4: HANDOFF
HALT execution. Output a 2-line summary of flagged components and confirm `.tmp/refactor-proposal.md` is ready for review. 

Await human instruction:
- Human reviews the proposal.
- IF approved -> Human commands agent to run `create-issue` workflow to commit issues to the backlog and github.