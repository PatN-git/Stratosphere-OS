---
description: Canonical templates for StratOS backlog issues (Spike for parked, high-uncertainty, or discovery items, Build slice for normal vertical slices).
version: "1.0.3"
timestamp: 2026-10-09
---

# Issue Templates

## SPIKE (Template A)
*Use for: parked, high-uncertainty, or discovery items. Label `status:needs_spec` plus `type:`, `mode:`, `tier:slice`, `size:medium`. Sprintable at the medium weight (3h), not buildable. Close on Exit Criteria; mint follow-up Build slices via `/3b-create-issue`.*

### Overview
- One sentence: what and why.
- **Mental Model:** 2-3 bullets on core logic or specific question to answer.

### Dependencies
- Relation to existing tasks/files.

### Actionable Research Steps
- *List 3-4 concrete, stepwise checks, codebase symbols to inspect, or quick experiments/commands to run.*

### Exit Criteria & Deliverables
- *Specify the exact proof, throwaway prototype (not merged), or memory artifact required to answer the question and unblock downstream Build slices.*
- [ ] Close this issue when the criteria above are met; set `status:done` on GitHub and in BACKLOG_MAP; mint follow-up work with `/3b-create-issue`.

### Blockers
- What must be resolved before the follow-up Build slice can be minted?

---

## BUILD SLICE (Template B)
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
- **Parent:** `BT-<padded>` — the epic this slice belongs to (bare ID; `—` if standalone). Mirrors the GitHub sub-issue parent and the BACKLOG `Parent` column.
- **Blocked by:** `BT-<padded>, …` — slices that must land first (bare IDs; `—` if none). Mirrors GitHub blocked-by and the BACKLOG `Blocked by` column.

### Notes
Edge cases, trade-offs, and `.memory/LEARNINGS.md` traps.
