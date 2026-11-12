---
name: stratosphere-update
description: "Upgrade in-place the StratosphereOS framework templates, rules, and workflows without overwriting project data. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.10.0"
timestamp: 2026-11-12
---

# StratosphereOS Update Flow

Upgrade project framework files, rules, and memory templates in place while preserving custom project data, logs, and registries.

## Core Principle

Your `.memory/` data and customized constitution pointers are **never** overwritten. Only framework guidance wrapped in `SOS:BLOCK` markers updates in place. Conflicts are merged by the agent and confirmed by the user.

---

## Phase 0: Plugin Freshness (remote)

Verify installed plugin freshness against GitHub before updating workspace scaffolding.

1. **Locate Installed Plugin:**
   Locate installed `stratosphere-setup` skill directory `<plugin>` (carries scaffolder: `scripts/`, `assets/`, `versions.json`) using the first matching directory with `scripts/scaffold.py`. Check the running host's own group first; only if none matches, try the other group:
   - **Claude Code:** `./.claude/skills/stratosphere-setup/`, `~/.claude/skills/stratosphere-setup/`, marketplace cache `~/.claude/plugins/cache/*/stratosphere-os/*/dist/skills/stratosphere-setup/` (glob — newest version directory)
   - **Antigravity and other hosts:** `./.agents/skills/stratosphere-setup/`, `~/.gemini/config/plugins/*/skills/stratosphere-setup/` (glob — newest directory if multiple match), `~/.gemini/config/plugins/stratosphere-os/skills/stratosphere-setup/` (`agy plugin install dist`), `~/.gemini/config/skills/stratosphere-setup/`, `~/.agents/skills/stratosphere-setup/`

2. **Read Installed Version:**
   Read and parse `<plugin>/versions.json`. Extract `"plugin_version"` as `<installed_version>`.

3. **Check Latest Version on GitHub:**
   Query latest release tag: `gh release view --repo PatN-git/Stratosphere-OS --json tagName --jq .tagName`
   
   - **Offline / No GH fallback:** If `gh` is unavailable/unauthenticated or network fails, print verbatim:
     `Could not verify latest StratOS release (offline/no gh); proceeding under installed v<installed_version>. If the release changed the update procedure, re-run when online.`
     and immediately proceed to **Phase 0.5**.
   
   - Strip leading `v` (e.g. `v1.1.0` → `1.1.0`) to get `<latest_version>`.

4. **Compare and Route Update Flow:**
   Compare `<latest_version>` against `<installed_version>` numerically by major.minor.patch integers (so 1.10.0 > 1.9.0).
   
   - **Up to date:** If `<latest_version>` <= `<installed_version>`, print:
     `StratOS plugin is current (v<installed_version>).`
     and proceed to **Phase 0.5**.
     
   - **Out of date:** If `<latest_version>` > `<installed_version>`: detect installation type by checking `<plugin>`'s path and run matching update path:
     
     | `<plugin>` path | reference |
     |---|---|
     | starts with `~/.claude/plugins/cache/` | `references/update-claude-marketplace.md` |
     | is under `~/.gemini/config/plugins/` | `references/update-antigravity-plugin.md` |
     | is under `~/.gemini/config/skills/`, `./.agents/skills/`, `~/.agents/skills/`, `~/.claude/skills/` or `./.claude/skills/` | `references/update-copied-skills.md` |

     First match wins: the rows in order, then the two bullets below. Read and follow the matching reference exactly: its confirm-once gate is mandatory. On successful update, re-read `<plugin>/skills/stratosphere-update/SKILL.md` from disk into context and proceed directly to **Phase 0.5**.


     - **In-place Git Checkout** (plugin directory contains a `.git` folder):
       This is a development setup. Ask user for confirmation:
       `Latest version v<latest_version> is newer than installed v<installed_version>. Pull updates from git?`
       If confirmed (using `ask_question` or `AskUserQuestion`), run:
       `git -C <plugin> pull --ff-only`
       Once updated, re-locate plugin, re-read `<plugin>/versions.json` to get new version, re-read `<plugin>/skills/stratosphere-update/SKILL.md` into context to load updated phase definitions, print `StratOS plugin updated to v<new_version> — proceeding to Phase 0.5.` verbatim, and proceed to **Phase 0.5**.

     - **Else / Catch-all (Manual/Copied Claude Install or other)**:
       If plugin directory does not match any of the above, print verbatim:
       `Update your installed StratOS plugin from its source (re-run your original install method), then re-run /stratosphere-update.`
       Then **HALT** execution. Never run git commands on a non-git directory.

