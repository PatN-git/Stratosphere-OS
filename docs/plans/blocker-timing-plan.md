# Plan: blocker timing (slice 3 of lifecycle-status-pr-scope epic)

Draft by Sonnet 5.5; reviewed and revised by Opus 5.5 on 2026-10-20. Where this file differs from the **Consistency rulings** in `lifecycle-status-pr-scope-epic.md`, the epic plan wins; that includes the final version table. Below, `rel:X.Y` / `epic:N` / `self:N` read as slice 2's keys `vX.Y` / `BT-<padded>`.

Draft 2026-10-20. Binding: epic D1-D6 (`docs/plans/lifecycle-status-pr-scope-epic.md`). Plans against the post-slice-1-and-2 state. Slice 1 (`slice-close-at-ship-plan.md`): child slices `done` + closed at ship. Slice 2 (`release-scoped-pr-plan.md`, BT-191): D1 ship unit. All line numbers are from the current tree; slices 1/2 shift some of them (re-anchor by text).

## 1. Summary + D3 predicate

**Decision: script entrypoint.** The predicate is load-bearing (4a clears, 3z/3d gate, reconcile heals) and has three consumers of two shapes, so it is a deterministic mode of `src/scripts/reconcile.py`, not prose. Workflows run one command and act on its printed verdicts. The script only *decides*; writes (map cell, `removeBlockedBy`) stay with the workflow step that owns them (single writer, per-action step).

Why reconcile.py (reuse-before-create): it already has `parse_backlog` (rows carry `status`, `milestone`, `parent`, `blocked_by`), `fetch_issue`/`_gh_json`, `_edge` (prints `removeBlockedBy` commands), `stale_blockers`, and is already scaffolded/mapped (`scaffold.py` L628 list), so no new script, no scaffold place(), no orphan-guard mapping.

**Shared D1 helper (resolved in review): import it, don't define it.** Slice 2 owns the single D1 implementation, `pr_body.resolve_unit(id, milestone, parent, parent_milestone=None, epic=False)`. Its unit keys are `vX.Y` or `BT-<padded>`, and equal strings mean the same ship unit. In `reconcile.py`, add a thin adapter that imports it lazily, following the `_nightly_state()` pattern at L48:
```
ship_unit(bt, rows):
  r = rows[bt]; p = rows.get(r.parent) if r.parent else None
  is_epic = 'tier:epic' in r.labels
  return pr_body.resolve_unit(bt, r.milestone, r.parent, p.milestone if p else None, epic=is_epic)['unit']
```
Semantics, decided in slice 2:
- a milestone-less child inherits its epic's release;
- a standalone issue is always its own unit, even with a milestone;
- an epic row with a milestone is in that release, otherwise it is `BT-<epic>`, which equals its children's unit.

Because it is an import, `ship_unit` is not re-tested here beyond a smoke case (test 1 below). The rule tests live in slice 2's `test_pr_body.py`.

### D3 predicate (pure; BACKLOG rows + one tri-state PR lookup)
```
SHIPPED = {'in review','done'}
effective_blockers(dep, rows) = (rows[dep].blocked_by | rows[parent(dep)].blocked_by) - {dep}   # parent row absent -> own only

edge_verdict(dep, blk, rows, merged_of) -> (OK|UNMET|UNKNOWN, 'same-unit'|'cross-unit', reason):
  b = rows.get(blk)                          # absent row -> UNKNOWN 'blocker row absent'
  shipped = b.status in SHIPPED
  if ship_unit(dep) == ship_unit(blk):       # D3 bullet 1
      return (OK if shipped else UNMET), 'same-unit', ...
  # cross-unit: code must be on the default branch (D3 bullet 2)
  if not b.parent:                           # epic or standalone: merged <=> closed <=> row done
      return (OK if b.status == 'done' else UNMET), 'cross-unit', ...   # 'in review' = PR still open
  if not shipped: return UNMET, 'cross-unit', ...
  m = merged_of(blk)                         # 'merged' | 'open' | 'none' | None(unknown)
  'merged' -> OK ; 'none' -> OK 'no PR, no code (Spike/manual close)' ; 'open' -> UNMET ; None -> UNKNOWN
```
`merged_of(bt)` (`pr_merge_state`, only for cross-unit child-slice blockers, cached per run): `gh issue view <n> --json comments`, take the **last** comment whose body has `/pull/<k>` (4a step 6 text, L84; a re-shipped slice has the newest PR last), then `gh pr view <k> --json state -q .state`. `MERGED`->`merged`; `OPEN`/`CLOSED`->`open` (CLOSED unmerged = not on default); no `/pull/` comment->`none`; any gh failure or no gh -> `None`. Cost: 2 gh calls per cross-unit child blocker only; same-unit and epic/standalone edges need zero calls.

