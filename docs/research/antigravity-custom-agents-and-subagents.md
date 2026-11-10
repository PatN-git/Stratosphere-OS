---
type: research
title: "Research: Google Antigravity Custom Agents, Host Parity, and StratOS Subagent Architecture"
description: "Comprehensive investigation into Google Antigravity custom agents, cross-host parity (Claude Code, Cursor, Roo Code, Windsurf, Codex), architectural distinctions from slash commands, and progressive enhancement path for StratOS lifecycle subagents."
version: "1.0.0"
generated:
  by: 1a-research
  at: "2026-11-10"
sources:
  - resource: "https://antigravity.google/docs/skills"
    title: "Google Antigravity Customization System"
    author: "Google DeepMind / Antigravity Team"
  - resource: "https://antigravity.google/docs/cli/features"
    title: "Antigravity CLI Features, Subagents, and TUI"
    author: "Google Antigravity Team"
  - resource: "https://docs.anthropic.com/en/docs/agents-and-tools/claude-code"
    title: "Claude Code Architecture and Subagents Specification"
    author: "Anthropic"
  - resource: "https://docs.cursor.com/agent/subagents"
    title: "Cursor Agent Subagents Architecture"
    author: "Anysphere"
---

# Google Antigravity Custom Agents, Host Parity, and StratOS Subagent Architecture

## 1. Executive Summary

As AI-assisted software engineering evolves from single-turn chat prompts into multi-agent orchestration, platforms have developed specialized mechanisms to manage complex workflows while preserving reasoning quality and avoiding context degradation. 

This research investigates:
1. **Google Antigravity Custom Agents & Subagents:** The core primitives, execution models, context boundaries, workspace isolation, and declaration interfaces.
2. **Cross-Host Ecosystem Parity:** How Anthropic's Claude Code, Cursor, Roo Code, Windsurf, and OpenAI Codex handle custom agents and subagents.
3. **Custom Agents vs. Slash Commands:** The fundamental architectural differences across execution triggers, context footprint, concurrency, tool sandboxing, and lifecycle.
4. **StratOS Lifecycle Subagents vs. Host-Native Custom Agents:** Comparison between StratOS's current dynamic, prompt-instructed subagents (in `3z`, `4c`, `1a`, `2b`, `4a`) and static host-declared custom agents.
5. **Architectural Recommendations:** Why a disruptive rewrite of StratOS's 3-layer architecture would harm portability, and how a targeted, progressive adoption of static read-only auditor personas delivers high ROI without compromising core guarantees.

---

## 2. Google Antigravity Custom Agents & Subagents

In Google Antigravity, **custom agents** and **subagents** are autonomous AI workers configured with dedicated system prompts, constrained toolsets, tiered models, and isolated execution boundaries.

### 2.1 Core Architectural Primitives
* **Context Isolation:** Subagents operate in dedicated conversation threads with independent context windows. Deep codebase indexing, terminal compilation spam, and verbose error logs are digested inside the subagent; only distilled summaries or strongly typed JSON schemas return to the coordinator.
* **Workspace Isolation Modes (`workspace`):**
  * `inherit`: Subagents operate directly in the parent's current workspace directory.
  * `branch`: Antigravity provisions an isolated Git worktree, enabling parallel subagents to modify code concurrently without workspace collisions.
  * `share`: Shares underlying repository storage without duplicating disk overhead.
* **Model Tiering (`model`):** Antigravity enforces four standardized tiers (`inherit`, `flash_lite`, `flash`, `pro`), allowing orchestrators to offload high-fan-out research or audits to low-cost, low-latency models.
* **Tool Sandboxing:** Agents can be restricted to read-only capabilities (`read_file`, `search_web`), granted terminal access (`run_command`), or provisioned with specialized MCP tools.