---

## Phase 0.5: Suite Integrity & Legacy Cleanup (non-fatal halt)

Skills refresh from the canonical `dist/skills/` bundle. Before computing scope, verify bundle integrity and clear legacy leftovers via deterministic scripts:

0. **Old plugin guard:** if `<plugin>/scripts/check_suite.py` is missing, print `Installed StratOS plugin predates the integrity check; update it (re-run your install method), then re-run /stratosphere-update.` and **HALT**.

1. **Suite integrity:**
   ```bash
   python <plugin>/scripts/check_suite.py suite
   ```
   Exit 1 → print report verbatim (missing/corrupt skills + remediation) and **HALT** without touching project. Exit 0 → continue.

2. **Legacy paths** (`dist/claude-code`, payload `dist/antigravity`, stale command files in `commands/`, project leftovers, old plugin roots, and stale `~/.claude/plugins/cache/` versions). Never delete without confirmation:
   ```bash
   python <plugin>/scripts/check_suite.py legacy
   ```
   Exit 0 → continue. Exit 1:
   - **Tool Execution Barrier:** complete the legacy path check 100% before opening the prompt turn. Never invoke a question tool in the same turn as background check scripts.
   - **Mandatory Visible Markdown Content:** emit the full list of detected legacy paths directly in visible message `content` (never empty content or hidden inside tool calls).
   - **Synchronous Pairing:** call the question tool (`AskUserQuestion` / `ask_question`) in the same turn accompanying the visible list: delete them? On yes, run `python <plugin>/scripts/check_suite.py legacy --apply`; on no, continue noting they remain (may shadow new skills).

_Completion criterion:_ Suite confirmed whole, legacy paths removed, declined, or absent.

---

## Phase 1: Compute Update Scope

1. **Preview dry-run:**
   Run `python <plugin>/scripts/scaffold.py --update --dry-run` (using `<plugin>` located in Phase 0) from project root to inspect workspace, match versions, and write `.tmp/stratosphere-update-worklist.json`.

2. **Read worklist:**
   Load and parse `.tmp/stratosphere-update-worklist.json`.

---

## Phase 2 & 3: Merge Residue & Review

For every file in the worklist, perform the appropriate merge or review step:

### 1. Conflict Preserved Files (`status: "conflict"`)
For each block in `preserved_files` flagged with `status: "conflict"`, perform a 3-way merge:
- **Base / User / New:** Merge framework improvements from `<plugin>/assets/templates/memory/` into user block while preserving user edits. Do **NOT** touch content outside block.
- **Write back:** Write fully merged file to `<filepath>.stratosphere-new` (e.g. `.memory/LEARNINGS.md.stratosphere-new`).
- **Frontmatter:** Copy project file's frontmatter verbatim; never adopt template's (a changed frontmatter, e.g. `timestamp:` → `generated:`, aborts update).

### 2. Constitution Files (`needs_review_constitution`)
For each constitution file that has changed:
- **Tool Execution Barrier:** complete diff generation 100% before opening the review turn. Never invoke a question tool in the same turn as background diff commands.
- **Mandatory Visible Markdown Content:** emit the side-by-side diff comparing workspace file against new template under `<plugin>/assets/templates/constitution/` directly in visible message `content` (never empty content or hidden inside tool calls).
- **Synchronous Pairing:** call the question tool in the same turn accompanying the visible diff: *"Found updates to constitution file `<filename>`. Merge them?"*
- If confirmed, merge new rules/sections while keeping user customizations (pointer directory, vision) and write to `<filepath>.stratosphere-new`.
- If declined, copy existing workspace file verbatim to `<filepath>.stratosphere-new` to ensure it passes Phase 4 invariants during commit.

### 3. Unmarked Preserved Files (`status: "unmarked"`)
- If file has no `SOS:BLOCK` markers, do **NOT** overwrite or merge.
- Print guard notice: *"Unmarked framework file `<path>` — run `python scripts/migrations/inject_markers.py` to enable in-place updates."*
- If not already acknowledged, prompt user to migrate. Skip updating file content.

