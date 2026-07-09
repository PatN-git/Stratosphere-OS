---
name: 4a_verify-and-ship
description: Validates that test suites match business requirements, acceptance criteria, and security boundaries. Opens a traceable PR once the slice is verified.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.13"
timestamp: 2026-07-09
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
3. If none of the above are met, the audit is skipped. Proceed to Phase 5.

## Phase 2: Execution
**Context Isolation Rule:** Before running the audit, verify whether this session authored the code under audit. Execute natively ONLY IF you can positively confirm this session has been read-only with respect to production code—i.e., you have not run `/3d_implement-issue` and have not edited files under the slice's source paths this session. (Session-setup writes by `/0a` to `.memory/STATUS.md` or branch checkouts do not count as tainting). If executing natively, the agent MUST run both audits/axes (Spec Axis and Standards Axis) natively in sequence or parallel. Otherwise, or if you are at all unsure, isolate: invoke two independent parallel subagents (using Antigravity's `invoke_subagent` or Claude Code's `Task` tool with the `general-purpose` type) for Phase 2–3:

1. **Strict Business-Logic Auditor (Spec Axis):**
   - **Guardrails:** *"Audit + format the AC↔test table only; do not edit code/tests, do not commit or push; return to main for Phase 4."*
   - **Scope:** stated requirements, acceptance criteria, business logic, and security boundaries.
   - **Input:** GitHub Issue/PRD + frozen design doc, new/modified test files, relevant implementation files, `.memory/LEARNINGS.md`, and `.agents/workflows/.reference/confidence-scale.md`.
   - **Persona:** Strict Business Logic Auditor. Restrict audit to requirements and security boundaries.
   - **Confidence Scale & Reporting Threshold:** Score findings 0–100 per `.agents/workflows/.reference/confidence-scale.md`; report only ≥ 80.
   - **Implementation-only Divergence Rule:** Any implementation-only divergence (no PRD/design contract violation) caps at < 70 confidence and is withheld.
   - **Output Contract:** The subagent returns the AC↔test table only.

2. **Standards Auditor (Standards Axis):**
   - **Guardrails:** *"Review the slice diff for code-smell/standards violations only; do not edit code/tests, do not commit or push; return to main for Phase 4."*
   - **Scope:** slice diff only (new/modified files for this slice), never the whole repo.
   - **Input:** Slice diff (new/modified files), `.agents/workflows/.reference/code-smell-baseline.md`, plus any repo standards doc (`CODING_STANDARDS.md` or `.memory/ARCHITECTURE.md`).
   - **Persona:** Standards Auditor. Review the slice diff for code quality, naming, maintainability, and baseline code smells.
   - **Output Contract:** A separate findings list: `File · Smell/Rule · Hard breach | Judgment call · One-line fix`.

### Clean Exit Rule
- IF no spec issues meet the **confidence >= 80** threshold AND no standards violations are found → proceed to Phase 5.
- OUTPUT: `[PASS] No high-confidence logical or security anomalies identified. Code meets quality standards. Slice is verified.`
Do not generate additional output.

## Phase 3: Output
IF issues exist, output them in two clearly separated sections (never merge or re-rank them):

### 1. Spec / Business-Logic (Ship-Blocking)
IF issues **confidence >= 80** exist, output only compact, dense markdown table mapping PRD Acceptance Criteria (AC) directly to tests:

| AC / Requirement | Test Target | Status | Confidence | Gap / Security Risk |
|---|---|---:|---:|---|
| [1-line AC or requirement description] | [test_name] or [NONE] | FAIL | [80-100] | [Missing assertion, untested edge case, business logic gap, or security boundary risk] |

*(Optional Footnote)* If sub-threshold findings (40-79) were identified and withheld, append: *"Note: <N> sub-threshold findings were withheld from this report."*

### 2. Standards / Code Smells (Advisory)
IF code smell or standards violations exist, output them in a separate table. This table is advisory and does not auto-block shipping (the human decides at Phase 4):

| File | Smell / Rule | Hard breach \| Judgment call | One-line fix |
|---|---|---|---|
| [filename] | [Smell name/Rule ID] | [Hard breach or Judgment call] | [Proposed fix description] |

## Phase 4: Handoff
HALT execution. Await human instruction:
- Human commands agent back to standard TDD loop to implement missing test coverage, OR approves.
- If the user's response to a gap report authorizes shipping, proceed to Phase 5 on a clean re-audit without a second halt. If gaps remain unresolved → back to the TDD loop; NO PR.

## Phase 5: Isolated Ship Gate
_INPUT:_ Verified code changes.
_ACTION:_ Push isolated changes and open/update the PR.
1. **Branch isolation:** Enforce that the current branch is NOT `main`/`master` (`AGENT.md` branch rule) AND is the feature branch for this slice's parent. If on `main` → HALT and instruct the user to branch first.
2. Run the CSS design validator to check alignment with `DESIGN.md`:
   - Command:
   ```bash
   python .agents/scripts/design/design_theme.py --design .memory/DESIGN.md --check <app-css-dir>/theme.tokens.css
   ```
   If this command exits with a non-zero code, **halt and fail the ship**. The generated CSS is out of sync with `.memory/DESIGN.md` or was hand-edited. The agent (or user) must run `design_theme` with `--out` to synchronize, verify the changes, and commit the synchronized CSS file before shipping.
3. HALT for explicit user confirmation to ship (unless pre-authorized in Phase 4 or by an orchestrating workflow).
4. On confirmation: commit any uncommitted slice code+tests ONLY on the isolated branch (message: `<type>(BT-<padded>): <slice summary>`). This is a safety net for uncommitted slice files only — never sweep unrelated `.memory/`/`docs/` drift into it. (Note: 4a never creates the first commit; 3d owns commits). Push the branch.
5. The PR is ONE per feature branch: if no PR exists for the branch → create it with `gh pr create` (if connected); else UPDATE its body and add a comment noting the re-verification — do NOT create a duplicate PR per slice. The PR body accumulates each shipped slice:
   - `Closes #<sliceIssue>` (and the parent `BT-<padded>`)
   - One-line slice summary
   - Extend the AC↔test coverage table (if audited), OR `[PASS] slice verified`, OR `[SKIP] cosmetic`
   - `[ ] Manual QA Required` (if needs_manual_qa is flagged by implementer)
   - Keep design ref `docs/design/BT-<padded>-interface.md` (if UI)
   - Keep test cmd + result
   - Keep relevant `[[L-xxx]]`/`[[A-xxx]]` references
6. Comment the PR link back on the GitHub issue (bi-directional trace); leave the slice at `status:in progress` in GitHub and `.memory/BACKLOG_MAP.md` (do NOT set status:done on ship; the slice is marked done when the PR is merged and automatically closes the issue).
7. Output: `[SHIPPED] PR #<n> open for BT-<padded>. /4b_audit-architecture-drift is optional next.` Never merge.
   - **Epic Check:** If all sub-issues under `#parent` are closed (`gh issue view <parent>`), state: `"All sub-issues for BT-<parent> complete! PR #<n> ready to merge (human), and BT-<parent> ready for status:done & closure."` (using `gh issue edit <parent> --remove-label "status:in progress" --add-label "status:done"`).