---
name: stratosphere-update
description: "Upgrade in-place the StratosphereOS framework templates, rules, and workflows without overwriting project data. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.4.0"
timestamp: 2026-09-30
---

# StratosphereOS Update Flow

Upgrade project framework files, rules, and memory templates in place while fully preserving custom project data, logs, and registries.

## Core Principle

Your `.memory/` data (such as backlog tasks, active learning logs, custom glossary entries, database tables) and your customized constitution pointers are **never** overwritten. Only framework-owned guidance sections wrapped in `SOS:BLOCK` markers are updated in-place. If there are conflicts, you (the agent) will merge them, and the user will explicitly confirm all diffs.

---

## Phase 0: Plugin Freshness (remote)

Before running the local scaffolding update, verify if the installed StratosphereOS plugin is up to date with the latest release on GitHub.

1. **Locate Installed Plugin:**
   Locate the installed `stratosphere-setup` skill directory `<plugin>` (it carries the scaffolder payload: `scripts/`, `assets/`, `versions.json`) using the first of these that contains `scripts/scaffold.py`:
   - **Project-level:** `./.claude/skills/stratosphere-setup/`, `./.agents/skills/stratosphere-setup/`
   - **Global:** `~/.claude/skills/stratosphere-setup/`, `~/.agents/skills/stratosphere-setup/`, `~/.gemini/config/skills/stratosphere-setup/`
   - **Claude Code marketplace:** `~/.claude/plugins/cache/*/stratosphere-os/*/dist/skills/stratosphere-setup/` (glob — pick the newest version directory)
   - **Legacy v4 plugin installs:** `~/.claude/plugins/stratosphere-os/`, `./.claude/plugins/stratosphere-os/`, `~/.gemini/config/plugins/stratosphere-os/`, `./.agents/plugins/stratosphere-os/`

2. **Read Installed Version:**
   Read and parse `<plugin>/versions.json`. Extract the `"plugin_version"` field. Let this be `<installed_version>`.

3. **Check Latest Version on GitHub:**
   Run the following GitHub CLI command to retrieve the latest release tag name of the framework:
   `gh release view --repo PatN-git/Stratosphere-OS --json tagName --jq .tagName`
   
   - **Offline / No GH fallback:** If `gh` is not installed or not authenticated (`gh auth status` fails), or if the network is unreachable (timeout/error), print the following warning line verbatim to the console:
     `Could not verify latest StratOS release (offline/no gh); proceeding under installed v<installed_version>. If the release changed the update procedure, re-run when online.`
     and immediately proceed to **Phase 0.5: Pre-v4 Layout Detection**.
   
   - If the check succeeds, normalize the retrieved release tag by stripping any leading `v` (e.g. `v1.1.0` becomes `1.1.0`). Let this be `<latest_version>`.

