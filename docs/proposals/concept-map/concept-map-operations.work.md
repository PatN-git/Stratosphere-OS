---
type: reference
name: concept-map-operations
description: CLI verbs for executing concept map tracker operations.
timestamp: 2026-07-30
version: "1.1.0"
---

# Concept Map Tracker Operations

CLI verbs (reusing `3b` primitives) for charting, working, and querying a concept-map issue tree.

## Preflight
`gh auth status` must succeed. Fails, or `gh` absent → halt with `[BLOCKED] 1c requires an authenticated gh`. **There is no local fallback:** the map's value is the shared tracker issue and the tracker's native blocking, which renders the frontier visually without opening the map. Neither survives a local copy.

## Issue relations
Wire sub-issue and blocked-by relations via `.agents/workflows/.reference/github-issue-relations.md` (native `gh api graphql`).

---

## 1. Create Map (Tracking Issue)
Create the root tracking issue for the concept map.

```bash
gh issue create --title "Concept Map: <Destination>" --label "concept:map" --body-file ".agents/workflows/.reference/concept-map-template.md"
```
Then append a row for the map to `.memory/BACKLOG_MAP.md` (milestone-exempt, Status `in progress`, carrying the `concept:map` label).

**Open tickets are never listed in the map body** — they are open child issues, found by the frontier query (§4).

---

## 2. Create Decision Ticket (Create-then-Wire)
Create a child decision ticket and link it as a sub-issue. Size each ticket to **one agent session (~100K tokens)**; split a question that cannot fit.

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

The answer is **not** part of the body — it is posted on resolution (§5). Assets created while resolving are **linked** from the issue, never pasted in.

---

## 3. Claim Ticket
Claim an open decision ticket to prevent concurrent agent execution. Claim **first, before any work**. Concurrency is arbitrated by the GitHub remote.

```bash
gh issue edit <ticket#> --add-assignee @me
```

The assignee *is* the claim — an open, unassigned ticket is unclaimed.

**Release the claim** on any ticket halted without resolving:
```bash
gh issue edit <ticket#> --remove-assignee @me
```
An assigned open ticket is off the frontier, so an unreleased claim strands it permanently.

---

## 4. Query Frontier
Identify the set of open, unblocked, unassigned decision tickets (the "frontier").

1. Retrieve all open sub-issues under the map:
   ```bash
   gh issue view <map#> --json subIssues
   ```
2. For each sub-issue, fetch its details:
   ```bash
   gh issue view <ticket#> --json state,blockedBy,assignees,labels
   ```
3. Filter to find the frontier:
   `state == "OPEN" && length(blockedBy containing open issues) == 0 && length(assignees) == 0`

Tie-break when no ticket is named: **lowest open issue number** (creation order).

### 4a. Partition the frontier by mode
Split the frontier on the execution-mode label from step 2's `labels` — `1c` Phase 2A drains the first set, Phase 2 works the second:

- **Drainable:** `mode:AFK` tickets, plus the build half of `mode:HITL` `prototype` tickets and the prep half of `mode:HITL` `grilling` tickets.
- **Human:** every other frontier ticket, **including any ticket carrying no mode label** — an unlabelled ticket is never drained.

A `mode:HITL` ticket that already carries a prep comment or a linked artifact is **not re-prepped** unless a blocker closed since that comment.

---

## 5. Resolve Ticket
Post the decision answer, close the ticket, and index it on the map. **Re-read the map body immediately before writing it** — parallel sessions edit it concurrently.

1. Comment the answer:
   ```bash
   gh issue comment <ticket#> --body "<answer/resolution>"
   ```
2. Close the issue:
   ```bash
   gh issue close <ticket#>
   ```
3. Update the map: append a line to the `Decisions so far` section in the `concept:map` body:
   `- [<ticket title>](<#/link>) — <gist>`

---

## 6. Rule Out of Scope
For a **ticket** or a **fog patch** that turns out to sit past the destination — mis-scoped while charting, or exposed by a resolution.

**Fog patch:** move the patch's line out of `Not yet specified` into `Out of scope` with the gist + why. No ticket exists, so nothing is closed. Convergence (`1c` Phase 3, step 1) requires fog empty; this and graduation (§7) are the only two ways it empties.

**Ticket:**

1. Comment why it is out of scope, then close it:
   ```bash
   gh issue close <ticket#> --comment "Out of scope: <why>"
   ```
2. Append one line to the map's `Out of scope` section: `- [<ticket title>](<#/link>) — <gist> — out of scope: <why>`.

Keep it **out of** `Decisions so far` — that section records only the route walked. Out-of-scope work never graduates; a redrawn destination starts a fresh map.

---

## 7. Graduate Fog
For a fog patch the latest resolution made specifiable.

1. Create-then-wire the new ticket(s) per §2.
2. **Clear the graduated patch from the map's `Not yet specified` section** so it lives only as its new ticket.
