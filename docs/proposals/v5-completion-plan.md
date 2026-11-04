---
name: v5-completion-plan
description: Staged plan to finish PR #216 (StratOS v5.0.0, tracker backends) cleanly: publish the verified state, fold the backlog and Standards items into the same PR, then prove real GitHub before CleanTechHub moves to v5.
type: proposal
version: "0.2.0"
generated:
  by: Claude
  at: "2026-11-03"
---

# Plan: complete v5.0.0 in PR #216 (stages 0-4)

**Status:** v0.2. v0.1 was challenged by an independent reviewer (Sonnet 5.5 high; 8 must, 15 should, 6 nit; evidence in `.tmp/l3live/plan-challenge.md`); this version answers every must and should item (see section 10). **Owner decisions taken:** fold the 14 triage backlog items and the Standards audit items into this PR; stage the work; publish the current verified state first; leave `apply-moves` blocker enforcement out (backlog issue, decided separately). **Owner decisions pending:** none that block stage 0.

## 1. Where we are (HEAD `97e62f3`, 24 commits ahead of `origin/improvement/BT-194-tracker-backend-no-map` = `5800852`; PR #216 non-draft, GitHub head `5800852`)

| Evidence | Result |
|:--|:--|
| `scripts/check.sh` at HEAD | ALL CHECKS PASSED (second run; the first run crashed `floor_guard.py` with a Windows access violation, exit 3221225477, inside `test_floor_guard.py::test_silent_on_tightening`; the file passes 40/40 alone) |
| Test gate recorded at HEAD | 1137 passed, 272 files (a `test_gate record` run; **not** the per-slice suite record 4a reads: see 0.1) |
| 4a audit-only round 1 (`5800852..66aabd7`) | `[PASS]`, spec gaps 0, std_hard 0, Watch W1-W5, 12 Standards judgment smells |
| 4a audit-only round 2 delta (`66aabd7..f7fe45d`) | `[PASS]`, 2 advisory smells, Watch W-a..W-d |
| **Not audited:** `f7fe45d..97e62f3` (`9671738` no-PR ship path, 3z Step 2B `gaps`, FAA/0b/ci-gate clauses) | audited in 0.2 before anything is pushed |
| Live L1 / L2 / L3 (local tracker, Haiku, fake gh), B3 re-runs | L1 33/33, L2 29/29, L3 49/51 (50/51 neutralising one rig false positive); L4 39/39, L5 20/21 (first pass). L3: FAA CLEAN, `gh pr ready`, CI gate, epic flip, 3z Phase 4, sentinel |
| B4 + live F35 | round-2 convergence 2/2 and negative control 2/2 (replayed audits); recovery case live; cap case reaches `status:blocked` via stand-ins. Ran at pin `66aabd7`, **before** the 3z `gaps` change |
| Part A local no-PR flow | ran at pin `66aabd7`: U1 pass, U2 PARTIAL (the D2 CI-gate halt), squash advisory, remote-only merge, unmerged stays open. Fix is `9671738`, covered by pin tests only, **no live re-run** |
| Board real mouse drag-and-drop | 5/5 (Done column not mouse-tested) |
| Real GitHub | Antigravity smoke (B1) only |

**Unverified today (carried into the PR body `post_merge:`/`## Notes`, section 3.0):** Linux CI for the 24 commits (last green CI is `5800852`); 3z Step 2B `gaps`/retry wording and the no-PR ship fix live; three real audit rounds to the cap; real GitHub beyond B1; Antigravity host run of the v5 skills; concurrent worktrees on the `<repo>/issues` branch; a real v4-to-v5 consumer upgrade (CleanTechHub); `apply-moves` blocker semantics (decision pending).

## 2. Principles (every stage)

