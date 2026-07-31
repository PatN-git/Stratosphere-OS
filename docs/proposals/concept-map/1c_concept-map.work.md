---
name: 1c_concept-map
description: Chart decisions as tickets on tracker, drain the AFK frontier autonomously, and converge the remaining decisions to discovery brief.
type: workflow HITL
trigger: manual
version: "1.3.0"
timestamp: 2026-07-30
---

# Concept Map Workflow

**Purpose:** Deconstruct complex, multi-session ideas into dependency-ordered tracker tickets, resolving one per session to converge to discovery brief.

**Hand-off contract:** Composes `/1a_research` and tracker operations in `.agents/workflows/.reference/concept-map-operations.md`. Converges to discovery brief (`docs/discovery/<slug>.md`, type `discovery-brief`).

**Invocation:** `/1c_concept-map [<map>] [<ticket>] [--drain]`. `<map>` skips Phase 0 discovery; `<ticket>` preselects the frontier ticket. `--drain` runs **Phase 0 + Phase 2A only** — the sole AFK-safe surface, callable without a user present by a scheduled routine (AGENTS.md §1). `--drain` ignores `<ticket>`.

**Requires an authenticated `gh`.** The map *is* a tracker issue: the shared URL and the tracker's native blocking (which renders the frontier visually, without opening the map) are the artifact's value, not an implementation detail. There is no local fallback.

> [!NOTE]
> Use when effort exceeds one session **and** route is foggy. Route out instead: already clear → `/1b_concept-framing`; framed, ready to specify → `/2a_write-prd`; understood plan needing slices → `/3c_sprint-planning`.

---

## Invariants

