---
description: Canonical templates for StratOS backlog issues (Template A for spikes/discovery, Template B for normal vertical slices).
version: "1.0.1"
timestamp: 2026-07-10
---

# Issue Templates

## TEMPLATE A: Discovery & Spikes
*Use for: Rapid capture, "parking" vibes, or high-uncertainty research. Always label as `status:needs_spec` (note that leaves get `type:` + `mode:` + `tier:slice` + `size:`)*

### Overview
- One sentence: what and why.
- **Mental Model:** 2-3 bullets on core logic or specific question to answer.

### Dependencies
- Relation to existing tasks/files.

### Actionable Research Steps
- *List 3-4 concrete, stepwise checks, codebase symbols to inspect, or quick experiments/commands to run.*

### Exit Criteria & Deliverables
- *Specify the exact proof, prototype code, or memory artifact required to answer the question and unblock downstream Template B slices.*

### Blockers
- What must be resolved before this can move to a Vertical Slice (Template B)?

---

## TEMPLATE B: Normal Issue (Vertical Slice)
*Use for: Active builds. Must be deterministic.*

### Overview
- One paragraph: Business value, no jargon.
- **Mental Model:** 2-3 bullets on core logic or specific question to answer.

### ICE Priorities
- **Impact:** [Value]
- **Confidence:** [Value]
- **ICE Score:** [Calculated Score]

### Current state / Problem
Describe the behavior/interface that is wrong — name the affected type(s), function signature(s), and behavioral contract, and state what it does now vs. what it should do. (If a precise locator is unavoidable, prefer a symbol name over a line number).
Must cite the governing design/architectural laws violated (e.g. violates `[[A-xxx]]` or `[[DR-xxx]]`).

### The Path (Vertical Slice Flow)
- [ ] **Data Layer:** (Schema/RLS updates, Validations)
- [ ] **Logic Layer:** (Hooks/API/Functions/Shared Business Logic)
- [ ] **UI Layer:** (Components/Loading states/Error handling)

### Acceptance Criteria (Verifiable)
- [ ] **Verification:** [Specific test/run command]
- [ ] Feature is demoable end-to-end.
- [ ] **Time-to-Value:** Meets the aha-moment time-to-value constraint (from design doc).
- [ ] **Stress Cases:** Implements the handling for relevant adverse conditions in the Stress Matrix (from design doc).

### Dependencies
- **[[ID]] first** (blocks/blocked-by).

### Notes
Edge cases, trade-offs, and `.memory/LEARNINGS.md` traps.
