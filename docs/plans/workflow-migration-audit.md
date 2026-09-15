---
type: plan
title: Workflow Migration — In-Body Edit Inventory
description: Per-file inventory of body edits required by the v4.0.0 workflows-to-skills migration. Companion to future-proofing-spec-conformance-plan.md Slice 9.
version: "3.0.0"
timestamp: 2026-09-15
---

# Workflow Migration — In-Body Edit Inventory

> Slice numbers below match plan **v6.0.0** (flat 1–15).

Work list for **Slice 9** of [future-proofing-spec-conformance-plan.md](future-proofing-spec-conformance-plan.md).

> **Provenance.** The first pass ran against branch `feat/2c-reconcile-specs`, which was **34 commits behind `origin/main`** and missing `4c_codebase-health-audit` entirely. Sections **A, C, E** below have been **re-derived mechanically against `origin/main` (`c5b9ff9`)** and carry accurate line numbers. Sections **B, D, F, G, H, J, K** are prose findings from the first pass: the *findings* hold, but their **line numbers must be re-verified** against main before use.

## A. Reference repointing — re-derived against main

**37 citations** of `.agents/workflows/.reference/` across 14 workflows, 1 command, and 1 reference body.

| File | Lines | References |
|:---|:---|:---|
| `0b_stop-session` | 23 | `github-issue-relations` |
| `1a_research` | 92 (×2), 100 | `research-competitive-template`, `research-problem-template`, `research-evidence-standards` |
| `1b_concept-framing` | 39, 112 | `multi-sided-discovery`, `discovery_brief_template` |
| `1c_concept-map` | 14, 34, 38 | `concept-map-operations`, `concept-map-template`, `github-issue-relations` |
| `2a_write-prd` | 41 | `PRD-template` |
| `2b_interface-design` | 12, 51 | `design-doc-template`, `design-brief-guide` |
| `2c_reconcile-specs` | 46 | `confidence-scale` |
| `3a_version-planning` | 61, 64 | `ROADMAP-template`, `terminal-sync-invariant` |
| `3b_create-issue` | 49, 64, 67, 76 | `confidence-scale`, `github-issue-relations`, `terminal-sync-invariant`, `issue-templates` |
| `3c_sprint-planning` | 65, 67 | `github-issue-relations`, `terminal-sync-invariant` |
| `3d_implement-issue` | 18 | `shadcn-build-guide` |
| `4a_verify-and-ship` | 30, 31, 69, 71 | `confidence-scale`, `code-smell-baseline`, `github-issue-relations`, `terminal-sync-invariant` |
| `4b_audit-architecture-drift` | 33, 56, 65 | `confidence-scale` ×2, `issue-templates` |
| `4c_codebase-health-audit` | 69, 74, 94, 106 | `confidence-scale`, `health-audit-scan-matrix`, `health-audit-report-template` ×2 |
| `Instantiate-StratosphereOS` | 158 | `design-brief-guide` |
| **`concept-map-operations` (a reference body)** | 14, 23, 42 | `github-issue-relations` ×2, `concept-map-template` |

**Fan-out required** — built from the single `src/references/` source (I8). Five shared references, 18 emitted copies:

| Reference | Copies | Consumers |
|:---|:---|:---|
| `github-issue-relations.md` | **5** | `0b`, `1c`, `3b`, `3c`, `4a` |
| `confidence-scale.md` | **5** | `2c`, `3b`, `4a`, `4b`, `4c` |
| `terminal-sync-invariant.md` | **4** | `3a`, `3b`, `3c`, `4a` |
| `issue-templates.md` | 2 | `3b`, `4b` |
| `design-brief-guide.md` | 2 | `2b`, `stratosphere-setup` |

The remaining 14 references are single-consumer and simply move.

**Reference bodies cite references too.** `concept-map-operations.md` carries 3 citations of its own. Rewriting only the workflows leaves these broken.

**Uncited dependency:** `2c:57` depends on "Template A" semantics from `issue-templates.md` without citing it. Either add the reference to that skill or make the prose self-sufficient.

