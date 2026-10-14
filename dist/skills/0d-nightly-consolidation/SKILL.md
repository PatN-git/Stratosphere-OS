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
Do not modify files without user approval, except the report, `.last-run.json`, rebuilt indices, and approved heals.

## Phase 1: Review Sessions
1. Determine the unanalyzed delta:
   - Read `docs/nightly/.last-run.json`. If present and valid JSON, extract `last_run` timestamp.
   - Delta start = `last_run` if present; if `.last-run.json` is absent or malformed, default to `24 hours ago`.
2. Inspect the delta across all branches with fresh eyes (do not read prior nightly proposal text here to prevent anchoring on old issues):
   - Run `git log --all --since="<delta start>" --stat --no-merges` to identify tasks, branches, and files touched across the project.
   - Review session transcripts or telemetry since `delta start` for tool failures, syntax errors (e.g. shell quoting), and redundant reads.
   - **Sampling:** if the delta has more than ~15 sessions, review the 5 with the most failed tool calls plus 3 random others, and state the sample in the report.
3. Identify inefficiencies, redundant tool calls, and recurring main/sub-agent mistakes specific to this delta. Route each finding per `references/environment-fix-ladder.md` (escalation and hypothesis rules apply).
4. Report findings only: no session roster and no positive observations.

## Phase 2: Distill Plan
- Before proposing, read the `## Decisions` section (max 30 lines) of each of the last 7 `docs/nightly/nightly-*.md` reports by filename date; none yet → skip. An item the user **declined** is not re-proposed without new evidence; an accepted-but-undone item may be. Do not read their proposal text (Phase 1 anti-anchoring).
- Output the high-density proposal to `docs/nightly/nightly-<YYYY-MM-DD>.md` (tracked — preserved so a month+ of nights can be reviewed for recurring meta-patterns), covering session/skill optimizations. **Prepend OKF frontmatter** — `type: proposal`, `title`, `description` (the index rebuild in Phase 3.5 reads both), `status: stable`, `generated: {by: 0d-nightly-consolidation, at: <ISO 8601>}`. Without it the file is non-conformant and its index row renders blank.
- Update `docs/nightly/.last-run.json` to `{"last_run": "<ISO 8601>"}` and nothing else.
- **Retention:** archive or delete `docs/nightly/*` entries older than ~90 days so the meta-review window stays bounded.

## Phase 3: Crystallize Memory
- Scan `.memory/*` (except `DESIGN.md`) for:

    | Trigger | Proposal |
    |:---|:---|
    | Duplicate or overlapping entries | Merge? |
    | `[PATTERN]` cited ≥3 times | Promote to `[LAW]` in `ARCHITECTURE.md` or `DESIGN_RULES.md`? (Not for `GLOSSARY.md`) |
    | `[ASSUMED]` older than 7 days by its inline `[YYYY-MM-DD]`, unvalidated | Supersede with a `[REMOVED]` tombstone? |
- A removal is a tombstone under `## Superseded`, never a deletion (memory-protocol §3, §5): deleting leaves an ID gap.
- **Avoid-list reconciliation:** Migrate or retire `Avoid:` synonyms for superseded terms.
- Adjust plan if proposals surface. Skip silently if nothing qualifies.
- Do not scan codebase for `Avoid:` terms.

## Phase 3.5: Rebuild Directory Indices
Run `python .agents/scripts/okf_view.py --rebuild-indices` and report its `N indices rebuilt` line. Do not rebuild by hand.

## Phase 3.6: Backlog Drift Check
Run `python .agents/scripts/reconcile.py --all-open` (no `--require-gh`: this phase is advisory, and without `gh` the script prints `[local-only — GitHub not checked]` itself). Write its findings verbatim to the report as numbered items (`D-1`, `D-2`, …), never to chat; on approval, heal per `references/terminal-sync-invariant.md`. This phase invokes no lifecycle skill.

## Phase 4: Recommend & Await Direction
The report is the record; chat is a decision brief. Never restate report sections, evidence, or no-op audits in chat.
1. Link the report. One status line for mechanical phases (e.g. `indices: 7 rebuilt · retention: ok · memory: nothing qualifies`).
2. ≤5 recommendations, ranked by payoff (recurrence × cost of the failure), under two headings by route:
   - **Quick fix** — memory, docs, config or drift heal; no code. Applied in this session on approval.
   - **New issue** — this project's code, tests or tooling. Recommend `/3b-create-issue`; 0d never creates it.

   Each: `R-n` · action (one line) · why (one clause + report anchor) · size.
   - A defect in an installed StratOS skill is not an `R-n`: write it under `## Framework feedback` in the report (skill · installed version · defect · evidence · suggested fix) for the project owner to forward to the StratOS maintainer, and add a one-line notice in chat. Never file it, name a repo, or edit the installed skill.
   - A finding routed to an existing law is not a recommendation unless it recurs across nights — then recommend a fix for the law not reaching agents.
   - Drift: one recommendation per heal batch, grouped by kind (labels | parent | blocked_by) with count and `D-n` range.
3. Write the `R-n` list as `## Recommendations` at the top of the report; evidence and verbatim output go below it.
4. Halt. Ask: *"Which recommendations should I implement? Reply with R-numbers, `all`, or `none`."*

After the user answers, append `## Decisions` to that night's report: one line per `R-n` (with its `D-n` range and each BT id, as `D-n` restarts nightly), `accepted` or `declined`. Phase 2 of later nights reads it.
