---
name: 1c_concept-map
description: Chart decisions as tickets on tracker and converge them to discovery brief.
type: workflow HITL
trigger: manual
version: "1.0.4"
timestamp: 2026-07-17
---

# Concept Map Workflow

**Purpose:** Deconstruct complex, multi-session ideas into dependency-ordered tracker tickets, resolving one per session to converge to discovery brief.

**Hand-off contract:** Composes `/1a_research` and tracker operations in `.agents/workflows/.reference/concept-map-operations.md`. Converges to discovery brief (`docs/discovery/<slug>.md`, type `discovery-brief`).

---

## Phase 0: Resume & Route

1. **Start Session:** Run `/0a_start-session` to load context.
2. **Discover Open Maps:** Query open concept maps:
   - **GitHub CLI:** `gh issue list --label concept:map --state open`
   - **BT-LOCAL Fallback:** Scan `docs/discovery/*.map.md` for open maps.
3. **Map Selection:** Present open maps. Resume existing map (proceed to Phase 2: Work) or proceed to Phase 1: Chart to start new map.
4. **Fog-or-Flat:** If new map, assess complexity. Single-session and no dependencies → redirect `/1b_concept-framing`; else proceed to Phase 1: Chart.

---

## Phase 1: Chart

1. **Destination:** Define destination and scope.
2. **Breadth-First Scan:** Scan for ambiguity and dependencies. If no fog, compile brief inline or hand off to `/1b_concept-framing`.
3. **Register Map:**
   - **GitHub CLI:** Create `concept:map` issue using `.agents/workflows/.reference/concept-map-template.md`. Add map row to `.memory/BACKLOG_MAP.md` (status: `in progress`, milestone-exempt).
   - **BT-LOCAL Fallback:** Create `docs/discovery/<slug>.map.md` using template; row in `BACKLOG_MAP.md`.
4. **Create-and-Wire Decision Tickets:** Create child issues:
   - Label `concept:<type>` (`research`, `grilling`, `prototype`, `task`).
   - Link as sub-issues (`gh sub-issue add <map#> <N>`).
   - Wire dependencies (`gh issue edit <N> --add-blocked-by <ids>`) if blocked.
5. **Halt Charting:** Do not resolve decisions during charting; hand off map to user.

---

## Phase 2: Work

1. **Calculate Frontier:** Query the tracker to compute the "frontier" (the set of open, unblocked, unassigned decision tickets):
   - Open tickets with no open dependencies/blockers and no assignee.
2. **Select & Claim Ticket:** Present the frontier to the user. The user select (or the agent picks) one ticket.
   - **Claim:** Assign the ticket to yourself (`gh issue edit <N> --add-assignee @me`) to lock the ticket.
3. **Grilling Guidelines (G1-G3):**
   - **G1 (Recommend when grounded, open when not):** If you have a defensible basis for an answer (a codebase fact, prior art, research, or a clear best practice), give your recommended answer and the rationale, then ask the user to confirm, correct, or choose. If the answer is a genuine user decision you lack signal on, ask open-ended first and let the user frame it — then reflect a synthesis back to confirm. A recommendation is a proposal to react to, never a default that passes unexamined.
   - **G2 (Facts vs Decisions):** If a codebase exists, look up facts (constants, configurations, API schemas, file structures) natively first. Do NOT grill the user on facts that are discoverable in the codebase; only grill them on decisions (preferences, constraints, desired outcomes) — a decision is the user's — put each and wait; recommending a candidate (G1) does not make the decision — only the user's confirmation does. (Also guards an AFK agent against grilling itself.)
   - **G3 (Dependency Order):** Resolve dependency chains sequentially.
4. **Vocabulary Discipline (V1-V3):** Apply V1 (Scenario stress-test), V2 (Code-contradiction check), and V3 (Glossary-conflict check) to all vocabulary terms.
5. **Resolve Ticket by Type:**
   - **`research`:** Run `/1a_research` Phase 1 inline, spawn research subagent to run research loop, and save the result as `docs/research/<map-slug>-<question-slug>.md`.
   - **`grilling`:** Grill to resolve the decision.
   - **`prototype`:** Run `plan-html` (UI) or Template A spike (logic).
   - **`task`:** Execute action (e.g. provision access) to unblock a decision.
6. **Ticket Resolution Commit:**
   - Comment the resolution on the ticket and close the ticket.
   - Index the resolved ticket on the map body under `Decisions so far`.
   - Update the map: create-then-wire newly surfaced tickets, graduate sharp fog, or mark mis-scoped tickets as out-of-scope.
7. **Halt Work:** Resolve only one dependency step per session (though independent, cheap frontier tickets may be batched if they fit the context limit), then stop.

---

## Phase 3: Converge

1. **Convergence Condition:** Run Phase 3: Converge only when frontier and fog are empty.
2. **Synthesize Brief:** Compile resolutions and research into brief `docs/discovery/<slug>.md` via template (type: `discovery-brief`).
3. **RAT Audit:** Invoke a subagent to challenge brief:
   - *RAT Guardrail:* "Review brief for logical gaps, contradictions, or unaddressed assumptions. Report findings only; do not edit files."
4. **Crystallize Vocabulary:** Write confirmed terms to `.memory/GLOSSARY.md` as `[[G-xxx]] [ASSUMED]`.
5. **Archive Lifecycle:** Close `concept:map` issue. Set map row status in `BACKLOG_MAP.md` to `status:done`.
6. **Hand-off:** Expose brief. Trigger `/2a_write-prd` or exit ramps.