1. **Surgical.** One clause per item, removing an ambiguity or contradiction; no rules for hypothetical cases. **Always-loaded files (`AGENTS.md`, `src/constitution/*`, `rules/*`) never grow**; this plan changes none.
2. **Pinned.** Behavioural clauses get a RED-first pin in the existing style; pure prose polish with no pin pattern gets none.
3. **Source only.** Edit `src/`; `dist/` and `.agents/` are build outputs. Per-file `version:` is bumped once per PR vs the fork point `b7329af`: of the Stage 1 files only `references/design-doc-template.md` still needs its first bump; the rest only if the level is understated.
4. **Measured size budget (replaces "net text does not grow").** Baseline = HEAD at stage start; ceiling = baseline + 1500 characters over all edited files of the stage (Stage 1), measured by a `.tmp/` script and reported; deletions are preferred over additions; the playbook `src/dev-skills/improve-workflows-skills/SKILL.md` (prune and diff gate, non-negotiables 5-7) is applied to each cluster. No test constrains workflow size today, so the report is the gate.
5. **Git ownership (AGENTS.md section 8).** Implementers, finishers and auditors make **no git writes**. **The lead (this session) commits** per cluster with explicit paths and the Co-Authored-By trailer; `dist/` in its own commit. The stages run as a direct user request (precedence 2); the 3d claim and milestone path does not apply, and the no-milestone override is recorded in the slice bodies (StratOS uses no milestones).
6. **Authorization is per action and does not carry over (AGENTS.md section 4).** Every push, every `gh pr ready` / `--undo`, issue minting and comments, Stage 3 and Stage 4 deletions need the user's OK in chat, stated at the stage exit. OK given for Stage 0 covers only Stage 0's listed actions.
7. **Never:** merge, force-push, push to `main`, touch credentials from a sandbox, or reference the throwaway real repo outside Stage 3.
8. **Quota.** Read usage before each Haiku batch; stop and report at 70% of the 5-hour window (ceiling 90%); also read the weekly figure and stop a stage that would take it past 60%. Measured cost: 1.3-1.9 points of the 5-hour window per Haiku run. Sonnet 5.5 high implements and orchestrates; Haiku 5.5 high is the agent under test only.
9. **Stop after each stage** with usage, commits, size delta, the stage's exit numbers and what is unverified.

## 3. Stage 0: publish the verified state

### 3.0 Facts that shape the order (from the review)
- 4a ships **slices**, never the epic. Re-shipping needs a named slice id (use **BT-222**, the last slice; steps 6-7 are idempotent re-runs per `4a` lines 88 and 90). `--audit-file` replaces only that slice's `audit:` entry, so epic-scope rounds go to `## Notes`.
- If BT-194 stays `in review` with every sibling closed, 4a step 8 treats the epic as complete, runs the CI gate and `gh pr ready`, undoing a draft. So **the follow-on slices are minted and BT-194 set back to `status:in progress` before the ship run**; then 4a step 9's draft rule keeps the PR draft by itself (no manual flips needed).
- `risk:` in the `stratos-pr` block is computed from `merge-risk-paths.md`; unverified items go in `post_merge:` (and `## Notes`), never `risk:`.
- The existing `post_merge:` list has duplicates and stale lines; a rebuild unions the prior list, so it is cleaned first.