### 4. Modified Scripts (`needs_review_scripts`)
- Merge `<script>.stratosphere-new` into **real** script (keep local fixes, take upstream features), then delete `.stratosphere-new`. Never edit `.stratosphere-new`: every update run re-stages it.
- A script still differing from upstream stays flagged on later runs; once it equals upstream, next `--update` baselines it. To keep intentional local changes, run `scaffold.py --repair-lock` only after reviewing — it re-baselines managed files.

### 5. Retired `timestamp:` in `.memory/`
- `validate_memory.py` warns per file (exit 2) and no update fixes it: preserved files keep frontmatter. Fix by hand, frontmatter only: `timestamp: <D>` → `generated:` with `by: stratosphere-setup` and `at: <D>`.

---

## Phase 4: Verification and Commit

1. **Verify proposed files:**
   Ensure all `.stratosphere-new` files are populated. Run `python <plugin>/scripts/scaffold.py --verify` or `python <plugin>/scripts/scaffold.py --update` (non-dry-run).
   Scaffolder runs Level-3 invariants:
   1. **Out-of-block byte-identity:** Raw bytes outside changed blocks equal original.
   2. **Marker integrity:** Exactly one ordered START/END pair per block ID; no unknown IDs.
   3. **Cheap corroborating check:** Assert §3 Immortal Component DR-xxx ID set is unchanged.

2. **Apply changes:**
   If all invariants pass, scaffolder overwrites project files with `.stratosphere-new` files, deletes them, and updates `.agents/.stratosphere-lock.json` last. Validation failure aborts with no writes.

3. **Design toolchain lockfile:** worklist `design_lockfile_stale: true` (scaffolder prints `NOTE:`) → committed `.agents/scripts/design/package-lock.json` pins old `@google/design.md`; `npm ci` fails. After apply succeeds, run `npm install --prefix .agents/scripts/design` (Windows: `cmd /c "npm install --prefix .agents/scripts/design"`); include updated `package-lock.json` in update commit. No Node → skip.

4. **Test gate advisory:** run `python .agents/scripts/test_gate.py status`. Exit 1 → print: `Optional: python .agents/scripts/test_gate.py install adds the pre-commit test gate (see stratosphere-setup Checkpoint 5.3).` Advisory: never install or ask.

5. **v5 map migration (once):** `.memory/BACKLOG_MAP.md` with `tracker: local` or no `tracker:` key → ask once (`AskUserQuestion` / `ask_question`) to migrate it. Yes → set `tracker: local` and `tracker_branch: <repo>/issues` in ARCHITECTURE.md's frontmatter, run `python .agents/scripts/issues.py migrate` (map moves to `.memory/archive/`), commit both. No → next update asks again. Never merge map.

6. **Untrack STATUS:** if `.memory/STATUS.md` is tracked: `git rm --cached` it, `git add .gitignore`, plain `git commit`.

---

## Phase 5: GitHub Reconcile

1. **Reconcile labels and extensions:**
   Invoke `stratosphere-setup --re-reconcile-labels` (in Standalone Mode) in user workspace.
   It syncs new canonical labels (e.g. `concept:*`) and Project board; skips without `gh` and under `tracker: local`.

---

## Phase 6: Skill Synchronization (Advisory)

1. **Verify and synchronize domain skills:**
   Domain skills are third-party, gitignored, and fetched on-demand. Remind user to run, or offer to run:
   `/sync-skills`
   to ensure local skill definitions are synchronized with upstreams.

2. **Host-visibility check (also after a sync):** ensure system pack (`code-simplifier`, `skill-creator`) is visible to running host (`--host claude` on Claude Code, `--host agents` otherwise):
   ```bash
   python <plugin>/scripts/check_suite.py visibility --host <claude|agents>
   ```
   Exit 1 → non-fatal halt: print report verbatim (skills + copy command, or `/sync-skills` if absent) and re-run after fix.

---

## Phase 7: Host Cache Invalidation

Refresh host-cached slash commands and tool registries without terminating conversation or restarting host. Subprocesses and `AGENTS.md` §8 disk fallbacks are already live.

1. **Detect Host Environment:**
   Check running host (`CLAUDECODE` env or `--host claude` → Claude Code; else Antigravity).

2. **Emit Host Reload Snippet:**
   - **Antigravity:** Output reload command:
     ```
     /skills reload
     ```
     *(If MCP schemas changed, reload window instead).*
   - **Claude Code:** Output reload command:
     ```
     /reload-plugins
     ```

_Completion criterion:_ Project framework files updated, suite intact, host invalidation directive emitted.