### 2.2 Declaration & Orchestration Surfaces
Antigravity supports four primary mechanisms to declare and invoke agents:
1. **Static Markdown Manifests:** Stored in `.agents/agents/<name>.md` (workspace scope), `~/.gemini/config/agents/<name>.md` (global scope), or packaged within plugins (`plugins/<name>/agents/<name>.md`). Manifests declare frontmatter (`name`, `description`, `subagent: true`, `mainAgent: false`, `tools: [...]`, `model: flash`) and use the markdown body as the system prompt.
2. **Dynamic Runtime Definition:** Agents can be defined on-the-fly using the `define_subagent` tool and launched via `invoke_subagent`.
3. **Dynamic Workflows (`run_workflow`):** Python orchestration scripts utilizing async primitives (`agent()`, `parallel()`, `pipeline()`, `phase()`, `trajectory()`) for structured fan-out and aggregation.
4. **Swarm Coordination (`swarm`):** Multi-agent collaboration across a shared message board, separating coordination, technical execution, monitoring (`swarm_monitor`), and UI reporting (`swarm_narrator`).

---

## 3. Cross-Host Ecosystem Parity

The multi-agent paradigm has converged across leading developer tools:

### 3.1 Claude Code (Anthropic)
* **Custom Subagents:** Declared as Markdown files with YAML frontmatter under `~/.claude/agents/*.md` (global) or `.claude/agents/*.md` (project).
* **Configuration:** Includes `name`, `description`, `model` (e.g., `sonnet`, `haiku`), and `tools` (e.g., `[Read, Grep, Glob]` for read-only sandboxing).
* **Invocation:** Managed interactively via `/agents`, CLI flags (`claude --agent <name>`), or auto-delegated by the coordinator.

### 3.2 Cursor
* **Custom Subagents:** Defined in `.cursor/agents/*.md` or `~/.cursor/agents/*.md`.
* **Configuration:** YAML frontmatter fields include `name`, `description`, `model: fast`, `readonly: true`, and `is_background: true/false`.
* **Execution:** Supports blocking foreground execution or background execution in isolated Git worktrees.

### 3.3 Roo Code (VS Code Extension)
* **Custom Modes & Personas:** Configured via JSON or prompt synthesis, defining `slug`, `name`, `roleDefinition`, allowed tool groups, and per-mode LLM routing.
* **Boomerang Subtasks:** Child subtasks launched in private context windows with restricted tool profiles, reporting back upon completion.

### 3.4 Windsurf (Codeium) & Codex
* **Windsurf:** Governed by Cascade flows, `AGENTS.md` rules, and the Agent Command Center for delegating long-running tasks to remote or cloud VM environments.
* **Codex:** Uses prompt templates (`~/.codex/prompts/*.md`), skills, and configuration files (`.codex/agents/*.toml`).

---

## 4. Custom Agents vs. Slash Commands

While both extend the assistant's capabilities, they operate at fundamentally different layers:

| Dimension | Slash Commands (`/command`) | Custom Agents / Subagents (`@agent` / delegated) |
| :--- | :--- | :--- |
| **Trigger & Agency** | **Human-Initiated (HITL)**. Entered explicitly in the chat UI. The model cannot trigger slash commands. | **Autonomous & Delegated**. Invoked dynamically by the coordinator, scripted via workflows, or assigned by humans. |
| **Context Window** | **Shared stream**. Dumps prompts, tool executions, and logs directly into the primary conversation. | **Isolated context**. Operates in a fresh context window; returns only synthesized outputs. |
| **Context Degradation** | High risk of **Context Bloat & Rot** over long sessions. | **Zero context pollution**. Noisy exploration remains private. |
| **Execution Concurrency** | **Sequential**. Single turn execution in the current chat. | **Parallel / Concurrent**. Can execute concurrently (`parallel`, swarms) across independent Git worktrees. |
| **Tool Permissions** | **Global session permissions**. Inherits all session capabilities. | **Granular sandboxing**. Can be strictly restricted (e.g., read-only, no shell access). |
| **Model Routing** | Locked to the active session model. | **Heterogeneous model tiers** (`flash_lite`, `flash`, `pro`, `haiku`). |
| **Primary Role** | **Workflow macro / prompt shortcut**. Standardizes repetitive prompts and procedures. | **Specialized cognitive worker**. Executes independent analytical or implementation labor. |

