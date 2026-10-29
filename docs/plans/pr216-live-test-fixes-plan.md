---
type: plan
title: PR 216 Live-Test Fixes Plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-28
version: "1.1.1"
---

# Plan: PR #216 (v5.0.0) live-test fixes

**Status:** implemented on `improvement/BT-194-tracker-backend-no-map` in the 15 local commits `e41d23a` … `d07679c`. Nothing is pushed.

- **v1.0.0:** the docs findings, F27 and F35.
- **v1.1.0, revised:** adds the follow-up rounds (0b wording, okf row, F38, F32) and the product bug F32 exposed (F32b).

**Source:** two live AFK tests of PR #216, run in sandboxes with a fake `gh` and Haiku 5.5 agents. The records are outside the repo, in the main checkout's `.tmp/l3live/`:
- `report.md` (verdicts);
- `findings.md` (F1–F43);
- `v5-fix-plan.md`, `f35-options.md` and `f32b-plan.md`.

## Scope
These fix commits sit inside epic BT-194's ship unit; there is no issue of their own. Every row below is an acceptance criterion: verifiable from the diff or a named test.

**Out of scope:**
- F5: the `--effort` flag name of the L3 harness CLI driver is unconfirmed against a real CLI (harness only).
- F21(c): already correct.
- F35 options (a)/(b): rejected in `f35-options.md`.

## Round 1: first live run (commits `e41d23a`, `d8e62f7`, `6435c6e`, `09559c5`, `7ead6d5`, `de1ad3a`)
| AC | Finding | Must hold |
|:--|:--|:--|
| R1-1 | F14 | `test_gate.py record --suite` accepts `BT-LOCAL-*` ids. |
| R1-2 | F15 | `pr_body.py build` accepts `BT-LOCAL-*` for `--epic`, `--parent` and `--slice`. A local id gets no `Closes` line. |
| R1-3 | F16 | `issues.py comment` with a resume note writes `.memory/resume/<id>.md`; `load-memory` reads it there. |
| R1-4 | F21 | `tracker_switch.py`: ensures milestones before any issue create; rewrites `BT-LOCAL-*` ids in created bodies and comments; a claim becomes an assignee; a re-run is idempotent. |
| R1-5 | F22 | `issues.py` refuses every command under `tracker: github`, `migrate` included (the update runs `migrate` only for `tracker: local` or no key). |
| R1-6 | F7, F13, F18, F19, F25, F8, F9 | Docs give: the local id and milestone forms; ICE from the `**Impact:**`/`**Confidence:**` bullets; 0b `Last Sync` rules; 0a resolves to the leaf and skips the pull without an upstream; 3b reads the epic with a scoped read; the update error names its decline path; the update untracks a tracked STATUS. |
| R1-7 | F1–F4, F10, F12, F17, F20, F24 | L3 harness: credential expiry, a phase-scoped responder, the sentinel before the budget, fake `gh` labels/milestones/`pr list`/`pr edit`/`reopen`/CI fields, a born `master`, a local session line, `check_0b` accepting a skipped merge sync. |

