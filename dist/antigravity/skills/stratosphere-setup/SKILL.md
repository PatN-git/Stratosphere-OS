---
name: stratosphere-setup
type: workflow
description: Bootstrap a project with the StratosphereOS constitution, durable memory layer, workspace rules, and the right skill packs. Run once per project; safe to re-run.
version: "1.0.4"
timestamp: 2026-06-17
---

# Instantiate StratosphereOS

Instantiate minimum durable context an AI agent needs to resume work on a repository without re-reading everything. Two paths: **greenfield** (scaffold empty templates) and **brownfield** (audit first, then write findings into templates).

This command is a **one-time setup** (safe to re-run for upgrades). The ongoing protocols live in:
- `.agents/rules/memory-protocol.md` — trust tags, supersession, cross-references, lint
- `.memory/DESIGN.md` — spec-compliant brand tokens (Google Labs DESIGN.md spec)
- `.memory/DESIGN_RULES.md` — project structural rules: design principles, design system governance, immortal components

## Why this exists

Cold starts are expensive! A small, durable memory layer eliminates re-derivation cost. The protocol files keep memory dense and trustworthy as the project scales.

## Template source (read before any file creation)

All templates ship **bundled with the plugin** under its `assets/templates/` directory. Locate the installed plugin's `assets/templates/` and read the relevant template file before creating any project file — never reconstruct templates from memory:
- `assets/templates/constitution/` → `AGENT.md`, `CLAUDE.md`, `GEMINI.md`
- `assets/templates/rules/` → `output-mode.md`, `memory-protocol.md`
- `assets/templates/memory/` → `STATUS.md`, `BACKLOG_MAP.md`, `LEARNINGS.md`, `GLOSSARY.md`, `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, `DESIGN.md`, `DESIGN_RULES.md`
- `assets/templates/references/` → PRD and discovery-brief templates

The lifecycle workflows (`0a`–`4b`, `sync-skills`) are **copied into the project's `.agents/workflows/`** by the scaffolder (Checkpoint 0). This is required on **Antigravity**, which surfaces *workspace* workflows as `/` commands but does **not** register a plugin's bundled workflows. On **Claude Code** the plugin's commands register globally, so the in-project copies are inert there. Domain skills are not bundled — they are fetched on demand in Checkpoint 8.

## Version Control Setup & Path Detection

Before any file operations:

1. **Initialize Git (Greenfield only):**
   - **Greenfield** if: no `src/`, no committed code beyond scaffolding, fresh init, or no live database.
     - If **Greenfield** is chosen and no git repository is connected (e.g. no `.git` directory exists in the project root), use the native `AskUserQuestion` tool (on Claude Code) or `ask_question` tool (on Google Antigravity) to prompt the user:
       `No git repository is initialized in this project. Initialize a git repository? [y/N]`
     - If they answer yes, initialize it by running `git init` before continuing.
   - **Brownfield** if: existing source code, dependencies present, or a live database connection is configured.

2. **Verify GitHub CLI & Remote Connection (Optional):**
   - Check if the GitHub CLI (`gh`) is installed and authenticated. Run `gh --version` and `gh auth status` (be sure to clear the `GITHUB_TOKEN` environment variable if running tests to verify the user's persistent credentials).
   - If `gh` is not installed or not authenticated, prompt the user using `AskUserQuestion` (on Claude Code) or `ask_question` (on Google Antigravity):
     `GitHub CLI (gh) is recommended for automating PRs and issue management. It is not set up/authenticated. Would you like to pause to set it up now? [y/N]`
   - If the user selects **Yes**:
     - Provide instructions to install `gh` (e.g., using `winget install GitHub.cli`, `brew install gh`, or from `https://cli.github.com/`) and run `gh auth login` in their terminal. Wait for authentication before proceeding.
   - If the user selects **No**:
     - Document in `.memory/STATUS.md` that GitHub CLI is unavailable. Skip all subsequent automated remote GitHub integrations (such as automated label creation in Checkpoint 6) and fall back to local file-based tracking.
   - **Check GitHub Remote Repository Connection:** If `gh` is installed and authenticated (or if GitHub integration was selected during plugin installation), verify that the local repository is connected to a remote GitHub repository by running `git remote -v` or `gh repo view`.
   - If no GitHub remote repository is connected, prompt the user using `AskUserQuestion` (on Claude Code) or `ask_question` (on Google Antigravity):
     `No remote GitHub repository is connected to this project. A connected GitHub repository is required to automatically populate labels and issues in BACKLOG_MAP.md. Would you like to connect or create a GitHub repository now? [y/N]`
   - If the user selects **Yes**:
     - Provide instructions or assist the user in running `gh repo create` or `git remote add origin <url>` and pushing their initial commit. Wait for connection confirmation before proceeding.
   - If the user selects **No**:
     - Document in `.memory/STATUS.md` that remote GitHub connection is unavailable. Fall back to local file-based label and issue tracking so `BACKLOG_MAP.md` is populated locally without remote sync errors.


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

