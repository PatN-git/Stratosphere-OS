---
type: design-doc
title: "Master plan — lifecycle status + load-memory skill + trigger harmonization (single MAJOR release)"
status: ready-to-implement
timestamp: 2026-07-17
---

# Master Plan — one MAJOR release combining three approved plans

This master plan merges three independently-approved plans into a single, phased,
executable release. They are combined because **Plan C (lifecycle status) is locked to a
MAJOR bump and explicitly requires being batched with the other all-files changes under
ONE `VERSION` bump and ONE `build.py` run** (Plan C §Handoff). The three sources:

- **Plan A — Trigger semantics harmonization** (`harmonize-trigger-semantics-plan.md`) — rules ↔ workflows `trigger` enum, host-conditional rule placement, validate.py enforcement.
- **Plan B — Context-hydrate skill + lean 0a + docs/memory backup** (`context-hydrate-guard-plan.md`) — new read-only skill (**renamed `load-memory`** per feedback; Plan B calls it `context-hydrate`), 0a refactor, Phase 0 in lifecycle workflows, doc-commit owner, installer gitignore hygiene.
- **Plan C — Lifecycle status + BACKLOG schema** (`lifecycle-status-and-backlog-schema-plan.md`) — unified status state machine, `status:in review`, doc-frontmatter editorial vocab, BACKLOG `Parent`/`Blocked by` split. **MAJOR.**

**The individual plans remain the source of truth for exact edit text.** This document
sequences them, resolves overlaps, and guarantees each file is touched once per pass with a
single version bump. Where a section says "per Plan X §Y", apply that plan's exact edit.

---

## Global reconciliation (read before starting)

| Concern | Plan A | Plan B | Plan C | **Resolved for master** |
|---|---|---|---|---|
| Plugin `VERSION` | 2.2.0 (unchanged) | 2.2.0 (unchanged) | **MAJOR → 3.0.0** | **3.0.0** — MAJOR wins; set once in Phase 5. |
| `build.py` run | once at end | once at end | **once, batched** | **Exactly one** `build.py` run (Phase 5). |
| Per-file bump | patch each | ~15 bumps | bump each touched `src/**` | **One bump per file per pass**, magnitude ≥ largest change to that file. Do NOT double-bump files touched by multiple plans. |
| Branch | (n/a) | `feat/context-hydrate-and-backup` | single MAJOR branch | **One combined feature branch** (see Phase 0). |
| Migration | (n/a) | (n/a) | one-shot external, after ship | **Phase 7**, after build+verify. |

**In-flight working tree (must resolve in Phase 0):** the tree already carries uncommitted
v2.2.0 prep (`M dist/**`, `M build/build.py` VERSION=2.2.0, `M src/rules/*`, `M README.md`
badge=2.2.0, `M src/workflows/0b_stop-session.md`), plus the three plan drafts in
`docs/plans/`. Because Plan C forces MAJOR and `build.py` regenerates all of `dist/`,
building on top of a half-staged 2.2.0 mixes changesets. **This is the one open decision —
see Phase 0, D0.** Everything downstream assumes a clean branch off a committed base.

### Overlap map (files touched by >1 plan — apply union, bump once)

