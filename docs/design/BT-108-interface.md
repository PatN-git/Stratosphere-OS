---
type: interface-design
title: "Design: BT-108 - Host-Agnostic Skill Distribution Framework"
description: "Technical interface and contract design for host-agnostic skill distribution across 8+ AI agent hosts, establishing canonical dist/skills bundling, dual-track distribution, and decoupled repository scaffolding."
timestamp: 2026-09-28
status: approved
slug: host-agnostic-skill-distribution
bt: BT-108
prd: docs/prds/BT-108-host-agnostic-skill-distribution.md
surface: non-ui
version: "1.0.0"
---

# Design: BT-108 - Host-Agnostic Skill Distribution Framework

## Surface & Scope
This design defines the technical distribution interface, packaging contracts, and verification seams for transitioning StratosphereOS from bespoke shell installers (`install-claude-code.{sh,ps1}` and `install-antigravity.{sh,ps1}`) to an open-ecosystem distribution framework. The surface encompasses:
1. **Build & Compilation Seam:** `build/build.py` emitting a unified, self-contained `dist/skills/` distribution bundle containing all 26 skills with resolved relative references and multi-host HITL invocation sidecars.
2. **Distribution Track Contracts:**
   - **Track A (Ecosystem Package Manager):** Standard `skills.sh` (`npx skills add`) installation interface.
   - **Track B (Direct Zero-Dependency Copy/Paste):** Direct filesystem placement interface for restricted/offline environments.
   - **Track C (Native Managed Marketplace):** Claude Code plugin marketplace manifest interface (`.claude-plugin/marketplace.json`).
   - **Track D (Antigravity Fallback Bridge):** Lightweight global bridge interface for Google Antigravity environments until upstream path resolution.
3. **Scaffolding & Integrity Seam:** Decoupled execution contract between skill delivery and repository scaffolding, with suite integrity verification confined exclusively to `stratosphere-setup` and `stratosphere-update`.

## Actors & Core Flows

### Actor 1: Framework Maintainer
- **Flow: Release Compilation:** Maintainer runs `python build/build.py`. The build engine compiles all skills from `src/skills/` and `src/workflows/`, resolves transitive `references/`, attaches `agents/openai.yaml` and frontmatter sidecars, and deposits the output strictly into `dist/skills/`.
- **Flow: CI & Drift Audit:** Automated test harnesses (`tests/install-harness` and `scripts/check.sh`) validate `dist/skills/` against source definitions and confirm that no obsolete shell scripts exist.

### Actor 2: Consumer Developer
- **Flow: Skill Acquisition (Track A):** Developer runs `npx skills add PatN-git/Stratosphere-OS/dist/skills -a <agent> --copy -y`. The package manager copies all 26 skills into the host's designated directory (e.g. `.agents/skills/`, `.cursor/skills/`, `.claude/skills/`).
- **Flow: Skill Acquisition (Track B):** In an air-gapped or non-Node environment, developer copies or clones `dist/skills/` directly into `.agents/skills/`.
- **Flow: Skill Acquisition (Track C):** In Claude Code, developer runs `/plugin marketplace add PatN-git/Stratosphere-OS`.
- **Flow: Repository Scaffolding:** Developer opens their agent host and triggers `/stratosphere-setup`. The setup skill verifies lifecycle suite integrity and bootstraps repository memory (`.memory/`), constitution (`AGENTS.md`), rules (`.agents/rules/`), and harness pointers.
- **Flow: Project Upgrade:** Developer runs `/stratosphere-update` to refresh skills from `dist/skills/`, auditing and cleaning legacy paths.

## Aha Moment & Time-to-Value
- **Aha Moment:** Time to first successful skill invocation (`<30s`). The developer runs one single command (`npx skills add PatN-git/Stratosphere-OS/dist/skills --copy -y`), opens their IDE, types `/0a-start-session` or `/stratosphere-setup`, and the agent immediately recognizes the command with full progressive disclosure and zero broken links.
- **Time-to-Value Goal:** Zero prerequisite shell execution; zero script permission prompting (`chmod +x` or PowerShell execution policy bypasses); zero installation questions beyond target agent selection.

## Direction Alternatives (Considered)
- **Winner: Dual-Track Distribution via Canonical `dist/skills/` + Direct GitHub Fallback (Direction 1):**
  Single unified `dist/skills/` directory containing all 26 compiled skills with sidecars and relative references. Consumers install via `skills.sh` (Track A) or direct copy/paste (Track B) alongside native marketplaces (Track C). Antigravity global fallback bridge retained (Track D). Clean split delegates scaffolding to `/stratosphere-setup`, with integrity checks isolated in setup/update.
