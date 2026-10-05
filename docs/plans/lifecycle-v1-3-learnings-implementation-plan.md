---
type: plan
title: Lifecycle v1.3 Learnings — Implementation Plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-05
version: "1.1.0"
---

# Implementation Plan: lifecycle improvements (Pocock v1.3 + CleanTechHub evidence)

**Status:** Ready for `/3b`. The rationale and evidence live in [`docs/proposals/.archive/FEAT-pocock-v1-3-learnings-proposal.md`](../proposals/.archive/FEAT-pocock-v1-3-learnings-proposal.md). This file is **only** the build spec. An implementing agent should not need the proposal, except for the "Why" links.

> **Review pass applied (2026-10-05).** Every path and anchor was checked against `src/`, `tests/`, `build/` and CleanTechHub. Material changes:
> - **§0.4:** the old-vs-new hash rule is made concrete. Only the OLD `body_hash` is added, and the v4.3.0 `reconcile.py` and `validate_memory.py` hashes are missing from the map today. New scripts need the `verify_scripts.py` orphan mapping instead. §0.5 now commits `dist/` before `check.sh`.
> - **S1:** the guard moves to Phase 1 step 0 and also runs for `ship-only`, which 3z uses and which skips Phases 1–2. The Phase 5 safety-net commit sentence is removed.
> - **S3:** 3d Phase 3's "Ephemeral (no writes)" is amended. 4a reuses any suite file at HEAD and writes its own result back, because the per-slice file never matched HEAD in 3z or after the release commit.
> - **S5:**
>   - The slice rebuild now specifies its `<base>`, `--no-merges`, verdict carry-over from the old body, and `PENDING`.
>   - The template keeps the `Closes #<n>.` literal (a test pins it), and `gh label create --force` runs before `--add-label`.
>   - The judgement-based risk rows are cut, and the draft rule gets a one-shot `gh pr ready --undo` heal.
> - **S6:** duplicate-ID detection already exists. The `[REMOVED]` tombstone would be an error today, so validate_memory must accept it. Follow-up issues get a registry-complete label set, and the active count is 10, not 11.
> - **S7:**
>   - The stale-blocker and closed-issue checks are `--all-open`-only, so the in-band gates keep their semantics, and `--require-gh` is dropped.
>   - "Declined" gets a data source (`## Decisions`). `[ASSUMED]` age is measured in days, and "Delete?" becomes a tombstone.
> - **S8 / S9:**
>   - The parser gets precision rules and a no-schema skip. The acceptance drops F-1/P1-2, which are not mechanically decidable.
>   - 2c runs in the main thread: its own isolation rule spawns the auditor, and a subagent cannot run 2c Phase 4's HITL.
>   - Adds resume detection and the skill-count and list updates the new skill needs. The sidecar is build-generated.
> - **S10 / S11:** "only 3d commits" was false (2a/2b/3a/4a commit too). The 4c checks go in `health-audit-scan-matrix.md` B2, and Phase 1 must pass the CI and hook files.
>
> **Review decisions (2026-10-05):**
> 1. **S3:** the full suite runs **once at the Phase 3 gate** (commits stay local until 4a). Intermediate commits run related tests only.
> 2. **S7:** the `[ASSUMED]` age threshold is 7 days.
> 3. **Docs:** this plan and the proposal ride on the feature branch. The first S-slice commit adds them; the final slice archives the proposal.
> 4. **S9:** the speculative delegations (PRD drafting subagent, 3 parallel direction subagents) are cut. Revisit only if a real 2z run shows context pressure.

---

## 0. Rules for the implementing agent (apply to every slice)

1. **Load the dev skill first:** `improve-workflows-skills` (`src/dev-skills/improve-workflows-skills/`). Follow its non-negotiables:
   - Edit **`src/` only**, never `dist/` or `.agents/`.
   - Never prune sub-agent guardrails, leading-word tokens or completion criteria.
   - An execution skill (`src/skills/*`) carries no project-local refs.
2. **Version bumps:** bump `version:` **once per PR** on each changed `src/` **`.md`** file (`minor` = behaviour change, `patch` = wording). Also refresh `timestamp:`. Never bump per commit. Scripts (`*.py`) carry no `version:`; the SOS block in a memory template carries its own `v=`.
3. **Shared prose** goes in `src/references/<file>.md`. The build (`build/build.py` `cited_refs`/`closure_for`) fans a reference out to every skill whose body cites `references/<file>.md` (transitively). A bare filename without the `references/` prefix does **not** fan out. Never paste the same rule into two workflows. A new reference needs frontmatter `description`, `version`, `timestamp` (`build/validate.py` rejects one without `version`).
4. **New or changed bundled scripts** (`src/scripts/*.py` that are placed into projects):
   - **New script:** add its name to the tuple in `get_bundled_project_scripts()` (`src/scripts/scaffold.py` ~L617; this also drives `place()`), **and** add a `rel_str == "scripts/<name>"` → `.agents/scripts/<name>` branch to the orphan-guard mapping in `tests/runners/verify_scripts.py` (~L302). An unmapped bundled file fails `check.sh`. A new script needs no hash entry.
   - **Changed existing script:** add the `_versioning.body_hash` (not raw sha256) of the **currently released, pre-change** copy to `KNOWN_SHIPPED_SCRIPT_HASHES` in `scaffold.py` (~L383), so projects without a lock baseline still refresh. The new hash is not needed (an identical copy is detected by equality). The v4.3.0 hashes missing from the map today: `reconcile.py` `8507cbfb11caa51554ce45cac63c7c26e76f0cc68c5c5cee186f8ebf92670d0e`, `validate_memory.py` `6b7e4e03ecbae6307440ad65b3184507eb213479585db2ee437ce0ccb3a3115e` (recompute on the pre-change file: `python -c "import sys;sys.path.insert(0,'src/scripts');import _versioning as v;print(v.body_hash(open('src/scripts/reconcile.py',encoding='utf-8').read()))"`). The `okf_view.py` v4.3.0 hash is already present.
   - Run `tests/framework/test_update_flow.py`.
