# PR #216 live AFK test — report

## v5 fix round: docs findings, F27, F35 (2026-10-28)
**Every remaining product finding is fixed and verified.** Plan: `.tmp/l3live/v5-fix-plan.md`.

The work is three local commits on `improvement/BT-194-tracker-backend-no-map`. They are **not pushed**.

| Commit | Content |
|:--|:--|
| `95fa506` | code: F36, F27c |
| `8ac3e6c` | docs: F27a/b, F30, F31, F33, F34, F35c/d, F37, F40, F41, F42, F43 |
| `dba6a63` | dist |

| Gate | Result |
|:--|:--|
| G1 lead diff review | only the planned files changed; WP-A (Sonnet high) and WP-B (Sonnet high) |
| G2 rubric (Haiku high) | 15/15 PASS. X5 (an ambiguity at 40–59 was both reported and not) fixed. X1 (0b clause) kept: the brief allowed it. |
| G3 build, validate, tests | VALIDATION OK; 979 passed (framework, workflows, scripts, lifecycle), recorded. Version bumps: concept-map-template 2.1.0, confidence-scale 1.2.0, ROADMAP-template 2.1.0, audit-inputs 1.1.0. |
| R1 F35 replay (Haiku high, 2 runs) | PASS, details below |
| R2 F27 scripted probe | PASS, 6/6 asserts: features → A closed done; fetch → `[CLEAR S <- A1]` with the `issues.py` cmd; S unblocked; check OK |
| R3 F27 live 0b (Haiku high) | PASS: features: → close A → `git fetch` → reconcile → `issues.py set --remove-blocker` → `CHECK-OK`; verified from `sbx.log` and the store |

**R1 details:**
- Round 2 is `[UNCOVERED]`. G1 is still open against its own round-1 bar: the round-2 code ran 2 of the 4 reason paths, so this is a real gap, not a widened one.
- AC4 stays Watch, marked as a user decision.
- Round 3 is `[PASS]`: AC4 Watch (70) is "a decision for the user", not G-AC4.
- Under the new rules the slice ships at attempt 3 instead of blocking. That corrects the f35-options estimate of attempt 2.

**Build catch:** the first wording of the tracker-verbs Misfits line linked `references/post-merge-sync.md`, which made the build copy it into about 10 skills. The path was dropped from the line, so only 0b bundles it.

**Logged, not fixed** (older wording, not from this round):
- R3 unclear notes:
  - U1: 0b's query names `closingIssuesReferences` (the local source is only in post-merge-sync);
  - U2: the `vX.Y.0` release wording for the `/3a` suggestion;
  - U3: `issues.py check` is whole-store;
  - U4: the "this session" vs `Last Sync` window.
- `okf-protocol.md` still registers `concept-map` at `docs/discovery/*.map.md`. Kept for v4 maps until `issues.py migrate`.
- Harness F32/F38 are not done.

**Usage:** 5-hour window 68% → 83%, with no extra usage. Full `scripts/check.sh`: ALL CHECKS PASSED (install-harness 155/0).

