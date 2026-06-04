---
name: instantiate-stratosphere
description: Bootstrap a project with the StratosphereOS constitution, durable memory layer, workspace rules, optional personas, and the right skill packs. Run once per project; safe to re-run.
---

# Instantiate StratosphereOS

Instantiate the minimum durable context an AI agent needs to resume work on a repository without re-reading everything. Two paths: **greenfield** (scaffold empty templates) and **brownfield** (audit first, then write findings into templates).

This command is a **one-time setup** (safe to re-run for upgrades). The ongoing protocols live in:
- `.agents/rules/memory-protocol.md` — trust tags, supersession, cross-references, lint
- `.agents/rules/persona-protocol.md` — persona activation, autonomy, handoff
- `.memory/DESIGN.md` — spec-compliant brand tokens (Google Labs DESIGN.md spec)
- `.memory/DESIGN_RULES.md` — project structural rules: design principles, Stitch harmonization, immortal components

## Why this exists

Cold starts are expensive. A small, durable memory layer eliminates re-derivation cost. The protocol files keep memory dense and trustworthy as the project scales. The persona system lets you navigate complex multi-role work (Analyst, PM, Designer, Dev, Reviewer) without memorizing commands.

## Template source (read before any file creation)

All templates ship **bundled with the plugin** under its `assets/templates/` directory. Locate the installed plugin's `assets/templates/` and read the relevant template file before creating any project file — never reconstruct templates from memory:
- `assets/templates/constitution/` → `AGENT.md`, `CLAUDE.md`, `GEMINI.md`
- `assets/templates/instantiate-references/` → `templates-memory-core.md`, `templates-agents-rules.md`, `templates-agents-design.md`, `templates-agents-personas.md`
- `assets/templates/personas/` → persona drafts (optional, Step 1b)
- `assets/templates/references/` → PRD and discovery-brief templates

The lifecycle workflows (`0a`–`4b`) and skills are **provided by the plugin itself** and invoked as slash commands; this installer does not copy them into the project.

## Path detection

Before any file operations, decide and state the path in one line:

- **Greenfield** if: no `src/`, no committed code beyond scaffolding, fresh init, or no live database.
- **Brownfield** if: existing source code, dependencies present, or a live database connection is configured.

## Step 0: Preparation (both paths)

Create files **only if missing**. DO NOT overwrite. If a file already exists, check for **structural differences** against the template and explicitly ask the user if changes should be implemented before proceeding. Re-running this skill must be safe.

**Structural differences to check for:**
- Missing required top-level sections (e.g., `## Active Entries`, `## Superseded`, `## Commands`)
- Missing required metadata blocks (e.g., Trust Tags reference, Label Registry, Immortal Components)
- Renamed or removed required headers

Report differences as a list and await user confirmation per file.

**Folders to create if missing:**
- `.memory/`
- `.agents/rules/`

**Files to create if missing:**

| File | Template Source |
|:---|:---|
| `AGENT.md` (project root) | `constitution/AGENT.md` |
| `CLAUDE.md` (project root) | `constitution/CLAUDE.md` |
| `GEMINI.md` (project root) | `constitution/GEMINI.md` |
| `.memory/STATUS.md` | `instantiate-references/templates-memory-core.md` |
| `.memory/BACKLOG_MAP.md` | `instantiate-references/templates-memory-core.md` |
| `.memory/LEARNINGS.md` | `instantiate-references/templates-memory-core.md` |
| `.memory/GLOSSARY.md` | `instantiate-references/templates-memory-core.md` |
| `.memory/ARCHITECTURE.md` | `instantiate-references/templates-memory-core.md` |
| `.memory/DATABASE_SCHEMA.md` | `instantiate-references/templates-memory-core.md` |
| `.memory/DESIGN.md` | `instantiate-references/templates-agents-design.md` |
| `.memory/DESIGN_RULES.md` | `instantiate-references/templates-agents-design.md` |
| `.agents/rules/output-mode.md` | `instantiate-references/templates-agents-rules.md` |
| `.agents/rules/memory-protocol.md` | `instantiate-references/templates-agents-rules.md` |
| `.agents/rules/persona-protocol.md` | `instantiate-references/templates-agents-personas.md` |

The **constitution files** (`AGENT.md`/`CLAUDE.md`/`GEMINI.md`) are copied verbatim from the bundled templates — they are how both Claude Code and Antigravity read the StratosphereOS rules in this project. Persona scaffolding is **optional** and handled separately in Step 1b.

> [!IMPORTANT]
> Read the template files before creation — do not reconstruct from memory.

## Step 1: Establish workspace rules (both paths)

