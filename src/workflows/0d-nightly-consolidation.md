---
name: 0d-nightly-consolidation
description: "Reconcile sessions, crystallize memory, and rebuild indices. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.7.0"
timestamp: 2026-11-10
---

# Nightly Consolidation

## Constraint
Do not modify files without user approval, except the report, `.last-run.json` (only through `nightly_state.py`), rebuilt indices, and the `## Decisions` line of an earlier report (that line only).

## Phase 1: Review Sessions
1. Run `python .agents/scripts/nightly_scan.py`; its header `since` is the delta start. Run `python .agents/scripts/nightly_state.py slugs` (names of earlier findings only; read no prior report text in Phase 1).
2. Run `git log --all --since="<since>" --stat --no-merges`. Review the scan, not transcripts; open one only to inspect a failing call. More than ~15 sessions → inspect the failing calls of the 5 with the most errors; state the sample in the report.
3. Name inefficiencies, redundant tool calls (`repeats` in the scan) and recurring main/sub-agent mistakes with a stable kebab-case slug (`shell-quoting`, `stale-path`), reusing a listed slug for the same failure. Run `python .agents/scripts/nightly_state.py findings --slugs <a,b,…>` (skip when there are none); it prints `<slug> nights=N`. Format findings into a rigid table:
   | Slug | Nights | Ladder Rung | Finding Summary | Recommended Action |
   |:---|:---:|:---:|:---|:---|
4. Route each finding per `references/environment-fix-ladder.md` (escalation and hypothesis rules apply): `nights ≥ 2` also counts as a recurrence (ladder Escalation): rung 1 or 4.
5. Report findings only: no session roster and no positive observations.

## Phase 2: Distill Plan
- Before proposing, read the `## Decisions` section (max 30 lines) of each of the last 7 `docs/nightly/nightly-*.md` reports by filename date; none yet → skip. An item the user **declined** is not re-proposed without new evidence; an `accepted · deferred` item may be. A `pending` line is carried forward (Phase 4 step 2). Do not read their proposal text (Phase 1 anti-anchoring).
- Output the high-density proposal to `docs/nightly/nightly-<YYYY-MM-DD>.md` (tracked), covering session/skill optimizations. **Prepend OKF frontmatter** — `type: proposal`, `title`, `description` (Phase 3.5 reads both), `status: stable`, `generated: {by: 0d-nightly-consolidation, at: <ISO 8601>}`.
- Stamp the run: `python .agents/scripts/nightly_state.py stamp` (never hand-write `.last-run.json`).
- **Retention:** delete `docs/nightly/nightly-*.md` reports older than ~90 days by filename date. Keep `.last-run.json` and `index.md`.

## Phase 3: Crystallize Memory
- **Diff-Based Consolidation Verification:** Before proposing memory promotions or merges, run `git log --since="<since>" --stat` to verify that candidate learnings correspond to shipped and verified commit diffs rather than ephemeral transcript noise.
- Scan `.memory/*` (except `DESIGN.md`) for:

    | Trigger | Proposal |
    |:---|:---|
    | Duplicate or overlapping entries | Merge? |
    | `[PATTERN]` cited ≥3 times | Promote to `[LAW]` in `ARCHITECTURE.md` or `DESIGN_RULES.md`? (Not for `GLOSSARY.md`) |
    | `[ASSUMED]` cited in `Ref` by ≥2 distinct tasks | Promote to `[PATTERN]`? |
    | `[ASSUMED]` older than 7 days by its inline `[YYYY-MM-DD]` | Supersede with a `[REMOVED]` tombstone? |
