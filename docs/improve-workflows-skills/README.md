---
type: reference
title: Improving Workflows & Skills
description: Dev-time discipline for authoring and improving StratOS's own skills (src/skills) and workflows (src/workflows). Repo-local guidance — NOT shipped to consumer projects.
version: "1.2.0"
timestamp: 2026-06-23
---

# Improving Workflows & Skills

Dev-time playbook for authoring, editing, and pruning **StratOS's own** skills (`src/skills/`) and workflows (`src/workflows/`). Lives in `docs/`, **never ships** — consumer projects don't author the framework.

**Self-contained pair:** this playbook + its companion lexicon **[`glossary.md`](glossary.md)** (every term and the leading-word palette, defined inline). Bold terms below are defined there.

Consult it when: writing a new skill/workflow, editing one, or running a pruning/refactor pass. **Root virtue:** a skill/workflow exists to make the agent take the same *process* every run — every lever below serves that **predictability**.

---

## 1. Two artifact types — know which you're editing

The single most important distinction, because the rules below (especially §2 extraction) depend on it. A **skill** is self-sustaining discipline; a **workflow** is a user-driven orchestrator.

| | **Skill** (`src/skills/`) | **Workflow** (`src/workflows/`) |
|---|---|---|
| Installs as | `dist/*/skills/` — **registers globally** | a `/` **command** (`commands/`; Antigravity surfaces `.agents/workflows/`) |
| Invoked by | model **or** user, via its `description` | **user only** — the channel enforces it |
| Runs where | **any** project, even unscaffolded | only inside a **scaffolded** StratOS project |
| Dependencies | **must be self-contained** — no project-local refs | **may cite** `.agents/workflows/.reference/*` |
| Role | self-contained discipline; reusable everywhere | orchestrates a phase; **may delegate to skills** |
| `disable-model-invocation` | set it to make a skill user-only | N/A — a command is already user-only |
| `trigger:` frontmatter | inert — the **`description`** drives invocation | inert — documentation only |

**Consequences you'll keep hitting:**
- A skill can fire in a project that was never scaffolded, so it **cannot depend on a scaffolded file** — bundle its discipline inline.
- A workflow always runs in a scaffolded project, so it **can and should** point at shared references instead of duplicating them.
- Don't add `disable-model-invocation` to a workflow (redundant); to tune whether a *skill* auto-fires, edit its **`description`**, not `trigger:`.

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
- **Shared reference → `src/references/*`** → builds/scaffolds to `.agents/workflows/.reference/<name>.md`. **Workflows** cite it by that installed path; consumers **point, never re-paste, never cross-read another workflow's body**. Fix a weak **context pointer**'s *wording*, don't inline.
- **Skills can't use that path** (they run unscaffolded — §1). Instead of extracting a skill's content to a project-local file, **have the workflow delegate to the skill** and keep the skill self-contained.

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

**Never prune:** load-bearing exhaustiveness ("list every AC by name"), safety invariants, or sub-agent guardrails (§2). They read like over-statement but are the lever.

## 5. Mechanics

- Edit `src/` only — never hand-edit `dist/`. Rebuild via `python build/build.py`; confirm `build/validate.py` + the install-harness are green. Bump OKF `version` + `timestamp` on every changed file.
- This folder is `docs/`-only: it never ships, so it may need not be self-contained against the repo — but it **is** self-contained as a pair (playbook + `glossary.md`), so an author needs nothing else open.
