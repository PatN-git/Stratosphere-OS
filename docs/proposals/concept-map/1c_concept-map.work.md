---
name: 1c_concept-map
description: Chart decisions as tickets on tracker and converge them to discovery brief.
type: workflow HITL
trigger: manual
version: "1.2.0"
timestamp: 2026-07-30
---

# Concept Map Workflow

**Purpose:** Deconstruct complex, multi-session ideas into dependency-ordered tracker tickets, resolving one per session to converge to discovery brief.

**Hand-off contract:** Composes `/1a_research` and tracker operations in `.agents/workflows/.reference/concept-map-operations.md`. Converges to discovery brief (`docs/discovery/<slug>.md`, type `discovery-brief`).

**Invocation:** `/1c_concept-map [<map>] [<ticket>]`. `<map>` skips Phase 0 discovery; `<ticket>` also skips frontier selection.

> [!NOTE]
> Use when effort exceeds one session **and** route is foggy. Route out instead: already clear → `/1b_concept-framing`; framed, ready to specify → `/2a_write-prd`; understood plan needing slices → `/3c_sprint-planning`.

---

## Invariants

- **Plan, don't do.** A ticket resolves a **decision**, never a build slice. Map is done when nothing remains to decide before someone builds. The pull to build is the edge of the map — hand off. Override only via explicit map `Notes` entry. Implementation tickets belong downstream to `/3b_create-issue` + `/3c_sprint-planning`.
- **Index, not store.** A decision lives in exactly one place — its ticket. Map gists and links; never restates.
- **Refer by name.** Name maps and tickets by title in all user-facing output; link rides inside name. Never a bare `#<n>`.
- **One ticket per session** — `research` excepted (AFK; burned down in parallel).

---

## Phase 0: Resume & Route

1. **Hydrate:** Run `.agents/skills/load-memory/SKILL.md` to restore session context (read-only).
2. **Detect tracker mode** — once per session, then hold: run `gh auth status`. Success → **GitHub mode**; failure or absent → **BT-LOCAL mode**. State chosen mode. On an existing map, adopt the mode recorded in its `Tracker mode` field rather than re-deciding — a map charted in one mode and worked in the other splits its decisions across two stores.
3. **Discover open maps** (skip if `<map>` passed):
   - **GitHub:** `gh issue list --label concept:map --state open`
   - **BT-LOCAL:** scan `docs/discovery/*.map.md`.
4. **Map selection:** present open maps by title. Resume → Phase 2. New → step 5.
5. **Fog-or-flat:** single-session and no dependencies → redirect `/1b_concept-framing`; else Phase 1.

---

## Phase 1: Chart

1. **Name destination.** Grill per `.agents/workflows/.reference/grilling-protocol.md` to pin what this map is finding its way to, plus its **destination type**: `discovery-brief` (default) | `locked-decision` | `in-place-change`. Destination fixes scope — settle it first.
2. **Map frontier — breadth-first.** Grill again, fanning across the whole space rather than deep on one thread; surface open decisions and steps takeable now. No fog surfaced → route is already clear: redirect `/1b_concept-framing`.
3. **Register map:**
   - **GitHub:** create `concept:map` issue from `.agents/workflows/.reference/concept-map-template.md`. Add map row to `.memory/BACKLOG_MAP.md` (`status:in progress`, milestone-exempt).
   - **BT-LOCAL:** create `docs/discovery/<slug>.map.md` from template; row in `.memory/BACKLOG_MAP.md`.

   Fill Destination, destination type, `Tracker mode`, Notes; sketch fog into `Not yet specified`; leave `Decisions so far` empty. **Map body never lists open tickets** — they are open child issues, found by frontier query. Exception: BT-LOCAL's `## Tickets` table *is* the tracker, so it lists them.
4. **Create-and-wire decision tickets.** Create every ticket specifiable now as a child issue, then wire blockers in a **second pass** (issues need ids before referencing each other):
   - Label `concept:<type>` (`research`, `grilling`, `prototype`, `task`).
   - Body per `.agents/workflows/.reference/concept-map-operations.md` §2 — `## Question`, sized to one agent session.
   - **Fog-or-ticket test:** can you state the question precisely **now** — not answer it? Sharp → ticket, **even if blocked**. Not phraseable that sharply → leave in `Not yet specified`. Never pre-slice fog into ticket-sized pieces: one patch may graduate into several tickets, or none.
   - Prefer `prototype` over `grilling` when the open question is "how should it look / behave".
   - Link sub-issue and wire blockers via the `addSubIssue` / `addBlockedBy` mutations per `.agents/workflows/.reference/github-issue-relations.md`.
5. **Fire research subagents.** For each unblocked `concept:research` ticket just created, invoke a `/1a_research` subagent (Antigravity `invoke_subagent` or Claude Code `Task` general-purpose) — in parallel, one per ticket. Research is AFK: charting does not stop and read. Per subagent — Input: ticket `## Question` + map Destination, inline. Guardrail: *"Run the research loop and write only `docs/research/<map-slug>-<question-slug>.md`. Do not edit the map, the ticket, or any other file. Do not create branches, commit, or push. Report the findings path + gist."* Output: findings path + 3-line gist. The parent — never the subagent — comments the resolution and closes the ticket per Phase 2, step 5.
6. **Halt charting.** Resolve no HITL ticket while charting; hand the map to the user by name.