## B. Absolute paths required (subagent boundary)

> Line numbers from the pre-merge pass — re-verify.

**Five sites**, verified: `4a:30`, `4a:31`, `4b:33`, `4c:69`, `4c:74`. Each passes a reference path **as input to an isolated subagent**. A bare relative `references/<file>.md` resolves against the subagent's cwd (repo root), not the skill directory — it returns nothing and fails **silently**.

`4c:74` is the highest-severity of the set. 4c spawns 3 parallel subagents (`:63`) and each "reads its assigned sections from the scan matrix" (`:82`). With no scan matrix, every subagent reports zero findings across both its passes, and 4c's Clean Exit branch prints `[HEALTHY] No findings ≥60 confidence across 6 passes.` — a **false all-clear** persisted to `.last-run.json`.

These call sites must emit the full `.agents/skills/<name>/references/<file>.md`. The Slice 12 link-integrity check must resolve relative paths **from the skill directory**, or it will pass a path that is broken at runtime.

## C. Path-based skill delegation — re-derived against main

**17 path delegations** that should become name-based invocation (the form already used for `plan-html` and `micro-tdd`):

| Target | Count | Sites |
|:---|:---|:---|
| `load-memory` | **13** | `0a:17`, `1b:21`, `1c:20`, `2a:15`, `2b:17`, `2c:15`, `3a:29`, `3b:17`, `3c:15`, `3d:15`, `4a:17`, `4b:13`, `4c:20` |
| `jules-dispatch` | 2 | `x_jules-dispatch:17`, `:19` |
| `concept-brainstorm` | 1 | `1b:28` |
| `code-simplifier` | 1 | `3d:35` |

`load-memory` appears **nowhere in `scaffold.py`** — it is a plugin skill never placed into a scaffolded project's `.agents/skills/`, so all 13 delegations are **already broken in consumer projects**. `code-simplifier` is an on-demand pack that may be absent.

## D. Underscore names — sweep hazards

> Line numbers from the pre-merge pass — re-verify.

Three syntactic forms; a single pattern misses some:
- **Slash form:** `/3b_create-issue` — most occurrences
- **Bare prose:** "Gate between `2b_interface-design` and `3b_create-issue`"
- **Unbackticked:** `/1a_research` in plain prose — a backtick-anchored sweep misses it
- **Inside quoted strings / escaped-JSON payloads:** several in `3z_afk-loop`

**Do NOT touch:**
- Bare short-form ids (`0a`, `1b`, `3d`, `4a`) — they survive the rename
- `.github/workflows/` — GitHub Actions, not agent workflows (`Instantiate-StratosphereOS`, `scaffold.py:339`)
- `src/references/discovery_brief_template.md` — the underscore is in a *reference* filename, not a skill name. A blanket `_`→`-` breaks the file and its citation at `1b:112`
- `4a` "If command exits non-zero" — refers to a shell command

**User-visible handoff strings** are the highest-cost misses, since there are no alias shims (I2): a stale one prints a command the user types that silently does not resolve.

## E. Frontmatter defects — re-verified against main

