---
name: 4a-verify-and-ship
description: "Validate test suites against business requirements, acceptance criteria, and security boundaries. Open/update PR once verified. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.8.0"
timestamp: 2026-10-22
---

# Verify and Ship

**Hand-off contract:** Final gate before pushing and opening or updating the PR. The unit PR stays draft until every slice of every epic in it is `status:in review|done` (Spikes closed as `done` count). A standalone issue opens non-draft. On ship, a child slice goes `status:done` and is closed (GitHub's progress bar counts closed issues); a standalone issue goes `status:in review` and its merge closes it. Each epic goes `in review` once its own slices are all shipped; merge closes every epic the PR completed.

---

## Phase 0: Load Memory
Run the `load-memory` skill to restore session context (read-only).

## Phase 1: Value-Add Gate
*Input:* slice issue + parent PRD §8 (`BT-<parentPadded>` resolved as in Phase 2).
0. **Clean-tree guard (every gate, incl. `ship-only`):** run `git status --porcelain`. Any path outside `.memory/`, `docs/`, `.tmp/` (untracked files and generated output such as `dist/` or `theme.tokens.css` included) → HALT: `[UNCOMMITTED] <paths> — commit via /3d-implement-issue first (or stash/remove unrelated files); 4a audits committed work only.` Then run `python .agents/scripts/floor_guard.py`: exit 1 → HALT `[FLOOR] <findings> — fix via /3d-implement-issue (a loosening needs a human-merged Floor exceptions row)`; exit 2 (could not run) halts the same, never a pass. Both run before the bypasses below.
   Record the decision below as `phase1` per `references/pr-body-and-ship.md` § Audit findings: `bypass` for steps 1 and 3, `trigger:<name>` for step 2.
1. If task is pure UI/cosmetic (layout/CSS/view/copy/visual polish with no data/logic invariants) → proceed directly to Phase 5: Isolated Ship Gate (Output: `[SKIP] Cosmetic task. Audit bypassed.`).
2. If task touches security/RLS, auth, billing/entitlements, core math/algorithms, covers a PRD §8 Definition of Done item, or is `[size:large]` / `[mode:AFK]` → proceed to Phase 2: Execution (Context Isolation).
3. Else, bypass audit and proceed directly to Phase 5: Isolated Ship Gate.

## Phase 2: Execution (Context Isolation)

> **Named gate — `audit-only`:** Phases 1–4. Produces the coverage map and verdict; touches no branch, commit, or PR. This is the contract `3z-afk-loop` dispatches against; keep the name stable even if the phase numbers move. After each audit, record the findings per `references/pr-body-and-ship.md` § Audit findings.
- **Resolve targets first:** in the parent, compute the changed-file set and pass explicit paths; **the subagent must never run repo-wide discovery** (`grep -r`, dir sweeps) to locate inputs.
  - Base ref = first that resolves: upstream merge-base (`git diff --name-only "$(git merge-base HEAD origin/<default>)"...HEAD`) → local default branch → files changed on this branch. Never abort if unresolvable — use the best available list. Host-adapt `<default>` (`main`/`master`).
  - Also resolve spec inputs: `BT-<parentPadded>` = the slice's Parent (`gh issue view <n> --json parent`; local backend: its `BACKLOG_MAP.md` row); pass `docs/prds/BT-<parentPadded>-*.md`, `docs/design/BT-<parentPadded>-interface.md` and the `## Deviations` of `.tmp/3d-plan-BT-<padded>.md` when they exist (no PRD/design doc at that path (standalone slice) → the issue only).
- **Context Isolation Rule:**
  - **Local:** Run Phase 2/3 natively only if this session was read-only on production code (no edits under slice path, no `/3d-implement-issue`; `/0a` memory/branch writes do not taint). If native, run both Spec and Standards audits.
  - **Isolate:** Otherwise run the two audits as **two separate, independent subagents in two isolated contexts** — never one agent doing both (each guardrail is that agent's entire contract; inputs and scopes differ):
    1. **Strict Business-Logic Auditor** (independent subagent). Input: the lean packet per `.agents/skills/4a-verify-and-ship/references/audit-inputs.md` (the slice issue's `### Acceptance Criteria` (primary, `gh issue view <n>`); the resolved PRD §6/§7/§8, design doc and 3d `## Deviations`; the scoped diff and named tests inline; full files only on demand); `.agents/skills/4a-verify-and-ship/references/confidence-scale.md`. Guardrail: "Audit + format the AC↔test table only; no edits, commits or pushes; return to main for Phase 4. Judge recorded deviations on merit." Output: AC↔test gaps ≥ 80 confidence (withhold implementation-only divergences < 70), plus a `Watch` list: findings scored 60-79, one line each (what, where, why unsure). Watch items never block.
    2. **Standards Auditor** (a second, separate subagent — do not fold into the first; dispatch it with `auditor_model: small` per `references/auditor-model-tiers.md` and record the tier as `std_tier`): Input: changed-file list + the scoped diff command `git diff <base>...HEAD -- <changed paths>` (pass the command, not pasted diff), coding standards, `.agents/skills/4a-verify-and-ship/references/code-smell-baseline.md`, and the `info:` lines `floor_guard.py` printed in step 0 (it skips and drops per that reference). Guardrail: "Report findings only; no edits, commits, or pushes; return to main; scan slice diff only." Output: findings list (File · Smell/Rule · Hard breach | Judgment · One-line fix), plus `Dismissed` (cap 3): findings it considered and rejected, each `File · Rule · reason ≤ 8 words`.

### Clean Exit Rule
If no spec issues (confidence ≥ 80) and no standards violations → proceed directly to Phase 5: Isolated Ship Gate. Output: `[PASS] Slice verified.` plus any `Dismissed` lines and any Watch items (§3 below); Watch items alone never stop the ship.

## Phase 3: Output
If issues exist, output in three separate sections:

### 1. Spec / Business-Logic (Ship-Blocking)
Map the slice's Acceptance Criteria (AC), plus the PRD/design requirements the auditor checked, directly to tests:

| Slice AC / Requirement | Test Target | Status | Confidence | Gap / Security Risk |
|---|---|---:|---:|---|
| [AC description] | [test_name] or [NONE] | FAIL | [80-100] | [Description of missing test coverage or gap] |

*(Optional Footnote)* If sub-threshold findings (40-59) were withheld, append: "Note: <N> sub-threshold findings were withheld."

### 2. Standards / Code Smells (Advisory)
Advisory findings (does not block shipping):

| File | Smell / Rule | Hard breach \| Judgment call | One-line fix |
|---|---|---|---|
| [filename] | [Rule ID] | [Hard breach or Judgment] | [Proposed fix] |

`Dismissed` (omit when empty): one line each; HITL shows them at the ship halt; 3z's `audit-only` return carries them (listed, plus counts).

### 3. Watch (Non-blocking)
The Spec auditor's 60-79 findings (omit when empty), one line each. Never a halt or a retry. The lead settles an item only on evidence from at most one targeted grep or read (a test or text that covers it → drop it); no further subagent. HITL shows what remains at the ship halt; 3z's `audit-only` return carries the items and the count. Record the count as `watch` per `references/pr-body-and-ship.md` § Audit findings.

## Phase 4: Handoff
Halt. Await human approval. If approved, or if user response to gap report authorizes shipping, proceed to Phase 5: Isolated Ship Gate (clean re-audit without second halt, scoped by the delta rule of `.agents/skills/4a-verify-and-ship/references/audit-inputs.md`). If gaps remain unresolved and unauthorized → return to TDD loop (no PR).

## Phase 5: Isolated Ship Gate

> **Named gate — `ship-only`:** this phase alone. Branch-safety + design-drift gate, push, open/update PR, status flip. Never reached by an `audit-only` run. `ship-only` skips Phases 1–2, so it runs the Phase 1 step 0 clean-tree guard and floor guard first.
1. **Branch isolation:** Verify branch is NOT `main`/`master` AND `branch_ok` from `python .agents/scripts/pr_body.py unit --slice BT-<padded> --milestone <Milestone> --parent <Parent> --parent-milestone <parent's Milestone> --branch "$(git branch --show-current)"` (inputs as 3d step 1) is true. Else halt `[BRANCH-UNIT]`; HITL may confirm shipping on that branch (adoption: `features:` then lists the parent).
2. **CSS check (UI surfaces only):** Skip when the feature has no UI surface — no `theme.tokens.css` in the app and no UI block in the interface design doc (`2b` Path C). State the skip. A backend-only project has no tokens to synchronize and must not be blocked on them. Otherwise run the design validator:
   ```bash
   python .agents/scripts/design/design_theme.py --design .memory/DESIGN.md --check <app-css-dir>/theme.tokens.css
   ```
   If command exits non-zero, **halt and fail ship**. Synchronize CSS tokens first.
3. Halt for user confirmation to ship (unless pre-authorized).
4. **Release bump + push:** if `scripts/release.py` exists and the branch changes shipped content (`src/` artifacts), run `python scripts/release.py -y` at every ship and commit the result as `release: prepare v<x>` only if its output changed — CI's bump-guard fails the PR otherwise. The clean-tree guard guarantees no uncommitted slice code; commit nothing here except the release bump — never sweep unrelated `.memory/`/`docs/` drift in. (4a never creates the first commit; 3d owns commits.) Push the branch.
5. **PR (one per ship unit):** none exists for the branch → `gh pr create` (if connected) as **draft** (`--draft`): the unit PR accumulates slices (of several epics for a release), un-mergeable until every epic in it completes (step 8 flips it ready). **Exception:** standalone issue → non-draft. PR exists → update its body; no duplicate PR per slice, no draft-state change here. Title: `<type>(vX.Y): release vX.Y` for a release unit, else `<type>(BT-<parentPadded>): <epic or issue name>`; never retitled. Body format, build flags, suite record, risk label and read-back: `references/pr-body-and-ship.md`.
   - **Suite:** `python .agents/scripts/pr_body.py suite`; none → run the suite once and record it per the reference.
   - **Build:** save PR's current body to `.tmp/4a-prior-body.md` (`gh pr view <n> --json body -q .body`; none yet → omit the flag), then run `python .agents/scripts/pr_body.py build --slice BT-<padded> --summary "<one line>" --verdict <PASS|WAIVED|SKIP> --audit-rounds <n> [--audit-file .tmp/4a-audit-BT-<padded>.json] --prior-body-file .tmp/4a-prior-body.md --parent BT-<parent> [--deviation "<deviation line>"]... [--post-merge "noticed: <line>"]... [--manual-qa] --out .tmp/4a-pr-body-BT-<padded>.md`. Flags per `references/pr-body-and-ship.md`.
   - **Body file:** pass `--body-file .tmp/4a-pr-body-BT-<padded>.md` on `gh pr create` / `gh pr edit`; once the call succeeds, `rm -f .tmp/4a-pr-body-BT-<padded>.md .tmp/4a-prior-body.md`. Never commit them.
   - **Risk label, then closing-link read-back:** per the reference, after the call.
6. **PR-link comment (bi-directional trace):** `gh issue comment <n> --body "Shipped in PR #<pr> — <pr-url>"`, where `<pr-url>` is the full `https://github.com/<owner>/<repo>/pull/<pr>` link. The terminal gate (step 9) accepts only a comment containing that `/pull/` URL — a bare `#<pr>` fails it — so posting exactly this is what makes the check pass. Its own step on purpose: folded into the status write below, it is the clause that drops. Skip the post when the issue already carries a comment with that URL (a `ship-only` re-run after a CI fix).
7. **Ship-status:** move the slice to its shipped status (code complete + verified + pushed) with the verbs of `references/tracker-verbs.md`:
   - **Child slice:** `set_status` `done`, then `close` (`gh issue close <n> --reason completed`; skip if already closed). Never `not planned`: the board Action maps only completed closes to done.
   - **Standalone issue:** `set_status` `in review`; the merge closes it and sets `done`.
   - **Clear blockers (single writer for this edge):** this slice is now shipped (`done`; standalone `in review`). github: step 9's combined call decides and clears them. Local backend: run `python .agents/scripts/reconcile.py --edges dependents --ids BT-<slice>`. For each `[CLEAR]` line remove the bare ID from that dependent's `Blocked by` in `.memory/BACKLOG_MAP.md`. Then run its `cmd:` (`clear_blocker`, `removeBlockedBy` per `references/github-issue-relations.md`) so the map stays a faithful mirror. Leave every `[KEEP]` edge (it clears at merge via 0b). Refresh `generated.at` (and `generated.by`) on any `.memory/` document this step mutates.
   - **Standalone issue (no parent):** same CI gate here (rules: `references/ci-gate.md` §2-§4): `python .agents/scripts/ci_gate.py status --pr <n> --sha "$(git rev-parse HEAD)" --attempt 1 [--expect-checks]`; tool timeout `600000` or `--wait` below host limit. `[CI-RED]` leaves PR open, non-draft; halt text says so.
8. **Epic Check** (skip for a standalone issue): E = `features:` of the body built in step 5. Epic P in E is **complete** when every sibling sub-issue under it is `status:in review` or `status:done` (Spikes close as `done` without a PR; `gh issue view <P> --json subIssues`). N = complete epics still at `status:in progress`; R = every epic in E complete. Run when N ≠ ∅ or R (a `ship-only` re-run after a CI fix has N ≠ ∅, R true; it skips the audits). In order:
   - **Feature Acceptance Audit** for each P in N (once per epic, never per slice; skip on a `ship-only` re-run after a CI fix; an `audit-only` run never reaches this step). Spec: `references/feature-acceptance-audit.md`. Gaps ≥ 80 halt the ship: PR stays draft, that epic stays `in progress`.
   - If R, **CI gate** (once per PR, after the audits, before the body rebuild, never per intermediate slice; spec `references/ci-gate.md`): `python .agents/scripts/ci_gate.py status --pr <n> --sha "$(git rev-parse HEAD)" --attempt 1 [--expect-checks]` (`--attempt 2` on a `ship-only` re-run after a CI fix; dispatch passes it); tool timeout `600000` or `--wait` below host limit (`ci-gate.md` §2). By result:
     - `green` | `pending` | `none` → continue (`pending`: `ci:pending` in ship line). `conflict` → report only.
     - `red`+`small` → fix per `ci-gate.md` §3, re-run once `--attempt 2`. Under 3z (dispatch carries `verdict`/`audit_rounds`): return `[CI-FIX]` + `log_tail`, 4a does not commit.
     - `red`+`big`, or exit 2 from `status`/`cap` → HALT `[CI-RED] <check>` (`could not check` on exit 2): slice keeps its shipped status, PR stays draft, each epic in N stays `in progress`, step 9 for the slice and its dependents (epics not flipped), `/3b-create-issue` with `log_tail` as brief (`ci-gate.md` §4).
   - If R, rebuild the body: re-save the PR's current body to `.tmp/4a-prior-body.md` (step 5 deleted it; `gh pr view <n> --json body -q .body`), then run `pr_body.py build … --prior-body-file .tmp/4a-prior-body.md --close BT-<P>` for every P in E (adds `Closes #<P>.`; without the prior body earlier slices become `PENDING` and lose their `Closes` lines). `gh pr edit --body-file` it, `rm -f` both scratch files as in step 5, re-run the `closingIssuesReferences` read-back for **each** P in E, then `gh pr ready <n>` (if connected; no-op if opened non-draft) and state `"All slices for <unit> shipped! PR #<n> ready to merge."`.
   - If not R: state `"BT-<P> complete; PR #<n> stays draft (waiting on BT-<Q>)"` per P in N; no CI gate, no `Closes` rebuild.
   - `set_status` each P in N `in review`. Its dependents' edges clear in step 9. Local backend: run `python .agents/scripts/reconcile.py --edges dependents --ids <each P in N>` and clear its `[CLEAR]` edges as in step 7 (map + `cmd:`); leave `[KEEP]`.
   - Each epic moves to `status:done` on PR **merge** (`Closes #<P>`), not here; its slices are already `done`.
9. **Terminal sync gate** (`references/terminal-sync-invariant.md`; PR-link checked on the slice only):
   - One combined call over the slice and each epic flipped in step 8; the intended end state is inline and the dependents' edges come from the same fetch (standalone issue: `status=in review`): `python .agents/scripts/reconcile.py --ids BT-<slice>[,BT-<epic flipped>] --pr-id BT-<slice> --expect "BT-<slice>:status=done[;BT-<epic>:status=in review]" --with-edges dependents`. For each `[CLEAR]` line run its `cmd:` (`clear_blocker`), then re-run `python .agents/scripts/reconcile.py --edges dependents --ids <the same ids>` once and require no `[CLEAR]` left; `[KEEP]` edges clear at merge via 0b.
   - Non-zero → re-apply the missing write and re-run, **at most 3 attempts**; still non-zero, or `[GH-UNAVAILABLE]` (exit 3) → halt and surface the drift. Never loop unbounded; do not emit the ship line until it passes.
   - **Draft rule** (skip for a standalone issue or `local-only`): if any sibling slice of an epic in E (the `features:` list; github: `gh issue view <P> --json subIssues`; local backend: the BACKLOG rows with `Parent` ∈ E) is not `in review`/`done`, the PR must be draft (`gh pr view <n> --json isDraft`). Not draft → heal once with `gh pr ready <n> --undo` and re-check; still not draft → halt `[DRAFT-RULE]`.
10. **Cleanup:** `rm -f .tmp/3d-plan-BT-<padded>.md .tmp/4a-audit-BT-<padded>.json` (last step). Keep `.tmp/3d-suite-BT-<padded>.json`.
11. Output: `[SHIPPED] PR #<n> open for BT-<padded>.` (append `risk:one-way` when the label was applied, `ci:pending` when the CI check was still running). Never merge.