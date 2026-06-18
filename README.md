# 🌌 Stratosphere-OS

A weightless, 3-layer agentic operating system for building full-stack apps — packaged as an installable plugin for **Claude Code** and **Google Antigravity**. Install it once, run one command, and any project gets the StratosphereOS constitution, a durable memory layer, lifecycle workflows, and the right skill packs.

> One source of truth → two plugins. Update the source, rebuild, and every project that updates the plugin gets your learnings.

---

## 🔁 The Philosophy: Don't Prompt, Build Loops

In modern AI engineering, manual chat-based prompting is being replaced by autonomous, self-correcting execution loops. Rather than having a human constantly prompt, evaluate, copy-paste errors, and re-prompt the AI, developers act as **Loop Engineers**—constructing structured harnesses where the AI is given clear objectives, verification tools (compilers, linters, test suites), and a feedback loop.

Stratosphere-OS is a state-aware agentic environment built specifically around this paradigm. It structures development into three distinct layers to manage the loop lifecycle:

```mermaid
graph TD
    %% Layer 1
    subgraph L1["Layer 1: Workflows (HITL Outer Loop)"]
        direction TB
        A["User /1b, /2a, /3a Commands"] --> B["Design & Slicing Checkpoints"]
        B -->|Human Approval| C["Vertical Slice Issue"]
    end

    %% Layer 2
    subgraph L2["Layer 2: Orchestration (Routing & Guardrails)"]
        direction TB
        C --> D["Orchestration Brain"]
        D -->|Checks Precedence & Pre-requisites| E{"Active Rules?"}
        E -->|No| F["Standard Routine"]
        E -->|Yes| G["Selects Skill (e.g. Micro-TDD)"]
    end

    %% Layer 3
    subgraph L3["Layer 3: Execution (Autonomous Inner Loop)"]
        direction TB
        G --> H["Isolate & Specify (Red Test)"]
        H --> I["Run Test Suite"]
        I -->|Failure Log| J["Implement Code (Green)"]
        J --> I
        I -->|Success (Green)| K["Clean & Refactor"]
        K -->|/4a Verify & Ship| L["Open Pull Request"]
    end

    L3 -->|Stuck Protocol Trigger| L1
```

- **Layer 1: Workflows (HITL Outer Loop)**: Standardizes the development lifecycle (Discover, Design, Implement, Verify). Crucially, these enforce Human-in-the-Loop checkpoints to prevent runaway agent loops or architectural misalignment.
- **Layer 2: Orchestration (Routing & Guardrails)**: The agent core that routes inputs, checks rules, and governs actions based on strict precedence (Core Rules → User Requests → Workflows → Skills). It acts as the bridge connecting Layer 1 and Layer 3.
- **Layer 3: Execution (Autonomous Inner Loop)**: Fast-track playbooks (like the first-party `micro-tdd` skill) that run completely autonomously. The agent writes tests, runs the suite, analyzes errors, and iterates automatically until all tests pass, or hits safety conditions (the "Stuck Protocol") to prompt the user.

---

## What you get

- **Constitution** (`AGENT.md` / `CLAUDE.md` / `GEMINI.md`) — the "StratosphereOS Architect" 3-layer rules: Workflows → Orchestration → Execution, with strict precedence and token-efficient, deterministic behavior.