| File | A | B | C |
|---|:-:|:-:|:-:|
| `src/rules/okf-protocol.md` | ✅ §2.1 activation contract + `paths` superset | | ✅ §2 doc-status vocab line |
| `src/rules/memory-protocol.md` | ✅ `trigger: always_on` | | ✅ §8 `Parent` col, §2 bare-ID note |
| `src/rules/output-mode.md` | ✅ `always_on`, drop `globs` | | |
| `src/workflows/0a_start-session.md` | ✅ `trigger: manual` | ✅ Phase A/B refactor | ✅ first-slice epic rule, add `in review` to removal set |
| `src/workflows/2a_write-prd.md` | ✅ trigger | ✅ Phase 0 + B1 doc-commit | ✅ epic `needs_spec`, PRD `draft`, `Parent = —` |
| `src/workflows/2b_interface-design.md` | ✅ trigger | ✅ Phase 0 + B1 doc-commit | ✅ design `approved`, epic→`planned`, skip-path promotion |
| `src/workflows/3b_create-issue.md` | ✅ trigger | ✅ Phase 0 | ✅ slice born `planned`, defensive epic promote, `Parent`/`Blocked by` cols |
| `src/workflows/3c_sprint-planning.md` | ✅ trigger | ✅ Phase 0 | ✅ `tier:slice AND status:planned`, 9-col header |
| `src/workflows/3d_implement-issue.md` | ✅ trigger | ✅ prepend skill to Phase 0 | ✅ first-slice rule |
| `src/workflows/4a_verify-and-ship.md` | ✅ trigger | ✅ Phase 0 memory-only | ✅ step 6 `in review`, step 7 gate, hand-off line |
| `src/workflows/3z_afk-loop.md` | ✅ trigger | (excluded from Phase 0) | ✅ terminal set incl. `in review` |
| `src/workflows/0b_stop-session.md` | ✅ trigger | ✅ Phase 0 | ✅ `done` = closed/merged |
| `src/workflows/0d_nightly-consolidation.md` | ✅ trigger | ✅ Phase 0 | ✅ extend Phase 3.6 drift check |
| `src/workflows/3a_version-planning.md` | ✅ trigger | ✅ Phase 0 | ✅ 9-col header refs |
| `src/workflows/1b_concept-framing.md` | ✅ trigger | ✅ Phase 0 memory-only | ✅ discovery-brief status vocab |
| `src/workflows/1a_research.md`, `1c_concept-map.md`, `0c_handoff.md`, `x_jules-dispatch.md` | ✅ trigger | ✅ Phase 0 | |
| `src/workflows/4b_audit-architecture-drift.md` | ✅ trigger (insert after `type:` — has none) | ✅ Phase 0 standard | |
| `src/references/PRD-template.md`, `design-doc-template.md` | | | ✅ editorial status vocab |
| `src/memory-templates/BACKLOG_MAP.md` | | | ✅ `status:in review` + 9-col schema |
| `src/scripts/scaffold.py` | ✅ host-conditional placement | | |
| `build/validate.py` | ✅ §2.6 enum enforcement | | |
| installer (`Instantiate-StratosphereOS.md`) | | ✅ gitignore `.memory/STATUS.md` | |
| `AGENTS.md` (constitution + repo-root) | ✅ §8 host-activation bullet | | |
| **new** `src/skills/load-memory/SKILL.md` | | ✅ create | |

**Ordering rule:** for every workflow above, apply Plan B's Phase 0 block **and** Plan C's
status/schema edits **and** Plan A's `trigger: manual` in a single edit pass, then bump that
file's `version:` exactly once. `build/validate.py` §2.6 (Plan A, Phase 4) will reject any
workflow that is not `trigger: manual`, so no workflow may be skipped.

---

## Phase 0 — Prerequisites, branch, discovery

**D0 (RESOLVED — fold into 3.0.0):** commit/absorb the in-flight working-tree v2.2.0 prep onto a clean base, then let this combined change carry `VERSION 3.0.0` as one MAJOR release. No orphan 2.2.0 tag. Matches Plan C's single-MAJOR-bump mandate.

**Steps:**
1. Resolve D0; get to a clean, committed base on `main`.
2. Create the single combined feature branch, e.g. `feat/lifecycle-context-triggers` (no parent BT epic; standalone infra change per constitution §4 → own branch + PR).
3. **Pre-flight discovery greps** (Plan C §Pre-flight — file lists in all three plans are "known hits, not guarantees"). Fold any stragglers into the right phase:
   ```
   rg -n "Dependencies|Sub-?issue of"          src/
   rg -n "ready-for-slicing|ready-for-design"  src/
   rg -n "status:in progress|status:needs_spec|status:planned|status:blocked|status:done" src/
   rg -n "in-progress|complete|obsolete"       src/references/
   rg -n "^trigger:"                            src/workflows/ src/rules/
   ```
