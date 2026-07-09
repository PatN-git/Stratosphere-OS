---
type: reference
name: concept-map-operations
description: CLI verbs and local fallbacks for executing concept map tracker operations.
timestamp: 2026-07-09
version: "1.0.0"
---

# Concept Map Tracker Operations

This reference documents the CLI operations (reusing `3b` primitives) and their disconnected local fallbacks (`BT-LOCAL`) for charting, working, and querying a concept map issue tree.

## Native dependency verification
Before running dependency commands, run `gh issue create --help` to check for native dependency flags (`--blocked-by`). If the flags are absent, fall back to encoding blocking as the text `Blocked by: [IDs]` field in the issue body, matching the `BT-LOCAL` fallback.

---

## 1. Create Map (Tracking Issue)
Create the root tracking issue for the concept map.

- **GitHub CLI:**
  ```bash
  gh issue create --title "Concept Map: <Destination>" --label "concept:map" --body-file ".agents/workflows/.reference/concept-map-template.md"
  ```
  And append a row for the map to `.memory/BACKLOG_MAP.md` (milestone-exempt, `status:in progress`, carrying the `concept:map` label).
- **BT-LOCAL Fallback:**
  Create a local map file at `docs/discovery/<slug>.map.md` copying the template body, and add a `BT-LOCAL-<n>` row to `.memory/BACKLOG_MAP.md`.

---

## 2. Create Decision Ticket (Create-then-Wire)
Create a child decision ticket and link it as a sub-issue.

- **GitHub CLI:**
  1. Create the issue:
     ```bash
     gh issue create --title "<Type>: <Title>" --label "concept:<type>" --body "<!-- SOS:BLOCK id=concept-ticket v=1.0.0 -->
Blocked by: 
<!-- SOS:/BLOCK id=concept-ticket -->"
     ```
     *(Where `<type>` is research, grilling, prototype, or task)*
  2. Link as sub-issue:
     ```bash
     gh sub-issue add <map#> <ticket#>
     ```
  3. Wire native dependencies (if blocked by other tickets, and native support is present):
     ```bash
     gh issue edit <ticket#> --add-blocked-by <blocked_by_ticket_ids>
     ```
- **BT-LOCAL Fallback:**
  Add a new `BT-LOCAL-<n>` row to the local map file `docs/discovery/<slug>.map.md` under a `## Tickets` section, recording its type, status, and `Blocked by: [BT-LOCAL-ids]` text field.

---

## 3. Claim Ticket
Claim an open decision ticket to prevent concurrent agent execution.

- **GitHub CLI:**
  Assign yourself to the issue (concurrency arbitrated by GitHub remote):
  ```bash
  gh issue edit <ticket#> --add-assignee @me
  ```
- **BT-LOCAL Fallback:**
  Mark the ticket row in the local map file as `assigned: @me`. (Advisory only; acts as a single-writer lock).

---

## 4. Query Frontier
Identify the set of open, unblocked, unassigned decision tickets (the "frontier").

- **GitHub CLI:**
  Query the tracking issue's sub-issues, resolving their dependencies:
  1. Retrieve all open sub-issues under the map:
     ```bash
     gh issue view <map#> --json subIssues
     ```
  2. For each sub-issue, fetch its details:
     ```bash
     gh issue view <ticket#> --json state,blockedBy,assignees
     ```
  3. Filter to find the frontier:
     `state == "OPEN" && length(blockedBy containing open issues) == 0 && length(assignees) == 0`
- **BT-LOCAL Fallback:**
  Parse `docs/discovery/<slug>.map.md`'s ticket table, selecting rows where `status == open`, no listed `Blocked by` local IDs are open, and `assignee` is empty.

---

## 5. Resolve Ticket
Post the decision answer, close the ticket, and index it on the map.

- **GitHub CLI:**
  1. Comment the answer:
     ```bash
     gh issue comment <ticket#> --body "<answer/resolution>"
     ```
  2. Close the issue:
     ```bash
     gh issue close <ticket#>
     ```
  3. Update the map: Append a line to the `Decisions so far` section in the `concept:map` body:
     `- [<ticket title>](<#/link>) — <gist>`
- **BT-LOCAL Fallback:**
  1. Record the answer directly in the local map file's ticket row/section.
  2. Transition status to `done`.
  3. Update the local map file's `Decisions so far` index.