- Citations are the `Refs:` lines of tracker issues (`issues.py list --all`, then `get`) plus `[[ID]]` mentions in `.memory/`.
- **Cross-file promotion (`[PATTERN]` → `[LAW]`):** Promoting a `[PATTERN]` in `LEARNINGS.md` (`[[L-xxx]]`) to `[LAW]` in `ARCHITECTURE.md` (`[[A-yyy]]`) or `DESIGN_RULES.md` (`[[DR-yyy]]`) is a cross-file supersession: write the new `[LAW]` entry in the target file and move `[[L-xxx]]` to `## Superseded` in `LEARNINGS.md` with `[SUPERSEDED BY [[A-yyy]]]` (or `[[DR-yyy]]`).
- A removal is a tombstone under `## Superseded`, never a deletion (memory-protocol §3, §5): deleting leaves an ID gap.
- **Avoid-list reconciliation:** Migrate or retire `Avoid:` synonyms for superseded terms.
- Adjust plan if proposals surface. No-op audits (promotion, avoid-list, retention with nothing qualifying) collapse into one status line in the report (same line as Phase 4 step 1), never a section.
- Do not scan codebase for `Avoid:` terms.

## Phase 3.5: Rebuild Directory Indices
Run `python .agents/scripts/okf_view.py --rebuild-indices` and report its `N indices rebuilt` line. Do not rebuild by hand.

## Phase 4: Recommend & Await Direction
The report is the record; chat is a decision brief. Never restate report sections, evidence, or no-op audits in chat.
1. Link report. One status line for mechanical phases (e.g. `indices: 7 rebuilt · retention: ok · memory: nothing qualifies`).
2. ≤5 recommendations, ranked by payoff (recurrence × cost of failure), under two headings by route. Group routine Tier 1 cleanups (dead links, formatting, index syncing, avoid-list retirement) under batch recommendation `R-ALL-CLEAN` for single-click approval (`.memory/` writes require explicit approval; never mutate silently per `.agents/rules/memory-protocol.md` §5). Each `pending` line carried from Phase 2 takes a slot first and is shown as a binary (`do it` / `decline`). If forced items exceed 5, keep carried `pending` first; list overflow as one-line count (`+N more in the report`):
   - **Quick fix** — memory, docs or config; no code. Applied in this session on approval.
   - **New issue** — this project's code, tests or tooling. Recommend `/3b-create-issue`; 0d never creates it.

   Each: `R-n` · action (one line) · why (one clause + report anchor) · size.
   - A rung-4 finding is not an `R-n`: record it under `## Framework feedback` per the ladder, plus a one-line notice in chat.
   - A finding routed to an existing law is not an `R-n` unless it recurs; then recommend a fix for the law not reaching agents.
3. Write the `R-n` list as `## Recommendations` at the top of the report, and one `## Decisions` stub line per `R-n` before halting: `R-n · <action> · pending`. Rewrite each carried `pending` line in its original report to `carried → nightly-<date> R-m`. Evidence and verbatim output go below. When 0 `R-n` items exist across Phases 1–3 and carried `pending`, omit `## Recommendations` / `## Decisions` stubs (or record `No recommendations`) and skip the Phase 4 decision halt.
4. **Decision Halt:**
   - **Batch Approval:** prompt user via native question tool (`ask_question` on Antigravity; `AskUserQuestion` on Claude Code) with options `["(Recommended) Apply Cleanups (R-ALL-CLEAN)", "Review Cleanups Individually", "Decline All"]`.
   - **Fallback (non-interactive hosts):** prompt `[Apply Recommended Cleanups (R-ALL-CLEAN)] / [Decline]` (or ask for R-numbers, `all`, or `none`) and halt for user response.
   - **Safety Invariant:** `.memory/` writes require explicit approval; never mutate silently per `.agents/rules/memory-protocol.md` §5.

After the user answers, rewrite each stub line in place (never append a second one): `accepted · applied` (append ` <sha>` only when a commit was made), `accepted · deferred`, or `declined`. `none` → every line `declined`; an accepted New issue → `accepted · deferred`. Phase 2 of later nights reads it.
- **Commit rule (D1):** On the default branch (`main`/`master`), after rewriting `## Decisions` stub lines (or when skipping the halt on empty findings), commit ONLY explicit touched paths (`docs/nightly/`, rebuilt `index.md` files, and approved `.memory/` Quick fixes) locally on default branch as `chore(nightly): consolidate <YYYY-MM-DD>` (never push automatically) and append `<sha>` to `accepted · applied <sha>`. On a feature branch, leave changes uncommitted and write `accepted · applied` without `<sha>`.
