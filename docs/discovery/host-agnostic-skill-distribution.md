---
type: discovery-brief
title: "Discovery: Host-agnostic skill distribution retiring per-host installers"
description: "Implementation-ready concept brief for host-agnostic skill distribution — replacing bespoke shell scripts with dual-track distribution via skills.sh, direct GitHub copy-paste, and native marketplaces, backed by a canonical dist/skills bundle."
generated:
  by: 1b-concept-framing
  at: 2026-09-28
status: ready-for-prd
slug: host-agnostic-skill-distribution
linked-prd: BT-108
version: "1.0.0"
---

# Discovery: Host-agnostic skill distribution retiring per-host installers

## Ask (verbatim)
> Stop hand-maintaining per-host installers. Install StratOS the way the agent-skills ecosystem now does, so adding a seventh host costs nothing.
> /0a-start-session for BT-108 review relevant context and perform deep research using /1a_research for all host systems again (use subagents if helpful per host)
> 1) yes, retire Claude Code shell scripts
> 2) ye, keep antigravity fallback
> 3) yes, collapse duplicated skill trees into dist/skills
> 4) I still want to have a dual track with skills.sh and easy copy paste from github
> 5) only add the integriry check in "stratosphe-setup and - update"

## Vocabulary

- **Skill package manager:** A host-agnostic CLI tool (specifically `vercel-labs/skills` / `skills.sh`) that installs agent skills across multiple consumption hosts from a repository into host-specific agent directories. Avoid: "installer script", "package manager" (too generic).
- **Consumption host:** An AI coding agent environment or runtime (e.g. Claude Code, Google Antigravity, Cursor, OpenAI Codex, GitHub Copilot, Devin, OpenClaw, Windsurf, Zed) that executes Agent Skills. Avoid: "platform", "client", "agent" (ambiguous with subagents).
- **Distribution bundle:** The compiled, self-contained directory (`dist/skills/`) emitted by `build.py` containing all validated skills with relative references and invocation sidecars ready for external consumption. Avoid: "dist folder", "release package".
- **Dual-track distribution:** Providing both an automated skill package manager path (`npx skills add`) and an un-opinionated, zero-dependency copy/paste path from GitHub (direct folder copy or raw curl/git) alongside native host marketplaces. Avoid: "multi-installer".
- **Invocation sidecar:** Metadata files or frontmatter fields required by specific hosts to enforce Human-In-The-Loop execution (e.g. `agents/openai.yaml` for Codex, `disable-model-invocation: true` for Claude/Cursor/OpenClaw/Copilot, `triggers: ["user"]` for Devin). Avoid: "config file", "policy file".
- **Repository scaffolding:** The run-once initialization process (performed by `/stratosphere-setup` or `scaffold.py`) that writes repository memory templates (`.memory/`), constitution (`AGENTS.md`), rules (`.agents/rules/`), and harness pointers into a consumer project. Avoid: "installation" (conflates skill delivery with workspace configuration).
- **Suite integrity check:** A validation check performed exclusively during setup or update (`stratosphere-setup` and `stratosphere-update`) verifying that all core lifecycle skills are present in the host's directory without missing dependencies. Avoid: "runtime guard", "session check".

## Actor
1. **Framework Maintainer:** StratosphereOS core developer maintaining release artifacts, build scripts, and multi-host distribution manifests.
2. **Consumer Developer:** Software developer installing StratosphereOS skills into one or more of their local AI agent hosts (Claude Code, Google Antigravity, Cursor, Codex, Copilot, Devin, OpenClaw) across Linux, macOS, and Windows.

## Problem
Maintaining bespoke shell scripts (`install-claude-code.{sh,ps1}` and `install-antigravity.{sh,ps1}`, ~350 lines of duplicate bash and PowerShell) is brittle, redundant with native marketplaces, and scales linearly with each newly supported consumption host. Simultaneously, duplicated `dist/` directories (`dist/antigravity/skills` and `dist/claude-code/skills`) mislead contributors into believing skills are host-specific when only packaging is. Because the AI agent ecosystem has converged on `skills.sh` and native marketplaces, hand-rolled shell installers add ongoing maintenance friction without expanding agent reach.

## Chosen Framing
**Ecosystem Convergence with Dual-Track Distribution** — Adopt the standard open-ecosystem skill package manager (`skills.sh`) and native marketplaces as primary distribution mechanisms, backed by a direct copy/paste path from GitHub for zero-dependency environments. Consolidate all compiled skills into a single `dist/skills/` distribution bundle while maintaining a clean boundary between skill delivery and repository scaffolding.

