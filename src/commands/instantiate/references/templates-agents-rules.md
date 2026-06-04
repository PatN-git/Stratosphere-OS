---
description: Verbatim templates for the core .agents/rules/* files
---

# Agent Layer Templates — Rules

Verbatim templates for the two rule files in `.agents/rules/`.

## Table of contents

1. `.agents/rules/output-mode.md`
2. `.agents/rules/memory-protocol.md`

---

## 1. `.agents/rules/output-mode.md`

```markdown
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
- **No fillers:** avoid "I understand," "Sure," "Great," or "I'll get right on that."
- **Surgical narrative:** explain the *why*, not the *how*.
- **Direct verification:** show results, not process.
- **Memory discipline:** follow `.agents/rules/memory-protocol.md` for all memory operations.
- **Persona discipline:** follow `.agents/rules/persona-protocol.md` when a persona is active.
```

---

## 2. `.agents/rules/memory-protocol.md`

```markdown
# Memory Protocol

Single source of truth for how the agent reads, writes, and maintains the `.memory/` layer.

## 1. Trust Tags

Every entry in `LEARNINGS.md`, `GLOSSARY.md`, `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, and `DESIGN_RULES.md` carries exactly one trust tag.

`DESIGN.md` is **exempt** — external spec, validated by `npx @google/design.md lint`.

| Tag | Meaning | Where it lives |
|:---|:---|:---|
| `[LAW]` | Never violate. Hard constraint from code, DB, framework, or design governance. | `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, `DESIGN_RULES.md`. `LEARNINGS.md` only for code-vs-DB conflicts. |
| `[PATTERN]` | Established practice. Override requires justification. | `LEARNINGS.md`, `GLOSSARY.md`. |
| `[GUESS]` | Speculative or unverified. | `LEARNINGS.md`, `GLOSSARY.md`. |

### Promotion rules

- **New entries default to `[GUESS]`.**
- **`[GUESS] → [PATTERN]`**: cite ≥2 occurrences across distinct tasks. Agent may self-promote with evidence.
- **`[PATTERN] → [LAW]`**: explicit human confirmation required. Agent NEVER self-promotes to `[LAW]`. `GLOSSARY.md` entries never reach `[LAW]` — vocabulary is not architectural law.

### Demotion / challenge

- Agent SHOULD challenge a `[GUESS]` conflicting with observed code behavior.
- Agent MAY propose demoting a `[PATTERN]` violated successfully ≥2 times without harm.
- `[LAW]` is never demoted — it is superseded (§3).

## 2. Cross-References

| ID | Lives in |
|:---|:---|
| `[[BT-xxx]]` | `BACKLOG_MAP.md` |
| `[[L-xxx]]` | `LEARNINGS.md` |
| `[[A-xxx]]` | `ARCHITECTURE.md` |
| `[[DR-xxx]]` | `DESIGN_RULES.md` |
| `[[G-xxx]]` | `GLOSSARY.md` |

### EXAMPLES Bidirectional linking

- Entry born from a task: `Source: [[BT-42]]`.
- Task depending on an entry: `Ref: [[L-12]], [[G-005]], [[DR-020]]`.
- Lint validates all links every `/stop-session`.

## 3. Supersession (in-file)

When a rule changes, move the old entry to `## Superseded` in the **same file**:
- `[SUPERSEDED BY [[ID]]]` tag
- One-line reason
- Date or version

`## Superseded` is read only when explicitly triggered. No separate archive file.

## 4. Lint (at /stop-session)

Enforced deterministically by `.agents/scripts/validate_memory.py`. Propose fixes for any reported errors, list any warnings, and await confirmation.

## 5. What never happens

- Never self-promotes to `[LAW]`.
- Never deletes to supersede — moves to `## Superseded` with tag.
- Never silently rewrites memory during crystallization or lint.##
- Never reads `## Superseded` unless explicitly asked.
- Never writes to any `.memory/` file without proposing and awaiting user confirmation.
- Never write secrets, API keys, tokens, or PII to any `.memory/*` file. Redact before recording a learning.

## 6 Retrieval & Scale
- Never read `## Superseded` unless the task explicitly needs history.
- Resolve refs by ID, not by file - e.g. to follow a `[[L-xxx]]` reference, grep for that exact ID — do not read the whole memory file.
```