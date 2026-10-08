---
name: 0d-nightly-consolidation
description: "Reconcile sessions, crystallize memory, rebuild indices, and check backlog drift. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.2.1"
timestamp: 2026-10-06
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
Run `python .agents/scripts/reconcile.py --all-open` (no `--require-gh`: this phase is advisory, and without `gh` the script prints `[local-only — GitHub not checked]` itself). Print its findings verbatim, then append each to the report as a numbered item (`D-1`, `D-2`, …); on approval, heal per `references/terminal-sync-invariant.md`. This phase invokes no lifecycle skill.

## Phase 4: Await Direction
Halt. Ask user: *"What aspects of the plan do you want to implement?"*

After the user answers, append `## Decisions` to that night's report: one line per proposed item (a `D-n` item with its BT id, as `D-n` restarts nightly), `accepted` or `declined`. Phase 2 of later nights reads it.
