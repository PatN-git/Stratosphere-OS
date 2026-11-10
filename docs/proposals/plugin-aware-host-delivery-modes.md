---
name: plugin-aware-host-delivery-modes
title: "Proposal: Plugin-Aware Host Delivery Modes and Setup/Update Optimization"
description: Architectural proposal for configurable skill delivery modes (plugin vs in-repo), eliminating prompt token waste and git repo churn while maintaining bulletproof multi-host compatibility for v5.2.1+.
type: proposal
version: "1.0.0"
generated:
  by: Antigravity Architect
  at: 2026-11-10
---

# Proposal: Plugin-Aware Host Delivery Modes & Setup/Update Optimization

**Status:** Approved for Implementation (Target: v5.2.1)  
**Track:** Constitution & Setup Optimization (`0 Constitution & Memory`)  
**Target Release:** v5.2.1  
**Author:** Antigravity Architect  

---

## 1. Executive Summary & Problem Statement

StratosphereOS v5.2 introduced native Google Antigravity and Claude Code plugin distribution (`dist/plugin.json`, `~/.gemini/config/plugins/stratosphere-os`). Under this packaging model, the host IDE natively discovers, registers, and serves all 28 bundled lifecycle workflows and execution skills (`/0a-start-session`, `/stratosphere-update`, `/micro-tdd`, etc.) host-wide.

However, `src/scripts/scaffold.py` was historically authored for file-based copy distribution (`SKILL_TARGETS = [".agents/skills"]`). When developers run `/stratosphere-setup` or `/stratosphere-update`:
1. **Duplicate Host Discovery:** Antigravity registers all 28 bundled skills twice—once under **Plugins** (`stratosphere-os`) and once under **Workspace Skills & Rules** (`.agents/skills/`).
2. **System Prompt Token Waste:** Duplicate registration injects skill signatures twice into every agent invocation, consuming **~1,540 redundant prompt tokens per turn** (~61,600 wasted tokens over an average 40-turn feature session).
3. **Severe Git Churn & Clutter:** Consumer repositories (`Trading`, `CleanTechHub`) are burdened with **186 boilerplate framework files** across 28 skill folders in `.agents/skills/`. Routine StratOS updates generate multi-file diffs in consumer project commit histories.
4. **The Multi-Host Dilemma:** If `.agents/skills/` is dropped unconditionally, multi-host workflows fail: developers opening projects in Cursor, Codex, Devin, or CLI agents (which lack plugin runtimes and depend strictly on `.agents/skills/`) are left with zero lifecycle skills.

This proposal introduces **Configurable Host Delivery Modes** (`skill_delivery: "plugin" | "in-repo"`), providing a zero-clutter experience for plugin hosts while ensuring robust fallback bridges for multi-host environments.

---

## 2. Quantitative & Architectural Impact

| Metric | Legacy (v5.2.0 In-Repo Only) | Optimized (v5.2.1 Plugin Mode) | Benefit |
| :--- | :--- | :--- | :--- |
| **System Prompt Overhead** | ~3,080 tokens/turn (duplicate entries) | ~1,540 tokens/turn (plugin host only) | **50% prompt token reduction** (~1,540 tokens/turn saved) |
| **Boilerplate File Footprint** | 186 files across 28 skill directories | 0 bundled skill files (only third-party skills) | **186 files eliminated from consumer git repos** |
| **Upgrade Git Diff** | 50–150 changed files per release | 1 file modified (`.stratosphere-lock.json`) | **Zero-noise git log in downstream consumer repos** |
| **Multi-Host Usability** | Works out-of-the-box in Cursor | Seamless switch via 1-command fallback bridge | Full multi-host parity with explicit opt-in |

---

## 3. Core Architecture & Contracts

### 3.1 Lockfile Contract (`.agents/.stratosphere-lock.json`)

The lockfile schema is updated to track delivery mode and plugin provenance:

```json
{
  "plugin_id": "stratosphere-os",
  "installed_plugin_version": "5.2.1",
  "skill_delivery": "plugin",
  "artifacts": {
    ".agents/rules/stratosphere.md": {
      "version": "5.2.1",
      "sha256_at_install": "abc123..."
    }
  }
}
```

**Valid values for `skill_delivery`:**
- `"plugin"`: Host delivers bundled lifecycle and execution skills. `scaffold.py` does **not** copy bundled skills into `.agents/skills/`. `.agents/skills/` is reserved strictly for project-level third-party skills (e.g. Supabase, Vercel) installed via `/sync-skills`.
- `"in-repo"`: Multi-host compatibility. `scaffold.py` copies and tracks all 28 bundled skills in `.agents/skills/`.

---

### 3.2 Interactive Setup Flow (`stratosphere-setup`)

When `/stratosphere-setup` runs in a new or unconfigured project:

1. **Host Environment Detection (Smart Contextual Default):**
   - Check execution path: if running from `~/.gemini/config/plugins/stratosphere-os` or `~/.claude/plugins/cache/*`, detect that a native plugin host is active.
2. **Interactive Decision Gate:**
   Prompt the user with a single high-clarity choice:
   ```text
   Choose StratosphereOS Skill Delivery Mode:
     [1] (Recommended) Plugin Mode: Zero repo clutter. 28 lifecycle skills load from Antigravity/Claude plugin.
         -> Only third-party project skills live in .agents/skills/. Saves ~1,500 prompt tokens/turn.
     [2] Multi-Host Mode: Copies all 28 lifecycle skills into .agents/skills/ for Cursor, Codex, Devin, or CLI agents.
   Select [1/2] (default: 1):
   ```
   *(If running from raw git clone / CLI without host plugin detection, the default is intelligently inverted to `[2] Multi-Host Mode`)*.
3. **Execution:**
   - Record `skill_delivery: "plugin" | "in-repo"` in `.agents/.stratosphere-lock.json`.
   - In `"plugin"` mode: scaffold `.memory/`, `.agents/rules/`, `.agents/scripts/`, and `.agents/skills/.gitkeep`. Skip copying bundled skills into `.agents/skills/`.
   - In `"in-repo"` mode: scaffold complete file tree including bundled skills into `.agents/skills/`.

---

### 3.3 Seamless Update & Migration Flow (`stratosphere-update`)

When `/stratosphere-update` runs on an existing project:

1. **Lockfile Inspection:**
   - If `skill_delivery` is already recorded in `.agents/.stratosphere-lock.json`, respect it automatically without prompting the user.
   - If `skill_delivery` is missing (legacy v5.0/v5.1/v5.2.0 project):
     - Prompt once to select mode (defaulting to `plugin` if running inside a host plugin).
2. **Migration Handling (`in-repo` → `plugin`):**
   - Identify all 28 bundled skills previously tracked in `artifacts`.
   - For each file: verify if file content matches `sha256_at_install`.
   - **Pristine Bundled Skills:** Safely unlinked and deleted from `.agents/skills/`.
   - **User-Modified Bundled Skills:** **Quarantined to `.agents/custom-skills/<name>/`** with a clear notification. This guarantees zero data loss while preventing duplicate command collisions in the host.
   - **Third-Party Skills (e.g. Supabase, Vercel):** Left completely untouched. Third-party skills are tracked in `.agents/skills/.lock.json` and are immune to bundled artifact operations.
3. **Reverse Migration (`plugin` → `in-repo`):**
   - If the user re-runs with `--delivery in-repo`, copy all 28 bundled skills into `.agents/skills/` and record their hashes in `artifacts`.
4. **Ghost Lock Cleanup:**
   - Prune unlinked skill artifacts from `.agents/.stratosphere-lock.json` so `scaffold.py` does not retain ghost references.

---

### 3.4 Multi-Host Fallback Bridge & `AGENTS.md` Contract

