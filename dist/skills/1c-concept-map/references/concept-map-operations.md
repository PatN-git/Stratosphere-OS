---
name: concept-map-operations
description: GitHub CLI and local `issues.py` forms of the concept map tracker operations.
timestamp: 2026-11-06
version: "1.2.0"
---

# Concept Map Tracker Operations

The operations (reusing `3b` primitives) for charting, working, and querying a concept map issue tree, in GitHub and local (`tracker: local`, `references/tracker-verbs-github.md` (local: `references/tracker-verbs-local.md`)) form. Both backends hold the same issues: the map issue and its decision tickets.

## Issue relations
Wire sub-issue and blocked-by relations via `references/github-issue-relations.md` (native `gh api graphql`). Local: `--parent` and `--blocked-by` on `issues.py create`.

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
  1. Create the issue with both `concept:<type>` and `mode:<AFK|HITL>` labels:
     ```bash
     gh issue create --title "<Type>: <Title>" --label "concept:<type>" --label "mode:<AFK|HITL>" --body "<!-- SOS:BLOCK id=concept-ticket v=1.1.0 -->
     ## Question
     <1–3 targeted decision questions, sized to one ~100k-token agent session>

     Blocked by: 
     <!-- SOS:/BLOCK id=concept-ticket -->"
     ```
     *(Where `<type>` is `research`, `grilling`, `prototype`, or `task`, and `mode:*` is `mode:AFK` or `mode:HITL`)*
  2. Link as sub-issue and wire blockers via `addSubIssue` / `addBlockedBy` mutations (`references/github-issue-relations.md`).
- **Local:** `issues.py create --title "<Type>: <Title>" --label concept:<type> --label mode:<AFK|HITL> --parent <map-id> [--blocked-by <ids>] --body-file <f>` (same block body).

---

## 3. Claim Ticket & Claim Release
Claim an open decision ticket to prevent concurrent agent execution.

- **GitHub CLI:**
  - Claim: `gh issue edit <ticket#> --add-assignee @me`
  - Release claim on unresolved halt: `gh issue edit <ticket#> --remove-assignee @me`
- **Local:** `issues.py claim <ticket-id>` (compare-and-set to the current branch; `[CLAIMED …]` → pick another ticket). Local claims are branch-scoped (`claimed_by == current_branch()`); §4 keeps tickets claimed by the current branch selectable across sessions on the same branch.

---

## 4. Query Frontier & Partition by Mode
Query tracker for frontier (open, unblocked, unassigned decision tickets).

- **GitHub CLI:**
  1. Retrieve all open sub-issues under the map:
     ```bash
     gh issue view <map#> --json subIssues
     ```
  2. For each sub-issue, fetch its details:
     ```bash
     gh issue view <ticket#> --json number,title,state,blockedBy,assignees,labels
     ```
  3. Filter to find the frontier:
     `state == "OPEN" && length(blockedBy.nodes containing open issues) == 0 && length(assignees) == 0`
- **Local:** `issues.py children <map-id>`: `state == "OPEN"`, `claimed_by` is `null` or equals current branch (`issues.py branch`), and every `blocked_by` id has `state == "CLOSED"`.
- **Tie-break:** Lowest open issue number / ID (creation order).

### 4a. Partition by Mode & Idempotent Prep Read
- **Drainable (Phase 2A):** Frontier tickets carrying `mode:AFK`, plus the build/prep half of frontier `mode:HITL` `prototype` and `grilling` tickets.
- **Human (Phase 2):** Frontier tickets carrying `mode:HITL` (or missing a `mode:*` label — never infer `mode:AFK` from `concept:<type>`).
- **Idempotent Prep Check:** Before prepping a `mode:HITL` frontier ticket in Phase 2A, inspect its comments (`gh issue view <ticket#> --json comments` or `issues.py get <ticket-id>`) and skip if an `### AFK Prep` comment or linked prototype artifact is already present (unless a blocker closed after that comment).

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
  3. Re-read the latest map body (`gh issue view <map#> --json body`), append `- [<ticket title>](<#/link>) — <gist>` under `## Decisions so far`, and regenerate `## Dependency Map` in a single `gh issue edit <map#> --body-file <f>` write.
- **Local:** the same three steps: `issues.py comment <ticket-id> --body "<answer>"`, `issues.py close <ticket-id>`, then re-read with `issues.py get <map-id>` and write `## Decisions so far` + `## Dependency Map` through `issues.py set <map-id> --body-file <f>`.

---

## 6. Rule Out of Scope
Exclude a fog patch or mis-scoped decision ticket without recording it as a settled decision.

- **Fog patch:** Move the bullet from `## Not yet specified (fog)` to `## Out of scope` with a one-line reason and regenerate `## Dependency Map`.
- **Decision ticket (two-step close):**
  1. Comment reason: `gh issue comment <ticket#> --body "Out of scope: <why>"` (Local: `issues.py comment <ticket-id> --body "Out of scope: <why>"`).
  2. Close as not planned: `gh issue close <ticket#> --reason "not planned"` (Local: `issues.py close <ticket-id> --reason "not planned"`).
  3. Record under `## Out of scope` (never under `## Decisions so far`) and remove from `## Dependency Map`.

---

## 7. Graduate Fog
When resolving a ticket sharpens an entry in `## Not yet specified (fog)` into a concrete question:
1. Create and wire the new child ticket(s) per §2 (with explicit `concept:<type>` and `mode:<AFK|HITL>` labels).
2. Remove the graduated bullet from `## Not yet specified (fog)`.
3. Regenerate `## Dependency Map` in the same map body write.