- **The three `src/commands/` drivers carry no `trigger:` key** — `Instantiate-StratosphereOS.md`, `Stratosphere-Update.md`, `SKILL_sync-skills.md` all have `type: workflow` and **no `trigger:`**. Any Slice 8 transform keyed on `trigger: manual` silently skips them, leaving `/stratosphere-setup` **model-invocable** — the worst failure in this set.
- **`name` ≠ parent directory** for two: `instantiate/Instantiate-StratosphereOS.md` → `stratosphere-setup`; `update/Stratosphere-Update.md` → `stratosphere-update`. Rename the `src/` dirs so both trees agree.
- `sync-skills/SKILL_sync-skills.md` → rename to `SKILL.md` on move.
- **RESOLVED on main:** the earlier finding that `4b` carried a bare `type: workflow` with no `HITL`/`AFK` qualifier no longer applies — every `src/workflows/` file on main has a qualifier. Only the three drivers are defective.
- `2c:58` instructs agents to bump `timestamp` in document bodies — Slice 4's frontmatter grep does not catch body prose.
- **`src/references/health-audit-report-template.md:34`** carries `timestamp: <YYYY-MM-DD>` inside a fenced report skeleton — a template that **mints v0.1-shaped frontmatter into every future audit report**, under `docs/audits/`, which the `okf-protocol` glob matches. The `^timestamp:` gate does fire (column 0 inside the fence), but a mechanical rename produces invalid YAML: `generated` is a nested mapping.
- **Eight unregistered OKF types are in use**, not one. The registry lacks `audit-report`, `concept-map`, `implementation-plan`, `plan`, `proposal`, `reference`, `roadmap`, `skill` — while §3 states *"Agents must never invent or use a type silently."* Instructed sites include `3a:61` (`roadmap`) and `health-audit-report-template.md:32` (`audit-report`). Note these two planning documents use `plan` and `reference`, both unregistered.

## E2. `4c_codebase-health-audit` — findings unique to it

Audited separately (it was absent from the stale branch). Clean on §D (no underscore names in its body — it uses protected short forms `/3b`, `/3d`) and clean on §H (no cross-workflow phase coupling). Its frontmatter is sound: `type: workflow HITL`, `trigger: manual` both present.

Unique requirements:

- **Parallel subagent fan-out.** `:63` invokes **3 subagents in parallel**; Phases 2–3 are built on it (three named auditors → six passes → parent merge at `:88`). §G's remedy addresses *whether* a host has subagents, not concurrency. Unverified on Cursor, Codex, Devin, OpenClaw. Sequential is semantically equivalent (the auditors share no state) but all six passes must still run, or Phase 5's `6/6` claim is false.
- **Argument channel.** `:36` — "Trigger prompt may narrow scope (e.g. `4c src/features/billing`)" — hard-codes the bare short id as the invocation token *and* assumes an argument channel Antigravity skills do not have. The `[WARN] Narrowed scope:` block at `:37–39` becomes dead prose there.
- **"Read-only" contradiction.** `:15` asserts `**Read-only.** Never modify production code...` while `:115` **deletes** `docs/audits/health-*.md` older than 90 days. The description is Antigravity's only invocation signal, and a read-only framing is what makes model-invocation look harmless.
- **Magic-constant coupling.** `:69` states "overrides default ≥80 in `confidence-scale.md`". That file currently says ≥ 80; if it changes, 4c's prose is silently wrong. Same failure class as §H's phase numbers.
- **`allowed-tools` case.** `:48–50` shells out to `git log`. 4c is the strongest candidate for declaring the spec-standard `allowed-tools` field, which no workflow currently sets.

Its two references also need Slice 6 sweeping: `health-audit-report-template.md:2,9,118` and `health-audit-scan-matrix.md:2,9` all carry `4c_codebase-health-audit` or `/4b_audit-architecture-drift`. `scaffold.py:320`'s comment reads `# 0a..4b` and is stale (the regex itself is fine).

## F. HITL prose (the Antigravity gap)

> Re-verify line numbers.

Antigravity reads only `description`. Body prose is invisible to its invocation decision; frontmatter keys are ignored.

Only `2c:10` and `4b:10` carry a body-level HITL assertion. The rest rely on `trigger: manual` plus the command channel — both of which Antigravity loses. Every skill's **`description`** must restate user-only status.

**Highest exposure: `0d_nightly-consolidation` Phase 3.6**, which emits `/<sibling-skill>` recommendations directly into agent context, guarded only by prose. Strengthen, don't merely carry over.

## G. Host enumeration — 2 of 6

**5 files** contain `invoke_subagent` ("via Antigravity `invoke_subagent` or Claude Code `Task` general-purpose"). Reads as *unsupported* on Cursor, Codex, Devin, OpenClaw. Generalize to "invoke a subagent using the host's subagent mechanism".

