---
name: 1c_concept-map
description: Chart decisions as tickets on tracker and converge them to discovery brief.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.2"
timestamp: 2026-07-09
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

1. **Calculate Frontier:** Query tracker for frontier (open, unblocked, unassigned tickets).
2. **Select & Claim:** Present frontier. Claim ticket: assign to self (`gh issue edit <N> --add-assignee @me`).
3. **Guidelines:** Apply G1-G3 (grill guidelines) and V1-V3 (vocabulary discipline) from 1b.
4. **Resolve by Type:**
    - **`research`:** Run `/1a_research` inline, spawn research subagent, save to `docs/research/<map-slug>-<question-slug>.md`.
    - **`grilling`:** Grill.
    - **`prototype`:** Run `plan-html` (UI) or Template A spike (logic).
    - **`task`:** Execute action.
5. **Commit Resolution:** Comment and close ticket. Index on map body under `Decisions so far`. Update map (wire new tickets, graduate fog, or mark mis-scoped tickets out-of-scope).
6. **Halt Work:** Resolve only one dependency step per session and stop (cheap frontier tickets can be batched).

---

## Phase 3: Converge

1. **Convergence Condition:** Run Phase 3: Converge only when frontier and fog are empty.
2. **Synthesize Brief:** Compile resolutions and research into brief `docs/discovery/<slug>.md` via template (type: `discovery-brief`).
3. **RAT Audit:** Invoke a subagent to challenge brief:
   - *RAT Guardrail:* "Review brief for logical gaps, contradictions, or unaddressed assumptions. Report findings only; do not edit files."
4. **Crystallize Vocabulary:** Write confirmed terms to `.memory/GLOSSARY.md` as `[[G-xxx]] [ASSUMED]`.
5. **Archive Lifecycle:** Close `concept:map` issue. Set map row status in `BACKLOG_MAP.md` to `status:done`.
6. **Hand-off:** Expose brief. Trigger `/2a_write-prd` or exit ramps.
