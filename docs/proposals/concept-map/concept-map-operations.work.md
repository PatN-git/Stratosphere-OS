---
type: reference
name: concept-map-operations
description: CLI verbs and local fallbacks for executing concept map tracker operations.
timestamp: 2026-07-30
version: "1.1.0"
---

# Concept Map Tracker Operations

CLI verbs (reusing `3b` primitives) + `BT-LOCAL` fallbacks for charting, working, and querying a concept-map issue tree.

## Tracker mode (preflight — once per session)
`gh auth status` succeeds → **GitHub mode**. Fails or `gh` absent → **BT-LOCAL mode**. Hold the mode for the whole session. On an existing map, adopt the mode in its `Tracker mode` field instead of re-deciding — mixing modes on one map splits its decisions across two stores.

## Issue relations
Wire sub-issue and blocked-by relations via `.agents/workflows/.reference/github-issue-relations.md` (native `gh api graphql`). Disconnected: encode `Blocked by: [IDs]` text in the issue body, matching the `BT-LOCAL` fallback.

---

## 1. Create Map (Tracking Issue)
Create the root tracking issue for the concept map.

- **GitHub mode:**
  ```bash
  gh issue create --title "Concept Map: <Destination>" --label "concept:map" --body-file ".agents/workflows/.reference/concept-map-template.md"
  ```
  And append a row for the map to `.memory/BACKLOG_MAP.md` (milestone-exempt, Status `in progress`, carrying the `concept:map` label).
- **BT-LOCAL mode:**
  Create a local map file at `docs/discovery/<slug>.map.md` copying the template body, and add a `BT-LOCAL-<n>` row to `.memory/BACKLOG_MAP.md`.

**Open tickets are never listed in the map body** — they are open child issues, found by the frontier query (§4). Exception: BT-LOCAL's `## Tickets` table *is* the tracker, so it lists them.

---

## 2. Create Decision Ticket (Create-then-Wire)
Create a child decision ticket and link it as a sub-issue. Size each ticket to **one agent session (~100K tokens)**; split a question that cannot fit.

- **GitHub mode:**
  1. Create the issue:
     ```bash
     gh issue create --title "<Type>: <Title>" --label "concept:<type>" --label "mode:AFK|mode:HITL" --body "<!-- SOS:BLOCK id=concept-ticket v=1.1.0 -->
## Question

<the decision or investigation this ticket resolves — one question, sized to one agent session>

Blocked by: 
<!-- SOS:/BLOCK id=concept-ticket -->"
     ```
     *(Where `<type>` is research, grilling, prototype, or task. Exactly one execution mode — `mode:AFK` or `mode:HITL` — set per ticket, never inferred from type. Both labels are already in the `BACKLOG_MAP.md` Label Registry.)*
  2. Link as sub-issue and wire blockers via the `addSubIssue` / `addBlockedBy` mutations (see `.agents/workflows/.reference/github-issue-relations.md`).
- **BT-LOCAL mode:**
  Add a new `BT-LOCAL-<n>` row to the local map file `docs/discovery/<slug>.map.md` under a `## Tickets` section, recording its type, `mode:` (`AFK` or `HITL`), status, `## Question` text, and `Blocked by: [BT-LOCAL-ids]` text field.

The answer is **not** part of the body — it is posted on resolution (§5). Assets created while resolving are **linked** from the issue, never pasted in.

---

## 3. Claim Ticket
Claim an open decision ticket to prevent concurrent agent execution. Claim **first, before any work**.

- **GitHub mode:**
  Assign yourself to the issue (concurrency arbitrated by GitHub remote):
  ```bash
  gh issue edit <ticket#> --add-assignee @me
  ```
- **BT-LOCAL mode:**
  Mark the ticket row in the local map file as `assigned: @me`. (Advisory only; acts as a single-writer lock).

The assignee *is* the claim — an open, unassigned ticket is unclaimed.

**Release the claim** on any ticket halted without resolving (`gh issue edit <ticket#> --remove-assignee @me`; BT-LOCAL: clear `assigned:`). An assigned open ticket is off the frontier, so an unreleased claim strands it permanently.

**BT-LOCAL limit:** a file-based claim is advisory — it serializes a cooperating agent, never enforces mutual exclusion. Two BT-LOCAL sessions can hold the same ticket; GitHub mode is the only mode where the remote arbitrates.

---

## 4. Query Frontier
Identify the set of open, unblocked, unassigned decision tickets (the "frontier").

- **GitHub mode:**
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
- **BT-LOCAL mode:**
  Parse `docs/discovery/<slug>.map.md`'s ticket table, selecting rows where `status == open`, no listed `Blocked by` local IDs are open, and `assignee` is empty. Only `status == open` is on the frontier — `done` and `out-of-scope` rows are excluded by that predicate, not by convention.

Tie-break when no ticket is named: **lowest open issue number** (creation order). BT-LOCAL: lowest `BT-LOCAL-<n>`.

### 4a. Partition the frontier by mode
Split the frontier on the execution-mode label — `1c` Phase 2A drains the first set, Phase 2 works the second:

- **Drainable:** `mode:AFK` tickets, plus the build half of `mode:HITL` `prototype` tickets and the prep half of `mode:HITL` `grilling` tickets.
- **Human:** every other frontier ticket, **including any ticket carrying no mode label** — an unlabelled ticket is never drained.

```bash
gh issue view <ticket#> --json labels   # read the mode label alongside concept:<type>
```
BT-LOCAL: read the `mode:` column of the ticket row.

---

## 5. Resolve Ticket
Post the decision answer, close the ticket, and index it on the map. **Re-read the map body immediately before writing it** — parallel sessions edit it concurrently.

- **GitHub mode:**
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
- **BT-LOCAL mode:**
  1. Record the answer directly in the local map file's ticket row/section.
  2. Transition status to `done`.
  3. Update the local map file's `Decisions so far` index.

---

## 6. Rule Out of Scope
For a **ticket** or a **fog patch** that turns out to sit past the destination — mis-scoped while charting, or exposed by a resolution.

**Fog patch:** move the patch's line out of `Not yet specified` into `Out of scope` with the gist + why. No ticket exists, so nothing is closed. Convergence (`1c` Phase 3, step 1) requires fog empty; this and graduation (§7) are the only two ways it empties.

**Ticket:**

- **GitHub mode:**
  1. Comment why it is out of scope, then close it:
     ```bash
     gh issue close <ticket#> --comment "Out of scope: <why>"
     ```
  2. Append one line to the map's `Out of scope` section: `- [<ticket title>](<#/link>) — <gist> — out of scope: <why>`.
- **BT-LOCAL mode:**
  Set the ticket row `status: out-of-scope` and add the same line to the local map file's `Out of scope` section.

Keep it **out of** `Decisions so far` — that section records only the route walked. Out-of-scope work never graduates; a redrawn destination starts a fresh map.

---

## 7. Graduate Fog
For a fog patch the latest resolution made specifiable.

1. Create-then-wire the new ticket(s) per §2.
2. **Clear the graduated patch from the map's `Not yet specified` section** so it lives only as its new ticket.