**Follow-up (same day):** the 0b nits U1–U4, the okf `concept-map` legacy row and F38 (shim assignee dedupe) are fixed: `8d50d32` + dist `7567093`. Gates: lifecycle integration 292 passed; recorded suite 979 passed. Window 87%. Still open: F32 (strict shim labels).
**F32 (after the reset):** fixed. The fake gh refuses unknown labels (case-insensitive, as GitHub) and the seed creates the taxonomy: `10786d3`. The stricter fake exposed a **product bug**: `tracker_switch --apply` never created labels, so a switch to a GitHub repo without them stopped at the first `gh issue create --label`. It is fixed in `7480eb8` (`ensure_labels`: list once, create only the missing ones, case-insensitive, skip when nothing is pending); dist `d07679c`. Sonnet high implemented. The Haiku high review found 1 FAIL (a vacuous idempotency test), and the lead fixed it RED to GREEN, plus the case-insensitivity. Gates: tracker_switch 17 passed; lifecycle integration 299 passed; recorded 982 passed (one Windows 0xC0000005 crash in `test_test_gate`, 3/3 green on re-run); scripted probe `f32b_probe.py` PASS (7 labels created before the first issue; re-run creates nothing). The branch is 15 commits ahead, unpushed.
**Shipped (4a, Sonnet 5.5 high):** the audit-only pass returned [PASS] (spec 0, std_hard 0; Watch R1-5 was a plan-row error, fixed in `7c9b664`). The ship-only pass pushed the branch to `7c9b664` (PR #216): CI green (verify-dist, install-harness-l1), body rebuilt with the same 10 Closes lines and 9 slice rows plus a deviation line, terminal gate MIRROR-OK. Not merged. Spec: `docs/plans/pr216-live-test-fixes-plan.md`.
**F5 closed:** the pinned Claude Code CLI 2.1.170 `--help` lists `--effort <level>` (low, medium, high, xhigh, max). session.py now names it, and run-L3 accepts only those values: `5800852`, pushed. Lifecycle 299 passed. Claude only: other hosts would need their own harness driver.

**Open sandboxes:**
- `C:\t\l3-1yrze0x6`, `C:\t\l3-d8um5m7b` and `C:\t\l3-q979zjg3` (F27 probes);
- the replay worktrees `C:\t\l3-4brkfd5x\r1-04a` and `\r1-06a`.

The rig `C:\t\l3src` is pinned at `dba6a63`.

## Follow-up verdict: the phases not yet driven (2026-10-28)
**Every planned stage ran and passed its checks.** That covers 3a, 3c, 3z → 3d → 4a (audit and ship), merge + 0b post-merge sync, the BT-222 glossary writers in 0b, 1b and 1c, and 1c chart → converge on the local tracker. The run found 15 new findings (F28–F43; F29 withdrawn). One is fixed. One is a design question: **F35, audit non-convergence under 3z** (see below). The rest are minor wording or harness items.

| Stage | Result | Checks |
|:--|:--|:--|
| G1 3a (github) | PASS after the F28 fix (35db52d) and a re-run | stage_checks 16/16 |
| G2 3c (github) | PASS | 16/16 |
| G3 3z run 1 | Shipped nothing, correctly. BT-002 was blocked at the 3-attempt cap after 3 `[UNCOVERED]` rounds (F35). S got `[SKIP-DEP]`. | blocked path verified by hand |
| G3 3z re-run | PASS: genuine `[PASS]`, PR #6, Epic Check R, FAA CLEAN, CI green, ready flip, epic `in review`, S edge KEEP. The user's override for shipping imperfect work was never needed. | 21/21 |
| G4 merge + 0b | PASS: epic done, S's edge CLEAR (via F40 judgment), Last Sync, `/3a` suggestion, BT-222 entry `[[G-001]] Bucket key` | 19/19 |
| B1 1b relay (local) | PASS: glossary hash unchanged after "enough"; two entries written only after approval | harness check_1b [ok] |
| B2–B4 1c (local) | PASS: map + 9 wired tickets; converge with `concept-map:` set; glossary hash unchanged at the gate; 2 entries with `Avoid:` from the resolutions; map closed done | scripted asserts |

**Findings to act on:**
- **F35 (design call needed):** each 3z retry re-audits every row, because the delta rule is file-level. Gaps appear late on unchanged code, so a slice can hit the cap. Options: a row-level delta, late gaps on carried rows become Watch, or a frozen gap list.
- **Minor docs** (one batch):
  - F30: ROADMAP version fallback;
  - F31: 3c ensure_label for priority;
  - F33: AGENTS §4 standalone unit wording;
  - F34: Watch band 60–79 vs confidence-scale;
  - F36: test_gate accepts `python -m unittest`;
  - F37: re-queued slice gets its gap report;
  - F40: post-merge dependents include child slices;
  - F41: `Avoid:` "always in 1b/1c" wording;
  - F42: 1c map template vs tracker-only;
  - F43: 1c stores the Ask verbatim.
- **Harness:**
  - F32: shim accepts unknown labels;
  - F38: shim duplicates assignees.
- **Still suspected, not driven:** F27 (local post-merge sync cannot find a merged epic).

**Rig learnings:**
- Subagent hand-backs are summarized, so relays must go through files (`dispatch-NN` / `result-NN`, `*-out-NN` / `user-NN`).
- A 4a pass relays its own auditors, including the FAA.
- The Spec auditor ran on Haiku. A host's "default" model would be stronger, which likely contributed to F35.

**Containment:** the real repo's remote refs are unchanged. The account's event feed shows #217 label/assign events (16:03–16:31Z, an unrelated `/0f` issue, before this follow-up started) and a delayed PushEvent from 01:29Z. Neither came from a sandbox; sandboxes only reach the fake gh.

**Cost:** 5-hour window 1% → 60% (one window; no extra usage), weekly 52% → 62%. About 45 Haiku runs.

**State:**
- The PR branch has 7 unpushed commits: e41d23a … de1ad3a, plus 35db52d (F28).
- Sandboxes `C:\t\l3-e28jbsvr`, `C:\t\l3-4brkfd5x`, `C:\t\l3-1o9xjlx2` and `C:\t\l3-j6med60n` are kept for inspection.

---

## Final verdict, after the fix round (2026-10-28)
**PR #216 is ready, from the live-test side.**

**Fixes:** every finding from the first run has been fixed and verified, with two exceptions:
- F21(c) was already correct.
- F5's `--effort` flag name is not yet confirmed against a real CLI.

The fixes are 5 commits on `improvement/BT-194-tracker-backend-no-map` (e41d23a … 7ead6d5). They are local and **not pushed**.

**Gates:**
- related tests: 1245 passed;
- full `scripts/check.sh`: ALL CHECKS PASSED (1008 + install-harness 155).

**Light Haiku re-test on fresh sandboxes: all green.**
- Scripted R0–R8 confirm each local-id fix and the resume-note file.
- The `tracker_switch` hardening works: milestones are ensured first, body ids are rewritten, the claim becomes an assignee, and a re-run changes nothing.
- `issues.py` refuses under `tracker: github`.
- The fake `gh` now supports labels and `pr list`.
- Live 0b → 0a now hands off end to end on the local tracker.

**Containment:** no real-GitHub activity across both rounds.

**Still open (not live-tested):**
- 3a, 3c, 3z, 4a, post-merge sync;
- BT-222 glossary writer rules live;
- real GitHub API behaviour, notably milestone creation and assignees, against an actual repo.

---

## First run (findings below are from before the fixes)

**Run date:** 2026-10-28
**Code:** PatN-git/Stratosphere-OS#216 @ `9a1b511`, pinned at `C:\t\l3src`
**Agent under test:** Haiku 5.5, effort high, 10 subagent runs, fully AFK
**Orchestrator:** Opus 5.5. It re-ran every key check itself.

**Detail:**
- Findings table, per-stage log and learnings: `.tmp/l3live/findings.md`
- Every in-run fix: `.tmp/l3live/in-run-fixes.patch`

## Verdict
- **GitHub mode works.** Two checks passed, and nothing broke compared with today:
  - live 3b minted 4 slices with parents, blockers and a milestone, and the `--expect` gate passed on the first attempt;
  - reconcile, ice_read and the removed-flag contract all behaved as specified.
- **The local tracker mostly works, but two bugs break it at the session hand-off and in recording suites.** Both were fixed in-run so the test could finish, and both need real fixes plus tests on the PR:
  - **F16:** a local resume note never reaches `.memory/resume/<id>.md`, so the next session finds no note. BT-218 is broken on the local backend.
  - **F14:** `test_gate.py record --suite` rejects `BT-LOCAL-*` ids, so 3d/0b/4a get no reusable suite record.
- **One more confirmed local bug, not fixed: F15.** `pr_body.py build` rejects local ids for `--epic`/`--parent`/`--slice`, so a local project that ships PRs cannot build its PR body.
- **Containment held.** There were no new events on the GitHub account, and the real repo's remote and local refs are unchanged.

## What passed (verified by the orchestrator)
| Area | Result |
|:--|:--|
| Baseline | `scripts/check.sh` at `9a1b511`: 1001 passed + install-harness 155/0 |
| `issues.py` local | create (`-2` on a clash), set, children, blockers, ready (`[BLOCKED]`), comment, claim compare-and-set (exactly one `[CLAIMED]` across two worktrees), close (archive) and reopen, check, sync (`LOCAL-ONLY`, `MERGED` across two clones). Issue files live only on `throwaway/issues`. |
| v4 → v5 upgrade | `scaffold --update`: tracker NOTE and `needs_review_constitution`. Then `issues.py migrate`: 4 issues with edges and ICE, map archived, `check` OK. |
| `validate_memory` | STATUS over 3,000 chars, tracked STATUS, glossary field other than `Avoid:`/`Source:` (BT-222); a prose label inside a definition correctly does not warn |
| Live 3b local | 4 slices via verbs, `check_3b` OK, no GitHub call |
| Live 3d local | claim (`claimed_by` = branch), epic `in progress`, session line, 2 commits, nothing pushed; `check_3d` OK |
| Live 0b local | resume note, STATUS own field only, suite reused, lint clean, tracker branch **not** pushed |
| Live 0a local | started on `master`, **followed the task's branch**, read the resume note (after the F16 fix), reported the right next step; `check_0a_second` OK |
| `tracker_switch` | dry run writes nothing; killed mid-apply leaves 4/5 issues and `tracker: local`; resume creates no duplicates and writes `tracker: github` last; re-run idempotent |
| GitHub gate | reconcile `--expect` gives OK or DRIFT; `--edges` and `--with-edges` work; `--heal`, `--summary` and `--require-gh` exit 2; unknown tracker exits 3 |
| Live 3b GitHub | `addSubIssue` and `addBlockedBy`, `ensure_milestone`, `[MIRROR-OK …]` first attempt; `check_3b` OK |

## Findings to fix (product)
| # | Severity | Fix in-run? | One line |
|:--|:--|:--|:--|
| F16 | major | yes | `issues.py comment` never writes the local resume-note file the docs and load-memory read |
| F14 | major | yes | `test_gate.py` suite id regex rejects `BT-LOCAL-*` |
| F15 | major | no | `pr_body.py build` id checks reject `BT-LOCAL-*` (`--epic`, `--parent`, `--slice`) |
| F21 | minor (suspect major) | no | `tracker_switch` keeps `BT-LOCAL` text in migrated bodies and comments, miscounts rewritten files, drops the claim. It never ensures milestones; real `gh` probably fails there (unverified). |
| F13 | minor | no | 3b template, pre-mint guard and `ensure_milestone` lack the local id/milestone form |
| F19 | minor | no | `wip` local form undocumented; 0a doesn't say whether to resume the epic or the slice; 0a's "pull" when the branch has no upstream |
| F18 | minor | no | 0b: `Last Sync` window when empty, and when the sync is skipped |
| F22 | minor | no | `issues.py` ignores `tracker:`; after a switch it serves the stale local store |
| F25 | minor | no | GitHub 3b has no scoped read for the parent epic; Haiku read up to 500 issues with bodies |
| F7 | minor | no | `tracker-verbs.md` says ICE comes from `I:`/`C:` lines; the parser reads the `**Impact:**` bullets |
| F8, F9 | minor | no | the update error gives no non-interactive path; the update never untracks a tracked STATUS |
| F23 | minor | no | a killed `tracker_switch` can leave a `gh` child running; the SWITCH-FAIL message is empty |

## Harness findings
- **F1:** the expired credential passes preflight.
- **F2:** the responder answers the 3b/3z gates wrongly.
- **F3:** the budget is checked before the sentinel.
- **F4/F20/F24:** shim gaps. Milestones are fixed in-run; still missing are labels, `pr list/edit`, complex `--jq`, and the CI fields.
- **F5:** no effort passthrough.
- **F10:** fresh sandboxes have an unborn `master`.
- **F11:** sbx encoding (fixed in-run).
- **F12:** the session-line regex is numeric-only (fixed in-run).
- **F17:** `check_0b` needs `pr list` and a tool stream.

## Not covered
- **Workflows not driven:** 3a, 3c, 3z, 4a (audit and ship), post-merge sync, 1b/1c/2a/2b, 0d.
- **BT-222 glossary writer rules live:** 0b raised no term.
- **Real GitHub API:** the fake `gh` is lenient (see F21's milestone suspicion).

## Fidelity limits
- Skills were read from disk by Agent subagents, not loaded by the host.
- Nested subagents ran inline.
- sbx guards commands, not file tools; the canary was the backstop.

## Cost
- **Quota:** 5-hour window 3% → 22%, weekly 38% → 41%; no extra-usage spend.
- **Haiku:** 10 runs, about 1.5M tokens in total, 1.5–9 min each.
- **Wall time:** about 2 h 15 min, including the five stops.

## Suggested next steps (not done)
1. **One slice on PR #216 for the local-id bugs:** F16 + F14 + F15, each with a regression test. `in-run-fixes.patch` has the first two.
2. **Small doc slice:** F13, F19, F7, F18.
3. **tracker_switch hardening:** F21 (ensure milestones, rewrite ids in bodies), F22, F23. Verify the milestone failure against a real throwaway repo.
4. **Harness slice:** F1–F5, F10, F12, F17, F20, F24.

## B3/B4 and fix rounds (2026-11-03, code under test 7d535b7 then e853baf, c0a87c3, 66aabd7)
- **B3 (first pass):** L1 33/33, L2 29/29, L4 39/39, L5 20/21, L3 incomplete. Triage (`b3-triage.md`): Haiku over-reported (25 of 59 claims were not defects). Must/should fixes shipped as 7587b38 + dist e853baf (parse_expect comment lines, 3z audit-object mapping, local tracker push after the gate, FAA/0d/2a clauses).
- **B4 (F35 round 2, 4 Haiku runs):** convergence case 2/2 PASS (frozen gap closed against its round-1 bar, unchanged-line concerns stay Watch 62-75); negative control 2/2 `[UNCOVERED]` (new defect on changed lines, confidence 85-92). n=2 per case, one slice, hand-built round-1 map.
- **L3 re-run 1 (b3-results2):** 42/51; the FAA returned GAPS because the fixture PRD claimed more than A1-A3 delivered. Triage 2 (`b3-triage2.md`): 0 must, 8 should; shipped as 98ad6eb + dist c0a87c3 (FAA scale pointer and scope, 4a audit-only Phases 1-3 contract, 3d any-glob, micro-tdd guard carve-out, delete-if-absent wording, fake gh no-PR refusal).
- **L3 re-run 2 (b3-results3, narrowed PRD):** L1 33/33, L2 29/29, L3 49/51 (50/51 with the rig false positive neutralised). Verified live: FAA CLEAN, `gh pr ready`, CI gate, epic flip to `in review`, 3z Phase 4 report, sentinel, 4a audit-only returning verdict + coverage_map. Found and fixed a real bug: `reconcile.py --expect-file` joined with `;` so a leading `#` comment line failed (655f9eb + dist 66aabd7), plus an FAA verdict-word clause and a 3z CI-gate ownership clause.
- **Unverified:** the F35 retry loop on a live 3z run (all three slices passed round 1; B4 replays cover the rule); real mouse drag-and-drop on the board; real GitHub beyond the B1 smoke; wording edits since 7587b38 are pinned by text tests only.
- **Cost:** Haiku runs this stretch: 4 (B4) + 26 + 24; 5-hour window ended near 56-60% after the re-runs.
