---
type: plan
title: 4a Audit Work Handoff
description: "Where the BT-201 audit work stands on 2026-10-20 and how to continue: unpushed commits, the open BT-204 rework, the findings so far and the next experiments."
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-20
version: "1.0.0"
---

# Handoff: 4a audit work (epic BT-201), 2026-10-20

Read this first. Evidence: [replays](../research/4a-audit-lean-replay.md), [first test results](../research/4a-audit-eval-results.md), [test plan](4a-audit-eval-strategy.md), [corpus](../research/4a-audit-eval/README.md).

## State
- **Branch** `improvement/BT-201-4a-audit-yield-log-auditor-findings-cut`, stacked on `feat/BT-190-lifecycle-status-pr-scope` (PR #193). **Draft PR #210** (base = the BT-190 branch), 4 CI checks were green at the last push.
- **3 commits are local, not pushed:** `0946c7a` (BT-204: Codex row names `gpt-6-luna`), `3d8e153` (CleanTech replay + test plan docs), `975b3eb` (corpus, `scripts/dev/audit_eval_*.py`, tests, first results).
- **BT-202 and BT-203 are shipped** (closed, `status:done`). **BT-204 was reopened** (`status:in progress`) for the Codex rework and is the only open slice of the three. BT-201 stays in progress for the Spikes BT-205, 206, 208 and slice BT-207.
- Local `.memory/BACKLOG_MAP.md` already shows BT-204 `in progress` (the file is untracked).

## To finish BT-204 and update the PR
1. `git status` should be clean. Run the full suite once at HEAD: `python src/scripts/test_gate.py record --suite BT-204 -- python -m pytest -n 6 --dist worksteal` (about 2 minutes; the installed `.agents/scripts/` copies are stale, so use `src/scripts/`).
2. `git push` (the branch exists on origin; this updates PR #210).
3. Ship-only steps per `src/workflows/4a-verify-and-ship.md` Phase 5: rebuild the PR body with `python src/scripts/pr_body.py build --slice BT-204 ... --base 10ed067 --prior-body-file <current body>` (keep the `--deviation` and `--notes` lines already in the PR; `gh pr view 210 --json body -q .body` shows them), `gh pr edit 210 --body-file ...`, comment `Shipped in PR #210 ...` on #204, set `status:done` and `gh issue close 204 --reason completed`, update `.memory/BACKLOG_MAP.md`, run the terminal sync gate.
4. When PR #193 (BT-190) merges, retarget #210 to `main` (the release bump baseline then moves: re-run `python scripts/release.py -y` and commit any bump).

## What the data says (short)
- Lean and full audit packets find the same gaps; the lean default saves about 28% tokens. The weak spot is recall, not the packet.
- On 43 labeled gaps from 13 real slices, the shipped lean auditor finds 23% at the blocking threshold (80), sees 70% at 60 or above in some run, and never sees 30%. Four clean controls: no findings at 80+.
- **Watch rows** (list findings scored 60-79, non-blocking) recover 52% of the gaps missed at 80 with about 3 items per slice and 46% matching a label: worth adding **as a list for the human at the existing ship halt**. A second-agent triage of the watch items does not work (confirms 77-90% of everything, costs about one more audit).
- **AC-literal lint:** drop (1 real hit, 19 false flags).
- **Effort split (Spec auditor high effort, Standards small tier low effort):** not tested yet.

## Next steps, in order
1. **Decide and implement watch rows** (small edit to 4a Phase 2/3 and the audit-only return in 3z: a `Watch` list, non-blocking, shown at the ship halt, count recorded in the BT-202 `audit:` line as `watch`). Needs a slice via `/3b-create-issue`.
2. **Run Test 3 (effort)** after approving spend: cases BT-187, BT-061, BT-169, BT-139, BT-118, Spec auditor at `high` effort (and `max` if `high` helps), k=2, about 1.5-2.5M tokens. Compare with the baseline in `docs/research/4a-audit-eval/results/` using `python scripts/dev/audit_eval_score.py --eval-dir <dir> --arm B` and add an arm name (for example `E`) in the result file names `<case>__E__<k>.json`. Pass rule is in the plan (flaky-gap detection up by 0.2 or recall up 5 points at no more than 1.5x tokens). Claude Code takes a per-call `effort` on the subagent dispatch; Codex uses `model_reasoning_effort`.
3. **Standards half of the effort split** needs seeded smells (not built): one scripted mutation per clean slice adds a known smell.
4. Mint slices for the plan's items (corpus builder is done; remaining: seeded-defect scripts, runner automation, telemetry `cfg` field).

## Rebuilding the working data
The snapshots and packets lived in a temp folder and are gone; rebuild with `python scripts/dev/audit_eval_build.py --out <dir>` (needs both repos checked out at the paths in `docs/research/4a-audit-eval/cases.json`). Labels, results, triage verdicts and token counts are committed under `docs/research/4a-audit-eval/`. To run more audits, give each auditor subagent `<dir>/<case>/packet.md` and `<dir>/<case>/snapshot`, and have it write `{"findings":[{"ac","conf","text"}],"files_read":n}` to `<dir>/results/<case>__<arm>__<k>.json` (the prompt used is described in the results doc); add the subagent token total to `results/tokens.csv`.

## Cautions
- The BT-203 replay AC2 ("lean re-finds every recorded gap") is not strictly met; recorded in the PR notes. The owner chose to keep lean as default and run the test plan first.
- Do not ship a change to the auditors' prompts or the 80 threshold until an experiment passes its rule.
- Labels come from fix commits via a labeler subagent (6 of 43 low confidence); treat small differences as noise.
