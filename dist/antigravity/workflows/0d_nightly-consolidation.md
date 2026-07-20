---
name: 0d_nightly-consolidation
description: Reconcile sessions, crystallize memory, rebuild indices, and check roadmap health.
type: workflow HITL
trigger: manual
version: "1.1.0"
timestamp: 2026-07-17
---

# Nightly Consolidation

## Constraint
Do not modify files without user approval.

## Phase 1: Review Sessions
- Review sessions across models from past 24 hours.
- Identify inefficiencies, redundant tool calls, and recurring main/sub-agent mistakes.

## Phase 2: Distill Plan
- Output high-density proposal to `.tmp/nightly_[date].md` for session/workflow optimizations.

## Phase 3: Crystallize Memory
- Scan `.memory/*` (except `DESIGN.md`) for:

    | Trigger | Proposal |
    |:---|:---|
    | Duplicate or overlapping entries | Merge? |
    | `[PATTERN]` cited ≥3 times | Promote to `[LAW]` in `ARCHITECTURE.md` or `DESIGN_RULES.md`? (Not for `GLOSSARY.md`) |
    | `[ASSUMED]` older than 5 sessions, unvalidated | Delete? |
- **Avoid-list reconciliation:** Migrate or retire `Avoid:` synonyms for superseded terms.
- Adjust plan if proposals surface. Skip silently if nothing qualifies.
- Do not scan codebase for `Avoid:` terms.

## Phase 3.5: Rebuild Directory Indices
- Rebuild `index.md` for `.memory/` and `docs/` subdirectories (`prds/`, `discovery/`, `research/`, `design/`, `knowledge/`):
  - Read frontmatter `title` and `description` from each `.md` file.
  - Rebuild `index.md` as `* [Title](/path.md) - description` grouped under `# [Directory Name]`.
  - **Special-case `docs/knowledge/`**: List one entry per source bundle (`docs/knowledge/<source>/` subdirectory).

## Phase 3.6: Planning-State Advisor
Recommend the next planning workflow from backlog state. Read-only; never run a planning workflow autonomously.

1. **Base state:** parse `.memory/BACKLOG_MAP.md` rows where `status != done`.
2. **Ground-truth against GitHub:** run `gh auth status`.
   - **Connected** → GitHub is authoritative; enrich each base-state row (status != done):
     - milestones + open issues: `gh issue list --state open --json number,milestone,labels`; open milestones via `gh api repos/{owner}/{repo}/milestones`.
     - epic children: for each `tier:epic`, `gh issue view <n> --json subIssues` (numeric `<n>`, matching the repo's existing read convention) — count child slices.
     - a base-state row whose mapped issue is **absent from the open list** is *closed* on GitHub, not milestone-cleared — reconcile it as done for the advisory and do **not** emit `[DRIFT]`.
     - only when the mapped issue is **present (open)** and any of its **7 mirror fields** — status, milestone, `Labels`, `Parent`, `Blocked by` — disagrees with GitHub → emit `[DRIFT] BT-<padded>: <field> map=<x> github=<y>` and trust GitHub for the advisory (compare bare `status` token to the `Status` column, non-status labels to `Labels`, sub-issue parent to `Parent`, blocked-by to `Blocked by`).
     - **stale-blocker check:** if a row's `Blocked by` names a blocker already at `status:in review` or `status:done` → emit `[DRIFT] BT-<padded>: stale blocker <id> should be cleared` (4a/merge should have removed it).
   - **Absent/unauth** → compute from `.memory/BACKLOG_MAP.md` only; tag the outlook `[local-only — GitHub not checked]`.
3. **Recommendation (evaluate in this order — finish in-flight work before starting new planning; first match wins):**
   | Signal (`status != done`) | Recommend |
   |---|---|
   | an open sprint `vX.Y.Z` (Z≥1) with unfinished slices | `/3d_implement-issue` (or `/3z_afk-loop` for `mode:AFK` slices) |
   | ≥1 ready `tier:slice` (`status:planned`, milestone `vX.Y.0`, no sprint digit Z) and no open sprint `vX.Y.Z` (Z≥1) | `/3c_sprint-planning` |
   | a current-release `tier:epic` whose slicing is **incomplete** — zero child slices, **or** fewer child slices than its PRD §6 `[BASELINE]`/`[DIFFERENTIATOR]` stories (lazy slicing means a part-sliced epic still needs more) | `/3b_create-issue` — slice `BT-<padded>` |
   | ≥2 `tier:epic` unassigned to a release (milestone empty/`-`/`—`, or ID absent from `docs/ROADMAP.md`) | `/3a_version-planning` |
   | `docs/ROADMAP.md` absent and ≥1 `tier:epic` exists | `/3a_version-planning` — initialize roadmap |
   | none of the above | *"Backlog healthy — no planning action pending."* |
4. **Output** the top recommended command (first match), the signal that fired it **naming every `BT-<padded>` involved**, then a one-line **"also pending:"** list of any lower-priority signals that also match (so a running sprint never hides that epics need roadmapping), plus any `[DRIFT]` lines and the `[local-only]` tag. Never summarize as "some features".

_Completion criterion:_ one top recommendation (or the healthy no-op) **plus** the also-pending list emitted; every cited signal names its `BT-<padded>` IDs; drift and local-only state surfaced. This phase invokes no planning workflow.

## Phase 4: Await Direction
Halt. Ask user: *"What aspects of the plan do you want to implement?"*