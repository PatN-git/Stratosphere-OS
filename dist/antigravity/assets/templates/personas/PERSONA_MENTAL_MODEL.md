# Persona System — Mental Model & Working Approach

A handoff document to kickstart the next AI session on building the remaining personas (Analyst, PM, Full-Stack-Dev, Reviewer). Read this first before designing any new persona.

**Companion document:** `PRD_MODEL.md` — defines the PRD → Issue convention used by the PM persona and related skills. Read after this if working on PM-related design.

---

## 1. What I'm Building

A **persona/workflow layer** that sits on top of my existing memory system and helps me navigate the entire build journey — from initial brainstorming to final code review — without memorizing every `/command` across every skill.

The Designer persona is built. Four more to go: **Analyst, Product Manager, Full-Stack-Developer, Reviewer**.

## 2. My Setup

- **Solo Vibe Coder.** Hobby projects, high design standards.
- **Stack:** React, Supabase, Tailwind, shadcn/ui.
- **Tools:** Antigravity (primary IDE), Google Stitch (for design vibes, not source of truth), GitHub Issues (for backlog and tracking).
- **Working style:** vertical slices. A "feature" cuts across DB → backend → UI in one go.
- **Skill folder structure:** organized by lifecycle stage (`0-general`, `1-analysis`, `2-plan&design`, `3-Implementing`, `4-Reviewing`). This maps almost 1:1 to the personas.
- **Token efficiency matters.** I won't pay context cost for a persona unless it's earning its keep that session.

## 3. The Mental Model

### One persona per session

This is the load-bearing constraint. **A session = one role.** I don't switch personas mid-session. I don't have personas calling each other.

Why this works:
- Forces me to scope sessions tightly. "What am I doing right now — researching, planning, building, or reviewing?"
- Eliminates handoff complexity. Personas don't need to know about each other.
- Matches how I actually work — I do focused stretches, not multi-role juggling.

### Sessions hand off via `STATUS.md`, not in-session state

When a persona finishes its work, it:
1. Produces a **durable artifact** (code, document, GitHub issue update, memory entry).
2. Updates `STATUS.md` with what was done and a **suggested next persona**.

The next session reads `STATUS.md` and the user (me) decides whether to follow the suggestion. No automation, no enforcement. The artifact is the handoff. `STATUS.md` is the universal connector.

### The journey, in personas

A typical feature flows like this:

```
/persona_analyst   →  research brief in docs/research/  →  STATUS suggests /persona_pm
/persona_pm        →  PRD in docs/prds/ + parent issue  →  STATUS suggests /persona_designer or /persona_dev
/persona_designer  →  UI audit/polish/lock              →  STATUS suggests /persona_dev
/persona_dev       →  code + tests for sub-issue        →  STATUS suggests /persona_reviewer
/persona_reviewer  →  review + sign-off                 →  STATUS marks task done
```

Each arrow is a session boundary. Each persona produces something the next persona reads. **The whole flow is asynchronous** — sessions can be hours, days, or weeks apart. `STATUS.md` is what makes resumption frictionless.

## 4. File Layout (Two Distinct Areas)

The project has two **separate** areas for written context. Mixing them is a mistake.

```
.memory/                  # Agent memory layer (small, dense, lint-validated)
  STATUS.md               # Universal session connector
  LEARNINGS.md            # Episodic memory
  ARCHITECTURE.md         # Crystallized [LAW] rules
  DATABASE_SCHEMA.md      # Live DB ground truth
  BACKLOG_MAP.md          # Task index (references docs/prds/ and memory IDs)
  DESIGN.md               # Brand tokens (Google Labs DESIGN.md spec — external)
  DESIGN_RULES.md         # Project structural rules ([DR-xxx], [LAW]-tagged)

docs/                     # Project working files (human + agent authored)
  research/               # Analyst output
    YYYY-MM-DD-topic.md
  prds/                   # PM output (see PRD_MODEL.md)
    BT-<n>-<feature>.md   # Active PRDs
    archive/
      BT-<n>-<feature>.md # Shipped PRDs

.agents/                  # Workflow & rule files
  workflows/
    start-session.md
    stop-session.md
    designer.md           # First persona, built
    _persona-template.md  # Template for new personas
  rules/
    output-mode.md
    memory-protocol.md
    persona-protocol.md
```

