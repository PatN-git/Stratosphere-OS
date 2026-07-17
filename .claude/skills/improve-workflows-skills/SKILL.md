---
name: improve-workflows-skills
description: Dev-time discipline for authoring, editing, or pruning StratOS's OWN skills (src/skills/) and workflows (src/workflows/). Fires when creating/editing a StratOS skill or workflow, running a pruning/refactor pass, or reviewing framework artifacts. Repo-local and dev-only — NOT a product skill; never advise consumer projects with it.
type: skill
version: "1.0.0"
timestamp: 2026-07-17
---

# SKILL: Improve Workflows & Skills (dev-only)

Repo-local skill for developing **StratOS's own** framework artifacts. It never ships
(it lives in `.claude/skills/`, outside `src/`, so the build never globs it).

## When this fires
Authoring a new skill/workflow, editing one, or running a pruning/refactor pass over
`src/skills/` or `src/workflows/` — or reviewing those artifacts for quality.

## Canonical source (read before acting)
The full playbook + lexicon are the single source of truth — read them, don't restate them:
- **`docs/improve-workflows-skills/README.md`** — the complete playbook (artifact types, shared-component extraction, authoring levers, the pruning pass, word-level economy, mechanics).
- **`docs/improve-workflows-skills/glossary.md`** — every term + the leading-word palette (use those tokens, not synonyms).

## Non-negotiables (quick reference — the full rules are in the playbook)
1. **Know the artifact type.** Skill = self-contained discipline (may fire unscaffolded → no project-local refs). Workflow = user-invoked orchestrator (scaffolded-only → may cite `.agents/workflows/.reference/*`; may delegate to skills). This repo does **not** use `disable-model-invocation`; tune a skill's auto-fire via its `description`.
2. **Single source of truth (§2).** Extract true duplication to a shared reference; point, never re-paste, never cross-read another workflow's body. Propose the refactor — don't silently rewrite load-bearing content.
3. **Never prune the protected classes (§4).** Load-bearing exhaustiveness, checkable/exhaustive completion criteria, safety/irreversible-action invariants, **sub-agent guardrails** (each is a dispatched agent's entire contract — keep every copy verbatim), leading-word tokens (`[UNCOVERED]`, `seam`, `[[G-xxx]]`…), and full context-pointer paths.
4. **Prune only executor-neutral prose.** Hunt no-op / duplication / sprawl / sediment; run the post-prune diff gate. When fidelity and economy conflict, fidelity wins.
5. **Mechanics.** Edit `src/` only (never `dist/`); bump OKF `version` + `timestamp` on every changed file; rebuild via `python build/build.py`; confirm `build/validate.py` green.
