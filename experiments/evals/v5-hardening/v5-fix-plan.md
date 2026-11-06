---
title: PR #216 v5.0.0 clean-up — docs findings, F27, F35
version: "1.0.0"
date: 2026-10-28
---

# PR #216 clean-up plan: docs findings, F27, F35

**Goal:** close every remaining product finding from the live tests, so v5.0.0 ships clean:
- docs F30, F31, F33, F34, F36, F37, F40, F41, F42, F43;
- F27a/b/c (local post-merge);
- F35 (c) + (d) (audit convergence).

Each piece is verified by tests and a selective Haiku retest. **No push.** The plan ends with a hold for the user's push approval.

**Where:** worktree `C:\Users\patri\Dev\Stratosphere-OS\.claude\worktrees\bt221`, branch `improvement/BT-194-tracker-backend-no-map`, HEAD `35db52d` (7 unpushed commits).

**Out of scope:**
- harness F32/F38 (not requested; a later harness slice);
- F35 options (a)/(b) (rejected; `.tmp/l3live/f35-options.md`).

## Rules (every agent)
- Edit `src/`, `tests/` and `build/` only. Never `dist/` or `.agents/` by hand.
  - Root `AGENTS.md`: edit by hand only if the build does not write it (check `build/build.py` first).
- Subagents make **no git writes** (no add, commit, stash or checkout). The lead commits.
- Surgical edits; match the surrounding style.
  - Always-loaded text (AGENTS.md, rules) adds the fewest characters possible. The `tests/framework` budget tests must stay green.
- Versions: `version:` and `timestamp: 2026-10-28` bumps only where `python build/validate.py .` asks: once per file per PR, measured from the fork point.
- Behaviour change (code) → micro-tdd: RED seen, then GREEN. A doc change gets a test only where an existing test pins the old wording (update that test).
- Long shell content goes in `.tmp/` files, never inline (AGENTS §3).
- Run pytest with `TMP=C:\t TEMP=C:\t`, because of Windows MAX_PATH.

## Budget and stop gates
- **Start:** 5-hour window 68% (resets 22:30 UTC); weekly 63%. Extra usage is enabled, so **crossing 100% costs money: never do it.**
- **Before each stage:** the lead reads the usage. If the stage's estimate would push the window past 95%, stop, report and hold until the reset. **Hard stop at 97%**, whatever the stage.
- **Estimates (window points):**

  | Stage | Estimate |
  |:--|:--|
  | WP-A | 3 |
  | WP-B | 6 |
  | Grader | 2 |
  | Lead gates and commits | 4 |
  | R1 | 3 |
  | R2 | 0 |
  | R3 | 3 (optional) |
  | Lead overhead | 4 |
  | **Total** | **≈ 25** |

  This lands at about 93%, so R3 runs only if the window is ≤ 85% after R1.
- Each stop gives a stop report with usage.

## Models
| Role | Model | Writes |
|:--|:--|:--|
| Lead / orchestrator | Opus 5.5 (this session) | git, build, test_gate, commits |
| WP-A code implementer | Sonnet 5.5, effort high | `src/scripts/`, `tests/` files named below |
| WP-B docs implementer | Sonnet 5.5, effort high | `src/` markdown named below |
| Rubric grader | Haiku 5.5, effort high | read-only; report to `.tmp/` |
| R1 / R3 retest agents | Haiku 5.5, effort high | read-only (R1); sandbox only (R3) |

WP-A and WP-B run **in parallel**: their file sets are disjoint.

## Stage 0: preflight (lead)
- G0 checks:
  - HEAD is `35db52d`;
  - `git status --short` is clean on tracked files;
  - usage has been read;
  - `C:\t\l3src` is still pinned at `35db52d`.

## Stage 1a: WP-A, code (Sonnet high)
| # | File | Change | Test |
|:--|:--|:--|:--|
| F36 | `src/scripts/pr_body.py` (`FULL_SIMPLE` around line 71, the check around line 223, `is_scoped`) | `python -m unittest` and `python -m unittest discover` (optionally `-s <dir>`, `-p <pattern>`, `-t <dir>`) count as the whole suite. `python -m unittest tests.x`, or a file path, stays scoped. | `tests/scripts/test_pr_body.py` or `test_test_gate.py`: RED first, then GREEN; full and scoped cases |
| F27c | `src/scripts/reconcile.py` (`edges_cmd` / `_edge`, around lines 191–224) | On the local backend (`--all-open` or the local store path), a `[CLEAR D <- B]` line prints `cmd: python .agents/scripts/issues.py set <D> --remove-blocker <B>` instead of `# skip <D>: no GitHub issue`. GitHub output is unchanged. | `tests/workflows/test_reconcile.py` (or `test_reconcile_contract.py` if it pins the line): RED, then GREEN |

Done when the named test files pass locally. The agent writes `.tmp/v5fix/wp-a-report.md` with the files touched, the RED evidence and the GREEN run.

## Stage 1b: WP-B, docs (Sonnet high)
Each item quotes its finding. Change only the lines named.

