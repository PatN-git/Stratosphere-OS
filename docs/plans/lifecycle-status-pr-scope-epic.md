---
type: plan
title: Lifecycle Status, PR Scope and Blocker Timing Epic Plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-20
version: "1.0.0"
---

# Epic plan: lifecycle status, PR scope and blocker timing

Epic: BT-190

Status: reviewed 2026-10-20 (slice plans drafted by Sonnet 5.5, reviewed and revised by Opus 5.5). Source: the BT-188 design session. Issue ids are in the table below.

This epic has three slices. They ship on **one feature branch as one PR, with one release bump**, and land in order 1 → 2 → 3. Each slice plan assumes the earlier slices have landed on the branch.

| Issue | Slice | Plan | Blocked by |
|---|---|---|---|
| BT-188 | Close child slices at ship so epic progress tracks shipped work | `slice-close-at-ship-plan.md` | — |
| BT-191 | Release-scoped PR: one branch and PR per `vX.Y` release | `release-scoped-pr-plan.md` | — (lands after 1: shared files) |
| BT-192 | Blocker timing: an edge clears when the dependent's branch has the code | `blocker-timing-plan.md` | BT-191 |

How it is executed (waves, agents, gates): `lifecycle-status-pr-scope-execution.md`.

## Why (evidence)
- **Progress bar.** GitHub's sub-issue progress counts only closed issues, so an epic sits at 0% until its PR merges (slice 1).
- **cleantech_jobs PR #244** (`feat/BT-051-…`, draft) carries slices of epic #51 (v1.2.5) and epic #204 (v1.2.6), which is intended. In `vX.Y.Z`, Y is the feature/release and Z is only a sprint, so the sprints of one release belong in one PR. The tooling is still built around one epic per PR:
  - `pr_body.py --close-parent` closes a single epic, so merging #244 would leave epic #204 open;
  - the Epic Check and the Draft rule look at one parent's siblings only, so the PR can go ready while #204's slices are still in progress;
  - AGENTS.md §4 says "one branch + one PR per FEATURE (the parent BT)".
- **Blocker timing.** #207 (v1.2.6) was unblocked when #70 (v1.2.5) reached `in review`, before any merge. That was correct only because both ship in PR #244. An edge to a blocker that lands in a *different* PR must wait for that PR to merge. Today, 4a step 8 clears epic edges at epic `in review`, and 3c L30, 3z L40/L50, the BACKLOG rule and reconcile `STALE_STATUSES` all treat `in review` as satisfied. In addition, nothing checks a slice's parent epic's blockers: 3z checks only the slice's own `Blocked by`, and 3d checks none.

## Shared decisions (all slice plans must follow these)

**D1. Ship unit (slice 2).**
- A child slice with a milestone `vX.Y.Z` ships on the branch and PR of release `vX.Y`.
- A child slice with no milestone **inherits its epic's milestone** (revised in review). With neither milestone, it ships on its parent epic's branch, as today.
- A standalone issue (no parent) always ships on its own branch and PR, even with a milestone.
- An epic is in the release `vX.Y` of its own milestone, else in its own unit `BT-<epic>`.
- "Same ship unit" = equal unit keys (`vX.Y` or `BT-<padded>`).
- The rule is computed from the milestone and parent fields only, never guessed. It has exactly one implementation, `pr_body.resolve_unit` (slice 2), which every consumer calls or imports.

**D2. Shipped = closed, for child slices** (slice 1). A child slice is `done` and closed at 4a ship. An epic or standalone issue is `done` only when its PR merges. A merged PR closes **every** epic it completed.

**D3. Blocker satisfied** (slice 3).
- The blocker and the dependent are in the **same ship unit** → satisfied once the blocker is shipped (`done`, or a legacy `in review`).
- Otherwise → satisfied only once the blocker's code is on the default branch:
  - epic or standalone issue: closed (merged);
  - child slice: the PR named in its `Shipped in PR` comment is `MERGED`.
- A slice's effective blockers = its own `Blocked by` ∪ its parent epic's `Blocked by`.

**D4. Edge clearing follows D3.** 4a clears at ship only the edges that D3 marks satisfied at ship. All other edges clear when the blocker merges: the 0b done-detection, with the 0d stale-blocker heal as backstop. `reconcile.py` must use the same predicate, so it never flags a not-yet-satisfied edge as stale.

**D5. One version bump per file per PR.** All three slices share one PR, so a file touched by several slices is bumped once (validate.py fork-point baseline). The plugin release bump runs at 4a ship (step 4).

**D6. Discipline.**
- Edit only under `src/` (plus AGENTS.md); `.agents/` and `dist/` are build outputs.
- Terse, agent-first prose; surgical edits; no new abstractions.
- No markdown-wording pin tests; script behavior gets script tests.
- Follow `src/dev-skills/improve-workflows-skills/`.

## Consistency rulings (review, 2026-10-20; these override the slice plans)

The slice plans were drafted in parallel by Sonnet 5.5 and reviewed against the source by Opus 5.5. The rulings below settle every point where the plans overlapped or disagreed. Each slice applies only its own part, on top of the earlier slices.

**C1. One D1 implementation.** `pr_body.resolve_unit(id, milestone, parent, parent_milestone=None, epic=False)` (slice 2).
- Slice 3's `reconcile.ship_unit` is a thin lazy-import adapter, never a second copy.
- Unit keys are slice 2's `vX.Y` / `BT-<padded>`. Slice 3's draft `rel:` / `epic:` / `self:` keys are dropped.

