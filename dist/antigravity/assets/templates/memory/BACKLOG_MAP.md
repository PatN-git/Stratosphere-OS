---
type: backlog
title: Backlog Map
description: Authoritative registry and status mapping of all project issues.
timestamp: 2026-07-02
version: "1.1.3"
---
# BACKLOG MAP

## Purpose
Authoritative, high-density reference for project issues and their status.

> Cross-reference rules → `.agents/rules/memory-protocol.md`.

## Rules
- **PRESERVATION RULE:** Do NOT delete or modify operational instructions under Rules (such as Label source of truth syncing rules) or the `Milestone` definition line under Label Registry during setup or backlog updates. They must remain permanently as operational guidance.
- When writing the first entry, populate the Label Registry with all labels used in this GitHub project.
- **BT-id padding & Atomic Minting:** The GitHub issue number must be zero-padded to 3 digits (e.g., #7 becomes BT-007). All references, links, and filenames must use this padded format. **CRITICAL:** Never predict or pre-allocate `BT-<n>` IDs offline by scanning existing entries and calculating `MAX(BT_ID) + 1`. Because GitHub shares sequence numbers across both Issues and Pull Requests, guessing numbers locally guarantees collisions. IDs must be atomically captured strictly upon executing `gh issue create`.
- Update when GitHub issues are created, closed, or change status.
- Include only ID, Title, Status, Labels, Milestone, Dependencies, ICE, Ref — nothing else.
- Use the Label Registry; do not invent labels.
- The `Ref` column links to learnings, architecture rules, design rules, or glossary terms (e.g., L-012, A-003, DR-020, G-005). Doc paths (PRD/design) live in the GitHub issue body, not in Ref.
- **Label source of truth:** After installation (Checkpoint 6), the Label Registry here reflects the live GitHub label set.
  - If a label appears in **GitHub but not the registry** → add it to the registry (with user confirmation).
  - If a label appears in the **registry but not GitHub** → create it in GitHub before using it in any issue.
  - Never use a label in the Backlog table that is not in both the registry and GitHub.
- **Single Status Invariant:** An issue must always have exactly one `status:*` label. When transitioning an issue to a new status in GitHub or the Backlog table, always remove the prior `status:*` label first.

## Label Registry
- **Area (`area:xxx`)**: `area:BE-ai`, `area:BE-api`, `area:BE-auth`, `area:BE-data`, `area:BE-infrastructure`, `area:FE-<page_name>` (where `<page_name>` is replaced with the page's slug during audit or page creation, e.g., `area:FE-login`, `area:FE-dashboard`)
- **Primary Type (`type:<class>`)**: `type:bug`, `type:content`, `type:feature`, `type:improvement`, `type:maintenance`, `type:research`
- **Execution Mode (`type:<mode>`)**: `type:HITL` (Human-in-Loop required), `type:AFK` (Autonomous execution)
- **Priority (`priority:xxx`)**: `priority:high` (Must have), `priority:medium` (Important), `priority:low` (Nice to have)
- **Size (`size:xxx`)**: `size:large` (Architectural: Multi-feature/major schema), `size:medium` (Vertical: Standard Data/Logic/UI slice), `size:small` (Surgical: Local/Single-file)
- **Scope (`scope:xxx`)**: `scope:baseline` (MVP end-to-end), `scope:differentiator` (differentiator to win), `scope:deferred` (out of scope/temporal deferral)
- **Status (`status:xxx`)**: `status:planned`, `status:needs_spec`, `status:in progress`, `status:blocked`, `status:done`
- **Milestone**: `vX.Y.Z` (`vMAJOR.MINOR.SPRINT`, e.g. `v1.2.3` = release 1.2, sprint 3). `MAJOR.MINOR` = the product release, owned by `/3a_version-planning`; `SPRINT` (Z) owned by `/3c_sprint-planning`. `vX.Y.0` = release planned, not yet sprinted. No leading zeros. Mirrors the GitHub milestone. This is the project's product-release tracker — not a tool/library version.

## Backlog

| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |
|:---|:---|:---|:---|:---|:---|:---|:---|
| BT-XXX | Example task title | planned | area:FE-dashboard, type:feature | v1.0.3 | — | ICE: 0.27 (I: 2.0, C: 80%) | [[L-XXX]], [[A-XXX]], [[DR-XXX]] |
