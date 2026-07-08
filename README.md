# Stratosphere-OS
![StratosphereOS Architecture Banner](docs/assets/hero-banner.png)

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/PatN-git/Stratosphere-OS)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/PatN-git/Stratosphere-OS)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2.svg)](https://github.com/PatN-git/Stratosphere-OS)
[![Google Antigravity](https://img.shields.io/badge/Google%20Antigravity-plugin-00CED1.svg)](https://github.com/PatN-git/Stratosphere-OS)

> An agentic orchestration framework that equips AI coding assistants (Claude Code, Google Antigravity) with structured memory, automated TDD guardrails, and deterministic project lifecycles. Developed out of frustration with unstructured AI workflows and inspired by popular skill builders.

---

## Table of Contents
- [Why StratosphereOS?](#why-stratosphereos)
- [Workspace Directory Structure](#workspace-directory-structure)
- [Lifecycle Commands Matrix](#lifecycle-commands-matrix)
- [Getting Started (Installation)](#getting-started-installation)
- [Architecture & Governance](#architecture--governance)

---

## Why StratosphereOS?

### Beyond Unstructured Code Generation
In modern AI software development, ad-hoc chat prompting quickly leads to architectural drift, subtle bugs, and unmaintainable technical debt. StratosphereOS addresses this by enforcing **Human-in-the-Loop (HITL) architecture governance**. 

Developers act as **Loop Engineers**—interviewing the agent, stress-testing specifications, and establishing clear UI and logic contracts before any implementation begins. Once the human explicitly approves the requirements, small vertical slices are delegated to autonomous test-driven loops (`micro-tdd`) that execute independently until all compiler and test suite checks pass.

StratosphereOS structures your workspace into three cooperating layers:
1. **Layer 1: Workflows (Human Driven)** — Interactive lifecycle stages (Discover, Design, Slice) ensuring alignment before code generation.
2. **Layer 2: Orchestration Brain** — The agent router governing tool execution and strict precedence rules.
3. **Layer 3: Autonomous Execution** — Self-correcting inner loops (like test suites and linters) running deterministically against local code.

---

## Workspace Directory Structure

When initialized via `/stratosphere-setup`, StratosphereOS scaffolds durable project state into your repository:

```text
├── AGENT.md / CLAUDE.md / GEMINI.md  ← Core constitution and layer rules
├── .agents/                          ← Orchestration engine (rules, workflows, skills)
├── .memory/                          ← Authoritative project memory
│   ├── STATUS.md                     ← Active session health and build status
│   ├── BACKLOG_MAP.md                ← Feature slices and issue tracking
│   ├── LEARNINGS.md                  ← Accumulated architectural traps and fixes
│   ├── GLOSSARY.md                   ← Project domain vocabulary
│   ├── ARCHITECTURE.md               ← System structural invariants
│   ├── DATABASE_SCHEMA.md            ← Living database definitions
│   └── DESIGN.md / DESIGN_RULES.md   ← UI design tokens and structural contracts
└── docs/                             ← Product Requirement Documents (PRDs) and research
```

---

## Lifecycle Commands Matrix

StratosphereOS provides structured slash commands spanning the entire development lifecycle.

| Stage | Command | Purpose & Rationale | Reads | Produces |
|:---|:---|:---|:---|:---|
| **0. Session Start** | `/0a_start-session` | Eliminates cold-start costs by restoring branch state and loading durable memory. | `STATUS`, `.memory/*` | Synced session context |
| **1. Discovery** | `/1a_research`<br/>`/1b_concept-framing` | Investigates domain context and deconstructs fuzzy ideas into structured briefs. | `.memory/*` | Discovery brief, glossary terms |
| **2. Design** | `/2a_write-prd`<br/>`/2b_interface-design` | Derives formal PRDs and UI contracts to prevent agent hallucinations and UI drift. | Discovery brief | PRD doc, UI/logic contracts |
| **3. Planning** | `/3a_version-planning`<br/>`/3b_create-issue`<br/>`/3c_sprint-planning` | Deconstructs PRDs into traceable vertical-slice issues sized for single context windows. | PRD, `BACKLOG_MAP` | Release roadmap, sprint plan, vertical issues |
| **3d. Execution** | `/3d_implement-issue` | Runs autonomous `micro-tdd`: writes failing test, executes suite, writes code, refactors. | Issue, `ARCHITECTURE` | Passing unit tests, committed code |
| **3z. Orchestration** | `/3z_afk-loop` | Runs the autonomous end-to-end loop for `type:AFK` slices (single slice or batch), chaining session start, implementation, verification, PR shipping, and stop session. | `BACKLOG_MAP`, `STATUS` | Automated PRs and synced status |
| **4. Ship** | `/4a_verify-and-ship`<br/>`/4b_audit-architecture-drift` | Audits acceptance criteria against automated test coverage and audits structural drift. | Issue, tests, `.memory/*` | Quality gap report, traceable PR |
| **0. Session Stop** | `/0b_stop-session`<br/>`/0c_handoff` | Lints project memory, updates status ground truth, and prepares clean session handoffs. | Session work | Updated `STATUS.md`, clean handoff |
| **Maintenance** | `/stratosphere-update` | Upgrades framework templates, rules, and workflows in-place without overwriting user memory or configuration. | `.memory/*`, lockfile | Updated framework files |

---

## Getting Started (Installation)

### 1. Direct Plugin Installation (Recommended)

**Claude Code:**
```text
/plugin marketplace add PatN-git/Stratosphere-OS
/plugin install stratosphere-os@stratosphere-os
```

**Google Antigravity:**
```bash
git clone https://github.com/PatN-git/Stratosphere-OS.git
bash scripts/install-antigravity.sh --global
# Windows: powershell -ExecutionPolicy Bypass -File scripts/install-antigravity.ps1 --global
```

> [!TIP]
> **Zero-Click AI Installation Shortcut**
> Want your agent to handle the installation, dependency checks, and GitHub integration automatically? Simply paste this prompt into your chat:
> `Install StratosphereOS from this repository: https://github.com/PatN-git/Stratosphere-OS. Check dependencies (Python, Git, GitHub CLI gh), verify GitHub auth/connection, and assist with setup if needed.`

### 2. Instantiate Project Memory
After installing the plugin, restart your app or agent session, navigate to your target project repository, and run:
```text
/stratosphere-setup
```
This interactive command bootstraps the initial `.memory/` state layer, constitution files, and domain skills for new projects.

### 3. Upgrading Framework Files (Updating)
To upgrade an already-instantiated project to later plugin versions, run:
```text
/stratosphere-update
```
Your `.memory/` data and constitution are never overwritten; framework-owned blocks are updated in place, and you confirm any conflicts.

---

## Architecture & Governance

### Open Knowledge Format (OKF) Conformance
StratosphereOS conforms to the [Open Knowledge Format (OKF) v0.1 Specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf). The `.memory/` and `docs/` directories form a structured knowledge bundle. An interactive HTML graph visualizer can be generated anytime via `python .agents/scripts/okf_view.py`.

### UI Stack & Design Tooling
By default, UI projects assume React + Tailwind CSS + shadcn/ui. Non-UI projects rely on clean interface contracts defined during `/2b_interface-design`. Google Stitch design integration is supported automatically when enabled in workspace settings.

---

### Maintainer Notes: Single Source Build Pipeline
This repository is the single source of truth (`src/`) that compiles into both Claude Code and Google Antigravity plugin distributions (`dist/`).

```bash
python build/build.py
```