# Upgrade an existing project: preview, then refresh managed framework files
python <plugin>/scripts/scaffold.py --update --dry-run
python <plugin>/scripts/scaffold.py --update
```

**What it creates** (skips anything already present):
- Folders: `.memory/`, `.agents/rules/`, `.agents/workflows/` (+ `.reference/`), `docs/discovery/`, `docs/prds/`, `.tmp/`
- Constitution → project root: `AGENT.md`, `CLAUDE.md`, `GEMINI.md`
- Memory: `.memory/{STATUS,BACKLOG_MAP,LEARNINGS,GLOSSARY,ARCHITECTURE,DATABASE_SCHEMA,DESIGN,DESIGN_RULES}.md`
- Rules: `.agents/rules/{output-mode,memory-protocol}.md`
- Lifecycle workflows (`0a`–`4b`, `sync-skills`) + their `.reference/` templates → `.agents/workflows/`
- `.agents/scripts/validate_memory.py` (memory lint, run by `/0b_stop-session`)
- `.gitignore` (only if missing)

**Update & Drift check (re-runs / brownfield):** The scaffolder script leaves existing files untouched and lists them under `LEFT AS-IS`. It also drops `.agents/.stratosphere-lock.json` containing the baseline hashes of what was installed.

1. Run `python <plugin>/scripts/scaffold.py --update --dry-run` to compute state.
2. If any `STALE` or `NEEDS-REVIEW` files exist, ask the user with the native tool (`AskUserQuestion` on Claude Code, `ask_question` on Antigravity), e.g.: *"Found N updated framework files (workflows + rules). Refresh them? Your `.memory/` and constitution stay untouched."*
3. On confirmation, re-run with `--update` (no `--dry-run`).
4. Surface any `NEEDS-REVIEW` constitution diffs separately for per-file confirmation; never auto-overwrite the constitution. The `.memory/` and `.gitignore` files remain fully preserved (`LEFT AS-IS`) and require manual review if they drift from templates under `assets/templates/`.

If the lockfile exists, compare the current project state against the bundled `versions.json` from the plugin:
1. Identify **Updates**: Bundled `version` > locked `version`.
2. Identify **Drift**: Current workspace file hash != locked `sha256_at_install` hash.

For any file that requires an update or has drifted:
- **Do NOT just tell the user to manually analyze the differences.**
- **Do NOT overwrite silently or insert raw git conflict markers.**
- Instead, **you (the agent) must prepare a merge plan**: Analyze the new bundled template, analyze the user's current drifted file, and prepare an intelligent merge plan that applies the new template structure/rules while preserving the user's custom project data (e.g., custom trust tags, immortal components, specific logic).
- Present this merge plan to the user for **explicit approval**.
- Once the user approves, execute the merge to update the files.
- **CRITICAL**: After successfully merging an updated or drifted file, you MUST run `python <plugin>/scripts/scaffold.py --repair-lock` to register the new merged state as the baseline. This ensures the drift check won't endlessly trigger on subsequent runs.

## Checkpoint 0.5: Project Vision (both paths)

1. Prompt the user using the native `AskUserQuestion` tool (on Claude Code) or `ask_question` tool (on Google Antigravity) to input the project's core vision statement (e.g. "What is the primary vision or goal of this project?").
2. Write this statement directly into `AGENT.md` under the `## Vision` heading, replacing the placeholder.