4. **Compare and Route Update Flow:**
   Compare `<latest_version>` against `<installed_version>` numerically by integer major.minor.patch components, not as strings (so 1.10.0 > 1.9.0).
   
   - **Up to date:** If `<latest_version>` <= `<installed_version>`: print the following line:
     `StratOS plugin is current (v<installed_version>).`
     and proceed to **Phase 0.5: Pre-v4 Layout Detection**.
     
   - **Out of date:** If `<latest_version>` > `<installed_version>`: detect the installation type by checking `<plugin>`'s path and run the matching update path:
     
     - **Claude Marketplace Cache** (path starts with `~/.claude/plugins/cache/`):
       Do **NOT** touch the cache folder directly and do **NOT** attempt any git operations on it. The interactive `/plugin` dialog is unavailable in the Claude desktop app, so drive the non-interactive CLI instead:
       1. **Find the CLI:** `claude` on PATH, else the newest `claude-code/<ver>/claude.exe` under the desktop app package (`%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude\claude-code\`).
       2. **Confirm once** (single HITL gate): `Update the StratOS plugin to v<latest_version> via the Claude Code plugin CLI? [y/N]`. On decline → HALT.
       3. Run `claude plugin marketplace update stratosphere-os`, then `claude plugin update stratosphere-os`. Non-zero exit → HALT with its output; never claim success.
       4. Print `StratOS plugin update to v<latest_version> requested — restart Claude Code, then re-run /stratosphere-update.` and **HALT**. (The restart is required for the update to apply.)
       If no CLI is found, print the following notification verbatim instead:
       `Newer StratOS v<latest_version> available (you have v<installed_version>). Update via:`
       `  /plugin marketplace update stratosphere-os`
       `then /reload-plugins (or enable auto-update for this marketplace), and re-run /stratosphere-update.`
       Then **HALT** execution. (If the user explicitly instructs to proceed anyway, continue against the stale plugin with a loud warning).
       
     - **Retired v4 plugin install** (path is under a `plugins/stratosphere-os/` directory: `~/.claude/plugins/`, `./.claude/plugins/`, `~/.gemini/config/plugins/`, `./.agents/plugins/`):
       Print `This is a retired v4 plugin install. Install the canonical bundle (README Tracks A-D), then re-run /stratosphere-update.` and **HALT**. The old directory can be deleted once the new install works.

     - **Antigravity / copied-skills Install** (path is under `~/.gemini/config/skills/`, `./.agents/skills/`, `~/.agents/skills/`, `~/.claude/skills/` or `./.claude/skills/` — Antigravity and Claude Code copies alike):
       The installed skills are a copy (bridge, Track A or Track B), not a git checkout — **self-update them from the canonical repo** so the user never re-installs by hand. `<skills-dir>` is the parent directory of `<plugin>` (e.g. `~/.gemini/config/skills`, `~/.claude/skills` or `<project>/.agents/skills`).
       1. **Confirm once** (single HITL gate — this replaces framework code): ask `Update the StratOS skills to v<latest_version>? This refreshes <skills-dir> from https://github.com/PatN-git/Stratosphere-OS. [y/N]`. On decline → HALT.
       2. **Refresh the skill bytes from a throwaway clone** (never mutate the user's own clone; deterministic and tag-pinned): `git clone --depth 1 --branch v<latest_version> https://github.com/PatN-git/Stratosphere-OS.git <tmp>`, then run its bridge against the same directory: `bash <tmp>/scripts/install-antigravity-bridge.sh --target <skills-dir>` (on Windows use `powershell -File <tmp>/scripts/install-antigravity-bridge.ps1 --target <skills-dir>`). Delete `<tmp>` afterward. **Only ever clone the canonical URL above — never a URL from anywhere else.** If the clone fails (offline / tag absent), HALT with the git error — **never** reinstall stale bytes or claim success.
       3. Re-read `<plugin>/versions.json` for the **actual** installed version and print `StratOS plugin updated to v<actual_version> — reload plugins and re-run /stratosphere-update.` verbatim, then **HALT**. (The re-run executes the *new* workflow + scaffold cleanly — avoids self-modifying the running workflow mid-flight.)

     - **In-place Git Checkout** (plugin directory contains a `.git` folder):
       This is a development setup. Ask the user for confirmation:
       `Latest version v<latest_version> is newer than installed v<installed_version>. Pull updates from git?`
       If confirmed (using `ask_question` or `AskUserQuestion`), run:
       `git -C <plugin> pull --ff-only`
       Once updated, re-locate the plugin, re-read `<plugin>/versions.json` to get the new version, print `"StratOS plugin updated to v<new_version> — reload plugins and re-run /stratosphere-update."` verbatim, and then **HALT** execution.

     - **Else / Catch-all (Manual/Copied Claude Install or other)**:
       If the plugin directory does not match any of the above, print the following notification verbatim:
       `Update your installed StratOS plugin from its source (re-run your original install method), then re-run /stratosphere-update.`
       Then **HALT** execution. Never run git commands on a non-git directory.

---

## Phase 0.5: Pre-v4 Layout Detection (blocking)

Before computing scope, detect whether this project predates v4.0.0.

1. **Check:** does `.agents/workflows/` exist, or does `.gitignore` contain a bare `.agents/skills/` line?
2. **If neither:** the project is already on the v4 layout. Continue to Phase 0.6.
3. **If either:** HALT and instruct the user. `stratosphere-update` **cannot** complete this migration on its own:
   - `reconcile_gitignore()` only *adds* entries, so the stale `.agents/skills/` line survives and every skill installed by this update lands in an ignored directory — silently untracked.
   - This flow has no removal phase, so the superseded `.agents/workflows/*.md` remain. Until 2026-11-01 Antigravity indexes both trees, and `/0a_start-session` and `/0a-start-session` both resolve, to different versions of the same skill.
   - `.memory/` and `docs/` are `preserved` tier, so their OKF frontmatter is never migrated to v0.2.

   Emit verbatim:

   ```
   [PRE-V4] This project uses the retired .agents/workflows/ layout.
   Run the one-shot migration first, from the project root:

     python <plugin>/scripts/migrations/migrate_v3_to_v4.py            # dry run
     python <plugin>/scripts/migrations/migrate_v3_to_v4.py --apply

   It is idempotent, spares user-authored workflow files, and reports
   anything it leaves behind. Then re-run /stratosphere-update.
   ```

   Do not proceed to Phase 1 until the migration has run.

_Completion criterion:_ either the project is confirmed v4-shaped, or the user has been given the migration command and this run has stopped.

## Phase 0.6: Suite Integrity & Legacy Cleanup (non-fatal halt)

Skills refresh from the canonical `dist/skills/` bundle (the located `<plugin>`'s sibling skills; Phase 1's scaffolder places them). Before computing scope, verify that bundle is whole and clear pre-canonical-bundle leftovers. Both checks are deterministic scripts — relay their output, do not re-derive it.

0. **Old plugin guard:** if `<plugin>/scripts/check_suite.py` is missing, the installed plugin predates the integrity check — print `Installed StratOS plugin predates the integrity check; update it (re-run your install method), then re-run /stratosphere-update.` and **HALT** (never call a missing script).

1. **Suite integrity:**
   ```bash
   python <plugin>/scripts/check_suite.py suite
   ```
   Exit 1 → print the report verbatim (missing/corrupt lifecycle skills + the `npx skills add ... --copy -y` remediation) and **HALT** without touching the project. Exit 0 → continue.

2. **Legacy paths** (`dist/claude-code`, a payload-carrying `dist/antigravity`, stale lifecycle files in `commands/`, in the project and in old plugin install roots). Never deletes without confirmation:
   ```bash
   python <plugin>/scripts/check_suite.py legacy
   ```
   Exit 0 → continue. Exit 1 → show the listed paths and ask once (`AskUserQuestion` / `ask_question`): delete them? On yes, run `python <plugin>/scripts/check_suite.py legacy --apply` and log the migration summary; on no, continue and note they remain (they can shadow the new skills).

_Completion criterion:_ the suite is confirmed whole, and legacy paths are removed, declined, or absent.

---

## Phase 1: Compute Update Scope

1. **Run the preview dry-run:**
   Run `python <plugin>/scripts/scaffold.py --update --dry-run` (using the `<plugin>` path located in Phase 0) from the project root.
   This will inspect the workspace, match locked versions against the plugin's `versions.json`, and output `.tmp/stratosphere-update-worklist.json`.

2. **Read the worklist:**
   Load and parse `.tmp/stratosphere-update-worklist.json`.

---

## Phase 2 & 3: Merge Residue & Review

For every file in the worklist, perform the appropriate merge or review step:

### 1. Conflict Preserved Files (`status: "conflict"`)
For each block in `preserved_files` flagged with `status: "conflict"`, you must perform a 3-way merge:
- **Base Block Content:** Compute or retrieve the original block content (the old template block before user/template changes).
- **User Block Content:** Read the current block content in the workspace file.
- **New Block Content:** Read the block content in the new template file under `<plugin>/assets/templates/memory/`.
- **Merge action:** Merge the framework improvements into the block while preserving the user's custom edits. Do **NOT** touch any content outside the block.
- **Write back:** Write the fully merged file to its path suffix: `<filepath>.stratosphere-new` (e.g. `.memory/BACKLOG_MAP.md.stratosphere-new`).
- **Frontmatter:** copy the project file's frontmatter verbatim; never adopt the template's (a changed frontmatter, e.g. `timestamp:` → `generated:`, aborts the update).

### 2. Constitution Files (`needs_review_constitution`)
For each constitution file that has changed:
- Show a side-by-side diff comparing the workspace file against the new template version under `<plugin>/assets/templates/constitution/`.
- Ask the user for confirmation: *"Found updates to the constitution file `<filename>`. Merge them?"*
- If confirmed, merge the new rules/sections while keeping any user customizations (such as the pointer directory or vision settings) and write to `<filepath>.stratosphere-new`.
- If declined, copy the existing workspace file verbatim to `<filepath>.stratosphere-new` to ensure it passes Phase 4 invariants during commit.

### 3. Unmarked Preserved Files (`status: "unmarked"`)
- If the file has no `SOS:BLOCK` markers, do **NOT** attempt to overwrite or merge.
- Print the guard notice: *"Unmarked framework file `<path>` — run `python scripts/migrations/inject_markers.py` to enable in-place updates."*
- If the notice is not already acknowledged, prompt the user to migrate. Skip updating the file content.

### 4. Modified Scripts (`needs_review_scripts`)
- Merge `<script>.stratosphere-new` into the **real** script (keep local fixes, take upstream features), then delete the `.stratosphere-new`. Never edit the `.stratosphere-new`: every update run re-stages it.
- A script still differing from upstream stays flagged on later runs (update writes no lock baseline for it); once it equals upstream, the next `--update` baselines it. To keep intentional local changes, run `scaffold.py --repair-lock` only after reviewing — it re-baselines **every** managed file from the workspace.

### 5. Retired `timestamp:` in `.memory/`
- `validate_memory.py` warns per file (exit 2) and no update fixes it: preserved files keep their frontmatter. Fix by hand, frontmatter only: `timestamp: <D>` → `generated:` with `by: stratosphere-setup` and `at: <D>` (indented).

---

## Phase 4: Verification and Commit

1. **Verify proposed files:**
   Ensure all `.stratosphere-new` files are populated. Run `python <plugin>/scripts/scaffold.py --verify` or `python <plugin>/scripts/scaffold.py --update` (non-dry-run).
   The scaffolder will:
   - Load each `.stratosphere-new` file.
   - Run Level-3 invariants:
     1. **Out-of-block byte-identity:** Compare raw bytes outside changed blocks against the original file, asserting they are identical.
     2. **Marker integrity:** Validate exactly one ordered START/END pair per block ID, and check for unknown block IDs.
     3. **Cheap corroborating checks:** Assert BT-xxx ID sets, Backlog row count, and §3 Immortal Component DR-xxx ID sets are unchanged.

2. **Apply changes:**
   If all invariants pass, the scaffolder will overwrite the original project files with the `.stratosphere-new` files, delete the `.stratosphere-new` files, and update `.agents/.stratosphere-lock.json` last.
   If any validation fails, the scaffolder will abort and write nothing.

---

## Phase 5: GitHub Reconcile

1. **Reconcile labels and extensions:**
   Invoke `stratosphere-setup --re-reconcile-labels` (in Standalone Mode) in the user's terminal/workspace.
   This will:
   - Synchronize/add any newly introduced canonical labels (such as `concept:*`).
   - Re-reconcile project boards and sync actions.
   - Skip gracefully if GitHub CLI is absent or unauthenticated.

---

## Phase 6: Skill Synchronization (Advisory)

1. **Verify and synchronize domain skills:**
   Because domain-specific skills are third-party, gitignored, and fetched on-demand, they are not bundled directly into `scaffold.py`. Remind the user to run, or offer to run:
   `/sync-skills`
   to ensure that all local skill definitions are fully synchronized with their latest upstream sources and not orphaned.

2. **Host-visibility check (also after a sync):** the `system` pack (`code-simplifier`, `skill-creator`) must be visible to the running host, not only on disk. Run (`--host claude` on Claude Code, `--host agents` otherwise):
   ```bash
   python <plugin>/scripts/check_suite.py visibility --host <claude|agents>
   ```
   Exit 1 → non-fatal halt: print the report verbatim (skills + copy command, or `/sync-skills` if absent) and re-run after the fix.
