---
name: concept-brainstorm
description: Frame vague concepts via 4-phase execution loop (Constraints → Diverge → Triage → Validate).
type: skill
version: "1.4.1"
timestamp: 2026-07-24
---

# Concept Brainstorming Skill

Execute the 4-phase loop. Never output a bare list and halt.

## Anti-Default Guards
**CRITICAL:** No generic numbered lists.
1. Strictly follow the 4-Phase loop.
2. Rigidly output the exact contract for the selected technique.
3. **Escape Hatch:** If diverging from the Selection Guide, explicitly name the custom technique and define its strict tabular `Output` contract *before* generating ideas.

---

## Execution Loop

### Phase 1: Analysis (Constraints)
- **Method:** `CHAIN Framework`.
- **Action:** Confirm Context, Outcomes, Boundaries, and Non-goals. Await sign-off.

### Phase 2: Generation (Diverge)
Read `references/techniques.md` to load the Selection Guide.
- **Action:** Recommend Path A (high complexity) or Path B (standard); await confirmation.
  - **Path A (Subagent Swarm):** Spawn PM, Designer, and Engineer subagents. Inject Phase 1 constraints explicitly (no discovery). Assign each ONE specific technique from the Selection Guide fitting their persona. Synthesize outputs into one table.
  - **Path B (Single-Agent):** Execute ONE technique from the Selection Guide.
  - **Escape Hatch:** Valid for both paths if no standard technique fits (must obey Guard #3).

### Phase 3: Synthesis (Triage)
- **Method:** `Pre-ICE Triage`.
- **Action:** Score top candidates by Impact. Ask user for Confidence score. Agree on one winner.

### Phase 4: Validate
- **Method:** `Opportunity Solution Tree`.
- **Action:** Frame winner: Outcome → Opportunities → Solutions → Experiments. Present riskiest assumptions for final approval.