## Round 2: follow-up live run (commits `35db52d`, `95fa506`, `8ac3e6c`, `dba6a63`)
| AC | Finding | Must hold |
|:--|:--|:--|
| R2-1 | F28 | 3a Phase 4 step 3: `set_milestone` on each placed epic or standalone issue, never on an epic's slices. |
| R2-2 | F36 | `pr_body.py`: `python -m unittest` and `discover` (only `-s/-p/-t`, `-v/-q`) are the whole suite; a module, a file or `-k` is scoped. Tests in `test_pr_body.py`. |
| R2-3 | F27c | `reconcile.py --edges`: a `[CLEAR]` edge between local ids prints `cmd: python .agents/scripts/issues.py set <D> --remove-blocker <B>`. GitHub output is unchanged. Test in `test_reconcile.py`. |
| R2-4 | F27a | `post-merge-sync.md`: local merged ids = each merged PR's `stratos-pr` `features:` list, then `close`; local with no PR host is a named gap. The tracker-verbs Misfits line agrees. |
| R2-5 | F27b | `post-merge-sync.md`: the local dependents pass runs `git fetch -q origin` first. |
| R2-6 | F40 | `post-merge-sync.md`: the github dependents `--ids` = every id in the merged PRs' `closingIssuesReferences`, child slices included. |
| R2-7 | F35c | `audit-inputs.md` § Delta re-audit freezes the round-1 gap list: (1) an open gap is judged only against its stated bar; (2) a new ≥ 80 gap only on changed lines, else Watch; (3) other rows carried. The per-AC `[PASS]` rule and the history-rewritten fallback are kept. The 3z Step 2B dispatch passes the gap list with its bars. |
| R2-8 | F34, F35d | `confidence-scale.md`: 60–79 = Watch (reported where the workflow has a Watch list, never blocking); 40–59 not reported; an ambiguity the spec does not settle scores at most 79 (Watch, marked as a decision for the user). 4a's Watch text agrees. |
| R2-9 | F37 | 3z: a re-queued `status:blocked` slice carries its last `[UNCOVERED]`/`[STUCK]`/`[FLOOR]`/`[NO-RED]` comment as the attempt-1 gap report. |
| R2-10 | F30 | 3a and the ROADMAP template: `version:` is omitted when unresolvable; the tags are only `[PLANNED]/[ACTIVE]/[SHIPPED <date>]`; MAJOR/MINOR goes in the rationale. |
| R2-11 | F31 | 3c: a missing `priority:*` band is `ensure_label`ed (the user confirms) before `set_labels`. |
| R2-12 | F33 | AGENTS §4 (both copies, identical): "a standalone issue is itself". The always-loaded budget stays green. |
| R2-13 | F41 | `glossary-entry-rules.md`: one non-contradictory `Avoid:` rule. |
| R2-14 | F42, F43 | The 1c map template is the issue body (no file path, no frontmatter) with `## Ask (verbatim)`, written at Chart and copied into the brief at Converge. |

## Round 3: follow-ups (commits `8d50d32`, `7567093`, `10786d3`, `7480eb8`, `d07679c`)
| AC | Finding | Must hold |
|:--|:--|:--|
| R3-1 | 0b U1 | 0b merge-time sync: local merged ids come from the `features:` list. |
| R3-2 | 0b U2–U4 | `post-merge-sync.md`: one window (the 0b PR query's); a release's epics are listed by milestone `vX.Y.0` on both backends; `issues.py check` is the whole local gate. |
| R3-3 | okf | `okf-protocol.md`: the `concept-map` file row is marked v4 legacy (`issues.py migrate`). |
| R3-4 | F38 | The fake `gh` keeps assignees unique. |
| R3-5 | F32 | The fake `gh` refuses an unknown label on `issue`/`pr` `create`/`edit` (exit 1, nothing changed); names match case-insensitively; the seed creates the taxonomy. |
| R3-6 | F32b | `tracker_switch.py --apply` ensures the labels the to-be-created issues carry before the first create: one list (`--limit 1000`), case-insensitive, nothing created twice, no read when nothing is pending; a failure stops with `[SWITCH-FAIL]` before any issue. Tests in `test_tracker_switch.py`. |

## Verification already run (lead)
- **Retests:**
  - R1 F35 replay (Haiku): round 2 `[UNCOVERED]` on its own bar, round 3 `[PASS]` with AC4 as Watch.
  - R2/R3 F27: a scripted probe and a live Haiku 0b run.
  - F32b: scripted probe `f32b_probe.py`.
- **Tests:**
  - recorded run of framework, workflows, scripts and lifecycle: 982 passed;
  - `-m integration tests/lifecycle`: 299 passed;
  - full `scripts/check.sh`: ALL CHECKS PASSED.
