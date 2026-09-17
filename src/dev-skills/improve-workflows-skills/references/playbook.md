---
type: reference
title: Improving Workflows & Skills
description: Dev-time discipline for authoring and improving StratOS's own skills (src/skills) and workflows (src/workflows). Repo-local guidance — NOT shipped to consumer projects.
version: "2.1.0"
generated:
  by: Patrick Nennewitz
  at: 2026-09-15
---

# Improving Workflows & Skills

Dev-time playbook for authoring, editing, and pruning **StratOS's own** skills (`src/skills/`) and workflows (`src/workflows/`). Carried inside the `improve-workflows-skills` dev skill, which **never ships** — consumer projects don't author the framework.

**Self-contained pair:** this playbook + its companion lexicon **[`glossary.md`](glossary.md)** (every term and the leading-word palette, defined inline). Bold terms below are defined there. Both load with the skill; an author needs nothing else open.

Consult it when: writing a new skill/workflow, editing one, or running a pruning/refactor pass. **Root virtue:** a skill/workflow exists to make the agent take the same *process* every run — every lever below serves that **predictability**.

---

## 1. Two artifact kinds — know which you're editing

Both install to the same place. The distinction is **frontmatter, never location**. A **lifecycle skill** orchestrates a phase and is user-driven; an **execution skill** is self-sustaining discipline.

| | **Lifecycle skill** (`src/workflows/`) | **Execution skill** (`src/skills/`) |
|---|---|---|
| Installs as | `.agents/skills/<name>/SKILL.md` (+ `.claude/skills/`) — `/<name>` on every host | same path, same shape |
| `metadata.stratos.layer` | `lifecycle` | `execution` |
| `metadata.stratos.mode` | `HITL` or `AFK` | — |
| Invoked by | **user only** — enforced by frontmatter, not by channel | model **or** user, via its `description` |
| Runs where | only inside a **scaffolded** StratOS project | **any** project, even unscaffolded |
| Dependencies | ships its own `references/` (fanned out at build) | **must be self-contained** |
| Role | orchestrates a phase; **may delegate to** execution skills | reusable discipline |

**Consequences you'll keep hitting:**
- An execution skill can fire in an unscaffolded project, so it **cannot depend on a scaffolded file** — bundle its discipline inline.
- Both kinds live in `.agents/skills/`. To tell them apart, read `metadata.stratos.layer`. Never infer from the path.
- `AGENTS.md` §2 precedence keys off `layer`. An artifact without one cannot be placed in the precedence order.

### Frontmatter contract

| | Lifecycle skill | Execution skill |
|---|---|---|
| Required | `name` (== parent dir, `^[a-z0-9]+(-[a-z0-9]+)*$`), `description` (≤ 1024 chars) | same |
| Invocation | `disable-model-invocation: true` + `triggers: ["user"]` + `agents/openai.yaml` sidecar | omit all three |
| `metadata` | `stratos.layer: lifecycle`, `stratos.mode: HITL\|AFK`, `stratos.version` | `stratos.layer: execution`, `stratos.version` |

- **This repo DOES use `disable-model-invocation`.** It was previously unnecessary because workflows compiled to slash commands, which the model could not auto-fire. Claude Code has since merged commands into skills, so the field is now **the only thing enforcing user-only invocation** on Claude Code, Cursor and OpenClaw. Devin needs `triggers: ["user"]`; Codex needs the `agents/openai.yaml` sidecar. Emit all three.
- **Antigravity honours none of them.** It reads only `name` and `description`. Every lifecycle skill's `description` must restate its user-only status — a prompt-level signal, **not enforcement**. See `AGENTS.md` §8.
- **No OKF `type:` on either kind.** `src/` is outside the OKF bundle scope (`okf-protocol.md` §1). Status/maturity lives in the `description`.
- **`trigger:` is retired on skills.** It survives only on `.agents/rules/*` files.

### Shared references fan out — that is not duplication

A reference used by several skills is authored **once** in `src/references/` and **copied into each consuming skill's `references/`** at build time. `confidence-scale.md` lands in five skill directories; `github-issue-relations.md` in five. This satisfies §2's single-source-of-truth rule — the source is single, the copies are generated and never hand-edited. Editing an emitted copy is the error, not the copy's existence.

### Distribution — bundled vs on-demand (and where a launcher must live)

- **Bundled skills** live in `src/skills/` → build → `dist/*/skills/`; they ship with the plugin and register globally.
- **On-demand packs** (opt-in / experimental) live in `src/experimental/<name>/`, are registered in `external-skills.json`, and are fetched by **`sync-skills`** into `.agents/skills/<name>/`. `build/validate.py` guards that no `experimental/` path leaks into `dist/`.
- **`sync_skills.py` installs by *name* under `.agents/skills/<name>/`** — the same namespace bundled lifecycle skills occupy. A fetched pack is therefore `/<name>`-invocable on every host, including Antigravity. `sync_skills.py` carries a **reserved-name guard**: it must never overwrite a bundled skill directory.
- **A bundled launcher is now optional, not structural.** An on-demand pack is directly invocable once fetched, so a launcher earns its place only by existing when the pack does **not** — e.g. `3x-jules-dispatch`, which tells the user to run `/sync-skills`. Name it distinctly from the pack it fronts.

