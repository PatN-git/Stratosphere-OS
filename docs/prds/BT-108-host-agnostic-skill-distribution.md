---
type: prd
title: "BT-108: Host-Agnostic Skill Distribution Framework"
description: "Product Requirements Document for transitioning StratosphereOS from bespoke shell script installers to an open-ecosystem dual-track distribution framework via skills.sh, direct GitHub copy-paste, and native marketplaces, backed by a canonical dist/skills bundle."
bt: BT-108
generated:
  by: 2c-reconcile-specs
  at: 2026-09-28
resource: https://github.com/PatN-git/Stratosphere-OS/issues/108
status: stable
version: "1.0.1"
---

# BT-108: Host-Agnostic Skill Distribution Framework

> [!NOTE]
> **Legend & Marker Definitions:**
> - `[BASELINE]` ↔ `scope:baseline` (high-pain, well-served — build to not lose)
> - `[DIFFERENTIATOR]` ↔ `scope:differentiator` (high-pain, under-served — build to win)
> - `[DEFERRED]` ↔ `scope:deferred` (temporal deferral, mirrored in §9, not sliced in this version)
> - `[unbacked]`: Scope tag or score assigned by judgment without research backing (needs HITL confirmation)
> - `[unverified estimate — confirm]`: A figure stated without a cited research source (needs HITL confirmation)
> - `[Unknown]`: Data/value that is missing or not publicly available