| # | File(s) | Change |
|:--|:--|:--|
| F30 | `src/workflows/3a-version-planning.md` Phase 4 step 2; `src/references/ROADMAP-template.md` | `version:` = the plugin version, **omitted when unresolvable** (okf-protocol §5). Release tags are only `[PLANNED]` / `[ACTIVE]` / `[SHIPPED <date>]`. MAJOR/MINOR is a justification, never a tag; a cold-start first release is `[PLANNED]` (`[ACTIVE]` once it has a sprint). |
| F31 | `src/workflows/3c-sprint-planning.md` Phase 3 "Label Check" and Phase 5 step 1 | A `priority:*` band missing from the registry → `ensure_label` (user confirms, per tracker-verbs) before `set_labels`. |
| F33 | `src/constitution/AGENTS.md` §4 Granularity (and root `AGENTS.md` if the build does not write it) | Make "a standalone issue is always its own unit (never its release)" explicit, matching `_tracker_common.resolve_unit`. Fewest characters possible. |
| F34 + F35(d) | `src/references/confidence-scale.md` (check the 4a Phase 3 §3 Watch wording for consistency) | (1) **60–79 = Watch: reported, never blocking.** <60 is not reported. This matches 4a's "Spec auditor's 60-79 findings". (2) **(d):** a finding the auditor says the spec/PRD/design does not settle (ambiguity) scores < 80. It is reported as Watch, marked as a decision for the user, never a gap. |
| F35(c) | `src/references/audit-inputs.md` § Delta re-audit | Replace the file-level carry with a **frozen gap list**. Round ≥2: (1) re-check each open gap only against the bar its round-1 entry stated (its suggested fix); (2) a new ≥80 gap only on lines changed since the last audited head (in the fix diff); anything else → Watch; (3) carry every other row unchanged. Keep "the final `[PASS]` needs a row per AC" and the "history rewritten → full lean packet" fallback. |
| F35(c) | `src/workflows/3z-afk-loop.md` Step 2B dispatch (around line 64) | On attempt > 1, also pass the round-1 gap list with each gap's stated bar (the coverage map rows plus the `Gaps` entries); the auditor applies the reference's frozen-gap rule. One clause. Check 4a's re-audit text: if it restates the delta rule, point it at `audit-inputs.md` only. |
| F37 | `src/workflows/3z-afk-loop.md` Step 1B Retry (around line 32) and Step 2A (around line 55) | A re-queued `status:blocked` slice: read its last `[UNCOVERED]` / `[STUCK]` / `[FLOOR]` / `[NO-RED]` comment (the `get` read) and attach it as the prior gap report on attempt 1. |
| F40 | `src/references/post-merge-sync.md` (github dependents pass) | `--ids` = every id in the merged PR's `closingIssuesReferences`, child slices included (a slice edge such as S ← A1 must clear at merge), not only the epics and standalone issues. |
| F27a | `src/references/post-merge-sync.md` done detection | **Local backend:** the merged ids are the `features:` list of each merged PR's `stratos-pr` block (`gh pr view <pr> --json body`, the same read the follow-ups step makes, so read once and reuse); `close` each one. **Local with no PR host:** 0b cannot see a merge; the user runs `issues.py close <id>` after merging (a named gap). |
| F27b | `src/references/post-merge-sync.md` local dependents line | Run `git fetch -q origin` before `reconcile.py --edges dependents --all-open` (the local merge check uses git ancestry against `origin/HEAD`). |
| F27a | `src/references/tracker-verbs.md` § Misfits `close` line | Replace "locally 0b closes explicitly because there is no merge" with the true rule: locally, 0b closes the epics named in the merged PR's `features:`; with no PR host, the user closes them. |
| F41 | `src/references/glossary-entry-rules.md` | Remove the contradiction in "`Avoid:` … required whenever any were rejected (always in 1b and 1c), omitted otherwise". One consistent rule: required whenever a term was rejected, otherwise omitted. If 1b/1c always produce rejections, say so as a fact, not as a second condition. |
| F42 | `src/references/concept-map-template.md` (and the `src/workflows/1c-concept-map.md` lines that cite it) | The template is the **issue body**: drop "Instantiate into `docs/discovery/<slug>.map.md`" and the frontmatter block. "The tracker is the only record." |
| F43 | `src/references/concept-map-template.md`; `src/workflows/1c-concept-map.md` | Add `## Ask (verbatim)`, written at Phase 1 Chart with the user's words unedited. Converge copies it into the brief. |

- Check `tests/workflows/test_workflow_script_crosschecks.py`, `tests/framework/test_scoped_readers.py` and `tests/lifecycle/test_l3_local_scenario.py` for pinned wording. Update a pinned phrase only when the finding changes its meaning, and list it in the report.
- Done when every row is applied. The agent writes `.tmp/v5fix/wp-b-report.md` with each row's file:line and before/after, plus any pinned test updated.

## Stage 1 gate (lead): G1
- `git diff --stat`: only the files named above. No `dist/` or `.agents/` changes.
- The lead reads the whole diff against the tables, then fixes small misses inline. A big miss → one re-brief, at most.