---

## 5. Current StratOS Setup vs. Host-Native Custom Agents

### 5.1 The Current StratOS Mechanism
In StratOS lifecycle skills (`3z-afk-loop`, `4c-codebase-health-audit`, `1a-research`, `2b-interface-design`, `4a-verify-and-ship`):
* Subagents are **ephemeral and prompt-instructed**. The parent skill dynamically calls `invoke_subagent(TypeName="self", Prompt="...")`.
* Constraints are **prompt-based negative rules** (e.g., *"Guardrail: Report findings only; do not edit any file. Do not commit or push"*).
* Model tiers are governed by conventions (`auditor-model-tiers.md`).
* Subagents rely on `load-memory` and `shared/inherit` workspaces so that git commits and `.tmp/` artifacts remain accessible across lifecycle transitions.

### 5.2 Strengths of the Current Setup
1. **Host Neutrality:** Runs seamlessly across Antigravity, Claude Code, Cursor, and CLI harnesses with zero host-specific schema dependencies.
2. **Graceful Fallback:** If a host lacks subagent capabilities, `AGENTS.md` §8 dictates running the steps inline without workflow failure.
3. **Dynamic Flexibility:** Prompts can inject ephemeral state, issue IDs, and runtime diffs without requiring disk schema updates.

### 5.3 Weaknesses of the Current Setup
1. **Safety Relies on Model Obedience:** A subagent prompted with `TypeName: "self"` still possesses `edit_file` and `run_command` in its tool definitions. A hallucinating model could violate read-only constraints.
2. **Token Overhead:** Every subagent dispatch must serialize guardrails, persona descriptions, and schemas into the dispatch prompt.
3. **UI Opacity:** In TUI/IDE dashboards, ephemeral subagents often appear as generic workers rather than identified specialists.

---

## 6. Architectural Evaluation & Recommendations for StratOS

### 6.1 Verdict: Progressive Enhancement, Not a Disruptive Redesign
* **Do NOT rewrite `3d-implement-issue` as a static custom subagent:** `3d` is not a micro-persona; it is a complex, stateful lifecycle workflow requiring full filesystem access, git operations, and memory synchronization. It belongs in the Layer 1/3 skill architecture.
* **Do NOT alter core 3-layer orchestration:** The separation between Lifecycle Skills (HITL), Orchestration (`3z`), and Execution (`micro-tdd`, `test_gate.py`) is mathematically sound and battle-tested.

### 6.2 Recommended Upgrade: Package Static Read-Only Auditor Personas
Extract read-only analytical passes into declared custom subagents packaged within the `stratosphere-os` plugin (`plugins/stratosphere-os/agents/`):

1. **`security-auditor`** (for `4c` pass A1/A2): `tools: [read_file, search_web]`, `model: flash`.
2. **`reliability-auditor`** (for `4c` pass B1/B2): `tools: [read_file]`, `model: flash`.
3. **`maintainability-auditor`** (for `4c` pass C1/C2): `tools: [read_file]`, `model: flash`.
4. **`architecture-auditor`** (for `4c` pass D1): `tools: [read_file]`, `model: flash`.
5. **`standards-auditor`** (for `4a` Phase 2 and `3z` Step 2B): `tools: [read_file]`, `model: flash`.
6. **`research-refutation-auditor`** (for `1a` Phase 2): `tools: [read_file, search_web]`, `model: flash`.
7. **`ux-stress-tester`** (for `2b` Phase 3): `tools: [read_file]`, `model: flash`.

### 6.3 Benefits of Progressive Adoption
* **True Architectural Sandboxing:** Tool prohibition physically prevents unauthorized edits or commands.
* **Automatic Model Optimization:** Flash/Haiku tiers are hardcoded in the agent manifest.
* **Zero Repo Clutter:** Bundled directly inside the plugin.
* **Backward Compatible:** Skills can attempt to dispatch named agent types (e.g. `TypeName: "security-auditor"`), falling back to `TypeName: "self"` if the named agent is not mounted.
