---
type: plan
title: Lifecycle Epic Execution Plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-20
version: "1.0.0"
---

# Execution plan: epic BT-190 (BT-188 → BT-191 → BT-192)

Status: agreed 2026-10-20.
- Decisions:
  - ship once at the end (Wave 4);
  - continue from wave to wave without pausing, stopping only for the ship confirmation and design questions;
  - graders are Sonnet 5.5. Inputs: `lifecycle-status-pr-scope-epic.md` (its consistency rulings C1–C9 win) and the three slice plans.

## Roles
- **Orchestrator / reviewer:** the main session (Opus 5.5). It runs `/3d` for each slice: branch, status flips, plan check, commits. It splits the work, reviews every diff against the slice plan and the rulings, and runs the gates. It is the **only writer to git**: subagents never commit, never push, and never touch `.memory/` or GitHub (AGENTS §8).
- **Implementers:** Sonnet 5.5 subagents in the shared workspace. Each one owns a **disjoint file set**. They edit `src/` and `tests/`, run their own targeted pytest, and return the fixed report below. They never edit `dist/` or `.agents/`.
- **Grader:** a fresh Sonnet 5.5 subagent per slice, read-only. It checks the slice diff against the issue's acceptance criteria and the slice plan, and scores the gaps per `confidence-scale.md`. This plays the role of the independent auditor in 3d and 4a.
- **You:** answer HITL questions, approve the single ship (push + PR) in Wave 4, and merge at the end.

Facts this plan relies on:
- `build/build.py` regenerates `dist/` only. `.agents/` is gitignored and comes from the installed copy, so the workflows we run stay stable while we edit `src/`.
- Shipping uses the *installed* (old) 4a, so BT-188 ships as `in review` under the old rule. The new behavior is live only after the merge and a `/stratosphere-update`.

## Why mostly sequential, partly parallel
- The slices share prose files (4a, 3z, 0b, terminal-sync, the BACKLOG template) and must commit in order with per-slice messages (AGENTS §4). So **slices run in sequence**.
- The **script work splits cleanly by file**, and much of it can start one slice early:
  - `pr_body.py` (BT-191) is untouched by BT-188, so it can be built during BT-188.
  - `reconcile.py --edges` (BT-192) needs BT-188's `reconcile.py` commit and BT-191's `resolve_unit`, so it can be built during BT-191.
- An early start is uncommitted work in the tree. The orchestrator commits each slice **by explicit paths** and checks the result with `git show --stat HEAD`.

## Waves

### Wave 0: set up (orchestrator)
1. `/3d BT-188` entry:
   - create `feat/BT-190-lifecycle-status-pr-scope` from `main` (C8);
   - set BT-188 to `in progress` and epic BT-190 `planned → in progress`.
2. First commit: the five `docs/plans/*` files (this plan included), `docs(BT-188): epic and slice plans for BT-190`.

### Wave 1: BT-188, close child slices at ship
| Agent | Owns (disjoint) | Work |
|---|---|---|
| I1 prose | `4a`, `3d`, `3z`, `0b`, `ci-gate.md`, `terminal-sync-invariant.md`, `memory-templates/BACKLOG_MAP.md` | slice 1 plan §3 + the abandoned-PR 0b bullet; version bumps per C7 |
| I2 script | `reconcile.py`, `tests/workflows/test_reconcile.py`, `tests/workflows/test_workflow_script_crosschecks.py` | `open_on_github`, ids-path state check, tests; the `--reason completed` crosscheck |
| I3 early start (BT-191) | `pr_body.py`, `tests/scripts/test_pr_body.py` | `resolve_unit`, `unit` subcommand, `features:`, repeatable `--close`, tests. **Not committed in this wave.** |

