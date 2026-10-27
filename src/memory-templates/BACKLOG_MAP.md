---
type: backlog
title: Backlog Map
description: Issue store of the local tracker backend (no map exists under `tracker: github`): registry and status of all project issues.
generated:
  by: stratosphere-setup
  at: 2026-09-29
version: "1.5.0"
---
# BACKLOG MAP

## Purpose
Authoritative, high-density reference for project issues and their status.

> Cross-reference rules → `.agents/rules/memory-protocol.md`.

## Rules
<!-- SOS:BLOCK id=backlog-rules v=1.4.0 -->
- **Local backend only.** This map is the issue store when `tracker: local`; with `tracker: github` there is no map (`references/tracker-verbs.md`). Labels, composition rules, the status lifecycle, concept exemptions and the milestone scheme: `references/label-taxonomy.md`.
- **PRESERVATION RULE:** do NOT delete or modify these rules during setup or backlog updates. The `Area` line under Label Registry must always exist: its slugs are project-defined and may change, but the line itself is never dropped.
- Columns: ID, Title, Status, Labels, Milestone, Parent, Blocked by, ICE, Ref; nothing else. Update the row whenever an issue is created, closed or changes status.
- **IDs:** `BT-LOCAL-<slug>` until `tracker_switch.py` moves the project to GitHub, where each id is the zero-padded issue number from `gh issue create` (`BT-007`), never predicted or pre-allocated.
- **Parent / Blocked by:** `Parent` holds a single `BT-<padded>` on the child only (`—` for epics/standalone); an epic's children are a query (`filter Parent = BT-<epic>`), never a stored list. `Blocked by` is a comma-list of bare ids (`—` if none). An edge clears when the dependent's branch has the blocker's code: same ship unit → blocker shipped; otherwise → blocker merged. `reconcile.py --edges` decides. A slice's effective blockers include its parent epic's.
- Use the Label Registry; do not invent labels. A closed issue is `status:done`; an issue carries exactly one `status:*` label.
- The `Ref` column links to learnings, architecture rules, design rules or glossary terms (L-012, A-003, DR-020, G-005). Doc paths (PRD/design) live in the issue's draft or spec file.
<!-- SOS:/BLOCK id=backlog-rules -->

## Label Registry
- **Area (`area:xxx`)**: `area:BE-ai`, `area:BE-api`, `area:BE-auth`, `area:BE-data`, `area:BE-infrastructure`, `area:FE-<page_name>` (where `<page_name>` is replaced with the page's slug during audit or page creation, e.g., `area:FE-login`, `area:FE-dashboard`)
<!-- SOS:BLOCK id=label-canonical v=1.3.0 -->
- **Canonical labels, composition rules and milestone scheme:** `references/label-taxonomy.md`. This registry adds only the project's own `area:*` slugs above.
<!-- SOS:/BLOCK id=label-canonical -->

## Backlog

<!-- SOS:BLOCK id=backlog-header v=1.2.0 -->
| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
<!-- SOS:/BLOCK id=backlog-header -->
| BT-XXX | Example task title | planned | area:FE-dashboard, type:feature, mode:HITL, tier:slice, size:medium | v1.0.3 | BT-YYY | — | ICE: 0.27 (I: 2.0, C: 80%) | [[L-XXX]], [[A-XXX]], [[DR-XXX]] |