Justification for `none` => OK: 4a step 6 always posts the PR comment before step 7 closes a slice and the step-9 gate demands it, so a `done` child with no PR comment is a Spike or manual close with no code to merge.

**Offline / local-only:** `merged_of` returns None, so cross-unit child-slice edges are UNKNOWN. Every other edge is decidable from the map alone. Consumers treat UNKNOWN as unmet (fail closed; the user may override in HITL), except reconcile/4a/0b which treat UNKNOWN as KEEP (never clear/flag what cannot be verified).

### CLI (new `--edges` mode; uses existing `--ids`/`--all-open` scope flags)
```
reconcile.py --edges blockers   --ids BT-207[,...]   # dependent side: effective blockers (own + parent epic's) of each id
reconcile.py --edges dependents --ids BT-070[,...]   # blocker side: each STORED edge `Blocked by` that names the id
reconcile.py --edges dependents --all-open           # sweep: every stored edge on every open row (0b)
```
Output, one line per edge (`<scope>` = `same-unit|cross-unit`, stable tokens consumers key on):
- blockers mode: `[BLOCKER-OK|BLOCKER-UNMET|BLOCKER-UNKNOWN BT-207 <- BT-070] <scope>: <reason>`; exit 0 only if every edge is OK, else 1. An id with no effective blockers prints `[BLOCKERS-NONE BT-207]`, exit 0.
- dependents mode: `[CLEAR BT-207 <- BT-070] <scope>: <reason>` then one indented `cmd:` line with the `removeBlockedBy` command from the existing `_edge` helper; `[KEEP BT-301 <- BT-070] <scope>: <reason>` (UNMET and UNKNOWN). Exit 0 always (it is a decision list), 1 only if a named id is absent from the map.
- `--edges` with `--heal`/`--summary`/`--pr-id`/`--fields` -> `ap.error`. Never writes anything (same contract as the script header).