4. Confirm current `version:` of every file in the overlap map (Plan B warns bases drifted with Jul-17 edits — **read actual values, do not trust the plans' base numbers**).

---

## Phase 1 — Shared contracts (rules, OKF, templates)

Foundation edits other phases reference. One bump per file.

1. **`src/rules/okf-protocol.md`** — apply **Plan A Step 1** (frontmatter `paths` superset alongside `trigger`/`globs`; new **§2.1 Activation contract** for the shared `trigger` enum; §3 type-registry rows for `rule`/`workflow`) **and Plan C Workstream B** (one line under §2 documenting canonical doc-status vocab `draft/approved/superseded` for `prd`, `interface-design`, `discovery-brief`). Single version bump covering both.
2. **`src/rules/memory-protocol.md`** — apply **Plan A Step 3** (`trigger: always_on`) **and Plan C Workstream C** (§8 hierarchy via **`Parent`** column; §2 bare-ID note references `Parent`/`Blocked by`). Single bump.
3. **`src/rules/output-mode.md`** — apply **Plan A Step 2** (`trigger: glob` → `always_on`, remove `globs:`). Single bump.
4. **`src/references/PRD-template.md`** — **Plan C Workstream B**: `status:` → `draft | approved | superseded`; add `bt:`; drop `ready-for-design|in-progress|complete`. Bump.
5. **`src/references/design-doc-template.md`** — **Plan C Workstream B**: `status:` → `draft | approved | superseded` (rename `obsolete`→`superseded`); confirm `bt:`. Bump.
6. **`src/memory-templates/BACKLOG_MAP.md`** — **Plan C Workstreams A + C**: registry adds `status:in review` + documents lifecycle order; header `Dependencies` → `Parent` + `Blocked by` (9-column schema `ID, Title, Status, Labels, Milestone, Parent, Blocked by, ICE, Ref`); update Rules text, example rows, identity-contract note (7 gh-mirror cols incl. Milestone; ICE+Ref local; closed ≡ done). Single bump.

---

## Phase 2 — New skill + 0a refactor

1. **Create `src/skills/load-memory/SKILL.md`** — **Plan B A1**, with the skill renamed **`context-hydrate` → `load-memory`** (`name: load-memory`; update its `description` accordingly; skill path `src/skills/load-memory/`). Frontmatter incl. `version: "1.0.0"` + `timestamp`; body: purpose, invocation modes default/`memory-only`, procedure steps 0–9, NON-GOALS, output contract. No `disable-model-invocation`. Keep the documented output token `HYDRATE_STATUS` (the token names the *action*, independent of the skill name; changing it would ripple through the Phase 6 dry-run checks for no gain). **Self-containment (per `improve-workflows-skills` §1):** skills may fire in an *unscaffolded* project, so step 0 must degrade gracefully — **if `.memory/` (or `STATUS.md`) is absent → `HYDRATE_STATUS: no-active-task`, RETURN** (no error, no project-local dependency assumed).
2. **`src/workflows/0a_start-session.md`** — union of:
   - **Plan B A2**: refactor to **Phase A (Hydrate → run `load-memory` skill)** + **Phase B (Activate: branch restore, state transition)**; delete old inline read-only steps.
   - **Plan C Workstream A**: epic→`in progress` only via the first-slice rule; keep the remove-prior-label list and **add `in review` to the removal set**.
   - **Plan A**: `trigger: manual`.
   - One version bump (≥ minor — substantial refactor).

---

## Phase 3 — Workflow edits (single pass per file)

For **every** workflow file, apply the union of its Plan A/B/C edits in one pass, set
`trigger: manual`, set `timestamp: 2026-07-17`, and bump `version:` exactly once.

### 3.1 Status lifecycle + review state (Plan C Workstream A)
- **2a** — Phase 2 mint epic `status:needs_spec` (was `in progress`); Phase 5 PRD `status: approved`; **epic stays `needs_spec` — 2a never promotes it** (2b is the sole promoter; PR-review correction — 2b Path C covers non-UI interfaces, so 2a can't decide "non-UI → planned"); BACKLOG Status `needs_spec`; epic BACKLOG row `Parent = —`.
- **2b** — replace `status → ready-for-slicing` with design `status → approved` **and** epic `needs_spec→planned`; Phase 2 init keeps `draft`; **Phase 1 step-2 skip/handoff path also promotes epic `needs_spec→planned`**.
- **3b** — slices born `status:planned` (Template A spike → `needs_spec`, milestone-exempt); **Phase 1 entry: defensively promote parent epic `needs_spec→planned`** (idempotent guard); Phase 3 step 4 write `Parent`/`Blocked by` columns (was free-text `Dependencies`).
- **3c** — operate on `tier:slice AND status:planned` only; never auto-flip `needs_spec`→`planned`; update row-shape refs to 9-column header.
- **3d** — first-slice rule: slice→`in progress`; parent epic `planned→in progress` only if not past it. (Plan B also **prepends the `load-memory` skill call to 3d's existing Phase 0** — keep the branch/status/design steps.)
- **4a** — step 6 slice→`in review` (was "leave at in progress"); step 7 gate on **all siblings `in review`** (was "closed"), epic→`in review` + `gh pr ready`, `done` deferred to merge; update Hand-off contract line. **Also (item 4 below) dispatch Phase 2's two auditors as two separate subagents.**
- **3z** — terminal set includes `in review`; retry/preflight excludes `in review` **and** `done`. Frontier/unblocked query treats a `Blocked by` entry that is already `in review` or `done` as satisfied (see blocker-clearing below).
- **0b** — `done` detection = issue closed/merged; don't force `done` on unmerged slices.

**Blocker clearing (new transition edge — feedback item 3; not in any source plan).**
Plan C added the `Blocked by` column and the `blocked` state (3z sets it) but defined **no edge that
clears a blocker**. Add it:
- **Rule:** when a blocking issue reaches **`in review` or `done`**, remove its ID from every dependent's
  `Blocked by` — in both `.memory/BACKLOG_MAP.md` **and** the GitHub blocked-by relationship (`gh`) — so the
  identity contract (backlog mirrors gh) stays honest and the dependent becomes visibly unblocked.
- **Owner (single writer):** **4a**, at the same step 6 where it sets a slice → `in review`: after the
  transition, clear that slice's ID from all sibling/dependent `Blocked by` entries (backlog + `gh`).
- **Safety net:** **0b / merge confirmation** re-clears on `done` (covers a blocker that went straight to
  merge). **0d Phase 3.6** drift check (extended in Workstream C below) reconciles any stragglers.
- **Add to Plan C's Transition-ownership table** as: `blocker → in review|done ⇒ dependents' Blocked by cleared | 4a step 6 (in review), merge/0b (done)`.
- *(Threshold is "in review OR done" per feedback — slices share a feature branch/PR, so a blocker's code exists once it is `in review`, making dependents safe to proceed.)*
- **Blocker placement writers (post-feedback):** `3b` is the birth writer of `Blocked by` (at issue creation). `3c` may **add** a late-discovered blocker edge during sprint planning — but only as a `[NEW-DEP]` surfaced at its Phase 4 HITL halt and written on explicit user confirmation (Phase 5 step 3); it never removes an edge. Clearing remains 4a (at `in review`) / 0b / merge. This keeps effectively one writer per action: 3b births, 3c amends-with-confirmation, 4a/0b clear.
- **3a** — BACKLOG row-shape refs → 9-column header.
- **0d** — **extend existing Phase 3.6 drift check** to also compare `Parent` + `Blocked by` (+ `Labels`) against `gh`, not just status/milestone (GitHub authoritative, advisory-only, no new pass), **and flag any `Blocked by` entry whose blocker is already `in review`/`done` as stale (should have been cleared by 4a/merge).**
- **1b** — align discovery-brief `status` to `draft|approved|superseded` if it uses old vocab (verify during execution).

### 3.2 Phase 0 memory-load block (Plan B A3)
Add the **standard** or **memory-only** Phase 0 block (per Plan B A3 wording, referencing the
renamed `load-memory` skill at `.agents/skills/load-memory/SKILL.md`) to these 15
workflows. **Excluded:** `0a` (the caller) and `3z` (orchestrator; inherits via `/0a`).

| Workflow | Phase 0 mode |
|---|---|
| 1a_research, 4a_verify-and-ship | memory-only |
| 1b_concept-framing, 1c_concept-map | memory-only |
| 2a, 2b, 3a, 3b, 3c, 4b, 0b, 0c, 0d, x_jules-dispatch | standard |
| 3d_implement-issue | PREPEND skill call to existing Phase 0 (keep its branch/status/design steps) |

### 3.3 Doc-commit owner (Plan B B1)
- **2a** — after Phase 3/4, add **"Commit & Push Doc"**: `git add docs/prds/BT-<pad>-<name>.md && git commit …` then push to **default** (if `gh`/remote connected; else local commit). Resolves RISK-1 (3a reads PRDs on default).
- **2b** — same for `docs/design/BT-<pad>-interface.md`.
- Confirm no existing step already commits these (grep 2a/2b for `git add`); keep code off default (feature branch still born at 3d — §4 unchanged).

### 3.35 4a auditor dispatch — two separate subagents (feedback item 4)
4a Phase 2 "Isolate" path defines **two** auditors — the **Strict Business-Logic Auditor** and the
**Standards Auditor** — each with its own inputs and its own guardrail. In practice an executor
folded both into a single subagent. Make the separation explicit and enforced: dispatch them as
**two independent subagent invocations, in two isolated contexts** (never one agent doing both
roles). Per `improve-workflows-skills` §2/§4, each auditor's guardrail is its *entire contract*
and must not be merged or diluted. Tighten the Phase 2 wording to, e.g.: *"Dispatch two separate
subagents (independent contexts): (1) Strict Business-Logic Auditor … (2) Standards Auditor ….
Do not combine them into one agent."* Fold this into the same single 4a edit/bump as Phase 3.1.

### 3.4 Trigger normalization (Plan A Step 4)
Every workflow (all 17) ends this phase at `trigger: manual` (insert after `type:` for
`4b`, which has none). `3z` stays `manual` — post-invocation autonomy stays described in the
body, not the trigger. **Apply body edits (3.1–3.3) first, then set `trigger: manual` +
`timestamp` + the single `version:` bump** so each file bumps exactly once (avoids the
double-bump the Plan A Appendix-A script would cause if run before body edits). The Appendix-A
script may be used only for the trigger/timestamp/bump mechanics **after** body edits, or the
whole per-file edit done by hand. **Keep `0a` out of any scripted pass** — it was already
set to `manual` + given its ≥minor bump by hand in Phase 2.2 (the Appendix-A script only
patch-bumps, which would under-bump 0a's refactor).

---

## Phase 4 — Installer, scaffold, validate, AGENTS.md

1. **`src/scripts/scaffold.py`** — **already implemented in the base prototype**, but **host-AGNOSTIC** rather than Plan A's locked D4 host-conditional: it always dual-places any `trigger: glob` rule to `.claude/rules/` regardless of host. This is a deliberate, accepted deviation — it preserves D1 (only `glob` rules land in `.claude/rules/`; `always_on` rules never do, so Claude token-efficiency holds) and its intent (native `paths` activation for Claude), and strictly improves the both-host case (a teammate opening in Claude gets native activation even if the Claude installer never ran). Cost: one inert extra committed file for a pure-Antigravity user. **Stale-note correction:** the Plan A verification item "Antigravity install → no `.claude/rules/`" no longer holds under host-agnostic placement — an Antigravity install now also emits `.claude/rules/okf-protocol.md` (inert at runtime). No code change needed.
2. **`build/validate.py`** — **Plan A Step 7**: insert §2.6 trigger-enum contract (rules ∈ {`always_on`,`glob`,`model_decision`}, `glob` requires `globs`+`paths`; workflows must be `manual`). Insert the block **before** the `# Also check python script files … for BOM` block (the anchor is load-bearing — the block reuses `fm_dict`/`errs` already in scope). Use Plan A's exact block. *(Not itself version-stamped; it's tooling.)*
3. **Installer `Instantiate-StratosphereOS.md`** (~line 199) — **Plan B B2**: add `.memory/STATUS.md` to the gitignore-ensure list (durable memory stays tracked; ephemeral session pointer stays local). Bump the installer file's version.
4. **`AGENTS.md` — both copies** (`src/constitution/AGENTS.md` **and** repo-root `AGENTS.md`) — **Plan A Step 8**: add the §8 host-activation bullet. Bump both (constitution `2.0.0→2.0.1`; repo-root `1.0.3→1.0.4` — verify actual bases), `timestamp: 2026-07-17`.

---

## Phase 5 — Build, validate, guard (ONCE)

1. Set plugin `VERSION` → **3.0.0** (per D0; the in-flight tree set it to 2.2.0 — correct to 3.0.0). Drive the README badge to **3.0.0** as well; `validate.py`'s badge-sync check compares badge ↔ VERSION, so both must read 3.0.0 or validate fails (Plan B relies on this).
2. `python build/build.py` — regenerates both `dist/` trees + `versions.json` + marketplace; auto-globs the new `load-memory` skill.
3. `python build/validate.py` → `VALIDATION OK` **including new §2.6 checks**.
4. `python build/bump_guard.py` → green (3.0.0 > last tag v2.1.0; every changed body bumped).
5. `python src/scripts/validate_memory.py` against the updated template **and** this repo's `.memory/` (Plan C DoD). It is a **distributed product script**, not build tooling. It parses BACKLOG_MAP **positionally**: `parts[3]`=Status, `parts[4]`=Labels — these indices are **unchanged** by the split because `Parent`/`Blocked by` insert *after* `Milestone` (index 5), and it does not hardcode the `Dependencies` label. So **no code edit is expected**, but confirm it passes on the 9-column schema and tolerates `status:in review` slices (they are non-exempt → get the normal taxonomy check, which they satisfy). If any positional check does break, fold the fix into Plan C Workstream C as an added file.

**Run these exactly once, at the end of the combined change** (Plan C mandate). Do not build per-phase.

---

## Phase 6 — Verification (union of all three)

**Plan A (triggers/placement):**
- `dist/{claude-code,antigravity}/…/rules/okf-protocol.md` both carry `globs` + `paths` (byte-identical across dists); `output-mode.md`/`memory-protocol.md` are `always_on`.
- A built command (e.g. `dist/claude-code/commands/4a_verify-and-ship.md`) shows `trigger: manual`.
- Host-conditional dry-runs of dist `scaffold.py --dry-run`: Claude install → `okf-protocol` under **both** `.agents/rules/` and `.claude/rules/`, `always_on` rules under `.agents/rules/` only; Antigravity install → **no** `.claude/rules/`.

**Plan B (hydrate/backup):**
- Dry-run A (active task): guarded workflow → `HYDRATE_STATUS: synced`, context loaded once.
- Dry-run B (empty STATUS): `/1a` → `no-active-task`, zero code reads; `/0a` halts at Phase B (no side effects).
- Dry-run C (2nd workflow same session): `HYDRATE_STATUS: cached`. Dry-run D (Active issue changed): re-hydrates.
- B1: run 2a → PRD committed+pushed to default; 3a on default reads it (RISK-1 gone).
- B2: fresh install → `.gitignore` contains `.memory/STATUS.md`; durable memory files tracked.

**Plan C (lifecycle/schema):**
- Flow test on `.tmp/flow-test`: 2a→2b→3b→3d→4a; epic walks `needs_spec→planned→in progress→in review`; slice walks `planned→in progress→in review`; BACKLOG `Parent`/`Blocked by` populate and match `gh`; no doc frontmatter ever carries a work-status token; no issue ever carries `draft`/`approved`.
- 4a deadlock regression: Epic Check fires (marks PR ready) before merge, on all-siblings-`in review`.
- Drift detection: hand-corrupt a BACKLOG row's `Parent`/`Blocked by`/status/milestone → `/0d` Phase 3.6 emits `[DRIFT]` for each (advisory, not auto-fixed).

**Cross-cutting:** `versions.json` lists `load-memory` + every bumped file; no file double-bumped; `validate.py` + `bump_guard.py` green.

---

## Phase 6.5 — Critical implementation review (four subagents)

Gate on the **implementation** (not the plan — that was already reviewed at authoring). Run
**after** Phase 6 passes, **before** Phase 7 ship.

1. **Three parallel per-plan critics** — dispatch three independent subagents, one per source
   plan, each with the read-only diff/working tree + its assigned source plan + this master plan:
   - **Critic A** → `harmonize-trigger-semantics-plan.md`: verify every Plan A requirement is faithfully implemented (trigger enum, `paths`/`globs` superset, host-conditional scaffold, validate.py §2.6, §8 pointers) and nothing regressed.
   - **Critic B** → `context-hydrate-guard-plan.md`: verify the `load-memory` skill, 0a Phase A/B, Phase 0 blocks, doc-commit owner, installer gitignore, read-only guard invariant.
   - **Critic C** → `lifecycle-status-and-backlog-schema-plan.md`: verify the status state machines, `status:in review`, doc-frontmatter vocab, `Parent`/`Blocked by` split, blocker-clearing edge, single-writer invariants.
   - Each critic returns: per-requirement COVERED/PARTIAL/MISSING + any correctness/regression finding, scored, with file:line refs. **Guardrail (per `improve-workflows-skills` §2 — sub-agent contract):** "Review only; do not edit, commit, or push. Return findings."
2. **Consolidate learnings** — merge the three critics' findings; **apply only fixes that are in-scope and do not conflict with this master plan** (a critic asking for something the master plan deliberately deferred/rejected is noted, not applied). Conflicts surface to the user, not silently resolved.
3. **Fourth judge subagent** — after consolidation, dispatch one final critic to judge the **overall** implementation holistically: cross-plan coherence, no dropped/double bump, the union-edited shared files carry all three plans' edits, invariants hold across the whole change, build/validate/guard green. Returns a ship / no-ship verdict with blocking issues (if any). No-ship → loop back to the relevant phase; ship → proceed to Phase 7.

---

## Phase 7 — Ship (§4)

Commit per touched area on the combined feature branch; push; open/update the single feature
PR (Plan A/B/C all land in it). **A human merges after review** — workflows never merge. Push
is gated on validate+guard green and `gh` connected (constitution §4 Git Protocol).

---

## Phase 8 — One-shot migration (external — Plan C §Migration)

**Timing (RESOLVED — after PR merge):** run the external CleanTech + local `.memory/`
migration **only after the 3.0.0 PR is merged** (Phase 7), so a live install is never
migrated to a schema that could still change in review. Not carried in StratOS; not committed
to `dist/`.
- Author `docs/plans/migrate-backlog-oneshot.py` (deleted after use): deterministic file transforms (split `Dependencies`→`Parent`+`Blocked by`, rewrite header to 9 cols; remap PRD/design `status` `ready-for-*`→`approved`, `obsolete`→`superseded`); GitHub-side actions **emitted as a reviewable `gh` script, never auto-run** (`gh label create "status:in review"`; per-epic relabel suggestions). Idempotent.
- Targets: the CleanTech test project **and** this repo's own `.memory/BACKLOG_MAP.md` (old schema too).

---

## Constitution / invariants preserved

- **§1 workflow-invokes-skill** (Plan B): allowed everywhere; no workflow-invoking-workflow introduced. No §1 change.
- **§4 branch model** (Plan B B3, Plan C): feature branch still born at 3d; 0a restores, 4a pushes/PRs, human merges. Docs backed up via B1 commit-owner, not by moving branch birth.
- **Read-only hydrate guard** (Plan B invariants): Phase 0 never checks out/pulls, transitions status, or writes memory — side effects live only in `0a` Phase B and `3d` Phase 0.
- **Single Status Invariant + single-writer-per-edge** (Plan C): exactly one `status:*` per issue; no two workflows write the same transition edge; concept issues stay exempt.
- **No token-bloat migrations** ([[stratos-no-token-bloat-migrations]]): migration is throwaway external (Phase 8); drift-heal stays the deterministic `/0d` check, not agent passes.

## Compliance with `docs/improve-workflows-skills` (dev-time playbook)

This release edits ~20 skill/workflow files, so its authoring must obey the playbook. Applied
in this plan:
- **Self-containment (§1):** `load-memory` degrades gracefully when `.memory/` is absent (Phase 2.1) — no hard dependency on a scaffolded file.
- **Sub-agent guardrails are whole contracts (§2/§4):** 4a's two auditors stay two isolated agents with separate guardrails (Phase 3.35); Phase 6.5 critics carry explicit review-only guardrails.
- **Single source of truth (§2):** shared contracts edited once in `src/` (rules/templates/references); workflows point, never re-paste. `okf-protocol` §2.1 is the single trigger-enum authority.
- **Version discipline (§4/§5):** every touched `src/**` file bumps `version` forward once; edit `src/`, never `dist/`; rebuild once.
- **Never-prune protected classes (§4):** status edits must not dilute existing completion criteria, safety invariants, or leading-word tokens (`[UNCOVERED]`, `[DRIFT]`, `seam`, `[[…]]`).

## Phase 4.5 — Promote the playbook to a dev-only skill (CONFIRMED — this branch)

`docs/improve-workflows-skills/` is dev-time-only. Per its own §1 a *bundled* skill
(`src/skills/`) would register globally in every **consumer** project — wrong for
framework-authoring guidance. Correct form: a **repo-local skill outside `src/`** so the build
never sees it and it never ships. Land on this branch as a **non-shipping** addition (no
product-version impact — not counted in the 3.0.0 bump).
1. Create `.claude/skills/improve-workflows-skills/SKILL.md` (this repo only); optionally mirror to `.agents/skills/` for Antigravity dev use. **Not** under `src/`; **not** in `external-skills.json`.
2. Content = the existing `README.md` playbook + `glossary.md` lexicon (self-contained pair), with skill frontmatter: `name: improve-workflows-skills`, `type: skill`, a `description` that fires on "authoring / editing / pruning a StratOS skill or workflow" (and says dev-only), `version`, `timestamp`. Keep `docs/improve-workflows-skills/` as canonical source (skill references/embeds it) — or move it into the skill dir; decide at execution, avoiding a second drifting copy (§2 single-source-of-truth).
3. Confirm the new path is excluded from `build/build.py` globs and that `build/validate.py`'s "no dev-only leak into `dist/`" guard stays green (Phase 5).
4. Because it's repo-local (outside `src/`), it is **not** part of the plugin `VERSION` bump and does **not** appear in `versions.json`.

## Residual risks (accepted / watch)
- Self-gate is model-judged (no sentinel) — watch in AFK (Plan B).
- `memory-only` depth carve-out relies on model honoring the mode (Plan B).
- ~18 version bumps across the release — miss/double one → build/guard failure (caught, not silent).
- MAJOR renames public contracts (label set + BACKLOG schema) — external installs need the Phase 8 migration.

## Decisions (all resolved)
- **D0** — fold the in-flight v2.2.0 tree into a single 3.0.0 MAJOR release (Phase 0). ✔ (user-confirmed)
- **D2** — run the external migration only after the 3.0.0 PR merges (Phase 8). ✔ (user-confirmed)
- `validate_memory.py` is a distributed product script; its positional BACKLOG parse survives the column split → verify step (Phase 5.5), not an edit. ✔
- README badge currently `2.2.0` → drive to `3.0.0` (Phase 5.1). ✔
- `4b_audit-architecture-drift` folded into the overlap map (trigger + Phase 0). ✔
- Skill renamed `context-hydrate` → **`load-memory`** (feedback item 1). ✔
- Blocker-clearing edge added: cleared at blocker `in review`/`done`, owned by 4a step 6 + merge/0b, reconciled by 0d (feedback item 3). ✔
- 4a dispatches its two auditors as **two separate subagents** (feedback item 4). ✔
- Phase 6.5 added: three per-plan implementation critics + a fourth overall judge (feedback item 5). ✔
- **D3** — promote `improve-workflows-skills` to a repo-local dev-only skill on this branch (Phase 4.5); non-shipping, no product-version impact (feedback item 2). ✔ (user-confirmed)