Create the four rule/protocol files first. They govern everything that follows:
- `.agents/rules/output-mode.md`
- `.agents/rules/memory-protocol.md`
- `.agents/rules/persona-protocol.md`
- `.memory/DESIGN.md` (spec-compliant brand tokens — external spec, not trust-tagged)
- `.memory/DESIGN_RULES.md` (project structural rules — trust-tagged with `[[DR-xxx]]` IDs)

## Step 1b: Personas (optional)

The persona layer is **opt-in**. Ask the user once:

> "Scaffold the StratosphereOS persona layer (Analyst, PM, Designer, Dev, Reviewer)? [y/N]"

- **If no (default):** skip entirely. Do not create `persona-protocol.md` persona files or `.agents/workflows/designer.md`. The system works without personas.
- **If yes:** create `.agents/workflows/` if missing, then scaffold the persona files from `assets/templates/personas/` and `assets/templates/instantiate-references/templates-agents-personas.md` (including `.agents/workflows/designer.md`). Read the templates before writing; create only if missing.

## Step 2: Database audit

- **Greenfield:** skip. Leave `.memory/DATABASE_SCHEMA.md` as the empty template.
- **Brownfield:** introspect the live schema using the available DB skill or tooling.
  1. Map all tables, primary keys, and foreign relationships.
  2. Identify Row Level Security (RLS) policies and non-nullable constraints.
  3. Write findings into `.memory/DATABASE_SCHEMA.md`. All entries are `[LAW]` — the live DB is ground truth.

Why the live DB wins over code: migrations drift, ORMs lie, stale type files mislead. The running database is the only authoritative source.

## Step 3: Architectural mapping

- **Greenfield:** skip. Leave `.memory/ARCHITECTURE.md` as the empty template.
- **Brownfield:** analyze `src/`, `components/`, `lib/`, `execution/`.
  1. Map data flow (frontend ↔ backend ↔ database).
  2. Identify feature boundaries and immortal UI components.
  3. Assign `[[A-xxx]]` IDs to architectural rules. Only `[LAW]`-tier rules belong here.
  4. Add the one-line pointer to `DESIGN.md` and `DESIGN_RULES.md` in the `## Tech Stack` section: `UI/UX standards: see .memory/DESIGN.md (brand tokens) and .memory/DESIGN_RULES.md (structural rules)`.

## Step 4: Design audit

This step has TWO outputs: brand tokens go to `DESIGN.md` (spec format); structural rules go to `DESIGN_RULES.md`.

### Step 4a: Brand tokens → `DESIGN.md` (spec-compliant)

- **Greenfield:** skip. Leave `DESIGN.md` as the empty template; fill in as the brand develops.
- **Brownfield:** extract tokens from existing CSS variables, `tailwind.config.js`/`tailwind.config.ts`, and any theme files.
  1. Map color variables to the `colors:` YAML block (primary, secondary, tertiary, neutral, etc.).
  2. Map typography to the `typography:` YAML block (one entry per type level).
  3. Map spacing scale to the `spacing:` YAML block.
  4. Map corner radii to the `rounded:` YAML block.
  5. Add brief markdown rationale in the `## Overview`, `## Colors`, `## Typography`, `## Layout`, `## Shapes`, and `## Do's and Don'ts` sections.
  6. Validate optionally with `npx @google/design.md lint .memory/DESIGN.md` (Windows: `npx @google/designmd lint`).

`DESIGN.md` does NOT use trust tags or `[DR-xxx]` IDs — it follows the external spec format.

### Step 4b: Structural rules → `DESIGN_RULES.md`

- **Greenfield:** skip. `DESIGN_RULES.md` keeps the empty Immortal Components registry to fill in as components are built.
- **Brownfield:** scan `components/layout/*`, `components/ui/*`, and any `Header.tsx` / `Navbar.tsx` / `Sidebar.tsx` / `Footer.tsx` files.
  1. For each global structural component, add an entry to §3 Immortal Components in `.memory/DESIGN_RULES.md` with a `[[DR-xxx]]` ID and `[LAW]` trust tag.
  2. Note the desktop/mobile pattern observed.
  3. Flag any drift candidates the agent notices (e.g., two Navbar variants in the codebase).
  4. The §1 Principles and §2 Stitch Harmonization sections come pre-populated from the template — review and adjust to match the project.

## Step 5: Constraint extraction

- **Greenfield:** skip. `LEARNINGS.md` accrues entries over time.
- **Brownfield:** identify "Brownfield Traps" surfaced during the audit. Add as initial entries in `.memory/LEARNINGS.md` with [[L-xxx]] IDs.
- Apply trust tags per `memory-protocol.md`. Default to `[GUESS]` unless evidence supports a higher tier. Never self-promote to `[LAW]` — propose to user.

### Step 5a: Vocabulary seeding

