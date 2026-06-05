# <PERSONA NAME> PERSONA

> Copy this file to `.agents/workflows/<persona-name>.md` and fill in the placeholders. This template itself is not a runtime file — the leading underscore marks it as a template.

## Role
<One-sentence description of what this persona does and when to use it.>

## Required reads (on activation)
1. `STATUS.md` (already loaded by `/0a_start-session`).
2. `.agents/rules/persona-protocol.md` — framework rules.
3. `.agents/rules/memory-protocol.md` — memory discipline.
4. <Domain-specific memory files this persona needs, e.g. `.memory/DESIGN.md` and `.memory/DESIGN_RULES.md`>
5. <Other context files, e.g. relevant code paths>

## Commands

> Fill in commands as the persona's responsibilities are defined.
> Each command needs: name, one-line purpose, inputs, output artifact, autonomy classification (read-only or mutating).

### /<command-name-1>
- **Purpose:**
- **Inputs:**
- **Output artifact:**
- **Autonomy:** [read-only / mutating-proposes]

### /<command-name-2>
- **Purpose:**
- **Inputs:**
- **Output artifact:**
- **Autonomy:** [read-only / mutating-proposes]

## Handoff

When finishing, update `STATUS.md` per `persona-protocol.md` §6:
- Active Persona: <persona-name>
- Completed This Session: <what was produced>
- Persona Artifacts Produced: <filepath / issue / memory IDs>
- Next Immediate Step: <next concrete action>
- Suggested Next Persona: <persona-name or none>

## Constraints
- Apply the autonomy rule from `persona-protocol.md` §5: auto for read, propose for write.
- Never self-promote memory entries to `[LAW]`.
- Never enter persona theater. Exit cleanly when the task is done.
