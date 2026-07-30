# 1c_concept-map — Optimization Plan (Wayfinder review)

Date: 2026-07-30 · Branch: `claude/1c-workflow-optimization-3fk2f4` · Status: **plan only, nothing implemented**

## Sources reviewed
- `src/workflows/1c_concept-map.md` v1.1.1 (+ `src/references/concept-map-operations.md`, `concept-map-template.md`, `github-issue-relations.md`, `discovery_brief_template.md`, `src/workflows/1b_concept-framing.md`, `1a_research.md`)
- `mattpocock/skills` → `skills/engineering/wayfinder/SKILL.md` (128 lines, fetched raw, read in full)
- Video transcript (supplied in prompt)
- `https://www.aihero.dev/skills-wayfinder` — proxy denied CONNECT (403); **content supplied by the user as a transcript** and reviewed. Adds items #21–#22; independently confirms #2 (low-res load + zoom on demand), #3 (research stays a ticket because it's a shared blocker, but AFK → fire a subagent, don't stop and read), #7 (HITL/AFK split), #9 (one shared URL the whole team watches).
- Repo authoring discipline: `.claude/skills/improve-workflows-skills/SKILL.md` + `docs/improve-workflows-skills/README.md`

## Already covered — do not churn
Phase 0 map discovery/resume (better than Wayfinder, which has no resume), fog-or-flat redirect to `/1b`, create-then-wire two-pass ticket creation, native `addSubIssue`/`addBlockedBy` + BT-LOCAL fallback, claim-by-assignee locking, frontier definition, four ticket types, one-step-per-session halt, Phase 3 RAT + hard HITL gate + glossary crystallization (Wayfinder has no convergence phase at all — this is StratOS's own value, keep it).

## P1 — highest value

| # | Gap | Change | File |
|---|---|---|---|
| 1 | No ticket body contract. `concept-map-operations.md` §2 creates a body containing only `Blocked by:`. The question lives nowhere. | Add ticket template: `## Question` + one-line scope note. Add sizing bound: **one ticket = one ~100K-token agent session**; split if larger. | `concept-map-operations.md` §2, `1c` Phase 1.4 |
| 2 | Phase 2 opens with a frontier query — never loads the map, destination, or Notes. Ticket gets resolved without orientation; `Notes` ("skills to consult") is written at charting and never read. | Phase 2.1 = load map body (low-res, once) → orient to Destination → honour Notes' named skills. Add **zoom-as-needed**: fetch full bodies of related/closed tickets on demand, never up front. | `1c` Phase 2.1 |
| 3 | Research tickets wait for their own HITL session. Wayfinder fires them in parallel at charting time (AFK, no human needed). | Charting step: after wiring, spawn a `/1a_research` subagent per unblocked `concept:research` ticket, in parallel. Keep "Halt Charting" for HITL types. Restate the one-per-session rule as: **never more than one ticket per session — research excepted.** | `1c` Phase 1.5 + Phase 2.7 |
| 4 | No decision trail in the brief. The transcript's key claim: a Wayfinder-derived spec is superior precisely because it links back to the decision tickets as **primary source**. `discovery_brief_template.md` has no such section. | Add `## Decision Trail` — map link + one line per resolved ticket (name → link → gist). Phase 3.2 populates it from `Decisions so far`. `2a_write-prd` can then zoom to primary source instead of trusting the summary. | `discovery_brief_template.md`, `1c` Phase 3.2 |
| 5 | No **fog-or-ticket** test. Nothing tells the agent where a ticket ends and fog begins → over-charting (pre-slicing fog into fake tickets) or under-charting. | Add the rule verbatim in intent: the test is whether you can **state the question precisely now — not whether you can answer it now**. Ticket when sharp *even if blocked*; fog when not phraseable that sharply; **never pre-slice fog into ticket-sized pieces**. | `1c` Phase 1.4, `concept-map-template.md` |
| 6 | Out-of-scope has a section but no procedure. Phase 2.6 says "mark mis-scoped tickets as out-of-scope" — silent on closing them or on keeping them out of the decision index. | Procedure: **close** the ticket (a closed ticket is unambiguously off the frontier) + one line in `Out of scope` (gist + why + link). Stays **out of** `Decisions so far` — that records the route walked, not scope boundaries. Out-of-scope never graduates; it returns only if the destination is redrawn, as a fresh map. | `1c` Phase 2.6, `concept-map-template.md` |

## P2 — worth doing

| # | Gap | Change | File |
|---|---|---|---|
| 7 | Ticket types are not classified HITL vs AFK. Matters for batching, for `3z_afk-loop`, and to stop an agent grilling itself. | Tag each type: research **AFK**, prototype **HITL**, grilling **HITL**, task **HITL or AFK**. Add the invariant: on a HITL ticket the agent never speaks for the human's side — an agent that answers its own grilling question has broken it. (Extends G2's parenthetical to the ticket layer.) | `1c` Phase 2.5 |
| 8 | Fog graduation leaves residue; invalidation unhandled. | On graduation, **clear the patch from `Not yet specified`** so it lives only as its ticket. If a resolution invalidates other tickets, update or delete them. | `1c` Phase 2.6 |
| 9 | Concurrency hazard. Claim-locking prevents duplicate work, but the map body is a shared mutable doc and parallel sessions are expected. | Note: expect concurrent sessions; **re-read the map body immediately before writing it** (lost-update guard). | `1c` Phase 2.6 |
| 10 | Bare-id narration. Wayfinder devotes a section to it: `#42, #43, #44` is illegible. | One line: refer to maps and tickets by **title** in all human-facing output; the link rides inside the name, never replaces it. | `1c` header |
| 11 | Map body may accumulate open tickets. Wayfinder: open tickets are **not** listed — they are found by query. | State it, with the explicit exception: BT-LOCAL's `## Tickets` table **is** the tracker, so it does list them. | `1c` Phase 1.3, `concept-map-template.md` |
| 12 | "Plan, don't do" is implicit. Transcript flags a recurring user confusion: decision tickets vs implementation tickets. | Invariant near the top: tickets resolve **decisions**, not build slices; the map is done when nothing remains to decide. The urge to just build = the edge of the map = hand off. Overridable only by an explicit `Notes` entry. Implementation tickets are `3b`/`3c`'s job, downstream. | `1c` header |
| 13 | No deterministic ticket pick. "User selects (or the agent picks) one" — unpredictable across runs, against the playbook's predictability virtue. | Default tie-break: **lowest open issue number** (creation order) when the user names none. | `1c` Phase 2.2 |
| 14 | No next-session handoff. Transcript's author automates this; multi-session flow is the whole point. | At halt, emit a paste-ready invocation: `/1c_concept-map <map-name-or-url> "<next frontier ticket title>"`. Reuse `0c_handoff` — do not build a new mechanism. | `1c` Phase 2.7 |
| 15 | Cannot be invoked with a target. Phase 0 always runs discovery. | Accept optional args `<map> [<ticket>]` → skip Phase 0 discovery, jump to Phase 2. Token saving on every working session. | `1c` Phase 0 |
| 21 | **No tracker precondition check.** Every phase forks "GitHub CLI" vs "BT-LOCAL Fallback" without ever saying how the fork is decided. The agent guesses, and can guess differently in Phase 0 than in Phase 2 — a map charted on `gh` then worked in BT-LOCAL is a split-brain map. Wayfinder makes this a named prerequisite that defaults to local-markdown. | Phase 0 step 0: detect tracker once (`gh auth status` + repo has issues) → **GitHub mode**, else **BT-LOCAL mode**; state the chosen mode and hold it for the whole session. Record the mode on the map at charting so later sessions inherit it rather than re-deciding. | `1c` Phase 0, `concept-map-template.md` |
| 22 | **No upstream/when-not-to-use routing note.** `1a` opens with a `> [!NOTE]` gate; `1c` has none. Its only guard is Phase 0.4's fog-or-flat check, which fires *after* the user already chose `1c`. The blog is explicit that wayfinder sits upstream of to-spec/to-tickets and is the wrong tool when the thread is already clear. | Header `> [!NOTE]`: use when the effort exceeds one session **and** the route is foggy. Already clear → `/1b_concept-framing`; framed and ready to specify → `/2a_write-prd`; understood plan needing slices → `/3c_sprint-planning`. Pairs with P3 #17 (destination type). | `1c` header |

