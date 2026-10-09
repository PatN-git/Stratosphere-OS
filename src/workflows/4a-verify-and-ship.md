---
name: 4a-verify-and-ship
description: "Validate test suites against business requirements, acceptance criteria, and security boundaries. Open/update PR once verified. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.3.2"
timestamp: 2026-10-06
---

# Verify and Ship

**Hand-off:** Final gate before pushing and opening or updating the PR. The PR stays draft until every sibling slice is `status:in review|done` (Spikes closed as `done` count). A standalone issue opens non-draft. On ship, set the slice to `status:in review` in BACKLOG_MAP and GitHub; merge closes it and sets `status:done`.

---

## Phase 0: Load Memory
Run the `load-memory` skill to restore session context (read-only).

## Phase 1: Value-Add Gate
*Input:* GitHub Issue/PRD.
0. **Clean-tree guard (every gate, incl. `ship-only`):** run `git status --porcelain`. Any path outside `.memory/`, `docs/`, `.tmp/` (untracked files and generated output such as `dist/` or `theme.tokens.css` included) → HALT: `[UNCOMMITTED] <paths> — commit via /3d-implement-issue first (or stash/remove unrelated files); 4a audits committed work only.` It runs before the bypasses below, so a cosmetic or skipped audit cannot ship uncommitted code.
1. If task is pure UI/cosmetic (layout/CSS/view/copy/visual polish with no data/logic invariants) → proceed directly to Phase 5: Isolated Ship Gate (Output: `[SKIP] Cosmetic task. Audit bypassed.`).
2. If task touches security/RLS, auth, billing/entitlements, core math/algorithms, explicit PRD AC, or is `[size:large]` / `[mode:AFK]` → proceed to Phase 2: Execution (Context Isolation).
3. Else, bypass audit and proceed directly to Phase 5: Isolated Ship Gate.

## Phase 2: Execution (Context Isolation)

