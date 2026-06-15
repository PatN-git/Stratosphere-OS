---
name: stratosphere-setup
type: workflow
description: Bootstrap a project with the StratosphereOS constitution, durable memory layer, workspace rules, and the right skill packs. Run once per project; safe to re-run.
---

# Instantiate StratosphereOS

Instantiate minimum durable context an AI agent needs to resume work on a repository without re-reading everything. Two paths: **greenfield** (scaffold empty templates) and **brownfield** (audit first, then write findings into templates).

This command is a **one-time setup** (safe to re-run for upgrades). The ongoing protocols live in:
- `.agents/rules/memory-protocol.md` — trust tags, supersession, cross-references, lint
- `.memory/DESIGN.md` — spec-compliant brand tokens (Google Labs DESIGN.md spec)
- `.memory/DESIGN_RULES.md` — project structural rules: design principles, Stitch harmonization, immortal components

## Why this exists

Cold starts are expensive! A small, durable memory layer eliminates re-derivation cost. The protocol files keep memory dense and trustworthy as the project scales.

## Template source (read before any file creation)

All templates ship **bundled with the plugin** under its `assets/templates/` directory. Locate the installed plugin's `assets/templates/` and read the relevant template file before creating any project file — never reconstruct templates from memory:
- `assets/templates/constitution/` → `AGENT.md`, `CLAUDE.md`, `GEMINI.md`
- `assets/templates/rules/` → `output-mode.md`, `memory-protocol.md`
- `assets/templates/memory/` → `STATUS.md`, `BACKLOG_MAP.md`, `LEARNINGS.md`, `GLOSSARY.md`, `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, `DESIGN.md`, `DESIGN_RULES.md`
- `assets/templates/references/` → PRD and discovery-brief templates

The lifecycle workflows (`0a`–`4b`, `sync-skills`) are **copied into the project's `.agents/workflows/`** by the scaffolder (Checkpoint 0). This is required on **Antigravity**, which surfaces *workspace* workflows as `/` commands but does **not** register a plugin's bundled workflows. On **Claude Code** the plugin's commands register globally, so the in-project copies are inert there. Domain skills are not bundled — they are fetched on demand in Checkpoint 8.

## Path detection

Before any file operations, decide and state the path in one line:

- **Greenfield** if: no `src/`, no committed code beyond scaffolding, fresh init, or no live database.
  - If **Greenfield** is chosen and no git repository is connected (e.g. no `.git` directory exists in the project root), use the native `AskUserQuestion` tool (on Claude Code) or `ask_question` tool (on Google Antigravity) to prompt the user:
    `No git repository is initialized in this project. Initialize a git repository? [y/N]`
  - If they answer yes, initialize it by running `git init` before continuing.
- **Brownfield** if: existing source code, dependencies present, or a live database connection is configured.

## Checkpoint 0: Scaffold (deterministic — both paths)

The plugin is **already installed** (from the install step) — do not re-stage or re-choose a scope here. Instead, **locate the installed plugin root** (`<plugin>`), then run its bundled scaffolder from the **project root** (cwd = your project). `scaffold.py` resolves its templates relative to its own location, so any valid install path works.

Find `<plugin>` by checking these locations in order and using the first that contains `scripts/scaffold.py`:

- **Claude Code:**
  - Marketplace install: `~/.claude/plugins/cache/*/stratosphere-os/*/` (glob — pick the newest version directory)
  - Manual/global: `~/.claude/plugins/stratosphere-os/`
  - Manual/local: `./.claude/plugins/stratosphere-os/`
- **Antigravity:**
  - Global: `~/.gemini/config/plugins/stratosphere-os/`
  - Local: `./.agents/plugins/stratosphere-os/`

If none match (e.g. a custom path), search for `stratosphere-os/scripts/scaffold.py` under the plugin roots above. Then run it from the project root — it creates the full folder structure and copies every template verbatim, **create-only-if-missing**, with **zero LLM tokens** (do not hand-create these files — let the script do it):

```bash
# <plugin> = the path you found above
python <plugin>/scripts/scaffold.py