---

## Phase 2: Work

1. **Load map (low-res).** Read the map body once — Destination, Notes, `Decisions so far`, `Not yet specified`, `Out of scope` — never every ticket body. Orient to Destination before choosing a ticket. Invoke the skills Notes names. **Zoom as needed:** fetch a related or closed ticket's full body on demand, never up front.
2. **Select & claim ticket.** Query tracker for frontier (open, unblocked, unassigned tickets) per `concept-map-operations.md` §4. Present frontier by title. Precedence: passed `<ticket>` → user's pick → **lowest open issue number** (creation order). **Claim first, before any work:** `gh issue edit <n> --add-assignee @me` (BT-LOCAL: `assigned: @me` on the row). The assignee *is* the claim — an open, unassigned ticket is unclaimed. Expect concurrent sessions on other unblocked tickets.
3. **Grill** per `.agents/workflows/.reference/grilling-protocol.md` (G1–G3 grilling guidelines + V1–V3 vocabulary discipline).
4. **Resolve by type.** **HITL** tickets resolve only through live exchange with the user; never stand in for the user's side — an agent that answers its own grilling question has broken this:
   - **`research` (AFK):** invoke the `/1a_research` subagent per Phase 1, step 5 — same Input / Guardrail / Output contract.
   - **`grilling` (HITL):** grill to resolve the decision.
   - **`prototype` (HITL):** run `plan-html` (UI) or Template A spike (logic). Link the artifact from the ticket; never paste it in.
   - **`task` (HITL or AFK):** execute the action unblocking the decision (e.g. provision access). Drive it alone where you can (AFK); else hand the user a precise checklist. Resolution records what was done plus facts later tickets depend on — credential location, URLs, row counts.
5. **Commit resolution:** comment the resolution on the ticket; close the ticket.
6. **Update map** — **re-read the map body immediately before writing** (parallel sessions edit it concurrently):
   - Index the closed ticket under `Decisions so far`: `- [<ticket title>](<link>) — <gist>`.
   - **Graduate fog:** create-then-wire tickets the answer made specifiable, and **clear each graduated patch from `Not yet specified`** so it lives only as its new ticket.
   - **Rule out of scope** any ticket the answer reveals sits past the destination: **close** it (a closed ticket is unambiguously off the frontier) and add one line to `Out of scope` — gist + why + link. Keep it **out of** `Decisions so far`, which records only the route walked. Out-of-scope work never graduates.
   - If the resolution invalidates other tickets, update or delete them.
7. **Halt work.** One dependency step per session — independent `research` tickets excepted (they run in parallel; cheap independent frontier tickets may be batched only if they fit the context limit). Then emit the next-session invocation verbatim for the user to paste: `/1c_concept-map "<map title>" "<next frontier ticket title>"`. Compact via `/0c_handoff` if the session needs a fuller record.

---

## Phase 3: Converge

1. **Convergence condition:** run Phase 3 only when frontier and fog are both empty.
2. **Synthesize brief:** compile resolutions and research into `docs/discovery/<slug>.md` via `.agents/workflows/.reference/discovery_brief_template.md` (type: `discovery-brief`). Populate `## Decision Trail` from `Decisions so far` — map link plus every resolved ticket by name, link, and gist — so `/2a_write-prd` can zoom to the primary source instead of trusting the summary.
3. **RAT Audit:** Invoke a subagent to challenge brief:
   - *RAT Guardrail:* "Review brief for logical gaps, contradictions, or unaddressed assumptions. Report findings only; do not edit files."
4. **Self-Review + User Gate (hard HITL stop — same gate `1b` Phase 6 applies to a discovery brief):** verify the brief against the checklist — terms used appear in Vocabulary; actor is specific (not "users"); problem contains no solution language; chosen framing notes rejected alternatives; RAT + cheapest test documented with status; Decision Trail links the map and every resolved ticket; no unfiled Open Questions — then present the brief **and** the RAT findings for approval. Do not proceed to steps 5–7 until the user confirms. Never auto-close the map.
5. **Crystallize Vocabulary:** Only after the user confirmation in step 4 (per `.agents/rules/memory-protocol.md` — never write a `.memory/` content entry without it), write confirmed terms to `.memory/GLOSSARY.md` as `[[G-xxx]] [ASSUMED]`.
6. **Archive Lifecycle:** Close `concept:map` issue. Set map row status in `.memory/BACKLOG_MAP.md` to `status:done`. Abandoned map → close + `status:dropped`. A redrawn destination starts a **fresh** map, never a resumption.
7. **Hand-off:** Expose brief by name. Route by destination type: `discovery-brief` → `/2a_write-prd`; `locked-decision` → `/3b_create-issue` Template A/B; `in-place-change` → the change itself. Or exit ramps.
