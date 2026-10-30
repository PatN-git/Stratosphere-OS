---
name: concept-map-operations
description: GitHub CLI and local `issues.py` forms of the concept map tracker operations.
timestamp: 2026-10-22
version: "1.1.0"
---

# Concept Map Tracker Operations

The operations (reusing `3b` primitives) for charting, working, and querying a concept map issue tree, in GitHub and local (`tracker: local`, `references/tracker-verbs.md`) form. Both backends hold the same issues: the map issue and its decision tickets.

## Issue relations
Wire sub-issue and blocked-by relations via `github-issue-relations.md` (native `gh api graphql`). Local: `--parent` and `--blocked-by` on `issues.py create`.

---

## 1. Create Map (Tracking Issue)
Create the root tracking issue for the concept map.

- **GitHub CLI:**
  ```bash
  gh issue create --title "Concept Map: <Destination>" --label "concept:map" --label "status:in progress" --body-file ".tmp/1c-concept-map-body.md"
  ```
  Write `.tmp/1c-concept-map-body.md` first from the template's **Artifact body** section only — never pipe the template file itself, whose frontmatter and instantiation instructions are not issue content.

  No milestone. Nothing is written to a local copy.
- **Local:** `issues.py create --title "Concept Map: <Destination>" --label concept:map --status "in progress" --body-file .tmp/1c-concept-map-body.md` (same body).

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
  2. Link as sub-issue and wire blockers via the `addSubIssue` / `addBlockedBy` mutations (see `github-issue-relations.md`).
- **Local:** `issues.py create --title "<Type>: <Title>" --label concept:<type> --parent <map-id> [--blocked-by <ids>] --body-file <f>` (same block body).

---

## 3. Claim Ticket
Claim an open decision ticket to prevent concurrent agent execution.

- **GitHub CLI:**
  Assign yourself to the issue (concurrency arbitrated by GitHub remote):
  ```bash
  gh issue edit <ticket#> --add-assignee @me
  ```
- **Local:** `issues.py claim <ticket-id>` (compare-and-set; `[CLAIMED …]` → pick another ticket).

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
     `state == "OPEN" && length(blockedBy.nodes containing open issues) == 0 && length(assignees) == 0`
- **Local:** `issues.py children <map-id>`: `state == "OPEN"`, no `claimed_by`, and every `blocked_by` id `CLOSED`.

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
- **Local:** the same three steps: `issues.py comment <ticket-id> --body "<answer>"`, `issues.py close <ticket-id>`, then the `Decisions so far` line through `issues.py set <map-id> --body-file <f>`.
