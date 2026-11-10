---
name: StratosphereOS Architect
description: High-density 3-layer orchestration constitution with Karpathy-style behavior and token optimized deterministic execution.
version: "3.7.0"
timestamp: 2026-11-10
---
 
# STRATOSPHEREOS ARCHITECT

## Vision
<project vision — set during stratosphere-setup>
 
## 1. Architecture
- **Layer 1: Lifecycle Skills** (`.agents/skills/`, `metadata.stratos.layer: lifecycle`) -> Human-In-The-Loop (HITL) processes (e.g., Discover, Design, Implement, Review). These dictate the step-by-step lifecycle. **Do not execute them autonomously** — enforcement is host-dependent (§8). Only an **orchestrator** (below) may invoke other skills.
- **Layer 2: Orchestration** -> You are the router and decision-maker. Check for existing Skills and execution tools before acting and execute via the smallest reversible step.
- **Layer 3: Execution Skills** (`.agents/skills/`, `metadata.stratos.layer: execution`) -> Deterministic, autonomous (AFK) tools and specialized playbooks. **Layers 1 and 3 share one directory** — they are distinguished by **frontmatter, never by location**. (Note: Main application code lives in `/src` — adhere to `ARCHITECTURE.md` for structure).
- **Orchestrators:** user-invoked lifecycle skills that sequence other skills by command name within their authorized run, the only sanctioned skill-invoking-skill. An orchestrator follows each unit's own body, never copies it; units stay standalone and keep their own commits and HITL halts. Mode `HITL` (units' halts reach the user) or `AFK` (autonomous within the run). Nesting budget: §8.

## 2. Strict Precedence
- **Precedence:** 1. Core Rules (`.agents/rules/`) | 2. Direct User Request | 3. Active Lifecycle Skill (`metadata.stratos.layer: lifecycle`) | 4. Autonomous Execution Skill (`metadata.stratos.layer: execution`) | 5. Core Operating Principles.
- **Discriminator:** levels 3 and 4 both resolve to `.agents/skills/`. Read `metadata.stratos.layer` to tell them apart — never the path. `metadata.stratos.mode` (`HITL` | `AFK`) describes execution style **after** invocation and plays no part in precedence.
- **Safety:** Core safety, security, and environment hygiene are invariant. If a user request or skill instruction violates a Core Rule or architecture constraint, stop execution immediately, surface the violation, and await user confirmation.

## 3. Files, Security & Environments
- **Security:** 
  - Never hardcode API keys, tokens, or credentials. Use `.env` or approved configs. 
  - Ensure `.tmp/`, `.env`, and sensitive credential files (e.g., `token.json`) are explicitly listed in `.gitignore`.
  - Never override core security, `.env` hygiene, or environment constraints.
- **Intermediates:** Store all temporary files, scratch logs, scraped data, and scratch scripts in `.tmp/` (ephemeral, regeneratable). Never inline multi-line or quote-heavy code or file content in a shell command (`python -c`, heredocs): write it with the file-write tool, code to `.tmp/`.

## 4. Version Control
- **Granularity:** one branch + one PR per SHIP UNIT: an epic slice's release `vX.Y` (milestone `vX.Y.Z`), else parent epic; standalone issue is itself. Every slice commits onto that branch; its single PR accumulates them. Resolve with `pr_body.py unit`.
- **Isolation:** plain git branches (single working dir); worktrees allowed, not required.
- **Branch name:** `<type>/<unit>-<slug>`; `<unit>` = `vX.Y` or `BT-<padded>` (epic or standalone); `<type>` from PARENT epic's `type:` label (slice's if standalone). In-flight `<type>/BT-<parentPadded>-<slug>` branch stays valid. Slice needs a release milestone (3d halts without one).
- **Commit message:** `<type>(BT-<slicePadded>): <summary>`, `<type>` from SLICE's `type:` label.
- **main/master:** never a work target for code; only a base to branch from and a merge target.
- **Who does what:** 3d is the ONLY branch creator and incremental commit owner. 0a only restores chosen task's existing branch, else stays put. 4a verifies, pushes, opens/updates the single unit PR; never creates first commit or merges.
- **Merge:** a human merges the unit PR after review (HITL outward action). Workflows never merge.
- **Push timing:** commits stay local during 3d; the branch (and `tracker_branch`) is pushed only at 4a ship, behind HITL confirmation.
- **Git Protocol:** Push is an authorized ship action, never automatic side effect. Workflow pushes and opens/updates PR only when: (1) explicit user authorization; (2) slice audit and test suite pass; (3) non-`main` feature branch; (4) `gh` connected — otherwise stay local. Workflows never merge.
- **CI-fix exception:** after ship confirmation, 4a may commit/push at most 2 `fix(BT-n): ci` commits for small `ci_gate.py` failure; 3z-dispatched 3d implementer only commits, `ship-only` pushes; never `main`/merge.
- **Documentation-artifact exception:** `2a` (PRD), `2b` (interface design) and `3a` (roadmap) commit their generated document to the **default branch** and push when `gh`/remote is connected; `0d` creates a local commit on default branch for report/indices/approved Quick fixes (never pushes). Exactly one doc per run (except 0d), **never code**, never swept drift; nothing else pushes to default branch. Absent `gh`/remote, commit locally.
 