Gate:
1. The orchestrator reviews I1 and I2.
2. G1 grades BT-188.
3. Fix loop: at most 2 rounds per finding ≥ 80.
4. `bash scripts/check.sh` must be green.
5. Commit `feat(BT-188): …` (explicit paths, excluding I3's files). It stays local; there is no ship here (decided: ship once at the end).

### Wave 2: BT-191, release-scoped PR
| Agent | Owns | Work |
|---|---|---|
| I3 (continues) | `pr_body.py`, `test_pr_body.py` | finish and rebase on the review |
| I4 prose | both `AGENTS.md` copies, `3d` step 1, `4a` L15 and steps 1/5/8/9, `3z`, `pr-body-and-ship.md`, `feature-acceptance-audit.md`, `ci-gate.md` L16/L45, `terminal-sync-invariant.md` L20, plus the crosscheck anchor and `unit`-flags test | slice 2 plan §2 per C2/C3; AGENTS.md character budget |
| I5 early start (BT-192) | `reconcile.py` `--edges` and the adapter, `test_reconcile.py` `edge_checks` | needs I3's `resolve_unit` (it imports it). **Not committed in this wave.** |

**Note:** I4 and I1's files overlap (4a, 3z, ci-gate, terminal-sync), but Wave 1 is committed by then, so I4 edits on top.

Gate: same as Wave 1, with G2 grading BT-191. Commit `feat(BT-191): …`; it stays local.

### Wave 3: BT-192, blocker timing
| Agent | Owns | Work |
|---|---|---|
| I5 (continues) | `reconcile.py`, `test_reconcile.py` | finish and rebase on the review |
| I6 prose | `4a` steps 7–9, `3d` guard, `3z` L40/L50/L56/L107, `3c`, `0b` L27, `terminal-sync-invariant.md`, BACKLOG template `backlog-rules` block, `--edges` crosscheck test | slice 3 plan §2 per C2–C4 |
| I7 Jules | `src/experimental/jules-dispatch/dispatch.py`, `tests/jules/test_jules_dispatch.py` | merged-PR check per C5; starts once I5's `pr_merge_state` exists |

Gate: same, with G3 grading BT-192. Commit `feat(BT-192): …`.

### Wave 4: ship once (decided 2026-10-20)
1. Ask you **once** to confirm the push for all three slices.
2. Run `/4a` per slice in order (BT-188, BT-191, BT-192). Each run does its own verify pass and its own slice status flip; the first run pushes and opens the draft PR, and the later runs update it.
3. The first `/4a` run does the release bump (`scripts/release.py -y`); later runs commit a bump only if its output changed.
4. On the last run, the Epic Check sees every slice shipped: BT-190 → `in review`, the PR goes ready, and `Closes #190` is added.
5. **You merge.** After that, `/stratosphere-update` installs the new workflows.

## Implementer contract (every brief carries it)
- Read the slice plan, the epic rulings and `src/dev-skills/improve-workflows-skills/SKILL.md` first.
- Edit only the files you own. If you need a change in a file you don't own, stop and report it.
- Bump `version:` and `timestamp:` once per file per PR, using the C7 table.
- Run your targeted pytest until it is green. Do not run `build.py` or `check.sh`: the orchestrator does that once per wave, because the build is a shared write.
- Report as JSON: `{files_changed, tests_run, tests_passed, deviations_from_plan, questions, noticed_not_touched}`.
- Questions with a design impact go to the orchestrator, which answers from the plans or asks you.

## Review loop (per slice)
1. **Orchestrator diff review:**
   - the diff matches the slice plan and C1–C9;
   - no edits outside the owned files;
   - protected tokens are kept verbatim;
   - version bumps match C7.
2. **Grader:** a fresh-context AC audit. Findings ≥ 80 go back to the owning implementer, at most 2 rounds. After that, the orchestrator decides, or asks you if the finding has a design impact.
3. **Gates:** targeted pytest, then `bash scripts/check.sh`, then commit by explicit paths, then `git show --stat HEAD`.

## Budget and timing (estimates)
- About 10 subagent runs: 7 implementers and 3 graders. The earlier planning runs used about 135–240k tokens each, so expect roughly 1.5–2M tokens in total.
- Wall clock: about 1–2 h per wave including `check.sh`, plus your ship confirmations.

## Stop conditions
- `check.sh` fails twice after a fix: halt and report.
- A grader finding ≥ 80 is still open after 2 rounds and has a design impact: ask you.
- Any need to touch `main`, force-push or merge: never. Report instead.