### Why the split

- **`.memory/`** — agent state. Small, structured, lint-validated. Read often. The agent always knows what's here.
- **`docs/`** — project artifacts. Human-readable. Variable size. Read on demand. The agent reads these when a task references them.

`.memory/BACKLOG_MAP.md` references `docs/` paths in its `Ref` column, e.g.:
`Ref: docs/prds/BT-49-user-profiles.md, [L-12], [DR-020]`

### Note on `DESIGN.md` vs. `DESIGN_RULES.md`

These are two separate files with different governance:

- **`DESIGN.md`** follows the **Google Labs DESIGN.md spec** (open-source, Apache-2.0, alpha as of April 2026). It contains brand tokens (colors, typography, spacing, components) in YAML front matter plus markdown rationale. It is the file fed to Stitch and read by AI coding agents (Claude Code, Cursor, etc.). The team is a **consumer** of this spec, not its author. Validate manually with `npx @google/design.md lint .memory/DESIGN.md`. **Not subject to trust tags or `[DR-xxx]` IDs.**

- **`DESIGN_RULES.md`** is a **custom project file** for operational design governance. Contains design principles (Kill AI Slop, OKLCH preference), Stitch harmonization rules (Structural Shield), and immortal components — all `[LAW]`-tier with `[DR-xxx]` IDs. **Subject to trust tags and the memory protocol.**

Why split: brand tokens evolve slowly and must follow an external spec to remain interoperable with Stitch and other agents. Project rules evolve constantly and need trust tags, supersession, and lint validation. Mixing them in one file would either break the spec compliance or lose the governance machinery.

## 5. PRD → Issue Model

The full convention lives in **`PRD_MODEL.md`**. Read that document when:
- Designing the PM persona
- Revising the `write-prd` or `write-issue` skills
- Updating `BACKLOG_MAP.md` reference conventions

Quick summary (do not duplicate details — go to the source):
- PRD doc lives in `docs/prds/`, parent GitHub issue links to it
- Sub-issues are vertical slices, linked to parent in GitHub
- IDs use GitHub issue numbers: `BT-<n>` for parents, `BT-<parent>-<child>` for sub-issues
- PRD doc moves to `docs/prds/archive/` when parent issue closes

## 6. How Personas Work (The Framework)

All personas share the same shape, defined in `.agents/rules/persona-protocol.md`:

