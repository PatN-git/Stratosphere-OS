---
type: plan
title: 0d Nightly Rework Plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-13
version: "1.0.0"
---

# Plan: make 0d nightly consolidation impactful and cheap

**Status:** Slice **BT-163** (parent BT-116, blocked by BT-162). Baseline is 0d v1.3.0 (`fix/0d-recommendation-brief`: a chat brief with a quick-fix / new-issue split). Framework fixes that 0d *surfaces* (reconcile bug, ladder, 4a blockers) are in [`nightly-evidence-lifecycle-fixes-plan.md`](nightly-evidence-lifecycle-fixes-plan.md).

## Verdict: evolve, don't rewrite
The phase skeleton is sound, and Phase 3 (memory crystallization) demonstrably works: L-005, L-006, L-010 and L-012 were promoted, as were G-016…G-027 (CleanTechHub `5ccc9cd`, `1625e8a`, `a68b37e`). What fails is **closing the loop across nights**. Recommendations evaporate, drift repeats, and recurring findings get "existing law" every time. Three mechanisms are missing: memory of what was found, memory of what was decided, and a cheap path from recommendation to fix. Add those, and push the expensive counting into scripts.

## Evidence (6 CleanTechHub reports, 07-25 → 10-13)
| Problem | Data |
|---|---|
| Low-value share of the report | 51–69% every night. Bloat moved from hand-written indices (≤10-05) to verbatim D-item dumps (10-09, 10-13). |
| Drift is chronic | 79 → 74 items; **56 lines identical** between 10-09 and 10-13; BT-215 stale since 10-05; no heal commit. |
| Decisions never recorded | No report has `## Decisions`, including the two v1.2.1 runs that required it. Decisions went into prose ("preserved per user instruction"). |
| Recurrence invisible | About 3 of 5–6 Phase 1 findings a night are repeats routed to rung 3. Anti-anchoring blinds Phase 1 to history, and nothing replaces it. |
| Framework findings never reach the owner | Skill defects (git-diff exit-1, scaffold flag hallucination) stayed buried in report prose. Nothing marks them as "forward to the StratOS maintainer". |
| Undecided memory items loop | L-017 resurfaced 10-09 and 10-13 with no decision. |
| Watermark misuse | 10-05 wrote a BOM plus a 150-line `sessions_reviewed` array into `.last-run.json` (fixed 10-09). |

## Changes

### R1 — Drift: grouped, delta-only (deterministic)
- `reconcile.py --all-open --summary`: prints counts by kind (`labels` / `parent` / `blocked_by` / `status`), marks each item **new** or **carried** against the previous night's keys, and writes the full raw list to `.tmp/nightly-drift.txt`.
- The report holds the summary plus *new* items verbatim. Carried items appear only as counts, with an age ("BT-215 blockers: 3rd night").
- Chronic carried items (≥3 nights) become one forced recommendation: heal, or accept as known and suppress.
- *Depends on* lifecycle plan F1 (false label drift) landing first.

### R2 — Cheap heals (deterministic)
- `reconcile.py --heal --kind <k> --source gh|map [--ids …]`: applies one drift kind in one direction (map edits; GitHub edits only with `gh` + approval).
- This turns "R-3: heal 74 items" into one quick fix the user can approve in one word, instead of 74 manual edits. It follows `terminal-sync-invariant.md` heal semantics and does not duplicate them.

### R3 — Cross-night memory without anchoring
- Extend `.last-run.json` to `{"last_run", "findings": {"<slug>": {"first": date, "nights": n}}, "drift_keys": [...]}`. Stable slugs (`shell-quoting`, `stale-path`, `file-reread`) carry no prose, so Phase 1 still reviews with fresh eyes.
- After Phase 1 names its findings, match the slugs. The `nights` count drives ranking, and any `nights ≥ 2` finding escalates per ladder rule (rung 1/4, never 3).
- Replaces the current "nothing else" watermark rule. Update `test_watermark_is_last_run_only`. Read the old `{"last_run"}`-only format as empty history (backward-compatible, minor bump).

### R4 — Decisions become mechanical
- Phase 2 writes `## Decisions` with `R-n: pending` per recommendation *at report time*; Phase 4 rewrites each line to `accepted` / `declined`.
- The next night's Phase 2 surfaces any still-`pending` lines as carry-over, never silently dropping them.
- A missing section becomes impossible, not merely forbidden.

