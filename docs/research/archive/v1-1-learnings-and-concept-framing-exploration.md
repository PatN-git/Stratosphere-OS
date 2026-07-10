---
name: v1-1-learnings-and-concept-framing-exploration
description: Review/analysis record of the external skills v1.1 learnings triage and the exploration history that led to the concept-framing investigation-hub design. Record only — active work lives in the linked proposals.
type: research
trigger: User. Do not run autonomously.
version: "0.3.0"
timestamp: 2026-07-08
---

# Review & Exploration Record: v1.1 skills learnings + concept-framing hub

> **This is a record, not an active plan** (moved here from `docs/proposals/`). Active work has been split out:
> - **Wayfinder / concept-framing hub** → carried forward in the focused plan [`../proposals/FEAT-wayfinder-concept-framing-hub-proposal.md`](../proposals/FEAT-wayfinder-concept-framing-hub-proposal.md). Sections §3/§7/§8 below are its design history.
> - **Code-review & TDD learnings (L2/L3/L8)** → **IMPLEMENTED** (spec: [`../proposals/FEAT-code-review-and-tdd-v1-1-learnings-proposal.md`](../proposals/FEAT-code-review-and-tdd-v1-1-learnings-proposal.md)). See the triage in §2.

**Origin:** Review of an external skills release **v1.1** (`/wayfinder`, `/to-spec`, `/to-tickets`, `/grilling`, two-axis `/code-review`, `/tdd`). The driving idea is the user's own long-standing intent: `1b` was named **concept_framing** because framing a concept is *either* a single grill *or* a multi-session mapping of a foggy space — it was always meant to route.

> **Decisions locked during the exploration:**
> - **`concept-framing` becomes an orchestrator/hub** routing an intake to (A) a single-session grill for a sharp/small idea, or (B) a multi-session wayfinder path for a foggy/oversized one.
> - **Wayfinder sits *under* concept-framing and produces the *same* discovery brief** (`docs/discovery/<slug>.md`) → `/2a_write-prd`. Same destination, different path length.
> - **Wayfinder reuses existing StratOS primitives** (see §3.3) — no parallel machinery.
> - **Do NOT collapse `3a`/`3b`/`3c`.** StratOS deliberately splits release-planning / slicing / sprinting for milestone+sprint tracking. The split stays.

> **Cross-proposal constraint (inherited):**
> The parked [`../proposals/FEAT-planning-soundness-and-impact-check-proposal.md`](../proposals/FEAT-planning-soundness-and-impact-check-proposal.md) proposal locked **"NO separate prototype skill"** (runnable-throwaway needs are covered by `3b` Template A spikes + `micro-tdd`; `plan-html` is a render-only layer). Wayfinder's **Prototype ticket type** is reconciled *within* that constraint (dispatch to `plan-html` / `3b` Template A), not by adding a new skill.

---

## 1. Why this exists

StratOS's discovery pipeline (`1a → 1b → 2a → 2b → 3a…`) assumes the idea is already articulable enough to grill in one `1b` session and then write up. `/wayfinder` names the phase *before* that: a loose idea "too big for one agent session and wrapped in fog," where you can feel the shape but can't yet state the spec. Today `1b` has no multi-session, decision-graph path — a big foggy effort either blows the smart zone in one grill or gets prematurely forced into a PRD. Making concept-framing route between grill and wayfind closes that gap using machinery StratOS mostly already has.

Architecturally this is sanctioned: AGENT.md §1 explicitly allows *"a user-invoked orchestrator workflow [to] sequence other workflows as part of its authorized run."*

---

## 2. Full v1.1 learnings triage

