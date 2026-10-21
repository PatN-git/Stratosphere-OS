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
- **Local commits not pushed (owner rule: push nothing until it works reliably):** `0946c7a` (BT-204: Codex row names `gpt-6-luna`), `3d8e153` (CleanTech replay + test plan docs), `975b3eb` (corpus, `scripts/dev/audit_eval_*.py`, tests, first results), `32e5010` (this handoff), then the yardstick, arm P and effort result commits (`git log origin/improvement/BT-201-4a-audit-yield-log-auditor-findings-cut..HEAD`). The full suite passed at `0946c7a`.
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
- **Yardstick check (2026-10-21):** 3 of 6 low labels are not AC gaps; on medium and high labels the baseline finds 0.32 to 0.45 at 80+ and sees 73-84% at 60+.
- **Evidence-rule paragraph (arm P):** adds to the Spec auditor prompt "quote the assertion that would fail if the AC regressed; partial, existence-only or missing is a gap; grep required literals". On 11 cases mean detection at 80+ went 0.24 to 0.38 (labels found in every run 6 to 10), controls stayed clean, tokens unchanged, watch noise about doubled (0.9 to 1.6 per run). Held on a repeat but noisy per label. This is the best candidate; not yet shippable because the 11 cases are not a clean hold-out.
- **Effort split:** Spec auditor at high effort (arm PE) on 5 hard cases: 0.12 to 0.25, inconclusive at n=12, k=1; the harness token total may exclude thinking tokens. Not adopted. Standards half (small tier, low effort) not tested.
- Nothing moves: unpinned-case and wiring-omission labels, BT-170's `if: always()` CI step, the 13 labels never seen at 60.

## Next steps, in order
1. **Arm P is not validated; stop pursuing it.** Real hold-out (3 cases): 4 found for B, 3 for P. Seeded defects (4 mutants, `scripts/dev/audit_eval_mutate.py`, 11 listed in `docs/research/4a-audit-eval/mutants.json`): identical results for B and P. The earlier gain was likely partly leakage and noise. Do not change the Spec auditor prompt.
2. **What the mutants do show:** the auditor notices 3 of 4 deleted or weakened proofs and files them as 60-79 watch items, never as gaps. So the next change is **watch rows**, not a prompt change (see next item).
3. **Watch rows slice**: a non-blocking `Watch` list (findings scored 60-79, a few lines) in the audit report shown at the ship halt, with the count recorded in the BT-202 `audit:` line as `watch`. Evidence: 17 of 33 labeled gaps missed at 80 sat in the watch band; on 4 of 4 seeded defects the auditor already produced a watch item; controls produced about 2.5 watch items per run and no findings at 80+. Not tested: whether a human acts on them. Mint via `/3b-create-issue`.
4. **Effort repeats**: inconclusive at n=12 (0.12 to 0.25); only worth more spend if the human wants a stronger default. Claude Code takes `effort` per subagent dispatch; Codex uses `model_reasoning_effort`.
4. Standards half of the effort split needs seeded smells (not built). Telemetry `cfg` field and runner automation are later.

## Parked ideas (not lost; revisit from BT-208's production data)
- **Epic-level audit test (was BT-206, closed as not planned 2026-10-21):** does one Spec audit per epic lose gaps that per-slice audits catch? Only worth running if BT-208's data makes per-unit audits attractive. Cheap to revive: pool each epic's slice labels from `docs/research/4a-audit-eval/labels/`, build a union-of-diffs packet (the only new tool), run lean audits per epic and per slice, score with `scripts/dev/audit_eval_score.py`. Both issues (#206, #208) carry the recipe.
- **Pattern log:** a project-specific list of things the auditor should check, a section of `LEARNINGS.md`, fed by confirmed watch items and post-ship fixes, capped (about 15 entries, each with its evidence), pruned when unused or covered by a lint or test. Must be handed to the auditor (the lean packet reads `LEARNINGS.md` only on demand) and measured on the seeded-defect bench before enabling.
- **Effort split / evidence-rule prompt:** not validated (see the results doc); revisit only if production escape data shows the auditor missing a class these target.
- **Seeded defects:** 7 of 11 mutants in `mutants.json` were never run (about 1.4M tokens).

## Rebuilding the working data
The snapshots and packets lived in a temp folder and are gone; rebuild with `python scripts/dev/audit_eval_build.py --out <dir>` (needs both repos checked out at the paths in `docs/research/4a-audit-eval/cases.json`). Labels, results, triage verdicts and token counts are committed under `docs/research/4a-audit-eval/`. To run more audits, give each auditor subagent `<dir>/<case>/packet.md` and `<dir>/<case>/snapshot`, and have it write `{"findings":[{"ac","conf","text"}],"files_read":n}` to `<dir>/results/<case>__<arm>__<k>.json` (the prompt used is described in the results doc); add the subagent token total to `results/tokens.csv`.

## Cautions
- The BT-203 replay AC2 ("lean re-finds every recorded gap") is not strictly met; recorded in the PR notes. The owner chose to keep lean as default and run the test plan first.
- Do not ship a change to the auditors' prompts or the 80 threshold until an experiment passes its rule.
- Labels come from fix commits via a labeler subagent (6 of 43 low confidence); treat small differences as noise.