### R5 — Close the routes
- **Quick fix:** applied in-session after approval, then marked `accepted · applied <sha>` in Decisions.
- **New issue:** project code, tests or tooling. Recommend `/3b-create-issue`. Host/tooling behaviour is project-local (rung 1), never a StratOS matter.
- **Framework feedback (notice only):** a defect in an installed StratOS skill (lifecycle plan F3b). The report gets a `## Framework feedback` section: one self-contained note per defect (skill · installed version · defect · evidence · suggested fix) that the project owner can forward to the StratOS maintainer. The chat brief shows a one-line notice pointing at it. 0d files nothing, sends nothing, names no repo and never edits installed skills. Not an `R-n`: there is nothing to approve in the project.
- The Phase 4 route split becomes **Quick fix / New issue / Framework feedback**. Update the v1.3.0 wording ("New issue — code, tests, or a StratOS framework change"), which currently folds framework changes into New issue.

### R6 — Phase 3 completeness
- Add the missing table row: `[ASSUMED]` with ≥2 distinct-task citations → "Promote to `[PATTERN]`?" (memory-protocol §promotion).
- An item proposed on ≥2 nights without a decision becomes a forced binary in the chat brief (L-017 case).
- No-op audits (avoid-list, retention, promotion with nothing qualifying) collapse into the single status line, both in the report and in chat.

### R7 — Scripted session pre-pass (spike first)
- Phase 1's costly part is counting: failed tool calls, repeated reads and error strings per session. A `nightly_scan.py` would emit a compact table (session · failures by kind · top re-reads · first error line) for the agent to interpret. It would also make the >15-session sampling deterministic.
- **Spike:** transcript locations and formats differ by host (Antigravity vs Claude Code). Confirm both are readable before committing to the script; otherwise keep the agent review.

## Not doing
- **A full rewrite or new phases.** The skeleton works; the gaps are state and scripts.
- **Reading prior report prose in Phase 1.** Keep anti-anchoring; slugs are enough.
- **Auto-healing drift or auto-filing issues.** These stay HITL (AGENTS.md §4, safety).
- **Any outward action toward StratOS from a consumer project.** Framework feedback is a notice the project owner chooses to forward.

## Sequencing and sizing
| Order | Item | Size | Bump |
|---|---|---|---|
| 1 | R1 (after F1) | M | 0d minor + reconcile.py |
| 2 | R4 + R6 | S | 0d minor |
| 3 | R3 | M | 0d minor (backward-compatible watermark) |
| 4 | R2 | M | reconcile.py |
| 5 | R5 | S | 0d + ladder (with F3) |
| 6 | R7 spike → build | M | new script |

Ship 1–3 as one feature PR (one release bump; per memory, prefer combined over stacked PRs).

## Success criteria (measured on CleanTechHub nightlies)
- Report size ≤ 5 KB on a typical night, and low-value share < 20%.
- Chat brief ≤ 5 recommendations, each tagged Quick fix / New issue.
- Every report has `## Decisions` with no `pending` older than one night.
- Carried drift trends to 0 within two weeks of R2; no D-item survives more than 3 nights unhealed or unsuppressed.
- A recurring finding (`nights ≥ 2`) never routes to rung 3.
- Every StratOS skill defect a nightly finds appears as a Framework feedback notice (skill + installed version + evidence), and no nightly takes an outward action.

## Implementation spec (re-planned 2026-10-13, after BT-162 and BT-164..167)
A read-only planning pass re-verified R1–R7 against the working tree. 0d is already bumped on this branch (1.2.1 → 1.3.0), so it gets no further bump. BT-162 F1 removes the 11 status-only D-items; the 10-13 drift section is still 6.4 KB of a 14.6 KB report.

**User decisions:**
- **C1:** a new `nightly_state.py` is the only writer of `docs/nightly/.last-run.json`. It needs scaffold `place()` and orphan-guard wiring.
- **C2:** `reconcile.py --heal` writes BACKLOG_MAP only. GitHub-direction fixes are *printed* as commands, which the agent runs after the user approves the R-n. The contract becomes "never writes GitHub".
- **C3:** R7 is spiked within this slice.