# Add --dry-run to preview what would be created without writing any files:
python <plugin>/scripts/scaffold.py --dry-run
```

**What it creates** (skips anything already present):
- Folders: `.memory/`, `.agents/rules/`, `.agents/workflows/` (+ `.reference/`), `docs/discovery/`, `docs/prds/`, `.tmp/`
- Constitution → project root: `AGENT.md`, `CLAUDE.md`, `GEMINI.md`
- Memory: `.memory/{STATUS,BACKLOG_MAP,LEARNINGS,GLOSSARY,ARCHITECTURE,DATABASE_SCHEMA,DESIGN,DESIGN_RULES}.md`
- Rules: `.agents/rules/{output-mode,memory-protocol}.md`
- Lifecycle workflows (`0a`–`4b`, `sync-skills`) + their `.reference/` templates → `.agents/workflows/`
- `.agents/scripts/validate_memory.py` (memory lint, run by `/0b_stop-session`)
- `.gitignore` (only if missing)

**Drift check (re-runs / brownfield):** the script leaves existing files untouched and lists them under `LEFT AS-IS`. For each, compare against its template and **ask the user before changing** — never overwrite silently. Look for:
- Missing required top-level sections (e.g., `## Active Entries`, `## Superseded`)
- Missing required metadata blocks (Trust Tags reference, Label Registry, Immortal Components)
- Renamed or removed required headers

Report differences as a list and await per-file confirmation. Templates live under the plugin's `assets/templates/{constitution,memory,rules,references}/` if you need to read one for comparison.

## Checkpoint 1: Workspace rules in effect (both paths)

Checkpoint 0 has placed the rule/protocol files; they govern everything that follows:
- `.agents/rules/output-mode.md`, `memory-protocol.md`
- `.memory/DESIGN.md` (brand tokens — external spec, not trust-tagged) and `.memory/DESIGN_RULES.md` (structural rules — `[[DR-xxx]]`)

Confirm they exist. If Checkpoint 0 reported any as `LEFT AS-IS`, run the drift check before relying on them.

## Checkpoint 2: Database audit

- **Greenfield:** skip. Leave `.memory/DATABASE_SCHEMA.md` as the empty template.
- **Brownfield:** introspect the live schema using the available DB skill or tooling.
  1. Map all tables, primary keys, and foreign relationships.
  2. Identify Row Level Security (RLS) policies and non-nullable constraints.
  3. Write findings into `.memory/DATABASE_SCHEMA.md`. All entries are `[LAW]` — the live DB is ground truth.

Why the live DB wins over code: migrations drift, ORMs lie, stale type files mislead. The running database is the only authoritative source.

## Checkpoint 3: Architectural mapping

- **Greenfield:** skip. Leave `.memory/ARCHITECTURE.md` as the empty template.
- **Brownfield:** analyze `src/`, `components/`, `lib/`, `execution/`.
  1. Map data flow (frontend ↔ backend ↔ database).
  2. Identify feature boundaries and immortal UI components.
  3. Assign `[[A-xxx]]` IDs to architectural rules. Only `[LAW]`-tier rules belong here.
  4. Add the one-line pointer to `DESIGN.md` and `DESIGN_RULES.md` in the `## Tech Stack` section: `UI/UX standards: see .memory/DESIGN.md (brand tokens) and .memory/DESIGN_RULES.md (structural rules)`.

## Checkpoint 4: Design audit

This step has TWO outputs: brand tokens go to `DESIGN.md` (spec format); structural rules go to `DESIGN_RULES.md`.

### Checkpoint 4.1: Brand tokens → `DESIGN.md` (spec-compliant)

