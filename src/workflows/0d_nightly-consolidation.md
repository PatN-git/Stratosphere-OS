---
name: 0d_nightly-consolidation
description: End-of-day maintenance routine to reconcile multi-session learnings and purge intermediate scratchpads.
type: workflow HITL
trigger: User. Do not run autonomously.
---

# Nightly Consolidation

## Constraint
Do not modify any files without explicit user approval.


## Phase 1: Review Sessions
- Review all sessions across all models from the last 24 hours.
- Identify problems, inefficiencies, redundant tool calls, and recurring main/sub-agent mistakes worth optimizing.

## Phase 2: Distill Plan
- Output a high-density, bulleted proposal in `.tmp/` for how sessions can be optimized or which skills/workflows to modify.
- Name the plan file `nightly_[date].md`.

## Phase 3: Crystallize Memory
- Scan all entries in `.memory/*` except `DESIGN.md` (external Google Labs DESIGN.md spec) for:

    | Trigger | Proposal |
    |:---|:---|
    | Duplicate or overlapping entries | Merge? |
    | `[PATTERN]` cited ≥3 times across tasks | Promote to `[LAW]` in `ARCHITECTURE.md` or `DESIGN_RULES.md`? (not applicable to `GLOSSARY.md`) |
    | `[ASSUMED]` older than 5 sessions, never validated | Delete? |
- If proposals surface adjust the plan created in Phase 2. If nothing qualifies, skip silently.

## Phase 3.5: Rebuild Directory Indices
- Rebuild the `index.md` for `.memory/` and all subdirectories under `docs/` (`prds/`, `discovery/`, `research/`, `design/`, `knowledge/`) by scanning their `.md` concept files:
  - Read the frontmatter `title` and `description` from each `.md` file.
  - Rebuild the directory's `index.md` listing as `* [Title](/path.md) - description`, grouped under a `# [Directory Name]` heading.
  - **Special-case `docs/knowledge/`**: Do not scan foreign concept `.md` files; instead, list one entry per source bundle (`docs/knowledge/<source>/` subdirectory).

## Phase 4: Await Execution Direction
Halt execution entirely. Ask the user: *"What aspects of the plan do you want to implement?"*