- **Greenfield:** skip. Leave `.memory/GLOSSARY.md` as the empty template.
- **Brownfield:** scan `docs/prds/`, `docs/discovery/`, READMEs, and DB enum/type definitions for recurring domain terms.
  1. Propose 5–10 terms with one-line definitions to the user.
  2. User confirms which to keep; write confirmed entries as `[[G-xxx]] [GUESS]` with `Source:` pointing to the originating doc.
  3. Assign sequential IDs starting from `[[G-001]]`.

### Step 5b: Secret hygiene

- Verify `.gitignore` contains `.tmp/`, `.env`, `.env.*`, `token.json`, and common credential files; if missing, **propose** adding them (don't silently edit).

## Step 6: Label Reconciliation (both paths)

GitHub labels are ground truth for the `area:` dimension — the same principle as the live database in Step 2. The canonical taxonomy dimensions (`type:`, `priority:`, `size:`, `status:`) are system-level constants and must always match the registry.

### Greenfield
No GitHub labels exist yet.
1. Create every label in the canonical registry verbatim in GitHub.
2. No user confirmation required — no conflicts possible.
3. Write the confirmed label set into `.memory/BACKLOG_MAP.md ## Label Registry`.

### Brownfield
GitHub labels already exist and may differ from the registry.

1. **Fetch** all existing GitHub labels (names + colours).
2. **Build a reconciliation table** — one row per label, assign exactly one Action:

   | GitHub Label (existing) | Registry Equivalent | Action |
   |:---|:---|:---|
   | `bug` | `type:bug` | MAP |
   | `frontend` | `area:FE-<page_name>` | MAP |
   | `wontfix` | _(none)_ | DROP |
   | _(missing)_ | `priority:high` | ADD |
   | `type:feature` | `type:feature` | KEEP |

   **Action definitions:**
   - **KEEP** — exact match; no change needed.
   - **MAP** — different name, same intent. Rename GitHub label to canonical registry name.
   - **DROP** — exists in GitHub, no registry equivalent. Retire after migrating any issues that use it.
   - **ADD** — in registry but not yet in GitHub. Create it.

3. **Present full table** to the user.
   - `KEEP` and `ADD` are auto-approved.
   - `MAP` and `DROP` require explicit per-row user confirmation before executing.

4. **Execute** confirmed changes in GitHub.

5. **Write final resolved label set** into `.memory/BACKLOG_MAP.md ## Label Registry`. This becomes single source of truth — do not revert to template defaults.

> [!IMPORTANT]
> **`area:` labels are project-specific.** Adopt project's existing page/domain slugs rather than forcing template placeholders. All other dimensions (`type:`, `priority:`, `size:`, `status:`) are canonical — always propose renaming GitHub's labels to match, never adopt GitHub's non-standard names.

## Step 7: Session & Backlog Sync (both paths)

1. Update `.memory/STATUS.md` to reflect current version, build state, and immediate next step.
2. If GitHub issues or active tasks exist, populate `.memory/BACKLOG_MAP.md` using `[[BT-xxx]]` IDs and the Label Registry. **Run Step 6a first** to ensure the registry reflects live GitHub labels.

## Step 8: Skill setup (interactive)

Domain skills are **not bundled** — they are fetched on demand into `.agents/skills/` from the registry at the plugin's `external-skills.json` via the `sync-skills` script. Select only what this project needs.

1. **System skills (default on):** offer `code-simplifier` and `skill-creator` (registry entries with `"default": true`). Confirm, then fetch.
2. **Ask targeted questions**, mapping each "yes" to its registry `category`:
   - "Does this project use a database?" → `category: database` (`supabase`, `supabase-postgres-best-practices`)
   - "React or web frontend?" → `category: web` (`react-best-practices`, `composition-patterns`, `vercel-web-design`)
   - "React Native / mobile?" → `category: mobile` (`react-native-skills`)
   - "Do you want design-polish tooling?" → `category: design` (`impeccable`, `ui-ux-pro-max`)
3. **Fetch the selected packs** by running the bundled `sync-skills` script with `--pull`, sourcing entries from `external-skills.json`. Skip any entry whose `repoZipUrl` is `TODO` and report it.
4. Re-runnable: re-invoke this command anytime to add packs later.

## Constraints

- **Re-running this skill is safe.** Files are created only if missing; existing files are checked for structural drift and user is asked before changes.
- **Minimalism:** shortest accurate phrasing. No filler.
- **Live DB wins over code.** Conflicts logged as `[LAW]` entries in `LEARNINGS.md`.
- **Live GitHub labels win over the template registry (area: only).** After Step 6a, the registry in `.memory/BACKLOG_MAP.md` is authoritative. Do not revert to template defaults.
- **Protocols govern ongoing behavior.** This skill instantiates the structure; the rule files in `.agents/rules/` and `.memory/DESIGN_RULES.md` govern all ongoing work. `DESIGN.md` follows an external spec.