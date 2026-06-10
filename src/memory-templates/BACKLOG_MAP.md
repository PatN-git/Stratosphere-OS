# BACKLOG MAP

## Purpose
Authoritative, high-density reference for project issues and their status.

> Cross-reference rules → `.agents/rules/memory-protocol.md`.

## Rules
- When writing the first entry, populate the Label Registry with all labels used in this GitHub project.
- **BT-id padding:** The GitHub issue number must be zero-padded to 3 digits (e.g., #7 becomes BT-007). All references, links, and filenames must use this padded format.
- Update when GitHub issues are created, closed, or change status.
- Include only ID, Title, Status, Labels, Milestone, Dependencies, ICE, Ref — nothing else.
- Use the Label Registry; do not invent labels.
- The `Ref` column links to learnings, architecture rules, design rules, or glossary terms (e.g., L-012, A-003, DR-020, G-005).
- **Label source of truth:** After installation (Checkpoint 6), the Label Registry here reflects the live GitHub label set.
  - If a label appears in **GitHub but not the registry** → add it to the registry (with user confirmation).
  - If a label appears in the **registry but not GitHub** → create it in GitHub before using it in any issue.
  - Never use a label in the Backlog table that is not in both the registry and GitHub.

## Label Registry
- **Area (`area:xxx`)**: `area:BE-ai`, `area:BE-api`, `area:BE-auth`, `area:BE-data`, `area:BE-infrastructure`, `area:FE-<page_name>` (where `<page_name>` is replaced with the page's slug during audit or page creation, e.g., `area:FE-login`, `area:FE-dashboard`)
- **Type (`type:xxx`)**: `type:bug`, `type:content`, `type:feature`, `type:improvement`, `type:maintenance`, `type:research`, `type:HITL`, `type:AFK`, `type:NEEDS_SPEC`
- **Priority (`priority:xxx`)**: `priority:high` (Must have), `priority:medium` (Important), `priority:low` (Nice to have)
- **Size (`size:xxx`)**: `size:large` (Architectural: Multi-feature/major schema), `size:medium` (Vertical: Standard Data/Logic/UI slice), `size:small` (Surgical: Local/Single-file)
- **Status (`status:xxx`)**: `status:planned`, `status:in progress`, `status:done`
- **Milestone**: `x.yy` (where `x` is the release version, `yy` is the sprint number; `x.00` is targeted but not yet sprinted). Mirrors the GitHub milestone.

## Backlog

| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |
|:---|:---|:---|:---|:---|:---|:---|:---|
| BT-001 | Example task title | planned | area:FE-dashboard, type:feature | 0.08 | — | ICE: 0.27 (I: 2.0, C: 80%) | [[L-002]], [[A-003]], [[DR-012]] |