### 3.1 Steps (in this order)
| Step | Action | Needs OK | Verify (measurable) |
|:--|:--|:--|:--|
| 0.1 Preflight | tree clean outside `docs/`, `.memory/`, `.tmp/`; `git fetch origin`; `origin/improvement/BT-194-...` is an ancestor of HEAD; rerun `floor_guard.py` once (a second crash is reported and halts); run `python .agents/scripts/test_gate.py record --suite BT-222 -- bash scripts/check.sh` at HEAD so `pr_body.py suite` is not `[NO-SUITE] head moved`; run `claude plugin validate .` and `agy plugin validate dist` (RELEASING step 2; if a CLI is absent, record that) | no | clean tree; `pr_body.py suite` returns the HEAD record; validators ok or recorded absent |
| 0.2 D3 decision (constitution consistency) | `4a` currently pushes whenever an `origin` exists; AGENTS.md section 4 (Git Protocol 4) allows a push only when `gh` is connected. Resolve **without touching the constitution** (it has 164 characters of headroom and an edit re-triggers `needs_review_constitution` for every consumer): tighten `4a` steps 4 and 9 to "push only when `gh` is connected; otherwise stay local and say so" (the local tracker branch then waits for a connected push; `merged --close` uses local ancestry), with the 0b/`post-merge-sync` wording unchanged. RED-first pin, rebuild, `check.sh` | no (a fix, not an outward action) | pin passes; Part A scripted checks unchanged (no remote needed) |
| 0.3 Delta audit | audit-only (Sonnet 5.5 high, 4a Phases 1-3, no Haiku) on `f7fe45d..HEAD` (covers `9671738`, `97e62f3` and 0.2); frozen list empty | no | `[PASS]`, spec gaps >= 80: 0, std_hard: 0; a gap is fixed before going on |
| 0.4 Mint the follow-on work | after the user approves the AC lines drafted below: epic BT-194 back to `status:in progress`; child slices **S1** wording batch, **S2** behaviour-preserving refactors, **S3** board "blocked" badge (own commit), each `tier:slice`, scoped commits `<type>(BT-<n>)`; non-code children **S4** real GitHub smoke and **S5** handoff are closed by comment with evidence (4a ships nothing for them); one standalone backlog issue for `apply-moves` blocker enforcement. Minimal 3b minting (mode + Lifecycle field, dry-run, `reconcile.py --expect` gate); the no-milestone override is stated in each body. Comment on #194, #221, #222 with the live-test summary and a link to this plan | **yes** (AC lines and the mint) | `reconcile.py --expect` OK on all new issues; BT-194 `in progress`; each slice has verifiable AC |
| 0.5 PR body + push | clean the prior body (`.tmp/4a-prior-body.md`: dedupe the repeated `after merge`/`noticed` lines, drop stale ones: reconcile.py size ~990/609 (file is 582), "live harness run not done", `head: 7c9b664`, BT-219 chore), then `/4a-verify-and-ship` ship-only for slice **BT-222** (named; epic scope never passed as slice): push (fast-forward), rebuild body (`head` = new HEAD, `test.observed` from the 0.1 record, unverified list in `post_merge:`, epic-scope audit rounds in `## Notes`), read the result back (no duplicate lines; counts match files) | **yes** (push + body) | PR head == local HEAD; body parses with `pr_body.py`; `closingIssuesReferences` lists the 10 `Closes` issues present today; PR still draft |
| 0.6 CI | watch checks through the PR tools (no polling loops). While the PR is draft `ci_gate.py` does not run: a red check is fixed by a plain `fix(BT-<slice>): ci` commit (at most 2 for one failure; a third stops the stage) followed by a push with OK; a Windows-only crash is reported, never masked. The first Linux CI run of the local tracker, board and shim code happens here | no (watching) | all required checks green |
| 0.7 Reference docs | verify `RELEASING.md` section v5.0.0 against the shipped scripts and **add** the missing verbs (`merged`, `board`, `apply-moves`) and the cleantech_jobs#267 pointer; note the no-PR ship path and (per 0.2) that a project without `gh` keeps the tracker branch local; mark `docs/plans/tracker-parity-and-smoke-plan.md` and `docs/plans/pr216-live-test-fixes-plan.md` implemented with evidence locations; commit this plan with the S5 slice | no | doc tests green |

**S1-S5 acceptance lines (drafted here, approved at 0.4):**
- **S1:** each cluster-A/B/C row of section 4 is applied or struck with a reason; size delta <= +1500 characters; `check.sh` green; delta audit `[PASS]`; no `AGENTS.md`/constitution change.
- **S2:** each listed refactor lands as its own behaviour-preserving commit with the affected test files green before and after; `floor_guard.py` exit 0 before each commit; L1 >= 33/33, L2 >= 29/29, L3 >= 49/51 after (live); Part A scripted checks U1-U4 unchanged; one real-mouse drag-and-drop re-check passes.
- **S3:** the board shows a blocked card's blockers (display only); drag-and-drop 5/5 unchanged; apply-moves behaviour unchanged.
- **S4:** the named verbs and `--expect` forms from section 6 produce real responses; 0 unexplained diffs vs the fixtures.
- **S5:** section 7 items done or listed as owner actions.