- **🚀 The Agentic Workflow** - slash commands for the whole dev lifecycle:
  - Stage 0: Workflows to manage the environment and workflow.
  - Stage 1: Workflows to deconstruct the problem and customer needs.
  - Stage 2: Workflows for automated architectural blueprints and logic mapping.
  - Stage 3: Workflows for full-stack implementation via "vibe coding"
  - Stage 4: Workflows for continuous feedback loops to ensure production-ready quality.


  | Stage | Command | File | When to use | Reads | Produces |
  |---|---|---|---|---|---|
  | 0 | `/0a_start-session` | `0a_start-session.md` | Begin any session | `STATUS`, relevant memory | synced context |
  | 0 | `/0b_stop-session` | `0b_stop-session.md` | End any session | session work | updated memory, lint, handoff |
  | 0 | `/0c_handoff` | `0c_handoff.md` | Hand to a fresh session | conversation | `.tmp/handoff_*` |
  | 0 | `/0d_nightly-consolidation` | `0d_nightly-consolidation.md` | End-of-day maintenance (AFK) | sessions, `.memory/*` | consolidation plan |
  | 1 | `/1a_research` | `1a_research.md` | Research domain (problem vs. competitive, quick vs. deep) | memory | `docs/research/` |
  | 1 | `/1b_concept-framing` | `1b_concept-framing.md` | Frame a fuzzy idea | `GLOSSARY`, `BACKLOG_MAP` | discovery brief, `[[G-xxx]]` |
  | 2 | `/2a_write-prd` | `2a_write-prd.md` | Turn a brief into a PRD | brief, memory | PRD doc + parent issue |
  | 2 | `/2b_interface-design` | `2b_interface-design.md` | Design interface (UI or non-UI contract) | PRD | design blueprint / contract |
  | 3 | `/3a_version-planning` | `3a_version-planning.md` | Map features to releases (roadmap) | `BACKLOG_MAP`, PRDs | `docs/ROADMAP.md`, release milestones |
  | 3 | `/3b_create-issue` | `3b_create-issue.md` | Slice a PRD into work | PRD | vertical-slice issues |
  | 3 | `/3c_sprint-planning` | `3c_sprint-planning.md` | Sequence a sprint | `BACKLOG_MAP` | sprint plan |
  | 3 | `/3d_implement-issue` | `3d_implement-issue.md` | Build a slice (TDD) | issue, `ARCHITECTURE`, UX | code + tests |
  | 4 | `/4a_verify-and-ship` | `4a_verify-and-ship.md` | Verify a slice (AC↔test coverage), then open a traceable PR | issue, tests, design doc | gap report + PR |
  | 4 | `/4b_audit-architecture-drift` | `4b_audit-architecture-drift.md` | Find structural drift | target dir, `.memory/*` | `.tmp/refactor-proposal.md` |

- **Installer** — `/stratosphere-setup` scaffolds the project: memory layer, workspace rules, constitution, and an interactive skill-pack setup. Safe to re-run (diff-aware) as an upgrade path.
- **First-party skills** — `micro-tdd` (autonomous, token-efficient TDD) and `plan-html` (interactive HTML plans/matrices/micro-apps).
- **On-demand skills** — database, React/web, React Native, and design packs are fetched only when a project needs them (see `src/external-skills.json`).

> **Design tooling:** Google Stitch is the default design tool **when enabled** (`Stitch Status: yes`); no-Stitch projects use reference-driven native design (Path B in `2b_interface-design`). Brand tokens live in `.memory/DESIGN.md` (Google Labs `DESIGN.md` spec) and structural rules in `.memory/DESIGN_RULES.md`. The optional `design` skill pack (`impeccable`) is polish on top, not a replacement.

## Assumptions

StratosphereOS assumes a React + Tailwind + shadcn/ui UI stack by default. Non-UI features are handled by the Path C interface contract in `2b_interface-design`. A project can adopt another stack by superseding DR-004/DR-005 (see `memory-protocol.md` §3) with explicit user confirmation.

---

## Open Knowledge Format (OKF) Conformance

StratosphereOS natively conforms to the [Open Knowledge Format (OKF) v0.1 Specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf).

- **Bundle Scope:** The `.memory/` directory (registries and rules) and the `docs/` directory (PRDs, discovery briefs, designs, and research) form a conformant OKF Knowledge Bundle.
- **Concept Typing:** Every markdown file within the bundle scope (excluding reserved index files and foreign knowledge sources) contains structured YAML frontmatter mapping to the project's OKF type registry.
- **OKF Dashboard:** An interactive visualizer is included in the project. It can be regenerated at session stop, or manually using the command:
  ```bash
  python .agents/scripts/okf_view.py
  ```
  This creates an interactive HTML graph at `docs/okf-view.html` mapping the bundle's concept relationships. Note that while the file is generated locally, viewing it requires an active internet connection to load graph-rendering libraries (Cytoscape and Marked) from a CDN.

---

## Install

New to agentic coding? The easiest way to install StratosphereOS is to **let your AI agent do it**. Open Claude Code or Google Antigravity and paste this one prompt into the chat:

> Install StratosphereOS from this repository: https://github.com/PatN-git/Stratosphere-OS

The agent follows the instructions below and does the rest. You'll be asked a couple of quick questions (install scope, and whether to install any missing dependency). Prefer to do it by hand? See [Manual install](#manual-install).

> ### 🤖 Attention AI Agents — Zero-Click Install
> *If your user asked you to install StratosphereOS from the link above, follow these steps. Do not improvise file copies — use the deterministic paths below.*
>
> **1. Identify your environment** (Claude Code vs Google Antigravity) and the operating system.
>
> **2. Check dependencies.** StratosphereOS needs **Python** (to run the project scaffolder and the skill-sync script). The Antigravity path additionally needs **Git** (to clone). Run `python --version` (and `git --version` for Antigravity). If either is missing, use your native question tool — `AskUserQuestion` on Claude Code, `ask_question` on Antigravity — to ask the user whether to install it and explain why. Only on confirmation, install via the system package manager (`winget` on Windows, `brew` on macOS, `apt`/`dnf` on Linux). **Never install system software silently.**
>
> **3. Ask the install scope** with your native question tool: *"Install StratosphereOS for all your projects (global, recommended) or just this one (local)?"* This is the **single** scope decision — scaffolding always targets the current project, and skill scope is derived from this answer later, so you won't ask again.
>
> **4a. Claude Code:**
> - **Global** → plugin marketplace (no clone, no Git):
>   ```
>   /plugin marketplace add PatN-git/Stratosphere-OS
>   /plugin install stratosphere-os@stratosphere-os
>   ```
>   *Use the `owner/repo` shorthand exactly as shown — a raw URL to `marketplace.json` will not resolve relative plugin paths.*
> - **Local** (project-only) → clone and run the script with `--local`, then delete the clone:
>   ```bash
>   git clone https://github.com/PatN-git/Stratosphere-OS.git .tmp/stratosphere-os
>   bash .tmp/stratosphere-os/scripts/install-claude-code.sh --local --target <project-root>
>   # Windows: powershell -ExecutionPolicy Bypass -File .tmp/stratosphere-os/scripts/install-claude-code.ps1 --local --target <project-root>
>   
>   # Cleanup — remove the temp clone (files are now installed, clone is no longer needed)
>   rm -rf .tmp/stratosphere-os
>   # Windows: Remove-Item -Recurse -Force .tmp/stratosphere-os
>   ```
>
> **4b. Google Antigravity — clone and run the deterministic installer** (pass `--global` or `--local` per step 3), then delete the clone:
> ```bash
> git clone https://github.com/PatN-git/Stratosphere-OS.git .tmp/stratosphere-os
> # Global:
> bash .tmp/stratosphere-os/scripts/install-antigravity.sh --global
> # Windows: powershell -ExecutionPolicy Bypass -File .tmp/stratosphere-os/scripts/install-antigravity.ps1 --global
> 
> # Local:
> bash .tmp/stratosphere-os/scripts/install-antigravity.sh --local --target <project-root>
> # Windows: powershell -ExecutionPolicy Bypass -File .tmp/stratosphere-os/scripts/install-antigravity.ps1 --local --target <project-root>
> 
> # Cleanup — remove the temp clone (files are now installed, clone is no longer needed)
> rm -rf .tmp/stratosphere-os
> # Windows: Remove-Item -Recurse -Force .tmp/stratosphere-os
> ```
> (`--global` → `~/.gemini/config/plugins/`, `--local --target <project-root>` → `<project-root>/.agents/plugins/`.)
>
> **5. Tell the user to reload.** They must **restart the app** (or start a new agent session for Antigravity) so the new commands load. *Do not tell them to close the terminal — that is not how plugins reload.*
>
> **6. Point them to scaffolding.** Have them open *their own* project and run `/stratosphere-setup`, which scaffolds the project and (in its skill-setup step) installs domain skills at the scope chosen in step 3.

### Manual install

**Prerequisites:** **Python** (scaffolder + skill sync) and — for the clone-based paths — **Git**.

**Claude Code (recommended — plugin marketplace):**
```
/plugin marketplace add PatN-git/Stratosphere-OS
/plugin install stratosphere-os@stratosphere-os
```
*Marketplace installs at user (global) scope. For a project-local install, use the script below with `--local`.*

