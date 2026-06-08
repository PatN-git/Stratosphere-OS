---
name: stratosphere-setup
type: workflow
description: Bootstrap a project with the StratosphereOS constitution, durable memory layer, workspace rules, optional personas, and the right skill packs. Run once per project; safe to re-run.
---

# Instantiate StratosphereOS

Instantiate minimum durable context an AI agent needs to resume work on a repository without re-reading everything. Two paths: **greenfield** (scaffold empty templates) and **brownfield** (audit first, then write findings into templates).

This command is a **one-time setup** (safe to re-run for upgrades). The ongoing protocols live in:
- `.agents/rules/memory-protocol.md` — trust tags, supersession, cross-references, lint
- `.agents/rules/persona-protocol.md` — persona activation, autonomy, handoff (optional)
- `.memory/DESIGN.md` — spec-compliant brand tokens (Google Labs DESIGN.md spec)
- `.memory/DESIGN_RULES.md` — project structural rules: design principles, Stitch harmonization, immortal components

## Why this exists

Cold starts are expensive! A small, durable memory layer eliminates re-derivation cost. The protocol files keep memory dense and trustworthy as the project scales. The persona system lets you navigate complex multi-role work (Analyst, PM, Designer, Dev, Reviewer) without memorizing commands.

## Template source (read before any file creation)

All templates ship **bundled with the plugin** under its `assets/templates/` directory. Locate the installed plugin's `assets/templates/` and read the relevant template file before creating any project file — never reconstruct templates from memory:
- `assets/templates/constitution/` → `AGENT.md`, `CLAUDE.md`, `GEMINI.md`
- `assets/templates/rules/` → `output-mode.md`, `memory-protocol.md`, `persona-protocol.md`
- `assets/templates/memory/` → `STATUS.md`, `BACKLOG_MAP.md`, `LEARNINGS.md`, `GLOSSARY.md`, `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, `DESIGN.md`, `DESIGN_RULES.md`
- `assets/templates/personas/` → `_persona-template.md`, `designer.md`, persona drafts (optional, Step 1b)
- `assets/templates/references/` → PRD and discovery-brief templates

The lifecycle workflows (`0a`–`4b`, `sync-skills`) are **copied into the project's `.agents/workflows/`** by the scaffolder (Step 0). This is required on **Antigravity**, which surfaces *workspace* workflows as `/` commands but does **not** register a plugin's bundled workflows. On **Claude Code** the plugin's commands register globally, so the in-project copies are inert there. Domain skills are not bundled — they are fetched on demand in Step 8.

## Path detection

Before any file operations, decide and state the path in one line:

- **Greenfield** if: no `src/`, no committed code beyond scaffolding, fresh init, or no live database.
- **Brownfield** if: existing source code, dependencies present, or a live database connection is configured.

## Step 0: Scaffold (deterministic — both paths)

Before scaffolding, choose whether you want to stage/install the plugin **globally** (available to any project on your system) or **locally** (isolated to this project only):

- **Global Scope (Recommended):** Stage the plugin under the global configuration directory:
  `~/.gemini/config/plugins/stratosphere-os/`
  Invoke the scaffolder using:
  ```bash
  python ~/.gemini/config/plugins/stratosphere-os/scripts/scaffold.py
  ```
- **Local Scope:** Stage the plugin under your workspace's plugins directory:
  `.agents/plugins/stratosphere-os/`
  Invoke the scaffolder using:
  ```bash
  python .agents/plugins/stratosphere-os/scripts/scaffold.py
  ```

Run the bundled scaffolder from the **project root**. It creates the full folder structure and copies every template verbatim, **create-only-if-missing**, with **zero LLM tokens** (do not hand-create these files — let the script do it):

```bash
# Example showing a global staging run:
python ~/.gemini/config/plugins/stratosphere-os/scripts/scaffold.py

# Add --dry-run to preview what would be created without writing any files:
python ~/.gemini/config/plugins/stratosphere-os/scripts/scaffold.py --dry-run
```

`<plugin>` is the installed plugin root — Claude Code: `~/.claude/plugins/stratosphere-os/` (global) or `.claude/plugins/stratosphere-os/` (local); Antigravity: the global staged plugin directory `~/.gemini/config/plugins/stratosphere-os/` or local `.agents/plugins/stratosphere-os/`.

**What it creates** (skips anything already present):
- Folders: `.memory/`, `.agents/rules/`, `.agents/workflows/` (+ `.reference/`), `docs/discovery/`, `docs/prds/`, `.tmp/`
- Constitution → project root: `AGENT.md`, `CLAUDE.md`, `GEMINI.md`
- Memory: `.memory/{STATUS,BACKLOG_MAP,LEARNINGS,GLOSSARY,ARCHITECTURE,DATABASE_SCHEMA,DESIGN,DESIGN_RULES}.md`
- Rules: `.agents/rules/{output-mode,memory-protocol,persona-protocol}.md`
- Lifecycle workflows (`0a`–`4b`, `sync-skills`) + their `.reference/` templates → `.agents/workflows/`
- `.agents/scripts/validate_memory.py` (memory lint, run by `/0b_stop-session`)
- `.gitignore` (only if missing)

**Drift check (re-runs / brownfield):** the script leaves existing files untouched and lists them under `LEFT AS-IS`. For each, compare against its template and **ask the user before changing** — never overwrite silently. Look for:
- Missing required top-level sections (e.g., `## Active Entries`, `## Superseded`)
- Missing required metadata blocks (Trust Tags reference, Label Registry, Immortal Components)
- Renamed or removed required headers