**Stage 0 exit (numbers):** PR head == HEAD; draft; all required checks green; delta audit `[PASS]` spec 0, std_hard 0; BT-194 `in progress` with S1-S3 `planned`; `pr_body.py` body round-trips. **Report:** usage, PR link, CI result.

## 4. Stage 1: wording batch (S1; about 1.5-2 h, about 8-10% quota)

Before assigning, a pre-step re-verifies every row against HEAD and strikes what is already done (for example, the FAA status set `PASS | FAIL | UNVERIFIED` is already at `feature-acceptance-audit.md:23`; only "helper-only tests = FAIL" remains for L3-20). Deferred explicitly (triage 2 backlog): T4b, T8, T33, T34, T36, T48.

| Cluster | File | Items |
|:--|:--|:--|
| A: memory and planning | `0d-nightly-consolidation.md` | P3a delete ", unvalidated"; P3d "delete (git history is the archive)" |
| | `2b-interface-design.md`, `references/design-doc-template.md` (first bump needed) | P10a stable-vs-Contract-Check order; P10b `## Deviations` pointer; P10d blocking §10 question rule |
| | `3a-version-planning.md` | P11c `none yet` Live product; P11d scope from PRD §6 tags |
| | `3c-sprint-planning.md` | P12d `Area: —` when none |
| B: build and ship | `3z-afk-loop.md` | L3-8 unit order = first appearance in the queue |
| | `3d-implement-issue.md` | L3-9 `<cmd>` = the project's test command |
| | `skills/micro-tdd/SKILL.md` | L3-13 batching field; whole-module ImportError as RED |
| | `4a-verify-and-ship.md` | L3-15 Phase 1 trigger precedence; L3-18 coverage_map keying for PRD §8 items owned by a later slice; `done` then `close` quirk on local |
| | `references/feature-acceptance-audit.md` | L3-20 remainder: helper-only tests = FAIL |
| C: audit watch | `references/post-merge-sync.md` | W-d mirror the non-fatal fetch wording of 0b |
| | `src/scripts/reconcile.py` + `tests/workflows/test_reconcile.py` | W-a `--with-edges` refusal names the right flag; the test asserts the message, not just exit 2 |
| | `0b-stop-session.md` | W-c split the dense `merged --close` line (order unchanged; pin stays green) |
| | tests | `next(..., None)` + assert message in the 0b pin; tracker-verbs `close` row reads alone in the local projection |

**Execution:** two Sonnet implementers on disjoint clusters (A; B+C) with no git writes and no dist rebuild; a Sonnet finisher (no git writes) rebuilds `dist/`, runs `validate.py`, the targeted tests, records the test gate and runs `check.sh`; the **lead commits** per cluster. **Verify (exit numbers):** `check.sh` ALL CHECKS PASSED at the final HEAD; size delta reported and <= +1500 characters; `floor_guard.py` exit 0; delta audit-only `[PASS]` with the frozen list empty; **wording is unverified live until Stage 2's L1-L3 and a short L5 (0d) run pass, and the stage report says so.** **Exit:** local commits plus the report; the push and PR-body refresh need the user's OK.

## 5. Stage 2: refactors (S2) and the blocked badge (S3) (about 3 h, about 40-45% quota; run after a 5-hour reset)

**S2 (behaviour-preserving, one commit per item, tests run before and after the edit):** hoist the three `effective_status` closures; `cmd_merged --close` calls `_close_issue()` (mind the always-reset `closed` date: keep behaviour identical or stop); one per-issue helper shared by `local_gate` and `github_gate`; escapes instead of raw TAB/U+2028 literals; direct `a.attr` instead of `getattr` defaults; inline `generate_projected_verbs`; hidden board cards marked by class instead of `[style*="display: none"]`. **No test removal** (`floor_guard.py` `tests-removed` halts 4a; run `floor_guard.py` before every commit; a file that must shed an assertion adds one in the same commit so it nets >= 0). **S3 is its own commit:** the "blocked by" badge on board cards, display only.

