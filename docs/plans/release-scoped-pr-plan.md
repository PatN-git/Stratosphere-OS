# Plan: release-scoped PR (epic slice 2, D1)

Draft by Sonnet 5.5; reviewed and revised by Opus 5.5 on 2026-10-20. Where this file differs from the **Consistency rulings** in `lifecycle-status-pr-scope-epic.md`, the epic plan wins; that includes the final version table.

Planned against: HEAD b01d30d + slice 1 (`docs/plans/slice-close-at-ship-plan.md`) landed. Line numbers are current-source numbers; slice 1 rewrites lines in place (no insert/delete in 3d/3z/4a), so they hold. Nothing here is implemented.

## 1. Summary + D1 resolution algorithm

One branch + one PR per **ship unit**. A PR can carry slices of several epics and sprints of one release. Tooling today assumes one epic per PR (AGENTS.md §4 L32-38; 3d L20; 4a L79/L88-102; `pr_body.py` single `feature:`/`--close-parent`).

Key design move: the branch scheme stays `<type>/<unit>-<slug>`. Today `<unit>` is always `BT-<parentPadded>`; it becomes `vX.Y` for release units. Per-epic branches already in flight are therefore unchanged (they are `<unit>=BT-…`), and no script or workflow parses a branch name today (grep over `src/` found only prose: AGENTS.md §4, 3d L20, 4a L71/L79, 3z L21/L56/L84; `ci_gate.py`, `test_gate.py`, 0a, jules-dispatch build/parse none). The one deterministic implementation lives in `pr_body.py unit` (pure, no git/gh), so 3d, 4a, 3z and slice 3 (D3 "same ship unit") share it instead of restating the rule.

