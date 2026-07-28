# Plan — Context-hydrate skill + lean 0a + docs/memory backup

Status: ready to execute. Part A adversarially reviewed (2 passes); Part B de-risked
after the "feature-branch-born-at-2a" model was rejected (see Rejected Alternatives).
Branch birth stays at 3d (no §4 amendment). Single canonical plan (supersedes the
`context-hydrate-and-early-branch-plan.md` draft).

## Locked decisions
1. **Scope:** all lifecycle workflows incl. 1-series get a self-gated Phase 0 (15 workflows). `0a` is the *caller* (kept, lean), not guarded. `3z` excluded (orchestrator; already bootstraps `/0a` per subagent).
2. **0a relationship:** extract 0a's read-only reads into a shared skill; `0a` = hydrate + activate (restore existing branch + optional status). DRY.
3. **Idempotency:** self-gate, no sentinel — skill *always* re-reads `STATUS.md`, gates only heavy reads (re-runs if `Active issue` changed).
4. **Depth:** full-depth incl. relevant code by default; **memory-only** for `4a` and `1a/1b/1c`.
5. **No `disable-model-invocation`** (repo convention forbids it; breaks inline skill invocation). Tune via `description`.
6. **Branch birth stays at 3d** (status quo). Docs/memory backup solved by commit-owner + installer hygiene, NOT by moving branch creation.
7. **Docs → committed+pushed to `default`** at authoring (2a/2b). **Durable memory stays tracked; ephemeral `STATUS.md` becomes gitignored** (installer).

## Invariants (must hold)
- **Read-only guard:** Phase 0 NEVER checks out/pulls a branch, transitions issue status, or writes memory. Side effects live only in `0a` (Activate) and `3d` Phase 0.
- **No-op on idle:** empty `STATUS.md` ⇒ `HYDRATE_STATUS: no-active-task`, no further reads.
- **§1 fit:** workflow-invokes-skill is allowed everywhere; not workflow-invoking-workflow. No §1 change.

---

## PREREQUISITE (do first)
Working tree carries an in-flight **v2.2.0** release (`M dist/**`, `M build/build.py` VERSION=2.2.0, `M src/rules/*`, `M src/workflows/0b_stop-session.md`, `M README.md` badge=2.2.0), plus parallel plan drafts in `docs/plans/` (harmonize-trigger, lifecycle-status — leave untouched). `build.py` regenerates all of `dist/`, so building on top mixes changesets.
→ **Commit or stash the v2.2.0 work, then branch clean.** Branch: `feat/context-hydrate-and-backup`.

---

# PART A — Context-hydrate skill + lean 0a

## A1 — Create `src/skills/context-hydrate/SKILL.md`
Frontmatter (NO `disable-model-invocation`; `timestamp` required — build does not auto-add it):
```yaml
---
name: context-hydrate
type: skill
description: Read-only session-context reconstruction from the memory layer. Invoked inline by lifecycle workflows and /0a; do not fire autonomously or on general requests.
version: "1.0.0"
timestamp: 2026-07-17
---
```
Body:
```markdown
# SKILL: Context Hydrate
## Purpose
Reconstruct read-only session context from the memory layer without reading the whole
repo. Mechanical, side-effect-free. Invoked inline by lifecycle workflows (Phase 0) and
/0a. NEVER mutates state.
## Invocation modes
- default: memory context + relevant code (steps 1-9).
- `memory-only`: skip step 9 (code reads). Used by 4a and 1a/1b/1c.
## Procedure
0. **Always** read `.memory/STATUS.md` (cheap). Determine `Active issue`.
   - If no active task → output `HYDRATE_STATUS: no-active-task`, "Needs verification: none", RETURN.
1. **Self-gate:** if already hydrated this session AND `Active issue` unchanged → `HYDRATE_STATUS: cached`, RETURN.
2. Read active task source (prompt/issue/PRD/spec): objective, constraints, deps.
3. Read `.memory/LEARNINGS.md` (Active only; skip ## Superseded).
4. If PRD/discovery/domain feature → `.memory/GLOSSARY.md` (Active only).
5. If task affects structure/state/boundaries/cross-feature → `.memory/ARCHITECTURE.md`.
6. Read `.memory/BACKLOG_MAP.md` (WIP conflicts).
7. If DB/schema/migrations/RLS → `.memory/DATABASE_SCHEMA.md`.
8. If .tsx/UI/layout/styling → `.memory/DESIGN.md` + `.memory/DESIGN_RULES.md`.
9. (default only) Read only relevant code files for the active task — never whole codebase. Skip in `memory-only`.
## NON-GOALS
- No branch checkout/pull. No `gh` label/status changes. No memory writes. Those belong to /0a and 3d.
## Output
`HYDRATE_STATUS: synced` — Objective / Current state / Current branch / Next step / Needs verification.
```