| # | v1.1 learning | StratOS today | Decision / Status | Home |
|---|---|---|---|---|
| L1 | **Wayfinder** — multi-session fog-mapping via decision tickets w/ blocking edges | no equivalent | **ADOPT** — in design | [wayfinder proposal](../proposals/FEAT-wayfinder-concept-framing-hub-proposal.md) (§3/§7/§8 here = history) |
| L2 | **Two-axis `/code-review`** — separate *Standards* (code-smell baseline) + *Spec* reviewers, aggregated independently | `4a` was single-axis (business-logic/security only) | **✅ IMPLEMENTED** | [code-review/tdd proposal §1](../proposals/FEAT-code-review-and-tdd-v1-1-learnings-proposal.md) |
| L3 | **Seam pre-agreement + test cadence** — declare seams before writing tests; type-check regularly, single test files during loop, full sweep at end | `micro-tdd` jumped to RED; no explicit seam declaration | **✅ IMPLEMENTED** | [code-review/tdd proposal §2](../proposals/FEAT-code-review-and-tdd-v1-1-learnings-proposal.md) |
| L4 | **Prototype-before-spec** — rough artifact to raise discussion fidelity, esp. front-end | `2b` is post-PRD; no discovery-time prototype | **RESOLVED** — no new skill (plan-html UI / `3b` Template A logic); folded into the hub's prototype investigation | wayfinder proposal |
| L5 | **Grilling fixes** — explain *why* one-question, confirmation gate, **Facts vs Decisions** leading words to stop self-grilling (AFK) | `1b` has one-question + Phase-6 gate; no Facts/Decisions split | **ADOPT** — folds into the extracted grill loop | wayfinder proposal (§2.8 there) |
| L6 | **`/to-spec`** rename — "spec" > "PRD" | `1b`(interview) → `2a`(synthesize) split already does this | **REJECTED** — keep "PRD"; StratOS `2a` is genuinely product-focused | note only |
| L7 | **AFK-autonomous `/tdd`** | `type:AFK` slices + `micro-tdd` silent mode | **ALREADY AHEAD** | — |
| L8 | **Refactor moved OUT of the TDD loop** into code-review | `3d`/`micro-tdd` keep REFACTOR in-loop + `code-simplifier` | **✅ IMPLEMENTED** — decided to **keep** `3d` Phase 2 in-loop (no change) | [code-review/tdd proposal §3](../proposals/FEAT-code-review-and-tdd-v1-1-learnings-proposal.md) |
| L9 | **`/to-tickets` two-mode** (local `tickets.md` vs native blocking) | `3b` already does GitHub-else-local | **ALREADY SATISFIED** | — |
| L10 | **StratOS is ahead** on subagent isolation, ICE/ODI, coverage auditor | — | keep | — |

---

## 3. The design (history) — router → hub

> **Note:** §3 captured the first framing (add a WAYFIND *mode* to `1b`). It was superseded by the §7 pivot (concept-framing becomes the hub). The current, cleaned design lives in the [wayfinder proposal](../proposals/FEAT-wayfinder-concept-framing-hub-proposal.md). §3/§7/§8 are retained here as the exploration trail.

### 3.1 The routing gate (extends `1b` Phase 0)
`1b` already infers **Sharpen vs Generate** (clarity of the idea). Wayfinder adds an orthogonal **size/fog** axis (can this reach a brief in *one* session?). Combined router at intake:

```
concept-framing — Route
  Q1 (fog):  is the destination a web of unresolved decisions, or one graspable problem?
  Q2 (size): can it be grilled to a discovery brief in ONE session,
             or will it blow the smart zone / context window?
   ├─ graspable & one-session      → GRILL  (current 1b phases, unchanged)
   └─ foggy / multi-session         → WAYFIND (mapped path)
```

### 3.2 The wayfind path (multi-session)
1. **Chart (session 1):** build a **decision map** indexing child **decision tickets** (not implementation slices) with native blocking edges + a *"Not yet specified"* fog section + *Destination* + *Out of scope*. The map is an **index, not a store**.
2. **Resolve (sessions 2..n):** each session takes one **frontier** ticket (open + unblocked), resolves it, records the answer, closes it, appends a one-line summary to *Decisions so far*, and surfaces any newly-visible fog as new tickets.
3. **Converge:** when nothing is left to decide → synthesize the map into `docs/discovery/<slug>.md` → `/2a_write-prd`.

### 3.3 Ticket-type → StratOS primitive mapping
| Wayfinder ticket type | Nature | StratOS primitive |
|---|---|---|
| **Research** | AFK, investigate + report | `/1a_research` (Quick or Deep) writing `docs/research/<slug>.md` |
| **Grilling** | HITL, decide via interview | the **extracted shared grill loop** |
| **Prototype** | raise discussion fidelity | `plan-html` (UI/interaction, render-only) or `3b` Template A spike (runnable logic) — no new skill |
| **Task** | config/provisioning, no grill | `3b` Template A / small task |

### 3.4 Extract the grill loop (enabling step)
Both router branches grill, and wayfinder's Grilling tickets grill too. Extract the loop — one-question-at-a-time (+ *why*), **Facts vs Decisions** leading words (stops AFK self-grilling), name-the-vagueness, ~5-question check-in, confirmation gate — into a shared reference invoked by grill, the wayfind path, and reusable by `2a`.

---

## 7. Pivot (2026-07-08) — concept-framing as the investigation hub