To prevent the "Blind Drop" when a `plugin`-mode repository is cloned or opened in Cursor, Codex, or Devin:

1. **`AGENTS.md §8` Fallback Directive:**
   Add explicit instruction in `AGENTS.md §8 (Host Activation)`:
   > "If `skill_delivery: plugin` is set in `.agents/.stratosphere-lock.json` and this host lacks native StratosphereOS plugin integration (e.g., Cursor, Codex, OpenClaw), restore lifecycle skills into `.agents/skills/` by running:  
   > `python .agents/scripts/delivery.py --restore-skills` or `npx skills add PatN-git/Stratosphere-OS/dist/skills -a <host> --copy -y`."
2. **Lightweight In-Repo Utility (`.agents/scripts/delivery.py`):**
   Commit a lightweight, zero-dependency helper in `.agents/scripts/` that allows switching modes or restoring skills without requiring the global plugin cache:
   ```bash
   python .agents/scripts/delivery.py --status
   python .agents/scripts/delivery.py --set-mode [plugin|in-repo]
   python .agents/scripts/delivery.py --restore-skills
   ```

---

### 3.5 Delivery-Mode Aware Suite Integrity (`check_suite.py`)

`src/scripts/check_suite.py` is updated to support both delivery modes:

1. **`check_suite.py suite`:**
   - Reads `.agents/.stratosphere-lock.json` if run inside a consumer project.
   - If `skill_delivery == "plugin"`:
     - Verifies integrity of the plugin bundle at `<plugin>`.
     - Asserts that `.agents/skills/` contains **zero duplicate bundled skills** (flagging accidental prompt bloat).
   - If `skill_delivery == "in-repo"`:
     - Asserts that all 24 lifecycle skills are present in `.agents/skills/` with valid frontmatter.
2. **`check_suite.py visibility`:**
   - Enhanced to verify that the host's active plugin search paths include `~/.gemini/config/plugins/stratosphere-os` and `~/.claude/plugins/cache/*`.

---

## 4. Key Invariants & Safeguards

1. **Third-Party Isolation:** Skills installed via `/sync-skills` or `npx skills add` are tracked in `.agents/skills/.lock.json` and MUST NEVER be touched or pruned by delivery mode changes.
2. **Directory Anchor (`.gitkeep`):** `.agents/skills/.gitkeep` is tracked by git so `.agents/skills/` is never dropped by git when empty of bundled skills.
3. **Reversibility:** A user can switch between modes at any time with a single command (`python .agents/scripts/scaffold.py --update --delivery in-repo`).
4. **Zero Prompting on Repeat Runs:** Once configured in the lockfile, routine updates never re-prompt.

---

## 5. Implementation Plan (v5.2.1 Slices)

1. **Phase 1: Lockfile & Scaffolder Engine (`src/scripts/scaffold.py`):**
   - Add `--delivery [plugin|in-repo]` CLI argument.
   - Add interactive delivery mode prompt to `stratosphere-setup` and `stratosphere-update`.
   - Implement `is_file_pristine()` checking and quarantine logic to `.agents/custom-skills/`.
   - Update `get_bundled_project_scripts()` to include `delivery.py`.
2. **Phase 2: Suite Check Mode Awareness (`src/scripts/check_suite.py`):**
   - Make `suite` and `visibility` commands inspect `.stratosphere-lock.json`.
   - Add verification that `.agents/skills/` has no duplicate bundled skills in `plugin` mode.
3. **Phase 3: In-Repo Helper & Fallback (`src/scripts/delivery.py` & `AGENTS.md`):**
   - Implement `.agents/scripts/delivery.py`.
   - Update `src/constitution/AGENTS.md §8` with the fallback command.
4. **Phase 4: Automated Test Coverage (`tests/scripts/`):**
   - Unit and integration tests for `plugin` mode setup, `in-repo` mode setup, migration from `in-repo` to `plugin` with quarantine of modified files, and `check_suite.py` behavior under both modes.