**Hard guards:** no change to merge detection semantics, `parse_expect`, gate verdicts or `apply-moves` rules; a refactor that needs a test change stops and reports.
**Verify:** `check.sh`; deterministic Part A checks (scripted U1-U4: merge commit, squash advisory, remote-only merge, unmerged) re-run on the new code; one real-mouse DnD re-check (5 cases); **L1-L3 live regression is unconditional** (new sandbox; pass bar L1 >= 33/33, L2 >= 29/29, L3 >= 49/51; Haiku cap 26; stop at 70%) plus a short **L5** (0d, cap 3); delta audit-only. If the budget does not fit one window, the live regression is the last item and waits for the next reset.

## 6. Stage 3: real GitHub smoke (S4; about 40 min, about 5% quota; needs the user's OK; uses credentials)

The **user** creates (or approves creating) the throwaway repo with a one-job `pull_request` workflow so `ci_gate.py` has real checks. Exercise, with real responses diffed against `tests/lifecycle-harness/shims/gh_shim.py` fixtures: tracker setup on a fresh clone; issue create/label/comment/close verbs; `reconcile.py --expect` and `--with-edges`; `ci_gate.py status` and `--expect-checks`; `gh pr ready`; `tracker_switch.py` dry run then `--apply`; one 4a ship-only to a real PR. **Exit numbers:** every verb listed produces a response; 0 unexplained diffs (each drift fixed in the shim or the product with a RED pin, `check.sh`, a delta audit, and the Stage 2 live regression re-run if product code moved). The PR is marked ready (with OK) once this passes; the user deletes the throwaway repo.

## 7. Stage 4: handoff (S5; about 30 min)