**Model.** `concept-framing` moves to the front of the lifecycle and becomes an **orchestrator hub**, not a single grill stage. It assesses the intake and **dispatches** one or more **investigation sub-sessions**, each producing its own artifact, then **re-integrates** them and **crystallizes a single final artifact** (the discovery brief) that `2a_write-prd` consumes (name kept). The hub *is* the map; the sub-sessions *are* the ticket types; a sharp/small idea skips dispatch and grills inline.

**Flow:**
```
intake → [concept-framing HUB] → dispatch {research, brainstorm, grilling, prototype}
       → each writes its artifact → hub re-integrates → discovery brief (final artifact)
       → 2a_write-prd → 2b → 3a → …
```

**Decisions:**
- **Numbering / skill-vs-workflow: DEFERRED.** Criterion: *a unit never invoked directly by the user → **skill**; a unit that stands alone as user-invocable and/or is composed by an orchestrator (precedent: `4a_verify-and-ship` runs standalone AND inside `3z_afk-loop`) → **numbered workflow**.*
- **`write-prd` rename: REJECTED. Keep "PRD".**
- **Final-artifact name.** Keep "discovery brief".
- **Locks:** map storage = GitHub issue + BACKLOG_MAP mirror; research reuses `1a_research`; v1 scope = full incl. prototype (no new skill needed).

## 8. Concept spec (behavioural)

### 8.1 Role & output contract
Front-of-lifecycle entry. **Output contract unchanged:** produces `docs/discovery/<slug>.md` and hands to `2a_write-prd`. Nothing downstream changes.

### 8.2 Two operating modes
- **Direct (fast path)** — sharp, single-session idea → grill inline → write brief. ≈ today's `1b`. No map, no overhead.
- **Mapped (hub path)** — foggy / too big for one session → open a decision map, dispatch investigations across sessions, converge.
- **Discriminator:** can we reach a brief in *one* session, and is the destination *one graspable problem* or *a web of unresolved decisions*? (Vagueness alone ≠ mapped.)

### 8.3 Investigations
| Investigation | Nature | Artifact | Backed by |
|---|---|---|---|
| research | AFK | `docs/research/<slug>.md` | reuse `1a_research` |
| brainstorm | HITL | options/ideas table | extract today's `1b` Phase 0 |
| grilling | HITL | grill notes + locked decisions | extract the shared grill loop |
| prototype | HITL / AFK | UI mock **or** logic spike | `plan-html` / `3b` Template A — no new asset |
| task | AFK / HITL | config/provisioning done | `3b` Template A / small task |

### 8.4 The map (state)
GitHub tracking issue = store; lean `BACKLOG_MAP.md` row = mirror; local `docs/discovery/.<slug>.map.md` = fallback. Sections: **Destination · Frontier · Blocked · Fog · Decisions so far · Out of scope**. Native blocking edges gate order; the map is an index (gists + links).

### 8.5 Session model — *open behavioural choice*
Proposal: **each non-trivial investigation runs in its own session** (research AFK/background; grilling & prototype HITL) — the *map* absorbs the "where was I" state. Trivial investigations run inline. On resume, the hub reads the map + closed artifacts and picks the next frontier item. **Open:** per-investigation-own-session vs prefer-inline-spin-out-heavy-only.

### 8.6 Re-integration & crystallization
When the fog clears, the hub reads every closed ticket's artifact (primary sources) and synthesizes the **single discovery brief** from today's template, enriched with source links. **RAT** and **vocabulary crystallization** run at this step, as `1b` does now.

### 8.7 How today's `1a`/`1b` decompose (no behaviour lost)
- `1b` intake/scope + RAT + write-brief → the **hub skeleton**.
- `1b` Phase 0 brainstorm → **brainstorm** investigation.
- `1b` grill phases → **grilling** investigation (shared loop).
- `1a_research` → **research** investigation (reused whole).
- Direct mode reproduces today's `1b` path end-to-end.

## 6. Refinement log
- 2026-07-08 — initial draft created from the v1.1 review. Locked: concept-framing-as-orchestrator, wayfinder-under-concept-framing converging to the discovery brief, no `3a/3b/3c` collapse.
- 2026-07-08 — forks answered: map storage = GitHub+mirror; research reuses `1a`; scope = Full. Prototype reconciled with no new skill.
- 2026-07-08 — **PIVOT (§7):** concept-framing becomes the front-of-line investigation *hub* dispatching research/brainstorm/grilling/prototype and re-integrating into the brief.
- 2026-07-08 — split: **code-review/TDD (L2/L3/L8) implemented** via the standalone proposal; wayfinder design moved to its own focused proposal. This doc relocated to `docs/research/` as the review/exploration record.
