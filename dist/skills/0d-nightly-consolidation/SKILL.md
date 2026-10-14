---
name: 0d-nightly-consolidation
description: "Reconcile sessions, crystallize memory, rebuild indices, and check backlog drift. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.3.0"
timestamp: 2026-10-13
---

# Nightly Consolidation

## Constraint
Do not modify files without user approval, except the report, `.last-run.json` (only through `nightly_state.py`), rebuilt indices, approved heals, and the `## Decisions` line of an earlier report (that line only).

## Phase 1: Review Sessions
1. Determine the unanalyzed delta:
   - Read `docs/nightly/.last-run.json`. If present and valid JSON, extract `last_run` timestamp.
   - Delta start = `last_run` if present; if `.last-run.json` is absent, malformed or has no `last_run`, default to `24 hours ago`.
   - Run `python .agents/scripts/nightly_state.py slugs` for the names of findings seen on earlier nights. Names only: do not read prior nightly reports here, and do not go looking for those findings.
2. Inspect the delta across all branches with fresh eyes (do not read prior nightly proposal text here to prevent anchoring on old issues):
   - Run `git log --all --since="<delta start>" --stat --no-merges` to identify tasks, branches, and files touched across the project.
   - Review session transcripts or telemetry since `delta start` for tool failures, syntax errors (e.g. shell quoting), and redundant reads.
   - **Sampling:** if the delta has more than ~15 sessions, review the 5 with the most failed tool calls plus 3 random others, and state the sample in the report.
3. Identify inefficiencies, redundant tool calls, and recurring main/sub-agent mistakes specific to this delta. Name each with a stable kebab-case slug (`shell-quoting`, `stale-path`), reusing a listed slug when it is the same failure. Run `python .agents/scripts/nightly_state.py findings --slugs <a,b,…>`; it prints `<slug> nights=N`.
4. Route each finding per `references/environment-fix-ladder.md` (escalation and hypothesis rules apply): `nights ≥ 2` is a recurrence, rung 1 or 4.
5. Report findings only: no session roster and no positive observations.

## Phase 2: Distill Plan
- Before proposing, read the `## Decisions` section (max 30 lines) of each of the last 7 `docs/nightly/nightly-*.md` reports by filename date; none yet → skip. An item the user **declined** is not re-proposed without new evidence; an accepted-but-undone item may be. A `pending` line is carried forward: it takes one slot of Phase 4's ≤5 as a forced binary. Do not read their proposal text (Phase 1 anti-anchoring).
- Output the high-density proposal to `docs/nightly/nightly-<YYYY-MM-DD>.md` (tracked — preserved so a month+ of nights can be reviewed for recurring meta-patterns), covering session/skill optimizations. **Prepend OKF frontmatter** — `type: proposal`, `title`, `description` (the index rebuild in Phase 3.5 reads both), `status: stable`, `generated: {by: 0d-nightly-consolidation, at: <ISO 8601>}`. Without it the file is non-conformant and its index row renders blank.
- Stamp the run with `python .agents/scripts/nightly_state.py stamp`. The script is the only writer of `.last-run.json` (`last_run`, `findings`, `drift`): never hand-write it, and never add a session roster to it.
- **Retention:** archive or delete `docs/nightly/nightly-*.md` reports older than ~90 days by filename date. Keep `.last-run.json` and `index.md`.

## Phase 3: Crystallize Memory
- Scan `.memory/*` (except `DESIGN.md`) for:

    | Trigger | Proposal |
    |:---|:---|
    | Duplicate or overlapping entries | Merge? |
    | `[PATTERN]` cited ≥3 times | Promote to `[LAW]` in `ARCHITECTURE.md` or `DESIGN_RULES.md`? (Not for `GLOSSARY.md`) |
    | `[ASSUMED]` cited by ≥2 distinct tasks | Promote to `[PATTERN]`? |
    | `[ASSUMED]` older than 7 days by its inline `[YYYY-MM-DD]`, unvalidated | Supersede with a `[REMOVED]` tombstone? |
