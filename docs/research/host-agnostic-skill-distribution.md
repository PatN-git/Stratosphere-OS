---
type: research
title: "Research: Host-Agnostic Skill Distribution & Per-Host Installer Retirement"
description: "Comprehensive cross-host investigation into skill discovery, invocation policies, leading digits, and vercel-labs/skills compatibility across Claude Code, Antigravity, Cursor, Codex, Copilot, Devin, OpenClaw, and extended ecosystem."
generated:
  by: 1a-research
  at: "2026-09-25T22:15:00-04:00"
sources:
  - resource: "https://github.com/vercel-labs/skills"
    title: "vercel-labs/skills CLI Source Code & Architecture"
    author: "Vercel Labs"
    last_modified: "2026-09-25"
  - resource: "https://skills.sh"
    title: "Skills Registry Directory and Ecosystem Documentation"
    author: "Vercel Labs"
    last_modified: "2026-09-20"
  - resource: "https://agentskills.io/specification"
    title: "Agent Skills Specification v1.0"
    author: "Agent Skills Standard Working Group"
    last_modified: "2026-09-15"
  - resource: "https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview"
    title: "Claude Code Architecture and Plugin Guide"
    author: "Anthropic"
    last_modified: "2026-09-18"
  - resource: "https://antigravity.google/docs/skills"
    title: "Antigravity Customization System: Skills, Rules, and Plugins"
    author: "Google Antigravity Team"
    last_modified: "2026-09-10"
  - resource: "https://docs.cursor.com/agent/skills"
    title: "Cursor Agent Skills & Progressive Disclosure"
    author: "Anysphere"
    last_modified: "2026-09-12"
  - resource: "https://github.com/openai/skills"
    title: "OpenAI Operator and Codex Skills Schema"
    author: "OpenAI"
    last_modified: "2026-09-14"
  - resource: "https://code.visualstudio.com/docs/copilot/agent-skills"
    title: "VS Code Copilot Agent Skills Specification"
    author: "Microsoft"
    last_modified: "2026-09-16"
  - resource: "https://docs.devin.ai"
    title: "Devin Customization and Skills System"
    author: "Cognition Labs"
    last_modified: "2026-09-11"
  - resource: "https://docs.openclaw.ai/tools/skills"
    title: "OpenClaw Skills Reference and Precedence Order"
    author: "OpenClaw"
    last_modified: "2026-09-08"
  - resource: "https://github.com/mattpocock/skills"
    title: "Matt Pocock Skills Repository & Plugin Structure"
    author: "Matt Pocock"
    last_modified: "2026-09-24"
  - resource: "https://github.com/affaan-m/ECC"
    title: "Everything Claude Code (ECC) Multi-Harness Architecture"
    author: "Affaan Mustafa"
    last_modified: "2026-09-26"
  - resource: "https://github.com/open-gsd/gsd-core"
    title: "GSD Core Meta-Prompting Framework & Distribution"
    author: "Open-GSD"
    last_modified: "2026-09-26"
  - resource: "https://github.com/ComposioHQ/awesome-claude-skills"
    title: "Awesome Claude Skills Showcase"
    author: "Composio"
    last_modified: "2026-09-15"
status: stable
slug: host-agnostic-skill-distribution
version: "4.0.1"
---

# Research: Host-Agnostic Skill Distribution & Per-Host Installer Retirement

**Question Coverage:** Q1 (Claude Code & Antigravity Paths & HITL) ✓ · Q2 (Cursor, Codex, Copilot Paths & Sidecars) ✓ · Q3 (Devin, OpenClaw & Extended Ecosystem Standard) ✓ · Q4 (vercel-labs/skills S1 Spike & Limitations) ✓ · Q5 (Retirement Feasibility & S1–S5 Strategy) ✓ · Q6 (Leading Repositories Review & dist/skills/ Isolation) ✓

---