- **Plan, don't do.** A ticket resolves a **decision**, never a build slice. Map is done when nothing remains to decide before someone builds. The pull to build is the edge of the map — hand off. Override only via explicit map `Notes` entry. `1c` never edits production code and never creates a branch; implementation belongs downstream to `/3b_create-issue` + `/3d_implement-issue`.
- **Index, not store.** A decision lives in exactly one place — its ticket. Map gists and links; never restates.
- **Refer by name.** Name maps and tickets by title in all user-facing output; link rides inside name. Never a bare `#<n>`.
- **Attention is the bound, not context.** One `mode:HITL` ticket per session — never batch two. The `mode:AFK` sub-frontier carries no such bound: drain it in parallel to exhaustion (Phase 2A), so a human session opens on decisions only.
- **AFK prepares a HITL ticket; it never resolves one.** An AFK pass may post a prep comment on a `mode:HITL` ticket and may build its prototype artifact. It may **never** post a resolution to, or close, a `mode:HITL` ticket — only the live exchange does that (mirrors `/3z_afk-loop`'s "never autonomously execute non-`mode:AFK` slices"). An agent that answers its own grilling question has broken this.

---

## Phase 0: Resume & Route

1. **Hydrate:** Run `.agents/skills/load-memory/SKILL.md` to restore session context (read-only).
2. **Preflight:** `gh auth status`. Fails, or `gh` absent → halt with `[BLOCKED] 1c requires an authenticated gh`. Never degrade to a local map.
3. **Discover open maps** — skip when `<map>` was passed: resolve `<map>` by title or URL, then Phase 2A.
   ```bash
   gh issue list --label concept:map --state open
   ```
4. **Map selection:** present open maps by title. Resume → Phase 2A. New → step 5. (`--drain` never charts: with no resumable map it exits `[SKIP] no map to drain`.)
5. **Fog-or-flat:** single-session and no dependencies → redirect `/1b_concept-framing`; else Phase 1.

---

## Phase 1: Chart

1. **Name destination.** Grill per `.agents/workflows/.reference/grilling-protocol.md` to pin what this map is finding its way to, plus its **destination type**: `discovery-brief` (default) | `locked-decision` | `in-place-change`. Destination fixes scope — settle it first.
2. **Map frontier — breadth-first.** Grill again, fanning across the whole space rather than deep on one thread; surface open decisions and steps takeable now. No fog surfaced → route is already clear: compile the brief inline per Phase 3, step 2, or redirect `/1b_concept-framing`.
3. **Register map:** create `concept:map` issue from `.agents/workflows/.reference/concept-map-template.md`. Add map row to `.memory/BACKLOG_MAP.md` (Status `in progress`, `concept:map` label, milestone-exempt). Fill Destination, destination type, `AFK drain`, Notes; sketch fog into `Not yet specified`; leave `Decisions so far` empty. **Map body never lists open tickets** — they are open child issues, found by the frontier query.
4. **Create-and-wire decision tickets.** Create every ticket specifiable now as a child issue, then wire blockers in a **second pass** (issues need ids before referencing each other) — capture each returned issue number from `gh issue create`; never predict one:
   - Label `concept:<type>` (`research`, `grilling`, `prototype`, `task`) **and** an execution mode — `mode:AFK` or `mode:HITL`. **Set mode per ticket; never infer it from type.** `research` is normally `mode:AFK`; `grilling` is always `mode:HITL`; `prototype` is `mode:HITL` (its build half still drains — Phase 2A); `task` is either, decided by whether the agent can drive it alone. A ticket with no mode label is excluded from the drain and stays on the human frontier.
   - Body per `.agents/workflows/.reference/concept-map-operations.md` §2 — `## Question`, sized to one agent session.
   - **Fog-or-ticket test:** can you state the question precisely **now** — not answer it? Sharp → ticket, **even if blocked**. Not phraseable that sharply → leave in `Not yet specified`. Never pre-slice fog into ticket-sized pieces: one patch may graduate into several tickets, or none.
   - Prefer `prototype` over `grilling` when the open question is "how should it look / behave".
   - Link sub-issue and wire blockers via the `addSubIssue` / `addBlockedBy` mutations per `.agents/workflows/.reference/github-issue-relations.md`.
5. **Halt charting.** Resolve no ticket while charting; hand the map to the user by name, then Phase 2A.

---

## Phase 2A: AFK Drain

Clears everything the agent can clear without the user, so Phase 2 opens on decisions only. Runs after charting and at the start of every working session.

1. **Partition frontier.** Query tracker for frontier (open, unblocked, unassigned tickets) per `.agents/workflows/.reference/concept-map-operations.md` §4, then split by mode label (§4a): **drainable** (`mode:AFK`, plus the build/prep half of `mode:HITL` tickets) and **human** (everything else).
2. **Skip what is already done.** A `mode:HITL` ticket already carrying a prep comment or a linked prototype artifact is **not re-prepped** unless a blocker closed since that comment — otherwise a scheduled drain re-posts the same prep every run. Prep is idempotent per frontier state, not per invocation.
3. **Authorize once [HITL gate].** Present the drain plan by ticket title: what each pass will do and what it will write. Halt for confirmation before executing. **Skip this gate only** when the map's `AFK drain` field reads `authorized` (standing authorization) or the invocation is `--drain` (the caller already authorized it).
4. **Drain in parallel** — one pass per drainable ticket:
   - **`research` (`mode:AFK`):** invoke a research subagent (Antigravity `invoke_subagent` or Claude Code `Task` general-purpose). Per ticket the **parent** first derives `1a` Phase 1 inline from the ticket `## Question` — topic sentence, canonical slug, 3–5 research questions, Primary Domain, Depth — stating the choice with a one-line rationale, and skips `1a`'s Propose-and-Confirm Gate (the map already gated scope). The subagent runs `1a`'s Phase 2 research loop only; `1c` never invokes the `/1a_research` workflow itself (AGENTS.md §1).
     - **Input:** that derived brief + the ticket `## Question` + map Destination, passed inline — the parent resolves every input; the subagent never sweeps the repo to locate them.
     - **Guardrail:** *"Run the research loop and write only `docs/research/<map-slug>-<question-slug>.md`. Do not edit the map, the ticket, or any other file. Do not create branches, commit, or push. Report the findings path + gist."*
     - **Output:** findings path + 3-line gist. Parent owns the filename — pass it in, so parallel passes cannot collide.
   - **`task` (`mode:AFK`):** execute the action unblocking the decision. Resolution records what was done plus facts later tickets depend on — the credential's env-var name (never its value or file path), URLs, row counts.
   - **`prototype` (`mode:HITL`) — build half only:** produce the artifact via `plan-html` (UI) or an `.agents/workflows/.reference/issue-templates.md` Template A spike (logic) and link it from the ticket. **Leave the ticket open** — the user's reaction is the resolution.
   - **`grilling` (`mode:HITL`) — prep half only:** look up every G2-discoverable fact and post one prep comment carrying those facts plus your G1 recommendation and its rationale, labelled *"proposal — awaiting the user's decision"*. **Leave the ticket open.** Posting a prep comment is not resolving; per the Invariants, only the live exchange resolves it.
5. **Terminal state per ticket (exhaustive — every drained ticket reaches exactly one):** `resolved` (`mode:AFK` only — comment the resolution and close per Phase 2, step 5) | `prepped` (`mode:HITL`; artifact or prep comment posted, ticket still open) | `blocked-needs-human` | `out-of-scope` (per §6 of the operations reference). Never leave a drained ticket unstated.
6. **Bounded attempts:** max 3 per ticket per run. On exhaustion **demote** it — relabel `mode:HITL`, comment what failed and what it needs, leave it open on the human frontier. Never retry past 3; never silently drop a ticket.
7. **Write the map once, after the batch.** Apply every Phase 2 step 6 map update for the whole drain in a single write — parallel passes make per-ticket writes race. Re-read the map body immediately before writing.
8. **Recompute and repeat** from step 1 while any drainable frontier ticket remains unattempted this run — a resolution graduates fog, which can surface fresh `mode:AFK` tickets. Stop when the frontier is human-only, or frontier and fog are both empty (→ Phase 3).
9. **Report** per ticket: title, terminal state, artifacts written. Then `--drain` exits; an interactive run continues to Phase 2.

---

## Phase 2: Work

The human frontier — one `mode:HITL` ticket per session.

1. **Load map (low-res).** Read the map body once — Destination, Notes, `Decisions so far`, `Not yet specified`, `Out of scope` — never every ticket body. Orient to Destination before choosing a ticket. Invoke every skill named in the map's `Notes` section. **Zoom as needed:** fetch a related or closed ticket's full body on demand, never up front.
2. **Select & claim ticket.** Present the human frontier by title. Precedence: passed `<ticket>` → user's pick → tie-break per `.agents/workflows/.reference/concept-map-operations.md` §4. **Claim first, before any work** (§3 of the same reference). Expect concurrent sessions on other unblocked tickets.
3. **Grill** per `.agents/workflows/.reference/grilling-protocol.md` (G1–G3 grilling guidelines + V1–V3 vocabulary discipline). Open with the ticket's prep comment if Phase 2A left one — its recommendation is a proposal to react to, never a settled answer.
4. **Resolve by type.** These are `mode:HITL` tickets: they resolve only through live exchange with the user; never stand in for the user's side.
   - **`grilling`:** grill to resolve the decision.
   - **`prototype`:** react to the artifact Phase 2A built (build it now if the drain was skipped); the user's judgement on it is the resolution.
   - **`task` (`mode:HITL`):** hand the user a precise checklist; resolution records what was done plus facts later tickets depend on — the credential's env-var name (never its value or file path), URLs, row counts.
5. **Commit resolution:** comment the resolution on the ticket; close the ticket.
6. **Update map** — **re-read the map body immediately before writing** (parallel sessions edit it concurrently):
   - Index the closed ticket under `Decisions so far`: `- [<ticket title>](<link>) — <gist>`.
   - **Graduate fog:** create-then-wire tickets the answer made specifiable — label each with `concept:<type>` **and** a mode per Phase 1, step 4 — and **clear each graduated patch from `Not yet specified`** so it lives only as its new ticket.
   - **Rule out of scope** anything the answer reveals sits past the destination — a ticket **or** a fog patch — per `.agents/workflows/.reference/concept-map-operations.md` §6.
   - If the resolution invalidates other tickets, update or delete them.
7. **Halt work.** One `mode:HITL` ticket per session. **Release the claim** on any ticket you halt without resolving (`gh issue edit <n> --remove-assignee @me`) — an assigned open ticket is off the frontier, so an unreleased claim strands it. If the resolution surfaced fresh `mode:AFK` tickets, return to Phase 2A to drain them before halting. Then emit the next-session invocation verbatim for the user to paste: `/1c_concept-map "<map title>" "<next frontier ticket title>"`. Offer `/0c_handoff` if the session needs a fuller record — the user invokes it.

---

## Phase 3: Converge

1. **Convergence condition:** run Phase 3 only when frontier and fog are both empty — fog empties by graduating to tickets or by being ruled out of scope (§6 of the operations reference), never by being dropped silently.
2. **Synthesize brief:** compile resolutions and research into `docs/discovery/<slug>.md` via `.agents/workflows/.reference/discovery_brief_template.md` (type: `discovery-brief`). Populate `## Decision Trail` from `Decisions so far` — map link plus every resolved ticket by name, link, and gist — so a reader can reach the primary source instead of trusting the summary.
3. **RAT Audit:** invoke a Skeptical Challenger subagent (Antigravity `invoke_subagent` or Claude Code `Task` general-purpose) to challenge brief. Input: the drafted brief (`docs/discovery/<slug>.md`) + map Destination, passed inline.
   - *RAT Guardrail:* "Review brief for logical gaps, contradictions, or unaddressed assumptions. Report findings only; do not edit files."
   - Output: findings list, each naming the brief section it lands on.
4. **Self-Review + User Gate (hard HITL stop — same gate `1b` Phase 6 applies to a discovery brief):** verify the brief against the checklist — terms used appear in Vocabulary; actor is specific (not "users"); problem contains no solution language; chosen framing notes rejected alternatives; RAT + cheapest test documented with status; Decision Trail links the map and every resolved ticket; no unfiled Open Questions — then present the brief **and** the RAT findings for approval. Do not proceed to steps 5–7 until the user confirms. Never auto-close the map.

   **An AFK pass may draft the brief (step 2) and run the RAT (step 3); it may never pass this gate or close the map.** `--drain` stops at step 1 and reports that the map is ready to converge.
5. **Crystallize Vocabulary:** Only after the user confirmation in step 4 (per `.agents/rules/memory-protocol.md` — never write a `.memory/` content entry without it), write confirmed terms to `.memory/GLOSSARY.md` as `[[G-xxx]] [ASSUMED]`.
6. **Archive Lifecycle:** Close `concept:map` issue. Set map row Status in `.memory/BACKLOG_MAP.md` to `done`. Abandoned map → close the issue with the abandon reason, set Status `done` (closed ≡ done), and note `abandoned: <why>` on the row. A redrawn destination starts a **fresh** map, never a resumption.
7. **Hand-off:** Expose brief by name. Route by destination type: `discovery-brief` → `/2a_write-prd`; `locked-decision` → `/3b_create-issue` Template A/B; `in-place-change` → `/3b_create-issue` Template B, then `/3d_implement-issue`. Or exit ramps.