## Stage 2: rubric grader (Haiku high, read-only): G2
- Input: this plan's tables plus `git diff 35db52d -- src tests` written to `.tmp/v5fix/diff.patch`.
- The rubric has one row per finding id: PASS/FAIL, with the quoted line that proves it. It also checks:
  - no unrelated edits;
  - F33 added the fewest characters possible;
  - F35(c) keeps the fallback and the per-AC `[PASS]` rule.
- Output: `.tmp/v5fix/grade.md`. Any FAIL → the lead fixes it, then re-grades only the FAIL rows (a second pass at most).

## Stage 3: build, validate, tests (lead): G3
1. `python build/build.py`, then `python build/validate.py .`. Fix any version-stamp request, then re-run until clean.
2. `TMP=C:\t TEMP=C:\t python -m pytest -q tests/framework tests/workflows tests/scripts tests/lifecycle`: all green.
3. Record the run: `TMP=C:\t TEMP=C:\t python .agents/scripts/test_gate.py record -- python -m pytest -q tests/framework tests/workflows tests/scripts tests/lifecycle`.

## Stage 4: commits (lead): G4
Explicit paths only. Each commit ends with the Co-Authored-By trailer. Check each with `git show --stat HEAD`.
- C1 `improvement(BT-194): …`: `pr_body.py` + `reconcile.py` + their tests (F36, F27c).
- C2 `improvement(BT-194): …`: the `src/` docs (F27a/b, F30, F31, F33, F34, F35, F37, F40, F41, F42, F43), plus root `AGENTS.md` if it was hand-edited.
- C3 `improvement(BT-194): rebuild dist`: `dist/` (and `.agents/` only if it is tracked and rebuilt).

## Stage 5: selective retest
- **Before:** re-pin the rig with `git -C C:\t\l3src checkout <C3 sha>`, so sandboxes vendor the fixed text.

### R1: F35 audit replay (Haiku high, 2 runs, read-only): G5
- **Source:** the G3 relay record in `C:\t\l3-4brkfd5x\project\.tmp\relay\`:
  - round 1: `dispatch-02a` / `result-02a`;
  - round 2: `dispatch-04a`;
  - round 3: `dispatch-06a`.
- **Setup:** for each replay, a read-only detached worktree of the sandbox project at that round's audited head (from the dispatch header). The dispatch is rebuilt from the original, with three changes:
  - the new `audit-inputs.md` and `confidence-scale.md` from `C:\t\l3src` dist;
  - the round-1 gap list and its stated bars (`result-02a`);
  - the fix diff since the last audited head.

  Results go to `.tmp/v5fix/r1-04a.md` and `.tmp/v5fix/r1-06a.md`.
- **Pass (both runs):**

  | Replay | Must hold |
  |:--|:--|
  | Round 2 (04a) | G1 judged against round 1's suggested fix only (no widened bar). AC4 < 80 as Watch, marked a user decision. No new ≥ 80 gap on unchanged lines. |
  | Round 3 (06a) | AC4 is Watch (unchanged lines, spec ambiguous), not G-AC4. Verdict `[PASS]`. |

- **Fail:** one wording fix in the reference, a rebuild, and one re-run of the failing replay only. A second fail → stop, and report it as an open design point.
- **Not covered:** a negative control (a real new gap on changed lines must still block). Rely on the G2 rubric and the lead's review.

### R2: F27 scripted probe (no model cost): G6
- Extend `C:\t\l3src\.tmp\l3live\f27_probe.py` with these asserts:
  1. Before the fetch, the local reconcile `[CLEAR]` line (if any) prints the `issues.py set … --remove-blocker` form.
  2. After `git fetch`, `[CLEAR S <- A1]` is printed with that form.
  3. The merged PR's `stratos-pr` `features:` parses to `[A]`.
  4. Following the doc steps by script (close every `features:` id, clear every `[CLEAR]`) gives A `done` and closed, S unblocked and `issues.py check` OK.
- Run it on a fresh sandbox. Pass = all asserts.

### R3 (optional, only if the window is ≤ 85% after R1): F27 live 0b (Haiku high)
- **Setup:** a fresh probe sandbox, stopped right after `merge_sim`. Haiku runs `/0b` post-merge sync from the skill on disk. File relay: the brief names `.tmp/relay/0b-out-01.md`.
- **Pass:** the agent fetches, reads `features:` from the PR body, closes A, clears S ← A1 with `issues.py`, `issues.py check` is OK, and nothing touches real GitHub.

## Stage 6: final gate and hold
1. Run full `bash scripts/check.sh` in the background (local; no quota). It must print ALL CHECKS PASSED.
2. Add a section to `.tmp/l3live/report.md` with:
   - the fixes;
   - the commits;
   - R1/R2/R3 results;
   - the usage at each gate.
3. **Hold.** Ask the user to approve the push of the commits to PR #216. Sandbox and worktree teardown (`C:\t\l3-*`, `C:\t\l3src`, `C:\t\l3main`) also waits for approval.