**Rejected framings:**
- *Maintenance Debt Elimination:* Frames the initiative purely as deleting ~350 lines of shell scripts to reduce CI burden. Rejected: fails to capture the core architectural benefit of instantly unlocking distribution to 8+ consumption hosts.
- *Marketplace-First Monopolization:* Frames distribution entirely around individual host marketplaces (e.g. Claude Code marketplace, OpenClaw registry). Rejected: creates high friction because several major hosts (Antigravity, Cursor, Codex, Devin) lack public plugin registries, making `skills.sh` and direct copy-paste essential.

## Prior Art
- **`mattpocock/skills`:** Ships 54 skills via dual distribution (`claude plugins install` and `npx skills add mattpocock/skills`), utilizing a dedicated internal bootstrap skill (`/setup-matt-pocock-skills`) to initialize repo-level context and tracker markdown.
- **`affaan-m/ECC` & `open-gsd/gsd-core`:** Multi-harness frameworks that retired raw shell scripts in favor of standardized package distribution runners.
- **StratosphereOS v4.0.0 (#107):** Added 6 consumption hosts but left distribution tied to 2 legacy shell installers and byte-identical `dist/` trees.
- **`docs/plans/host-agnostic-install-framework-plan.md`:** Initial architectural plan identifying S1–S5 slicing structure.

## Non-Goals (early signal)
- Does NOT alter any skill content, prompts, or workflows. This initiative is strictly distribution and packaging.
- Does NOT add any integrity checks or overhead to `0a-start-session`. Verification of suite completeness belongs exclusively in `stratosphere-setup` and `stratosphere-update`.
- Does NOT rewrite Google Antigravity's global plugin engine. Retains a lightweight Antigravity fallback bridge until upstream `skills.sh` resolves global paths on Windows.
- Does NOT deprecate or remove the native Claude Code marketplace path (`/plugin marketplace add PatN-git/Stratosphere-OS`).

## Constraints
- **Canonical Bundle Isolation:** Distribution skills must reside in `dist/skills/`, avoiding a root `skills/` directory that collides with OpenClaw during self-hosting.
- **HITL Preservation:** Every distributed skill must retain its invocation sidecars (`agents/openai.yaml`, `disable-model-invocation: true`, `triggers: ["user"]`) and relative `references/`.
- **Dual Track:** Documentation and distribution must provide both `npx skills add PatN-git/Stratosphere-OS/dist/skills` and an easy direct copy-paste option from GitHub (`.agents/skills/`), with zero dependency on Node.js/npx required for raw copy-paste.
- **Clean Split:** Skill delivery (`skills.sh` / copy-paste / marketplace) only places skills into agent paths; repository scaffolding (`AGENTS.md`, `.memory/`, rules) is exclusively handled by running `/stratosphere-setup` inside the agent.

## Open Questions
1. **Subpath Package Listing:** Can `skills.sh` be configured via an upstream PR or repo configuration so `npx skills add PatN-git/Stratosphere-OS` discovers `dist/skills/` without requiring the explicit `/dist/skills` subpath flag? — Owner: Framework Maintainer, Blocking: N.
2. **Antigravity Upstream Path Fix:** When will Vercel Labs merge the correction for Antigravity's global path (`~/.gemini/config/skills` vs `~/.gemini/antigravity/skills`) and Windows symlinks (Issue #633)? — Owner: External / Maintainer, Blocking: N (mitigated by Antigravity fallback bridge).

## Riskiest Assumption
- **Riskiest Assumption:** Consumers running `skills.sh` will cherry-pick partial skills or install from an unsupported global path, breaking the closed 22-lifecycle skill handoff graph or rendering skills inert on Antigravity.
- **Why Fatal:** If a developer cherry-picks only `3d-implement-issue` without `1a` or `4a`, lifecycle handoffs fail. If global Antigravity users lose their skills, StratOS becomes unusable in Antigravity IDE.
- **Cheapest Test:** 
  1. Verify offline with `npx skills add ./dist/skills -a claude-code antigravity cursor codex devin openclaw github-copilot --copy -y` (already passed in S1 spike).
  2. Implement suite integrity check in `stratosphere-setup` and `stratosphere-update` to immediately flag any missing lifecycle skills.
  3. Validate that the Antigravity fallback bridge works in dual-mode (global fallback + project `.agents/skills`).
- **Status:** Survived (S1 spike validated sidecar preservation; mitigations locked for setup/update and Antigravity bridge).

## Recommended Next Step
- [x] `write-prd` — problem is sharp, architecture is validated, PRD-worthy. Slices S1–S5 fully mapped.
- [ ] `create-issue` Template B — this is a bug.
- [ ] `create-issue` Template A — spike needed first.
- [ ] Dropped — do not build.