- **Merge readiness:** merge order against open PRs #231, #232, #235 (they overlap with #216 on `build/build.py`, `README.md`, `marketplace.json`, `dist` manifests): user's call; after any merge of `main` into the branch rerun `build.py` + `validate.py` and confirm `VERSION = "5.0.0"` and that `release.yml` creates `v5.0.0`. Merge method: **merge commit**, not squash (local `merged --close` depends on ancestry).
- **Release notes:** `release.yml` generates notes from titles only; put "BREAKING v5.0.0" in the PR title and add the migration pointer to the body so the Release page carries it.
- **Consumers:** dogfood StratOS's own install first; for CleanTechHub: `scaffold --update` (expect the constitution review notice and the AGENTS.md merge review), then `issues.py migrate`, then `tracker_switch.py` dry run and `--apply`, then the cleantech_jobs#267 cleanup; start checklist for the new local-tracker project.
- **Cleanup (each needs OK):** 47 `C:\t\l3-*` sandboxes (about 1.8 GB in `C:\t`), replay worktrees, `C:\t\v5*`; keep `C:\t\l3src` and back up `.tmp\l3live` first (fast delete: robocopy from an empty directory); the throwaway repo (user's action). Update the auto-memory index.
- A human merges the PR.

## 8. Stop rules and rollback
- Quota: stop at 70% of the 5-hour window (90% ceiling), weekly under 60% for the stage.
- CI red: small plain commits and a push with OK; never force-push; never mask a flake. A stage gate that fails twice: stop, report evidence, do not widen scope.
- Rollback unit is the commit (one cluster per commit); `dist/` is regenerated, never hand-reverted.
- The PR stays draft until Stage 3 passes; no workflow merges.

## 9. Decisions
1. **Decided:** `apply-moves` blocker enforcement stays out; a backlog issue records it (refuse a move into in-progress/in-review/done while a blocker is open unless `--force`, versus display only); the badge (S3) ships.
2. **Decided in 0.2:** the 4a push follows AGENTS.md section 4 (push needs `gh`); no constitution edit.
3. **Decided:** the Stage 2 live regression is unconditional.

## 10. Review answers (v0.1 challenge)
M1 mint first and set BT-194 `in progress` (3.0, 0.4-0.5); M2 named slice BT-222 (3.0, 0.5); M3 per-action OK column and principle 6; M4 delta audit before the push (0.3); M5 tighten 4a, constitution untouched (0.2, principle 1); M6 no test removal and `floor_guard.py` before each commit (section 5); M7 `post_merge:`/`## Notes`, never `risk:`/`audit:` overload (3.0, 0.5); M8 the lead commits (principle 5). Should/nit items: S1/S2 slice mechanics and AC (0.4); S3 suite record (0.1); S4 quota (principle 8, section 5); S5 prior-body cleanup (0.5); S6 merge order (section 7); S7 plugin validators (0.1); S8 release notes (section 7); S9 RELEASING verified, not rewritten (0.7), dogfood and consumer order (section 7); S10 measured budget (principle 4); S11 unconditional live regression plus L5 (section 5); S12 badge split, Part A and DnD re-checks (section 5); S13 numeric exits (every stage); S14 throwaway-repo ownership and fix rules (section 6); S15 draft-phase CI rule and floor_guard rerun (0.1, 0.6); N1 tree-clean wording (0.1); N2 bump rule (principle 3); N3/N4 corrected table and unverified list (section 1); N5 approval items (principle 6, section 7); N6 row re-verification (section 4).

## 11. Progress log and resume point (2026-11-03 evening)

| Stage | State |
|:--|:--|
| 0 publish | **Done.** 27 commits pushed (head `035ff9f`), PR #216 draft, CI green (`verify-dist`, `install-harness-l1`), body rebuilt (post_merge cleaned, unverified list added), issues #236-#240 minted, backlog #241, #194 `in progress`, comments on #194/#221/#222, RELEASING and plan statuses updated. Delta audits `[PASS]` x3. Suite record at `035ff9f`: 1177 passed |
| 1 wording (S1 #236) | **Done locally, not pushed:** `3d59ec7` cluster A (+86 chars), `524c7d5` clusters B+C (+1318), `19f68b7` dist; `check.sh` ALL CHECKS PASSED at `19f68b7`; delta audit `[PASS]` (spec 0, std_hard 0, Watch 7, all optional); size +1404 of 1500. **Push + PR body refresh pending the user's OK** (4a ship-only for BT-222, same steps as 0.5) |
| 2 refactors (S2 #237) + badge (S3 #238) | not started; needs a 5-hour reset; live L1-L3 + L5 regression unconditional; rig `C:\t\l3src` is pinned at `66aabd7` and must be re-pinned to the final HEAD first |
| 3 real GitHub smoke (S4 #239) | not started; needs the user's explicit OK and a user-created throwaway repo with a one-job workflow |
| 4 handoff (S5 #240) | not started |

**Open Watch items (backlog, not blocking):** `PARTIAL` undefined in 4a status vocabulary (Stage 1 audit W1); `.tmp/4a-pr-body-*` cleanup never triggers with no PR; "PR host"/"local-only"/"`gh` not connected" wording mix; `ci-gate.md` §1 pin and the `Bar` header pin are weak. **Open decisions:** #241 `apply-moves` blocker enforcement; `Closes #194` is in the PR body and must be dropped before merge unless #236-#240 are done (the epic gets a second FAA when its last slice ships).

**Resume (next morning):** (1) read `usage`; the 5-hour window resets 05:40 UTC; (2) `git status` clean and `git log origin/improvement/BT-194-tracker-backend-no-map..HEAD` shows the 3 BT-236 commits; (3) with the user's OK run 4a ship-only for slice BT-222 (push fast-forward, rebuild body with the Stage 1 `test:` line from a fresh `test_gate.py record --suite BT-222 -- bash scripts/check.sh` at the new HEAD, keep PR draft), watch CI through the PR tools; (4) close S1 #236 with a comment (4a ships it with the next re-ship; confirm the status flow in `4a` steps 6-7); (5) Stage 2 per section 5 with the rig re-pinned; (6) Stage 3 only after the user creates the throwaway repo.

### 11.1 Update 2026-11-04 (Stages 1-2 pushed, Stage 3 groups 1-6 run)

| Stage | State |
|:--|:--|
| 1, 2 | **Done and pushed** (head `0ab10bf`, PR draft, CI green on both checks; #236-#238 closed). |
| 3 real GitHub smoke (S4 #239) | **Groups 1-6 done** on `PatN-git/stratos-smoke-20261030` (user-authorized): scaffold + labels + CI, issue verbs, `reconcile.py` OK/DRIFT, draft PR + `ci_gate` + `gh pr ready` + `closingIssuesReferences`, `tracker_switch.py` dry run + `--apply`, 4a ship-only, merge commit, post-merge reads. 205 verb records, 0 blocking failures. **Fixed locally (`51cb32f`, `4bd4fb7`, not pushed):** reconcile edges treat CLOSED as done (a native merge-close leaves a stale status label: found live), `closingIssuesReferences` re-check waits ~5 s (GitHub lags; seen twice), fake gh: unknown milestone refused on edit, `removeSubIssue`, resume_note `--jq`, milestone list with milestone-less issues. **Known shim gaps (backlog, not product):** `pr merge`, `stateReason/closedAt/mergeCommit` JSON fields, complex `--jq`, graphql reads, duplicate label/milestone create, benign shape drifts. **Unverified:** `ci_gate` `red`/`none` paths, draft-rule heal (`gh pr ready --undo`), `--attempt 2` CI-fix path, `gh pr checks`, Phase 2 audits and FAA on real GitHub. Evidence: `.tmp/l3live/b7-results/` (diffs-A.md, diffs-B.md). |
| 4 handoff (S5 #240) | not started |

**Correction to 11.1 (appended, history kept):** `51cb32f` and `4bd4fb7` are pushed (origin was at `d51938d`); Stage 3 and the handoff continue under `docs/plans/bt240-v5-handoff-plan.md`, not as "Stage 4 not started"; `Closes #194.` stays in the PR body by decision (below), and the "drop it" note in section 11 is void.

### 11.2 Update 2026-11-04 (late)

- **Merge decision:** #235 (BT-234) and #231 (BT-229, Google Jules removal) are folded into the v5.0.0 branch (`6514094`, `5b69100`, plus `d51938d` for the stale 3x mentions): one v5.0.0 release. #232 ships later as 5.1.0 after its fixes.
- **#241 option A lands in v5.0.0.** Section 9 decision 1 is **reversed**: `apply-moves` is unreleased, so enforcement is not a behaviour change on a released command. A move into `in progress`, `in review` or `done` is refused while a blocker is open (the verdict `ready` uses) unless `--force`; the batch is judged on its end state.
- **Plans:** `docs/plans/bt240-v5-handoff-plan.md` (handoff: owner decisions D1-D7, ordered steps, release notes, post-merge checks, cleanup, appendix of follow-ups) and `docs/plans/bt241-apply-moves-blocker-plan.md` (option A: RED tests, `issues.py` guard, docs).
- **PR #216 state (2026-11-04):** head `d51938d`, ready (not draft), CI green (`verify-dist`, `install-harness-l1`), base `main` (`132dcb8`); the body carries `Closes #194.` plus the slice closing lines. #240 and #241 are sub-issues of #194, not closing refs.
- **What remains** (`bt241` plan section 5, in order): rewrite the #241 body and flip it to `status:planned`; RED tests, GREEN guard in `src/scripts/issues.py`, reference docs (`tracker-verbs.md`, `RELEASING.md`); `build.py` and `check.sh`; the shared v5 docs debt (the `RELEASING.md` Jules line and this log); CLI re-check of DnD case 5b on `C:\t\v5dnd`; delta audit on `d51938d..HEAD`; close #240 first, then 4a ship-only for #241 (suite record, fast-forward push, Epic Check and FAA on #194, CI gate, PR body rebuild with `Closes #241.`); `agy plugin validate dist`. Then the owner merges with a merge commit (never squash) and the post-merge checks and cleanup of the handoff plan run.
- **Unverified:** the Antigravity host, `claude plugin validate` (no CLI here), board-sync timing, whether GitHub flips #231/#235 to merged with #216, the FAA cost and result on the second Epic Check.
