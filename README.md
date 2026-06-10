# 🌌 Stratosphere-OS

A weightless, 3-layer agentic operating system for building full-stack apps — packaged as an installable plugin for **Claude Code** and **Google Antigravity**. Install it once, run one command, and any project gets the StratosphereOS constitution, a durable memory layer, lifecycle workflows, and the right skill packs.

> One source of truth → two plugins. Update the source, rebuild, and every project that updates the plugin gets your learnings.

---

## What you get

- **Constitution** (`AGENT.md` / `CLAUDE.md` / `GEMINI.md`) — the "Lean Architect" 3-layer rules: Workflows → Orchestration → Execution, with strict precedence and token-efficient, deterministic behavior.

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
  | 3 | `/3a_create-issue` | `3a_create-issue.md` | Slice a PRD into work | PRD | vertical-slice issues |
  | 3 | `/3b_sprint-planning` | `3b_sprint-planning.md` | Sequence a sprint | `BACKLOG_MAP` | sprint plan |
  | 3 | `/3c_implement-issue` | `3c_implement-issue.md` | Build a slice (TDD) | issue, `ARCHITECTURE`, UX | code + tests |
  | 4 | `/4a_verify-and-ship` | `4a_verify-and-ship.md` | Verify a slice (AC↔test coverage), then open a traceable PR | issue, tests, design doc | gap report + PR |
  | 4 | `/4b_audit-architecture-drift` | `4b_audit-architecture-drift.md` | Find structural drift | target dir, `.memory/*` | `.tmp/refactor-proposal.md` |

- **Installer** — `/stratosphere-setup` scaffolds the project: memory layer, workspace rules, constitution, and an interactive skill-pack setup. Safe to re-run (diff-aware) as an upgrade path.
- **First-party skills** — `micro-tdd` (autonomous, token-efficient TDD) and `plan-html` (interactive HTML plans/matrices/micro-apps).
- **On-demand skills** — database, React/web, React Native, and design packs are fetched only when a project needs them (see `src/external-skills.json`).

> **Design tooling:** Google Stitch is the default design tool **when enabled** (`Stitch Status: yes`); no-Stitch projects use reference-driven native design (Path B in `2b_interface-design`). Brand tokens live in `.memory/DESIGN.md` (Google Labs `DESIGN.md` spec) and structural rules in `.memory/DESIGN_RULES.md`. The optional `design` skill pack (`impeccable`) is polish on top, not a replacement.

## Assumptions

StratosphereOS assumes a React + Tailwind + shadcn/ui UI stack by default. Non-UI features are handled by the Path C interface contract in `2b_interface-design`. A project can adopt another stack by superseding DR-004/DR-005 (see `memory-protocol.md` §3) with explicit user confirmation.

---

## Install

### Claude Code
```bash
git clone https://github.com/PatN-git/Stratosphere-OS.git
# then run the install script for your shell:

# On Unix/Bash:
scripts/install-claude-code.sh

# On Windows/PowerShell:
powershell -ExecutionPolicy Bypass -File scripts/install-claude-code.ps1
```
Update: Re-pull the repository, run the build script (`python build/build.py`), and run the installer script again.

> [!IMPORTANT]
> **Restart Required:** After running the install script, you MUST restart Claude Code for the commands (including `/stratosphere-setup`) to be discovered.



### Google Antigravity
Choose whether you want to install/stage the plugin **globally** (for use across multiple projects) or **locally** (only for the current project):
- **Globally**: Copy/stage `dist/antigravity/` under `~/.gemini/config/plugins/stratosphere-os/`.
- **Locally**: Copy/stage `dist/antigravity/` under `.agents/plugins/stratosphere-os/`.

Then in the agent, run the setup skill:
```
/stratosphere-setup
```
Update: Re-pull the repository, run the build script, and copy/stage the updated `dist/antigravity/` folder to your chosen scope directory.

> **Install ≠ scaffold.** Installing the plugin makes the commands and skills available. Running `/stratosphere-setup` is what writes the constitution and memory layer into *your* project.

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