## A2 — Refactor `src/workflows/0a_start-session.md` (v1.0.6 → 1.1.0)
```markdown
## Phase A — Hydrate
Run `.agents/skills/context-hydrate/SKILL.md`.
## Phase B — Activate (side effects)
1. If hydrate returned `HYDRATE_STATUS: no-active-task` → output next-step guidance and HALT (before side effects).
2. Branch restore: if active/unmerged feature branch and repo not on it → checkout; if merged/unset → checkout default + pull. NEVER create (3d owns creation).
3. State transition: set target issue `status:in progress` in BACKLOG_MAP + GitHub; propagate to parent epic; update `Active issue`.
```
Delete old read-only steps (now in the skill).

## A3 — Add Phase 0 to lifecycle workflows
Standard block:
```markdown
## Phase 0: Context Hydration (self-gated, read-only)
Run `.agents/skills/context-hydrate/SKILL.md` to restore session context.
Self-gated (no-op if already loaded this session). Read-only: never transitions issue state or touches branches.
```
Memory-only block: append " in `memory-only` mode (skip code reads)".

| Workflow | Block | Version bump |
|---|---|---|
| 1a_research | memory-only | 1.0.4 → 1.0.5 |
| 1b_concept-framing | memory-only | 1.0.10 → 1.0.11 |
| 1c_concept-map | memory-only | 1.0.3 → 1.0.4 |
| 2a_write-prd | standard (+ B1 below) | 1.1.7 → 1.1.8 |
| 2b_interface-design | standard (+ B1 below) | 1.1.8 → 1.1.9 |
| 3a_version-planning | standard | 1.0.5 → 1.0.6 |
| 3b_create-issue | standard | 2.0.7 → 2.0.8 |
| 3c_sprint-planning | standard | 2.0.8 → 2.0.9 |
| 3d_implement-issue | PREPEND skill call to existing Phase 0; keep branch/status/design steps | 2.0.13 → 2.0.14 |
| 4a_verify-and-ship | memory-only | 1.0.19 → 1.0.20 |
| 4b_audit-architecture-drift | standard | 1.0.7 → 1.0.8 |
| 0b_stop-session | standard | (current) → patch |
| 0c_handoff | standard | 1.0.2 → 1.0.3 |
| 0d_nightly-consolidation | standard | 1.0.6 → 1.0.7 |
| x_jules-dispatch | standard | 0.1.1 → 0.1.2 |

Excluded: `0a` (caller), `3z_afk-loop` (orchestrator; inherits via /0a).
NOTE: version bases may have drifted (files show recent edits Jul 17) — read each file's actual `version:` and bump from that, don't trust this table blindly.

---

# PART B — Docs/memory backup (de-risked; branch stays at 3d)

## B1 — Give docs a real commit owner (backs up PRD/design; eliminates RISK-1)
Finding: existing "Commit & Sync" phases (3a:60, 3c:54) sync GitHub *milestones/issues* and write local
files, but do NOT `git commit`+`push` the doc files. `4a:62` explicitly refuses to sweep doc drift. So
PRD/design docs currently have no reliable git backup.

- **2a_write-prd:** after Phase 3 (draft) / Phase 4 (validate), add a **"Commit & Push Doc"** step:
  `git add docs/prds/BT-<pad>-<name>.md && git commit -m "docs(BT-<pad>): PRD" ` then push to **default**
  (if `gh`/remote connected; else local commit only). Committing PRDs to default means cross-feature
  `3a_version-planning` (which reads `docs/prds/` at 3a:12,36,49) sees them → **RISK-1 resolved.**