- **Greenfield:** skip. Leave `DESIGN.md` as the empty template; fill in as the brand develops.
- **Brownfield:** extract tokens from existing CSS variables, `tailwind.config.js`/`tailwind.config.ts`, and any theme files. If the project has UI but no DESIGN.md, derive an initial DESIGN.md from existing code per `.agents/workflows/.reference/stitch-brief-guide.md` §B (propose-only).
  1. Map color variables to the `colors:` YAML block (primary, secondary, tertiary, neutral, etc.).
  2. Map typography to the `typography:` YAML block (one entry per type level).
  3. Map spacing scale to the `spacing:` YAML block.
  4. Map corner radii to the `rounded:` YAML block.
  5. Add brief markdown rationale in the `## Overview`, `## Colors`, `## Typography`, `## Layout`, `## Shapes`, and `## Do's and Don'ts` sections.
  6. Validate optionally with `npx @google/design.md lint .memory/DESIGN.md` (Windows: `npx @google/designmd lint`).

`DESIGN.md` does NOT use trust tags or `[DR-xxx]` IDs — it follows the external spec format.

### Checkpoint 4.2: Structural rules → `DESIGN_RULES.md`

- **Greenfield:** skip. `DESIGN_RULES.md` keeps the empty Immortal Components registry to fill in as components are built.
- **Brownfield:** scan `components/layout/*`, `components/ui/*`, and any `Header.tsx` / `Navbar.tsx` / `Sidebar.tsx` / `Footer.tsx` files.
  1. For each global structural component, add an entry to §3 Immortal Components in `.memory/DESIGN_RULES.md` with a `[[DR-xxx]]` ID and `[LAW]` trust tag.
  2. Note the desktop/mobile pattern observed.
  3. Flag any drift candidates the agent notices (e.g., two Navbar variants in the codebase).
  4. The §1 Principles and §2 Stitch Harmonization sections come pre-populated from the template — review and adjust to match the project.

## Checkpoint 5: Constraint extraction

- **Greenfield:** skip. `LEARNINGS.md` accrues entries over time.
- **Brownfield:** identify "Brownfield Traps" surfaced during the audit. Add as initial entries in `.memory/LEARNINGS.md` with [[L-xxx]] IDs.
- Apply trust tags per `memory-protocol.md`. Default to `[ASSUMED]` unless evidence supports a higher tier. Never self-promote to `[LAW]` — propose to user.

### Checkpoint 5.1: Vocabulary seeding

- **Greenfield:** skip. Leave `.memory/GLOSSARY.md` as the empty template.
- **Brownfield:** scan `docs/prds/`, `docs/discovery/`, READMEs, and DB enum/type definitions for recurring domain terms.
  1. Propose 5–10 terms with one-line definitions to the user.
  2. User confirms which to keep; write confirmed entries as `[[G-xxx]] [ASSUMED]` with `Source:` pointing to the originating doc.
  3. Assign sequential IDs starting from `[[G-001]]`.

### Checkpoint 5.2: Secret hygiene

