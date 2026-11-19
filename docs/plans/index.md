# plans

* [[0d-rework-plan|0d Nightly Rework Plan]]
* [[docs/plans/0f-walk-me-through-concept|0f Walk Me Through — Concept Brief]] - Concept and draft body for a user-invoked skill that makes the chain behind a result, or the behavior of a planned change, visible in few plain words, so a non-technical owner judges outcomes and choices instead of code.
* [[0f-walk-me-through-implementation-plan|BT-217 Implementation Plan (0f Walk Me Through)]] - How a Haiku 5.5 implementer builds BT-217 in its own worktree on top of PR #216 under an Opus lead, the hold-out evaluation that is the slice's acceptance, and the fold into #216.
* [[1b-discovery-brief-sections-plan|1b Discovery Brief Sections and Brief Locator Plan]]
* [[3z-slice-routing-efficiency-plan|StratOS Plan — 3z Slice-Routing Efficiency (revised)]] - Right-size slices and remove the 0a relic so AFK orchestration cost is proportionate — without weakening independent verification.
* [[4a-audit-eval-handoff|4a Audit Work Handoff]] - Where the BT-201 audit work stands on 2026-10-20 and how to continue: unpushed commits, the open BT-204 rework, the findings so far and the next experiments.
* [[4a-audit-eval-strategy|4a Audit Improvement Test Strategy]] - How to test four ideas for catching more of what the 4a Spec auditor misses (watch rows, AC-literal lint, effort split, a labeled corpus) before any of them changes the production gate.
* [[4a-audit-yield-plan|4a Audit Yield Plan]] - Epic plan to log 4a auditor findings, cut cost per audit, consume Standards findings in AFK, and decide audit frequency from data.
* [[audit-report-then-slices-plan|Plan — Unified Audit Pipeline: Report → Proposal → Maintenance Epic (4b + 4c → 3b)]] - Unified audit pipeline: report, proposal, then maintenance epic (4b and 4c into 3b).
* [[backlog-map-decision|BT-189 Decision Record — BACKLOG_MAP in GitHub mode]]
* [[backlog-map-spike-plan|BT-189 Spike Execution Plan]]
* [[blocker-timing-plan|Blocker Timing Plan]]
* [[bt223-implementation-orchestration-plan|Implementation Orchestration Plan: Epic BT-223]]
* [[bt240-v5-handoff-plan|BT-240 v5.0.0 handoff plan]]
* [[bt241-apply-moves-blocker-plan|BT-241 apply-moves refuses guarded moves while a blocker is open]]
* [[bt242-v5-1-execution-plan|BT-242 (v5.1 Follow-ups): Orchestrator + Flash Subagent Execution Plan]] - Token-conscious orchestration plan for Epic BT-242 combining 3d/4a discipline, parallel Flash subagent implementation waves, D1-D4 owner decisions, and parallel HITL isolation for Slice S5 (#247). Revised after independent adversarial challenge.
* [[bt247-phase-5a-handover|BT-247 (Slice S5 of BT-242) Phase 5A Handover & Phase 5B Integration Guide]]
* [[bt249-concept-map-modernization-plan|BT-249: Modernization of 1c-concept-map Implementation Plan]] - Implementation plan for modernizing 1c-concept-map and 1b-concept-framing with Wayfinder parity, shared frontier-interview protocol, bounded Phase 2A AFK drain, lossless 1b-to-1c handover, and dual-backend tracker support.
* [[bt255-lifecycle-interaction-streamlining-plan|Implementation Plan: BT-255 Lifecycle Interaction Streamlining]]
* [[discovery-pipeline-quality-fixes-plan|Discovery Pipeline Quality Fixes Plan]]
* [[feature-level-acceptance-gate-plan|Plan — Feature-Level Acceptance Gate (4a) + 0a Zero-Test Invariant]] - Feature-level acceptance gate in 4a plus the 0a zero-test invariant.
* [[future-proofing-spec-conformance-plan|Future-Proofing StratOS — v4.0.0 Execution Plan]] - Migrate StratOS workflows to spec-conformant Agent Skills across six hosts, adopt OKF v0.2, before Antigravity retires workflow indexing on 2026-11-01.
* [[glossary-hygiene-plan|Glossary Hygiene Plan]]
* [[host-agnostic-install-framework-plan|Plan — Host-Agnostic Install Framework]] - Retire per-host installers in favour of a host-agnostic, skills.sh-style install framework.
* [[jules-afk-dispatch-implementation-plan|Jules Dispatch — Phased Implementation Plan (v0.1, experimental)]] - Optional, on-demand skill pack that offloads bounded StratOS slices to Google Jules (async cloud agent), preserving Claude/Antigravity tokens on the expensive implement step. Dispatches and reports; hands off at "PR opened". Distributed via sync-skills, invisible to scaffold --update, never merges, never orchestrates.
* [[l3-lifecycle-e2e-harness-plan|L3 — Automated Lifecycle E2E Harness]] - Drive the full StratOS lifecycle (0a→1a→1b→2a→2b→3b→3d→4a→0b) end-to-end in a throwaway environment with no human interaction, asserting on artifacts rather than prose.
* [[lifecycle-artifact-flow-audit|Lifecycle Artifact Flow Audit]]
* [[lifecycle-hygiene-bt168-plan|Lifecycle Hygiene BT-168 Plan]]
* [[lifecycle-run-defects-plan|Plan — Lifecycle-Run Defects (StratOS 3.3.0 field report)]] - Defects found in a full StratOS 3.3.0 lifecycle run on CleanTechHub, and their fixes.
* [[lifecycle-status-pr-scope-epic|Lifecycle Status, PR Scope and Blocker Timing Epic Plan]]
* [[lifecycle-status-pr-scope-execution|Lifecycle Epic Execution Plan]]
* [[lifecycle-v1-3-learnings-implementation-plan|Lifecycle v1.3 Learnings — Implementation Plan]]
* [[local-tracker-parity-plan|Local tracker parity with GitHub mode]]
* [[master-plan-lifecycle-context-triggers|Master plan — lifecycle status + load-memory skill + trigger harmonization (single MAJOR release)]]
* [[nightly-evidence-lifecycle-fixes-plan|Nightly Evidence — Lifecycle Fixes Plan]]
* [[pr107-review-response-plan|Plan — PR #107 Review Response]] - Responses to the 13 inline review comments on PR #107.
* [[pr216-live-test-fixes-plan|PR 216 Live-Test Fixes Plan]]
* [[pr216-live-test-plan|PR 216 live AFK test plan v3.0]] - Live in-app staged test plan for PR 216
* [[release-scoped-pr-plan|Release-Scoped PR Plan]]
* [[slice-close-at-ship-plan|Close Child Slices at Ship Plan]]
* [[status-md-concurrent-sessions-plan|STATUS.md for concurrent sessions (BT-218)]]
* [[stratos-4-1-1-hygiene-plan|StratOS 4.1.1 Hygiene — frontmatter drift, dry-run wording, update-skill gap, bump guard]] - Sized plan for the F1–F5 observations from the 4.1 follow-ups: fix the drifted docs, lint for recurrence, correct misleading wording, and harden the bump guard.
* [[stratos-4-1-followups-plan|StratOS 4.1 Follow-ups — reconcile.py gh shape, plan frontmatter, local cleanup]] - Fix reconcile.py's crash on real gh output, make the test shim mirror real gh, and clear the loose ends found while updating this dev project to 4.1.0.
* [[subagent-dispatch-efficiency-plan|Subagent Dispatch Efficiency Plan]]
* [[terminal-sync-invariant-plan|Terminal Sync Invariant Plan]]
* [[test-wait-1-cleantechhub-vitest-env|Test Wait Plan 1 - CleanTechHub Vitest Environment]]
* [[test-wait-2-stratos-dev-setup|Test Wait Plan 2 - StratOS Dev Setup]]
* [[test-wait-3-lifecycle-skills|Test Wait Plan 3 - Lifecycle Skills]]
* [[tracker-parity-and-smoke-plan|Tracker Parity Gaps and Real-GitHub Smoke Plan]]
* [[workflow-migration-audit|Workflow Migration — In-Body Edit Inventory]] - Per-file inventory of body edits required by the v4.0.0 workflows-to-skills migration. Companion to future-proofing-spec-conformance-plan.md Slice 9.