- A removal is a tombstone under `## Superseded`, never a deletion (memory-protocol §3, §5): deleting leaves an ID gap.
- **Avoid-list reconciliation:** Migrate or retire `Avoid:` synonyms for superseded terms.
- Adjust plan if proposals surface. No-op audits (promotion, avoid-list, retention with nothing qualifying) collapse into one status line in the report (same line as Phase 4 step 1), never a section.
- Do not scan codebase for `Avoid:` terms.

## Phase 3.5: Rebuild Directory Indices
Run `python .agents/scripts/okf_view.py --rebuild-indices` and report its `N indices rebuilt` line. Do not rebuild by hand.

## Phase 3.6: Backlog Drift Check
1. Run `python .agents/scripts/reconcile.py --all-open --summary --out .tmp/nightly-drift.txt --keys-out .tmp/nightly-drift-keys.txt` (no `--require-gh`: this phase is advisory, and without `gh` the script prints `[local-only — GitHub not checked]` itself). It prints the summary (raw list: `.tmp/nightly-drift.txt`): counts per kind, new items verbatim, one line per kind for carried items with BT ids and ages (`[CHRONIC n]` from night 3).
2. Write that summary to the report as numbered items (`D-1`, `D-2`, …): each new item and each carried line is one `D-n`. Never paste the raw list, and write drift to the report, never to chat.
3. If the script wrote `.tmp/nightly-drift-keys.txt` (not when `[local-only`), run `python .agents/scripts/nightly_state.py drift --keys-file .tmp/nightly-drift-keys.txt`.
4. A `[CHRONIC n]` item forces one recommendation in Phase 4: heal it, or decline it; a `declined` Decisions line for that BT·kind in the last 7 reports satisfies the force. On approval, heal per `references/terminal-sync-invariant.md`. This phase invokes no lifecycle skill.

## Phase 4: Recommend & Await Direction
The report is the record; chat is a decision brief. Never restate report sections, evidence, or no-op audits in chat.
1. Link the report. One status line for mechanical phases (e.g. `indices: 7 rebuilt · retention: ok · memory: nothing qualifies`).
2. ≤5 recommendations, ranked by payoff (recurrence × cost of the failure), under two headings by route. Each `pending` line carried from Phase 2 takes a slot first and is shown as a binary (`do it` / `decline`). If forced items exceed 5, keep this order: carried `pending`, then `[CHRONIC]`, then one per drift kind; list the overflow as a one-line count (`+N more in the report`):
   - **Quick fix** — memory, docs, config or drift heal; no code. Applied in this session on approval.
   - **New issue** — this project's code, tests or tooling. Recommend `/3b-create-issue`; 0d never creates it.

   Each: `R-n` · action (one line) · why (one clause + report anchor) · size.
   - A defect in an installed StratOS skill is not an `R-n`: write it under `## Framework feedback` in the report (skill · installed version · defect · evidence · suggested fix) for the project owner to forward to the StratOS maintainer, and add a one-line notice in chat. Never file it, name a repo, or edit the installed skill.
   - A finding routed to an existing law is not a recommendation unless it recurs (`nights ≥ 2`) — then rung 1 or 4 per ladder Escalation: recommend a fix for the law not reaching agents.
   - Drift: one recommendation per heal batch, grouped by kind (every kind in the summary, e.g. status | milestone | labels | parent | blocked_by | stale_blocker | closed) with count and `D-n` range.
3. Write the `R-n` list as `## Recommendations` at the top of the report, and one `## Decisions` stub line per `R-n` before halting: `R-n · <action> · pending`, drift lines adding ` · D-a..D-b BT-x,…` (`D-n` restarts nightly, so each line carries its range and each BT id). Rewrite each carried `pending` line in its original report to `carried → nightly-<date> R-m`, so one request never lives on as two `pending` lines. Evidence and verbatim output go below.
4. Halt. Ask: *"Which recommendations should I implement? Reply with R-numbers, `all`, or `none`."*

After the user answers, rewrite each stub line in place (never append a second one): `accepted · applied <sha>` (done in this session), `accepted · deferred`, or `declined`. Phase 2 of later nights reads it.