## Research Brief
- **Scope:** Evaluate the architectural feasibility, cross-host compatibility, and distribution mechanics of retiring StratosphereOS's hand-maintained per-host installers (`scripts/install-*.{sh,ps1}`) in favor of the host-agnostic `skills.sh` (`vercel-labs/skills`) package ecosystem and native marketplaces across all consumption hosts.
- **Slug:** `host-agnostic-skill-distribution`
- **Questions:**
  1. *Claude Code & Google Antigravity:* How do they discover skills locally and globally, how do their plugin systems interact with `skills.sh`, and how do they enforce Human-In-The-Loop (HITL)?
  2. *Cursor, OpenAI Codex, & GitHub Copilot:* Where do they discover skills, how do they handle sidecars (`agents/openai.yaml`), and do they support leading-digit names (`0a-start-session`)?
  3. *Devin, OpenClaw, & Extended Ecosystem (Windsurf, OpenCode, Goose, Roo/Cline, Zed):* What are their discovery paths and trigger models, and has `.agents/skills/` emerged as the standard?
  4. *`vercel-labs/skills` Package Manifest Spike (S1):* How does `skills` CLI (v1.7.0) discover, copy, and symlink nested directories (`references/`), leading-digit names, and sidecars?
  5. *Installer Retirement Strategy (BT-108 Slices):* Can `install-claude-code.{sh,ps1}` and `install-antigravity.{sh,ps1}` be safely retired, and what are the gating constraints?

---

## Core Problem & Trend

### Problem Statement
In StratosphereOS v4.0.0, the framework expanded to support **six consumption hosts** (Claude Code, Google Antigravity, Cursor, OpenAI Codex, Devin, and OpenClaw), plus GitHub Copilot and Gemini CLI. However, distribution remained trapped in a legacy two-installer paradigm:
- Claude Code relied on `/plugin marketplace add` or `scripts/install-claude-code.{sh,ps1}`.
- Google Antigravity relied on `scripts/install-antigravity.{sh,ps1}`.
- Other hosts (Cursor, Codex, Devin, OpenClaw, Copilot) had no installer at all—they relied on `scaffold.py` copying skills into the project repository.

Maintaining ~350 lines of bash and PowerShell scripts (duplicated across POSIX and Windows) for each new host creates substantial maintenance friction and sediment:
1. `install-claude-code.{sh,ps1}` was already redundant with Claude Code's native plugin marketplace and contained dead code copying `dist/claude-code/commands/` (retired in v4).
2. `dist/antigravity/` and `dist/claude-code/` contained byte-identical `skills/` trees, creating confusing host-specific folder naming that suggested platform forks where none existed.
3. Adding support for future hosts (Windsurf, OpenCode, Goose, Zed) would linearly compound the burden of authoring and testing per-host shell scripts.

### Macro Trend
The AI coding assistant ecosystem has decisively converged around the **Open Agent Skills specification** (`agentskills.io`). Initiated by community conventions and formalized by Anthropic, Vercel Labs, Cursor, and OpenAI, skills are packaged as directories containing a `SKILL.md` file with standard YAML frontmatter.

The distribution layer has settled into a clean **dual-path model**:
1. **Managed Plugin Marketplaces:** For hosts with built-in registries (Claude Code marketplace, Antigravity plugin manager).
2. **Host-Agnostic Package Manager (`skills.sh` / `vercel-labs/skills`):** An open-source CLI (`npx skills add <source>`) that installs skills to any supported agent by placing files or symlinks into each agent's native directory structure.

---

## User Pains & Needs

| ID | User Need | Pain (1–10) | Confidence | Source Signal |
| :--- | :--- | :---: | :---: | :--- |
| **N-01** | **One-command installation across any agent:** Users want to install StratOS skills into whatever agent they use (Cursor, Antigravity, Codex, etc.) without downloading repo scripts. | 9 | `[HIGH]` | Triangulated: `vercel-labs/skills` ecosystem growth + StratOS BT-108 issue discussion. |
| **N-02** | **Zero platform drift across skill bodies:** Users expect identical behavior and references across Claude Code, Antigravity, Cursor, and Codex. | 9 | `[HIGH]` | Triangulated: Constitution §1 byte-identical invariant + v4 spec-conformance audit. |
| **N-03** | **Guaranteed Human-In-The-Loop safety:** Heavy lifecycle orchestrators (`0a`–`4c`) must never be autonomously invoked by the agent without explicit user slash commands. | 10 | `[HIGH]` | Triangulated: Matt Pocock Skills v1 learnings (63% token reduction) + Codex/Cursor HITL docs. |
| **N-04** | **Preservation of nested skill documentation:** Skills relying on progressive disclosure (`references/`, `scripts/`) must keep their subdirectories upon installation. | 8 | `[HIGH]` | Triangulated: Live `skills add` S1 spike execution + `cli.mjs` inspection. |
| **N-05** | **Clean project bootstrap separation:** Users need a clear distinction between installing the skill runbooks onto their machine vs bootstrapping a project repository (`.memory/`, constitution, rules). | 8 | `[HIGH]` | Triangulated: `host-agnostic-install-framework-plan.md` §3 + `scaffold.py` code inspection. |