## P3 — optional / cheap

| # | Gap | Change |
|---|---|---|
| 16 | Prototype tickets under-encouraged. Transcript: prototypes are what stop this becoming waterfall. | Bias line: when the open question is "how should it look / behave", prefer a **prototype** ticket over grilling. |
| 17 | Destination type is hardcoded to a discovery brief. Wayfinder's destination varies (spec, locked decision, in-place change). | Name the destination **type** at charting (default: discovery brief → `/2a`; alternatives: locked decision → `/3b` Template A/B; in-place change). Do not remove the brief default — `2a`'s hand-off contract depends on it. |
| 18 | "Map is an index, not a store" lives only in the template. | One line in the workflow: a decision lives in exactly one place — its ticket; the map gists and links, never restates. |
| 19 | Map body section order. Wayfinder puts `Decisions so far` above the fog sections; that's the hot content on load. | Reorder template (cosmetic; skip if churn isn't worth it). |
| 20 | No abandon ramp. Phase 3.6 closes the map on convergence only. | Archive Lifecycle: abandoned map → close + `status:dropped`; a redrawn destination starts a fresh map, never a resumption. |

## Refactor proposal (playbook §2 — propose, don't silently rewrite)
G1–G3 and V1–V3 are **verbatim duplicated** across `1b_concept-framing.md` Phase 2 and `1c_concept-map.md` Phase 2.3–2.4. That is true duplication, not a sub-agent guardrail and not safety defense-in-depth → extract to `src/references/grilling-protocol.md`; `1b` and `1c` cite `.agents/workflows/.reference/grilling-protocol.md`. Both are workflows, so the scaffolded-path citation is legal (§1).

