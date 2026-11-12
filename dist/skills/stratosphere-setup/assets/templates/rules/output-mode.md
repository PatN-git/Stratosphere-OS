---
trigger: always_on
title: Output Mode Protocol
description: Guidelines to maximize information density and minimize token waste in agent responses.
timestamp: 2026-11-12
version: "2.1.0"
---

# Output Mode Protocol

## 1. Goal
Maximize information density while minimizing token waste. Focus on *what was done* and *what changed* rather than narrating the process.

## 2. Decision Matrix

| Mode | Task Type | Output Structure |
| :--- | :--- | :--- |
| **Routine** | Trivial, cosmetic, or repetitive mechanical tasks. | Skip plan. Execute immediately. Max 1 line of keyword-only status. |
| **Advisory** | A question, explanation, or recommendation with no file change. | Answer first (BLUF). No preamble or recap; length matches the question. |
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
- **Word economy:** Drop any word whose removal does not change meaning. Prefer the shortest phrasing that preserves intent for the reader (e.g. "in order to" → "to"; cut hedges and intensifiers).
- **No fillers:** delete any phrase whose removal loses no information — acknowledgements (e.g. "Sure", "Great"), flattery (e.g. "Great question"), self-narration (e.g. "Let me…"), and sign-offs (e.g. "Hope this helps").
- **Surgical narrative:** explain *why*, not *how*.
- **Direct verification:** show results, not process.
- **Disclose omissions:** if you cap, sample, truncate, or withhold anything (top-N, "and more", sub-threshold findings, an unread source), state the count and what was dropped. Never present a partial set as complete.
- **No preamble or recap:** open on content, not by restating the question; don't close with unnecessary summary if answer is short.
- **Memory discipline:** follow `.agents/rules/memory-protocol.md` and `.agents/rules/okf-protocol.md` for all memory and document operations.

## 5. Presentation & Question Contract
When prompting a user for confirmation, approval, or decision direction at an interactive decision gate using native question tools (`ask_question` on Antigravity; `AskUserQuestion` on Claude Code):
1. **Tool Execution Barrier:** 100% completion of all background tasks, subagent delegations, file operations, and scripts prior to opening the interactive turn. No background tools or script executions may run in the same turn as the question prompt.
2. **Mandatory Visible Markdown Content:** The complete evidence table, diff, proposal summary, or decision card must be emitted directly in the user-visible message `content`. Emitting question tools with empty message content (`Content: None` or blank body) or hiding evidence inside tool parameters or folded accordions is strictly prohibited.
3. **Synchronous Pairing:** The question tool call must accompany the visible markdown in the same presentation turn (never emitted before the content or in a separate follow-up turn without evidence).
4. **Non-Interactive Fallback Contract:** If running on non-interactive hosts or without native question tool support, output the complete markdown evidence and the decision options directly in visible message text and halt execution awaiting explicit user response.