## Checkpoint 1: Workspace rules in effect (both paths)

Checkpoint 0 has placed the rule/protocol files; they govern everything that follows:
- `.agents/rules/output-mode.md`, `memory-protocol.md`
- `.memory/DESIGN.md` (brand tokens — external spec, not trust-tagged) and `.memory/DESIGN_RULES.md` (structural rules — `[[DR-xxx]]`)

Confirm they exist. If Checkpoint 0 reported any as `STALE`, `NEEDS-REVIEW`, or `LEFT AS-IS`, ensure you have reviewed the differences before relying on them.

## Checkpoint 2: Database audit

- **Greenfield:** skip. Leave `.memory/DATABASE_SCHEMA.md` as the empty template.
- **Brownfield:** introspect the live schema using the available DB skill or tooling.
  1. Map all tables, primary keys, and foreign relationships.
  2. Identify Row Level Security (RLS) policies and non-nullable constraints.
  3. Write findings into `.memory/DATABASE_SCHEMA.md`. All entries are `[LAW]` — the live DB is ground truth. Do NOT delete the format example line under `## Superseded`.

Why the live DB wins over code: migrations drift, ORMs lie, stale type files mislead. The running database is the only authoritative source.

## Checkpoint 3: Architectural mapping

- **Greenfield:** skip. Leave `.memory/ARCHITECTURE.md` as the empty template.
- **Brownfield:** analyze `src/`, `components/`, `lib/`, `execution/`.
  1. Map data flow (frontend ↔ backend ↔ database).
  2. Identify feature boundaries and immortal UI components.
  3. Assign `[[A-xxx]]` IDs to architectural rules. Only `[LAW]`-tier rules belong here.
  4. Add the one-line pointer to `DESIGN.md` and `DESIGN_RULES.md` in the `## Tech Stack` section: `UI/UX standards: see .memory/DESIGN.md (brand tokens) and .memory/DESIGN_RULES.md (structural rules)`.
  5. **Preserve placeholders:** Do NOT delete empty structural sections (`## Major Feature Areas`, `## State / Data Flow`, `## Backend / Database Boundaries`) or the format example line under `## Superseded` if there are no immediate entries during setup. Keep them as placeholders.

## Checkpoint 4: Design audit

This step has TWO outputs: brand tokens go to `DESIGN.md` (spec format); structural rules go to `DESIGN_RULES.md`.

### Checkpoint 4.1: Brand tokens → `DESIGN.md` (spec-compliant)

- **Greenfield:** skip. Leave `DESIGN.md` as the empty template; fill in as the brand develops.
- **Brownfield:** extract tokens from existing CSS variables, `tailwind.config.js`/`tailwind.config.ts`, and any theme files. If the project has UI but no DESIGN.md, derive an initial DESIGN.md from existing code per `.agents/workflows/.reference/design-brief-guide.md` §B (propose-only).
  1. Map color variables to the `colors:` YAML block (primary, secondary, tertiary, neutral, etc.).
  2. Map typography to the `typography:` YAML block (one entry per type level).
  3. Map spacing scale to the `spacing:` YAML block.
  4. Map corner radii to the `rounded:` YAML block.
  5. Add brief markdown rationale in the `## Overview`, `## Colors`, `## Typography`, `## Layout`, `## Shapes`, and `## Do's and Don'ts` sections. Preserve all HTML comments (`<!-- shadcn... -->`, `<!-- optional dark overrides... -->`), prompt guidance comments (`<Rationale...>`), and empty sections (`## Shapes`, `## Components`, `## Do's and Don'ts`) if unpopulated.
  6. Validate optionally with `npx -p "@google/design.md" designmd lint .memory/DESIGN.md`.