## 2. Shared components over duplication — propose the refactor

Keep each meaning in **one place** (**single source of truth**). Duplication costs tokens *and* drifts. Repeated blocks across files — or one workflow reading **inside another workflow's body** — are a refactor signal.

### Detect → classify → propose
1. **Detect** a repeated rubric / template / protocol / checklist, or a cross-body read.
2. **Classify** before cutting — not everything that looks duplicated should merge:
   - **True duplication** → extract to a shared reference (below).
   - **Sub-agent guardrails** (`"do not edit/write/commit…"`) → **NOT duplication.** A dispatched sub-agent runs in an *isolated context* and never sees the surrounding prose; the guardrail is its entire contract. Keep every copy.
   - **Safety / irreversible-action reinforcement** (branch checks, "don't modify production code", PR-dup guards) → defensible defense-in-depth even when the constitution states it too. Don't salami-slice away every copy of an invariant.
3. **Propose the refactoring — don't silently rewrite.** State *what* to extract, *where* it lives, *who points at it*; get approval (especially for load-bearing content); then extract, repoint consumers, rebuild.

### Where it lives — and which artifact may use it (ties to §1)
- **Shared reference → `src/references/*`** → fans out to `.agents/skills/<consumer>/references/<name>.md`. Skills cite it by that path; consumers **point, never re-paste, never cross-read another skill's body**. Fix a weak **context pointer**'s *wording*, don't inline. **When the citation is passed to an isolated subagent, use the absolute `.agents/skills/<name>/references/<file>.md`** — a relative path resolves against repo-root cwd and fails silently.
- **Execution skills can't rely on a scaffolded path** (§1). Instead of extracting their content to a project-local file, **have the lifecycle skill delegate to the execution skill** and keep the latter self-contained.

### Worked examples in this repo
- ✅ `confidence-scale.md` — one rubric shared by `4a` + `4b` (each adds a one-line audit-scope; the bands live once).
- ✅ `issue-templates.md` — Template A/B shared by `3b` + `4b`; `4b` now **points at the reference** instead of reading `3b`'s body.
- ✅ `micro-tdd` stays **self-contained**; `3d` **delegates** the RED→GREEN→REFACTOR loop to it — *not* extracted to a project-local reference, because it's a global skill (§1).
- ⛔ Avoid: deleting a sub-agent guardrail in `2b`/`3b`/`4b` because it "looks redundant" — it's the sub-agent's only contract.

## 3. Authoring levers (apply when writing)

Each is one move; reach for the **leading-word palette** in [`glossary.md`](glossary.md) — use those tokens, **not their synonyms**.

- **Leading word** — encode a behaviour in a reused *token*, not a sentence, and **reuse the same token across artifacts** so the agent links them (`[UNCOVERED]` in both `3b`'s Coverage Auditor and `3d`'s gate; `vertical slice`, `seam`, `[[G-xxx]]`). Strengthen a weak word (`be thorough` → `relentless`); don't coin jargon that recruits no priors. Pick from the palette so authors don't drift into synonyms (`seam` not "boundary", `module` not "service").
- **Completion criterion** — end every step on a bound that is *checkable* and, where it matters, *exhaustive* ("every AC maps to a passing test", not "looks complete"). This is the defence against **premature completion**. Live example: `3d`'s Slice Completion Gate.
- **Progressive disclosure** — inline what every branch needs; push branch-specific **reference** behind a **context pointer** whose *wording* is reliable. Respect the skill self-containment limit (§1).
- **Single source of truth** — one meaning, one place → §2.

## 4. Pruning pass (apply when revising)

Run this over an artifact when you touch it or after it grows. Hunt **sentence-by-sentence** for the failure modes (defined in [`glossary.md`](glossary.md)):
- **No-op** — the line changes nothing vs. the model's default. It's **model-relative** — settle by *running* the artifact, not debating; raise the bar for AFK/weaker models. Author-facing *rationale* ("we do X because Y") is usually a no-op for the executor — keep the instruction, drop the why (it belongs in `docs/`).
- **Duplication** — → §2.
- **Sprawl** — too long even when every line is live; cure with the ladder (disclose reference; split by branch/sequence).
- **Sediment** — stale lines that accreted; the default fate without a pruning discipline.