| Aspect | Behavior |
|:---|:---|
| **Activation** | Explicit (`/persona_<role>`) or suggested (via `STATUS.md` from prior session) |
| **Naming** | All persona invocations use the `/persona_` prefix to avoid collision with general skills (e.g., `/persona_designer`, `/persona_pm`) |
| **Session-context check** | If `STATUS.md` is not in context (i.e., `/start-session` hasn't run), persona auto-runs `/start-session` first, then proceeds |
| **Reads** | Role-specific `.memory/*` files, relevant `docs/*` files, `persona-protocol.md`, `memory-protocol.md` |
| **Autonomy** | Auto for read-only operations; propose before any mutating operation |
| **Commands** | Small set of role-specific verbs — dispatched by the persona, not typed at top level |
| **Menu** | Shown only if activation has no intent. Skipped if user says `/persona_<role> <intent>` |
| **Handoff** | Via `STATUS.md` fields: artifact location, next step, suggested next persona |
| **Exit** | Clean end when task is done. No persona theater. No "stay in character." |

The framework is the product. Each persona instantiates it.

## 7. Phase 0: Skill Inventory (Prerequisite — must complete before any persona work)

The personas are **navigators that orchestrate existing skills**. Designing a persona without knowing what skills are available is guesswork. Before building any new persona, run a dedicated session to take stock of all skills in the skill folder.

### Approach

For each skill in `0-general`, `1-analysis`, `2-plan&design`, `3-Implementing`, `4-Reviewing`:
- Skill name + 1-line purpose
- Top 3-5 commands and what they do
- Notes (e.g., A/B variants like `write-prd-a` vs `write-prd-b` — which to keep, deprecation candidates)
- Whether it's role-specific or cross-cutting

### Output

A reference document at `docs/skill-inventory.md` (or similar) that personas read on activation to know what's available.

### Special status of `0-general` skills

`Methods.md`, `SKILL_challenger.md`, and `SKILL_explore.md` are cross-cutting — they're not bound to any single role. Treat them as **modifiers**: any persona can invoke `/challenger` to get pushback on its current output, `/explore` to widen the search space, etc. The inventory should explicitly tag these as cross-cutting.

### Until inventory exists, persona definitions are guesswork

This dependency is hard. **Do not build Analyst, PM, Dev, or Reviewer until the inventory document exists.** The Designer was built before this rule because it was the prototype that surfaced the rule.

## 8. Designing a New Persona — The Five Questions

Once the skill inventory is done, walk through these questions in order for each persona:

### Q1: What is this persona's job, in one sentence?
- **Designer** (built): "Audits and polishes UI work, harmonizes Stitch output with immortal components, kills AI slop."
- **Analyst** (TBD)
- **PM** (TBD)
- **Dev** (TBD)
- **Reviewer** (TBD)

### Q2: What memory and doc files does it need to read?
Every persona reads (via `/start-session`): `STATUS.md`, `LEARNINGS.md`, `BACKLOG_MAP.md`. Additionally:
- **Designer** reads `.memory/DESIGN.md` (brand tokens), `.memory/DESIGN_RULES.md` (structural rules), and `.memory/ARCHITECTURE.md` (Tech Stack section).
- **Analyst** likely reads `.memory/LEARNINGS.md` (full), `BACKLOG_MAP.md`, and writes to `docs/research/`.
- **PM** reads `.memory/BACKLOG_MAP.md`, `docs/research/*`, **`PRD_MODEL.md`**, and writes to `docs/prds/` + GitHub.
- **Dev** reads almost everything — `.memory/ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, `DESIGN.md`, `DESIGN_RULES.md`, `LEARNINGS.md`, the relevant PRD in `docs/prds/`, plus code files.
- **Reviewer** reads what was produced + relevant memory + the parent PRD.

The principle: **read what you need, nothing more.** Token efficiency.

### Q3: What 3–5 commands does it dispatch?
Keep the set small. If a persona needs more than 5 commands, it's probably two personas pretending to be one.

Designer's commands as a reference:
- `/audit` (read-only inspection)
- `/polish` (mutating fix)
- `/harmonize` (mutating reconciliation with external source)
- `/lock-component` (mutating LAW-tier promotion)
- `/start-slice` (read-only briefing)

Pattern: at least one read-only "look at things" command, at least one mutating "do things" command, possibly one "promote to durable memory" command.

### Q4: What artifact does it produce?
Every persona must produce something durable.
- **Designer** — modified `.tsx` files, new `[DR-xxx]` entries in `DESIGN_RULES.md`, occasional updates to brand tokens in `DESIGN.md`.
- **Analyst** — research brief at `docs/research/YYYY-MM-DD-topic.md`.
- **PM** — PRD + GitHub issues per `PRD_MODEL.md`.
- **Dev** — code, tests, possibly new `[L-xxx]` learnings.
- **Reviewer** — review notes (where? — TBD: comment on the GitHub sub-issue is the natural answer), possibly new `[L-xxx]` learnings, possibly `[A-xxx]` proposals.

### Q5: Which persona should it suggest next?
Default suggestions per persona's natural flow. The `Suggested Next Persona` field in `STATUS.md` is just text — a recommendation, not a rule.

## 9. Architectural Principles (Don't Violate These)

These are the constraints that make the system coherent. Violating them creates the chaos the system was built to prevent.

1. **One persona per session.** No mid-session switching. No persona-to-persona calls.
2. **Personas hand off via artifacts, not state.** If a persona's output isn't readable by the next session without context, it's not done.
3. **Auto for read, propose for write.** No persona silently mutates memory or code.
4. **Personas never self-promote to `[LAW]`.** Hard rule from `memory-protocol.md`. Even Designer's `/lock-component` proposes — never writes directly.
5. **No persona theater.** No "embody this character." No "stay in character until dismissed." A persona is a hat, not an identity.
6. **Token efficiency.** Read only what's needed. If `DESIGN.md` (brand tokens) and `DESIGN_RULES.md` (structural rules) are solid, the Designer persona may not need to be invoked at all for routine UI work — the dev simply reads them.
7. **The framework is the product.** When designing a new persona, look at `_persona-template.md` first. If the new persona doesn't fit the template, the template is wrong (or the persona is two personas).
8. **`.memory/` is for agent state. `docs/` is for project artifacts.** Don't mix.
9. **Persona names use the `/persona_` prefix.** Always. Avoids collision with general skills.

## 10. Things I Don't Want

For the next session, avoid these pitfalls (lessons from prior architectural debates):

- **No `<role>-protocol.md` files** unless the rules are referenced by 3+ files. `design-protocol.md` was correctly dropped because it would have been referenced only twice. Same logic applies to `analysis-protocol.md`, `review-protocol.md`, etc.
- **No 5-tier confidence scales.** Trust tags are `[LAW] / [PATTERN] / [GUESS]`. Nothing more.
- **No bidirectional ID requirements that aren't lint-enforced.** Lint catches what matters.
- **No separate ARCHIVE.md in `.memory/`.** Superseded entries stay in-file under `## Superseded`. (Note: `docs/prds/archive/` is different — it's a folder for completed PRDs, not a memory file.)
- **No automatic forgetting curves.** Old ≠ stale. Explicit supersession only.
- **No persona-switching protocols.** Sessions are scoped to one persona.
- **No `/help` command.** If `STATUS.md` is clear and `persona-protocol.md` is well-written, there's no ambiguity.
- **No "draft → final" PRD folders.** PRD state is tracked in the file and parent GitHub issue, not via folder migration. The only folder move is active → archive when the parent issue closes.

## 11. What's Already Built

- ✅ Memory layer (6 files in `.memory/*`)
- ✅ Core agent layer (workflows, output-mode, memory-protocol)
- ✅ Persona framework (`persona-protocol.md`)
- ✅ Generic persona template (`_persona-template.md`)
- ✅ Designer persona (first concrete instance)
- ✅ PRD → Issue model (`PRD_MODEL.md`)

## 12. What's Next (in order)

1. **Phase 0 — Skill Inventory.** Dedicated session to catalog all existing skills (`docs/skill-inventory.md`). No persona work until this is done.
2. **Revise `write-prd` and `write-issue` skills** to match `PRD_MODEL.md`. (Can happen during Phase 0 or right after.)
3. **Set up `docs/` folder structure** (`docs/research/`, `docs/prds/`, `docs/prds/archive/`).
4. **Update `BACKLOG_MAP.md`** to use the `Ref` column for `docs/prds/` paths in addition to memory IDs. **Update lint regex** in `memory-protocol.md` to handle sub-issue IDs (`\[BT-\d+(-\d+)?\]`).
5. **Build personas, in this order:**
   - **Full-Stack-Dev** — most-used persona, validates the framework against the heaviest case.
   - **Reviewer** — closes the loop after Dev.
   - **PM** — opens the loop. `PRD_MODEL.md` provides most of the structural decisions.
   - **Analyst** — last. Most exploratory, least defined.

For each persona, walk through the **Five Questions** in §8.

## 13. The Handoff Itself

When the next session starts:
1. `/start-session` loads the memory layer.
2. Read this document (`PERSONA_MENTAL_MODEL.md`).
3. If working on PM-related design or PRD/issue skill revision, also read `PRD_MODEL.md`.
4. Decide: skill inventory first (Phase 0), or PRD/issue skill revision, or persona build?
5. Recommended order: Phase 0 → revise PRD/issue skills → first persona (Full-Stack-Dev).
6. For each persona, walk through the Five Questions and copy `_persona-template.md` to `.agents/workflows/persona_<role>.md`.
7. Test the persona on a real task before building the next one.

The system should pass the **resumption test**: can I (or any AI agent) read this document and `STATUS.md` cold, with no other context, and immediately know what to do next? If yes, the handoff is sound.