5. **Gate for every slice:** `python build/build.py`, commit `dist/` together with the slice, then `bash scripts/check.sh`. It rebuilds, and its dist-drift step fails on an uncommitted `dist/`. It must end with `ALL CHECKS PASSED`.
6. **Wording tests:** workflow behaviour is pinned by text tests in `tests/workflows/`. Add new assertions there, mirroring `test_ship_gate_wording.py`, rather than inventing a new harness. Keep every existing assertion green unless the slice explicitly retires it.
7. **Host neutrality:**
   - Name host features as "the host's native X (e.g. Antigravity `/plan`, Claude Code plan mode)". Never require one host's tool name.
   - Every subagent step must also run inline where the host has no subagents.
8. **Commits:** `<type>(BT-<slice>): <summary>` on the feature branch, created by `/3d` (AGENTS.md §4).
9. **CleanTechHub** (evidence and manual validations) is the sibling checkout `C:\Users\patri\Dev\CleanTechHub`. Read it only; never commit there from this feature.

---

## 1. Slice overview

| # | Slice | Primary files | Size | Blocked by |
|---|---|---|---|---|
| S1 | 4a: refuse to audit or ship uncommitted slice changes; 3d: clean-tree completion | `src/workflows/4a-verify-and-ship.md`, `src/workflows/3d-implement-issue.md` | S | — |
| S2 | 3z: frontier skip for dependents of non-verified slices | `src/workflows/3z-afk-loop.md` | S | — |
| S3 | Test cadence: related tests per cycle, full suite per commit/gate, suite-result reuse in 4a | `src/skills/micro-tdd/SKILL.md`, `3d`, `4a` | S | S1 |
| S4 | 3d: default plan phase + deterministic plan check; 3z `plan_path` | `3d`, `3z` | M | S3 |
| S5 | 4a: minimal `stratos-pr` body, path-derived `risk:one-way` label, draft-rule gate | `4a`, `3z` Step 3A, `src/memory-templates/BACKLOG_MAP.md`, new `src/references/merge-risk-paths.md` | M | S1, S3 |
| S6 | 0b: environment-fix ladder, friction gate, cap, `post_merge` follow-ups; LEARNINGS ID lint | `0b`, new `src/references/environment-fix-ladder.md`, `src/rules/memory-protocol.md`, `src/scripts/validate_memory.py` | M | S5 |
| S7 | 0d: drift-only advisor via `reconcile.py --all-open`; scripted index rebuild; sampling; slim watermark | `0d`, `src/scripts/reconcile.py`, `src/scripts/okf_view.py` | M | S6 |
| S8 | `contract_check.py` shared by 2a/2b/2c | new `src/scripts/contract_check.py`, `2a`, `2b`, `2c` | M | — |
| S9 | `2z-write-spec` orchestrator | new `src/workflows/2z-write-spec.md`, `src/scripts/check_suite.py`, skill-count tests/docs | M | S8 |
| S10 | Subagent nesting contract (AGENTS §8) + 3z shared workspace and depth budget | `src/constitution/AGENTS.md`, `AGENTS.md`, `3z` | XS | S2 |
| S11 | 4c: guardrail and test-suite-health lens | `src/references/health-audit-scan-matrix.md`, `4c` Phase 1 | S | — |

Size maps to `size:` labels as XS/S → `size:small`, M → `size:medium`.

**Delivery (decided 2026-10-05):** **one epic → one feature branch → one PR → one version bump.**

The 11 plan sections are minted as **8 issues**. Small sections with no standalone verification value are folded into a sibling (3b minimum-slice floor). Each issue implements the named sections in full.

| Issue | Plan sections | Size | Blocked by | Why grouped |
|---|---|---|---|---|
| I1 | S1 + S5: 4a ship gate (uncommitted guard, `stratos-pr` body, risk label, draft gate) | medium | — | both edit 4a Phase 1/5 |
| I2 | S3: test cadence | medium | I1 | edits the 4a step-5 test line from I1 |
| I3 | S4: 3d plan phase | medium | I2 | both edit 3d Phase 3 |
| I4 | S2 + S10: 3z frontier, workspace and depth + AGENTS §8 nesting row | small | — | a few lines each, same guardrail theme |
| I5 | S6 + S11: environment-fix ladder (0b) + 4c guardrail and test-health lens | medium | I1 | 4c's "no guardrail" is ladder rung 1 at codebase level; 0b reads I1's `post_merge` |
| I6 | S7: 0d consolidation | medium | I5 | cites the ladder from I5 |
| I7 | S8: `contract_check.py` | medium | — | |
| I8 | S9: `2z-write-spec` | medium | I7 | |

The "Blocked by" column in the section table above is superseded by this table.

---

## 2. Slices

### S1 — 4a refuses unaudited changes; 3d clean-tree completion

**Problem.** In 4a Phase 2, targets are resolved via `git diff --name-only <merge-base>...HEAD` (committed changes only), and the Standards Auditor gets `git diff <base>...HEAD`. Phase 5 step 4 then commits and pushes *uncommitted* slice files as a "safety net", so those files ship **without being audited**. `3z` is unaffected, because Step 2A already requires a clean tree.

**Changes:**
- `4a` **Phase 1, new step 0** (before the Value-Add Gate bypasses, so the cosmetic/skip paths cannot ship uncommitted code either):
  > **Clean-tree guard (every gate, incl. `ship-only`):** run `git status --porcelain`. Any path outside `.memory/`, `docs/`, `.tmp/` → HALT: `[UNCOMMITTED] <paths> — commit via /3d-implement-issue first (or stash/remove unrelated files); 4a audits committed work only.`
  - It applies to **every** run: native, isolated, `audit-only` and `ship-only`.
  - `ship-only` is "Phase 5 alone" (3z Step 3A dispatches it), so it would skip Phase 1. Add to the Phase 5 named-gate line: "`ship-only` runs the Phase 1 step 0 clean-tree guard first."
  - Untracked files count: a never-added new source file is exactly the unaudited case. Generated output (`dist/`, `theme.tokens.css`) and lockfiles are not exempt; the producer (3d) commits them.