`DESIGN.md` does NOT use trust tags or `[DR-xxx]` IDs — it follows the external spec format.

### Checkpoint 4.2: Structural rules → `DESIGN_RULES.md`

- **Greenfield:** skip. `DESIGN_RULES.md` keeps the empty Immortal Components registry to fill in as components are built.
- **Brownfield:** scan `components/layout/*`, `components/ui/*`, and any `Header.tsx` / `Navbar.tsx` / `Sidebar.tsx` / `Footer.tsx` files.
  1. For each global structural component, add an entry to §3 Immortal Components in `.memory/DESIGN_RULES.md` with a `[[DR-xxx]]` ID and `[LAW]` trust tag.
  2. Note the desktop/mobile pattern observed.
  3. Flag any drift candidates the agent notices (e.g., two Navbar variants in the codebase).
  4. **Preserve governance laws and sections:** The §1 Principles (DR-001 to DR-006) and §2 Design Reference Rules (DR-007 to DR-016) come pre-populated from the template. Do NOT silently rewrite, ignore, or overwrite them.
     - If the existing codebase conflicts with DR-001 through DR-006 (e.g., uses hex colors instead of OKLCH, fixed px instead of fluid typography, or non-shadcn stack), explicitly flag these conflicts to the user and ask for instructions before modifying any laws.
     - Ask the user explicitly about their Design Source (`stitch`, `claude-design`, or `native`) to populate `**Design Source:**`. Do NOT overwrite or delete `## 2. Design Reference Rules`.
     - Preserve the **Applicability:** and **DESIGN.md round-trip:** paragraphs.
     - Do NOT rewrite rules DR-007 through DR-016 without flagging proposed modifications to the user for confirmation.
     - Do NOT delete the format example line under `## Superseded`.

## Checkpoint 5: Constraint extraction

- **Greenfield:** skip. `LEARNINGS.md` accrues entries over time.
- **Brownfield:** identify "Brownfield Traps" surfaced during the audit. Add as initial entries in `.memory/LEARNINGS.md` with [[L-xxx]] IDs.
- Apply trust tags per `memory-protocol.md`. Default to `[ASSUMED]` unless evidence supports a higher tier. Never self-promote to `[LAW]` — propose to user. Do NOT delete the format example line under `## Superseded`.

### Checkpoint 5.1: Vocabulary seeding

- **Greenfield:** skip. Leave `.memory/GLOSSARY.md` as the empty template.
- **Brownfield:** scan `docs/prds/`, `docs/discovery/`, READMEs, and DB enum/type definitions for recurring domain terms.
  1. Propose 5–10 terms with one-line definitions to the user.
  2. User confirms which to keep; write confirmed entries as `[[G-xxx]] [ASSUMED]` with `Source:` pointing to the originating doc.
  3. Assign sequential IDs starting from `[[G-001]]`.
  4. **Preserve guidelines and placeholders:** Do NOT delete the protocol instruction line (`> GLOSSARY follows the same protocol as LEARNINGS.md — not exempt from trust tags.`), the `Avoid:` instructions, or the format example line under `## Superseded`.

### Checkpoint 5.2: Secret hygiene

