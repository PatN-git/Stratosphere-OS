# Persona Protocol

Single source of truth for how personas activate, operate, and hand off. Referenced by every persona file in `.agents/workflows/`.

## 1. What a persona is

A **persona** is a role you summon for a focused task: Designer, Analyst, PM, Full-Stack-Dev, Reviewer. Each persona:
- Loads its own subset of `.memory/*` files relevant to the role.
- Dispatches a small set of role-specific commands (e.g., `/audit`, `/polish` for Designer).
- Produces a durable artifact (code, document, GitHub update, memory entry).
- Hands off via `STATUS.md` — never via in-session state.

A persona is a **hat you put on for a task**, not an identity you maintain. No persona theater. No "stay in character." When the task is done, the persona ends.

## 2. Vocabulary

- **Persona** = a role workflow file in `.agents/workflows/` (e.g., `designer.md`).
- **Skill** = a capability registered in the environment (e.g., Impeccable, `instantiate-memory`). Personas may invoke skills.
- **Command** = a verb defined inside a persona's workflow (e.g., `/audit`, `/polish`). Dispatched by the persona, not the user-typed top-level slash command.

## 3. One-persona-per-session model

- Sessions are scoped to **one persona per session**.
- Personas do not switch mid-session.
- Personas do not call other personas in-session.
- Cross-persona work happens across sessions via `STATUS.md` artifacts.

This means personas don't need handoff protocols *between each other*. They only need a handoff protocol to `STATUS.md`.

## 4. Activation

### Two activation modes:

- **Explicit:** user types `/<persona>` (e.g., `/designer`) or `/<persona> <intent>` (e.g., `/designer audit navbar`).
- **Suggested:** the previous session's `STATUS.md` includes a `Suggested Next Persona` field. The user reads it after `/0a_start-session` and decides whether to follow.

### On activation, every persona MUST:

1. Read `STATUS.md` (already loaded by `/0a_start-session`, but re-confirm focus).
2. Read its required `.memory/*` files per its workflow definition.
3. Read this file (`persona-protocol.md`) and its domain-specific rule files.
4. If the user provided an intent (e.g., `/designer audit navbar`), dispatch directly.
5. Otherwise, present the persona's command menu and wait for input.

## 5. Autonomy rule: read-auto, write-propose

The persona is a **navigator**, not a black box. Apply this rule to every operation:

| Operation type | Persona behavior |
|:---|:---|
| **Read-only** (loading files, audits, analyses, lint reports) | Auto-invoke. No confirmation needed. |
| **Mutating** (writing code, modifying memory files, creating GitHub issues, modifying `[LAW]` entries) | Propose first. Wait for explicit confirmation. |

Edge cases:
- **Generating output for the user to review** (a draft PRD, a proposed component, a design audit summary): auto-invoke. The output is not yet committed — the user reviews and confirms.
- **Saving that output to a file or issue tracker:** propose first.
- **Crystallization, supersession, lint fixes:** always propose (per `memory-protocol.md`).

The agent never self-promotes an entry to `[LAW]`. This is a hard rule from `memory-protocol.md` and applies regardless of persona.

## 6. Handoff via STATUS.md

When a persona finishes, update `STATUS.md` with:

- **Active Persona (this session):** the persona that just ran
- **Completed This Session:** what was produced
- **Persona Artifacts Produced:** filepath, GitHub issue, or memory entry IDs
- **Next Immediate Step:** the next concrete action
- **Suggested Next Persona (if applicable):** which persona is best suited for the next step

The suggestion is text — no automation, no enforcement. The user reads it next session and decides.

## 7. Menu fallback

When activated without an intent, a persona presents its commands as a numbered menu:

```
[Persona] active. Choose a command:

1. /<command-1> — short description
2. /<command-2> — short description
3. /<command-3> — short description

Or describe what you want to do.
```

When the user replies with a number, command name, or fuzzy description, dispatch on a clear match. If two items are genuinely close, ask one short clarifying question.

Skip the menu if the activation message contained an intent (e.g., `/designer polish navbar` dispatches `/polish` directly with `navbar` as scope).

## 8. Exit

A persona ends when:
- Its dispatched command completes and the user has no follow-up.
- The user types `/stop` (begins the stop-session workflow).
- The user invokes a different persona (rare in the one-per-session model).

There is no persistent persona state. The next session starts fresh.

## 9. What never happens

- A persona never writes to `[LAW]`-tier files (`ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, `DESIGN_RULES.md` entries) or to `DESIGN.md` (external spec) without explicit user confirmation.
- A persona never invokes another persona in-session.
- A persona never persists state between sessions outside `STATUS.md` and `.memory/*`.
- A persona never enters "character" theater that resists exit.
