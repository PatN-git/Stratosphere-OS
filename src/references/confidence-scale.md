---
description: Generic confidence scale and scoring rubric shared by StratOS audits (4a verify-and-ship, 4b audit-architecture-drift). The invoking workflow declares its audit scope; this file defines how to score against it.
version: "1.1.0"
timestamp: 2026-06-22
---

# Confidence Scale

Score every finding 0–100 against the **audit scope declared by the invoking workflow**. Confidence is the combined judgment across four dimensions:

## Scoring Dimensions
1. **Evidence strength** — Is the finding directly visible in the inputs (issue/PRD, design doc, tests, code, or `.memory/` guidance), versus inferred?
2. **Scope relevance** — Does it fall within *this workflow's declared audit scope*? Out-of-scope findings are discarded regardless of merit.
3. **Practical impact** — Would it cause a real failure, gap, or risk in normal operation if left unaddressed?
4. **Actionability** — Can it be turned into a specific, verifiable change?

## Banding Anchors
- **0–39: Discard** — Speculative, stylistic, pre-existing without current impact, already tracked, or out of scope. Do not mention in output.
- **40–69: Weak Signal** — Possibly valid, but evidence is incomplete, impact is low, or it rests on unstated assumptions. Do not report unless exploratory findings are explicitly requested.
- **70–79: Near Miss** — Likely valid and in scope, but missing direct evidence, clear impact, or immediate actionability. Use internally only; do not report.
- **80–89: Report** — Strong, directly-evidenced finding that a stated in-scope rule or criterion is unmet, with clear practical impact. Include in output.
- **90–100: Critical / Confirmed** — Directly proven violation of a stated in-scope rule or criterion, likely to cause a serious or repeated failure. Include in output.

## Threshold Rule
- **Only report findings with confidence ≥ 80.**
- When in doubt, lower the score and discard.