- Verify `.gitignore` contains `.tmp/`, `.env`, `.env.*`, `token.json`, and common credential files; if missing, **propose** adding them (don't silently edit).

## Checkpoint 6: Label Reconciliation (both paths)

GitHub labels are ground truth for the `area:` dimension — the same principle as the live database in Checkpoint 2. The canonical taxonomy dimensions (`type:`, `priority:`, `size:`, `status:`) are system-level constants and must always match the registry.

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
   | `frontend` | `area:FE-<page_name>` (Note: this is a PATTERN, use literal slug e.g. `area:FE-login`) | MAP |
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

## Checkpoint 7: Session & Backlog Sync (both paths)

1. Update `.memory/STATUS.md` to reflect current version, build state, and immediate next step.
2. If GitHub issues or active tasks exist, populate `.memory/BACKLOG_MAP.md` using `BT-xxx` IDs and the Label Registry.
3. Backlog seeding and the instantiate command MUST emit BT ids in zero-padded `BT-007` form, inheriting the global BACKLOG_MAP rule.
4. When a step seeds real content into a memory file, delete that file's shipped example rows; leave examples in files with nothing real to seed yet.

## Checkpoint 8: Design Context (interactive)

1. **Set Design Context:**
   Use the native `AskUserQuestion` tool (on Claude Code) or `ask_question` tool (on Google Antigravity) to ask: `Does this project use Google Stitch for UI design? [yes/no]`. 
   Write the answer into `.memory/DESIGN_RULES.md` §2 `Stitch Status`. 
   If `no`, optionally ask: `Provide any design reference URLs/templates (optional):` and record them in §2 `Design References`.

## Checkpoint 9: Skill setup (interactive)

Domain skills are **not bundled** — they are fetched on demand into `.agents/skills/` from the registry at the plugin's `external-skills.json` via the `sync_skills.py` script.

1. **Always sync `system` pack** without asking — it contains `skill-creator` and `code-simplifier` which every project needs. Do not present it as a choice.
2. **Ask one question using `AskUserQuestion` (multiSelect: true) on Claude Code, or `ask_question` (is_multi_select: true) on Antigravity:**
   > "The \`system\` pack (\`skill-creator\`, \`code-simplifier\`) is always installed. Which additional skill packs do you need?"
   - `database` — Supabase + Postgres best practices
   - `web` — React, composition patterns, Vercel web design
   - `mobile` — React Native skills
   - `design` — Impeccable (design polish + brand tokens)

3. **Determine skill scope — derive it from how StratosphereOS itself is installed; only ask when ambiguous:**
   You already located the plugin root `<plugin>` in Checkpoint 0. Use it:
   - If `<plugin>` is a **project-local** path (`./.claude/plugins/…` or `./.agents/plugins/…`), install skills **locally** too — do **not** ask. A project-scoped install implies project-scoped skills (and on Antigravity, global skills have no coherent home without a global plugin).
   - If `<plugin>` is **global** (`~/.claude/…`, `~/.gemini/config/plugins/…`, or the Claude Code marketplace cache `~/.claude/plugins/cache/…`), the choice is genuine — use the native `AskUserQuestion` (Claude Code) / `ask_question` (Antigravity) tool to ask (do not ask in prose):
     `Install third-party skills globally (system-wide) or locally (just for this project)? [global/local]`

4. **Sync the selected skill packs:**
   Combine `system` + selected answers and pass all to `sync_skills.py` with the selected categories as arguments, adding the `--global` flag if global installation was chosen. For example:
   ```bash
   # Local install
   python <plugin>/scripts/sync_skills.py --category system database
   
   # Global install
   python <plugin>/scripts/sync_skills.py --category system database --global
   ```
   (Where `<plugin>` is the installed plugin root located in Checkpoint 0 — including the Claude Code marketplace cache `~/.claude/plugins/cache/*/stratosphere-os/*/`.)

5. **Design note:** Google Stitch is OPTIONAL; no-Stitch projects bootstrap the design system from human-supplied references (e.g. template sites) + native model composition, with `impeccable` as optional polish. Brand tokens live in `.memory/DESIGN.md`.
6. **Re-runnable:** Re-invoke this command/script with updated categories or new files anytime.

## Constraints

- **Re-running this skill is safe.** Files are created only if missing; existing files are checked for structural drift and user is asked before changes.
- **Minimalism:** shortest accurate phrasing. No filler.
- **Live DB wins over code.** Conflicts logged as `[LAW]` entries in `LEARNINGS.md`.
- **Live GitHub labels win over the template registry (area: only).** After Checkpoint 6, the registry in `.memory/BACKLOG_MAP.md` is authoritative. Do not revert to template defaults.
- **Protocols govern ongoing behavior.** This skill instantiates the structure; the rule files in `.agents/rules/` and `.memory/DESIGN_RULES.md` govern all ongoing work. `DESIGN.md` follows an external spec.