- **Alternatives Considered:**
  - *Alternative 2 (Root-Level `skills/` Directory):* Rejected because OpenClaw hardcodes `skillsDir: "skills"`. Placing uncompiled sources or distribution artifacts in root `skills/` causes OpenClaw to collide build output with active runtime skills during self-hosting dogfooding.
  - *Alternative 3 (Host-Specific Multi-Package Generation):* Rejected because generating separate folders (`dist/claude/`, `dist/antigravity/`, `dist/cursor/`, etc.) re-introduces the maintenance combinatorial explosion and misleading byte-identical trees that BT-108 was designed to eliminate.

## States / Edge Classes
- **Input Edge Classes:**
  - Missing subpath flag (root invocation vs explicit subpath).
  - Non-Node / air-gapped execution environments.
  - Disabled Windows Developer Mode (NTFS symlink denial).
  - Selective skill cherry-picking via interactive prompts.
  - Case-sensitive vs case-insensitive filesystem paths.
  - Upgrading from legacy v4.0.0 directories (`dist/claude-code`, duplicate `dist/antigravity`, deprecated `commands/`).

### UX / System Stress Matrix

| Adverse Condition | Failure Mode | Required Handling / Mitigation |
| :--- | :--- | :--- |
| **Offline / air-gapped consumer environment without Node.js or git** | Track A (`npx skills add`) fails with `npx: command not found` or DNS timeout; git clone fails. Automated package fetchers crash, blocking skill acquisition. | Document and support Track B (Direct Copy): provide clear instructions for copying a pre-downloaded archive or local clone of `dist/skills/` into `.agents/skills/`. Ensure `build.py` emits zero-dependency standalone skill folders with self-contained relative references requiring no runtime Node.js or network access. |
| **Partial skill cherry-picking via interactive `skills add`** | Consumer selectively installs a subset of skills (e.g. cherry-picking `3d-implement-issue` while omitting `1a-research`, `2a-write-prd`, or `4a-verify-and-ship`). Mid-cycle handoffs fail at runtime when referencing missing orchestrators. | Scaffolding Seam: `stratosphere-setup` and `stratosphere-update` execute a strict suite integrity validation check asserting the presence of all 22 core lifecycle skills. Missing skills trigger a non-fatal halt with an actionable list of absent skills and the full command (`npx skills add PatN-git/Stratosphere-OS/dist/skills -y`). `0a-start-session` remains completely unburdened by checks. |
| **Upstream `skills.sh` breaking change, registry outage, or network timeout** | `npx skills add` hangs, returns HTTP 5xx / socket timeout, or CLI flags (`--agent`, `--copy`) break after an upstream `vercel-labs/skills` release. | Document Track B (Direct Copy/Paste) and Track C (Native Claude Marketplace `/plugin marketplace add`) as verified zero-network-dependency fallbacks in `README.md`; pin recommended invocation syntax and advise local path targeting (`npx skills add ./dist/skills`). |
| **Windows symlink permissions (Developer Mode disabled / non-admin)** | `npx skills add` defaults to creating NTFS symlinks; Windows throws `EPERM: operation not permitted, symlink`, or Antigravity IDE fails to traverse symlinks into `references/` (upstream Issue #633). | Mandate the `--copy` flag in all Track A documentation and automation (`npx skills add ... --copy -y`); ensure Track D Antigravity fallback bridge uses physical recursive file copying rather than filesystem symlinks. |
| **Upgrading from legacy v4.0.0 (`dist/claude-code`, duplicate `dist/antigravity`, or retired shell scripts)** | Stale duplicate skills in `dist/claude-code` or `~/.gemini/antigravity/skills/` shadow new versions; deprecated `commands/` directory collides with modern workflow definitions. | `stratosphere-update` audits legacy installation directories, displays migration alerts, safely deletes or deprecates legacy paths (`dist/claude-code`, `dist/antigravity`, `commands/`), and updates host pointers to the unified `dist/skills/` bundle. |
| **Path casing / trailing slash discrepancies (`dist/skills` vs `dist/skills/`)** | Trailing slash (e.g., `/dist/skills/`) causes `skills.sh` subpath parser to treat trailing segment as empty or mismatch remote git tree; casing divergence (`dist/Skills`) fails on case-sensitive Linux filesystems. | Enforce canonical lowercase path `PatN-git/Stratosphere-OS/dist/skills` (without trailing slash) across all docs, examples, and scripts; validate path normalization in harness tests across Windows and POSIX. |
| **Corrupted or missing transitive reference files inside a skill directory** | Transitive reference cited in `SKILL.md` (e.g., `references/research-evidence-standards.md`) fails to compile or is omitted during manual copy; agent throws read error during progressive disclosure. | Build Seam: upgrade `build.py` `closure_for()` from a warning to a strict build-failing fatal error on missing cited references; Scaffolding Seam: `stratosphere-setup` and `stratosphere-update` verify that all cited files in each skill's `references/` directory exist on disk. |
| **Root repo invocation without subpath (`npx skills add PatN-git/Stratosphere-OS`)** | `skills.sh`'s `SKIP_DIRS` ignores `dist/`, causing top-level root discovery to abort with `"No skills found"`. | Document the mandatory subpath `PatN-git/Stratosphere-OS/dist/skills` in all onboarding docs; maintain OpenClaw dogfooding safety by keeping distribution artifacts inside `dist/skills/` rather than root `skills/`. |
| **Antigravity global path mismatch (`~/.gemini/antigravity/` vs `~/.gemini/config/`)** | `skills.sh` installs globally to runtime state directory `~/.gemini/antigravity/skills/`, leaving Antigravity IDE unable to discover skills located outside `~/.gemini/config/`. | Route global Antigravity installation through Track D (lightweight fallback bridge / `agy plugin import`) targeting `~/.gemini/config/plugins/` or `~/.gemini/config/skills/`, while standardizing project-level installation on `.agents/skills/`. |
| **Missing or stripped HITL sidecars (`agents/openai.yaml`, frontmatter flags)** | Manual copy (Track B) or custom bundler drops dotfiles or `agents/` subfolder; Codex, Claude, Cursor, or Devin execute destructive lifecycle skills autonomously without human oversight. | `build.py` embeds all HITL sidecars (`agents/openai.yaml`, `disable-model-invocation: true`, `triggers: ["user"]`) directly into each skill directory in `dist/skills/`; `stratosphere-setup` suite integrity check validates that sidecars and HITL frontmatter tags are present. |
| **Premature session execution before repository scaffolding** | Developer installs skills via Track A/B and invokes `/0a-start-session` directly without running `/stratosphere-setup`, causing failures due to missing `.memory/` or `AGENTS.md`. | Keep `0a-start-session` lightweight (no runtime suite checks), but enforce an atomic check for `.memory/` presence; if `.memory/` is absent, cleanly prompt the user with a 1-line redirection: "Repository not initialized. Please run /stratosphere-setup first." |
| **Host directory name divergence or casing mismatch** | Host requires directory name to match frontmatter `name:` exactly (e.g. GitHub Copilot silently drops skills if directory casing/spelling differs). | `build.py` enforces directory names identical to frontmatter `name:` slugs (e.g., `0a-start-session`), validated via automated CI linting and `tests/install-harness` across all 8 supported agent hosts. |

## Handoff Notes for 3c/4a
- **3c / Slicing Scope:**
  - S1: Compile to `dist/skills/` and verify `skills.sh` subpath packaging.
  - S2: Delete `scripts/install-claude-code.{sh,ps1}`, remove dead `commands/` copy, update harness and docs.
  - S3: Implement lightweight Antigravity fallback bridge; standardize project-level Antigravity on `.agents/skills/`.
  - S4: Collapse `dist/` into `dist/skills/` with thin manifests (`dist/claude-code/.claude-plugin/plugin.json`, `dist/antigravity/plugin.json`).
  - S5: Implement suite integrity check in `stratosphere-setup` and `stratosphere-update`; update README with dual-track instructions.
- **4a / Audit Assertions:**
  - Assert that `scripts/install-claude-code.sh` and `scripts/install-claude-code.ps1` no longer exist in the working tree.
  - Assert that running `python build/build.py` succeeds with zero errors and emits exactly 26 skill directories in `dist/skills/`.
  - Assert that all 26 skills in `dist/skills/` contain their required HITL sidecars and relative `references/`.
  - Assert that `tests/install-harness` passes 100% against the new canonical bundle.

---

### [Path C · Non-UI] Interface Contract

#### 1. Interface & Command Signatures

##### Track A: Ecosystem Package Manager Contract
```bash
# Project-level installation across all agents (recommended default)
npx skills add PatN-git/Stratosphere-OS/dist/skills -a all --copy -y

# Targeted agent installation (e.g. Claude Code, Antigravity, Cursor, Codex)
npx skills add PatN-git/Stratosphere-OS/dist/skills -a <agent> --copy -y

# Global agent installation
npx skills add PatN-git/Stratosphere-OS/dist/skills -g -a <agent> --copy -y

# Upstream update
npx skills update
```
- **CLI Flags:**
  - `--copy` *(Mandatory)*: Enforces recursive directory file copy, bypassing Windows symlink permission failures and ensuring self-contained offline execution.
  - `-y` *(Mandatory in scripts)*: Accepts prompts automatically to install all 26 skills without interactive omissions.
  - `-a <agent>`: Target agent name matching `skills.sh` registry (`claude-code`, `antigravity`, `cursor`, `codex`, `devin`, `openclaw`, `github-copilot`, `windsurf`, `zed`).

##### Track B: Direct Zero-Dependency Copy/Paste Contract
```bash
# POSIX (Linux/macOS)
mkdir -p .agents/skills && cp -r dist/skills/* .agents/skills/

# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path .agents\skills
Copy-Item -Recurse -Force dist\skills\* .agents\skills\
```

##### Track C: Claude Code Marketplace Manifest Contract
Located at `.claude-plugin/marketplace.json`:
```json
{
  "name": "stratosphere-os",
  "version": "4.1.0",
  "description": "High-density 3-layer agentic orchestration constitution and lifecycle skill pack",
  "skills": [
    "./dist/skills/0a-start-session",
    "./dist/skills/0b-stop-session",
    "./dist/skills/1a-research",
    "./dist/skills/1b-concept-framing",
    "./dist/skills/2a-write-prd",
    "./dist/skills/2b-interface-design",
    "./dist/skills/3a-version-planning",
    "./dist/skills/3b-create-issue",
    "./dist/skills/3c-sprint-planning",
    "./dist/skills/3d-implement-issue",
    "./dist/skills/4a-verify-and-ship",
    "./dist/skills/4b-audit-architecture-drift",
    "./dist/skills/4c-codebase-health-audit",
    "./dist/skills/stratosphere-setup",
    "./dist/skills/stratosphere-update"
  ]
}
```

##### Track D: Antigravity Fallback Bridge Contract
Located at `scripts/install-antigravity-bridge.{sh,ps1}`:
- **Scope:** Fallback utility for global Antigravity installation until `skills.sh` path resolution.
- **Source:** `dist/skills/`.
- **Target:** `~/.gemini/config/skills/` (and optional plugin manifest into `~/.gemini/config/plugins/stratosphere-os`).
- **Behavior:** Performs physical recursive file copy; does not create symlinks; ensures zero drift.

#### 2. Behavioral Invariants
1. **Compilation Invariant:** Every skill emitted by `build.py` into `dist/skills/<slug>/` must be completely self-contained. Any file referenced in `references/` within `SKILL.md` must be physically copied into `dist/skills/<slug>/references/`. Missing referenced files cause `build.py` to immediately exit with status code 1.
2. **HITL Preservation Invariant:** Every Layer 1 lifecycle skill emitted to `dist/skills/` must preserve:
   - `agents/openai.yaml` with `policy.allow_implicit_invocation: false`.
   - Frontmatter `disable-model-invocation: true` (for Claude Code, Cursor, OpenClaw, Copilot).
   - Frontmatter `triggers: ["user"]` (for Devin).
   - Frontmatter description framing enforcing HITL boundaries (for Antigravity).
3. **Isolation Invariant:** No build or distribution step may create or populate a root `skills/` directory. All build outputs reside strictly in `dist/skills/` to prevent OpenClaw dogfooding collisions.
4. **Scaffolding Separation Invariant:** Skill distribution tools (Track A/B/C/D) only write skill folders into agent locations. They do not write or modify `.memory/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or `.agents/rules/`. Workspace initialization is executed exclusively by `/stratosphere-setup`.
5. **Zero-Session-Overhead Invariant:** `0a-start-session` performs zero suite integrity loops, network lookups, or file tree validations. Suite validation is strictly bound to `stratosphere-setup` and `stratosphere-update`.

#### 3. Input Edge-State Matrix

| Input / Condition | Operation | Expected System Output / State |
| :--- | :--- | :--- |
| `npx skills add PatN-git/Stratosphere-OS/dist/skills -a cursor --copy -y` | Track A install | All 26 skills copied into `.cursor/skills/` (or `.agents/skills/`) with sidecars intact; exit code 0. |
| `npx skills add PatN-git/Stratosphere-OS` (omitted subpath) | Track A install | Aborts with `"No skills found"` due to `SKIP_DIRS` ignoring `dist/`. User is guided by documentation to append `/dist/skills`. |
| `cp -r dist/skills/* .agents/skills/` | Track B manual copy | 26 skill directories copied; all agents reading `.agents/skills/` discover them immediately without running Node.js. |
| `/plugin marketplace add PatN-git/Stratosphere-OS` | Track C install | Claude Code loads plugin; registers all 26 skills; respects `disable-model-invocation: true`. |
| Running `/stratosphere-setup` with 15/22 core skills present | Integrity check | Halts setup with explicit error listing 7 missing lifecycle skills; outputs remediation command. |
| Running `/stratosphere-setup` with 22/22 core skills present | Integrity check | Passes validation immediately; proceeds to scaffold `.memory/`, `AGENTS.md`, and project rules. |
| Running `/0a-start-session` without `.memory/` | Session start | Detects missing `.memory/` directory; emits 1-line guidance: `"Repository uninitialized. Please run /stratosphere-setup first."` |
| Upgrading project via `/stratosphere-update` | Skill refresh | Replaces installed skills with latest `dist/skills/`; cleans legacy `dist/claude-code` or `commands/` paths; logs migration summary. |