### Never prune — the protected classes
They read like over-statement but are the lever. Do **not** cut, dilute, summarize, or word-trim any of:
- **Load-bearing exhaustiveness** — "list every AC by name", "map *every* `[BASELINE]`/`[DIFFERENTIATOR]` story to a slice or `[UNCOVERED]`".
- **Checkable/exhaustive completion criteria** — "every AC maps to a passing test", "never summarize as 'looks complete'", "never silently ship".
- **Safety / irreversible-action invariants** — branch checks, "don't modify production code", PR-dup guards. Keep them universal — don't narrow one to sub-agent scope only.
- **Sub-agent guardrails** (§2) — a dispatched sub-agent runs isolated and never sees surrounding prose; the guardrail is its **entire contract**. Keep every copy, verbatim.
- **Leading-word tokens** — `[UNCOVERED]`, `seam`, `depth`, `[[G-xxx]]`/`[[A-xxx]]`/`[[DR-xxx]]`. Keep the **exact token**, never a synonym; never drop a `[[…]]` reference.
- **Context-pointer paths** — cite the full installed path (`.agents/skills/<name>/references/<file>.md`, `.agents/rules/okf-protocol.md`), not a bare basename.

### Over-prune — the anti-pattern (guard against each)
**Over-prune** = cutting or diluting a protected class under the guise of economy. Real regressions seen in practice:
- deleting a sub-agent guardrail because it "looks redundant";
- collapsing an exhaustive output/completion contract to a summary fragment ("map every X…" → "check coverage");
- swapping a leading-word token for a synonym, or dropping a `[[…]]` reference;
- shortening a context-pointer to a bare basename (`per .agents/rules/okf-protocol.md` → `per okf-protocol`);
- narrowing a universal safety invariant to sub-agent scope only;
- rewriting a file from a **stale base** (version moves sideways/backward) instead of editing in place — clobbers newer content;
- introducing an inaccuracy while compressing (a claim the body contradicts, e.g. describing a HITL-gated loop as "without human gating");
- a copy/merge error (a duplicated or half-deleted clause).

### Post-prune diff gate (run before calling a prune done — checkable, not vibes)
Diff against the pre-prune version. For **every** removed or reworded span, name which non-protected class it was (**no-op / duplication / sprawl / sediment**); if you can't, restore it. Then confirm: every guardrail, completion criterion, safety invariant, leading-word token, and pointer path still present; `version` bumped **forward** (never sideways/backward); `build/validate.py` green. **When fidelity and economy conflict, fidelity wins — keep the words.**

## 4.5. Word-Level Economy

Perform a systematic, word-level economy pass on every sentence. Prune words that carry no structural or behavioral meaning for an agent.

**Scope limit (read §4 "Never prune" first):** these cuts apply to *executor-neutral prose only*. A sub-agent guardrail, completion criterion, safety invariant, leading-word token, or context-pointer path is **not** prose to trim — article/preposition/filler-compressing one of those is **over-pruning** (§4), not economy. Trim around the protected content, never through it.

- **Article audit:** Review all articles ("the", "a", "an"). Retain only when referencing a specific, disambiguated noun (e.g. "read the active issue's description"). Otherwise, cut them (e.g., "query the tracker" → "query tracker").
- **Preposition audit:** Compress multi-word prepositions and directional phrases (e.g. "in order to" → "to"; "with respect to" → "for"; "proceed to Phase 5" → "Phase 5").
- **Filler verb audit:** Drop imperative assertions that add no constraints (e.g., "you MUST load and read" → "read"; "confirm and proceed" → "confirm"). All instructions are mandatory by default.
- **Redundant qualifiers:** Eliminate redundant modifiers (e.g., "explicit user confirmation" → "user confirmation"; "strictly adhere to" → "follow").
- **Cross-workflow boilerplate:** Tool-invocation patterns (like explaining *how* to call `invoke_subagent` or `Claude Code's Task tool`) are no-ops. Keep the behavioral intent ("invoke a subagent"), but cut the tool mechanics.
- **Duplicate rationale:** Cut explanatory sentences unless they prevent a documented agent failure mode (e.g., keeping a one-line explanation of why guess-minting issue IDs causes collisions is allowed to prevent drift).

### Worked Example:
- **Before:** *"Query the tracker to compute the \"frontier\" (the set of open, unblocked, unassigned decision tickets)"*
- **After:** *"Query tracker for frontier (open, unblocked, unassigned tickets)"*
- **Cuts:** Pruned articles ("the" ×2), compressed "to compute the" to "for", dropped the verbose definition ("set of... decision tickets") in favor of direct qualifiers.

## 5. Mechanics

- Edit `src/` only — never hand-edit `dist/`. Rebuild via `python build/build.py`; confirm `build/validate.py` + the install-harness are green. Bump `version` once per PR on every changed file. `timestamp:` stays on `src/` files (build field); in-scope `.memory/`+`docs/` documents use `generated: {by, at}` instead (`okf-protocol.md` §2).
- These references never ship, so they need not be self-contained against a consumer project — but they **are** self-contained as a pair (playbook + `glossary.md`).