**Corrections to the draft above:**
- The 10-13 report already has a hand-written `## Decisions` that uses `deferred`.
- The BT-215 edges were healed on 10-13, and BT-162 F5 prevents a recurrence.
- R5 is done (`3561941`, `67e2212`). Only `applied <sha>` remains, and it folds into R4.
- R4's stub belongs in Phase 4 step 3, not Phase 2.
- R1 must follow R3 (it needs the prior-night keys), and it must cover every drift kind (`status`, `milestone`, closed, stale blocker, absent, not found).
- R2 has to amend the "detection only" contract (`reconcile.py:2`, terminal-sync-invariant).
- R6's "≥2 nights undecided" rule is subsumed by R4 carry-over. L-017 is resolved.
- One bump per file per PR.
- Missing from the draft: 0d retention globs `docs/nightly/*`, which includes `.last-run.json` and `index.md`. Restrict it to `nightly-*.md` by filename date, as 4c does.

| # | Change | Files | Tests |
|---|---|---|---|
| R3 | `nightly_state.py` (new, `src/scripts/`) owns `.last-run.json`: `{"last_run": ISO, "findings": {"<slug>": {"first","last","nights"}}, "drift": {"BT-x\|kind": {"first","nights"}}}`. A missing key or the old `{"last_run"}`-only format reads as empty history. Drift keys not seen tonight are dropped; findings are pruned 90 days after `last`. UTF-8 with no BOM. Commands: record findings (slugs), record drift keys, stamp. 0d Phase 1 reads slug names only (no prose) and reuses a slug when the finding matches; `nights ≥ 2` escalates per the ladder (rung 1/4). | new script + scaffold `place()` + orphan guard; 0d | script tests (old format, increment, prune, no BOM); rename `test_watermark_is_last_run_only` → `…_schema`, keep the `sessions_reviewed` ban |
| R1 | `reconcile.py --all-open --summary [--out .tmp/nightly-drift.txt]`. Raw lines go to `--out`. Prints a count per kind, **new** items verbatim, and carried items as one line per kind with their ages (ages come from `nightly_state.py`'s drift map). `[CHRONIC n]` at ≥3 nights becomes a forced recommendation (heal, or accept and suppress). Drift key = `BT-x\|kind`. 0d Phase 3.6 keeps the summary plus new items as `D-n`; the Phase 4 grouping covers every kind. | `reconcile.py`; 0d | new/carried/chronic/out-file tests; adjust the "verbatim" pins |
| R4 | Phase 4 step 3 also writes `## Decisions`: `R-n · <action> · pending [· D-a..D-b BT-x,…]`. After the user's answer, each line is rewritten to `accepted · applied <sha>`, `accepted · deferred` or `declined`. Phase 2 carries forward earlier `pending` lines; each takes a slot in the ≤5 and is shown as a forced binary. | 0d | stub before Halt; carry-over; vocabulary |
| R5 | Align `0d:63` to "recurs (`nights ≥ 2`) → rung 1 or 4 per ladder Escalation". | 0d | keep or update the existing assert |
| R6 | Add a Phase 3 row, "`[ASSUMED]` cited by ≥2 distinct tasks → Promote to `[PATTERN]`?", **before** the 7-day supersede row. No-op audits collapse to one status line in the report too. | 0d | row order |
| R2 | `reconcile.py --heal --kind <k> --source gh [--ids]` upserts BACKLOG_MAP cells from GitHub, keyed by BT, with no appends. The map→GitHub direction prints the `gh`/GraphQL commands. It refuses to run without `--kind` and `--ids`/`--all-open`. Amend the contract wording in `reconcile.py:2` and terminal-sync-invariant to "never writes GitHub". | `reconcile.py`, terminal-sync (already bumped) | upsert, dry-run output, refusal |
| R7 | **Spike:** map the on-disk session-transcript schemas of both hosts: Claude Code `~/.claude/projects/<slug>/*.jsonl`, and Antigravity `~/.gemini/antigravity/brain/<id>/.system_generated/logs/transcript.jsonl` plus `conversations/<id>.db`. Record the findings in this plan. If both are stable, add `nightly_scan.py`, which emits per-session tool-error counts and failing commands for 0d Phase 1. Otherwise document the gap and file a follow-up. Transcript *content* stays local; read schemas and keys only. | spike notes; maybe a new script | per findings |
| Retention | 0d's retention keeps `.last-run.json` and `index.md` and prunes only `nightly-*.md` by filename date. | 0d | pin |

**Order:** R3 → R1 → R4 + R5 + R6 + retention → R2 → R7 spike. That is two implementer passes: (a) R3 + R1 + wording, (b) R2 + R7.
