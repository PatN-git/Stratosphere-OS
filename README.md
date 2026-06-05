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
  | 1 | `/1a_discover-idea` | `1a_discover-idea.md` | Frame a fuzzy idea | `GLOSSARY`, `BACKLOG_MAP` | discovery brief, `[[G-xxx]]` |
  | 2 | `/2a_write-prd` | `2a_write-prd.md` | Turn a brief into a PRD | brief, memory | PRD doc + parent issue |
  | 3 | `/3a_create-issue` | `3a_create-issue.md` | Slice a PRD into work | PRD | vertical-slice issues |
  | 3 | `/3b_sprint-planning` | `3b_sprint-planning.md` | Sequence a sprint | `BACKLOG_MAP` | sprint plan |
  | 3 | `/3c_implement-issue` | `3c_implement-issue.md` | Build a slice (TDD) | issue, `ARCHITECTURE` | code + tests |
  | 4 | `/4a_audit-test-gaps` | `4a_audit-test-gaps.md` | Verify AC↔test coverage | issue, tests | gap report |
  | 4 | `/4b_audit-architecture-drift` | `4b_audit-architecture-drift.md` | Find structural drift | target dir, `.memory/*` | `.tmp/refactor-proposal.md` |

- **Installer** — `/instantiate-stratosphere` scaffolds the project: memory layer, workspace rules, constitution, optional personas, and an interactive skill-pack setup. Safe to re-run (diff-aware) as an upgrade path.
- **First-party skill** — `micro-tdd` (autonomous, token-efficient TDD).
- **On-demand skills** — database, React/web, React Native, and design packs are fetched only when a project needs them (see `src/external-skills.json`).

> **Design tooling:** Google Stitch is the default design tool — brand tokens live in `.memory/DESIGN.md` (Google Labs `DESIGN.md` spec) and structural rules in `.memory/DESIGN_RULES.md`. The optional `design` skill pack (`impeccable`) is polish on top, not a replacement.

---

## Install

### Claude Code
```
/plugin marketplace add PatN-git/Stratosphere-OS
/plugin install stratosphere-os
/instantiate-stratosphere
```
Update: `/plugin marketplace update` then reinstall.

### Google Antigravity
Install the plugin from this GitHub repo (it stages under `~/.gemini/antigravity-cli/plugins/`), or drop `dist/antigravity/` into your workspace's `.agents/plugins/`. Then in the agent:
```
/instantiate-stratosphere
```
Update: re-pull the plugin.

> **Install ≠ scaffold.** Installing the plugin makes the commands and skills available. Running `/instantiate-stratosphere` is what writes the constitution and memory layer into *your* project.

---

## How it's built

This repo is a **single source of truth** that compiles into both plugin formats.

```
src/                         ← edit here (single source of truth)
├─ constitution/             AGENT.md, CLAUDE.md, GEMINI.md
├─ skills/                   first-party skills (micro-tdd)
├─ workflows/                lifecycle commands (0a–4b)
├─ commands/                 instantiate + sync-skills
├─ rules/                    output-mode, memory-protocol, persona-protocol
├─ memory-templates/         .memory/* scaffolding (STATUS, ARCHITECTURE, DESIGN, …)
├─ personas/                 persona drafts + designer + _persona-template
├─ references/  scripts/     PRD/discovery templates; validate_memory.py
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

Skills are byte-identical across platforms; only the manifest and the
`commands/` vs `workflows/` directory naming differ. Project-instance files
(constitution, memory templates, rules, personas) ship under `assets/templates/`
and are written into a project by the installer — not on install.

---

## Third-party skills & attribution

Domain skills are **not bundled**; they are fetched on demand from their upstream repositories via `sync-skills`. Sources are tracked in `src/external-skills.json`. Each retains its own license and attribution from upstream (Anthropic, Supabase, Vercel Labs, and others).