Evidence case (fixture mirrors cleantech_jobs, read via gh: #207 `v1.2.6` parent #204 and #70 `v1.2.5` parent #51, both `in review`, both "Shipped in PR #244", epics at `v1.2.0`): `ship_unit` both `rel:1.2` -> `[BLOCKER-OK BT-207 <- BT-070] same-unit` and `--edges dependents --ids BT-070` -> `[CLEAR BT-207 <- BT-070]`. A `v1.3.1` slice blocked by BT-070 -> `cross-unit`, PR OPEN -> `[KEEP]`/`[BLOCKER-UNMET]`; MERGED -> CLEAR/OK.

### `[NEW-DEP]` recording: keep slice-level, do NOT move to epic->epic
Epic->epic would simplify the clear (epic closed at merge, no PR-comment lookup), but it over-blocks: every slice of the dependent epic would wait for the prerequisite epic, though one slice needs one prerequisite slice. 3c only sees leaf slices, and 3a already records epic->epic edges where an epic-level dependency is real. The inherited parent-epic edge (D3) already gives the coarse gate where it was recorded. So: 3a/3c recording text unchanged (3a L49/L72 untouched). 3c Phase 2 still *reads* effective blockers.

## 2. File-by-file changes (src/ only)

| File | Location (read) | Current gist | New gist |
|---|---|---|---|
| `src/scripts/reconcile.py` | L57 `STALE_STATUSES`; L110-118 `stale_blockers`; L398 heal skip; L427-475 `main`; L16-35 docstring | stale = open row blocked by a row in `in review`/`done` (BACKLOG only) | Replace `STALE_STATUSES` with `SHIPPED`; add `ship_unit`, `effective_blockers`, `edge_verdict`, `pr_merge_state`, `edges_cmd`; `--edges` flag. **`stale_blockers(rows, merged_of=<unknown>)` flags an edge iff `edge_verdict == OK`** (never a KEEP edge). **Heal skip (L398) uses the same verdict** (`stale = {b ... if edge_verdict(bt, b, rows, merged_of)[0]=='OK'}`), so a legitimately kept cross-unit edge that GitHub still has is real drift and heals from gh, not skipped. In `main`, compute `online = gh_available()` once before the `emit` list (L482), pass `merged_of = pr_merge_state` (cached) when online, else the unknown stub. Docstring: usage line + one line on `--edges`. |
| `src/workflows/4a-verify-and-ship.md` | L85-86 step 7 "Clear blockers"; L97 step 8 epic clear; L100 step 9 ids | clears dependents' `Blocked by` of an `in review` slice unconditionally; same for the epic at `in review` | **Step 7 sub-bullet:** run `python .agents/scripts/reconcile.py --edges dependents --ids BT-<slice>`; for each `[CLEAR]` line remove the bare ID from that dependent's `Blocked by` (map) and run the `cmd:` `removeBlockedBy`; **leave every `[KEEP]` edge** (it clears at merge, 0b). Keep "single writer for this edge". Slice 1 changes the lead sentence ("now `in review`" -> "now shipped"); fold both. **Step 8 (L97):** same with `--ids BT-<epic>` for each epic flipped (slice 2 may flip several; loop its list), dropping the unconditional clear. **Step 9 (L100):** pass only dependents with a `[CLEAR]` line (kept edges need no pass; map and GitHub still agree). Keep step 6 heading, all `[...]` tokens. |
| `src/workflows/3d-implement-issue.md` | L19 Phase 0 step 0 (Spike guard), L21 step 2 | Spike guard only; no blocker check | **New guard in step 0, after the Spike guard, before any side effect** (no renumbering; no other step cites step 0, confirmed by grep): "Blocker guard: run `python .agents/scripts/reconcile.py --edges blockers --ids BT-<n>`. Any `[BLOCKER-UNMET]`/`[BLOCKER-UNKNOWN]` -> HALT `[BLOCKED-BY] BT-<n> waits on BT-<b> (<same-unit or cross-unit>: <reason>)`. HITL: the user may override in chat, then continue (log the override in the Phase 0.5 plan). Skip when dispatched by 3z (its Step 2A frontier check ran it) and for a CI-fix dispatch." Rework of a shipped slice also skips (blockers shipped already). |
| `src/workflows/3z-afk-loop.md` | L40 step 3 group rule; L50 Step 2A.0 frontier; L107 final report | satisfied = blocker already `in review`/`done`; own `Blocked by` only | **L40:** order by effective blockers; satisfaction comes from the script, not status words. **L50 frontier:** run `reconcile.py --edges blockers --ids BT-<padded>`. Every `[BLOCKER-OK]`, or a `[BLOCKER-UNMET] same-unit` blocker that is `VERIFIED`/`VERIFIED-LOCAL` in this run (same branch, code present), passes. Any `cross-unit` unmet/unknown, or a same-unit blocker not VERIFIED, -> `[SKIP-DEP]` (existing text). Cross-unit is never waived by an in-run VERIFIED. **L56 dispatch prompt:** add "Blocker guard already satisfied by the orchestrator frontier check; skip it" (so the new 3d guard does not trip on same-unit VERIFIED-not-yet-shipped blockers). **L107:** "re-run /3z after BT-<blocker> reaches in review" -> "ships (same-unit) or merges (cross-unit)". Uncertain: exact L56 wording must keep the JSON contract verbatim (protected). |
| `src/workflows/3c-sprint-planning.md` | L29-32 Phase 2 step 1; L74 step 3 of Phase 5 | "blocker already `in review`/`done` counts as satisfied ... treat any stale entry as satisfied"; `[BLOCKED]` if prereqs not `done` | Run `reconcile.py --edges blockers --ids <candidate slices>` once; `[BLOCKER-OK]` = not blocking; UNMET/UNKNOWN -> `[BLOCKED]` (or `[blocked-but-sequenced-in-sprint]` when the blocker is in the current sprint, as today). Candidates' effective blockers include the parent epic's. Delete "treat any stale entry as satisfied" (a present edge can now be legitimately unmet). **L74:** "blocker **clearing** stays with 4a (at `in review`) / 0b / merge" -> "with 4a (same-unit edges, at ship) / 0b (at merge)". `[NEW-DEP]` recording unchanged. |
| `src/workflows/0b-stop-session.md` | L26-28 Done detection (slice 1 also rewrites L26-31) | "for each issue closed/merged this session: ... clear its bare ID from every dependent's `Blocked by` (safety net for the 4a in-review clearing)" | Clearing no longer hangs on "closed/merged this session" (post-slice-1 child slices close at ship, so closure no longer signals merge). New text: after marking merged epics/standalones `done`, run `python .agents/scripts/reconcile.py --edges dependents --all-open` **before deleting any row**; clear every `[CLEAR]` edge (map + `cmd:` `removeBlockedBy`). This is the primary clearer for cross-unit edges; 4a only clears same-unit ones. L28 `--fields blocked_by` gate over the cleared dependents unchanged. Needs gh; offline it prints UNKNOWN->KEEP, say so in the handoff `Blockers` line. |
| `src/references/terminal-sync-invariant.md` | L24 Heal; L28-32 Boundaries | "A stale blocker is healed on both sides" | One bullet in Boundaries: a blocker edge is stale only when `reconcile.py --edges` says CLEAR; a `[KEEP]` edge is never removed, and a map missing a KEEP edge that GitHub has is `blocked_by` drift (heal from gh). Heal sentence keeps "stale = a CLEAR edge still present". |
| `src/memory-templates/BACKLOG_MAP.md` | L25 inside block `backlog-rules` (L18-35) | "A blocker is cleared from `Blocked by` once it reaches `status:in review` or `status:done`." | "An edge is cleared when the dependent's branch has the blocker's code: same ship unit (`vX.Y`, else parent epic) -> blocker shipped (`in review`/`done`); otherwise -> blocker merged. `reconcile.py --edges` decides. A slice's effective blockers include its parent epic's." Bump block `backlog-rules` `v=` and the file. |
| `src/references/ci-gate.md` | L44 | "dependents cleared in step 7" | **No change** (still true; slice 1 owns L44). |
| `src/experimental/jules-dispatch/dispatch.py` | L88-102 `select_eligible`, L105-130 `_sprint_candidates` (closed → done) | a blocker is satisfied iff closed | **In scope (revised in review).** Slice 1 makes "closed" mean "shipped", and this epic ships in one PR, so the gap must close in the same PR. Jules always branches from the default branch, so **every edge is cross-unit**. In `_sprint_candidates`, a closed blocker counts as done only if `reconcile.pr_merge_state(<blocker>)` ∈ {`merged`, `none`}, via a lazy import; `None` (gh failure) counts as not done. Look up only the ids that appear in some `blocked_by`, and cache them. Test in `tests/jules/test_jules_dispatch.py`: a closed blocker whose last `/pull/` PR is OPEN keeps the dependent ineligible; MERGED or no PR comment makes it eligible. |

Confirmed unchanged: 0a (L30 state flip only), 0d (L66 kinds, L73-75 heal text; stale_blocker kind and heal flow keep working through the shared predicate), 3a (L49, L58, L72), 3b (birth writer), github-issue-relations.md, AGENTS.md, `scaffold.py` (reconcile.py already placed; `KNOWN_SHIPPED_SCRIPT_HASHES` is legacy-install only).

## 3. Script + test changes (`tests/workflows/test_reconcile.py`, house style: `check(name, cond)` helpers called from `main()`)
New `edge_checks()` called next to `all_open_checks()`/`summary_checks()`/`heal_checks()` (L578-580). Fixture rows (cleantech shape):
BT-051 epic v1.2.0 in progress; BT-204 epic v1.2.0 in progress; BT-070 slice v1.2.5 parent 051 in review; BT-207 slice v1.2.6 parent 204 `Blocked by` BT-070; BT-300 epic v1.3.0 `Blocked by` BT-051; BT-301 slice v1.3.1 parent 300 `Blocked by` BT-070; BT-302 slice v1.3.2 parent 300 (inherits BT-300's blocker); BT-309 standalone no milestone; BT-310 slice no milestone parent 300.
`merged_of` stubbed (dict -> `merged|open|none|None`); `rec.pr_merge_state` itself monkeypatched `subprocess`/`_gh_json` for the lookup test.
1. `ship_unit` adapter smoke (the rule itself is tested in slice 2): v1.2.5 and v1.2.6 → `v1.2`; BT-310 (no milestone, parent v1.3.0) → `v1.3`; epic row BT-051 (v1.2.0) → `v1.2`; standalone BT-309 → `BT-309`.
2. Same unit (evidence case): `BT-207 <- BT-070`: `in review` -> OK same-unit; `done` -> OK; `in progress`/`planned`/`blocked` -> UNMET same-unit.
3. Cross unit, child blocker: BT-301 <- BT-070 with merged `merged` -> OK; `open` -> UNMET; `None` -> UNKNOWN; `none` (no PR comment) -> OK; blocker `planned` (unshipped) -> UNMET without calling `merged_of` (assert stub not called).
4. Cross unit, epic/standalone blocker: `done` -> OK; `in review` -> UNMET (PR open); `in progress` -> UNMET.
5. Effective blockers: BT-302 has no own edge; `effective_blockers` = {BT-051} via BT-300; verdict UNMET while BT-051 in progress; BT-302's own + parent's deduped; a dep never blocks itself.
6. `edges_cmd` dependents for `--ids BT-070`: BT-207 CLEAR with `removeBlockedBy` cmd line; BT-301 KEEP when `open`, CLEAR when `merged`; exit 0. `--all-open` sweep lists the same edges once each.
7. `edges_cmd` blockers exit codes: all OK -> 0; any UNMET/UNKNOWN -> 1; no blockers -> `[BLOCKERS-NONE]` 0; absent id -> 1.
8. `stale_blockers`: existing assertions (L104-109, same-milestone rows) stay green unchanged; new: cross-unit child edge with `open`/unknown is NOT flagged; with `merged` it is flagged `stale blocker`. Existing ALLOPEN `--all-open` tests (L141-150, v1.0.0 rows, all same unit) pass unmodified.
9. Heal skip (L398 path, extend HEALMAP test at ~L426): blocker `in review`, **cross-unit child, PR open** -> NOT skipped, edge is healed into the map; same-unit `in review` -> skipped as today.
10. Offline (`gh_available` False): `--edges blockers` for a same-unit edge exits 0; for a cross-unit child blocker exits 1 with `[BLOCKER-UNKNOWN`; `--edges dependents` prints KEEP, exit 0.
11. `pr_merge_state`: last `/pull/` comment wins (two comments, newer PR merged -> `merged`); no `/pull/` -> `none`; PR `CLOSED` -> `open`; gh failure -> `None`.
12. Argparse: `--edges` + `--heal`/`--summary`/`--pr-id` -> exit 2; `--edges blockers` without `--ids` and without `--all-open` -> exit 2 (existing scope group).

`tests/workflows/test_workflow_script_crosschecks.py`: one `# md-crosscheck: workflow reconcile --edges literals vs reconcile.py's real argparse` test. For `4a`, `3d`, `3z`, `3c`, `0b`: every `python .agents/scripts/reconcile.py ... --edges <mode>` literal parses under `rec.main(argv + ['--backlog', <tmp map>])` argument errors only (no SystemExit 2), and the mode is in `{blockers, dependents}`. Style of the contract_check flag test (L101-114); `seen >= 5`. No wording pins.

Sync-script tests: none needed (no change to the Action).

## 4. Version bumps (D5: one bump per file per PR, above the fork-point baseline; "also touched" = slices that already bump it)
| File | Now | Target | Class | Also touched by |
|---|---|---|---|---|
| `workflows/4a-verify-and-ship.md` | 1.5.0 | 1.6.0 | minor (behavior) | 1 (minor), 2 |
| `workflows/3d-implement-issue.md` | 2.6.0 | 2.7.0 | minor | 1 (minor), 2 |
| `workflows/3z-afk-loop.md` | 1.7.0 | 1.8.0 | minor (slice 1 is patch; the higher class wins) | 1, 2 |
| `workflows/3c-sprint-planning.md` | 2.4.1 | 2.5.0 | minor | 2? (unknown) |
| `workflows/0b-stop-session.md` | 1.4.1 | 1.5.0 | minor | 1 (minor) |
| `references/terminal-sync-invariant.md` | 1.1.0 | 1.2.0 | minor | 1 (minor) |
| `memory-templates/BACKLOG_MAP.md` | 1.3.3 | 1.4.0; block `backlog-rules` `v=1.2.2` -> `1.3.0` | minor | 1 (bumps block `label-canonical`, file version shared) |
| `scripts/reconcile.py` | unversioned | none | n/a | 1 (adds `open_on_github`) |
If an earlier slice already bumped a file to the same or higher target, do not bump again. Plugin release bump runs once at 4a step 4 (`scripts/release.py -y`), not in this slice. `dist/` only via the build.

## 5. Verification (in order)
1. `python -m pytest tests/workflows/test_reconcile.py tests/workflows/test_workflow_script_crosschecks.py -n 0`
2. `python -m pytest tests/lifecycle tests/jules tests/scripts -n 0 -k "reconcile or blocked or dispatch"` (shim and jules selectors must stay green; L3 integration tests are gated off by default).
3. `python build/build.py && python build/validate.py .` (per-file bumps, markdown-only-test lint, fan-out).
4. `bash scripts/check.sh` (CI mirror incl. dist drift).
5. Read-only evidence smoke (no writes): `GH_REPO=PatN-git/cleantech_jobs python src/scripts/reconcile.py --edges blockers --ids BT-207 --backlog <fixture map in .tmp/>`; the default-branch map in that repo is stale (rows `planned`), so use a fixture map with `in review` rows, expect `[BLOCKER-OK BT-207 <- BT-070] same-unit`. State in the report that the live map was not used.

## 6. Acceptance criteria
1. `reconcile.py --edges blockers|dependents` returns, for the evidence fixture, OK/CLEAR for BT-207 <- BT-070 (same `v1.2`, shipped) and UNMET/KEEP for a `v1.3` slice blocked by BT-070 until its PR state is `MERGED` (tests 2, 3, 6).
2. `stale_blockers` and the blocked_by heal skip never flag or skip a not-yet-satisfied edge (tests 8, 9).
3. The consumers use the script and match its real flags (crosscheck test):
   - 4a steps 7-8, 0b, 3z L40/L50, and 3c L30 call it;
   - 3d gains a new `[BLOCKED-BY]` guard that includes parent-epic blockers;
   - Jules dispatch keeps a dependent ineligible while its closed blocker's PR is unmerged (jules test).
   - `scripts/check.sh` is green.
4. BACKLOG rule, terminal-sync reference and per-file versions updated once per file; no hand edits to `.agents/` or `dist/`.

## Risks / open questions
- **Coordination #1 (resolved):** a single definition, `pr_body.resolve_unit` (slice 2), which `reconcile.py` imports.
- **Slice 1 hole closed here:** after slice 1, "closed/merged this session" no longer detects a child slice's merge, so 0b clears via the `--all-open` edge sweep, not via closure detection. 0b must run the sweep before deleting retained-away rows (absent blocker row -> UNKNOWN).
- **HITL friction:** D3 needs a same-unit blocker *shipped* (4a), so a user who does 3d on blocker then dependent before shipping the blocker hits `[BLOCKED-BY]`; override exists (HITL). Under 3z the in-run VERIFIED waiver covers it. Accepted per D3, noted.
- **Fail-closed offline:** local-only projects with cross-unit child edges are UNKNOWN until gh is reachable; override is HITL only (3z has none, shows `[SKIP-DEP]` at the 1B confirmation).
- **`done` child with no PR comment treated as no-code (satisfied):** safe only because 4a always posts the comment; a hand-closed, hand-merged slice without it passes too early. Alternative is UNMET, which would strand Spikes. Confirm.
- **Jules dispatch** treats closed as done. After slice 1 that is wrong for blockers that are shipped but not merged, so it is now **in scope** (see the file table) and closed in the same PR.
- **Per-run cost:** 0b `--all-open` sweep adds 2 gh calls per distinct cross-unit child blocker only; same-unit/epic edges are free. Not measured; check against the ship-path-time rule (0b is not on the ship path; 4a adds 0 calls for same-unit and standalone cases, 2 per cross-unit child dependent edge).
- **Heal semantics change:** a cross-unit KEEP edge that GitHub has but the map lacks is now healed *from* gh (before, `in review` blockers were always skipped). Intended, covered by test 9.
- Slice 2's step 8 loop (several epics per release PR) is assumed; step 8 wording above must be rebased on it.