## 1. Problem
- **Current experience:** Developers installing StratosphereOS into AI agent hosts rely on ~350 lines of bespoke bash and PowerShell scripts (`install-claude-code.{sh,ps1}` and `install-antigravity.{sh,ps1}`). These scripts require dual-OS maintenance, are redundant with native marketplaces (such as Claude Code's plugin marketplace), and silently execute dead logic copying retired directories. Furthermore, build output is fractured across duplicate directories (`dist/antigravity/skills` and `dist/claude-code/skills`) containing byte-identical skills, which misleads contributors into believing skill code is host-dependent.
- **Who is affected:** StratosphereOS framework maintainers burdened by brittle cross-platform installer maintenance, and consumer developers seeking frictionless, standardized installation into diverse agent environments (Claude Code, Antigravity, Cursor, Codex, Copilot, Devin, OpenClaw, Windsurf, Zed).
- **Cost of inaction:** Adding support for each new AI agent host costs a pair of custom platform scripts, multiplying maintenance overhead. Concurrently, new contributors encounter confusing directory drift and broken installation edge cases on Windows and headless environments.

## 2. Solution (user view)
StratosphereOS skills install through the open agent-skills ecosystem using standard tools developers already know. Developers can install the entire 26-skill suite into any supported host using a single ecosystem command (`npx skills add PatN-git/Stratosphere-OS/dist/skills --copy -y`), through native agent marketplaces where available, or via an un-opinionated direct copy-paste from GitHub for offline or zero-dependency setups. All compiled skills live in a single canonical bundle with sidecars and relative references intact. Repository setup (installing constitutions, rules, and memory templates) is decoupled from skill copying and is triggered cleanly from inside the agent using a dedicated onboarding skill.

## 3. Goals
- **Single Canonical Distribution Package:** Consolidate all compiled skills into one unified distribution directory, eliminating byte-identical duplicate trees.
- **Zero-Bespoke-Installer Distribution:** Retire custom per-host shell scripts in favor of ecosystem-standard package management, native marketplaces, and direct copy-paste.
- **Broad Host Reach:** Enable frictionless installation across all 8+ major consumption hosts without writing host-specific shell installers.
- **Strict HITL Preservation:** Ensure Human-In-The-Loop invocation sidecars and relative references remain 100% functional across all installation channels.
- **Clean Functional Boundary:** Decouple skill delivery (placing markdown files in agent folders) from repository scaffolding (bootstrapping memory and rules).
- **Suite Integrity Verification:** Guard consumer projects against partial skill cherry-picking during onboarding and upgrade workflows.

## 4. Non-Goals
- **Altering Skill Content:** Principled exclusion — This effort strictly addresses packaging, distribution, and scaffolding orchestration. No workflow logic, prompts, or lifecycle phases are modified.
- **Runtime Session Guards in Daily Workflows:** Principled exclusion — No suite completeness checks will be injected into routine session start workflows (`0a-start-session`) to prevent runtime latency and cognitive bloat; verification belongs strictly in setup and update routines (affirming existing 0a-start-session pre-condition check for .memory/ presence is permitted; adding full suite integrity validation loops to 0a is strictly excluded).
- **Standalone Global Antigravity Engine Rewrite:** Principled exclusion — We will not implement a proprietary global daemon or plugin loader for Google Antigravity to bypass upstream package manager directory mismatches; a minimal bridge is retained until the upstream ecosystem fix lands.
- **Deprecating Native Claude Marketplace:** Principled exclusion — Claude Code's native plugin marketplace path remains a supported, first-class distribution channel.
- **Dark Pattern / Lock-in Exclusion:** Principled exclusion — StratosphereOS will never require proprietary account creation, telemetry telemetry reporting, or cloud dependencies to install or execute skills.

## 5. Success Signals
- Deletion of ~350 lines of duplicate bash and PowerShell installer scripts.
- Single command installation into any of 8+ supported agent hosts via `skills.sh`.
- Zero test regression or drift check failures across all build and install verification suites.
- Working offline and non-Node.js installations verified via direct GitHub copy-paste instructions.

## 6. User Stories

### Journey Step 1: Framework Packaging & Release
1. **[BASELINE]** As a framework maintainer, I want `build.py` to compile all 26 skills into a single canonical distribution directory, so that I do not maintain duplicated byte-identical trees for different hosts. (ODI: 9.2 [HIGH])
2. **[BASELINE]** As a framework maintainer, I want every Layer 1 lifecycle skill in the distribution directory to package its transitive references and host-specific HITL sidecars, so that agent hosts correctly enforce human authorization. (ODI: 8.8 [HIGH])
3. **[BASELINE]** As a framework maintainer, I want CI drift checks and automated test harnesses to validate the distribution directory without requiring legacy shell installers. (ODI: 8.5 [HIGH])

### Journey Step 2: Consumer Skill Acquisition & Placement
4. **[BASELINE]** As a consumer developer, I want to install StratosphereOS skills into any supported agent host using `skills.sh`, so that I do not have to download and run untrusted shell scripts. (ODI: 9.4 [HIGH])
5. **[BASELINE]** As a Claude Code user, I want to install StratosphereOS via the native Claude Code plugin marketplace, so that my skills automatically stay current without external tool dependencies. (ODI: 8.9 [HIGH])
6. **[DIFFERENTIATOR]** As a developer in a restricted or offline environment, I want clear instructions for directly copying or cloning skills from GitHub without requiring Node.js or `npx`, so that I have zero external dependencies. (ODI: 7.8 [MED])
7. **[BASELINE]** As a Google Antigravity user, I want a reliable fallback installation mechanism that places skills into the active Antigravity configuration directory, so that I am not blocked by upstream path bugs. (ODI: 8.7 [HIGH])
8. **[DEFERRED]** As a developer using a private enterprise skill registry, I want to publish and sync StratOS skills through internal corporate artifact mirrors. (ODI: - [unbacked])

### Journey Step 3: Project Scaffolding & Integrity Assurance
9. **[BASELINE]** As a consumer developer who just acquired the skills, I want to run the onboarding setup skill inside my agent to initialize project memory, constitution, and rules, so that repository scaffolding is completely self-contained. (ODI: 9.1 [HIGH])
10. **[DIFFERENTIATOR]** As a consumer developer running setup or update, I want the tool to verify that all 22 core lifecycle skills are present and uncorrupted, so that missing cherry-picked skills do not cause broken workflows later. (ODI: 8.2 [MED])
11. **[BASELINE]** As an existing user upgrading from v4.0.0, I want `stratosphere-update` to smoothly refresh my installed skills from the new canonical distribution directory, so that my existing repository continues to function. (ODI: 8.6 [HIGH])

## 7. Constraints & Direction
- **Canonical Bundle Isolation:** Distribution artifacts must be compiled into `dist/skills/` rather than the repository root `skills/` to prevent collisions with OpenClaw during self-hosting dogfooding.
- **Dual-Track Distribution Contract:** All distribution documentation and tooling must maintain dual tracks: Track A (automated ecosystem package manager via `skills.sh`) and Track B (direct zero-dependency copy/paste from GitHub).
- **Separation of Concerns:** Skill distribution (moving skill folders into agent locations) must remain strictly decoupled from repository scaffolding (generating `.memory/`, `AGENTS.md`, and project rules).
- **Graceful Antigravity Fallback:** A minimal global Antigravity bridge must remain available until `vercel-labs/skills` merges upstream support for `~/.gemini/config/skills/` on Windows.
- **Surgical Integrity Validation:** Suite completeness checks must be confined exclusively to `stratosphere-setup` and `stratosphere-update`, leaving routine session start workflows (`0a-start-session`) lightweight and fast.

## 8. Definition of Done
- All legacy shell installers (`scripts/install-claude-code.{sh,ps1}` and `scripts/install-antigravity.{sh,ps1}`) and dead `commands/` copy logic are deleted upon delivery of the fallback bridge.
- Single unified `dist/skills/` directory contains all 26 compiled, spec-conformant skills with sidecars and relative references intact.
- Host packaging manifests reside in their canonical locations (`.claude-plugin/marketplace.json` at repository root for Claude Code, `dist/antigravity/plugin.json` for Antigravity).
- Global Antigravity fallback bridge (`scripts/install-antigravity-bridge.{sh,ps1}`) is implemented, verified for Windows and POSIX, and documented.
- `build/build.py`, `scripts/check.sh`, and `tests/install-harness` are updated and passing 100% on the new distribution structure.
- Dual-track installation instructions (`skills.sh` + direct copy-paste + marketplace) are documented in `README.md`.
- `stratosphere-setup` and `stratosphere-update` validate lifecycle suite integrity without introducing overhead to `0a-start-session`.

## 9. Out of Scope
- **Deferred:** As a developer using a private enterprise skill registry, I want to publish and sync StratOS skills through internal corporate artifact mirrors (from §6 story #8).
- **Refactoring Skill Instructions:** Rewriting or editing any workflow instructions or markdown documentation inside the skills themselves.
- **Automated Upstream PR Submission:** Submitting automated code PRs to the `vercel-labs/skills` repository is handled as an external community action, not an internal blocker.

## 10. Open Questions
1. **Subpath Package Listing:** Can `skills.sh` support automatic root discovery of `dist/skills/` without requiring an explicit subpath flag (`/dist/skills`)? — Owner: Framework Maintainer, Blocking: N (Resolved: subpath syntax `npx skills add PatN-git/Stratosphere-OS/dist/skills` works out of the box).
2. **Antigravity Upstream Path Fix:** When will Vercel Labs merge the correction for Antigravity's global path (`~/.gemini/config/skills` vs `~/.gemini/antigravity/skills`) and Windows symlinks (Issue #633)? — Owner: External / Maintainer, Blocking: N (Resolved: mitigated by retaining Antigravity fallback bridge).

## 11. Further Notes
- **S1 Empirical Spike Results:** Spikes executed against `skills@1.7.0` confirmed recursive copying of `references/`, verbatim preservation of `agents/openai.yaml`, and complete indexing of leading-digit skill names (`0a-start-session`, `1a-research`).
- **Benchmark Alignment:** Benchmarking against `mattpocock/skills` validated that top-tier agent skill repositories decouple skill placement from repository onboarding (`setup-matt-pocock-skills` $\leftrightarrow$ `stratosphere-setup`).

## 12. Viability & Cost
- **Complexity Estimate:** 3 / 10 (Consolidation of build output, deletion of shell scripts, update of test harnesses and documentation; low architectural risk).
- **Cost Table:**
  | Service / Resource | Free Tier Limit | Cost Threshold / Pricing | Source / Citation |
  | :--- | :--- | :--- | :--- |
  | `skills.sh` / npm registry | Unlimited open-source | Free public distribution | Vercel Labs / npm public registry |
  | GitHub Marketplace / Raw CDN | Standard GitHub free tier | Free public repository hosting | GitHub Terms of Service |
- **Architecture Cost Warning:** Zero ongoing infrastructure cost. Eliminating custom shell scripts reduces CI run minutes and developer maintenance hours.
- **"Is There Money Here?" (Market Demand Signals):** Strong ecosystem adoption (>25M installs across leading repositories on `skills.sh`, 75+ agent hosts supported). Standardizing on the open ecosystem ensures StratosphereOS remains frictionless for developers across any agent runtime.
- **Profit Alignment:** Pure developer enablement. Value accrues directly to open-source users through simplified installation and maintainers through reduced script fragility.
