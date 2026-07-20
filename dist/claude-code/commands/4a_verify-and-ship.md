---
name: 4a_verify-and-ship
description: Validate test suites against business requirements, acceptance criteria, and security boundaries. Open/update PR once verified.
type: workflow HITL
trigger: manual
version: "1.1.2"
timestamp: 2026-07-17
---

# Verify and Ship

**Hand-off contract:** Final gate before pushing the feature branch and opening/updating the PR. The feature PR is opened as a **draft** and marked ready for review only when all sibling slices are `status:in review` (a standalone issue with no parent opens non-draft) — this keeps a partly-built feature un-mergeable until all its slices land. On ship, moves the slice to `status:in review` in `.memory/BACKLOG_MAP.md` and GitHub (code complete + verified + pushed to the feature PR, awaiting merge); the PR merge later closes the slice issue and marks it `done`.

---

## Phase 0: Load Memory
Run `.agents/skills/load-memory/SKILL.md` to restore session context (read-only).

## Phase 1: Value-Add Gate
*Input:* GitHub Issue/PRD.
1. If task is pure UI/cosmetic (layout/CSS/view/copy/visual polish with no data/logic invariants) → proceed directly to Phase 5: Isolated Ship Gate (Output: `[SKIP] Cosmetic task. Audit bypassed.`).
2. If task touches security/RLS, auth, billing/entitlements, core math/algorithms, explicit PRD AC, or is `[size:large]` / `[mode:AFK]` → proceed to Phase 2: Execution (Context Isolation).
3. Else, bypass audit and proceed directly to Phase 5: Isolated Ship Gate.

## Phase 2: Execution (Context Isolation)
- **Context Isolation Rule:**
  - **Local:** Run Phase 2/3 natively only if this session was read-only on production code (no edits under slice path, no `/3d_implement-issue`; `/0a` memory/branch writes do not taint). If native, run both Spec and Standards audits.
  - **Isolate:** Otherwise run the two audits as **two separate, independent subagents in two isolated contexts** — never one agent doing both (each guardrail is that agent's entire contract; inputs and scopes differ):
    1. **Strict Business-Logic Auditor:** invoke an independent Strict Business-Logic Auditor subagent (via `invoke_subagent` or `Task` tool). Input: Issue/PRD, design doc, tests, implementation files, `.memory/LEARNINGS.md`, `.agents/workflows/.reference/confidence-scale.md`. Guardrail: "Audit + format the AC↔test table only; do not edit code/tests, do not commit or push; return to main for Phase 4." Output: AC↔test table of gaps ≥ 80 confidence (withhold implementation-only divergences < 70).
    2. **Standards Auditor** (a second, separate subagent — do not fold into the first): Input: slice diff (new/modified files only), coding standards, `.agents/workflows/.reference/code-smell-baseline.md`. Guardrail: "Report findings only; no edits, commits, or pushes; return to main; scan slice diff only." Output: findings list (File · Smell/Rule · Hard breach | Judgment · One-line fix).

### Clean Exit Rule
If no spec issues (confidence ≥ 80) and no standards violations → proceed directly to Phase 5: Isolated Ship Gate. Output: `[PASS] Slice verified.`

## Phase 3: Output
If issues exist, output in two separate sections:

### 1. Spec / Business-Logic (Ship-Blocking)
Map PRD Acceptance Criteria (AC) directly to tests:

| AC / Requirement | Test Target | Status | Confidence | Gap / Security Risk |
|---|---|---:|---:|---|
| [AC description] | [test_name] or [NONE] | FAIL | [80-100] | [Description of missing test coverage or gap] |

*(Optional Footnote)* If sub-threshold findings (40-79) were withheld, append: "Note: <N> sub-threshold findings were withheld."

### 2. Standards / Code Smells (Advisory)
Advisory findings (does not block shipping):

| File | Smell / Rule | Hard breach \| Judgment call | One-line fix |
|---|---|---|---|
| [filename] | [Rule ID] | [Hard breach or Judgment] | [Proposed fix] |

## Phase 4: Handoff
Halt. Await human approval. If approved, or if user response to gap report authorizes shipping, proceed to Phase 5: Isolated Ship Gate (clean re-audit without second halt). If gaps remain unresolved and unauthorized → return to TDD loop (no PR).

## Phase 5: Isolated Ship Gate
1. **Branch isolation:** Verify branch is NOT `main`/`master` AND is correct feature branch for parent. Else halt.
2. **CSS check:** Run design validator:
   ```bash
   python .agents/scripts/design/design_theme.py --design .memory/DESIGN.md --check <app-css-dir>/theme.tokens.css
   ```
   If command exits non-zero, **halt and fail ship**. Synchronize CSS tokens first.
3. Halt for user confirmation to ship (unless pre-authorized).
4. **Push:** Commit only uncommitted slice code+tests (no memory/doc drift) on the isolated branch (message: `<type>(BT-<padded>): <slice summary>`). Safety net for uncommitted slice files only — never sweep unrelated `.memory/`/`docs/` drift in. (4a never creates the first commit; 3d owns commits.) Push the branch.
5. **PR (one per feature branch):** if no PR exists for the branch → create with `gh pr create` (if connected) as a **draft** (`--draft`) — the feature PR accumulates sibling slices and must stay un-mergeable until the parent epic is complete (step 7 flips it ready). **Exception:** a standalone issue with no parent feature is a complete unit — create it non-draft. Else (PR exists) → UPDATE its body and add a comment noting the re-verification; do NOT create a duplicate PR per slice and do NOT change its draft state here. Title: `feat(BT-<parentPadded>): <parent feature name>`. Body accumulates each shipped slice: `Closes #<sliceIssue>` (and parent `BT-<padded>`), one-line slice summary, design doc link (if UI), the AC↔test coverage table (if audited) OR `[PASS] slice verified` OR `[SKIP] cosmetic`, `[ ] Manual QA Required` if flagged, test command + result, and relevant `[[L-xxx]]`/`[[A-xxx]]` references.
6. **Ship-status + backport:** Comment the PR link on the GitHub issue (bi-directional trace). Move the slice to `status:in review` (code complete + verified + pushed; awaiting merge): `gh issue edit <n> --remove-label "status:in progress" --add-label "status:in review"` and update BACKLOG Status. Do **not** set `status:done` on ship — `done` is marked when the PR merges and auto-closes the issue.
   - **Clear blockers (single writer for this edge):** this slice is now `in review`, so remove its bare ID from every dependent's `Blocked by` — in `.memory/BACKLOG_MAP.md` **and** the GitHub blocked-by relationship (`gh issue edit <dependent> --remove-blocked-by <n>` where supported) — so dependents become visibly unblocked and the map stays a faithful mirror.
7. **Epic Check:** If **all sibling sub-issues under the parent are `status:in review`** (not "closed" — they close only on merge, which this gate enables) → mark the feature PR ready for review (`gh pr ready <n>`, if connected; no-op if it was opened non-draft), state `"All slices for BT-<parent> in review! PR #<n> ready to merge."`, and move the parent epic to `status:in review` (`gh issue edit <parent> --remove-label "status:in progress" --add-label "status:in review"`). The epic and slices move to `status:done` on PR **merge** (auto-close), not here.
8. Output: `[SHIPPED] PR #<n> open for BT-<padded>.` Never merge.