**Resolution (`pr_body.py unit`).** Revised in review; this is the single D1 definition, and slice 3 imports it.
- **Pure function:** `resolve_unit(id, milestone, parent, parent_milestone=None, epic=False)`.
- **CLI inputs:** id `BT-n` (`--slice`), milestone M, parent P, `--parent-milestone` PM (the parent epic's milestone), `--epic` (the id is a `tier:epic`), optional type T, slug S, and the current `branch`.

Rules:
1. **Validate.** M and PM ∈ {``, `-`, `—`} mean none. Otherwise each must match `^v(\d+)\.(\d+)\.(\d+)$` (any Z, including `.0`); anything else exits 2 with `[SHIP-UNIT-ERROR]`. P must be none or `^BT-\d+$`, else exit 2.
2. **`--epic`** (an epic row, used by slice 3 for epic→epic edges):
   - M valid → `kind=release`, `unit=v<X>.<Y>`;
   - otherwise → `kind=epic`, `unit=BT-<n:03d>`. This equals its children's epic unit.
3. **P none** → `kind=issue`, `unit=BT-<n:03d>`, `globs=[*/BT-<n:03d>-*]`.
   - A standalone issue ships on its own branch even when it has a milestone. 3b L104 gives standalone slices `v1.0.0`, and they must not merge into one release PR. Q1 is resolved: confirmed.
4. **P set, and M valid or (M none and PM valid)** → `kind=release`, `unit=v<X>.<Y>` (ints, no leading zeros) from M, else from PM, with `globs=[*/BT-<p:03d>-*, */v<X>.<Y>-*]`.
   - The legacy own-epic glob comes first, so a mid-flight per-epic branch keeps its epic (backward compat).
   - A milestone-less child **inherits its epic's release**. This happens when 3a gave the epic `vX.Y.0` before 3c sprinted the slices, and inheriting keeps one epic in one PR (this shrinks R4).
5. **P set, M and PM both none** → `kind=epic`, `unit=BT-<p:03d>`, `globs=[*/BT-<p:03d>-*]` (today's behavior).
5. With `--slug`: `branch = <T>/<unit>-<slugify(S)>` (lower-case, non-`[a-z0-9]` → `-`, collapsed, ≤ 40 chars; T default `feat`, must be `^[a-z]+$`). With `--branch X`: `branch_ok` = X fnmatches any glob (the trailing `-` in `v1.2-*` keeps `v1.20-…` from matching).
6. Output: one JSON object `{unit, kind, globs, branch?, branch_ok?}`. "Same ship unit" ⇔ equal `unit` strings.
7. PR title: release → `<T>(vX.Y): release vX.Y`; epic/issue → `<T>(BT-<padded>): <epic or issue name>` (today's). Set at create, never retitled (the body's `features:` is the roster).

`<T>` = the PARENT epic's `type:` label (the slice's own if standalone). `<slug>` for creating a release branch = the creating slice's parent epic name; later epics find the branch by glob, never by slug.

## 2. File-by-file changes

### AGENTS.md §4 — edit **both** `src/constitution/AGENTS.md` (L31-42) and root `AGENTS.md` (hand-kept copy; identical §4)
Final text (replace L32, L34, L35, L37, L38; L33/36/39-41 unchanged):
- **Granularity:** one branch + one PR per SHIP UNIT: the slice's release `vX.Y` (milestone `vX.Y.Z`), else its parent epic, else itself (standalone). Every slice of the unit commits onto that branch; its one PR accumulates them (several epics and sprints per release). Resolve with `pr_body.py unit`.
- **Branch name:** `<type>/<unit>-<slug>`; `<unit>` = `vX.Y` or `BT-<padded>` (epic or standalone issue); `<type>` from the PARENT epic's `type:` label (the slice's if standalone). An in-flight `<type>/BT-<parentPadded>-<slug>` branch stays valid.
- **Commit message:** `<type>(BT-<slicePadded>): <summary>`, `<type>` from the SLICE's `type:` label. (drops the "(Branch is keyed to the feature…)" parenthetical: sediment.)
- **Who does what:** `single feature PR` → `single unit PR`. **Merge:** `feature PR` → `unit PR`.
- **Char budget (the binding constraint):** `tests/framework/test_host_hygiene.py` L55 `CONSTITUTION_BUDGET = 9200` chars, enforced on BOTH copies. Measured: root `AGENTS.md` = 9186 (14 headroom), src = 8987. The edits above add +78. To stay under: delete from the Documentation-artifact exception (L42, both copies) the author rationale ` — the artifact must be readable by whoever picks the work up next, not stranded in one working copy` (100 chars; playbook §4 "rationale = no-op for the executor"). Result: root 9164, src 8965. Do not touch §8 (`test_constitution_section_8_identical_across_copies`). Do not cut any "never merge"/push invariant (protected class).
- Uncertain: none; counts measured with `len()` on the actual files.

