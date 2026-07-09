---
name: 1c_concept-map
description: Chart a concept map of decisions as tickets on the tracker and converge them to a discovery brief.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.1"
timestamp: 2026-07-09
---

# Concept Map Workflow

**Purpose:** Deconstruct a foggy, complex, multi-session idea into dependency-ordered decision tickets on the project's existing tracker, resolving one decision per session to converge systematically to a standard discovery brief.

**Hand-off contract:** Composes `/1a_research` and the tracker operations in `.agents/workflows/.reference/concept-map-operations.md`. Converges to a discovery brief (`docs/discovery/<slug>.md`, type `discovery-brief`) which is consumed identically by `/2a_write-prd`.

---

## Phase 0: Resume & Route

1. **Start Session:** Ensure `/0a_start-session` has been run to load context and state.
2. **Discover Open Maps:** Query for open concept maps in the tracker:
   - **GitHub CLI:** Run `gh issue list --label concept:map --state open`
   - **BT-LOCAL Fallback:** Scan `docs/discovery/*.map.md` for open maps.
3. **Map Selection:** 
   - If open maps exist, present them to the user. Allow resuming an existing map (transitioning directly to **Phase 2: Work**) or starting a new map.
   - If no map is selected/exists, proceed to **Phase 1: Chart** to bootstrap a new concept map.
4. **Fog-or-Flat Discriminator:** If starting a new map, assess the initial idea's complexity:
   - Does it fit in a single session?
   - Can all open questions be resolved immediately?
   - Is there a dependency graph of decisions, research spikes, or prototypes needed?
   - *Routing:* If the idea is flat (independent, user-decidable questions fitting one session), redirect to `/1b_concept-framing`. If it is foggy or has interdependencies, proceed with `1c` Charting.

---

## Phase 1: Chart

1. **Destination Definition:** Identify the core destination of the concept map. The destination defines the exact boundary of what the concept aims to accomplish, fixing the scope of the discovery phase.
2. **Breadth-First Grilling:** Conduct a breadth-first scan of the concept using the grilling guidelines:
   - Identify major open areas of ambiguity and dependency.
   - If no fog is surfaced (e.g. all questions are simple/flat), offer to compile a brief inline or hand off to `/1b_concept-framing`.
3. **Register Map:**
   - **GitHub CLI:** Create the `concept:map` tracking issue copying `.agents/workflows/.reference/concept-map-template.md`. Append the map row to `.memory/BACKLOG_MAP.md` (milestone-exempt, `status:in progress`).
   - **BT-LOCAL Fallback:** Create the local map file `docs/discovery/<slug>.map.md` copying the template, and row it in `BACKLOG_MAP.md`.
4. **Create-then-Wire Decision Tickets:** Create initial decision tickets for sharp questions as child issues:
   - Label as `concept:<type>` (`research`, `grilling`, `prototype`, or `task`).
   - Link as sub-issues to the map (`gh sub-issue add <map#> <N>`).
   - Wire native dependencies (`gh issue edit <N> --add-blocked-by <ids>`) if blocked by other tickets.
5. **Halt Charting:** Do not resolve any decisions during charting. Stop and hand off the map to the user.

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

1. **Convergence Condition:** Run Phase 3 only when both the frontier and the fog are empty.
2. **Synthesize Discovery Brief:** Compile all ticket resolutions and research files into the standard brief `docs/discovery/<slug>.md` using `.agents/workflows/.reference/discovery_brief_template.md` (set `type: discovery-brief`).
3. **RAT Audit (Adversarial Challenger):** Spawn a RAT subagent to challenge the brief:
   - *RAT Guardrail:* "Review the brief for logical gaps, contradictions, or unaddressed assumptions. Report findings only; do NOT edit files."
4. **Crystallize Vocabulary:** Write confirmed new domain terms into `.memory/GLOSSARY.md` as `[[G-xxx]] [ASSUMED]` terms.
5. **Archive Lifecycle:** 
   - Close the `concept:map` tracking issue.
   - Update the map's row status in `.memory/BACKLOG_MAP.md` to `status:done`.
6. **Hand-off:** Expose the completed discovery brief. Trigger `/2a_write-prd` or relevant exit ramps.
