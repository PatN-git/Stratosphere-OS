---
type: rule
title: Output Mode Protocol
description: Guidelines to maximize information density and minimize token waste in agent responses.
timestamp: 2026-06-16
---

# Output Mode Protocol

## 1. Goal
Maximize information density while minimizing token waste. Focus on *what was done* and *what changed* rather than narrating the process.

## 2. Decision Matrix

| Mode | Task Type | Output Structure |
| :--- | :--- | :--- |
| **Routine** | Trivial, cosmetic, or repetitive mechanical tasks. | Skip plan. Execute immediately. Max 1 line of keyword-only status. |
| **Standard** | Any non-trivial functional change. | 5-point brief: Assumptions, Plan, Execution, Verification, Updates. |
| **Complex** | Impacts `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, or `DESIGN_RULES.md`. | **Trade-off Brief** (Choice/Consequence) + Standard structure. |

## 3. Mode Specifications

### Routine Mode
- No preamble. No "I will now...".
- Response: optional 1-line status if tool feedback is insufficient.
- Example: `[DONE] Created /scratch. Moved verify_fix.py.`

### Complex Mode (Trade-off Brief)
- **Choice:** [1-sentence technical description]
- **Consequence:** [Direct impact on future build/logic]

### Standard Mode
1. **Assumptions**: [Short context]
2. **Plan**: [Surgical steps]
3. **Execution**: [The work]
4. **Verification**: [Results]
5. **Updates**: [Changes to docs/scripts]

## 4. General Constraints
- **No fillers:** e.g. avoid "I understand," "Sure," "Great," or "I'll get right on that."
- **Word economy:** Drop any word whose removal does not change meaning. Prefer the shortest phrasing that preserves intent (e.g. "in order to" → "to"; cut hedges and intensifiers).
- **Surgical narrative:** explain the *why*, not the *how*.
- **Direct verification:** show results, not process.
- **Memory discipline:** follow `.agents/rules/memory-protocol.md` and `.agents/rules/okf-protocol.md` for all memory and document operations.