- `4a` Phase 5 step 4: the guard makes the "commit only uncommitted slice code+tests … Safety net for uncommitted slice files only" sentence dead. Replace it with "The clean-tree guard guarantees no uncommitted slice code; commit nothing here except the release bump." Keep verbatim: the release-bump sentence, "never sweep unrelated `.memory/`/`docs/` drift in", "(4a never creates the first commit; 3d owns commits.)" and "Push the branch." (`test_4a_runs_release_bump_before_push_when_repo_has_one` pins `scripts/release.py` before `Push the branch`).
- `3d` Phase 3: add item 5.
  > Done also requires `git status --porcelain` to show no path outside `.memory/`, `docs/`, `.tmp/` (all work committed per Phase 2.3).

**Tests:** add to `tests/workflows/test_ship_gate_wording.py`:
- 4a contains `git status --porcelain` and `[UNCOMMITTED]`. The guard text appears before `Context Isolation Rule`, and the Phase 5 named-gate block mentions the clean-tree guard.
- 3d Phase 3 contains `git status --porcelain`.

**Acceptance:**
- An edit to an uncommitted slice file makes 4a halt before any audit or ship step, under every named gate including `ship-only`.
- `check.sh` is green.

### S2 — 3z frontier skip

**Problem.** Phase 2 never re-checks blockers. A dependent of a slice that hit `status:blocked` still runs up to 3 implement+audit cycles.

**Changes in `3z`:**
- Step 2A: insert step 0 before "Activate Slice".
  > **Frontier check:** for each `Blocked by` entry of this slice, the blocker must be `VERIFIED`/`VERIFIED-LOCAL` in this run, or already `status:in review`/`status:done`. Otherwise emit `[SKIP-DEP] BT-<padded> waits on BT-<blocker>`, leave the slice's status unchanged (do **not** mark it blocked), log to `.tmp/3z-loop.work.md`, and continue.
- Loop "done when": add `SKIP-DEP` to the terminal states.
- Phase 4 report: list `[SKIP-DEP]` slices per feature.
- Step 3A: a feature with any `SKIP-DEP` slice stays local, like `blocked`.

**Tests:** new `tests/workflows/test_3z_frontier.py`: `[SKIP-DEP]` appears in Step 2A, in the terminal-state list and in Phase 4. Do **not** extend `test_3z_orchestrator_simulation.py`: its `MockOrchestrator` never reads `3z-afk-loop.md`, so a simulated skip would only test the mock.

**Acceptance:** wording tests green.

### S3 — Test cadence

**Changes:**
- **`src/skills/micro-tdd/SKILL.md`, Fast-Track A step 3 (REFACTOR):** replace "Run one full-suite sweep to confirm no regression across the remaining suite" with:
  > Run the tests **related to the changed files** using the runner's related/changed mode (e.g. `vitest related <files> --run`, `jest --findRelatedTests <files>`, `pytest` with `testmon`). With no such mode, run the touched test files. When the caller owns the full suite (a lifecycle workflow says so), stop here. Otherwise (standalone use) run the full suite **once** at the end of the task.

  This is an execution skill, so it stays generic: no `.tmp` paths and no workflow names.
- **`3d`:**
  - Phase 1 header: add one line, "3d owns the full-suite runs; micro-tdd runs related tests per cycle."
  - Phase 2.1 (code-simplifier): change "re-run the suite after" to "re-run related tests after".
  - Phase 2.3 (incremental commits): add "run related tests before each incremental commit; the full suite runs once, at the Phase 3 gate".
  - Phase 3 header: "Ephemeral (no writes)" → "Ephemeral (no tracked writes; `.tmp/` scratch only)". S3 and S4 both write `.tmp/` files here.
  - Phase 3: add a step **after** S1's item 5 (clean tree), so HEAD is final.
    > Run the full suite once at HEAD (the only full run in 3d). Write `{"head_sha", "cmd", "observed"}` (the observed summary line) to `.tmp/3d-suite-BT-<padded>.json`.
- **`4a` Phase 5 step 5**, observed-test requirement:
  > If any `.tmp/3d-suite-BT-*.json` has `head_sha` equal to `git rev-parse HEAD`, use its `cmd`/`observed`. Else run the suite once and write the result to `.tmp/3d-suite-BT-<padded>.json`, so a sibling ship at the same HEAD reuses it.
  - "Any" matters: in 3z, slices A and B are both committed before A ships, so A's file is stale; A's ship writes a HEAD result and B's ship reuses it. Step 4's `release: prepare` commit runs before step 5, so the result is always taken at the pushed HEAD.
  - No deletion: a stale file is harmless because of the sha check, and `.tmp/` is ephemeral (AGENTS.md §3).

**Tests:** new `tests/workflows/test_test_cadence.py`:
- micro-tdd no longer contains `full-suite sweep`, and contains `related`.
- 3d contains `.tmp/3d-suite-BT-<padded>.json`.
- 4a contains `.tmp/3d-suite-BT-` and `head_sha`.

**Manual validation (HITL, after merge, CleanTechHub; record in the PR or a `docs/research/` note):**
- Two `size:medium` slices, each run twice from the same base sha with the same host and model, both arms cold in a shared workspace: arm A = previous release, arm B = this one.
- **Pass:**
  - arm B makes ≤3 full-suite runs per slice
  - wall-clock is down ≥25%
  - no regression reaches CI that arm A caught earlier
- If it fails, revert micro-tdd step 3. This is a two-way door.

### S4 — 3d plan phase (default on)