**C2. 4a, the most-contended file.** Final shape per step, with each slice's part:
| Step | Slice 1 | Slice 2 | Slice 3 |
|---|---|---|---|
| L15 hand-off | child `done` + closed; standalone `in review` | the unit PR stays draft until every slice of every epic in it is shipped; merge closes every completed epic | — |
| 1 (L71) | — | `branch_ok` from `pr_body.py unit` (with `--parent-milestone`), else `[BRANCH-UNIT]` | — |
| 5 (L79) | — | heading `5. **PR (one per ship unit):**` plus the crosscheck anchor in the same commit; release PR title | — |
| 7 (L85-86) | status `done` + `gh issue close --reason completed` (child); `in review` (standalone) | — | "Clear blockers" → `reconcile.py --edges dependents --ids BT-<slice>`; clear only `[CLEAR]` edges, keep the `[KEEP]` ones |
| 8 (L88-98) | drop "Build slices close only on merge"; epic `done` on merge | loop over E = `features:`; flip each completed epic P (N) to `in review`; PR ready + CI gate + `--close` for all of E only when every epic is complete (R) | the epic edge clear → `--edges dependents --ids <each P in N>` |
| 9 (L100-102) | coverage parenthetical | ids include each flipped epic; Draft rule over `Parent ∈ E` | pass only the dependents actually cleared |

**C3. 3z.**
- L40: group by unit (slice 2); satisfaction comes from `--edges blockers` (slice 3).
- L50: frontier via `--edges blockers` (slice 3).
- L56 dispatch prompt: the `branch` JSON key (slice 2) plus the "skip the blocker guard" clause (slice 3). Both are additive; keep the JSON contract verbatim otherwise.
- L85-86: "ship status" (slice 1), worded per unit (slice 2).
- L91: slice 1.
- L96: "shipped" (slice 1), "ship unit" (slice 2).
- L107: "ships (same-unit) or merges (cross-unit)" (slice 3 overrides slice 1's "ships").

**C4. 0b.**
- Slice 1 owns L26, L29-31 and the new abandoned-PR bullet. Its "open epic → feature PR" lookup still works when a release PR carries several epics.
- Slice 3 replaces L27's "closed this session → clear" with the `--edges dependents --all-open` sweep. After slice 1, a child closes at ship, so closure no longer signals a merge.

**C5. Jules dispatch: slice 3 owns it.** Slice 1 makes "closed" mean "shipped", and Jules branches from the default branch. A closed blocker therefore counts as done only when its `Shipped in PR` PR is merged, or when it has no PR at all (a Spike). The fix ships in the same PR, so the gap never reaches main.

**C6. Accepted open points.**
- A `done` child with no PR comment counts as satisfied: it's a Spike or manual close with no code to merge.
- The 3d `[BLOCKED-BY]` guard can be overridden in HITL. 3z waives it only for same-unit blockers verified in the same run.
- cleantech #244 adoption stays a HITL prompt (AFK never adopts).
- A 3z unit with one blocked slice stays local (conservative).

**C7. Final version table** (one bump per file per PR vs the fork point; bump at the first slice that touches the file, and a later slice may only raise its level):
| File | Now | Final | Slices |
|---|---|---|---|
| `src/constitution/AGENTS.md` + root `AGENTS.md` | 3.4.0 | 3.5.0 | 2 |
| `src/workflows/3d-implement-issue.md` | 2.6.0 | 2.7.0 | 1, 2, 3 |
| `src/workflows/4a-verify-and-ship.md` | 1.5.0 | 1.6.0 | 1, 2, 3 |
| `src/workflows/3z-afk-loop.md` | 1.7.0 | 1.8.0 | 1 (patch, raised to minor by 2), 2, 3 |
| `src/workflows/3c-sprint-planning.md` | 2.4.1 | 2.5.0 | 3 |
| `src/workflows/0a-start-session.md` | 1.1.2 | 1.1.3 | 1 (grader advisory: the flip also removes `status:done`) |
| `src/workflows/0b-stop-session.md` | 1.4.1 | 1.5.0 | 1, 3 |
| `src/references/terminal-sync-invariant.md` | 1.1.0 | 1.2.0 | 1, 2, 3 |
| `src/references/ci-gate.md` | 1.0.0 | 1.0.1 | 1, 2 |
| `src/references/pr-body-and-ship.md` | 1.0.3 | 1.1.0 | 2 |
| `src/references/feature-acceptance-audit.md` | 1.1.0 | 1.1.1 | 2 |
| `src/memory-templates/BACKLOG_MAP.md` | 1.3.3 | 1.4.0 | 1, 3 |
| ↳ block `label-canonical` | 1.1.9 | 1.2.0 | 1 |
| ↳ block `backlog-rules` | 1.2.2 | 1.3.0 | 3 |
| `reconcile.py`, `pr_body.py`, jules `dispatch.py` | unversioned | — | 1, 2, 3 (covered by the plugin release bump at 4a step 4) |

**C8. This epic's own branch.** StratOS has no GitHub milestones, so D1 puts every slice in the epic unit. `/3d` creates `feat/BT-<epic>-<slug>`, the same name under today's rule and slice 2's. All three slices commit there; 4a opens one draft PR, which goes ready after slice 3.

**C9. Per-slice gate.** Each slice runs its own targeted pytest, then `bash scripts/check.sh`, before its commit. AGENTS.md's 9200-char budget (`tests/framework/test_host_hygiene.py` L55) is checked in slice 2.

## Out of scope
- Fixing cleantech_jobs PR #244 itself (another repo). Once this epic ships and cleantech updates StratOS, re-running 4a there adds `Closes #204`. That is a manual follow-up.
- Sprint-order gating (a later sprint waiting for an earlier one). Sprints are planning buckets; ordering is expressed only by explicit `Blocked by` edges.
