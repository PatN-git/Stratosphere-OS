---
name: 4a_verify-and-ship
description: Validates that test suites match business requirements, acceptance criteria, and security boundaries. Opens a traceable PR once the slice is verified.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.6"
timestamp: 2026-06-22
---

## Phase 1: Value-Add Gate
_INPUT:_ GitHub Issue/PRD.
_ACTION:_ Enforce risk gate on target issue to justify a focused test-alignment audit.
1. IF the task is a pure UI/cosmetic change, standard layout tweak, CSS/Tailwind adjustment, basic view rendering, copy change, or simple visual polish with no underlying data/logic invariants → proceed to Phase 5 (cosmetic ship; verified by 3d/micro-tdd Fast-Track B).
    - OUTPUT: `[SKIP] Pure UI/cosmetic task with no logical or security invariants. Audit bypassed to save tokens.`
2. IF the task touches any of the following -> PROCEED to Phase 2:
  - Supabase RLS policies
  - User authentication or authorization
  - Billing, payments, credits, limits, or entitlements
  - Core business math, calculations, algorithms, or ranking logic
  - Security boundaries between users, tenants, teams, or roles
  - Explicit PRD acceptance criteria with meaningful edge cases
  - A `[size:large]` `[type:AFK]`

## Phase 2: Execution
**Context Isolation Rule:** Before running the audit, verify whether this session authored the code under audit. Execute natively ONLY IF you can positively confirm this session has been read-only with respect to production code—i.e., you have not run `/3d_implement-issue` and have not edited files under the slice's source paths this session. (Session-setup writes by `/0a` to `.memory/STATUS.md` or branch checkouts do not count as tainting). Otherwise, or if you are at all unsure, isolate: invoke an independent Strict Business-Logic Auditor subagent (using Antigravity's `invoke_subagent` or Claude Code's `Task` tool with the `general-purpose` type) for Phase 2–3.
- **Guardrails:** *"Audit + format the AC↔test table only; do not edit code/tests, do not commit or push; return to main for Phase 4."*
- **Output Contract:** The subagent returns the AC↔test table only. The main agent then resumes for the Phase 4 HITL halt.

_INPUT:_
- GitHub Issue/PRD + the frozen design doc (`docs/design/BT-<padded>-interface.md`)
- New/modified test files
- relevant implementation files when needed to understand what the tests verify 
- `.memory/LEARNINGS.md`
- `.agents/workflows/.reference/confidence-scale.md`.

_PERSONA:_ Strict Business Logic Auditor. Relentlessly restrict audit to requirements and security boundaries.

## Confidence scale & reporting threshold
**Audit scope:** stated requirements, acceptance criteria, business logic, and security boundaries (Supabase RLS, auth/authz, billing/credits/limits). A Report-grade (≥80) finding looks like a missing assertion of a stated requirement, an untested specified edge case, or a security-boundary bypass.
Score findings 0–100 per the **Audit scope** above and `.agents/workflows/.reference/confidence-scale.md`; report only ≥ 80.

- **Implementation-only Divergence Rule:** Any implementation-only divergence (where the code does something different from design/primitives but does NOT violate any stated PRD Acceptance Criteria or Design Contract) MUST cap at [Weak Signal] (confidence < 70) and is withheld from the final report.

## Clean Exit Rule
- IF no architectural issues meet the **confidence >= 80** threshold → proceed to Phase 5.
- OUTPUT: `[PASS] No high-confidence logical or security anomalies identified. Slice is verified.` 
Do not generate additional output.

## Phase 3: Output
IF issues **confidence >= 80** exist, output only compact, dense markdown table mapping PRD Acceptance Criteria (AC) directly to tests:

| AC / Requirement | Test Target | Status | Confidence | Gap / Security Risk |
|---|---|---:|---:|---|
| [1-line AC or requirement description] | [test_name] or [NONE] | FAIL | [80-100] | [Missing assertion, untested edge case, business logic gap, or security boundary risk] |

*(Optional Footnote)* If sub-threshold findings (40-79) were identified and withheld, append: *"Note: <N> sub-threshold findings were withheld from this report."*

## Phase 4: Handoff
HALT execution. Await human instruction:
- Human commands agent back to standard TDD loop to implement missing test coverage, OR approves.
- If the user's response to a gap report authorizes shipping, proceed to Phase 5 on a clean re-audit without a second halt. If gaps remain unresolved → back to the TDD loop; NO PR.

## Phase 5: Ship (gated, HITL)
Reached ONLY from a clean state — Phase 1 `[SKIP]`, Phase 3 `[PASS]`, or Phase 4 approval. NEVER while ≥80 gaps remain open.
1. Branch isolation: Enforce that the current branch is NOT `main`/`master` (`AGENT.md` branch rule) and that the current branch is the feature branch for this slice's parent. If on main → HALT and instruct the user to branch first.
2. **Design Drift Gate:** If this slice involves UI/styling, verify that the compiled token stylesheet is in sync with the design system source of truth:
   ```bash
   python .agents/scripts/design/design_theme.py --design .memory/DESIGN.md --check <app-css-dir>/theme.tokens.css
   ```
   If this command exits with a non-zero code, **halt and fail the ship**. The generated CSS is out of sync with `.memory/DESIGN.md` or was hand-edited. The agent (or user) must run `design_theme` with `--out` to synchronize, verify the changes, and commit the synchronized CSS file before shipping.
3. HALT for explicit user confirmation to ship (unless pre-authorized in Phase 4).
3. On confirmation: commit any uncommitted slice code+tests ONLY on the isolated branch (message: `<type>(BT-<padded>): <slice summary>`). This is a safety net for uncommitted slice files only — never sweep unrelated `.memory/`/`docs/` drift into it. (Note: 4a never creates the first commit; 3d owns commits). Push the branch.
4. The PR is ONE per feature branch: if no PR exists for the branch → create it with `gh pr create` (if connected); else UPDATE its body and add a comment noting the re-verification — do NOT create a duplicate PR per slice. The PR body accumulates each shipped slice:
   - `Closes #<sliceIssue>` (and the parent `BT-<padded>`)
   - One-line slice summary
   - Extend the AC↔test coverage table (if audited), OR `[PASS] slice verified`, OR `[SKIP] cosmetic`
   - Keep design ref `docs/design/BT-<padded>-interface.md` (if UI)
   - Keep test cmd + result
   - Keep relevant `[[L-xxx]]`/`[[A-xxx]]` references
5. Comment the PR link back on the GitHub issue (bi-directional trace); set the issue/`BACKLOG_MAP.md` status appropriately.
6. Output: `[SHIPPED] PR #<n> open for BT-<padded>. /4b_audit-architecture-drift is optional next.` Never merge.
   - **Epic Check:** If all sub-issues under `#parent` are closed (`gh issue view <parent>`), state: `"All sub-issues for BT-<parent> complete! PR #<n> ready to merge (human), and BT-<parent> ready for status:done & closure."`