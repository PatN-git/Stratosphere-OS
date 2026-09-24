# Stratosphere-OS
![StratosphereOS Architecture Banner](docs/assets/hero-banner.png)

[![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)](https://github.com/PatN-git/Stratosphere-OS)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/PatN-git/Stratosphere-OS)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2.svg)](https://github.com/PatN-git/Stratosphere-OS)
[![Google Antigravity](https://img.shields.io/badge/Google%20Antigravity-plugin-00CED1.svg)](https://github.com/PatN-git/Stratosphere-OS)

> An agentic orchestration framework that equips AI coding assistants (Claude Code, Google Antigravity) with structured memory, automated TDD guardrails, and deterministic project lifecycles. Developed out of frustration with unstructured AI workflows and inspired by popular skill builders.

---

## Table of Contents
- [Why StratosphereOS?](#why-stratosphereos)
- [Workspace Directory Structure](#workspace-directory-structure)
- [Lifecycle Skills Matrix](#lifecycle-skills-matrix)
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
├── AGENTS.md / CLAUDE.md / GEMINI.md  ← Core constitution and layer rules
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

## Lifecycle Skills Matrix

StratosphereOS provides structured lifecycle skills spanning the entire development lifecycle. Each installs to `.agents/skills/<name>/SKILL.md` and is invoked as `/<name>` on Claude Code, Antigravity, Cursor, Codex, Devin and OpenClaw.

| Stage | Command | Purpose & Rationale | Reads | Produces |
|:---|:---|:---|:---|:---|
| **0. Session Start** | `/0a-start-session` | Eliminates cold-start costs by restoring branch state and loading durable memory. | `STATUS`, `.memory/*` | Synced session context |
| **1. Discovery** | `/1a-research`<br/>`/1b-concept-framing`<br/>`/1c-concept-map` | Investigates domain context, deconstructs fuzzy ideas, and maps complex dependency trees. | `.memory/*` | Discovery brief, glossary terms |
| **2. Design** | `/2a-write-prd`<br/>`/2b-interface-design` | Derives formal PRDs and UI contracts to prevent agent hallucinations and UI drift. | Discovery brief | PRD doc, UI/logic contracts |
| **3. Planning** | `/3a-version-planning`<br/>`/3b-create-issue`<br/>`/3c-sprint-planning` | Deconstructs PRDs into traceable vertical-slice issues sized for single context windows. | PRD, `BACKLOG_MAP` | Release roadmap, sprint plan, vertical issues |
| **3d. Execution** | `/3d-implement-issue` | Runs autonomous `micro-tdd`: writes failing test, executes suite, writes code, refactors. | Issue, `ARCHITECTURE` | Passing unit tests, committed code |
| **3z. Orchestration** | `/3z-afk-loop` | Runs the autonomous end-to-end loop for `type:AFK` slices (single slice or batch), chaining session start, implementation, verification, PR shipping, and stop session. | `BACKLOG_MAP`, `STATUS` | Automated PRs and synced status |
| **4. Ship & Audit** | `/4a-verify-and-ship`<br/>`/4b-audit-architecture-drift`<br/>`/4c-codebase-health-audit` | Audits acceptance criteria against automated test coverage, audits structural drift, and screens broad codebase health across 6 passes. | Issue, tests, codebase, `.memory/*` | Quality gap report, traceable PR, audit reports (docs/audits/) + slice proposals |
| **0. Session Stop** | `/0b-stop-session`<br/>`/0c-handoff` | Lints project memory, updates status ground truth, and prepares clean session handoffs. | Session work | Updated `STATUS.md`, clean handoff |
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
This interactive skill bootstraps the initial `.memory/` state layer, constitution files, and domain skills for new projects.

### 3. Upgrading Framework Files (Updating)
To upgrade an already-instantiated project to later plugin versions, run:
```text
/stratosphere-update
```
Your `.memory/` data and constitution are never overwritten; framework-owned blocks are updated in place, and you confirm any conflicts.

> [!IMPORTANT]
> **Upgrading a v3 project to v4.0.0 — do not auto-update.**
> v4 is a breaking release: every lifecycle artifact is renamed to Agent Skills spec form and moves to `.agents/skills/<name>/SKILL.md`. `/0a_start-session` and its siblings stop resolving — use `/0a-start-session`. There are **no alias shims**.
>
> `/stratosphere-update` alone is **not sufficient** and will refuse to run. The migration is a one-shot script that is **not bundled with the plugin** — fetch it from the release tag and run it once, by hand, from your project root:
>
> ```bash
> curl -fsSL https://raw.githubusercontent.com/PatN-git/Stratosphere-OS/v4.0.0/scripts/migrations/migrate_v3_to_v4.py -o migrate_v3_to_v4.py
> python migrate_v3_to_v4.py            # dry run (default) — read it before applying
> python migrate_v3_to_v4.py --apply
> rm migrate_v3_to_v4.py
> ```
>
> If you keep a clone of this repo (Antigravity users do), run `scripts/migrations/migrate_v3_to_v4.py --project <your-project>` from it instead.
>
> Then run `/stratosphere-update` to place the v4 skills. Between the two commands the project has no lifecycle skills, so run them back-to-back — and on a dedicated branch, since the migration touches `.agents/`, `.memory/` and `docs/`.

> [!TIP]
> **Keeping the Plugin Fresh**
> - **Claude Code users:** leave the StratOS marketplace plugin's `autoUpdate` **off** until you have migrated — a background update into a breaking release leaves a v3 project with skills that no longer resolve. Update deliberately, migrate, then `/stratosphere-update`. Once on v4, `"autoUpdate": true` is safe again for MINOR/PATCH releases.
> - **Google Antigravity users:** update your local repository clone via `git pull` and re-run `scripts/install-antigravity.sh` or `scripts/install-antigravity.ps1` to install the latest templates.

---

## Architecture & Governance

### Open Knowledge Format (OKF) Conformance
StratosphereOS conforms to the [Open Knowledge Format (OKF) v0.1 Specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf). The `.memory/` and `docs/` directories form a structured knowledge bundle. An interactive HTML graph visualizer can be generated anytime via `python .agents/scripts/okf_view.py`.

### UI Stack & Design Tooling
By default, UI projects assume React + Tailwind CSS + shadcn/ui. Non-UI projects rely on clean interface contracts defined during `/2b-interface-design`. Google Stitch design integration is supported automatically when enabled in workspace settings.

### Experimental: Jules Dispatch (opt-in)
An optional pack that offloads bounded `mode:AFK` slices to **Google Jules** (an async cloud coding agent) so implementation runs on Google's side, preserving Claude/Antigravity tokens. It **dispatches and reports only** — it never merges, never enables auto-merge, and never orchestrates other workflows; you verify each Jules PR with `/4a-verify-and-ship` and merge it yourself.

- **Not bundled — fetched on demand:** `python <plugin>/scripts/sync_skills.py --only jules-dispatch` lands it at `.agents/skills/jules-dispatch/`. It is invisible to `/stratosphere-update` (survives byte-identical).
- **Setup:** `JULES_API_KEY` in `.env.local` (sent as the `X-Goog-Api-Key` header); install the Jules GitHub app on the repo and configure its environment once in Jules's UI (Initial Setup → Run and Snapshot); keep a root `AGENTS.md` (Jules auto-reads it for conventions).
- **Data egress:** Jules clones the repo into a Google-managed VM and opens a PR on origin. Reconcile via PR review — nothing is pushed from your local tree.
- Status: `v0.1`, experimental. Source: `src/experimental/jules-dispatch/`; plan: `docs/plans/jules-afk-dispatch-implementation-plan.md`.