- **2b_interface-design:** same for `docs/design/BT-<pad>-interface.md`.
- Confirm at implementation: check whether any existing step already commits these (grep 2a/2b for `git add`);
  if so, only ensure the push. Keep code on the feature branch (born at 3d) — unchanged.

## B2 — Memory backup hygiene (durable already tracked; clean the ephemeral churn)
Finding: the `.memory/` gitignore is only in the *tooling* repo. The **installer**
(`src/commands/instantiate/Instantiate-StratosphereOS.md:199`) ensures a target project ignores
`.tmp/`, `.env`, `.env.*`, `token.json`, credentials — but NOT `.memory/`. So installed projects already
**track and back up** durable memory (`LEARNINGS/GLOSSARY/ARCHITECTURE/DATABASE_SCHEMA/DESIGN/DESIGN_RULES/BACKLOG_MAP`).

- **Installer edit (line ~199):** add `.memory/STATUS.md` to the gitignore-ensure list, so the churny
  session pointer stays local while durable knowledge remains tracked. Bump the installer file's version.
- **Default: ignore `STATUS.md`** (recommended — it changes every session, causes diff/merge noise).
  Override only if you want exact cross-machine session *resume* (then keep it tracked).
- No other memory change needed — backup already works.

## B3 — Branch model: UNCHANGED
Feature branch stays born at 3d (0a restores, 3d creates, 4a pushes/PRs). No §4 amendment.
No `3z:45` edit needed (0a's restore/fallback behavior matches current §4).

---

## Build / validate
```bash
python build/build.py        # regenerates dist/** + versions.json; auto-globs new skill
python build/validate.py     # version markers, frontmatter contract, README badge sync
python build/bump_guard.py   # changed bodies must bump version (vs last tag)
```
- Every touched `.md` needs a `version:` bump. New skill needs `version` + `timestamp`.
- Plugin VERSION stays `2.2.0` (README badge already 2.2.0).

## Verify (definition of done)
- Build + validate + bump_guard pass; `versions.json` lists `context-hydrate` + all bumps.
- Dry-run A (active task): guarded workflow → `HYDRATE_STATUS: synced`, context loaded once.
- Dry-run B (empty STATUS): `/1a_research` → `no-active-task`, zero code reads; `/0a` halts at Phase B (no side effects).
- Dry-run C (2nd workflow same session): `HYDRATE_STATUS: cached`.
- Dry-run D (Active issue changed): re-hydrates.
- B1: run 2a → PRD committed+pushed to default; then 3a on default reads it (RISK-1 gone).
- B2: fresh install → `.gitignore` contains `.memory/STATUS.md`; durable memory files tracked.

## Ship
Commit per touched area; push `feat/context-hydrate-and-backup`; open PR. Human merges (§4).

---

## Rejected Alternatives (why the plan looks like this)
- **Session-start hook (CC `SessionStart` / Antigravity `PreInvocation@0`):** rejected as the *foundation* —
  eager loading bloats Q&A/research sessions, and it's host-specific. Kept as a possible later opt-in accelerator.
- **`disable-model-invocation` on the skill:** rejected — repo convention forbids it and it would block inline
  invocation (only description-triggered skills can be invoked inline by a workflow).
- **Feature branch born at 2a:** REJECTED — confirmed silent-failure blocker (RISK-1): PRDs are cross-feature
  inputs read by `3a` on `default`; siloing each PRD on its own 2a-born feature branch made 3a roadmap from
  missing content without halting. Solved instead by committing PRDs to default (B1) + keeping branch birth at 3d.
- **Sentinel file for idempotency:** rejected per user — self-gate + always-re-read-STATUS is enough; `.tmp` is
  gitignored and persists across conversations (staleness).

## Residual risks (accepted / watch)
- Self-gate is model-judged (no sentinel) — watch in AFK.
- Depth carve-out relies on model honoring `memory-only`.
- ~15 version bumps — miss one → build/guard failure (caught, not silent).
- B1 doc-commit-owner: verify no double-commit with any existing sweep; keep code off default.
