---
name: improve-workflows-skills
description: Dev-time discipline for authoring, editing, or pruning StratOS's OWN lifecycle skills (src/workflows/) and execution skills (src/skills/). Fires when creating/editing a StratOS skill, running a pruning/refactor pass, or reviewing framework artifacts. Repo-local and dev-only — NOT a product skill; never advise consumer projects with it.
metadata:
  stratos.layer: execution
version: "2.0.0"
timestamp: 2026-09-15
---

# SKILL: Improve Workflows & Skills (dev-only)

Repo-local skill for developing **StratOS's own** framework artifacts. Authored in
`src/dev-skills/`, which the build never globs — it is placed into this repo's
`.agents/skills/` and `.claude/skills/` by `scripts/place-dev-skills.py` and ships nowhere.

## When this fires
Authoring a new skill, editing one, or running a pruning/refactor pass over
`src/skills/` or `src/workflows/` — or reviewing those artifacts for quality.

## Canonical source (read before acting)
The full playbook + lexicon are the single source of truth — read them, don't restate them:
- **`docs/improve-workflows-skills/README.md`** — the complete playbook (artifact kinds, shared-component extraction, authoring levers, the pruning pass, word-level economy, mechanics).
- **`docs/improve-workflows-skills/glossary.md`** — every term + the leading-word palette (use those tokens, not synonyms).

## Non-negotiables (quick reference — the full rules are in the playbook)
1. **Know the artifact kind — by frontmatter, never by path.** Both kinds install to `.agents/skills/<name>/SKILL.md`. A **lifecycle skill** (`metadata.stratos.layer: lifecycle`, authored in `src/workflows/`) orchestrates a phase, is user-invoked, and ships its own `references/`. An **execution skill** (`layer: execution`, authored in `src/skills/`) is self-contained discipline that may fire in an unscaffolded project, so it must carry no project-local refs.
2. **This repo DOES use `disable-model-invocation`.** Claude Code merged commands into skills, so it is now the only thing enforcing user-only invocation on Claude Code, Cursor and OpenClaw. Emit it with `triggers: ["user"]` (Devin) and an `agents/openai.yaml` sidecar (Codex) on every lifecycle skill. **Antigravity honours none of them** — restate user-only status in the `description`, and never call that enforcement.
3. **No OKF `type:` on framework artifacts.** `src/` is outside the OKF bundle scope (`okf-protocol.md` §1). Status/maturity lives in the `description`. `trigger:` survives only on `.agents/rules/*`.
4. **Single source of truth (§2).** Extract true duplication to `src/references/`; it **fans out** into each consuming skill's `references/` at build time — generated copies are not duplication, and hand-editing one is the error. Point, never re-paste, never cross-read another skill's body. When a citation is passed to an isolated subagent, use the absolute `.agents/skills/<name>/references/<file>.md` — a relative path resolves against repo-root cwd and fails silently.
5. **Never prune the protected classes (§4).** Load-bearing exhaustiveness, checkable/exhaustive completion criteria, safety/irreversible-action invariants, **sub-agent guardrails** (each is a dispatched agent's entire contract — keep every copy verbatim), leading-word tokens (`[UNCOVERED]`, `seam`, `[[G-xxx]]`…), and full context-pointer paths.
6. **Prune only executor-neutral prose.** Hunt no-op / duplication / sprawl / sediment; run the post-prune diff gate. When fidelity and economy conflict, fidelity wins.
7. **Mechanics.** Edit `src/` only (never `dist/` or `.agents/`); bump `version` **once per PR** on each changed file — a single increment above the last-released version (`patch` = wording/clarity, `minor` = behavior, `major` = breaking), **not** a fresh bump per edit/commit (the guard's baseline is the PR fork point). `timestamp:` stays on `src/` files as a build field; in-scope `.memory/`+`docs/` documents use `generated: {by, at}` instead. Rebuild via `python build/build.py`; confirm `build/validate.py` green.
