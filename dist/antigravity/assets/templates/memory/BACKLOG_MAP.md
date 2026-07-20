---
type: backlog
title: Backlog Map
description: Authoritative registry and status mapping of all project issues.
timestamp: 2026-07-17
version: "1.2.1"
---
# BACKLOG MAP

## Purpose
Authoritative, high-density reference for project issues and their status.

> Cross-reference rules → `.agents/rules/memory-protocol.md`.

## Rules
<!-- SOS:BLOCK id=backlog-rules v=1.2.1 -->
- **PRESERVATION RULE:** Do NOT delete or modify operational instructions under Rules (such as Label source of truth syncing rules) or the `Milestone` definition line under Label Registry during setup or backlog updates. They must remain permanently as operational guidance.
- When writing the first entry, populate the Label Registry with all labels used in this GitHub project.
- **BT-id padding & Atomic Minting:** The GitHub issue number must be zero-padded to 3 digits (e.g., #7 becomes BT-007). All references, links, and filenames must use this padded format. **CRITICAL:** Never predict or pre-allocate `BT-<n>` IDs offline by scanning existing entries and calculating `MAX(BT_ID) + 1`. Because GitHub shares sequence numbers across both Issues and Pull Requests, guessing numbers locally guarantees collisions. IDs must be atomically captured strictly upon executing `gh issue create`.
- Update when GitHub issues are created, closed, or change status.
- Include only ID, Title, Status, Labels, Milestone, Parent, Blocked by, ICE, Ref — nothing else.
- **Identity contract:** the 7 columns `ID, Title, Status, Labels, Milestone, Parent, Blocked by` mirror GitHub's structured fields; `ICE` and `Ref` are local-only. A closed issue ≡ `status:done`.
- **Parent / Blocked by:** `Parent` holds a single `BT-<padded>` on the child only (`—` for epics/standalone); the reverse edge (an epic's children) is a query (`filter Parent = BT-<epic>`), never a stored list. `Blocked by` is a comma-list of bare `BT-<padded>` (`—` if none). A blocker is cleared from `Blocked by` once it reaches `status:in review` or `status:done`.
- Use the Label Registry; do not invent labels.
- The `Ref` column links to learnings, architecture rules, design rules, or glossary terms (e.g., L-012, A-003, DR-020, G-005). Doc paths (PRD/design) live in the GitHub issue body, not in Ref.
- **Label source of truth:** After installation (Checkpoint 6), the Label Registry here reflects the live GitHub label set.
  - If a label appears in **GitHub but not the registry** → add it to the registry (with user confirmation).
  - If a label appears in the **registry but not GitHub** → create it in GitHub before using it in any issue.
  - Never use a label in the Backlog table that is not in both the registry and GitHub.
- **Single Status Invariant:** An issue must always have exactly one `status:*` label. When transitioning an issue to a new status in GitHub or the Backlog table, always remove the prior `status:*` label first.
- **Concept Exemptions:** An issue carrying a `concept:*` label is exempt from `/3c_sprint-planning`, `[NEEDS_SPEC]` alerts, and the single-status invariant.
- **Concept Map Registry:** The `concept:map` row in the Backlog table carries `concept:map` + `status:*` (e.g. `status:in progress` while active, `status:done` on convergence) and is milestone-exempt. Child decision tickets (`concept:research`, `concept:grilling`, etc.) are tracked under their tracking issue as sub-issues and are NOT individually rowed in the Backlog table.
<!-- SOS:/BLOCK id=backlog-rules -->

## Label Registry
- **Area (`area:xxx`)**: `area:BE-ai`, `area:BE-api`, `area:BE-auth`, `area:BE-data`, `area:BE-infrastructure`, `area:FE-<page_name>` (where `<page_name>` is replaced with the page's slug during audit or page creation, e.g., `area:FE-login`, `area:FE-dashboard`)
<!-- SOS:BLOCK id=label-canonical v=1.1.7 -->
- **Primary Type (`type:<class>`)**: `type:bug`, `type:content`, `type:feature`, `type:improvement`, `type:maintenance`, `type:research`
- **Execution Mode (`mode:<mode>`)**: `mode:HITL` (Human-in-Loop required), `mode:AFK` (Autonomous execution)
- **Tier (`tier:<tier>`)**: `tier:epic` (PRD parent / epic), `tier:slice` (Leaf vertical slice)
- **Priority (`priority:xxx`)**: `priority:high` (Must have), `priority:medium` (Important), `priority:low` (Nice to have)
- **Size (`size:xxx`)**: `size:large` (Biggest effort vertical slice), `size:medium` (Medium effort vertical slice), `size:small` (Surgical effort / local fix)
- **Scope (`scope:xxx`)**: `scope:baseline` (MVP end-to-end), `scope:differentiator` (differentiator to win), `scope:deferred` (out of scope/temporal deferral)
- **Status (`status:xxx`)**: `status:needs_spec`, `status:planned`, `status:in progress`, `status:in review`, `status:blocked`, `status:done` (lifecycle order: `needs_spec → planned → in progress → in review → done`; `blocked` from any point)
- **Concept Discovery (`concept:xxx`)**: `concept:map`, `concept:research`, `concept:grilling`, `concept:prototype`, `concept:task`
- **Label Composition Rules**: Each leaf issue must carry exactly one `type:` + one `mode:` + `tier:slice` + one `size:`. Each epic must carry `tier:epic` + one `type:` (no `mode:`, no `size:`).
- **Milestone**: `vX.Y.Z` (`vMAJOR.MINOR.SPRINT`, e.g. `v1.2.3` = release 1.2, sprint 3). `MAJOR.MINOR` = the product release, owned by `/3a_version-planning`; `SPRINT` (Z) owned by `/3c_sprint-planning`. `vX.Y.0` = release planned, not yet sprinted. No leading zeros. Mirrors the GitHub milestone. This is the project's product-release tracker — not a tool/library version.
<!-- SOS:/BLOCK id=label-canonical -->

## Backlog

<!-- SOS:BLOCK id=backlog-header v=1.2.0 -->
| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
<!-- SOS:/BLOCK id=backlog-header -->
| BT-XXX | Example task title | planned | area:FE-dashboard, type:feature, mode:HITL, tier:slice, size:medium | v1.0.3 | BT-YYY | — | ICE: 0.27 (I: 2.0, C: 80%) | [[L-XXX]], [[A-XXX]], [[DR-XXX]] |