Report differences as a list and await per-file confirmation. Templates live under the plugin's `assets/templates/{constitution,memory,rules,references,personas}/` if you need to read one for comparison.

## Step 1: Workspace rules in effect (both paths)

Step 0 has placed the rule/protocol files; they govern everything that follows:
- `.agents/rules/output-mode.md`, `memory-protocol.md`, `persona-protocol.md`
- `.memory/DESIGN.md` (brand tokens — external spec, not trust-tagged) and `.memory/DESIGN_RULES.md` (structural rules — `[[DR-xxx]]`)

Confirm they exist. If Step 0 reported any as `LEFT AS-IS`, run the drift check before relying on them.

## Step 1b: Personas (optional)

The persona layer is **opt-in**. Use the native `AskUserQuestion` tool (on Claude Code) or `ask_question` tool (on Google Antigravity) to ask the user (do not ask in plain prose):

> "Scaffold the StratosphereOS persona layer (Analyst, PM, Designer, Dev, Reviewer)?"

- **If no (default):** Re-run the scaffolder passing the `--no-personas` flag:
  ```bash
  python <plugin>/scripts/scaffold.py --no-personas
  ```
- **If yes:** Re-run the scaffolder passing the `--personas` flag:
  ```bash
  python <plugin>/scripts/scaffold.py --personas
  ```
  This copies `designer.md` and `_persona-template.md` into `.agents/workflows/`. Use `_persona-template.md` to author any additional persona.

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
   - `MAP` and `DROP` require explicit per-row user confirmation. Use the native `AskUserQuestion` tool (on Claude Code) or `ask_question` tool (on Google Antigravity) to obtain the user's confirmation — do not ask in prose.

4. **Execute** confirmed changes in GitHub.

5. **Write final resolved label set** into `.memory/BACKLOG_MAP.md ## Label Registry`. This becomes single source of truth — do not revert to template defaults.

> [!IMPORTANT]
> **`area:` labels are project-specific.** Adopt project's existing page/domain slugs rather than forcing template placeholders. All other dimensions (`type:`, `priority:`, `size:`, `status:`) are canonical — always propose renaming GitHub's labels to match, never adopt GitHub's non-standard names.

## Step 7: Session & Backlog Sync (both paths)

1. Update `.memory/STATUS.md` to reflect current version, build state, and immediate next step.
2. If GitHub issues or active tasks exist, populate `.memory/BACKLOG_MAP.md` using `[[BT-xxx]]` IDs and the Label Registry.

## Step 8: Skill setup (interactive)

Domain skills are **not bundled** — they are fetched on demand into `.agents/skills/` from the registry at the plugin's `external-skills.json` via the `sync_skills.py` script.

1. **Select Skill Categories to sync:**
   Use the native `AskUserQuestion` tool with `multiSelect: true` (on Claude Code) or `ask_question` tool (on Google Antigravity) to prompt the user (do not ask in prose). Offer the following options:
   - `system` (installs `code-simplifier`, `skill-creator` - default on)
   - `database` (installs `supabase`, `supabase-postgres-best-practices`)
   - `web` (installs `react-best-practices`, `composition-patterns`, `vercel-web-design`)
   - `mobile` (installs `react-native-skills`)
   - `design` (installs `impeccable`)

2. **Sync the selected skill packs:**
   Invoke the `sync_skills.py` script with the selected categories as arguments. For example:
   ```bash
   python <plugin>/scripts/sync_skills.py --category system database
   ```
   (Where `<plugin>` is `~/.claude/plugins/stratosphere-os/` globally on Claude Code, `~/.gemini/config/plugins/stratosphere-os/` globally on Antigravity, or `.agents/plugins/stratosphere-os/` / `.claude/plugins/stratosphere-os/` locally).

3. **Design note:** Google Stitch is the default design tool (brand tokens live in `.memory/DESIGN.md`); the `design` category skills are optional polish on top.
4. **Re-runnable:** Re-invoke this command/script with updated categories or new files anytime.

## Constraints

- **Re-running this skill is safe.** Files are created only if missing; existing files are checked for structural drift and user is asked before changes.
- **Minimalism:** shortest accurate phrasing. No filler.
- **Live DB wins over code.** Conflicts logged as `[LAW]` entries in `LEARNINGS.md`.
- **Live GitHub labels win over the template registry (area: only).** After Step 6a, the registry in `.memory/BACKLOG_MAP.md` is authoritative. Do not revert to template defaults.
- **Protocols govern ongoing behavior.** This skill instantiates the structure; the rule files in `.agents/rules/` and `.memory/DESIGN_RULES.md` govern all ongoing work. `DESIGN.md` follows an external spec.