> **Named gate — `audit-only`:** Phases 1–4. Produces the coverage map and verdict; touches no branch, commit, or PR. This is the contract `3z-afk-loop` dispatches against; keep the name stable even if the phase numbers move.
- **Resolve targets first:** in the parent, compute the changed-file set and pass explicit paths; **the subagent must never run repo-wide discovery** (`grep -r`, dir sweeps) to locate inputs. Base ref = first that resolves: upstream merge-base (`git diff --name-only "$(git merge-base HEAD origin/<default>)"...HEAD`) → local default branch → files changed on this branch. Never abort if unresolvable — use the best available list. Host-adapt `<default>` (`main`/`master`).
- **Context Isolation Rule:**
  - **Local:** Run Phase 2/3 natively only if this session was read-only on production code (no edits under slice path, no `/3d-implement-issue`; `/0a` memory/branch writes do not taint). If native, run both Spec and Standards audits.
  - **Isolate:** Otherwise run the two audits as **two separate, independent subagents in two isolated contexts** — never one agent doing both (each guardrail is that agent's entire contract; inputs and scopes differ):
    1. **Strict Business-Logic Auditor:** invoke an independent Strict Business-Logic Auditor subagent (using the host's subagent mechanism). Input (full files, not a diff — it maps AC↔tests): Issue/PRD (`docs/prds/BT-<padded>-<name>.md`), design doc (`docs/design/BT-<padded>-interface.md`), resolved test + implementation files, `.memory/LEARNINGS.md`, `.agents/skills/4a-verify-and-ship/references/confidence-scale.md`. Guardrail: "Audit + format the AC↔test table only; do not edit code/tests, do not commit or push; return to main for Phase 4." Output: AC↔test table of gaps ≥ 80 confidence (withhold implementation-only divergences < 70).
    2. **Standards Auditor** (a second, separate subagent — do not fold into the first): Input: changed-file list + the scoped diff command `git diff <base>...HEAD -- <changed paths>` (pass the command, not pasted diff), coding standards, `.agents/skills/4a-verify-and-ship/references/code-smell-baseline.md`. Guardrail: "Report findings only; no edits, commits, or pushes; return to main; scan slice diff only." Output: findings list (File · Smell/Rule · Hard breach | Judgment · One-line fix).

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

> **Named gate — `ship-only`:** this phase alone. Branch-safety + design-drift gate, push, open/update PR, status flip. Never reached by an `audit-only` run. `ship-only` skips Phases 1–2, so it runs the Phase 1 step 0 clean-tree guard first.
1. **Branch isolation:** Verify branch is NOT `main`/`master` AND is correct feature branch for parent. Else halt.
2. **CSS check (UI surfaces only):** Skip when the feature has no UI surface — no `theme.tokens.css` in the app and no UI block in the interface design doc (`2b` Path C). State the skip. A backend-only project has no tokens to synchronize and must not be blocked on them. Otherwise run the design validator:
   ```bash
   python .agents/scripts/design/design_theme.py --design .memory/DESIGN.md --check <app-css-dir>/theme.tokens.css
   ```
   If command exits non-zero, **halt and fail ship**. Synchronize CSS tokens first.
3. Halt for user confirmation to ship (unless pre-authorized).
4. **Release bump + push:** if `scripts/release.py` exists and the branch changes shipped content (`src/` artifacts), run `python scripts/release.py -y` once per PR and commit the result as `release: prepare v<x>` — CI's bump-guard fails the PR otherwise. The clean-tree guard guarantees no uncommitted slice code; commit nothing here except the release bump — never sweep unrelated `.memory/`/`docs/` drift in. (4a never creates the first commit; 3d owns commits.) Push the branch.
5. **PR (one per feature branch):** none exists → `gh pr create` (if connected) as **draft** (`--draft`): feature PR accumulates sibling slices, un-mergeable until parent epic completes (step 8 flips it ready). **Exception:** standalone issue with no parent feature → non-draft. PR exists → update its body; no duplicate PR per slice, no draft-state change here. Title: `feat(BT-<parentPadded>): <parent feature name>`. Body format, build flags, suite record, risk label and read-back: `references/pr-body-and-ship.md`.
   - **Suite:** `python .agents/scripts/pr_body.py suite`; none → run the suite once and record it per the reference.
   - **Build:** save PR's current body to `.tmp/4a-prior-body.md` (`gh pr view <n> --json body -q .body`; none yet → omit the flag), then run `python .agents/scripts/pr_body.py build --slice BT-<padded> --summary "<one line>" --verdict <PASS|WAIVED|SKIP> --audit-rounds <n> --prior-body-file .tmp/4a-prior-body.md --parent BT-<parent> --out .tmp/4a-pr-body-BT-<padded>.md`.
   - **Body file:** pass `--body-file .tmp/4a-pr-body-BT-<padded>.md` on `gh pr create` / `gh pr edit`; once the call succeeds, `rm -f .tmp/4a-pr-body-BT-<padded>.md .tmp/4a-prior-body.md`. Never commit them.
   - **Risk label, then closing-link read-back:** per the reference, after the call.
6. **PR-link comment (bi-directional trace):** `gh issue comment <n> --body "Shipped in PR #<pr> — <pr-url>"`, where `<pr-url>` is the full `https://github.com/<owner>/<repo>/pull/<pr>` link. The terminal gate (step 9) accepts only a comment containing that `/pull/` URL — a bare `#<pr>` fails it — so posting exactly this is what makes the check pass. Its own step on purpose: folded into the status write below, it is the clause that drops.
7. **Ship-status + backport:** Move the slice to `status:in review` (code complete + verified + pushed; awaiting merge): `gh issue edit <n> --remove-label "status:in progress" --add-label "status:in review"` and update BACKLOG Status. Do **not** set `status:done` on ship — `done` is marked when the PR merges and auto-closes the issue.
   - **Clear blockers (single writer for this edge):** this slice is now `in review`, so remove its bare ID from every dependent's `Blocked by` — in `.memory/BACKLOG_MAP.md`. Refresh `generated.at` (and `generated.by`) on any `.memory/` document this step mutates. **and** the GitHub blocked-by relationship (`removeBlockedBy` mutation per `references/github-issue-relations.md`) — so dependents become visibly unblocked and the map stays a faithful mirror.
8. **Epic Check:** If **all sibling sub-issues under parent are `status:in review`, or Spikes closed as `done`** (not closed — they close on merge; query `gh issue view <parent> --json subIssues`) → run the **Feature Acceptance Audit** below, then rebuild the body: step 5 already deleted `.tmp/4a-prior-body.md`, so re-save the PR's current body there first (`gh pr view <n> --json body -q .body`) and run `pr_body.py build … --prior-body-file .tmp/4a-prior-body.md --close-parent` (adds `Closes #<parent>.`; without the prior body earlier slices become `PENDING` and lose their `Closes` lines), `gh pr edit --body-file` it, `rm -f` both scratch files as in step 5, and re-run the `closingIssuesReferences` read-back for the parent, then mark the feature PR ready for review (`gh pr ready <n>`, if connected; no-op if it was opened non-draft), state `"All slices for BT-<parent> in review! PR #<n> ready to merge."`, and move the parent epic to `status:in review` (`gh issue edit <parent> --remove-label "status:in progress" --add-label "status:in review"`). The epic and slices move to `status:done` on PR **merge** (auto-close), not here.
   - **Feature Acceptance Audit** — once per feature, never per slice; an `audit-only` run never reaches this step. Spec: `references/feature-acceptance-audit.md`. Gaps ≥ 80 halt the ship: PR stays draft, epic stays `in progress`.
9. **Terminal sync gate:** run `python .agents/scripts/reconcile.py --require-gh --ids BT-<slice>[,<each dependent cleared in Step 7>][,BT-<parent> when Step 8 flipped the epic] --pr-id BT-<slice> --fields status,blocked_by` per `references/terminal-sync-invariant.md` (covers the slice + epic `in review` and every dependent's `Blocked by` clear; PR-link checked on the slice only). Non-zero → heal per the reference and re-run, **at most 3 attempts**; still non-zero, or `[MIRROR-UNVERIFIED]` → halt and surface the drift. Never loop unbounded; do not emit the ship line until it passes. **Draft rule** (skip for a standalone issue or `local-only`): if any BACKLOG row with `Parent = BT-<parent>` is not `in review`/`done`, the PR must be draft (`gh pr view <n> --json isDraft`). Not draft → heal once with `gh pr ready <n> --undo` and re-check; still not draft → halt `[DRAFT-RULE]`.
10. **Cleanup:** `rm -f .tmp/3d-plan-BT-<padded>.md` (its `## Deviations` are in the PR body now). Keep `.tmp/3d-suite-BT-<padded>.json`.
11. Output: `[SHIPPED] PR #<n> open for BT-<padded>.` (append `risk:one-way` when the label was applied). Never merge.