---
name: stratosphere-update
type: workflow
description: Upgrade in-place the StratosphereOS framework files, workflows, memory templates, rules, and constitution without overwriting project data.
version: "1.0.0"
timestamp: 2026-07-08
---

# StratosphereOS Update Flow

Upgrade project framework files, rules, and memory templates in place while fully preserving custom project data, logs, and registries.

## Core Principle

Your `.memory/` data (such as backlog tasks, active learning logs, custom glossary entries, database tables) and your customized constitution pointers are **never** overwritten. Only framework-owned guidance sections wrapped in `SOS:BLOCK` markers are updated in-place. If there are conflicts, you (the agent) will merge them, and the user will explicitly confirm all diffs.

---

## Phase 0: Compute Update Scope

1. **Locate the installed plugin root** (`<plugin>`) using the same search order as setup:
   - **Claude Code:**
     - Marketplace install: `~/.claude/plugins/cache/*/stratosphere-os/*/` (glob — pick the newest version directory)
     - Manual/global: `~/.claude/plugins/stratosphere-os/`
     - Manual/local: `./.claude/plugins/stratosphere-os/`
   - **Antigravity:**
     - Global: `~/.gemini/config/plugins/stratosphere-os/`
     - Local: `./.agents/plugins/stratosphere-os/`

2. **Run the preview dry-run:**
   Run `python <plugin>/scripts/scaffold.py --update --dry-run` from the project root.
   This will inspect the workspace, match locked versions against the plugin's `versions.json`, and output `.tmp/stratosphere-update-worklist.json`.

3. **Read the worklist:**
   Load and parse `.tmp/stratosphere-update-worklist.json`.

---

## Phase 1 & 2: Merge Residue & Review

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
   - Run memory validation `python .agents/scripts/validate_memory.py`.

2. **Apply changes:**
   If all invariants pass, the scaffolder will overwrite the original project files with the `.stratosphere-new` files, delete the `.stratosphere-new` files, and update `.agents/.stratosphere-lock.json` last.
   If any validation fails, the scaffolder will abort and write nothing.