*Fallback (clone + script):*
```bash
git clone https://github.com/PatN-git/Stratosphere-OS.git
scripts/install-claude-code.sh                                          # Unix/Bash
powershell -ExecutionPolicy Bypass -File scripts/install-claude-code.ps1   # Windows
```

**Google Antigravity (clone + script):**
```bash
git clone https://github.com/PatN-git/Stratosphere-OS.git
# choose --global (all projects) or --local (this project only):
scripts/install-antigravity.sh --global                                  # Unix/Bash
powershell -ExecutionPolicy Bypass -File scripts/install-antigravity.ps1 --global   # Windows
```
- **Global** → `~/.gemini/config/plugins/stratosphere-os/`
- **Local** → `.agents/plugins/stratosphere-os/`

> [!IMPORTANT]
> **Reload after installing.** Restart the app / start a new agent session so the commands (including `/stratosphere-setup`) are discovered.

> **Install ≠ scaffold.** Installing the plugin makes the commands and skills available. Running `/stratosphere-setup` is what writes the constitution and memory layer into *your* project.

**Update:** re-pull the repository, run `python build/build.py`, then re-run the installer — on Claude Code, re-run `/plugin marketplace add` (or `/plugin update`). Re-running the Antigravity installer refreshes bundled content and removes stale files, but **preserves any external skills you fetched with `/sync-skills`**; run `/sync-skills` again to pull newly available ones.

> [!IMPORTANT]
> **Existing Projects gitignore Update:**
> The `/stratosphere-setup` scaffold script never overwrites or edits an existing `.gitignore` file. If you are upgrading/running in an existing project, you must manually add `*.work.md` to your `.gitignore` to ensure temporary deep-research loop workfiles are ignored by Git.

---

## How it's built

This repo is a **single source of truth** that compiles into both plugin formats.

```
src/                         ← edit here (single source of truth)
├─ constitution/             AGENT.md, CLAUDE.md, GEMINI.md
├─ skills/                   first-party skills (micro-tdd, plan-html)
├─ workflows/                lifecycle commands (0a–4b)
├─ commands/                 instantiate + sync-skills
├─ rules/                    output-mode, memory-protocol
├─ memory-templates/         .memory/* scaffolding (STATUS, ARCHITECTURE, DESIGN, …)
├─ references/               PRD/discovery/competitive/problem-space templates
├─ scripts/                  validate_memory.py
└─ external-skills.json      on-demand skill registry

build/build.py               ← single build step (build/validate.py checks output)
dist/                        ← generated, committed (installable plugins)
├─ claude-code/              .claude-plugin/plugin.json + commands/ + skills/ + assets/
└─ antigravity/              plugin.json + workflows/ + skills/ + assets/
.claude-plugin/marketplace.json   ← lets `/plugin marketplace add` work from GitHub
```

Rebuild both plugins:
```
python build/build.py
```

**Structural vocabulary:** `Stage` = lifecycle level (0–4). `Phase` = a division within a lifecycle workflow (`## Phase N`, 1-indexed; Phase 0 = optional prelude). `Step` = an atomic action (ordered-list item within a phase). `Procedure` = a flat workflow with no phases (0a/0b). `Checkpoint` = a unit of the one-time `/stratosphere-setup` installer. Workflows are invoked as `/Na_name` and referenced conceptually as bare `Na`.

Skills are byte-identical across platforms; only the manifest and the
`commands/` vs `workflows/` directory naming differ. Project-instance files
(constitution, memory templates, rules) ship under `assets/templates/`
and are written into a project by the installer — not on install.

---

## Third-party skills & attribution

Domain skills are **not bundled**; they are fetched on demand from their upstream repositories via `sync-skills`. Sources are tracked in `src/external-skills.json`. Each retains its own license and attribution from upstream (Anthropic, Supabase, Vercel Labs, and others).

### OKF Bundle Viewer
StratosphereOS includes a vendored copy of the Open Knowledge Format (OKF) reference HTML visualizer.
- **Source:** [Google Cloud Platform Knowledge Catalog - OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)
- **License:** Apache License 2.0 (see `src/scripts/okf_viewer/LICENSE` for full details).