Also host-coupled: `0c` "any passed arguments" (the `$ARGUMENTS` slash-command channel); `2b` `/design-sync` (Claude Design only); `Stratosphere-Update` `/plugin marketplace update` (Claude Code only).

## H. Cross-workflow body coupling

> Re-verify line numbers.

Not path references, so no link check catches them:
- `1c` — "Run `/1a_research` **Phase 1** inline"
- `2b` — "`3d` **Phase 0**"
- `3z` — "`/4a_verify-and-ship` **Phases 1–4 ONLY** … do NOT run Phase 5"; later "Phase 5"
- `0b` — "same as 1b" makes `0b` depend on reading `1b`'s body

`3z` is the dangerous one: if `4a` renumbers its phases, `3z` silently ships unverified work across a subagent boundary. Convert to **named gates** (`audit-only` / `ship-only`).

## I. Orphaned reference — corrected

The earlier claim that `health-audit-report-template.md`, `health-audit-scan-matrix.md`, and `terminal-sync-invariant.md` were orphans was **wrong** — an artifact of auditing a branch that predated `4c_codebase-health-audit`. On main:
- `health-audit-report-template.md`, `health-audit-scan-matrix.md` → owned by `4c`
- `terminal-sync-invariant.md` → **4 consumers** (`3a`, `3b`, `3c`, `4a`)

`terminal-sync-invariant.md` is cited from **Python** too — `src/scripts/reconcile.py:14` — so it has 5 consumers, and the retirement sweep must include `.py` (`scaffold.py:338` and `:1068` also hold the retired path).

The one genuine orphan is **`brainstorm-techniques.md`** — zero citations anywhere in `src/`. It was superseded by the `concept-brainstorm` skill (commits `d4ec45f`, `ceaf567`). Separate cleanup; not part of this migration.

## J. `x_jules-dispatch` → `3x-jules-dispatch` — RESOLVED

Renamed, not folded. The pack `jules-dispatch` stays an opt-in on-demand fetch; the launcher stays bundled so a `/`-invocable entry point exists even when the pack is absent. The defect was the near-identical sibling names, and the rename fixes exactly that.

Side effect: `3x-jules-dispatch.md` matches `LIFECYCLE_RE`, so `EXTRA_WORKFLOWS` drops to `{"sync-skills.md"}`.

Still required: the reserved-name guard in `sync_skills.py` (§K) — an `external-skills.json` `targetPath` could still collide with a bundled lifecycle skill.

## K. Install/upgrade driver corrections

> Re-verify line numbers.

`Instantiate-StratosphereOS.md`:
- The paragraph explaining that lifecycle workflows are copied into `.agents/workflows/` because Antigravity does not register plugin workflows — **every clause is falsified**. Destination, rationale, the "Claude Code copies are inert" claim, and the lifecycle-vs-domain split all change. Rewrite against the Slice 7 placement map.
- Retired `.agents/workflows/` + `.reference/` paths in the installed-files list.
- The workflow enumeration "`0a`–`4b`, `sync-skills`" omits both `4c` and `x_jules-dispatch` — the count told to the user is off by two.
- `.gitignore` handling: the checkpoint that enumerates expected entries **omits `.agents/skills/` entirely**, already disagreeing with `GITIGNORE_ENTRIES`.
- "this command" → "this skill" in several places; the file already says "skill" elsewhere.

`Stratosphere-Update.md` — see Slice 10; no removal phase, no `.gitignore` remediation, no "moved file" category in its worklist schema.

`SKILL_sync-skills.md`:
- "**not bundled**" is now half-true; `.agents/skills/` gains two tenants. State that `sync_skills.py` must never overwrite a bundled skill directory.
- Nothing prevents an `external-skills.json` `targetPath` of `.agents/skills/3d-implement-issue` from clobbering a lifecycle skill. Needs a reserved-name guard.
- Stale cross-reference: skill setup is **Checkpoint 9** in the current installer, not Checkpoint 8.