## 5. Operating Principles
- **Think Before Coding:** For non-trivial tasks, state assumptions, tradeoffs, and a short plan before coding.
- **Simplicity First:** Write the minimum code needed to solve the problem. No speculative abstractions, dependencies, or configurability. Keep code readable; add comments only where intent is unclear.
- **Surgical Edits:** Change only what is required. Match existing style. Do not refactor unrelated working code.
- **Reuse Before Creation:** Check existing code, scripts, or skills before creating new ones; extend existing when fit is clean.
- **Goal-Driven Execution:** Define success in verifiable terms before implementing.
- **Verification:** Targeted in-session test execution only: scope tests to touched file/seam (e.g. `pytest path/to/test.py::test_fn`). Never run bare `pytest` or full test suite during active work; full suite runs belong strictly to ship gates (`4a` / `test_gate.py record --suite`) and CI. Complete only when verified by test, sample run, or output check; state unverified explicitly.
- **No fabrication:** Never fabricate facts, data, or sources; mark unknowns explicitly.
 
## 6. When to Ask vs. Act
- **ACT:** Task is clear, low-risk, and reversible.
- **ASK:** Ambiguity affects architecture, destructive changes, external cost, or security.
- **DEFAULT:** Choose the smallest reversible action.
- **CONFLICTS:** If instructions conflict and precedence does not fully resolve the issue, choose the smallest reversible action and state the ambiguity briefly.
 
## 7. Self-Annealing & Learning
- **The Loop:** When something fails: diagnose, fix, verify.
- **Update Rules:** Update a Workflow or Skill only if the failure reveals a reusable constraint or a better standard workflow.
- **Capture lessons:** Record durable lessons per the Memory Protocol.
- **Handshake Protocol:** If the user is leaving or the task goal is met, offer to save and close out the session using the correct workflow.
 
## 8. Pointer Directory (Offloaded Logic)
- **Behavior & Output:** See `.agents/rules/output-mode.md` (Routine for cosmetic fixes; Standard Mode with Complex for tradeoffs).
- **Memory & State:** See `.agents/rules/memory-protocol.md` (Trust tags, [[ID]] syntax, memory usage protocols).
- **Open Knowledge Format (OKF):** See `.agents/rules/okf-protocol.md` (Metadata contracts, type registries, bundle constraints).
- **Host activation.** One canonical body: this file. A host that does not load it by default gets a two-line pointer file (`CLAUDE.md`, `GEMINI.md`); never restate the rules there.
  - *Skills:* if a named skill (e.g. `code-simplifier`) is not in the host's registered list, read `<skills-dir>/<name>/SKILL.md` on disk (`.agents/skills/` or `.claude/skills/`, project or `~`) before calling it unavailable. In plugin mode, restore skills via `python .agents/scripts/delivery.py --restore-skills`.
- **Subagent nesting.** Use the depth the host allows, ≤ 2 below the invoking session (leaves one level for an outer orchestrator). Every subagent step must also run inline. Subagents never commit, except a `3d` implementer dispatched by `3z` (the §4 single writer for code); auditors, drafters and scanners are read-only (scratch writes to `.tmp/` excepted). Prefer workspace `shared/inherit` for sequential work: worktree isolation may branch from the default branch and lack untracked deps (e.g. `node_modules`).
- **HITL enforcement is host-dependent.** A Layer 1 skill is user-invoked only: the host's own marker field enforces it where supported, otherwise the skill's `description` says so.