**Needs approval before touching** — G1–G3 is load-bearing content in `1b`, and this widens the blast radius beyond `1c`. If declined, everything above still lands; `1c` just keeps its copy.

## Do NOT adopt from Wayfinder
- **`research/<name>` throwaway branches for research findings.** Stated in both SKILL.md and the blog, and still rejected: AGENTS.md §4 makes `3d` the only branch creator, and `1c` is a discovery workflow. Keep the existing `docs/research/<map-slug>-<question-slug>.md` sink. (Adopt the *parallel subagent* half of that mechanic — #3 — just not the branch.)
- **`disable-model-invocation: true`.** Playbook §1: this repo doesn't use the field; a workflow is user-only by channel already.
- **`wayfinder:*` label namespace.** StratOS uses `concept:*`, registered in `src/memory-templates/BACKLOG_MAP.md`. Renaming breaks the registry and Phase 0's query for no gain.
- **Dropping the convergence phase.** Wayfinder ends at "the way is clear"; `1c`'s Phase 3 (brief + RAT + HITL gate + glossary) is the StratOS differentiator.
- **`/setup-matt-pocock-skills` tracker-config indirection.** `concept-map-operations.md` already fills that role.

## Execution shape (if approved)
1. `src/workflows/1c_concept-map.md` — P1 #2,3,5,6 + P2 #7–15 (+ P3 as chosen). `minor` bump (behavior), one bump for the whole PR.
2. `src/references/concept-map-operations.md` — P1 #1 ticket body template. `minor`.
3. `src/references/concept-map-template.md` — P1 #5,6 + P2 #11 (+ #19). `patch`/`minor`.
4. `src/references/discovery_brief_template.md` — P1 #4 `## Decision Trail`. `minor`.
5. Optional: `src/references/grilling-protocol.md` (new) + repoint `1b`, `1c`.
6. `python build/build.py` → `python build/validate.py` green. Run the §4 post-prune diff gate on every reworded span (net effect here is additive, so the gate is mostly a no-op — but apply the §4.5 word-economy pass to the *new* prose so `1c` doesn't sprawl past its current ~77 lines by more than the added behavior warrants).
7. Commit per AGENTS.md §4 message format; push to `claude/1c-workflow-optimization-3fk2f4`.

**Verification limit:** no way to end-to-end run a concept map here (needs `gh` + a live tracker + a human). Verifiable: `build/validate.py`, OKF frontmatter, pointer paths resolve. State the rest as unverified.