**Changes in `3d`:**
- New **Phase 0.5: Plan**, after Phase 0 and before the TDD banner. **Skip only** for pure cosmetic slices (micro-tdd Fast-Track B scope); small slices get a short plan.
  - **HITL:** use the host's native planning mode where one exists (e.g. Antigravity `/plan`, Claude Code plan mode). Any approval prompt is the host's own; 3d adds **no** extra review halt.
  - **AFK** (dispatched by 3z): no approval.
  - **Always** persist the plan to `.tmp/3d-plan-BT-<padded>.md`.
  - **Required sections:**
    1. Files `[NEW]`/`[MODIFY]` with one-line intent.
    2. Seams to test.
    3. **AC → planned test path**.
    4. Existing tests at risk and how each stays green.
    5. Cross-cutting touchpoints (state/URL hydration, mocks/fixtures, env stubs needed for CI parity).
    6. Applicable `[[L/A/DR/G-xxx]]`.
    7. Open decisions.
  - **Mechanical plan check** (agent-run, not a script): derive the repo's test-file naming pattern(s) from `git ls-files` (existing test paths). Every planned test path must match one, and every AC must have one. Any miss → fix the plan before Phase 1.
  - The plan file is `.tmp/` scratch: nothing deletes it (3z's Phase 4 report lists it after ship), and a missing file downstream means `deviations: []`.
- Phase 1: micro-tdd "Declare Seam" takes the seams from the plan.
- Phase 3: compare the coverage map with the plan's AC → test list. Name every deviation, and write deviations to a `## Deviations` section of the plan file (S5 reads it).

**Changes in `3z`:**
- Step 2A dispatch JSON gains `"plan_path"`.
- The Phase 4 report lists `plan_path` per slice next to `docs_read`.

**Tests:** extend `tests/workflows/test_test_cadence.py` or add `test_3d_plan_phase.py`:
- 3d has `Phase 0.5`, `.tmp/3d-plan-BT-<padded>.md`, and the AC → test check wording.
- The 3z JSON template contains `plan_path`.
- **Do not** assert host-specific tool names.

**Manual validation (HITL, CleanTechHub):** a clean re-run of the BT-221/222 experiment.
- **Protocol:** same base sha, both arms cold, `node_modules` pre-installed, model recorded.
- **Measure:**
  - tokens from host usage
  - wall-clock including the plan step
  - AC coverage scored by an independent `4a audit-only`
  - regressions to existing tests
  - follow-up commits within 48h
- **Keep the default** if it is not worse on tokens and time and is better on at least one quality metric. Otherwise add a size gate.

### S5 — 4a minimal agent-first PR body + risk label + draft gate

**Changes in `4a` Phase 5:**
- **Step 5 body spec:** replace the ingredient list ("one-line slice summary, design doc link…, the AC↔test coverage table… `[ ] Manual QA Required`…") with this exact shape:

  ````text
  Closes #<n>.                ← one line per shipped slice (+ parent, see step 8); keep this literal form

  ```stratos-pr
  feature: BT-<parentPadded>
  head: <sha>
  slices:
    - {id: BT-<padded>, summary: "<one line>", verdict: PASS|WAIVED|SKIP|PENDING, audit_rounds: <n>}
  test: {cmd: "<cmd>", observed: "<observed summary line>", at: <sha>}
  risk: [<tags>]              # from references/merge-risk-paths.md; [none] if no rule fires
  post_merge: ["<manual step>", …]   # [] if none; manual-QA items go here
  deviations: ["<decision not in issue/design>", …]   # from the 3d plan's ## Deviations
  refs: [<only IDs that constrained the change>]
  ```
  ## Notes   (optional; bug fixes: root cause only)
  ````

- **`slices` is rebuilt on every create/update**, never appended.
  - **ID set:** `git log --no-merges --format=%s <base>..HEAD`, with `<base>` resolved exactly as in Phase 2 ("Resolve targets first"). Collect the scope of every subject matching `^[a-z]+\(BT-(\d+)\):`. Unscoped commits (`release: prepare …`, `fix(ci): …`, `chore: …`) are ignored. Verified: CleanTechHub PR #158 (`39efc6e^1..39efc6e^2`) yields exactly 9 scopes.
  - **Per-slice fields:** the slice being shipped gets its fresh values. Every other ID keeps `summary`/`verdict`/`audit_rounds` from the existing PR body's `stratos-pr` block (`gh pr view <n> --json body`). An ID with commits but no prior entry (committed by 3d, not yet through 4a) gets `verdict: PENDING`.
  - **Verdicts:** `PASS` = audited clean; `WAIVED` = shipped on user authorization over gaps (Phase 4); `SKIP` = audit bypassed by the Value-Add Gate (Phase 1 step 1 or 3).
  - **`Closes` lines** are regenerated from the IDs whose verdict is not `PENDING`, plus `Closes #<parent>.` once step 8 has fired. `<n>` is the BT number (BT ids are zero-padded issue numbers).
  - Today's step-5 text "(the slice, and the parent)" changes accordingly: the parent line is added only at step 8.
  - A `ship-only` run never audited, so it cannot know `verdict`/`audit_rounds`. **`3z` Step 3A** passes them in each `ship-only` dispatch: the Step 2C verdict and the final `attempt`, plus `needs_manual_qa` → a `post_merge` item.
- **Keep unchanged:**
  - `--body-file .tmp/4a-pr-body-BT-<padded>.md` and its `rm -f`
  - the `closingIssuesReferences` read-back
  - `[NO-AUTOCLOSE]`
  - the exact `Closes #<n>.` form (pinned by `test_ship_gate_wording.py`)
- **Remove:**
  - the "add a comment noting the re-verification" clause (no consumer)
  - the AC↔test table, design-doc link and manual-QA checkbox from the **body**; the Phase 3 output to the user is unchanged
- **New `src/references/merge-risk-paths.md`:** glob rules matched against `git diff --name-only <base>...HEAD` → risk tags. **Path rules only, no agent judgement** (proposal §1.3). The project may extend it with `<glob> → <tag>` lines in `.memory/ARCHITECTURE.md` under a `## One-way paths` heading.

  | Path rule | Risk tag |
  |---|---|
  | `**/*.sql`, `**/migrations/**` (covers `schema.sql`, grants/RLS SQL) | `db-migration` |
  | `.github/workflows/**` | `ci` |

  The draft's "removed exported symbol" and "scripts that write to live systems" rows are cut: neither is a path rule. A project lists its live-write scripts under `## One-way paths`.

  Any tag other than `none` → apply the label `risk:one-way`, and name it in the step-10 output line. Ensure the label exists first, per the BACKLOG rule "registry but not GitHub → create it before use": `gh label create risk:one-way --force --description "Hard-to-reverse change; human must read before merge"`, then `gh pr edit <n> --add-label risk:one-way`. `gh pr edit --add-label` fails on a missing label.
- **Step 8 (Epic Check):** when it fires, add `Closes #<parent>.` to the body, `gh pr edit --body-file`, then re-run the closing-link read-back for the parent. Today the parent link was missing on CleanTechHub #192 and #225.
- **Step 9 (terminal gate):** after `reconcile.py` passes, add a draft-rule assertion (skip for a standalone issue or `local-only`). If any BACKLOG row with `Parent = BT-<parent>` is not `in review`/`done` (the mirror was just verified), the PR **must** be draft (`gh pr view <n> --json isDraft`). If it is not draft, heal once with `gh pr ready <n> --undo` and re-check; still not draft → halt `[DRAFT-RULE]`.

**Label registry:**
- Add a line to the `label-canonical` block in `src/memory-templates/BACKLOG_MAP.md`, and bump the block's `v=`:
  > **Risk (`risk:xxx`)**: `risk:one-way` (PR contains a hard-to-reverse change per `merge-risk-paths.md`; a human must read it before merge).
- No test or sync changes are needed. `tests/framework/test_status_label_contract.py` pins only `status:*`, and no scaffold label sync exists: labels are created on first use, which is why step 5 runs `gh label create --force`.
- Add the label to this repo's `.memory/BACKLOG_MAP.md` registry.

**Tests (`test_ship_gate_wording.py`):**
- 4a contains ```` ```stratos-pr ````, `risk:one-way`, `gh label create`, `references/merge-risk-paths.md`, `git log --no-merges` (slice rebuild), `PENDING` and `[DRAFT-RULE]`.
- 4a no longer contains `noting the re-verification`.
- The existing `Closes #<n>.` / `closingIssuesReferences` / `[NO-AUTOCLOSE` asserts still pass.
- The build ships `merge-risk-paths.md` into `4a`'s `references/`.

**Acceptance:**
- Replaying CleanTechHub PR #158's commit list (`git log --no-merges --format=%s 39efc6e^1..39efc6e^2`) through the spec yields 9 slices in the body.
- A diff touching `docs/database/x.sql` yields `risk: [db-migration]` and the label.

### S6 — 0b destination ladder, friction gate, cap, `post_merge`, ID lint

**New `src/references/environment-fix-ladder.md`** (cited by `0b` and `0d`):
- **Rungs:** route each candidate lesson to the **first** rung that fits:
  1. **Deterministic check:** lint, test, setup file, CI, hook, or `validate_memory.py`. Wire an existing check before inventing one.
  2. **Reviewer standard:** a rule read by the 4a Standards Auditor (`CODING_STANDARDS.md` → `[[A-xxx]]` → `code-smell-baseline.md`), not loaded into implementers. Write the bare filename: a `references/…` prefix would fan that file out into 0b/0d.
  3. **Existing law already covers it:** cite it and write nothing.
  4. **Framework issue:** host or agent tooling behaviour (shell quoting, tool misuse, re-reads). File it against StratOS, not the project.
  5. **Issue / `STATUS.md`:** in-flight state (the existing durability gate).
  6. **`LEARNINGS.md`:** only if durable, non-mechanical, needed while implementing a *different* slice, and backed by evidence (bit ≥2× or cost real time; cite the session moment or commit).
- **Escalation:** a recurrence of an existing LEARNINGS lesson must go to rung 1 or 4, never a new or duplicate entry.
- **Evidence rule:** every candidate cites a concrete session moment; discard any that cannot.
- **Hypothesis rule:** a root cause is stated as a hypothesis until verified.

**`0b` changes:**
- **Step 3 → friction gate.**
  > Run steps 3–4 only if this session hit friction: a failed approach, a costly wrong assumption, a defect fixed, or a reviewer/audit catch. Else skip silently. For each defect fixed, ask "what would have prevented it?". Route every candidate per `references/environment-fix-ladder.md`.
- **Step 4:**
  - Keep the durability gate, proposal format, `[ASSUMED]` default and "never self-write" verbatim.
  - Add: **at most one** LEARNINGS proposal per session unless the user asks for more.
  - Add: removal of an entry is via `## Superseded` (a one-line tombstone is allowed); IDs are never reused.
- **Step 1 (done detection):**
  > For each issue detected done this step, take the PR from its `Shipped in PR #<pr>` comment (4a step 6); dedupe PRs. Read each PR's `stratos-pr` block (`gh pr view <pr> --json body`; no block → skip). For each `post_merge` item, propose a follow-up issue (title + one-line body). On confirmation only, create it with a registry-complete label set: `type:maintenance`, `mode:HITL`, `tier:slice`, `size:small`, `status:planned`. Mint it atomically and add its BACKLOG row.
  - A label set of only `type` + `status` would break the BACKLOG Label Composition Rule.
- **Handoff Note Format:** add `Follow-ups proposed:`.

**`src/rules/memory-protocol.md` §3 (Supersession):** add one sentence. IDs are never reused. An entry removed without a successor stays as a one-line tombstone under `## Superseded`: `- **[[L-xxx]] [REMOVED] [YYYY-MM-DD]** Reason: <one line>.` (The file has no "ID section"; §5 already forbids deleting to supersede.)

**`src/scripts/validate_memory.py`:**
- Duplicate `[[X-nnn]]` definitions are **already an error** across all memory files (`validate_memory.py` ~L313, "Duplicate ID definition"). Add a regression test only; no code change.
- **Accept the tombstone:** today a `## Superseded` entry without a `[SUPERSEDED BY [[ID]]]` target is an **error** (~L468–470). Treat `[REMOVED]` as a valid terminal marker there.
- **Warning (not error,** because existing projects have gaps from past hard-deletes): ID gaps in `L-`/`G-`/`A-`/`DR-` sequences (placeholders such as `L-XXX` excluded), reported as `possible hard-delete: L-018..L-021 missing — add [REMOVED] tombstones to silence`. Warnings exit `2` (or `1` with `--warnings-as-errors`), and `test_fresh_scaffold_lint` requires a fresh scaffold to exit `0`. The placeholder exclusion keeps that green.
- Bundled-script rules apply (§0.4): add the v4.3.0 hash.

**Tests:**
- `tests/framework/test_validate_memory_ids.py` (new): duplicate ID → exit 1; gap → exit 2 with the warning and no error; `[REMOVED]` tombstone → no error and closes the gap.
- `tests/workflows/`: 0b cites `references/environment-fix-ladder.md`, contains `post_merge`, and contains the one-proposal cap.
- The build ships the ladder into `0b` (S7 adds `0d`'s citation and asserts it there).

**Acceptance:** classifying CleanTechHub's 10 active LEARNINGS entries (as of 2026-10-05; L-012 is now superseded) with the ladder routes ≥4 away from LEARNINGS:
- L-004/L-007/L-008 → rung 1
- L-009 → rung 2
- L-017 → rung 3
- L-013/14/15 → rung 4

### S7 — 0d: drift-only advisor, scripted indices, sampling, slim watermark

**`src/scripts/reconcile.py`:**
- Add `--all-open`: ids = every BACKLOG row whose status ≠ `done`. Today `--ids` is `required=True` (~L151), so make the two a **required mutually exclusive group**.
- `--all-open`-only checks, so the in-band gates (4a/3a/3b/3c call `--ids`) keep their exact semantics:
  - **Stale blocker:** a `Blocked by` entry whose own row is `in review`/`done` → `[MIRROR-DRIFT BT-x: stale blocker BT-y should be cleared]`. This is a BACKLOG-only check, so it also runs on the offline (`[local-only]`) path, which today returns before any per-id work.
  - **Closed on GitHub:** add `state` to the fetched fields under `--all-open`. An issue that is `CLOSED` while its row is not `done` → `[MIRROR-DRIFT BT-x: closed on GitHub, map=<status>]`. This is the most common post-merge drift, and per-field compare cannot see it (the labels still say `in review`).
- Keep `compare()` pure, and keep the exit codes (0 ok / 1 drift / 3 `--require-gh` unverified; `references/terminal-sync-invariant.md`).
- **Cost:** about 3 `gh issue view` calls per open row (core + `blockedBy` + `parent`). CleanTechHub has 53 open rows today (~160 calls, a few minutes): fine for 0d, never for an in-band gate.
- Bundled-script rules apply (§0.4): add the v4.3.0 hash.

**`src/scripts/okf_view.py`:** add `--rebuild-indices`, implementing today's 0d Phase 3.5 spec deterministically:
- For `.memory/` and each `docs/` subdir (`prds/`, `discovery/`, `research/`, `design/`, `knowledge/`, `nightly/`), rebuild `index.md` as `* [Title](/path.md) - description` from frontmatter.
- `docs/knowledge/` gets one entry per source bundle.
- Print `N indices rebuilt`.
- Bundled-script rules (§0.4): the v4.3.0 hash is already in the map, so there is nothing to add.

**`0d` changes:**
- **Frontmatter `description`:** "check roadmap health" → "check backlog drift".
- **Phase 1:**
  - Apply `references/environment-fix-ladder.md` (escalation + hypothesis rules).
  - **Sampling:** if the delta has more than ~15 sessions, review the 5 with the most failed tool calls plus 3 random others, and state the sample.
  - Drop the session roster and "positive observations" from the report.
- **Phase 2:**
  - `.last-run.json` stores `{"last_run": …}` only (remove `sessions_reviewed`).
  - Before proposing, read the `## Decisions` sections of the retained `docs/nightly/` reports: an item the user **declined** is not re-proposed without new evidence. Accepted-but-undone items may be re-proposed. Read only `## Decisions`, not the proposal text: Phase 1 still forbids anchoring on old proposals.
- **Phase 4:** after the user answers, append `## Decisions` (one line per item: `accepted` | `declined`) to that night's report. Without this, "declined" has no data source.
- **Phase 3:**
  - The `[ASSUMED]`-age test cannot count "sessions": nothing records them. Measure age from the entry's inline `[YYYY-MM-DD]` (LEARNINGS template format) and flag `[ASSUMED]` entries older than **7 days** *(threshold: user decision)*. L-017 (`[ASSUMED] [2026-09-22]`) must be caught.
  - The trigger table's `[ASSUMED]` row proposes "Supersede with a `[REMOVED]` tombstone?" instead of "Delete?". Deletion creates ID gaps and violates memory-protocol §5.
- **Phase 3.5** → `python .agents/scripts/okf_view.py --rebuild-indices`; the report gets one line.
- **Phase 3.6** → rename to **Backlog Drift Check**. Run `python .agents/scripts/reconcile.py --all-open` (no `--require-gh`: 0d is advisory, and without gh the script itself prints `[local-only — GitHub not checked]`). Print its findings verbatim.
- **Delete:** the recommendation table, the "also pending" list, the ROADMAP/`/3a` signals, the completion criterion that requires a recommendation, and the enrich-from-GitHub / stale-blocker prose now covered by the script.
- Keep one guard sentence: "This phase invokes no lifecycle skill."

**Tests:**
- Unit tests for `--all-open` (incl. the mutually exclusive group), stale blocker (online and offline paths) and closed-on-GitHub, in `tests/workflows/test_reconcile.py`. The existing `--ids` tests stay green unchanged.
- Unit test for `--rebuild-indices` on a tmp tree.
- 0d wording: no `Recommendation (evaluate in this order`; contains `--all-open`, `--rebuild-indices`, `## Decisions` and `references/environment-fix-ladder.md`.
- `tests/install-harness/run-L2.py` still finds `docs/nightly/index.md`.

**Acceptance:**
- Automated: the unit tests above.
- Manual (HITL, CleanTechHub): a 0d run emits drift lines only and no recommendation table. The report is ≤40% of the bytes of the previous release's report on the same delta.

### S8 — `contract_check.py` shared by 2a/2b/2c

**New `src/scripts/contract_check.py`** (bundled; §0.4: add it to `get_bundled_project_scripts()` and the `verify_scripts.py` mapping):
- **Input:** `--docs <paths>` (PRD, design doc) and `--schema .memory/DATABASE_SCHEMA.md` [`--sql <schema.sql>` when the project declares one].
- **Parse the schema source:** tables, columns, enum types/values, FKs, views (and their dependency order from `--sql` when given).
- **Extract references from the docs**, in backticked code spans and code blocks only:
  - `x.y` where `x` **is a known table** → `y` must be a column of `x`. Unknown `x` is ignored: `api/submit.js`, `schema.sql` and `foo.bar()` look identical to `table.column`.
  - An enum literal is checked **only when bound** in the same span/line to a known enum type, or to a column whose type is that enum (`employment_type = 'intern'`, `employment_type: 'intern'`). A free-floating `'intern'` is ignored.
  - Bare words are never reported as missing tables: there is no way to tell a table name from any other identifier.
- **Report** each unresolved reference as `[CONTRACT-MISSING] <doc>:<line> <ref> (<kind>, <source>)`. With `--sql`, a reference must resolve in **every** given source, and `<source>` names the one it is missing from. Exit non-zero if any are found.
- **No schema declared** (`DATABASE_SCHEMA.md` still holds only the template's `table_name` placeholder, and no `--sql`) → print `[CONTRACT-SKIP] no schema declared` and exit 0. Most consumer projects (and StratOS itself) have no DB.
- Be conservative: anything the parser cannot classify is ignored, not reported. Precision matters more than recall; 2c still reasons over the rest.
- **First step of the slice (spike-like):** read the CleanTechHub `.memory/DATABASE_SCHEMA.md` (`### \`table\`` headings, `- \`col\`:` bullets, prose enum lists) and `docs/database/schema.sql` (737 lines, read-only) to fix the parse format, and record it in the script docstring.

**Workflow wiring:**
- **`2a` Phase 4 (Validate):** add a checkbox.
  > `python .agents/scripts/contract_check.py --docs <prd> --schema .memory/DATABASE_SCHEMA.md` passes, or each finding is written as `> open:`.
- **`2b`:** the same check before Phase 5, over PRD + design doc.
- **`2c`:** Scan Matrix item 1 "Contract existence" becomes "run `contract_check.py` over all resolved artifacts; each `[CONTRACT-MISSING]` is a P0/P1 finding; reason only where the script cannot answer". Keep the auditor guardrail verbatim.

**Tests:** `tests/scripts/test_contract_check.py` with a fixture schema plus a PRD referencing a missing column, an invalid bound enum value and an FK to a missing column. All 3 must be flagged. A valid reference, an unbound literal and a filename like `api/submit.js` must not be. Also test the template-only schema → `[CONTRACT-SKIP]`, exit 0.

**Acceptance:** on CleanTechHub's BT-161 / BT-168 artifacts **as they stood when 2c audited them**, the script flags the findings 2c reported by hand that are **mechanically decidable**. Extract each file with `git -C <CleanTechHub> show <sha>:<path>` into this repo's `.tmp/`, taking `<sha>` from before each report's fixes landed. Current `schema.sql` already declares `consecutive_missing_scans`, so HEAD no longer reproduces P1-4.
- `.tmp/BT-161-slicing-readiness.md` **F-3** (`employment_type` `'intern'` not in the enum)
- `.tmp/BT-168-slicing-readiness.md` **P1-4** (`jobs.consecutive_missing_scans` absent from `schema.sql`, with `--sql`)

Out of scope, and left to 2c's reasoning:
- **F-1**: seeded FK *values* versus code in `taxonomy.js`; a data/code question, not schema existence.
- **P1-2**: the reverse direction, schema doc columns that no artifact creates.

### S9 — `2z-write-spec` orchestrator

**New `src/workflows/2z-write-spec.md`**, a lifecycle skill:
- **Frontmatter** like `1c`: `disable-model-invocation: true`, `triggers: ["user"]`, `metadata: {stratos.layer: lifecycle, stratos.mode: HITL}`, `version`, `timestamp`, and a description restating that it is user-invoked only (Antigravity honours no field). Do **not** author `agents/openai.yaml`: `build/build.py` `emit_skill` generates it for every skill whose frontmatter has `disable-model-invocation: true`.

**Body (thin; invokes units by name, never duplicates their bodies; AGENTS.md §1 orchestrator rule):**
- **Phase 0:**
  - `load-memory` **once**. State that the units' own Phase 0 `load-memory` is already satisfied under 2z.
  - **Resume detection:** if the PRD `docs/prds/BT-<padded>-*.md` exists → start at Phase 2. If the design doc is `status: stable`, or 2b's skip path already promoted the epic to `planned` → start at Phase 3.
  - Create the decision log `.tmp/2z-BT-<padded>-decisions.md` (`.tmp/2z-<slug>-decisions.md` before 2a mints the ID; rename it after minting). It is the decision record that resume and the hand-off read.
- **Phase 1: run `/2a-write-prd`.**
  - HITL questions and the cost gate stay in the main thread. Append each decision to the log.
  - 2a commits the PRD (one document per run, AGENTS.md §4).
- **Phase 2: run `/2b-interface-design`.**
  - Honour 2b's skip path and the Path A pause. On a Path A pause, 2z halts with a resume note; re-invoking `/2z-write-spec BT-<n>` resumes at 2b (resume detection above, then 2b's own Phase 1 resume check).
  - The HITL pick stays in the main thread. 2b commits the design doc.
- **Phase 3: run `/2c-reconcile-specs` in the main thread.** 2c's own Context Isolation Rule (Phase 2) sees that this session authored the artifacts and isolates the scan to its Spec-Reconciliation Auditor subagent (depth 1). Its Phase 4 HITL (present, Skip, apply) stays in the main thread. Do **not** wrap 2c itself in a subagent: a subagent cannot run 2c Phase 4's HALT for user Skips.
  - 2c's spec edits stay uncommitted on the default branch (unchanged 2c behaviour; AGENTS.md §4 allows 2a/2b/3a only). Say so in the hand-off.
- **Phase 4: hand-off line**, identical to 2b's routing (→ `/3a` or `/3b`).
- **Depth:** at most 2 levels below the 2z session (S10). Each subagent step runs inline when the host has none.

**Keep `2a`/`2b`/`2c` standalone and unchanged**, except S8's checks. Add one line to **2a's** hand-off (Phase 5 step 7): "or run `/2z-write-spec BT-<padded>` to chain 2b → 2c". 2b's and 2c's hand-offs point past the chain, so they get nothing.

**Registering a new lifecycle skill** (the build auto-globs `src/workflows/`, but these pin the count or list):
- `src/scripts/check_suite.py` `LIFECYCLE_SKILLS`: add `2z-write-spec` (drift-guarded by `tests/scripts/test_check_suite.py::test_hardcoded_lifecycle_list_matches_bundle_frontmatter`).
- `tests/scripts/test_check_suite.py`: `22/22` → `23/23`, `15/22` → `16/23`, `== 22` → `== 23`, plus the ~L388 docstring.
- `tests/framework/test_dist_bundle.py` `EXPECTED_SKILLS = 26` → `27`, plus the "26" docstrings.
- `src/commands/stratosphere-setup/SKILL.md`: "22 bundled skills" ×3 → 23 (version bump).
- `README.md`: the "26 skills" mentions → 27, and a `2z` row in the workflow table.
- `3z` Authority line "`1c` is user-invoked discovery orchestrator": append "; `2z` is the user-invoked spec orchestrator".

**Tests:**
- `tests/framework/test_skill_conformance.py` passes for the new lifecycle skill (frontmatter, generated sidecar).
- A wording test: 2z names `2a-write-prd`, `2b-interface-design` and `2c-reconcile-specs`, and contains no copied phase bodies (e.g. assert it does not contain `ATOMIC MINTING RULE`).

**Acceptance:**
- Automated: the tests above and `check.sh` green.
- Manual (HITL, on a scratch feature): a run commits exactly 2 documents (1 when 2b takes its skip path), leaves a decision log, and 2c's scan runs in its isolated auditor subagent. A re-invocation after a Path A pause resumes at 2b.

### S10 — Subagent nesting contract + 3z workspace and depth

**Changes:**
- **`src/constitution/AGENTS.md` §8** (product) **and** the repo's root `AGENTS.md`: add a short paragraph "Subagent nesting". The two files are identical apart from the Vision line, so the same edit applies.
  > Design budget: depth ≤ 2 below the invoking session (leaves one level for an outer orchestrator; Claude Code default 3, Antigravity max 10, Cursor 2, Codex 1, Gemini CLI none). Every subagent step must also run inline. Subagents never commit, except a `3d` implementer dispatched by `3z` (the §4 single writer for code). Auditors, drafters and scanners are read-only. Prefer workspace `shared/inherit` for sequential work; worktree isolation branches from the default branch on Claude Code and lacks untracked deps (e.g. `node_modules`).
  - The draft said "only 3d commits", which is false: 2a/2b/3a commit docs and 4a commits the release bump (§4).
  - Bump the constitution `version` (minor). `scaffold --update` never overwrites the constitution; existing projects get it as `needs_review`.
- **`3z` Authority & Guardrails:** add two bullets.
  - **Workspace:** dispatch 3d/4a subagents with workspace shared/inherit (not worktree), and state why in one line (3d's commits, and the `.tmp/` plan and suite files, must be visible to the next step).
  - **Depth:** 3z → 3d/4a subagent → at most one further level.

**Tests:** a wording test asserts that 3z contains `shared/inherit` and the depth budget, and that both `src/constitution/AGENTS.md` and root `AGENTS.md` contain `Subagent nesting`.

### S11 — 4c guardrail and test-suite-health lens

**Where:**
- The scan matrix is not in `4c` itself. It lives in `src/references/health-audit-scan-matrix.md`, which 4c's subagents read by absolute path. Add both checks to **B2 — Correctness (Test Coverage)** (Quality Auditor) and bump the reference `version`.
- Scanners only read the explicit file list the parent passes, never sweep. So 4c Phase 1 must add the guardrail inputs to the Quality Auditor's list: `.github/workflows/*`, hook config (`.husky/`, `.pre-commit-config.yaml`, `lefthook.yml`), the package manifest/test-runner config, and a runner summary if one exists in `.tmp/`.
- Keep the existing scanner guardrails verbatim.

**Checks:**
1. **Guardrail:** no pre-commit hook **and** no CI job running lint/typecheck/test → finding. A check script that exists but is not wired into CI → finding: "wire it".
2. **Test-suite health:** config-level, always checkable, flag:
   - duplicate CI triggers for the same commit (push + pull_request without a `concurrency` group)
   - no related/changed test mode configured

   Only when the parent passed a runner summary, also flag environment+import time greater than test time.

**Tests:** a wording test asserts the two check names are present in `src/references/health-audit-scan-matrix.md`, and that 4c Phase 1 names `.github/workflows`.

---

## 3. Definition of done (feature)

- **Build and checks:** all slices merged on the feature branch, and `bash scripts/check.sh` → `ALL CHECKS PASSED`.
- **Dist:** `dist/` is in sync.
- **Versions:** bumped once per changed `.md` file; block `v=` bumped for `label-canonical`.
- **Release:** `python scripts/release.py -y` run once (4a step 4).
- **Manual validations:** the S3, S4, S7 and S9 manual validations are scheduled as follow-up work in CleanTechHub. They are not CI.
- **Proposal:** `docs/proposals/FEAT-pocock-v1-3-learnings-proposal.md` is moved to `docs/proposals/.archive/` in the feature branch's last slice commit, before ship. After merge, no workflow may push to the default branch (AGENTS.md §4).

## 4. Out of scope

- **Dropped after review:**
  - parallel frontier execution
  - a deterministic 3z driver
  - Skill-tool invocation wording
  - Summary visuals / a `pr-body` skill
- **CleanTechHub-local fixes** (tracked there):
  - node-default Vitest env
  - CI concurrency group
  - `afterEach(cleanup)` in setup
  - stranded post-merge migrations (#175, #192)
  - the open `[DRIFT]` rows
  - LEARNINGS cleanup
