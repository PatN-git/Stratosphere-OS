---
name: pocock-v1-3-learnings-proposal
description: Per-workflow (0a–4c) improvement plan derived from mattpocock/skills v1.3 (implement-spec, pr, retro, chief-of-staff) and CleanTechHub evidence (3d experiment, test cost, LEARNINGS, nightly reports, last 10 PRs).
type: proposal
version: "1.0.0"
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-05
---

# Proposal: lifecycle improvements from mattpocock/skills v1.3

**Status:** Proposal, second review round (2026-10-05). Nothing is implemented. Mint the accepted items with `/3b`.
**Lineage:** [`.archive/matt-pocock-skills-v1-learnings.md`](.archive/matt-pocock-skills-v1-learnings.md) (v1.0), [`FEAT-discovery-pipeline-quality-fixes-proposal.md`](FEAT-discovery-pipeline-quality-fixes-proposal.md) (v1.1).

**Sources:**
- **Upstream:** the v1.3 release post (pasted by the user; its URL returns 404), `CHANGELOG.md` 1.3.0/1.3.1, release PR [mattpocock/skills#1120](https://github.com/mattpocock/skills/pull/1120), and the `SKILL.md` + docs page of `implement-spec`, `implement`, `pr`, `retro`, plus in-progress `chief-of-staff` (added 2026-10-05).
- **Host capabilities:** official docs and changelogs, plus the user's Antigravity logs.
- **CleanTechHub evidence (all read-only):**
  - `.tmp/3d-test/` experiment reports
  - CI timings
  - `.memory/LEARNINGS.md` and its history
  - `docs/nightly/` (4 reports)
  - `.tmp/*-slicing-readiness.md` (4 `2c` runs)
  - spec-commit timeline
  - PRs #157–#225 (last 10)

---

## 0. Plan at a glance

| Workflow | Change | Evidence | Size | Priority |
|---|---|---|---|---|
| **0a, 0c** | — | | | |
| **0b** | Raise the LEARNINGS bar via a destination ladder; friction-gated; one proposal max; ID hygiene; `post_merge` → follow-up issue | LEARNINGS audit, nightly L-013 recurrence, PR audit | M | **High** |
| **0d** | Phase 3.6 cut to drift-only via `reconcile.py`; Phase 3.5 scripted; escalation rule; sampling for big deltas | 4 nightly reports | S–M | **High** |
| **1a–1c** | — (v1.3 left the front half of the flow unchanged) | | | |
| **2a/2b/2c** | Guiding orchestrator **`2z-write-spec`** (units kept); **mechanical contract check** shifted left into a script | spec timeline, 4 `2c` reports, `chief-of-staff` | M | Medium |
| **3a–3c, 3x** | — | | | |
| **3d** | **Plan phase by default** (host-native `/plan` / plan mode); no mandatory review; deterministic plan check; test cadence; clean hand-off | 3d experiment, Antigravity `/plan`, CI timings | M | **High** |
| **micro-tdd** | Per-cycle related tests, not a full sweep every cycle | `implement`, CI timings | S | **High** |
| **3z** | Frontier skip; AFK plan; shared workspace; depth budget | `implement-spec`, host research | S–M | **High** |
| **4a** | Audit sees uncommitted work; one suite run per sha; **minimal agent-first PR body**; path-based risk label | PR audit | M | **High** |
| **4b** | — | | | |
| **4c** | Guardrail and test-suite-health lens | `retro`, CI timings | S | Low |
| **AGENTS.md §8** | Subagent nesting row (depth 3) | host research | XS | Medium |

Dropped after review: parallel frontier execution, a deterministic driver for 3z, Skill-tool wording, and the `pr-body` skill with Summary visuals.

---

## 1. Decisions from the review rounds

### 1.1 Subagent depth: budget 3, and it works across the whole lifecycle

| Host | Nesting | Default/max depth | Parallel | Worktree/subagent | Confidence |
|---|---|---|---|---|---|
| Claude Code | yes | **3** (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`; at the limit the Agent tool is withheld) | yes | `isolation: worktree`, **branched from the default branch, not the parent's HEAD** | VERIFIED |
| Antigravity app 2.x | yes | max **10** | yes (`invoke_subagent` with a `Subagents` array) | `inherit` / `branch` / `share` | VERIFIED |
| Antigravity CLI 1.x | yes | not stated | yes | `worktrees/` | VERIFIED; depth UNVERIFIED |
| Cursor / Copilot CLI / Codex | yes | 2 / 4 / 1 | yes | varies | VERIFIED / VERIFIED / COMMUNITY |
| Gemini CLI | **no** | 0 | — | — | VERIFIED |

The user's Antigravity logs show a 3-level chain in practice: root → `/teamwork-preview` → its orchestrator → 19 parallel children.

**Deepest chain in StratOS** (every workflow spawns only from its own level):

| Chain | Depth |
|---|---|
| 1a refuter, 1b challenger, 2b stress tester, 2c auditor, 3a/3b auditors, 4b/4c scanners | 1 |
| `3z` → `4a` audit-only subagent → isolated Spec + Standards auditors (when not native) | 2 |
| `2z` (proposed) → `2c` subagent → (native, no deeper) | 1 |
| **Any of the above wrapped by an outer orchestrator** (`/teamwork-preview`, `chief-of-staff`) | **3** |

**Rule:**
- **Budget:** 3, the host default on Claude Code and within Antigravity's 10.
- **StratOS's own design maximum:** 2, which leaves one level for an outer wrapper.
- **Fallback:** every step degrades to inline on shallower hosts (Cursor 2, Codex 1, Gemini CLI 0). The workflows' "using the host's subagent mechanism" wording already implies this; §2.11 makes it explicit.
- **Single writer:** only `3d` commits.

### 1.2 2a / 2b / 2c: guiding orchestrator, not a merge (deeper review)

**What real usage shows (CleanTechHub):**
- **The three run back-to-back.** 2a→2b gaps: BT-003 1h35, BT-119 25 min (then 2c +10 min), BT-168 23 min, BT-215 **6 min**. The split costs three invocations and three `load-memory` passes per feature without buying a pause. The exception is Path A (Stitch/Claude Design), whose brief pause is real.
- **2c earns its keep.** It found **P0s in 4 of 4 features**: BT-119 2, BT-161 3, BT-168 1, BT-215 1. That is 7 P0s plus 10 P1s, written up as 6–10 findings per report.
- **Most P0s are mechanical contract mismatches** (FK to a non-existent column, an invalid enum value `'intern'`, a view created before its dependency, a non-executable `schema.sql`). The rest are cross-artifact contradictions (scope, cardinality, trigger model). The mechanical half is retro's "a check can fail, a sentence cannot" case.

**Options:**

| | A. Merge into one `2a-write-spec` | B. Restructure (2a+2b one workflow, 2c inside) | **C. Guiding orchestrator `2z-write-spec`** |
|---|---|---|---|
| Invocations per feature | 1 | 1 | 1 |
| AGENTS.md §4 "exactly one document per run" | **violated**, needs a core-rule change | violated | kept: each unit commits its own doc |
| Re-run granularity (2a Expand mode, 2b Path A resume, standalone 2c) | lost | partly lost | kept |
| HITL steps (cost gate, direction pick, Path A pause) | all in one long context | same | main thread keeps only HITL + decisions |
| Context pressure | highest (PRD + design + audit in one window) | high | lowest: heavy work in subagents via pointers |
| Fit with existing patterns | new | new | same as `1c` (discovery orchestrator) and `3z` |

**Recommendation: C**, built as a small `chief-of-staff`-style conductor. Upstream's in-progress `chief-of-staff` (about 40 lines) supplies three principles: "all work in subagents, protect your context window", "communicate through context pointers", and "you are the gardener of the environment". Applied to the spec phase:
1. **Main thread:** HITL only. Clarifying questions, the 2a cost gate, the 2b direction pick, and the Path A pause/resume. It keeps a decision log `.tmp/2z-BT-<padded>-decisions.md` as the single context pointer.
2. **Subagents (depth 1):** PRD drafting from brief + decision log; the three 2b directions in **parallel**; the stress tester; then the `2c` auditor in a fresh context (forced anyway, since the run authored the artifacts).
3. **Units stay callable:** `2a`/`2b`/`2c` remain for Expand mode, Path A resume, and standalone re-audits. `2z` invokes them by name (AGENTS.md §1 orchestrator rule) and never duplicates their bodies.
4. **Shift left the mechanical checks:** a deterministic `contract_check.py` resolves every table/column/enum/FK/view the PRD or design names against `.memory/DATABASE_SCHEMA.md` (+ `schema.sql` when declared). It runs at the end of 2a and of 2b, and 2c scan item 1 calls the same script. 2c then spends its judgement on semantic contradictions.

**Not chosen:** a lifecycle-wide chief-of-staff session (2→3→4). It would blur the HITL boundary that `3z` keeps on purpose, and upstream's skill is a day-old experiment. Watch it.

### 1.3 PR body: minimal and agent-first (from the last 10 CleanTechHub PRs)

**Who reads the bodies:**
- No human or agent review read any body: 0 formal reviews, 0 inline comments.
- CI never reads the body, and agent re-verification comments (up to 9 per PR) were never answered.
- The one real pre-merge review (#192) read the **diff**.

**But the body is the only home for four things:**
- the audit verdict and waivers
- post-merge obligations
- "why" decisions not in the issue (for later `git blame`)
- the complete slice set

**Defects found:**
- **Parent closing link missing** (#192, #225).
- **Stale accumulation:** #158 lists 4 of 9 slices, and 5 issues were closed by hand.
- **Bloat:** #192 is 1,310 lines, 68% blank; the full test run is repeated per slice, 8–13×.
- **Claims instead of output:** #225, #195, #179.
- **Escape-corrupted body** (#196): it bypassed `--body-file`.
- **Post-merge DB migrations stranded in prose or checkboxes:** #175 merged with 8 unchecked boxes, including a live migration. #158 shipped 4 SQL migrations, including a data backfill, and never mentioned them.
- **4 of 8 merged PRs ship hand-applied `docs/database/*.sql` migrations** (grants, backfill, vocabulary rewrite). That is exactly the one-way-door case.

**Minimal schema** (replaces the 4a step-5 ingredient list). Closing lines stay outside the block, because GitHub ignores closing keywords in code blocks:

````text
Closes #<slice>.            (one per slice; + parent once the epic is complete)

```stratos-pr
feature: BT-215
head: <sha>
slices:                     # rebuilt from `git log` BT scopes on every update — never appended
  - {id: BT-218, summary: "<one line>", verdict: PASS|WAIVED|SKIP, audit_rounds: 2}
test: {cmd: "npx vitest run", observed: "Tests 1143 passed (1143)", at: <sha>}
risk: [db-migration, grants, live-write]    # path-derived; or [none]
post_merge: ["apply docs/database/migration_bt219_taxonomy_schema.sql"]
deviations: ["<decision not captured in issue/design>"]
refs: [A-012]               # only refs that constrained the change
```
## Notes   (optional; bug fixes: root cause only)
````

**Remove from the 4a spec:**
- AC↔test tables (link the audit output instead)
- the design-doc link (it lives on the issue)
- the manual-QA checkbox (it becomes `post_merge`)
- per-slice test output
- the re-verification PR comment

**Keep:**
- `--body-file`
- the closing-link read-back

The `risk` field mirrors to a registry label (`risk:one-way`, added to the label registry first). It is set by **path rules, not agent judgement**: `docs/database/**/*.sql`, `schema.sql`, grants/RLS, `.github/workflows/**`, plus a project list in `.memory/ARCHITECTURE.md`. The label marks the PRs where the human merger must actually look.

### 1.4 3d plan phase: on by default, no mandatory review

Antigravity's `/plan` is a built-in slash command: it researches, aligns, writes an implementation-plan artifact, and asks for approval. The user approved without reading, yet the experiment still showed:
- cleaner architecture (−60% on the BT-221 filter component)
- a pre-empted regression (`BT090_*`)
- surfaced cross-file seams

**So the value comes from the agent researching and structuring before coding, not from human review.** Consequences:
- **Gate:** plan **every** slice except `micro-tdd` Fast-Track B (cosmetic). Small slices get a short plan; the size gate from the previous revision is dropped.
- **Review:** not required. In HITL, use the host's native planning (`/plan` on Antigravity, plan mode on Claude Code), where the approval click is the host's own. In AFK (`3z`), write the plan file with no approval.
- **Replace the missing human check with a deterministic one:** every AC maps to a planned test path that matches the repo's existing test-naming glob. This is the defect the experiment's plan had: it named non-existent `CascadingSectorFilter.test.jsx` while the real tests are `tests/taxonomy/BT221_*`.

The evidence is still weak (tokens unmeasured, confounded arms, self-graded), so §3.2 keeps a clean re-run. It now *confirms* the default rather than deciding adoption.

### 1.5 Other answers carried over from round 1

- **Test cadence:** today a slice runs the full suite N+2 times. CleanTechHub's suite takes 100–184s in CI, and **82% of that is jsdom environment setup and imports, not tests.** The CleanTechHub-local levers (node default env, CI concurrency group, `afterEach(cleanup)` in setup, Vitest projects) belong in CleanTechHub issues.
- **LEARNINGS audit (11 active entries):**

  | Class | Count | Entries |
  |---|---|---|
  | Durable | 6 | 3 of these are host/agent tooling lessons that belong in the framework |
  | Mechanical | 3 | |
  | Reviewer standard | 1 | |
  | Session-specific | 1 | |

  Six entries were hard-deleted within a day, and IDs L-012 and L-020 were reused.

---

## 2. Changes per workflow

### 2.1 0a, 0c — no change

### 2.2 0b-stop-session — destination ladder (High, M)

**Problem.** The step-4 durability gate is self-judged and fails open. The nightly reports show the cost: the PowerShell-quoting lesson was written as L-013/L-014 on 09-17 and flagged **again** on 10-05 ("re-enforce L-013"). **Writing a lesson did not change behaviour.** That is `retro`'s core point: lessons belong in checks or with the reviewer, not in LEARNINGS, which is loaded into every `3d`.

**Change:**
1. **Friction gate.** Steps 3–4 run only after real friction: a failed approach, a costly wrong assumption, a bug, or a reviewer catch. A smooth session proposes nothing.
2. **Prevention question.** For each defect fixed this session, ask "what would have prevented it?" and route the answer through the ladder.
3. **Destination ladder** (new `src/references/environment-fix-ladder.md`, shared with `0d`). Each candidate goes to the first rung that fits:
   1. **Deterministic check** (lint, test, setup file, CI, hook, `validate_memory.py`). Wire an existing check before inventing one.
   2. **Reviewer standard** read by the `4a` Standards Auditor.
   3. **Existing law:** cite it, write nothing.
   4. **Framework issue** for host or agent tooling lessons.
   5. **Issue / `STATUS.md`** for in-flight state.
   6. **LEARNINGS:** durable, non-mechanical, needed while implementing a *different* slice, and backed by evidence (bit ≥2× or cost real time).
4. **Escalation.** If the friction repeats a lesson that already exists, the proposal **must** be rung 1 or 4, never another entry.
5. **Cap:** at most one LEARNINGS proposal per session. Propose-only, default `[ASSUMED]`.
6. **ID hygiene:** retire entries via `## Superseded`, never hard-delete. `validate_memory.py` fails on a reused ID.
7. **`post_merge` follow-up.** Done-detection reads the merged PR's `stratos-pr` block. Every unfinished `post_merge` item becomes a proposed follow-up issue, so nothing stays stranded in prose (#175, #192).

**Acceptance check:**
- Replaying the 11 CleanTechHub entries routes ≥4 away from LEARNINGS.
- A no-friction session proposes zero.
- A seeded reused ID fails lint.
- A merged PR with a `post_merge` item yields a proposed issue.

### 2.3 0d-nightly-consolidation — keep what works, script the rest (High, S–M)

**Evidence from 4 reports (07-25 → 10-05):**

| Phase | Acted on | Assessment |
|---|---|---|
| Phase 1 findings | 6 of 7 (~86%) | strongest |
| Phase 3 crystallization | 10 of 10 | strongest |
| Phase 3.6 recommendations | 4 of 4 followed, **0 non-obvious** | ¼ redundant with an open sprint the board shows; "also pending" lists wrong twice (maintenance epics with children listed for `/3b`; 14 future epics); `/3a` ROADMAP signal fired 3× and was ignored 2× (planning lives on the Projects board) |
| `[DRIFT]` lines | 11 of 11 fixed | genuinely useful, but duplicate `reconcile.py` |
| Phase 3.5 index rebuild | — | **52% of all report bytes**, zero judgement |
| `.last-run.json` | — | 10.6 KB, of which only `last_run` is ever read |

The cadence is post-burst, not nightly: deltas of 3 → 53 → 148 sessions.

**Change:**
1. **Phase 3.6 → drift-only.** Call `reconcile.py` over the non-done set (plus the stale-blocker check) and print its findings. Delete the recommendation table, the "also pending" list and the ROADMAP signal. The Projects board is the planning surface.
2. **Phase 3.5 → script.** The report gets one line: "N indices rebuilt".
3. **Phase 1 tightening:**
   - Apply the §2.2 ladder and escalation rule (a recurrence after an existing LEARNINGS entry → enforcement).
   - Label root causes as **hypotheses** (09-17 #5 misdiagnosed salience as sequencing).
   - Drop the session roster and "positive observations".
   - For large deltas, **sample**: the sessions with the most failed tool calls, plus a random few. This follows upstream's "run retro on a sample".
4. **Phase 3:** fix the `[ASSUMED]`-age test. It missed L-017 after about 148 sessions.
5. **`.last-run.json`:** store `last_run` only.
6. **Never re-propose a declined item** without new evidence (check the retained reports first). Re-proposing an *accepted-but-not-done* item stays allowed: L-006 needed two passes and then landed.
7. *(Naming)* Rename to "consolidation" without implying nightly. Optional, and it costs a rename.

### 2.4 1a–1c — no change

### 2.5 2a / 2b / 2c — `2z-write-spec` + contract check (Medium, M)

As in §1.2:
- **New:** user-invoked `src/workflows/2z-write-spec.md` (the orchestrator) and `src/scripts/contract_check.py` (the deterministic contract resolver).
- **2a/2b:** add one step each, "run `contract_check.py`; fix or `> open:`".
- **2c:** scan item 1 calls the script, and Phase 2 focuses on semantic contradictions.

**Acceptance check:**
- Re-running `contract_check.py` on the BT-161 and BT-168 artifacts flags the FK, enum and missing-column P0s that 2c found by hand.
- A `2z` run on one feature commits exactly two docs, one per unit run, and leaves a decision log.

### 2.6 3a, 3b, 3c, 3x — no change

### 2.7 3d-implement-issue — plan, cadence, clean hand-off (High, M)

**A. Phase 0.5: Plan.** Runs on every slice except Fast-Track B (§1.4).
- **HITL:** use host-native planning (`/plan`, plan mode).
- **AFK:** write `.tmp/3d-plan-BT-<padded>.md`.
- **Required contents:**
  1. files (`[NEW]` / `[MODIFY]`)
  2. seams
  3. AC → planned test path in the repo's naming convention
  4. existing tests at risk and how each stays green
  5. cross-cutting touchpoints (hydration, mocks/fixtures, CI env stubs)
  6. memory IDs
  7. open decisions
- **Deterministic plan check:** every AC has a planned test path matching the naming glob. Phase 3 compares the coverage map with the plan and names any deviations, which then feed the PR's `deviations`.

**B. Test cadence:**
- Per cycle: related tests (§2.8).
- Full suite: at each incremental commit and once at the Phase 3 gate.
- The Phase 2 post-simplifier re-run becomes related tests.
- Record `{head_sha, cmd, observed}` to `.tmp/3d-suite-BT-<padded>.json` for `4a`.

**C. Clean hand-off:** Phase 3 "done" requires no uncommitted slice-path changes.

### 2.8 micro-tdd — related tests per cycle (High, S)

Fast-Track A step 3 changes from "one full-suite sweep" to "run tests related to the changed files" (`vitest related --run`, `jest --findRelatedTests`, `pytest` + `testmon`, else the target files). The caller owns the full runs. Standalone `micro-tdd` keeps one full run at the end.

### 2.9 3z-afk-loop — frontier, plan, workspace, depth (High, S–M)

1. **Frontier skip.** `[SKIP-DEP] BT-<B> waits on BT-<A>` when a blocker is neither `VERIFIED` in this run nor `in review`/`done`. Today a dependent of a failed slice burns up to 3 implement+audit cycles.
2. **AFK plan.** The 3d JSON gains `plan_path`, and the report lists it.
3. **Shared workspace.** Dispatch `3d` with workspace shared/inherit, not worktree:
   - The CleanTechHub run lost ~12 tool calls to missing `node_modules` in a worktree.
   - Claude Code worktrees branch from the default branch.
   - The loop is sequential, so isolation buys nothing.
4. **Depth budget** per §1.1, stated in Authority & Guardrails.
5. *(Measure first)* Shared per-feature exploration notes passed as a pointer to each plan step.

### 2.10 4a-verify-and-ship — audit what ships, minimal body, risk gate (High, M)

1. **Audit sees uncommitted work (correctness gap).** The Phase 2 targets use `<merge-base>...HEAD` (committed only), while the Phase 5 safety net commits and pushes uncommitted slice files, so those ship **unaudited**. Fix: Phase 2 halts on uncommitted slice-path changes ("commit via 3d first").
2. **One suite run per sha.** Reuse `.tmp/3d-suite-*.json` when `HEAD` matches; otherwise run once. CI stays the independent re-run.
3. **Minimal agent-first body** (§1.3):
   - `slices` is **rebuilt from `git log` scopes on every update**. This fixes the #158 staleness.
   - The parent closing line is added when the Epic Check fires. This fixes #192/#225.
   - One `test` line at `head`.
4. **Path-derived `risk`** plus the `risk:one-way` label. The final ship line names it.
5. **Draft rule check.** A feature PR whose parent epic has open siblings must be draft. #225 was merged non-draft under the epic title while #199–203 were open. Today this is enforced only at creation; add it to the step-9 terminal gate.
6. **Explicit standards path** for the Standards Auditor: `CODING_STANDARDS.md` → `[[A-xxx]]` → `code-smell-baseline.md`.

### 2.11 4b — no change

### 2.12 4c-codebase-health-audit — guardrail and test-health lens (Low, S)

- A repo with no pre-commit hook and no CI lint/typecheck/test is a finding. So is an unwired check.
- **Test-suite health:**
  - environment/import time dominating execution
  - duplicate CI triggers
  - no related/changed test mode

### 2.13 AGENTS.md §8 — subagent nesting row (Medium, XS)

Add one row to the host table:
- depth per host, with a budget of 3
- the StratOS design maximum of 2
- the inline fallback
- only `3d` commits

---

## 3. Tests

### 3.1 Test cadence (micro-tdd + 3d + 4a), in CleanTechHub

- **Design:**
  - two `size:medium` slices
  - each run twice from the same base sha, same host and model
  - both arms cold, shared workspace
  - arm A = current skills, arm B = new cadence
- **Measure:**
  - full-suite runs (from the transcript)
  - wall-clock
  - tokens, if the host reports them
  - regressions first caught late (3d Phase 3, 4a, CI)
- **Pass:**
  - arm B makes ≤3 full runs per slice
  - wall-clock is down ≥25%
  - zero regressions reach CI that arm A caught earlier
- **Plus** a framework drift test in `tests/framework/`: micro-tdd names related-tests mode, and 3d Phase 3 names the full run.

### 3.2 3d plan phase: clean confirmation run

- **Design:** the same protocol as §3.1, plus `node_modules` pre-installed and the model recorded.
- **Measure:**
  - tokens from host usage (not step counts)
  - wall-clock including the plan step
  - AC coverage scored by an independent `4a audit-only`
  - regressions to existing tests
  - follow-up commits within 48h
- **The default stays on if:** it is no worse on tokens and wall-clock, and better on at least one quality metric. Otherwise, fall back to a size gate.

### 3.3 Inline acceptance checks

0b §2.2, 0d §2.3 (a report contains no recommendation table and is ≤40% of today's bytes), 2z §2.5, 3z frontier, 4a items 1, 3 and 5 (replay #158's commit set: the body lists all 9 slices).

---

## 4. Suggested slicing (for `/3b`)

One maintenance feature, in dependency order:

1. `fix(4a): halt on uncommitted slice changes before audit` (§2.10.1)
2. `feat(3z): frontier skip for dependents of failed slices` (§2.9.1)
3. `feat(micro-tdd,3d): related-tests cadence + suite-result handoff` (§2.7B, §2.8, §2.10.2) + test §3.1
4. `feat(3d): default plan phase + deterministic plan check; 3z plan_path` (§2.7A, §2.9.2) + test §3.2
5. `feat(4a): minimal stratos-pr body, path-derived risk label, draft-rule gate` (§2.10.3–5)
6. `feat(0b): destination ladder, escalation, cap, ID hygiene, post_merge follow-ups` (§2.2), plus the `validate_memory.py` ID check
7. `feat(0d): drift-only advisor via reconcile.py, scripted indices, sampling, slim watermark` (§2.3)
8. `feat(2z): write-spec orchestrator + contract_check.py shared by 2a/2b/2c` (§2.5)
9. `docs(AGENTS): subagent nesting row; 3z shared workspace + depth budget` (§2.13, §2.9.3–4)
10. *(Low)* `feat(4c): guardrail + test-suite-health lens` (§2.12)

**Separately, in CleanTechHub:**
- node-default test environment
- CI concurrency group
- `afterEach(cleanup)` in setup
- apply/track the stranded post-merge migrations from #175 and #192
- clean up the 4 open `[DRIFT]` rows from the 10-05 nightly
- run LEARNINGS through the new ladder

Per the version-bump policy, OKF `version:` bumps happen once per PR.

---

## Appendix: upstream v1.3 in brief

- **`implement` vs `implement-spec`:**
  - `implement`: one ticket per session, the human dispatches, `tdd` at seams, single files often, full suite once at the end, `code-review`, commit to the current branch.
  - `implement-spec`: a whole spec per run. It reads the task graph, runs the frontier in worktree subagents, lands everything on one integration branch via a merger subagent, then one `code-review` + fixer. The PR is optional.
  - Pocock ranks the agent loop below a deterministic loop.
  - Known rough edges: one big branch, collisions at merge time, stale GitHub frontier, gitignored files missing in worktrees.
- **StratOS mapping:**
  - `3d` ≈ `implement`.
  - `3z` ≈ a sequential `implement-spec` with per-slice independent audits and bounded retries.
  - A feature branch is already the integration branch.
  - Already solved in StratOS: TDD inheritance (`red_confirmed`), bounded review, stale frontier (`4a` clears `Blocked by` at `in review`), optional PR (`local-only`).
- **`pr`:** a Summary visual, before/after Evidence, Merge Danger (door + blast radius), aimed at human review speed. StratOS keeps only the evidence line and the door call, the latter as a path-derived label (§1.3).
- **`retro`:** proposes environment changes, never edits. Mechanical violations get a check; standards are for the reviewer; AGENTS.md stays lean; do not automate it.
- **`chief-of-staff`** (in-progress, 2026-10-05): a long-running single session; all work in subagents; context pointers; schedules; "gardener of the environment". Used as the pattern for `2z` (§1.2).
- **Removed `resolving-merge-conflicts`; renamed `CONTEXT.md` → `GLOSSARY.md`.** StratOS already used `.memory/GLOSSARY.md`.