### `src/workflows/3d-implement-issue.md` — L20 (step 1 Branch Isolation)
Current: resolve parent BT, branch `<type>/BT-<parentPadded>-<slug>`, parent ambiguous → prompt, AFK → slice branch. New step 1:
> 1. **Branch Isolation:** Resolve the ship unit: `python .agents/scripts/pr_body.py unit --slice BT-<padded> --milestone <Milestone> --parent <Parent> --parent-milestone <parent's Milestone> --type <type> --slug "<parent epic name>"` (Milestone and Parent: BACKLOG row, else `gh issue view <n> --json milestone,parent`; parent's Milestone: the parent's BACKLOG row, else `gh issue view <parent> --json milestone`; `—` for none; `<type>` = parent's `type:` label, the slice's if standalone; slice title as slug if standalone) → `{unit, globs, branch}`. Search local + `origin/` branches (`git for-each-ref --format='%(refname:short)' refs/heads refs/remotes/origin`) for the first glob, in order, with an active match (no merged PR: `gh pr list --head <b> --state merged --json number`; no `gh` → not in `git branch --no-merged <default>`). Found → checkout/pull. None → create `branch` from default (name taken by a merged branch → append `-2`). Several active matches for one glob, or Parent/Milestone unreadable/ambiguous, or the checked-out branch is an unmerged feature branch outside `globs` (adoption of a legacy epic branch by a later epic, e.g. cleantech #244) → prompt; AFK: first match / own-issue unit, never adopt. Never work on `main`. Update `.memory/STATUS.md` … (rest unchanged).
Slice 1 edits L21, not L20: no overlap. Uncertain: the `-2` rule and the active-branch probe are the least-verified prose; tune at implementation.

### `src/workflows/4a-verify-and-ship.md` — combined final wording (slice 1 + this slice)
- **L15 hand-off** (slice 1 sets child slice `done`+closed, standalone `in review`, epic open until merge). Final: "Final gate before pushing and opening or updating the PR. The unit PR stays draft until every slice of every epic in it is `status:in review|done` (Spikes closed as `done` count). A standalone issue opens non-draft. On ship a child slice is `done` and closed (the progress bar counts closed issues), a standalone issue is `in review` and merge closes it. Each epic goes `in review` once its own slices are all shipped; merge closes every epic the PR completed."
- **L71 step 1** (mine only): "Verify branch is NOT `main`/`master` AND `branch_ok` from `pr_body.py unit --slice BT-<padded> --milestone <Milestone> --parent <Parent> --parent-milestone <parent's Milestone> --branch "$(git branch --show-current)"` (inputs as 3d step 1) is true. Else halt `[BRANCH-UNIT]`; HITL may confirm shipping on that branch (adoption: `features:` then lists the parent)."
- **L79 step 5** heading + prose (mine; the literal `5. **PR (one per feature branch):**` is the slicing anchor of `tests/workflows/test_workflow_script_crosschecks.py` L38: change it there in the same commit): "5. **PR (one per ship unit):** none exists for the branch → `gh pr create` (if connected) as **draft**: the unit PR accumulates slices (of several epics for a release), un-mergeable until every epic in it completes (step 8 flips it ready). **Exception:** standalone issue → non-draft. PR exists → update its body; no duplicate PR per slice, no draft-state change here. Title: `<type>(vX.Y): release vX.Y` for a release unit, else `<type>(BT-<padded>): <epic or issue name>`; never retitled."
- **L81 build command:** `--parent BT-<parent>` keeps its meaning (the shipped slice's parent; omit for standalone). No new flag here; the script accumulates `features:`.
- **L85 step 7 / L86:** slice 1's wording only (no change from this slice).
- **L88 step 8 Epic Check** — combined final: "8. **Epic Check** (skip for a standalone issue): E = `features:` of the body built in step 5. For each epic P in E (`gh issue view <P> --json subIssues`) P is **complete** when every sibling sub-issue is `status:in review` or `status:done` (Spikes close as `done` without a PR). N = complete epics still at `status:in progress`; R = every epic in E complete. Run when N ≠ ∅ or R (a `ship-only` CI re-run has N = ∅, R true). Order:
  - **Feature Acceptance Audit** for each P in N (skip on a `ship-only` re-run after a CI fix).
  - If R: **CI gate** (once per PR, after the audits, before the body rebuild; unchanged command and result handling; `[CI-RED]` leaves every P in N at `in progress`), rebuild the body (re-save prior body, then `pr_body.py build … --prior-body-file .tmp/4a-prior-body.md --close BT-<P>` for every P in E), `gh pr edit --body-file`, `rm -f` both scratch files, re-run the `closingIssuesReferences` read-back for **each** P, `gh pr ready <n>` (no-op when non-draft), state `"All slices for <unit> in review! PR #<n> ready to merge."`.
  - If not R: state `"BT-<P> complete; PR #<n> stays draft (waiting on BT-<Q>)"`; no CI gate, no `Closes` rebuild.
  - Move each P in N to `status:in review` (`gh issue edit <P> --remove-label "status:in progress" --add-label "status:in review"`), then clear `BT-<P>` from every dependent's `Blocked by` as in step 7 (map + `removeBlockedBy`). Keep this a single clause: slice 3 replaces it with `reconcile.py --edges dependents --ids <each P in N>`, clearing only the `[CLEAR]` edges.
  - Epics move to `done` on merge (`Closes #<P>`), slices are already `done` (slice 1)."
- **L99 Feature Acceptance Audit bullet:** "once per epic, when it becomes complete (never per slice)"; gaps ≥ 80 halt the ship: PR stays draft, that epic stays `in progress`.
- **L100 step 9 ids:** `…[,BT-<each epic flipped in Step 8>]` (was `BT-<parent> when Step 8 flipped the epic`); slice 1's coverage parenthetical stays.
- **L102 Draft rule:** "if any BACKLOG row with `Parent` ∈ E (the `features:` list) is not `in review`/`done`, the PR must be draft…" (rest unchanged; standalone/`local-only` skip).
- **L93 CI-RED text:** "epic stays `in progress`" → "each epic in N stays `in progress`".
- Keep verbatim (slice 1 constraint, shared): step 6 heading, `[...]` tokens, "single writer for this edge", step numbering.

### `src/workflows/3z-afk-loop.md`
- L21: "fully-passed feature branches" → "fully-passed unit branches".
- L40: "**Group** slices by ship unit (`pr_body.py unit` per slice: Milestone, Parent from the BACKLOG row; unit = its `unit` key); order by `(unit, dependency_order, slice_id)`. (rest of the sentence unchanged; slice 3 owns the satisfied-blocker predicate.)"
- L56: "creates/restores the feature branch" → "creates/restores the ship-unit branch"; add `"branch": ""` to the implementer JSON (= `git branch --show-current` after 3d's last commit) so Step 3A knows which branch to check out. No test pins this JSON (checked `tests/`). Slice 3 adds one clause to the same dispatch prompt (skip 3d's new blocker guard). Both edits are additive, so keep the JSON contract verbatim apart from the new `branch` key.
- L83-84 (Step 3A): "For each ship unit whose queued slices are all `VERIFIED`: 1. Branch checkout: `git checkout <branch from the slices' Step 2A JSON>`."
- L85-86 combined with slice 1: "…move the slice to its ship status (child `done` + closed; standalone `in review`)… The `ship-only` gate is single-slice: its Epic Check flips each epic `in review` when that epic's last slice is shipped and the PR ready when every epic in it is complete, so every VERIFIED slice must get its own Phase-5 pass."
- L91 (slice 1: "keeps its shipped status"), L93 "per feature" → "per unit PR", L96/L97 "feature" → "ship unit", L105 "per feature" → "per ship unit". Frontmatter `description` "fully-passed features" → "fully-passed ship units" (optional).
- Conservative rule kept: a unit with a `status:blocked` or `SKIP-DEP` slice stays local (a blocked `[UNCOVERED]` slice has unverified commits on the branch). See risk R3.

### `src/references/pr-body-and-ship.md` (L11-33)
- Body format: `feature: BT-<parentPadded>` → `features: [BT-<parentPadded>, …]` (one entry per epic in the PR); slice rows `{id: BT-<padded>, parent: BT-<parentPadded>, summary: …}` (`parent:` omitted when standalone).
- Build bullets: `--parent` = the shipped slice's parent (joins `features:`); `--close BT-<n>` repeatable = epic completed by this PR (adds `Closes #<n>.` after the slice lines); `--close-parent` stays as the single-epic alias (closes `--parent`). Commits scoped to any epic in `features:` are not slices.
- Read-back: confirm the slice issue **and each closed epic** are listed.

### `src/references/feature-acceptance-audit.md` — L2/L14: "once per feature" → "once per epic when it becomes complete (several may complete in one release PR)"; L11 "full feature branch" stays. Scope/Input unchanged (parent PRD of that epic).
### `src/references/ci-gate.md` — L2 "feature PR" ok; L16 "Run once: ship of the last sibling" → "once per PR, when it goes ready (every epic in it complete; standalone: after step 7)"; L45 (slice 1 touches L44) "Feature PR stays draft, epic stays `in progress`" → "Unit PR stays draft, each completing epic stays `in progress`".
### `src/references/terminal-sync-invariant.md` L20 — "plus the parent epic when it flipped it" → "plus each epic it flipped to `in review`".

### Confirmed unchanged (read)
- **0a** (L28 branch restore reads STATUS `Current Branch`, branch-name-agnostic; L31 epic promote). **0b** (L30 done-detection; slice 1 owns its edits; merge of a multi-epic PR auto-closes via `Closes #<epic>` and 0b already detects per epic). **3c** (assigns milestones only; stays inside a release by L25, so unit keys are stable across vX.Y.0 → sprint moves). **3b** (L104 milestone `vX.Y.0` = parent's, `—` when none, standalone `v1.0.0`: exactly D1's inputs). **3a**, **3x/jules-dispatch** (Jules names its own branch, CONTRACT.md L62-64; `--starting-branch main`), **ci_gate.py**, **test_gate.py** (`--suite BT-<n>` is per-slice, `pr_body suite` takes the newest file), **reconcile.py**, **BACKLOG_MAP.md**.

## 3. Script + tests

### `src/scripts/pr_body.py`
- Docstring (L1-27): usage for `unit`, `--close`, `features:`.
- Constants: `SLICE_RE` (L43) gets an optional `parent: (BT-\d+), ` group after `id`; add `MILESTONE_RE`, `NONE_TOKENS`.
- `parse_prior` (L112-131): returns `features` list: `features: [..]` (like `refs`, L128), else legacy `feature: BT-n` → `[BT-n]`. Prior rows w/o `parent:` inherit the legacy single feature, else `—`. Tuple grows to `(id, parent, summary, verdict, rounds)`.
- `epic_ids` (L278-290) → also expose each row's `Parent` from the same `reconcile.parse_backlog` call (new helper `backlog_parents()`); fails open to `{}` as today. A new PENDING row's parent = BACKLOG `Parent`, else `—`.
- `slice_rows` (L293-324): takes `features`; pop commits scoped to every feature epic except the shipped slice (L308-310 generalized); shipped row parent = `--parent` or `—`.
- `render_body` (L333-344): `features: [..]` replaces `feature:` (L336); `Closes` = slice lines (not PENDING/DROPPED) then `Closes #n.` for each closing epic, deduped with `union`; rows print `parent:` when known.
- `cmd_build` (L347-404): validate each `--close` with `PARENT_RE` (clean exit 2 naming `--close`, like `--epic` L351); `features = union(prior_features, [--parent], row parents)`; if empty (standalone, no prior) → `[slice]` (today's `feature: BT-slice`); closing set = `--close` ∪ (`--close-parent` → `--parent` or first prior feature or slice, today's rule L385). Drop the `--parent overrides prior feature` warning (L386-387): a different parent is now the normal multi-epic case.
- Parser (L407-432): `--close` append; `unit` subparser (`--slice --milestone --parent --type --slug --branch`); `main` (L435-439) dispatches `build|suite|unit`.
- New pure functions `resolve_unit(id, milestone, parent, parent_milestone=None, epic=False)` and `slugify(...)`. `cmd_unit` prints JSON; errors print `[SHIP-UNIT-ERROR] …` and exit 2. `resolve_unit` is the **only** D1 implementation: slice 3's `reconcile.py` imports it lazily, the same way `pr_body.py` already imports `reconcile` (L283-285). Keep it import-safe: no top-level side effects.
- Scaffold/verify registration: none needed (`pr_body.py` already in `scaffold.py` L628 and `tests/runners/verify_scripts.py` L297-298).

### Tests — `tests/scripts/test_pr_body.py`
Update existing: helper `slices()` regex (L75) to accept optional `parent:`; `field(body, "feature")` asserts (L83, L245) → `features`; replace `test_parent_conflicting_with_prior_feature_warns_and_overrides` (L238-249) with the union test below. Legacy prior bodies (L215, L241, L247, L556-557) stay as-is: they exercise the legacy parse path.
New cases (reuse `repo`, `build`, `commit`, `write_backlog`):
1. two epics: ship BT-11 (`--parent BT-10`), then BT-21 (`--parent BT-20`, prior=first) → `features: [BT-10, BT-20]`; rows `BT-11 parent BT-10`, `BT-21 parent BT-20`; both `Closes #11/#21`; no epic Closes.
2. `--close BT-10 --close BT-20` → after slice lines, in order, deduped; `--close-parent` alone still closes only `--parent`.
3. commits `fix(BT-10)` and `docs(BT-20)` (both epics in features) add no slice rows; shipped slice that equals an epic id is never filtered.
4. legacy prior block (`feature: BT-10`, rows without `parent:`) + new slice of epic BT-20 → `features: [BT-10, BT-20]`, legacy rows now carry `parent: BT-10`; rebuilding again with that output as prior is byte-identical (idempotent).
5. `--close` malformed (`oops`, `10`, `BT-`) → clean exit 2 mentioning `--close`.
6. PENDING row parent from `write_backlog` Parent column, else no `parent:`.
7. `unit` resolve table (CLI, JSON):
   - (`v1.2.5`,`BT-51`) → `v1.2`, release, globs `[*/BT-051-*, */v1.2-*]`;
   - (`v1.2.0`,`BT-51`) → `v1.2`;
   - (`—`,`BT-51`, PM `v1.3.0`) → `v1.3` (inherits the epic's release);
   - (`—`,`BT-51`, PM `—`) → `BT-051`, epic;
   - `--epic` with `v1.2.0` → `v1.2`; `--epic` with no milestone → `BT-<id>`, which equals its child's epic unit; (`v1.2.5`,none)→`BT-<slice>`/issue (standalone keeps own unit); (none,none)→issue; epics 51 (`v1.2.5`) and 204 (`v1.2.6`) → equal `unit`; `v1.2.9` vs `v1.20.1` → different units.
8. `unit` errors: milestone `1.2.3`, `v1.2`, `v1.2.x`; parent `51`, `BT-`; `--type Feat` → exit 2 `[SHIP-UNIT-ERROR]`, no traceback.
9. `--slug "Offline Sync: v2!"` + `--type fix` → `fix/v1.2-offline-sync-v2`; empty slug after slugify → error.
10. `branch_ok`: `feat/v1.2-x` true; legacy `feat/BT-051-x` true for a slice of epic 51 in release v1.2; `feat/BT-204-x` false for epic 51's slice; `feat/v1.20-x` false for v1.2; `main` false; `origin/feat/v1.2-x` true.
Crosschecks — `tests/workflows/test_workflow_script_crosschecks.py`: L38 anchor → `5. **PR (one per ship unit):**`; add one test: every `pr_body.py unit …` call in 3d, 4a, 3z uses only flags `build_parser()` accepts (mirror L89-96), and 4a's build call flags (incl. `--close`) stay accepted. No wording pins (D6).

## 4. Version bumps (once per file per PR, D5; baseline = fork point; take the HIGHER class of slice 1 and this slice, never stack). The authoritative cross-slice table is in the epic plan.
| File | Now | Final | Slice 1 | This slice |
|---|---|---|---|---|
| `src/constitution/AGENTS.md` + root `AGENTS.md` | 3.4.0 | 3.5.0 | — | minor (policy) |
| `src/workflows/3d-implement-issue.md` | 2.6.0 | 2.7.0 | minor | minor |
| `src/workflows/4a-verify-and-ship.md` | 1.5.0 | 1.6.0 | minor | minor |
| `src/workflows/3z-afk-loop.md` | 1.7.0 | 1.8.0 | patch | minor (so 1.7.1 → 1.8.0, replaced) |
| `src/references/pr-body-and-ship.md` | 1.0.3 | 1.1.0 | — | minor (format) |
| `src/references/terminal-sync-invariant.md` | 1.1.0 | 1.2.0 | minor | patch (absorbed) |
| `src/references/ci-gate.md` | 1.0.0 | 1.0.1 | patch | patch (absorbed) |
| `src/references/feature-acceptance-audit.md` | 1.1.0 | 1.1.1 | — | patch |
`src/scripts/pr_body.py` has no frontmatter version; the shipped-script change is covered by the single plugin release bump at 4a step 4 (`scripts/release.py -y`; `build/bump_guard.py` signal 2). Not touched here: 0a, 0b (slice 1 only), 3b, 3c. Build outputs (`dist/`, `.agents/`, `.claude/skills/`) regenerate via the build, never by hand.

## 5. Verification (in order)
1. `python -m pytest tests/scripts/test_pr_body.py tests/workflows/test_workflow_script_crosschecks.py tests/framework/test_host_hygiene.py -n 0`
2. Smoke: `python src/scripts/pr_body.py unit --slice BT-070 --milestone v1.2.5 --parent BT-051 --type feat --slug "Offline sync" --branch feat/BT-051-old` → `unit v1.2`, `branch feat/v1.2-offline-sync`, `branch_ok true`.
3. `python build/build.py && python build/validate.py .` (per-file bump check, markdown-only-test lint).
4. `bash scripts/check.sh` (CI mirror: build, validate, bump-guard, full pytest `-n 6`, `verify_scripts.py`, plan-html, install-harness L1, dist drift).
The char budget is checked in step 1 (`test_constitution_stays_within_its_char_budget`, both copies).

## 6. Acceptance criteria
1. `pr_body.py unit` resolves per D1 (table in §1) and its tests pass, incl. same-unit across epics/sprints and `v1.2` vs `v1.20`.
2. `pr_body.py build` with two parents emits `features: [..]`, per-slice `parent:`, `Closes` for every `--close` epic, and still parses and upgrades a legacy single-`feature:` body (idempotent rebuild).
3. 3d/4a/3z/AGENTS.md §4 name the ship unit and call `pr_body.py unit`; 4a flips each epic on its own completion, readies the PR only when every epic in `features:` is complete, closes all of them via `--close`; `bash scripts/check.sh` is green and both AGENTS.md copies ≤ 9200 chars.
4. A mid-flight `<type>/BT-<n>-…` branch still passes 4a step 1 for its own epic's slices; standalone and milestone-less slices resolve to today's branch and PR behavior.

## 7. Risks / open questions
- **Q1 (resolved in review):** a standalone issue with a milestone ships on its own branch (D1 literal, 3b L104).
- **R1 PR #244 adoption:** epic 204's first slice does not match legacy `feat/BT-051-…`, so 3d creates `feat/v1.2-…` unless the HITL prompt adopts the current branch. AFK never adopts. Manual follow-up already out of scope in the epic plan.
- **R2 Epic `in review` before PR ready:** with several epics an epic reaches `in review` while the PR is draft. Slice 3 (D3) must treat it as satisfied only inside the same unit; it can compare `pr_body.py unit` keys (equal `unit`).
- **R3 3z blast radius:** one blocked slice keeps the whole unit local; releases are bigger than epics. Left conservative (unverified commits would be pushed). Candidate relaxation: ship only VERIFIED slices of a unit.
- **R4 Epic spanning two units.** This is now rare: a milestone-less child inherits its epic's release. It remains only when slices carry milestones from *different* releases (a 3c re-plan across releases): `Closes #<epic>` lands in the PR that ships its last slice; if that PR merges before the other unit's PR, the epic closes early.
- **R5 Mid-release merge:** if the release PR merges before the later epics start, the next slice creates a new branch (new slug; `-2` on collision); the active-branch probe costs one `gh pr list` per candidate.
- **R6 `feature:` → `features:` rename:** only `pr_body.py` reads it (0b reads only `post_merge`); old consumer bodies are handled by the legacy parse path.
- **R7 PR title is constant** (`feat(vX.Y): release vX.Y`) and not refreshed as epics join; the body block is the roster.
- Unverified: `-2` collision rule, `gh pr list --head … --state merged` behavior for remote-deleted branches, and 3z's `branch` JSON field in a real AFK run.
