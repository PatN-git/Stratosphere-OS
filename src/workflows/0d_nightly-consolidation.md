---
name: 0d_nightly-consolidation
description: Reconcile sessions, crystallize memory, rebuild indices, and check roadmap health.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.4"
timestamp: 2026-07-09
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

## Phase 3.6: Version-Planning Detector
- Scan `.memory/BACKLOG_MAP.md` for parent features (rows where Labels column has `size:large` and `type:feature`, and Status is not `status:done`).
- Parent feature is unroadmapped if:
  - Milestone column is empty/`-`/`—`, OR
  - `docs/ROADMAP.md` is absent, OR
  - `docs/ROADMAP.md` lacks the zero-padded ID (e.g., `BT-007`).
- Count unroadmapped parent features (N).
- If N > 0, output: *"N features unroadmapped — consider /3a_version-planning."* If `docs/ROADMAP.md` is missing: *"(Roadmap docs/ROADMAP.md is missing; run /3a_version-planning to initialize)."*
- Never run `3a` autonomously.

## Phase 4: Await Direction
Halt. Ask user: *"What aspects of the plan do you want to implement?"*