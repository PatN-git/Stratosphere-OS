---
type: plan
title: BT-241 apply-moves refuses guarded moves while a blocker is open
generated:
  by: claude-code session (PatN-git)
  at: 2026-11-04
version: "1.0.0"
---

# BT-241: `apply-moves` refuses moves into in-progress / in-review / done while a blocker is open

Status: proposed 2026-11-04 (not yet executed). Decided in review: option A lands in v5.0.0 (PR #216). #241 is a child of BT-194 (already a sub-issue: `gh api repos/PatN-git/Stratosphere-OS/issues/194/sub_issues` lists 240 and 241). Companion: `docs/plans/bt240-v5-handoff-plan.md` (owner decision round, order of work, release, cleanup).

Marks: **[V]** verified by reading code/docs or a command on 2026-11-04 (file:line at HEAD `d51938d`); **[U]** not verified.

## 1. Goal and exit criteria

Goal: a human's drag-and-drop payload cannot move a card past an open blocker without `--force`, with the same blocker definition as `ready` and the 3d guard.

Exit criteria (all checkable):
1. Section 4 criteria 1-12 pass; RED recorded before GREEN.
2. `bash scripts/check.sh` ALL CHECKS PASSED at the final HEAD; `floor_guard.py` exit 0 per commit; no test removed.
3. Delta audit-only `[PASS]` on `d51938d..HEAD`; CLI re-check of DnD case 5b done.
4. #241 shipped through 4a ship-only AFTER #240 is closed, so the 4a Epic Check completes #194 and runs the Feature Acceptance Audit (FAA).
5. CI green on the pushed head; PR #216 body rebuilt (`closingIssuesReferences` keeps 194 and adds 241).

## 2. Current behaviour (verified)

- `cmd_apply_moves` (`src/scripts/issues.py:818-898`) refuses only: unparseable line (`:854`), unknown id (`:859`), unknown status (`:862`), `claimed_by` another branch unless `--force` (`:868-870`), epic/standalone `in review -> done` not merged unless `--force` (`:872-876`). No `blocked_by` rule **[V]**. Evidence: `experiments/probes/v5-kanban-board/dnd.md` case 5b (main checkout, not `bt221\.tmp`) **[V]** file exists; content per the earlier draft **[U]**.
- Atomic: any problem raises `IssuesError(... nothing applied ...)` at `:888-889`; moves mutate `store.issues` in place inside the loop (`:877-884`), a refusal discards the store. `old == target` lines are skipped (`:866-867`): the board re-sends already-applied moves.
- The board page is a static snapshot; all refusals happen when the user runs the command. The badge (BT-238) lists raw `blocked_by` edges (`board.html:461`, fed from `issues.py:546-547`) **[V per earlier read; U on re-check]**.
- apply-moves is unreleased: `src/scripts/issues.py` and `src/references/tracker-verbs.md` are absent at fork point `b7329af` and at tag `v4.10.1` **[V]**. So v5.0.0 can define the rule with no compatibility cost.
- Callers: only humans via the board payload. No harness calls it (`stage_checks_local.py:31` only classifies the verb). The lifecycle workflow `src/workflows/3c-sprint-planning.md:21` tells the user to apply the board payload: **no text change needed there** **[V]**. Other mentions: `RELEASING.md:89,95`, `src/references/tracker-verbs.md:41`, `tests/framework/test_tracker_verbs.py:181-190`.
- GitHub backend: `apply_moves` is `n/a` (`tracker-verbs.md:41`); the GitHub cell and the assertion at `test_tracker_verbs.py:181-190` (GitHub file names no `apply-moves`) stay untouched. The agent-side guard on both backends is 3d's `reconcile.py --edges blockers` (`3d-implement-issue.md:20`).
- Blocker definition in the repo: `ready()` uses `effective_blockers(bt, rows)` plus `edge_verdict(...) != 'OK'` (`issues.py:415-424`); `reconcile.py:219-227,569` uses the same two functions **[V]**. `edge_verdict` (`_tracker_common.py:118-145`): same ship unit is OK on `in review|done` (`SHIPPED`, `:13`); a cross-unit epic/standalone blocker is OK only when `done`; a cross-unit child-slice blocker needs `merged_of` **[V]**.

## 3. Design: option A (confirmed in the owner round)

1. Guarded targets: `GUARDED = ('in progress', 'in review', 'done')`, next to `STATUSES` (`issues.py:48`). `needs_spec`, `planned`, `blocked` are never refused.
2. Checked moves: every move with `old != target` and a guarded target, including reopen `done -> in progress` and `in progress -> in review`. `-> done` is always `completed`; a not-planned close uses `issues.py close --reason` (unguarded) or `--force`.
3. "Blocker open" = `effective_blockers(bt, rows)` (own plus parent epic's, `_tracker_common.py:106`) with `edge_verdict(...) != 'OK'` (UNMET or UNKNOWN), as `ready`. Not the issue snippet (`effective_status(b) != 'done'`, own edges only), which disagrees with D3 in four cases: same-unit blocker `in review` (D3 accepts), parent epic's blockers (ignored), cross-unit done-but-unmerged slice (D3: UNMET), and a satisfied-but-uncleared edge (4a step 7 clears only `[CLEAR]` edges; `[KEEP]` waits for the merge).
4. `merged_of`: `make_merged_of(store)` runs `default_branch()` and `git for-each-ref` at construction (`issues.py:381-412`), so build it **on the first call** of a closure, not at the top of the pass. No default branch gives UNKNOWN and a refusal (as `ready`); `--force` overrides.
5. Evaluated on the batch end state: a pass after the line loop, over `touched` cards, using `store.rows()` of the mutated store. A payload that moves the blocker to `done` and its dependent to `in progress` passes in either line order. Only cards moved in this batch are checked. Run the pass BEFORE the `if problems:` raise (`:888`) so blocker lines and parse lines list together.
6. Message per open edge: `line N: [BLOCKED <id> <- <blocker>] <edge_verdict reason>; use --force to move`. `N` = the line of the card's LAST move (record `moved_at[bt] = n` where `touched[bt] = issue`, `:883`).
7. Exit codes: refusal = exit 1 via `IssuesError`; `--dry-run` reports the same refusal; `--dry-run --force` exits 0. Success output unchanged.
8. `--force` stays one blanket flag (claim, unmerged review-to-done, blockers). No `--ignore-blockers`. Owner confirms (decision 1 of the companion plan).
9. Badge: no change. Known accepted mismatch: the badge shows raw edges, the refusal acts on unmet ones; a precise badge needs a `meta` data-contract change (out of scope).
10. Scope: only `apply-moves`. `set --status`, `close`, `reopen`, `claim` stay unguarded; say so in the doc row.

## 4. Acceptance criteria (testable)

1. A card with an open blocker moved to each of `in progress`, `in review`, `done` is refused: exit 1, store tip unchanged, output contains `nothing applied`, `[BLOCKED <id> <- <blocker>]`, `--force`.
2. The same batch with `--force` exits 0, applies, and leaves `blocked_by` untouched.
3. Moves to `needs_spec`, `planned`, `blocked` are not refused while a blocker is open.
4. A `done` blocker (standalone), or a same-unit blocker `done` or `in review`, allows the move; a standalone blocker `in review` does not.
5. The parent epic's open blocker refuses a child slice's guarded move.
6. A cross-unit child-slice blocker `done` but not merged refuses; once merged it allows (`_blocker_with_tip_and_deleted_branch`, `test_issues.py:760`; needs `.memory/ARCHITECTURE.md` as at `:777-779`).
7. One batch moving the blocker to `done` and the dependent to `in progress` applies in either line order; moving only the dependent refuses.
8. A refused batch applies nothing even with good lines, and lists every blocker line and every other bad line.
9. `--dry-run` shows the same refusal (exit 1, clean tip); `--dry-run --force` exits 0, tip clean.
10. A line whose card is already in the target status (`old == target`) with an open blocker is NOT refused (the board re-sends applied moves).
11. Reopen `done -> in progress` with an open blocker refuses; a card moved twice in one payload reports the line of its last move.
12. The 16 existing `test_apply_moves*` tests (`test_issues.py:925-1255`, none uses `--blocked-by` **[V]**) pass unmodified; the `tracker-verbs.md` apply_moves local cell states the rule and `--force`; the GitHub cell stays `n/a`; `tracker-verbs-local.md`, dist copies and `RELEASING.md` agree.

## 5. Ordered steps

Owner column: user = needs the owner's per-action OK in the companion plan's decision round; agent = lead session; impl = Sonnet 5.5 high implementer with NO git writes; lead commits with explicit paths (shared index, commit pathspec only). Line numbers are at `d51938d`.

| # | Step | Owner | Outward? | Verification |
|:--|:--|:--|:--|:--|
| 0 | Precondition: decisions D1-D3 of the companion plan answered; work on the existing branch `improvement/BT-194-tracker-backend-no-map` (3d will print `[NO-RELEASE]`: no milestones in this repo, override to the epic branch) | user | no | answers recorded in the #240 comment later |
| 1 | Rewrite the #241 body to option A: Path/AC = sections 3-4 above, the `edge_verdict` rule (not the snippet), `Parent: BT-194`; flip `status:needs_spec` -> `status:planned` (3d HALTs `[SPIKE]` on `needs_spec`, `3d-implement-issue.md:19`). "Set as child of BT-194" is already done | agent | **needs the owner's OK** (2 issue writes) | `gh issue view 241 --json labels,body`; parent line present |
| 2 | RED tests in `tests/scripts/test_issues.py`, after `test_apply_moves_reads_stdin` (`:1249`); helper `_gated(repo)` creating blocker + dependent via `create --blocked-by`. RED (must fail today for the right reason): refuse x3 targets; standalone-in-review refuses vs same-unit-in-review allows; parent epic; cross-unit unmerged then merged; atomic and lists every line; dry-run refusal and `--force`; dependent-only; reopen `done -> in progress`; last-move line number. GREEN-vacuous today (pins that must survive; no guard exists yet): `--force` moves past a blocker; allowed once blocker done; moves to `planned/blocked/needs_spec`; `old == target` not refused; blocker-first/dependent-first order (becomes discriminating only after GREEN: also run it once against a naive in-loop check, or accept it as a post-GREEN pin). Add one assertion at `test_tracker_verbs.py:187-188`: the local `apply_moves` line contains `blocker` (RED until the doc row). Record output in `.tmp/bt241-red.txt` (expect about 11 failing, rest passing) | impl | no | run with `TMP=TEMP=C:\t`: failures are the RED set, for the stated reason |
| 3 | GREEN in `src/scripts/issues.py`: add `GUARDED` (`:48` area); `moved_at = {}` at `:838`, set at `:883`; the post-loop pass before `:886` (rows = `store.rows()`; lazy `merged_of` closure; per touched card with guarded effective status and not `force`, per sorted effective blocker with verdict != OK, append the section 3 message); docstring (`:819-822`) gets one sentence; `--force` help (`:1134` area) adds "; move past an open blocker". Imports already include `edge_verdict`, `effective_blockers` (`:38`) | impl | no | `pytest tests/scripts/test_issues.py tests/framework/test_tracker_verbs.py` green |
| 4 | Docs, reference text only: `src/references/tracker-verbs.md:41` local cell: "a move into `in progress`, `in review` or `done` is refused while a blocker is open (the `ready` verdict), else `--force`; `set`/`close`/`reopen` are not guarded"; `RELEASING.md:94-96` half a sentence (same rule); run `python build/build.py` (regenerates `-local.md`, `-github.md`, dist copies). No workflow, rule or AGENTS text changes | impl | no | `python build/validate.py .`; no dist drift |
| 5 | `floor_guard.py` (exit 0), then `TMP=C:\t TEMP=C:\t bash scripts/check.sh` (about 5.5 min, 321 s in the PR body); lead commits: (a) tests + `issues.py` + docs, (b) dist rebuild (precedent `19f68b7`) | agent | no (local commits) | ALL CHECKS PASSED; `git show --stat HEAD` lists only intended paths |
| 6 | Shared v5 docs debt in the same push (belongs to #240 by its own body): `RELEASING.md` "Removed" line for the Google Jules integration (`3x-jules-dispatch`, dispatch pack, no replacement; today `RELEASING.md` has zero Jules mentions **[V]**); `docs/proposals/v5-completion-plan.md` log: section 9 decision 1 reversed (enforcement lands in v5.0.0), section 11 final state (stale: it still says `51cb32f`/`4bd4fb7` not pushed, Stage 3 "groups 1-6", Stage 4 not started **[V per review]**) | agent | no | read-back diff |
| 7 | CLI re-check of DnD case 5b on `C:\t\v5dnd` (exists **[V]**; run it BEFORE the #240 cleanup deletes it): the Gated-to-In-Progress payload: `apply-moves --dry-run -` exits 1 with `[BLOCKED ... <- ...]`; `--force` applies; a payload moving the blocker to `done` first passes. Note the result in the plan log (commit with step 6 or a follow-up docs commit) | agent | no | exit codes as stated |
| 8 | Delta audit-only (Sonnet 5.5 high, 4a Phases 1-3, read-only subagent) on `d51938d..HEAD` | subagent | no | `[PASS]`, spec gaps >= 80: 0, std_hard: 0; fix findings, recommit |
| 9 | #240 closed first (companion plan step: per-item comment, `status:done`, close) so the Epic Check sees every sibling shipped | agent | **needs the owner's OK** | `gh issue view 240 --json state` CLOSED |
| 10 | 4a ship-only for #241: `test_gate.py record` suite line, push (fast-forward only), Epic Check -> FAA over the whole-feature diff of #194 (`4a-verify-and-ship.md:94-95`), CI gate, PR body rebuild (head, `test:` with the final test count, slices incl. BT-241, Notes refreshed), #241 `done` + closed, #194 `in review` per 4a. If the FAA finds gaps >= 80 the ship halts: the PR is already ready, so `gh pr ready --undo` (pre-authorize in the owner round), fix, re-run | agent | **needs the owner's OK** (push, PR body edit, issue writes, possible `gh pr ready --undo`) | `gh pr view 216 --json headRefOid,isDraft,mergeStateStatus,statusCheckRollup,closingIssuesReferences` |
| 11 | `agy plugin validate dist` (expect `[ok]`, 27 skills: dist changed); repeat the T1 gate of the companion plan (head == local HEAD, ready, CLEAN, both checks SUCCESS, `origin/main` still `132dcb8`) | agent | no | as stated |

PR body rebuild rules (step 10): keep the explicit `Closes #194.` line (body line 16); add `Closes #241.`; do not add `Closes #240` (closed by comment). Never write a closing keyword plus issue number in free prose, even inside backticks (GitHub parses it).

## 6. Quota estimate (one 5-hour window, Sonnet 5.5 high; **[U]** all)

| Item | Estimate |
|:--|:--|
| Steps 1-5 (impl, tests, code, docs, build, check.sh) | 5-7% (25-35 turns, 40-60 min wall) |
| Step 6-7 docs debt + CLI re-check | 2% |
| Step 8 delta audit-only | 2-3% |
| Step 10 ship-only (push, body, CI watch) | 3-4% |
| Step 10 FAA (Epic Check) | 5-12% |
| Total | about 17-28% (about 12-16% without the FAA) |
| Wall time | 2-3 h including CI (about 5-10 min per run **[U]**) and check.sh |

Marginal cost A over B is about 4-6%: B also needs a commit, check.sh, push, CI, body refresh and delta audit, so it saves only the ~20-line pass and ~11 tests.

Not needed: L1-L3/L5 live regressions (no harness or workflow calls apply-moves; no workflow/rule text changes), real-mouse DnD (`board.html`, the payload and `apply_cmd` are unchanged; the refusal is CLI-side), GitHub smoke. Counter-note: `v5-completion-plan.md:98` lists "no change to apply-moves rules" as a hard guard of Stage 2; this slice is an owner-approved exception after Stage 2, gated by its own pins and `check.sh`.

## 7. Risks

1. Definition drift: the issue snippet differs from the `edge_verdict` rule; the #241 body is rewritten (step 1) so 3d builds the rule here. The owner confirms in the round.
2. Blanket `--force` (accepted).
3. Cross-unit `UNKNOWN` with no default branch refuses with the `PR state unknown (gh unavailable)` wording, imprecise for the local tracker (same as `ready` today).
4. An UNKNOWN edge (blocker absent from the store) cannot be created through `create`/`set` (they require the blocker): untested; refuses by the `!= 'OK'` rule.
5. The FAA may find gaps >= 80 and halt the ship; the PR must go back to draft (`gh pr ready --undo`, OK needed) until fixed. Cost is **[U]**.
6. The first Linux CI run of the git-based cross-unit test is the arbiter for platform differences **[U]**.
7. A new push resets CI and the "ready" evidence for the new head; the PR body `head:` and `test:` lines must come from the final head.
8. Windows MAX_PATH: run tests with `TMP=TEMP=C:\t` (WinError 206 in `test_nightly_scan`); GDrive-style mtime flakes do not apply on the local disk. A subprocess access-violation flake (exit 3221225477) passes alone and in CI.
9. Concurrent sessions share the feature branch and index: commit with explicit paths and verify `git show --stat HEAD`; never pathspec-commit a `git rm --cached`.
10. Fallback B (display only, documented) is acceptable only if the owner accepts a documented gap in v5.0.0 and a behaviour change on a released command in 5.1; then only a pin and the doc sentence, and the companion plan's order is otherwise unchanged.

## 8. Definition of done

1. D1-D3 recorded; #241 body rewritten and `status:planned` (OK each); #241 is a sub-issue of #194.
2. Section 4 criteria pass; RED output recorded before code; GREEN after; no test removed; `floor_guard.py` exit 0 per commit.
3. `check.sh` ALL CHECKS PASSED at the final HEAD; dist rebuilt in its own commit; no drift; `agy plugin validate dist` ok.
4. CLI case 5b re-check noted in the plan log; delta audit `[PASS]`.
5. Docs agree: `tracker-verbs.md`, projections, dist, `RELEASING.md` (apply-moves rule and the Jules removal), `v5-completion-plan.md` sections 9/11, PR body Notes (the "planned / owner decides" sentences replaced) and the "apply-moves blocker semantics (decision pending)" unverified item in `v5-completion-plan.md:30` removed (it is not in the PR body).
6. #240 closed before the ship; 4a Epic Check ran with the FAA (or the owner-recorded scoped deviation); CI green; `closingIssuesReferences` contains 194 and 241.
7. Nothing pushed or edited outside the owner's OKs.
8. Not verified until run: FAA cost and findings, CI wall time, platform behaviour of the git-based test.
