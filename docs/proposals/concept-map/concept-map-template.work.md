---
type: concept-map
title: "Concept Map: <one-line destination statement>"
description: "Maps a foggy, multi-session idea into decision tickets on the tracker."
timestamp: 2026-07-30
status: "status:in progress"
slug: <topic-slug>
version: "1.1.0"
---

# Concept Map: <one-line destination statement>

<!-- Open tickets are NOT listed here — they are open child issues, found by the frontier query
     (concept-map-operations.md §4). Exception: BT-LOCAL mode's `## Tickets` table IS the tracker. -->

## Destination
<Define the concrete boundary of what this concept is aiming to accomplish. This fixes the scope of the discovery phase.>

**Destination type:** `discovery-brief` | `locked-decision` | `in-place-change`
**Tracker mode:** `github` | `bt-local`  <!-- set at charting; every later session adopts it, never re-decides -->

## Notes
<Domain context, relevant code areas, key resources, and lists of skills or experts to consult. Every working session reads this and invokes the skills named here. An explicit override of the "plan, don't do" invariant belongs here.>

## Decisions so far
<An index of all closed decision tickets resolved during this concept map lifecycle. The map is an index, not a store — actual answers and resolutions live as comments on the closed tickets themselves. Records only the route actually walked: scope boundaries belong under Out of scope, not here.>

- [<ticket title>](<#/link>) — <gist of the decision>

## Not yet specified (fog)
<In-scope areas you can tell are coming but cannot yet phrase as a precise question. Test for ticket vs fog: can you state the question precisely NOW — not answer it? Sharp → ticket, even if blocked. Not phraseable that sharply → leave here. Do not pre-slice fog into ticket-sized pieces; one patch may graduate into several tickets, or none. On graduation, clear the patch from this section so it lives only as its new ticket.>

## Out of scope
<Work consciously ruled beyond this destination — scope, not sharpness, lands it here. The ticket is closed; one line each: gist + why + link. Never graduates; a redrawn destination starts a fresh map.>

- [<ticket title>](<#/link>) — <gist> — out of scope: <why>
