---
name: stratosphere-update
type: workflow
description: Upgrade in-place the StratosphereOS framework templates, rules, and workflows without overwriting project data.
version: "1.0.6"
timestamp: 2026-07-13
---

# StratosphereOS Update Flow

Upgrade project framework files, rules, and memory templates in place while fully preserving custom project data, logs, and registries.

## Core Principle

Your `.memory/` data (such as backlog tasks, active learning logs, custom glossary entries, database tables) and your customized constitution pointers are **never** overwritten. Only framework-owned guidance sections wrapped in `SOS:BLOCK` markers are updated in-place. If there are conflicts, you (the agent) will merge them, and the user will explicitly confirm all diffs.

---

## Phase 0: Plugin Freshness (remote)

Before running the local scaffolding update, verify if the installed StratosphereOS plugin is up to date with the latest release on GitHub.

1. **Locate Installed Plugin:**
   Locate the installed plugin root directory `<plugin>` using the following search order:
   - **Claude Code:**
     - Marketplace install: `~/.claude/plugins/cache/*/stratosphere-os/*/` (glob — pick the newest version directory)
     - Manual/global: `~/.claude/plugins/stratosphere-os/`
     - Manual/local: `./.claude/plugins/stratosphere-os/`
   - **Antigravity:**
     - Global: `~/.gemini/config/plugins/stratosphere-os/`
     - Local: `./.agents/plugins/stratosphere-os/`

2. **Read Installed Version:**
   Read and parse `<plugin>/versions.json`. Extract the `"plugin_version"` field. Let this be `<installed_version>`.

3. **Check Latest Version on GitHub:**
   Run the following GitHub CLI command to retrieve the latest release tag name of the framework:
   `gh release view --repo PatN-git/Stratosphere-OS --json tagName --jq .tagName`
   
   - **Offline / No GH fallback:** If `gh` is not installed or not authenticated (`gh auth status` fails), or if the network is unreachable (timeout/error), print the following warning line verbatim to the console:
     `Could not verify latest StratOS release (offline/no gh); proceeding under installed v<installed_version>. If the release changed the update procedure, re-run when online.`
     and immediately proceed to **Phase 1: Compute Update Scope**.
   
   - If the check succeeds, normalize the retrieved release tag by stripping any leading `v` (e.g. `v1.1.0` becomes `1.1.0`). Let this be `<latest_version>`.

4. **Compare and Route Update Flow:**
   Compare `<latest_version>` against `<installed_version>` numerically by integer major.minor.patch components, not as strings (so 1.10.0 > 1.9.0).
   
   - **Up to date:** If `<latest_version>` <= `<installed_version>`: print the following line:
     `StratOS plugin is current (v<installed_version>).`
     and proceed to **Phase 1: Compute Update Scope**.
     
   - **Out of date:** If `<latest_version>` > `<installed_version>`: detect the installation type by checking `<plugin>`'s path and run the matching update path:
     
     - **Claude Marketplace Cache** (path starts with `~/.claude/plugins/cache/`):
       Do **NOT** touch the cache folder directly and do **NOT** attempt any git operations on it. Print the following notification verbatim:
       `Newer StratOS v<latest_version> available (you have v<installed_version>). Update via:`
       `  /plugin marketplace update stratosphere-os`
       `then /reload-plugins (or enable auto-update for this marketplace), and re-run /stratosphere-update.`
       Then **HALT** execution. (If the user explicitly instructs to proceed anyway, continue against the stale plugin with a loud warning).
       
     - **Antigravity Install** (path is under `~/.gemini/config/plugins/` or `./.agents/plugins/`):
       The installed directory is a copy, not a git checkout. Print the following notification verbatim:
       `Update your StratOS clone (git pull) and re-run scripts/install-antigravity.sh (or .ps1) --global (or --local), then re-run /stratosphere-update.`
       If a source clone path is known/available, offer to run those commands to pull and reinstall after one confirmation. Otherwise, halt.
       
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
   - Verify/install necessary tools (such as the `gh-sub-issue` extension).
   - Skip gracefully if GitHub CLI is absent or unauthenticated.

---

## Phase 6: Skill Synchronization (Advisory)

1. **Verify and synchronize domain skills:**
   Because domain-specific skills are third-party, gitignored, and fetched on-demand, they are not bundled directly into `scaffold.py`. Remind the user to run, or offer to run:
   `/sync-skills`
   to ensure that all local skill definitions are fully synchronized with their latest upstream sources and not orphaned.