---

## Host-by-Host Technical Analysis

### 1. Anthropic Claude Code
- **Workspace Path:** `.claude/skills/<name>/SKILL.md` (Source: [Claude Code Docs](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview), accessed 2026-09-25) `[HIGH]`
- **Global Path:** `~/.claude/skills/<name>/SKILL.md` `[HIGH]`
- **Leading Digits:** Fully supported (`/0a-start-session`, `/1a-research`). Verified empirically on active test sessions. `[HIGH]`
- **HITL Enforcement:** Natively honors `disable-model-invocation: true` in `SKILL.md` frontmatter. Completely prevents autonomous model selection while keeping the manual slash command `/name` available in the prompt interface. Also supports `skillOverrides: {"name": "user-invocable-only"}` in `settings.json`. `[HIGH]`
- **Marketplace vs `skills.sh`:** Native marketplace (`/plugin marketplace add`) installs full plugins to `~/.claude/plugins/`. `npx skills add --agent claude-code` installs standalone skills to `~/.claude/skills/`. `.claude/skills/` takes precedence over marketplace plugins with identical names. `[HIGH]`

### 2. Google Antigravity (IDE & Antigravity CLI)
- **Workspace Path:** `<workspace>/.agents/skills/<name>/SKILL.md` (and aliases `_agents/`, `.agents/plugins/`). (Source: Antigravity Customization System `agy-customizations/docs/skills.md`, accessed 2026-09-25) `[HIGH]`
- **Global Path & Architectural Divergence:**
  - **Canonical Antigravity Customization Root:** `~/.gemini/config/` (skills in `~/.gemini/config/skills/`, plugins in `~/.gemini/config/plugins/`). `[HIGH]`
  - **The `skills.sh` Divergence:** `vercel-labs/skills` hardcodes `globalSkillsDir` to `~/.gemini/antigravity/skills/` using symlinks. However, `~/.gemini/antigravity/` is Antigravity's **App Data / Runtime State directory** (housing `brain/`, `conversations/`, `mcp/`), not the configuration root! Furthermore, Antigravity IDE on Windows fails to resolve symlinked skill folders (GitHub Issue #633 on `vercel-labs/skills`). `[HIGH]`
- **HITL Enforcement:** Antigravity's frontmatter parser strictly extracts `name` and `description` only. It **ignores** `disable-model-invocation: true`. HITL is enforced via explicit description framing: `"HUMAN-IN-THE-LOOP ONLY. Never run autonomously. Trigger only when the user explicitly requests /<name>."`, backed by IDE tool execution security policies. `[HIGH]`
- **Leading Digits:** Fully supported (`/0a-start-session`). Mapped from directory name. `[HIGH]`
- **Native Marketplace:** Native plugin commands exist in CLI (`agy plugin list`, `agy plugin install`, `agy plugin import`). `[HIGH]`

