---
type: plan
title: 4a Audit Yield Plan
description: "Epic plan to log 4a auditor findings, cut cost per audit, consume Standards findings in AFK, and decide audit frequency from data."
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-20
version: "1.0.0"
---

# Plan: 4a audit yield (epic)

Evidence and decisions: [4a-audit-yield.md](../research/4a-audit-yield.md). Drafted by Sonnet 5.5, challenged by Opus 5.5 on 2026-10-20 (v3, slices merged); nothing here is implemented. Edit `src/` (workflows, references, scripts), never `.agents/` or `dist/`.

## Goal
Lower the token cost of the 4a audits without losing the spec-gap catches they make, and make future frequency decisions data-driven. No change to audit frequency or to the Spec confidence threshold in this epic.

## Slices
Minted 2026-10-20: epic BT-201; slice 1 = BT-202, 2 = BT-203, 3 = BT-207, 4 = BT-204; Spike A = BT-205, B = BT-206, C = BT-208.

| # | Slice | Type / size | Blocked by | Touches |
|---|---|---|---|---|
| 1 | Record auditor findings for HITL and AFK slices (kept whole above the slice ceiling by owner decision) | improvement / large | — | `src/scripts/pr_body.py` (+ test), `src/references/pr-body-and-ship.md`, 4a Phase 5 step 5 and `audit-only` gate, `src/workflows/3z-afk-loop.md` |
| 2 | Cheaper audits: lean inputs and delta re-audit | improvement / medium | — | 4a Phase 2/4, 3z Step 2B/2C, one shared reference |
| 3 | Auto-fix hard and medium Standards findings in AFK within the retry cap | improvement / large | 1, Spike A | 3z, 3d dispatch contract |
| 4 | Host-neutral `auditor_model` tier for the Standards auditor | improvement / medium | — | 4a Phase 2, 3z, a shipped reference, a framework test |
| A | Spike: classify CleanTechHub's hard breaches (mechanical vs judgment) | research / medium (fixed) | — | read-only; sample 5 slices |
| B | Spike: blind replay of known spec blockers at epic/batch level | research / medium (fixed) | — | read-only; temp worktrees |
| C | Spike: audit-policy checkpoint (per-slice vs per-unit; per-repo override?) | research / medium (fixed) | 1, B | read-only; reruns the scan prompt |

## Design notes
- **Findings record (1):** a separate top-level `audit:` block line keyed by slice id (`spec_r1, spec_final, std_hard, std_judg, phase1, std_tier`, where `std_tier` is the BT-204 tier name dispatched for the Standards auditor, absent if unset; `input` = `lean`|`full`, how the Spec auditor was fed, so BT-203's change is visible in the data; `rounds` stays on the slice row). The slice row stays byte-identical because `SLICE_RE` is anchored on `audit_rounds: (\d+)}` and an in-row field would revert old readers' rows to `PENDING`. Schema in `references/pr-body-and-ship.md`, not the 4a body. Old and new PR bodies must round-trip in both directions (CleanTechHub vendors its own `pr_body.py`). Tokens are measured offline, not logged. 3z returns and passes the counts through, or AFK slices (CleanTechHub's majority) record nothing.
- **Cost levers (2, 4):** BT-185's lean inline path cost 65k tokens vs a 493k median; BT-187's three full rounds cost 1.94M. Round 2+ carries PASS rows forward and re-checks only failed ACs plus rows the fix touched (no extra full pass: it would cost more than today's two full audits). Same gaps found at fewer tokens is the acceptance test, validated on 3 replayed slices. `auditor_model` is a named tier (for example `small`) each host maps to its own subagent model setting in a shipped reference; unsupported hosts fall back to the default silently.
- **Standards in AFK (3):** 3z consumes the Standards list; hard (Hard breach) and medium (Judgment) findings go to the 3d implementer within the retry cap; the rest stay advisory in the PR body. Mechanical rules are linted first (Spike A), otherwise hundreds of hard breaches flood the loop. Open design point: the cap, whether Standards fixes share the Spec retry budget, and the cap behavior.
- **Replay (B):** the replayable known blockers (the research doc lists 16; the case list is frozen first and drops cases with no recoverable pre-fix SHA) plus up to 4 clean controls, each checked out at its pre-fix SHA in a temp worktree; one cumulative-unit Spec audit plus a repeat per-slice audit to measure run-to-run variance. Sonnet-class subagents with lean inputs; controls and repeats only if inconclusive. Success criteria are declared before the run.
- **Checkpoint (C):** after the replay and about two weeks of slice-1 data (floor: 15 instrumented slices per repo), decide keep per-slice / per-unit Spec audit. A per-repo override (small config field read by 4a Phase 1, default = the framework rule) is added only if the instrumented data shows a material difference between repos.

## Not doing
Epic-only audits now; any diff-shape gate (saves <= ~10%); changing the Spec confidence threshold; a shadow PR-level audit on the ship path (adds minutes, sees only residual misses, duplicates the epic audit).

## Done when
Slices 1-4 are merged, Spikes A-C are closed on their Exit Criteria, and the checkpoint's follow-up work is minted via `/3b-create-issue`.
