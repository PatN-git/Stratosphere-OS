---
type: research
title: "Research: Skill-pack comparison (Osmani agent-skills, Cursor pstack) vs StratOS lifecycle"
description: "Every Osmani agent-skills and Cursor pstack skill compared against StratOS lifecycle skills 0a-4c; per-stage gaps, new scripts, rejected ideas; filed as BT-169..BT-177."
status: stable
slug: skill-pack-comparison
generated:
  by: 3d-implement-issue
  at: "2026-10-15T00:00:00Z"
sources:
  - resource: https://github.com/addyosmani/agent-skills/tree/aeac41d4d005999432bb7312f7ff06383a91d59d
    title: agent-skills (pinned commit aeac41d)
    author: Addy Osmani
  - resource: https://github.com/cursor/plugins/tree/1e5c90a4b6f249917bd21fe361b3a2a7deb741b8/pstack
    title: pstack plugin (pinned commit 1e5c90a)
    author: Cursor (poteto)
  - resource: https://youtu.be/sU9MW8Ycq2M
    title: "Pocock vs Pstack vs Osmani: Which Skill Pack Wins?"
    author: Rob Shocks
version: "4.8.0"
---

# Research: Skill-pack comparison (Osmani agent-skills, Cursor pstack) vs StratOS lifecycle

## Research Brief
- **Scope:** which ideas from two external skill packs should StratOS adopt per lifecycle stage, and where a new skill or script is warranted. Matt Pocock's skills (the earlier main inspiration) are context only, not re-reviewed here.
- **Questions:**
  1. Which external skills overlap each StratOS lifecycle skill (0a–4c), and how strongly?
  2. What do they do that StratOS does not, and is it worth the token cost?
  3. Which ideas conflict with StratOS design (HITL lifecycle, never merge, host-agnostic)?
- **Question coverage:** Q1 ✓ · Q2 ✓ · Q3 ✓