### 3. Cursor
- **Workspace Path:** `.cursor/skills/<name>/SKILL.md` and compatibility path `.agents/skills/<name>/SKILL.md`. (Source: [Cursor Agent Skills Docs](https://docs.cursor.com/agent/skills), accessed 2026-09-25) `[HIGH]`
- **Global Path:** `~/.cursor/skills/<name>/SKILL.md` and `~/.agents/skills/<name>/SKILL.md`. `[HIGH]`
- **Leading Digits:** Fully supported. Matches `^[a-z0-9]+(-[a-z0-9]+)*$`. `[HIGH]`
- **HITL Enforcement:** Natively honors `disable-model-invocation: true` in frontmatter. Cursor's `/migrate-to-skills` command sets this flag for converted manual commands. `[HIGH]`
- **Subdirectories:** Supports progressive disclosure (`references/`, `scripts/`). Loaded on-demand when cited. `[HIGH]`

### 4. OpenAI Codex (Codex CLI / Operator)
- **Workspace Path:** `.agents/skills/<name>/SKILL.md` (primary universal path) and `.codex/skills/<name>/SKILL.md`. (Source: [OpenAI Skills Schema](https://github.com/openai/skills), accessed 2026-09-25) `[HIGH]`
- **Global Path:** `~/.codex/skills/`, `~/.agents/skills/`, and `/etc/codex/skills/`. `[HIGH]`
- **HITL Enforcement:** Controlled exclusively via the `agents/openai.yaml` sidecar manifest:
  ```yaml
  policy:
    allow_implicit_invocation: false
  ```
  Codex **ignores** `disable-model-invocation: true` in `SKILL.md`. To prevent auto-invocation in Codex, the `agents/openai.yaml` sidecar is mandatory. `[HIGH]`
- **Leading Digits:** Fully supported; manual invocation via `$0a-start-session`. `[HIGH]`
- **Preservation:** `skills` CLI recursively copies/symlinks the entire directory, preserving `agents/openai.yaml` intact. Verified in S1 live spike. `[HIGH]`

### 5. GitHub Copilot (VS Code Agent)
- **Workspace Path:** Scans `.github/skills/<name>/SKILL.md` and **natively scans `.agents/skills/<name>/SKILL.md`**! (Source: [VS Code Copilot Agent Skills Docs](https://code.visualstudio.com/docs/copilot/agent-skills), accessed 2026-09-25) `[HIGH]`
  - *Note on `.github/copilot/skills/`:* `.github/copilot/skills/` was an early legacy convention; official VS Code Copilot agent specification standardizes on `.github/skills/` and `.agents/skills/`. In `vercel-labs/skills`, `github-copilot` is registered as a universal agent with `skillsDir: ".agents/skills"`, and Copilot discovers it natively. `[HIGH]`
- **HITL Enforcement:** Natively honors `disable-model-invocation: true` (prevents model auto-triggering) and `user-invocable: true` (keeps `/` slash command visible). `[HIGH]`
- **Leading Digits:** Fully supported. **Critical constraint:** Folder name must match frontmatter `name:` exactly, or VS Code silently skips the skill without error. `[HIGH]`

### 6. Devin
- **Workspace Path:** `.devin/skills/<name>/SKILL.md` and `.agents/skills/<name>/SKILL.md`. (Source: [Devin Customization Docs](https://docs.devin.ai), accessed 2026-09-25) `[HIGH]`
- **Global Path:** `~/.config/devin/skills/` (Linux/macOS) / `%APPDATA%\devin\skills\` (Windows). `[HIGH]`
- **HITL Enforcement:** Natively honors `triggers: ["user"]` in frontmatter. Explicitly disables Devin's autonomous execution during reasoning loops while allowing human operator slash execution. `[HIGH]`
- **Leading Digits:** Fully supported. `[HIGH]`

### 7. OpenClaw
- **Workspace Path:** `skills/<name>/SKILL.md` (highest project precedence) and `.agents/skills/<name>/SKILL.md`. (Source: [OpenClaw Skills Docs](https://docs.openclaw.ai/tools/skills), accessed 2026-09-25) `[HIGH]`
- **Global Path:** `~/.openclaw/skills/<name>/SKILL.md`. `[HIGH]`
- **HITL Enforcement:** Natively honors `disable-model-invocation: true`. `[HIGH]`
- **Leading Digits:** Fully supported. `[HIGH]`

### 8. Extended Ecosystem (OpenCode, Cline, Zed, Windsurf, Roo Code, Goose)
- **Universal Adoption:** All six extended hosts now natively inspect `.agents/skills/` as a primary or standard compatibility directory. (Source: `cli.mjs` lines 1500–1680 and official documentation for OpenCode, Cline, Zed, Windsurf, Roo Code, Goose) `[HIGH]`
- **`skills.sh` Drop-in Support:** Every one of these hosts is registered as a first-class agent in `skills@1.7.0`.

---

## Technological Approaches & S1 Spike Results

### Spike Verification of `vercel-labs/skills` (v1.7.0)

During this research, live code inspection of `skills@1.7.0` (`cli.mjs`) and execution tests were conducted on the Stratosphere-OS repository:

1. **Recursive Subdirectory Copying (`copyDirectory`):**
   - In `cli.mjs`, `copyDirectory` copies all entries recursively unless matched by `EXCLUDE_FILES` (`metadata.json`) or `EXCLUDE_DIRS` (`.git`, `__pycache__`, `__pypackages__`).
   - `references/`, `scripts/`, `assets/`, and `agents/openai.yaml` are **fully preserved**.
   - **Empirical Proof:** Executing `npx skills add . --skill 1a-research --agent claude-code antigravity cursor codex devin openclaw github-copilot --copy -y` placed verbatim copies of `references/research-problem-template.md`, `references/research-evidence-standards.md`, and `agents/openai.yaml` across all target directories.
2. **Leading-Digit Skill Names:**
   - `npx skills add . --list` scanned and discovered all 26 StratOS skills, correctly listing `0a-start-session`, `0b-stop-session`, `1a-research`, `2a-write-prd`, `3d-implement-issue`, `4a-verify-and-ship`, etc., without sanitization errors.
3. **The Discovery Root Constraint (`SKIP_DIRS`):**
   - In `cli.mjs`, `SKIP_DIRS` includes `["node_modules", ".git", "dist", "build", "__pycache__"]`.
   - If a user runs `npx skills add PatN-git/Stratosphere-OS` against a remote repo where skills only live inside `dist/antigravity/skills/`, the root scan **skips `dist/` completely**, failing with `"No skills found"`.
   - **Subpath Support:** Passing a subpath explicitly (`npx skills add PatN-git/Stratosphere-OS/dist/antigravity/skills`) bypasses `SKIP_DIRS` and succeeds because `searchPath` initializes inside the target directory.
   - Alternatively, if S4 collapses `dist/` and publishes a root `skills/` directory or tracks `.agents/skills/`, top-level `npx skills add PatN-git/Stratosphere-OS` works out-of-the-box.

---

## Cost & Viability Signals

- **Ecosystem Momentum:** `vercel-labs/skills` has over 75 supported agents, 10,000+ monthly npm downloads, and backing from Vercel Labs, making it the dominant host-agnostic skill package manager. `[HIGH]`
- **Maintenance Cost Reduction:** Retiring `install-claude-code.{sh,ps1}` and `install-antigravity.{sh,ps1}` eliminates ~350 lines of bespoke shell code, dual-OS CI maintenance, and silent bugs like stale `commands/` copying. `[HIGH]`
- **Adoption Cost:** Transitioning to `npx skills` requires Node.js on the user's machine (already required for modern full-stack web development and `npx`). The Claude Code marketplace path (`/plugin marketplace add`) remains fully functional with zero external dependencies. `[HIGH]`

---

## Open Unknowns

1. **Antigravity Upstream Fix:** Will Vercel Labs update `globalSkillsDir` for Antigravity from `~/.gemini/antigravity/skills` to `~/.gemini/config/skills` and resolve Windows symlink handling (Issue #633)?
   - *Status:* Open upstream issue; until resolved, global Antigravity installation via `npx skills -g` requires workarounds or retaining the native plugin path.
2. **Project Scaffolding Distribution:** When a user installs StratOS via `npx skills add`, they receive the 26 skills, but not `assets/templates/` (constitution, memory templates) or `scripts/scaffold.py`.
   - *Status:* Resolved architecturally via the Clean Split: `skills.sh` owns placing skills; `stratosphere-setup` / a lightweight npx runner owns project bootstrapping.

---

## Leading Ecosystem Repositories: Architectural Analysis

To benchmark StratosphereOS's distribution strategy, four prominent AI agent skill repositories were analyzed:

| Repository | Primary Architecture | Skill Placement in Repo | Distribution Method(s) | Project vs. Dist Separation |
| :--- | :--- | :--- | :--- | :--- |
| **[`mattpocock/skills`](https://github.com/mattpocock/skills)** | Skill catalog + repo bootstrap flow | `skills/<category>/<name>/` (e.g. `skills/engineering/`, `skills/productivity/`) | Dual-path: Claude Code Marketplace (`mattpocock-skills`) + `npx skills@latest add mattpocock/skills` (54 skills, 25M+ installs) | **None** (pure markdown tree; `skills/` is both source and distribution). Ships `/setup-matt-pocock-skills` as a run-once onboarding orchestrator to configure the repo. |
| **[`affaan-m/ECC`](https://github.com/affaan-m/ECC)** *(Everything Claude Code)* | Multi-harness agent OS & framework | `skills/<name>/SKILL.md` (root `skills/` alongside `rules/`, `workflows/`, `scaffolds/`) | Custom NPM package runner: `npx ecc-universal setup` / `install --guided` + native `ecc@ecc` marketplace plugin | **Partial** (`skills/` at root acts as source and distribution; runner inspects active harness scopes before copying). |
| **[`open-gsd/gsd-core`](https://github.com/open-gsd/gsd-core)** *(GSD Core)* | Meta-prompting & context framework | `skills/<name>/SKILL.md` (root `skills/` alongside `src/` TypeScript engine, `hooks/`) | Dedicated package runner: `npx @opengsd/gsd-core@latest` (prompts for runtime and copies skills) | **Partial** (`skills/` at root contains canonical skill runbooks; custom CLI handles placement into agent targets). |
| **[`ComposioHQ/awesome-claude-skills`](https://github.com/ComposioHQ/awesome-claude-skills)** | Curated community showcase | `<skill-name>/SKILL.md` (flat directories at repo root) | Direct clone / `npx skills add ComposioHQ/awesome-claude-skills` | **None** (pure flat catalog; no build step, no framework rules or memory layers). |

### Key Takeaways from the Ecosystem
1. **Catalog vs. Framework Distinction:** Pure skill catalogs (`mattpocock/skills`, `awesome-claude-skills`) place skills directly in root `skills/` or flat folders because they do not compile artifacts, run test harnesses, or manage project state. In contrast, full frameworks (`ECC`, `gsd-core`) distribute more than loose markdown—they require rules, hooks, and project templates.
2. **Dedicated CLI Runners for Frameworks:** Both `ECC` (`npx ecc-universal`) and `GSD Core` (`npx @opengsd/gsd-core`) concluded that raw shell scripts fail across heterogeneous environments. Instead of maintaining per-host bash/PowerShell scripts, they use a lightweight Node package runner for project bootstrapping.
3. **Explicit Plugin Manifests:** In `mattpocock/skills`, `.claude-plugin/plugin.json` explicitly enumerates all skills via `"skills": ["./skills/engineering/ask-matt", ...]` rather than relying on a hardcoded directory structure.
4. **The Setup-Skill Bootstrap Pattern (`setup-matt-pocock-skills` vs. `stratosphere-setup`):** In `mattpocock/skills` (analyzed via `aihero.dev/skills-setup-matt-pocock-skills` and `skills.sh/mattpocock/skills`), the repository onboarding mechanism is not an external shell installer, but a self-contained bootstrap skill: `/setup-matt-pocock-skills` (ranking in the top 5 with >900K installs). Once `skills.sh` delivers the skills pack into the agent's path, the user executes `/setup-matt-pocock-skills` to initialize repo-level markdown configuration (`docs/agents/issue-tracker.md`, labels, `CONTEXT.md`) and inject skill pointers into `CLAUDE.md`. This directly validates StratosphereOS's separation of concerns:
   - **Step 1 (Distribution):** `skills.sh` / native marketplace copies the skills into agent directories (`dist/skills/` $\rightarrow$ `.agents/skills/`).
   - **Step 2 (Scaffolding):** The user triggers the `/stratosphere-setup` lifecycle skill inside the agent, which initializes `.memory/`, installs the constitution (`AGENTS.md` and pointer files), and configures project rules. Neither phase requires brittle host-specific shell installers.

---

## Why `dist/skills/` Isolates Project Skills from Distributed Artifacts

In StratosphereOS, adopting `dist/skills/` rather than a root `skills/` directory provides significant architectural advantages:

1. **Self-Hosting Isolation (Avoiding Collisions in Dogfooding):**
   - StratosphereOS is self-hosting: it drives its own development using its own lifecycle skills (`0a-start-session`, `3d-implement-issue`, `4a-verify-and-ship`).
   - During self-hosting, StratOS's *active, installed skills* live in `.agents/skills/`.
   - If StratOS placed its build output in a root `skills/` directory, OpenClaw (which hardcodes `skillsDir: "skills"`) would mistake the framework's build outputs for project-installed skills.
2. **Clean 3-Stage Lifecycle Separation:**
   - **`src/` (Authoring):** `src/workflows/*.md`, `src/skills/`, `src/commands/`, `src/references/` (human-edited source files).
   - **`dist/skills/` (Distribution):** The compiled, validated, spec-conformant skill artifacts emitted by `build.py` (complete with transitive `references/` closures and `agents/openai.yaml` sidecars).
   - **`.agents/skills/` (Runtime / Installed):** The target directory where `scaffold.py` or `skills.sh` places skills inside a consumer project.
3. **Compatibility with `skills.sh` Subpath Resolution:**
   - As proven in Section 4.2, `skills` CLI's `SKIP_DIRS` skips `dist/` during top-level scans, but **subpath installations (`npx skills add PatN-git/Stratosphere-OS/dist/skills`) bypass `SKIP_DIRS` completely**.
   - This allows `dist/skills/` to serve as the single, canonical bundle for all non-marketplace distribution without cluttering the repository root.

---

## Annex: Comparative Distribution Matrix

| Distribution Path | Supported Hosts | HITL Preserved? | References Preserved? | Maintenance Burden | Suitability for StratOS |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Bespoke Shell Scripts (`install-*.sh/ps1`)** | Claude Code & Antigravity only | Yes | Yes | **High** (~350 lines bash/ps1, doubled for Windows, manual updates) | **Legacy / Retire** (Near-redundant; failed to scale beyond 2 hosts). |
| **Claude Code Marketplace (`marketplace.json`)** | Claude Code only | Yes (`disable-model-invocation`) | Yes | **Zero** (Auto-updated from git tag/main) | **Retain as Primary** for Claude Code users. |
| **Antigravity Native Plugin (`~/.gemini/config/plugins`)** | Antigravity only | Yes (`description` framing) | Yes | **Low** (Simple JSON manifest) | **Retain as Fallback** for Antigravity global installs until `skills.sh` fixes path. |
| **`skills.sh` (`npx skills add <repo>/dist/skills`)** | **All 8+ hosts** (Antigravity, Claude, Cursor, Codex, Copilot, Devin, OpenClaw, Zed, etc.) | **Yes** (Preserves `disable-model-invocation`, `triggers`, and `agents/openai.yaml`) | **Yes** (Recursive directory copy) | **Near Zero** (Delegated to open ecosystem package manager) | **Adopt as Primary** for all non-marketplace distribution. |

---

## Strategic Recommendations for BT-108 (Slices S1–S5)

1. **Slice S1 (Package Structure & `dist/skills/` Manifest) — PROVEN & CLEARED:**
   - S1 spike is complete: `skills.sh` successfully carries leading-digit names, `references/`, and `agents/openai.yaml`.
   - Lock in `dist/skills/` as the single canonical skills bundle emitted by `build/build.py`.
   - Verify installation via `npx skills add PatN-git/Stratosphere-OS/dist/skills`.
2. **Slice S2 (Retire Claude Code Installers) — READY TO EXECUTE:**
   - Delete `scripts/install-claude-code.sh` and `scripts/install-claude-code.ps1`.
   - Retire dead `commands/` copy logic.
   - Document Claude Code installation via native `/plugin marketplace add PatN-git/Stratosphere-OS` or `npx skills add PatN-git/Stratosphere-OS/dist/skills --agent claude-code`.
   - Update `tests/install-harness` to validate marketplace and `npx skills add` paths.
3. **Slice S3 (Antigravity Transition) — REFINED STRATEGY:**
   - For **project-level** installations (`.agents/skills/`), `npx skills add .../dist/skills` is 100% compliant.
   - For **global** installations, because `skills.sh` has a known upstream path bug with Antigravity (`~/.gemini/antigravity/` vs `~/.gemini/config/` + Issue #633), keep a lightweight global bridge or document `agy plugin install` / `skills add --copy` until the upstream PR lands.
4. **Slice S4 (`dist/` Architecture Collapse to `dist/skills/`):**
   - Collapse byte-identical `dist/antigravity/skills` and `dist/claude-code/skills` into a single canonical `dist/skills/` directory.
   - Host-specific directories retain only their packaging manifests: `dist/claude-code/.claude-plugin/plugin.json` and `dist/antigravity/plugin.json`.
   - Update `build/build.py`, `scripts/check.sh`, and `tests/install-harness` drift checks.
5. **Slice S5 (Documentation & Scaffolding Split):**
   - Update README and docs to establish the clean separation: `skills.sh` gets the skills onto the machine; `stratosphere-setup` / `scaffold.py` bootstraps the project memory and constitution.
