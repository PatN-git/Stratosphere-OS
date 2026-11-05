---
type: backlog
title: Backlog Map
description: Authoritative registry and status mapping of all project issues.
generated:
  by: 4a-verify-and-ship
  at: 2026-10-22
version: "1.3.0"
---
# BACKLOG MAP

## Purpose
Authoritative, high-density reference for project issues and their status.

> Cross-reference rules → `.agents/rules/memory-protocol.md`.

## Rules
<!-- SOS:BLOCK id=backlog-rules v=1.4.0 -->

- **PRESERVATION RULE:** Do NOT delete or modify operational instructions under Rules (such as Label source of truth syncing rules) or the `Milestone` definition line under Label Registry during setup or backlog updates. They must remain permanently as operational guidance. The `Area` line under Label Registry must always exist: its slugs are project-defined and may change, but the line itself is never dropped.
- When writing the first entry, populate the Label Registry with all labels used in this GitHub project.
- **BT-id padding & Atomic Minting:** The GitHub issue number must be zero-padded to 3 digits (e.g., #7 becomes BT-007). All references, links, and filenames must use this padded format. **CRITICAL:** Never predict or pre-allocate `BT-<n>` IDs offline by scanning existing entries and calculating `MAX(BT_ID) + 1`. Because GitHub shares sequence numbers across both Issues and Pull Requests, guessing numbers locally guarantees collisions. IDs must be atomically captured strictly upon executing `gh issue create`.
- Update when GitHub issues are created, closed, or change status.
- Include only ID, Title, Status, Labels, Milestone, Parent, Blocked by, ICE, Ref — nothing else.
- **Identity contract:** the 7 columns `ID, Title, Status, Labels, Milestone, Parent, Blocked by` mirror GitHub's structured fields; `ICE` and `Ref` are local-only. A closed issue ≡ `status:done`.
- **Parent / Blocked by:** `Parent` holds a single `BT-<padded>` on the child only (`—` for epics/standalone); the reverse edge (an epic's children) is a query (`filter Parent = BT-<epic>`), never a stored list. `Blocked by` is a comma-list of bare `BT-<padded>` (`—` if none). An edge is cleared when the dependent's branch has the blocker's code: same ship unit → blocker shipped; otherwise → blocker merged. `reconcile.py --edges` decides. A slice's effective blockers include its parent epic's.
- Use the Label Registry; do not invent labels.
- The `Ref` column links to learnings, architecture rules, design rules, or glossary terms (e.g., L-012, A-003, DR-020, G-005). Doc paths (PRD/design) live in the GitHub issue body, not in Ref.
- **Label source of truth:** After installation (Checkpoint 6), the Label Registry here reflects the live GitHub label set.
  - If a label appears in **GitHub but not the registry** → add it to the registry (with user confirmation).
  - If a label appears in the **registry but not GitHub** → create it in GitHub before using it in any issue.
  - Never use a label in the Backlog table that is not in both the registry and GitHub.
- **Single Status Invariant:** An issue must always have exactly one `status:*` label. When transitioning an issue to a new status in GitHub or the Backlog table, always remove the prior `status:*` label first.
- **Concept Exemptions:** An issue carrying a `concept:*` label is exempt from `/3c-sprint-planning`, `[NEEDS_SPEC]` alerts, and the single-status invariant.
- **Concept Map Registry:** The `concept:map` row in the Backlog table carries `concept:map` + `status:*` (e.g. `status:in progress` while active, `status:done` on convergence) and is milestone-exempt. Child decision tickets (`concept:research`, `concept:grilling`, etc.) are tracked under their tracking issue as sub-issues and are NOT individually rowed in the Backlog table.

<!-- SOS:/BLOCK id=backlog-rules -->

## Label Registry
- **Area (`area:xxx`)**: `area:BE-ai`, `area:BE-api`, `area:BE-auth`, `area:BE-data`, `area:BE-infrastructure`, `area:FE-<page_name>` (where `<page_name>` is replaced with the page's slug during audit or page creation, e.g., `area:FE-login`, `area:FE-dashboard`)
<!-- SOS:BLOCK id=label-canonical v=1.4.0 -->

- **Primary Type (`type:<class>`)**: `type:bug`, `type:content`, `type:feature`, `type:improvement`, `type:maintenance`, `type:research`
- **Execution Mode (`mode:<mode>`)**: `mode:HITL` (Human-in-Loop required), `mode:AFK` (Autonomous execution)
- **Tier (`tier:<tier>`)**: `tier:epic` (PRD parent / epic), `tier:slice` (Leaf vertical slice)
- **Priority (`priority:xxx`)**: `priority:high` (Must have), `priority:medium` (Important), `priority:low` (Nice to have)
- **Size (`size:xxx`)**: `size:large` (Biggest effort vertical slice), `size:medium` (Medium effort vertical slice), `size:small` (Surgical effort / local fix)
- **Scope (`scope:xxx`)**: `scope:baseline` (MVP end-to-end), `scope:differentiator` (differentiator to win), `scope:deferred` (out of scope/temporal deferral)
- **Status (`status:xxx`)**: `status:needs_spec`, `status:planned`, `status:in progress`, `status:in review`, `status:blocked`, `status:done` (lifecycle order: `needs_spec → planned → in progress → in review → done`; Spikes: `needs_spec → done`; `blocked` from any point; child slices go `in progress → done`, closed at ship; `in review` = standalone issue or epic with its PR open)
- **Concept Discovery (`concept:xxx`)**: `concept:map`, `concept:research`, `concept:grilling`, `concept:prototype`, `concept:task`
- **Risk (`risk:xxx`)**: `risk:one-way` (PR contains a hard-to-reverse change per `merge-risk-paths.md`; a human must read it before merge)
- **Label Composition Rules**: Each leaf issue must carry exactly one `type:` + one `mode:` + `tier:slice` + one `size:`. Each epic must carry `tier:epic` + one `type:` (no `mode:`, no `size:`).
- **Milestone**: `vX.Y.Z` (`vMAJOR.MINOR.SPRINT`, e.g. `v1.2.3` = release 1.2, sprint 3). `MAJOR.MINOR` = the product release, owned by `/3a-version-planning`; `SPRINT` (Z) owned by `/3c-sprint-planning`. `vX.Y.0` = release planned, not yet sprinted. No leading zeros. Mirrors the GitHub milestone. This is the project's product-release tracker — not a tool/library version.

<!-- SOS:/BLOCK id=label-canonical -->

## Backlog

<!-- SOS:BLOCK id=backlog-header v=1.2.0 -->
| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
<!-- SOS:/BLOCK id=backlog-header -->
| BT-108 | Host-agnostic install framework: retire per-host installers | done | 3-implement, type:feature, tier:epic | v1.0.0 | — | — | — | — |
| BT-118 | Canonical dist/skills/ bundle + build pipeline | done | 3-implement, type:feature, mode:HITL, tier:slice, size:medium, priority:high, scope:baseline | v1.0.0 | BT-108 | — | ICE: 0.50 (I: 1.0, C: 100%) | — |
| BT-119 | Legacy installer retirement | done | 3-implement, type:maintenance, mode:HITL, tier:slice, size:small, priority:high, scope:baseline | v1.0.0 | BT-108 | — | ICE: 1.00 (I: 1.0, C: 100%) | — |
| BT-120 | Antigravity fallback bridge | done | 3-implement, type:feature, mode:HITL, tier:slice, size:small, priority:high, scope:baseline | v1.0.0 | BT-108 | — | ICE: 1.00 (I: 1.0, C: 100%) | — |
| BT-121 | Dual-track documentation and copy-paste instructions | done | 3-implement, type:content, mode:HITL, tier:slice, size:small, priority:high, scope:baseline | v1.0.0 | BT-108 | — | ICE: 0.80 (I: 1.0, C: 80%) | — |
| BT-122 | Suite integrity check in stratosphere-setup and stratosphere-update | done | 3-implement, type:feature, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | v1.0.0 | BT-108 | — | ICE: 0.40 (I: 1.0, C: 80%) | — |
| BT-127 | Install-harness Track A/D coverage and L2 cleanup | done | 3-implement, type:maintenance, mode:HITL, tier:slice, size:small, priority:medium, scope:baseline | v1.0.0 | BT-108 | — | ICE: 0.48 (I: 0.6, C: 80%) | — |
| BT-128 | 4a ship gate: full PR URL in slice comment (reconcile pr-link) + .tmp body-file cleanup | done | type:bug, mode:HITL, tier:slice, size:small, priority:medium, scope:baseline | — | BT-017 | — | ICE: 0.40 (I: 0.4, C: 100%) | — |
| BT-129 | Review and clean the .tmp scratch folder | done | type:maintenance, mode:HITL, tier:slice, size:small, priority:low, scope:baseline | — | BT-116 | — | ICE: 0.24 (I: 0.3, C: 80%) | — |
| BT-131 | 4a ship gate: mention release.py bump step and verify PR closing links | done | type:bug, mode:HITL, tier:slice, size:small, priority:medium, scope:baseline | — | — | — | ICE: 0.36 (I: 0.4, C: 90%) | — |
| BT-133 | stratosphere-update: self-update Claude Code copied skills and drive the plugin CLI | done | type:bug, mode:HITL, tier:slice, size:small, priority:medium, scope:baseline | — | — | — | ICE: 0.48 (I: 0.6, C: 80%) | — |
| BT-135 | Bump @google/design.md pin to 0.4.0 and fix stale lint invocation in docs | done | type:maintenance, mode:HITL, tier:slice, size:small, priority:low, scope:baseline | — | BT-116 | — | ICE: 0.18 (I: 0.2, C: 90%) | — |
| BT-136 | Lifecycle v1.3 learnings: plan-first 3d, lean ship gate, environment-fix ladder, spec orchestrator | done | tier:epic, type:feature | — | — | — | ICE: - | — |
| BT-137 | 4a ship gate: clean-tree guard, stratos-pr body, risk label, draft gate | done | type:bug, mode:HITL, tier:slice, size:medium, priority:high, scope:baseline | — | BT-136 | — | ICE: 0.80 (I: 2.0, C: 80%) | — |
| BT-138 | Test cadence: related tests per cycle, one full run per slice, reuse in 4a | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-136 | — | ICE: 0.40 (I: 1.0, C: 80%) | — |
| BT-139 | 3d plan phase (default on, mechanical plan check) | done | type:feature, mode:HITL, tier:slice, size:medium, priority:high, scope:baseline | — | BT-136 | — | ICE: 0.80 (I: 2.0, C: 80%) | — |
| BT-140 | 3z frontier skip, shared workspace, depth budget + AGENTS §8 subagent nesting | done | type:improvement, mode:HITL, tier:slice, size:small, priority:high, scope:baseline | — | BT-136 | — | ICE: 1.00 (I: 1.0, C: 100%) | — |
| BT-141 | Environment-fix ladder in 0b + 4c guardrail and test-health lens | done | type:feature, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-136 | — | ICE: 0.40 (I: 1.0, C: 80%) | — |
| BT-142 | 0d consolidation: drift-only check, scripted indices, sampling, decisions record | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-136 | — | ICE: 0.40 (I: 1.0, C: 80%) | — |
| BT-143 | contract_check.py: spec-to-schema contract check shared by 2a/2b/2c | done | type:feature, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-136 | — | ICE: 0.25 (I: 1.0, C: 50%) | — |
| BT-144 | 2z-write-spec: spec-phase orchestrator chaining 2a → 2b → 2c | done | type:feature, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-136 | — | ICE: 0.20 (I: 0.5, C: 80%) | — |
| BT-146 | contract_check.py --parity: flag drift between DATABASE_SCHEMA.md and schema.sql | done | type:feature, mode:HITL, tier:slice, size:small, priority:low, scope:deferred | — | — | — | ICE: - | — |
| BT-148 | Host hygiene: AGENTS.md §8 host table, Codex/Gemini CLI trust note, dead hooks.json, Jules contract | done | type:maintenance, mode:HITL, tier:slice, size:small, priority:high, scope:baseline | — | BT-012 | — | ICE: 2.00 (I: 2.0, C: 100%) | — |
| BT-149 | Stop writing the Copilot .github/copilot/skills twin | done | type:maintenance, mode:HITL, tier:slice, size:small, priority:medium, scope:baseline | — | BT-012 | — | ICE: 0.40 (I: 0.5, C: 80%) | — |
| BT-150 | Plugin-shaped bundle: Antigravity CLI dir check, validators, native install route | done | type:feature, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-012 | — | ICE: 0.25 (I: 1.0, C: 50%) | — |
| BT-152 | micro-tdd change routing: Direct and Risk routes, bug localization, countable Stuck with AFK return | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-012 | — | ICE: 0.35 (I: 1.0, C: 70%) | — |
| BT-153 | Opt-in pre-commit test gate: block commits whose code was not in a recorded passing test run | done | type:feature, mode:HITL, tier:slice, size:medium, priority:low, scope:baseline | — | BT-012 | — | ICE: 0.15 (I: 0.5, C: 60%) | — |
| BT-154 | Update flow on Antigravity: host-blind plugin lookup, stale plugin, Vision loss, CRLF staleness, code-simplifier sync | done | type:bug, mode:HITL, tier:slice, size:medium, priority:high, scope:baseline | — | BT-012 | — | ICE: 0.80 (I: 2.0, C: 80%) | — |
| BT-157 | Untrack docs/okf-view.html: gitignored but still committed in the public repo | done | type:bug, mode:HITL, tier:slice, size:small, priority:high, scope:baseline | — | BT-116 | — | ICE: 2.00 (I: 2.0, C: 100%) | — |
| BT-160 | Make Spikes sprint-eligible in 3c/3b | done | type:maintenance, mode:HITL, tier:slice, size:small, priority:high, scope:baseline | — | BT-116 | — | ICE: 0.80 (I: 1.0, C: 80%) | — |
| BT-162 | Nightly-evidence lifecycle fixes: reconcile label drift, fix-ladder rungs 3/4, shell-script rule, 4a epic blockers | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:high, scope:baseline | — | — | — | ICE: 1.00 (I: 1.0, C: 100%) | — |
| BT-163 | 0d nightly rework: delta drift, heal mode, cross-night findings, mechanical Decisions, framework feedback | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | — | — | ICE: 0.56 (I: 0.8, C: 70%) | — |
| BT-164 | 1b discovery brief: established facts, settled decisions, success state, follow-ups, brownfield RAT tests | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | — | — | ICE: 0.64 (I: 0.8, C: 80%) | — |
| BT-165 | Deterministic artifact links: PRD frontmatter discovery/research links, brief locator, parent-keyed paths | done | type:bug, mode:HITL, tier:slice, size:small, priority:medium, scope:baseline | — | — | — | ICE: 0.45 (I: 0.5, C: 90%) | — |
| BT-166 | 3b/4a input contract: sibling check, explicit PRD sections, design link, slice AC source, deviations, FAA scope | done | type:improvement, mode:HITL, tier:slice, size:large, priority:high, scope:baseline | — | — | — | ICE: 0.80 (I: 1.0, C: 80%) | — |
| BT-167 | Standing epics in 3d/4a + release rerun for one-release multi-slice PRs | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:high, scope:baseline | — | — | — | ICE: 0.90 (I: 1.0, C: 90%) | — |
| BT-168 | Lifecycle artifact-flow hygiene backlog: 3a epic inputs, hand-off line drift, directions.html, blank descriptions | done | type:maintenance, mode:HITL, tier:slice, size:medium, priority:low, scope:baseline | — | — | — | ICE: 0.15 (I: 0.3, C: 50%) | — |
| BT-169 | Stage 0 session lifecycle: restartable handoff contract and proven checks | done | type:improvement, mode:HITL, tier:slice, size:small, priority:medium, scope:baseline | — | BT-179 | — | ICE: 0.40 (I: 0.5, C: 80%) | — |
| BT-170 | Stage 1 discovery: hollow-confirmation guard, probe-before-ask, retrieval safety | done | type:improvement, mode:HITL, tier:slice, size:small, priority:high, scope:baseline | — | BT-179 | — | ICE: 0.80 (I: 1.0, C: 80%) | — |
| BT-171 | Stage 2 spec: PRD boundaries, shared design red-flags, usage-first contracts, required UI states | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-179 | — | ICE: 0.40 (I: 1.0, C: 80%) | — |
| BT-172 | floor_guard: block changes that lower the quality bar (skips, suppressions, deleted tests, loosened thresholds) | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:high, scope:baseline | — | BT-179 | — | ICE: 0.80 (I: 2.0, C: 80%) | — |
| BT-173 | Spike: verify-app implications (project-local real-surface verification skill) | done | type:research, mode:HITL, tier:slice, size:medium, scope:baseline | — | BT-179 | — | ICE: - | — |
| BT-174 | Spike: post-PR babysit implications (lifecycle step after 4a opens the PR) | done | type:research, mode:HITL, tier:slice, size:medium, scope:baseline | — | BT-179 | — | ICE: - | — |
| BT-175 | spec_lint: deterministic gate for discovery-brief and PRD checklists | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-179 | — | ICE: 0.20 (I: 0.5, C: 80%) | — |
| BT-176 | Stage 3 build: slice ceiling, expand/contract migrations, noticed-not-touched, test-quality checks, AFK decision log | done | type:improvement, mode:HITL, tier:slice, size:large, priority:medium, scope:baseline | — | BT-179 | — | ICE: 0.27 (I: 1.0, C: 80%) | — |
| BT-177 | Stage 4 review: observed-RED gate, dismissed findings, intent check, health deltas, metric honesty | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-179 | — | ICE: 0.20 (I: 0.5, C: 80%) | — |
| BT-178 | 3b: issue body as spec for standalone slices (seed from brief, minimum spec bar, escalation rule) | done | type:improvement, mode:HITL, tier:slice, size:small, priority:medium, scope:baseline | — | — | — | ICE: 0.40 (I: 0.5, C: 80%) | — |
| BT-179 | Skill-pack lifecycle hardening (Osmani agent-skills + pstack) | done | type:improvement, tier:epic | — | — | — | ICE: - | — |
| BT-181 | Test-wait reduction: faster parallel-safe test suite and honest suite reuse | done | type:maintenance, tier:epic | — | — | — | ICE: - | — |
| BT-182 | StratOS tests: parallel-safe and fast (xdist worksteal, build race removed) | done | type:maintenance, mode:HITL, tier:slice, size:medium, priority:high, scope:baseline | — | BT-181 | — | ICE: 0.80 (I: 2.0, C: 80%) | — |
| BT-183 | Lifecycle suite mechanics: deterministic recorder, derived scope, related-tests hint | done | type:maintenance, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-181 | — | ICE: 0.40 (I: 1.0, C: 80%) | — |
| BT-185 | pr_body.py build: DROPPED verdict gets no Closes line, epic-scoped commits get no slice row | done | type:maintenance, mode:AFK, tier:slice, size:small, priority:medium, scope:baseline | — | — | — | ICE: 0.40 (I: 0.5, C: 80%) | — |
| BT-186 | micro-tdd Fast-Track B: capture screenshot evidence when a browser tool exists, else set needs_manual_qa | done | type:improvement, mode:HITL, tier:slice, size:small, priority:medium, scope:baseline | — | BT-179 | — | ICE: 0.40 (I: 0.5, C: 80%) | — |
| BT-187 | 4a/3z CI gate: triage red CI after the feature PR completes | done | type:improvement, mode:HITL, tier:slice, size:large, priority:medium, scope:baseline | — | BT-179 | — | ICE: 0.27 (I: 1.0, C: 80%) | — |
| BT-188 | Close child slices at ship so epic progress tracks shipped work | done | type:feature, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-190 | — | ICE: 0.40 (I: 1.0, C: 80%) | — |
| BT-189 | Spike: BACKLOG_MAP as a generated read-only cache of GitHub | done | type:research, mode:HITL, tier:slice, size:medium, scope:baseline | — | BT-190 | — | ICE: - | — |
| BT-190 | Lifecycle: status, PR scope and blocker timing | done | type:feature, tier:epic | — | — | — | ICE: - | — |
| BT-191 | Release-scoped PR: one branch and PR per vX.Y release | done | type:feature, mode:HITL, tier:slice, size:large, priority:medium, scope:baseline | — | BT-190 | — | ICE: 0.27 (I: 1.0, C: 80%) | — |
| BT-192 | Blocker timing: clear an edge when the dependent's branch has the code | done | type:feature, mode:HITL, tier:slice, size:large, priority:medium, scope:baseline | — | BT-190 | — | ICE: 0.27 (I: 1.0, C: 80%) | — |
| BT-194 | Tracker backend: no BACKLOG_MAP in GitHub mode | in progress | type:improvement, tier:epic | — | — | — | ICE: - | — |
| BT-195 | Gate on GitHub: tracker resolution, batched fetch, --expect, combined 4a mode | done | type:improvement, mode:AFK, tier:slice, size:large, scope:baseline | — | BT-194 | — | ICE: - | — |
| BT-196 | Tracker verbs and label taxonomy references; 2a/2b/3b writers; Refs in issue body | done | type:improvement, mode:HITL, tier:slice, size:medium, scope:baseline | — | BT-194 | — | ICE: - | — |
| BT-197 | Install: setup records the tracker backend, scaffold stops recreating the map, tracker_switch.py | done | type:improvement, mode:HITL, tier:slice, size:large, scope:baseline | — | BT-194 | — | ICE: - | — |
| BT-198 | Readers, stages 0-1 and planning, move to scoped queries | done | type:improvement, mode:AFK, tier:slice, size:large, scope:baseline | — | BT-194 | — | ICE: - | — |
| BT-199 | Readers, build and ship loop; 4a combined gate; measured on CleanTechHub | in progress | type:improvement, mode:HITL, tier:slice, size:large, scope:baseline | — | BT-194 | — | ICE: - | — |
| BT-200 | Contract: remove mirror writes, map diff, heal and drift check in GitHub mode | planned | type:improvement, mode:HITL, tier:slice, size:medium, scope:baseline | — | BT-194 | BT-199, BT-218 | ICE: - | — |
| BT-201 | 4a audit yield: log auditor findings, cut cost per audit, decide frequency from data | done | type:improvement, tier:epic | — | — | — | ICE: - | — |
| BT-202 | Record auditor findings for HITL and AFK slices | done | type:improvement, mode:HITL, tier:slice, size:large, priority:high, scope:baseline | — | BT-201 | — | ICE: 0.53 (I: 2.0, C: 80%) | — |
| BT-203 | Cheaper audits: lean inputs and delta re-audit | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:high, scope:baseline | — | BT-201 | — | ICE: 0.80 (I: 2.0, C: 80%) | — |
| BT-204 | Host-neutral auditor_model tier for the Standards auditor | done | type:improvement, mode:HITL, tier:slice, size:medium, priority:medium, scope:baseline | — | BT-201 | — | ICE: 0.40 (I: 1.0, C: 80%) | — |
| BT-205 | Spike: classify CleanTechHub's Standards hard breaches | done | type:research, mode:HITL, tier:slice, size:medium, scope:baseline | — | BT-212 | — | ICE: - | — |
| BT-206 | Spike: blind replay of known spec blockers at epic/batch level | done | type:research, mode:HITL, tier:slice, size:medium, scope:baseline | — | BT-201 | — | ICE: - | — |
| BT-207 | Auto-fix hard Standards breaches in 4a and 3z within one bounded round | needs_spec | type:improvement, mode:HITL, tier:slice, size:large, priority:medium, scope:baseline | — | — | BT-208 | ICE: 0.17 (I: 1.0, C: 50%) | — |
| BT-208 | Spike: audit-policy checkpoint (per-slice vs per-unit; per-repo override?) | needs_spec | type:research, mode:HITL, tier:slice, size:medium, scope:baseline | — | — | — | ICE: - | — |
| BT-211 | Watch list: non-blocking 60-79 findings shown at the ship halt | done | type:improvement, mode:HITL, tier:slice, size:small, priority:medium, scope:baseline | — | BT-201 | — | ICE: 0.40 (I: 1.0, C: 80%) | — |
| BT-209 | Skill: /0e-plain-english explains the last agent message in plain English | done | type:feature, mode:HITL, tier:slice, size:small, scope:baseline | — | BT-190 | — | ICE: - | — |
| BT-213 | 0b: read the merge-time bookkeeping only when a row is in review | done | type:improvement, mode:HITL, tier:slice, size:small, scope:baseline | — | BT-190 | — | ICE: - | — |
| BT-212 | 4a Standards findings: rule bindings, then conditional auto-fix | done | type:improvement, tier:epic | — | — | — | ICE: - | — |
| BT-214 | Rule bindings: a rule can name its check and the Standards auditor honours it | done | type:improvement, mode:HITL, tier:slice, size:medium, scope:baseline | — | BT-212 | — | ICE: - | — |
| BT-217 | Skill: /0f-walk-me-through traces a result or predicts a change's behavior in plain words | planned | type:feature, mode:HITL, tier:slice, size:medium, scope:baseline | — | — | — | ICE: - | [[L-001]], [[L-004]] |
| BT-218 | STATUS.md holds folder state only: session lines for concurrent sessions | planned | type:improvement, mode:HITL, tier:slice, size:medium, scope:baseline | — | BT-194 | BT-199 | ICE: - | — |