## Method
- **Read in full, at pinned commits** (cite these, not the video): Osmani `addyosmani/agent-skills@aeac41d`, 25 `skills/*/SKILL.md` plus `agents/`, `commands/`, `hooks/`, `references/`. pstack `cursor/plugins@1e5c90a` `pstack/`: 30 non-principle skills, `poteto-mode` with 23 playbooks, 24 `principle-*` leaves, `agents/`, `automations/benny/`, `docs/guide/`. In the tables below, paths are relative to those roots: **[O]** = Osmani, **[P]** = pstack.
- **Compared against** the bodies of all 20 StratOS lifecycle workflows (`src/workflows/`) and the execution skills `micro-tdd`, `plan-html`, `concept-brainstorm`, `load-memory`, `code-simplifier`, and the shared references (`environment-fix-ladder`, `code-smell-baseline`, `confidence-scale`, `pr-body-and-ship`, `feature-acceptance-audit`).
- **Verification:** per-skill digests were produced by parallel readers. Every claim a recommendation rests on was re-checked against the source text by grep (36 cited paths and their key phrases, all present at the pinned commits). Two reader claims were corrected: StratOS *does* have independent verifiers (4a's two isolated auditors), and 0b/0d already cover most of pstack `correct`/`reflect` via `environment-fix-ladder`.
- **Video:** used only for framing. Transcript from YouTube auto-captions, so names are garbled in places.

## Key findings
- **Shape of the packs.** Osmani covers the whole SDLC in six phases (Define, Plan, Build, Verify, Review, Ship). Every skill has a fixed anatomy, including an anti-rationalization table and a Verification checklist. Skills are large (≈14 KB average, 343 KB total) and description-triggered. pstack has one router (`poteto-mode`) dispatching to playbooks, with user-invoked skills averaging ≈3.6 KB. It deliberately skips planning ("the best spec is the code"), puts most of its weight on verification against the real artifact, and defaults to autonomy.
- **StratOS is already ahead on** session and memory lifecycle, tracker-driven slicing, spec reconciliation and nightly consolidation; neither pack has these. Overlap is strongest in spec, TDD and review.
- **Recurring ideas worth importing:**
  - Gates that detect a *lowered bar*, not just a missing test: floor guard, mutation probe.
  - Hedged replies are not approval.
  - Probe an empirical question instead of asking it.
  - Fetched content is data, not instructions.
  - Usage-first interface design screened against named red flags.
  - Ratchets: metrics must not get worse.
  - "Inconclusive" and "not measured" as first-class verdicts.
  - Append-only decision trails for unattended runs.
- **Video critiques that apply to us:** long skill files bloat context, and too many description-triggered skills fire by accident. Both argue for importing ideas as single clauses or deterministic scripts, not prose blocks.

## Lifecycle matrix
Effort: XS = one clause · S = section or reference edit · M = new script and wiring · L = new skill.

| Ours | Already strong (not duplicated) | Import | Source | Prio · Effort | Filed |
|---|---|---|---|---|---|
| 0a | load-memory, branch restore | Reverted-attempts line; status tag per thread; approval never carries over sessions | [P] `skills/recall/SKILL.md`; [O] `skills/context-engineering/SKILL.md` | Low · XS | [BT-169](https://github.com/PatN-git/Stratosphere-OS/issues/169) |
| 0b | friction gate, environment-fix-ladder, durability gate | Rung 1: a new check counts only once shown failing on the motivating mistake | [P] `skills/correct/SKILL.md` | Med · XS | BT-169 |
| 0c | — (unstructured) | Fixed sections: scope+decisions, status+next, tree state, verification, open approvals, on disk vs in chat | [O] `skills/context-engineering/SKILL.md`; [P] `skills/poteto-mode/playbooks/pause-safely.md` | Med · S | BT-169 |
| 0d | recurrence slugs, drift delta, decision memory | Finding class: context the user hand-supplied that a tool could fetch | [P] `skills/reflect/` | Low · XS | BT-169 |
| 1a | confidence tags, refutation subagent, budget cap | Retrieval safety; mandatory "What we don't know" | [O] `skills/source-driven-development/SKILL.md`; [P] `skills/why/references/epistemics.md` | Med · XS | [BT-170](https://github.com/PatN-git/Stratosphere-OS/issues/170) |
| 1b | G1/G2/G3, user-declared stop, RAT | Hedged replies are not confirmation; empirical fork → probe, not question | [O] `skills/interview-me/SKILL.md`, `commands/build.toml`; [P] `skills/poteto-mode/SKILL.md` | High · XS | BT-170 |
| 1c | frontier, prototype tickets | Prototype ticket names the decision it settles | [P] `skills/poteto-mode/playbooks/prototype.md` | Low · XS | BT-170 |
| 2a | journey map, cost gate, contract_check | §7 Always / Ask first / Never boundaries | [O] `skills/spec-driven-development/SKILL.md`, `skills/security-and-hardening/SKILL.md` | High · S | [BT-171](https://github.com/PatN-git/Stratosphere-OS/issues/171) |
| 2a/1b | prose checklists | `spec_lint` script for the mechanical checklist items | [P] `skills/poteto-mode/playbooks/multi-phase-plan.md`, `skills/poteto-mode/scripts/check-plan.mjs` | Med · M | [BT-175](https://github.com/PatN-git/Stratosphere-OS/issues/175) **closed, not adopted** (see Not adopted) |
| 2b | 3 directions, 5-lens, stress tester, deep-vs-shallow | Shared `design-red-flags.md`; usage before types; required UI states and patterns to reject | [P] `skills/architect/`; [O] `skills/api-and-interface-design/SKILL.md`, `skills/frontend-ui-engineering/SKILL.md` | High · S | BT-171 |
| 2c, 2z, 3a | — | No change | — | — | — |
| 3b | minimum-slice floor, coverage auditor | Maximum-slice ceiling (split triggers); expand/contract migrations | [O] `skills/planning-and-task-breakdown/SKILL.md`, `skills/deprecation-and-migration/SKILL.md` | High · S | [BT-176](https://github.com/PatN-git/Stratosphere-OS/issues/176) |
| 3c | ICE sort, capacity | *(optional)* parallel-safe tag for slices with disjoint files | [P] `skills/poteto-mode/playbooks/feature.md` | Low · S | BT-176 |
| 3d | plan, micro-tdd, AC↔test map | "Noticed, not touched" → post-merge items | [O] `skills/incremental-implementation/SKILL.md` | Med · XS | BT-176 |
| micro-tdd | observed RED, regression proof | Hollow-test check; error output is data; premise census after 2 failed fixes | [P] `skills/principle-test-behavior-not-implementation/`, `skills/principle-attack-the-premise/`; [O] `skills/debugging-and-error-recovery/SKILL.md` | Med · XS | BT-176 |
| 3z/3x | isolation, retry ≤ 3, frontier, docs_read | Append-only decision log; *(optional)* different-model-family verifier | [P] `skills/show-me-your-work/`, `skills/interrogate/`, `skills/arena/`; [O] `skills/doubt-driven-development/SKILL.md` | Med · M | BT-176 |
| 3d/4a/3z | — | **Floor guard**: diff-scoped, flags skips, suppressions, deleted tests, loosened thresholds; exit 0/1/2 | [O] `skills/constraint-driven-development/references/floor-guard.md`; [P] `skills/poteto-mode/playbooks/autopilot-full.md` | **High · M** | [BT-172](https://github.com/PatN-git/Stratosphere-OS/issues/172) |
| 4a, 3z | 2 isolated auditors, feature acceptance audit | Dismissed list with reasons (4a); 3z `[NO-RED]` gate when tests have no observed RED (replaces the mutation spot-check, see Not adopted) | [O] `skills/code-review-and-quality/SKILL.md`; [P] `skills/interrogate/references/lead-judgment.md` | Med · S | [BT-177](https://github.com/PatN-git/Stratosphere-OS/issues/177) |
| 4b | deletion test, collision check | Shared red-flags; git-history intent check before a finding scores ≥ 80 | [O] `skills/code-simplification/SKILL.md`; [P] `skills/why/` | Med · XS | BT-177 |
| 4c | 3 parallel auditors, delta lens | Per-pass delta row, `[REGRESSION]` only on CVE and skipped-test counts; perf measured or "not measured"; `inconclusive` vs `n/a`; destructive-path check | [O] `skills/constraint-driven-development/SKILL.md`, `agents/web-performance-auditor.md`, `skills/security-and-hardening/SKILL.md`; [P] `skills/benchmark-checklist/SKILL.md` | Med · S | BT-177 |

## Research-first candidates
| Candidate | Source | Why research first | Filed |
|---|---|---|---|
| verify-app: project-local real-surface verification skill and feature map | [P] `skills/create-verification-skill/`, `skills/maintain-verification-skill/`; [O] `skills/browser-testing-with-devtools/SKILL.md` | Host-agnostic driving, projects without a UI, token cost, overlap with micro-tdd Fast-Track B and `needs_manual_qa` | Spike [BT-173](https://github.com/PatN-git/Stratosphere-OS/issues/173) |
| Post-PR babysit (CI classification, review-thread triage) | [P] `skills/poteto-mode/playbooks/babysit.md`, `references/bugbot-triage.md` | Push authorization under AGENTS.md §4, host overlap, new skill vs 4a phase | Spike [BT-174](https://github.com/PatN-git/Stratosphere-OS/issues/174) |
| `/stratos-help` router | [P] `skills/poteto-help/`; [O] `skills/using-agent-skills/SKILL.md` | Low value; not filed | — |

## Not adopted
| Idea | Source | Reason |
|---|---|---|
| Autonomy-first, "never block on the human", no planning skills | [P] `skills/poteto-mode/SKILL.md`, `principle-never-block-on-the-human` | StratOS is a HITL lifecycle (AGENTS.md §1, §6) |
| Agents merge or arm auto-merge | [P] `playbooks/autopilot-full.md`, `playbooks/shipping.md` | AGENTS.md §4: workflows never merge |
| No automated pipelines; personas never orchestrate | [O] `references/orchestration-patterns.md` | 2z/3z orchestrators are deliberate (depth ≤ 2) |
| Description-trigger everything ("1% chance → invoke") | [O] `skills/using-agent-skills/SKILL.md` | Accidental triggering (video critique); lifecycle stays user-invoked |
| Anti-rationalization tables in every skill | [O] all skills | Context cost; add a line only where 0d shows a recurring excuse |
| PR-body Scope / Blast-radius sections | [P] `playbooks/opening-a-pr.md`, `skills/blast-radius/` | PR bodies are not read in this agent-first workflow |
| Deploy, rollout, observability | [O] `skills/shipping-and-launch/`, `skills/ci-cd-and-automation/`, `skills/observability-and-instrumentation/` | StratOS ends at PR; runtime operations are product concerns |
| `spec_lint` script for the mechanical PRD / brief checklist items (BT-175, closed 2026-10-15) | [P] `skills/poteto-mode/scripts/check-plan.mjs` | Built and tested, then closed. The script was correct (36/36 seeded structural defects on the tuning set, 75/75 held-out; false alarms fixed) but the gain was cosmetic: 7-8 of 12 CleanTechHub PRDs had a path in §7 and 2 of 16 briefs a bad RAT status, while a 3-repeat pilot showed a fresh agent with today's checklist already catches seeded defects 27/27 (isolated reviewer 9/9). The defects that cost real rework were semantic (e.g. an inverted root cause) and no lint catches them. It would add a script run to 2a, 1b, 1c and 2c. Revisit only if 0d/0b records a structural miss it would have caught. Work: local branch `deferred/BT-175-spec-lint`. |
| Mutation spot-check in 4a (flip a condition, rerun tests, restore) (BT-177, 2026-10-15) | [O] `skills/code-review-and-quality/SKILL.md` | micro-tdd already requires an observed RED per test; the probe edits files, so it cannot run under 3z `audit-only` (read-only, AGENTS.md §8); `merge-risk-paths` rules match only SQL, CI and one-way scripts (untestable or unsafe to mutate); equivalent mutants would block ships. Replaced by a `[NO-RED]` check on 3z's existing `red_confirmed`. |
| Stack- or vendor-specific | [P] `typescript-best-practices`, `make-bot-ui`, `setup-pstack`, `runtime-forensics`, `trace-forensics`, `worktree-cleanup`; [O] `hooks/` | Host- and stack-agnostic product |

## Coverage: every reviewed skill
Outcome: **BT-n** = adopted into that slice · **covered** = StratOS already has it · **later** = sound but not filed · **no** = not adopted (see above).

**[O] skills:** api-and-interface-design BT-171 · browser-testing-with-devtools BT-173 · ci-cd-and-automation no · code-review-and-quality BT-177 · code-simplification covered (+BT-177) · constraint-driven-development BT-172, BT-177 · context-engineering BT-169 · debugging-and-error-recovery BT-176 · deprecation-and-migration BT-176 · documentation-and-adrs covered · doubt-driven-development BT-176 · frontend-ui-engineering BT-171 · git-workflow-and-versioning covered · idea-refine covered · incremental-implementation BT-176 · interview-me BT-170 · observability-and-instrumentation no · performance-optimization BT-177 · planning-and-task-breakdown BT-176 · security-and-hardening BT-171, BT-177 · shipping-and-launch no · source-driven-development BT-170 · spec-driven-development BT-171 · test-driven-development covered · using-agent-skills covered.

**[O] assets:** `agents/` covered (4a/4c auditors; metric honesty → BT-177) · `commands/` BT-170 (hedged approval), BT-172 (`/constraints guard`) · `hooks/` no · `references/definition-of-done.md` covered (PRD §8 + feature acceptance audit).

**[P] skills:** architect BT-171, BT-177 · arena BT-176 · automate-me covered (0d recurrence) · benchmark-checklist BT-177 · blast-radius no · bro no · correct BT-169 · create-verification-skill BT-173 · figure-it-out later · how later · in-your-own-words later · interrogate BT-176, BT-177 · ketchup later · maintain-verification-skill BT-173 · make-bot-ui no · no-comments later · poteto-help later · recall BT-169 · reflect BT-169 · setup-pstack no · sharpen later · show-me-your-work BT-176 · swarm later · tdd covered · teach later · technical-writing later · typescript-best-practices no · unslop later · why BT-170, BT-177.

**[P] poteto-mode playbooks:** router SKILL BT-170 · authoring-a-skill covered · autonomous-run later · autopilot-full BT-172 (countersign idea; merging no) · autopilot-stack no · babysit BT-174 · bug-fix covered · eval later · feature BT-176 · hillclimb later · investigation later · multi-phase-plan no (BT-175 closed) · opening-a-pr no · orchestrate later · pause-safely BT-169 · perf-issue later · prototype BT-170 · refactoring later · runtime-forensics no · session-pickup covered · shipping no · trace-forensics no · visual-parity later · worktree-cleanup no · `references/bugbot-triage.md` BT-174.

**[P] principles (24):** test-behavior-not-implementation, attack-the-premise BT-176 · encode-lessons-in-structure, guard-the-context-window, laziness-protocol, separate-before-serializing-shared-state, sequence-verifiable-units, prove-it-works, minimize-reader-load, fix-root-causes covered (AGENTS.md §5/§7, micro-tdd, code-simplifier) · never-block-on-the-human no · build-the-lever, explain-the-number, make-operations-idempotent, model-the-domain, boundary-discipline, exhaust-the-design-space, outcome-oriented-execution, redesign-from-first-principles, subtract-before-you-add, migrate-callers-then-delete-legacy-apis, foundational-thinking, experience-first, type-system-discipline later.

**[P] agents and automations:** comment-sicko later · poteto-agent later · `automations/benny/` later (fix-gate checklist, dedupe taxonomy).

## What we don't know
- The ICE values on BT-169..BT-177 are judgment calls, confirmed by the user but not backed by evidence.
- None of the external scripts (floor-guard, check-plan, log.sh, watch-pr) were executed; only their specifications were read.
- Token cost of each import was estimated from file sizes, not measured on StratOS runs.
- "later" items were not evaluated in depth; a later pass may promote some of them.
- Matt Pocock's skills were not re-reviewed against the current StratOS state in this pass.