- Verify `.gitignore` contains `.tmp/`, `.env`, `.env.*`, `token.json`, and common credential files; if missing, **propose** adding them (don't silently edit).

## Checkpoint 6: Label Reconciliation (both paths)

> [!NOTE]
> **GitHub CLI Fallback:** If the GitHub CLI (`gh`) is unavailable or unauthenticated (because the user declined setup in the Version Control Setup step), skip all automated remote GitHub operations (Steps 1-4). Instead, skip directly to Step 5 using the template's canonical labels for the local registry, and inform the user they will need to manage remote labels manually on GitHub.

GitHub labels are ground truth for the `area:` dimension — the same principle as the live database in Checkpoint 2. The canonical taxonomy dimensions (`type:`, `priority:`, `size:`, `status:`) are system-level constants and must always match the registry.

### Greenfield
No GitHub labels exist yet.
1. Create every label in the canonical registry verbatim in GitHub.
2. No user confirmation required — no conflicts possible.
3. Write the confirmed label set into `.memory/BACKLOG_MAP.md ## Label Registry` while preserving all operational bullet points (such as label syncing rules and the `Milestone` definition line).

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

5. **Write final resolved label set** into `.memory/BACKLOG_MAP.md ## Label Registry`. This becomes single source of truth — do not revert to template defaults, but MUST preserve all operational bullet points (such as label syncing rules and the `Milestone` definition line).

> [!IMPORTANT]
> **`area:` labels are project-specific.** Adopt project's existing page/domain slugs rather than forcing template placeholders. All other dimensions (`type:`, `priority:`, `size:`, `status:`) are canonical — always propose renaming GitHub's labels to match, never adopt GitHub's non-standard names.

## Checkpoint 7: Session & Backlog Sync (both paths)

1. Update `.memory/STATUS.md` to reflect current version, build state, and immediate next step.
2. If GitHub issues or active tasks exist, populate `.memory/BACKLOG_MAP.md` using `BT-xxx` IDs and the Label Registry.
3. Backlog seeding and the instantiate command MUST emit BT ids in zero-padded `BT-007` form, inheriting the global BACKLOG_MAP rule.
4. When a step seeds real content into a memory file, delete ONLY that file's dummy active items (e.g., `BT-XXX`, `[[L-XXX]] Example placeholder`, `[[G-XXX]] Example Term`, `[[A-XXX]] Example placeholder`). NEVER delete structural headings, guideline comments, operational bullet points, or format example lines under `## Superseded`.

## Checkpoint 8: Design Context (interactive)

1. **Set Design Context:**
   Use the native `AskUserQuestion` tool (on Claude Code) or `ask_question` tool (on Google Antigravity) to ask: `What is the design source for this project? [stitch / claude-design / native]`. 
   Write the answer into `.memory/DESIGN_RULES.md` §2 `Design Source`. 
   If `native`, optionally ask: `Provide any design reference URLs/templates (optional):` and record them in §2 `Design References (native projects)`.

2. **Gated toolchain install:**
   If Design Source is `stitch`, or if this is a Node/UI project that wants design-spec linting, run npm install in the design scripts directory:
   ```bash
   # Windows (Antigravity/PowerShell)
   cmd /c "npm install --prefix .agents/scripts/design"

   # Unix/macOS (Claude Code)
   npm install --prefix .agents/scripts/design
   ```
   *(Note: If the install fails due to network constraints or offline environment, print a warning, record in STATUS.md that the Google lint seam is not provisioned, and proceed with setup rather than halting).*
   For `claude-design`, `native`, or non-Node/offline projects: skip the npm install and record in `.memory/STATUS.md` that the lint toolchain is not provisioned.

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

5. **Design note:** External design generators are OPTIONAL; native projects bootstrap the design system from human-supplied references (e.g. template sites) + native model composition, with `impeccable` as optional polish. Brand tokens live in `.memory/DESIGN.md`.
6. **Re-runnable:** Re-invoke this command/script with updated categories or new files anytime.

## Constraints

- **Re-running this skill is safe.** Files are created only if missing; existing files are checked for structural drift and user is asked before changes.
- **Minimalism:** shortest accurate phrasing. No filler.
- **Live DB wins over code.** Conflicts logged as `[LAW]` entries in `LEARNINGS.md`.
- **Live GitHub labels win over the template registry (area: only).** After Checkpoint 6, the registry in `.memory/BACKLOG_MAP.md` is authoritative. Do not revert to template defaults.
- **Protocols govern ongoing behavior.** This skill instantiates the structure; the rule files in `.agents/rules/` and `.memory/DESIGN_RULES.md` govern all ongoing work. `DESIGN.md` follows an external spec.