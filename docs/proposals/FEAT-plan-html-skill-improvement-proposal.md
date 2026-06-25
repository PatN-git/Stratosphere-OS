---
name: plan-html-skill-improvement-proposal
description: Consolidated proposal + execution-ready implementation plan to finish the plan-html skill's half-built hybrid architecture, fix verified defects, make HTML earn its place for complex human-facing plans, and keep the skill portable (description-based triggering, defined output locations, generic editor with the domain apply in workflows). Self-contained for a fresh agent in Claude Code or Antigravity.
type: proposal
version: "2.1.1"
updated: 2026-06-24
---

# `plan-html` Skill — Consolidated Proposal & Implementation Plan

> **This single document is both the rationale (Part I) and the execution-ready plan (Part II).** It supersedes the standalone v1.1.0 proposal. It was reviewed by three adversarial subagents; their blocking findings are incorporated, and the residual factual errors of v1.1.0 are corrected (`.agents/` is not built; templates 7→6; eval line-72; Phase 3 references no longer assume nonexistent repo artifacts). **v2.1** adds three findings from an audit against `docs/improve-workflows-skills`: an explicit skill/workflow split for the editor (**F1**), reliable description-based triggering (**F2**), and a defined output-location convention (**F3**).
>

> **For the executing agent — you may have NO prior context.** Read Part II §0–§1 before editing. Source of truth is `src/skills/plan-html/`; `dist/` is generated; `.agents/` is a stale local install. Land changes in `src/`, rebuild, reconcile via **PR** (this local folder is not a clone of origin — do not push). `src/skills/**` ships into other projects, so SKILL.md/templates stay self-contained (no `docs/` links, no external URLs).

---

# PART I — Rationale & Decisions

## 1. Objective
Make `plan-html` reliably **more helpful to a human reading a complex plan** than a long markdown file — while adopting HTML **only where it is most effective** (founding intent; memory `plan-html-purpose`). Three moves: **finish** the ~60%-scaffolded hybrid architecture, **fix** the verified defects, **add** the missing capability for big plans (navigation) plus a first-class interactive-editing path. Sequenced in three phases; Phase 1 unblocks the rest.

## 2. Where the skill is today (verified inventory)
**Already built and good:** 7 discrete templates (`assets/templates/`); a partly-built composition foundation — `assets/base-template.html` (tokens, dark mode, `plan-data` holder, generic toolbar), `references/html-patterns.md` (accordion/tabs/progress), `references/micro-app-patterns.md` (the round-trip editing protocol); and a sound Four-Scenario decision gate in `SKILL.md`. **So custom-composition and interactive editing are already designed — the job is to unify and finish, not invent.**

**Verified defects (re-confirmed in `src/` on 2026-06-24 — the doc-reorg PRs did not touch the skill):**

| ID | Defect | Where |
|:--|:--|:--|
| **D1** | Eval loads templates from `references/templates`; they live in `assets/templates` → all Template-Index assertions fail | `test/agentic-eval.ps1:72` |
| **D2** | `exportMd()` is **lossy** in 5 templates (drops sections/options/consequences/scores/annotations) — scrapes the DOM instead of reading `plan-data` | all but implementation-plan |
| **D3** | No template builds the DOM from `plan-data` on load; agent hand-writes DOM **and** `plan-data` (double tokens) | all 7 |
| **D4** | Templates **don't inherit `base-template.html`** — each re-implements export/state/toast (root of D2) | all 7 |
| **D5** | Dual-source drift: state in both DOM and `plan-data`, nothing syncing | architectural |
| **D6** | `copyState()` copies `{}` silently when `plan-data` is empty | all 7 |
| **D7** | Eval asserts `plan-data` *exists*, never *populated*; `wireframe-compare` missing from checklist | `test/agentic-eval.ps1` |
| **D8** | No navigation primitives (TOC/scroll-spy/anchor) → long plans aren't navigable | `references/html-patterns.md` |
| **D9** | A diagram adds little over markdown **standalone**; `annotated-flowchart` is also linear-only | template + patterns |
| **D10** | Gate triggers on "spatial" but not on **scale** (the ~100-line markdown failure mode) | `SKILL.md`, `index.md` |

**Root diagnosis:** D2–D6 are one bug (state in the DOM, not `plan-data`; templates don't share the base). D8–D9 are the value gap (good at small static artifacts; useless for a large branching plan — the case the founding intent targets).

## 3. Guiding principles (from the source review)
Validated against Anthropic's ["Unreasonable effectiveness of HTML"](https://claude.com/blog/using-claude-code-the-unreasonable-effectiveness-of-html), Thariq Shihipar's "How I AI" talk ([Lenny's](https://www.lennysnewsletter.com/p/how-i-ai-html-is-the-new-markdown)), "Markup is the new Markdown", and GitHub analogs ([html-effectiveness-skill](https://github.com/ghoulvspol/html-effectiveness-skill), [md2html](https://github.com/haidang1810/md2html), [claude-html-report-skill](https://github.com/voidful/claude-html-report-skill)).
1. **HTML earns its keep on engagement with complexity, not prettiness** — optimize for navigation + interaction.
2. **HTML only for human-facing + complex.** Markdown for agent loops, repo docs, model input, short output. Concrete trigger: **≥ ~100 lines OR genuinely spatial**.
3. **`plan-data` is the single source of truth** — render the DOM from it; export from it. Answers HTML's editability objection and enables round-trip editing.
4. **Keep the human in the loop two ways:** navigation (reading) + round-trip Copy-as-JSON / Copy-as-Prompt (editing).
5. **Lean & self-contained:** zero CDN, single file, dark+light, print, system fonts, a11y. Restraint over maximalism.

## 4. Target architecture — the hybrid, finished
- **Foundation** — `base-template.html` holds the canonical foundation block (`planData`/`copyState`/`exportMd`/`showToast` + `DOMContentLoaded→renderBody`). The authoritative copy of what templates inline.
- **Mode A · Discrete templates** (single-purpose spatial artifacts): `trade-off-matrix`, `decision-record`, `incident-timeline`, `status-report`, `wireframe-compare` — plus `implementation-plan` (refactored, then superseded by Mode B). **`annotated-flowchart` is retired in Phase 1 → 6 templates.**
- **Mode B · Complex-plan document** (NEW): navigable shell (TOC + scroll-spy + anchor nav + progress) composing per-section components by content shape (steps→step cards, "A vs B"→comparison cards, "must/avoid"→callout, appendix→collapsible, diagram→SVG component).
- **Micro-app overlay** (Phase 3): edit controls + copy-paste round-trip. **The skill ships only a *generic* editor** — a board template over a domain-agnostic `{columns, cards}` schema that emits a canonical change payload. Any **domain apply** (e.g. a roadmap drag mapped back to release→feature, audited, then written to ROADMAP/BACKLOG/GitHub) lives in a **workflow** (`3a_version-planning`), never the skill — **Finding F1** (keeps the skill portable; see §8 and Phase 3). The skill must never know "release", "feature", or "milestone" — only columns and cards.

**Diagrams are a Mode-B component only — never a standalone template.** The standalone `annotated-flowchart` is retired; diagrams become reusable components (inline SVG for decision/branch/loop; CSS for linear) in `html-patterns.md`.

> *Naming:* "Mode A / Mode B" are this proposal's internal labels only. The **shipped** `index.md`/`SKILL.md` should use plain, prior-recruiting language — "discrete templates" and "complex-plan document" — not coined jargon (`improve-workflows-skills §3`, leading words).

## 5. The gate, sharpened (D10)
| Consumer | Content | → Format |
|:--|:--|:--|
| Agent loop / repo doc / human→model input | any | **Markdown** |
| Human | < ~100 lines **and** not spatial | **Markdown** |
| Human | ≥ ~100 lines **or** spatial (comparison/dashboard/multi-section) | **HTML** |
| Human | needs to *edit* structured content | **HTML micro-app** |

A **diagram alone does not trigger HTML** (component only). The `<5×` size rule is a sanity ceiling, not the trigger.

## 6. Diagrams decision
Diagrams are component-only; render with **B (inline SVG)** for decision/branch/loop and **A (CSS)** for linear; **C (Mermaid runtime) rejected** (CDN/weight breaks the zero-dep ethos). B's one cost — the agent computing SVG coordinates — is bounded by shipping pre-built layout skeletons it fills.

## 7. Deliberately kept / not doing
- **Keep:** zero-CDN, single-file, dark+light, print, system fonts, a11y, the Four-Scenario gate.
- **Retire:** standalone `annotated-flowchart` (diagrams → Mode-B components; 7→6).
- **Not doing:** standalone diagram output; Mermaid-by-default; GitHub-Pages publishing (privacy/self-contained conflict — optional future); a full analyzer-only rewrite.

## 8. Invocation & output (audit findings F2, F3 vs `improve-workflows-skills`)
**F2 — Triggering is the `description`, not the gate or `trigger:`.** Skill auto-invocation is driven by the **`description` frontmatter** (`improve-workflows-skills §1`; `trigger: AFK` is **inert**). The current description is defensive ("…ONLY when… Defaults to markdown") and under-fires. Two levers, most-reliable first:
1. **Explicit workflow delegation** (deterministic): where a workflow knows it is producing a human-facing plan, it **invokes `plan-html` outright**. `2b` already does (wireframe-compare); add it to `3a`'s roadmap step and any "review this plan" moment.
2. **Ad-hoc auto-fire — front-load the description** with trigger conditions + leading words, guard second (Appendix F). Reuse the same trigger words (*plan, roadmap, matrix, dashboard, comparison*) across the description, workflows, and prompts so the model links them.

**F3 — Output location is undefined → define by lifespan.** `SKILL.md` says only "write a standalone `.html` file" (no directory), so outputs scatter. Convention:
- **Ephemeral** (decision aids, the board editor, throwaway comparisons) → **`.tmp/`** (gitignored) or OS temp — not committed.
- **Durable** (tied to a feature/decision) → **beside the artifact** it documents (`docs/design/BT-…`, etc.) — committed.
- The **skill stays path-agnostic** (writes where told → preserves portability, `§1`); the *convention* lives in the **invoking workflows** (`2b` already sets `docs/design/BT-…-directions.html`) and is noted in `improve-workflows-skills`.

---

# PART II — Execution

## §0. Orientation

### 0.1 Where things live
| Path | Role | Edit? |
|:--|:--|:--|
| `src/skills/plan-html/` | **Source of truth** | ✅ |
| `dist/claude-code/skills/plan-html/`, `dist/antigravity/skills/plan-html/` | Built copies; skill content **byte-identical** between them | ❌ generated |
| `.agents/.../plan-html/` | **Stale local install** — not built, not edited. **Scope every verification grep to `src/`** so it never misleads you. | ❌ ignore |
| `build/build.py` | Rebuilds **`dist/` + `.claude-plugin/marketplace.json`** from `src/` (does **NOT** touch `.agents/`) | run it |
| `build/validate.py` | Structural + bump validation (fails if a `.md` body changed but `version` didn't) | run it |
| `.github/workflows/build-guard.yml` | CI: `build.py`, `validate.py`, `tests/test_subagent_spawning.py`, `tests/verify_scripts.py`, a `dist/` drift check, + a 2nd job `tests/install-harness/run-L1.sh`. **The PowerShell eval is NOT run by CI.** | — |
| `src/skills/plan-html/test/agentic-eval.ps1` | Skill eval (PowerShell) | edit + run |

### 0.2 Golden rules
1. Edit only `src/`; never hand-edit `dist/` (CI fails on drift).
2. After any `src/` edit: `python build/build.py`, commit regenerated `dist/` + `marketplace.json` together. (Do **not** "rebuild `.agents/`" — the build doesn't produce it.)
3. Every `.md` under the skill needs OKF frontmatter; the build **raises** on a missing version stamp, and `validate.py` **fails if a `.md` body changed but `version` wasn't bumped**. So bump `version` + set `updated` **in the same step** you edit a `.md` body (`.html` files are not version-checked).
4. Shipped files self-contained: no `docs/` links; templates have **zero external URLs/CDNs**.
5. Template *source* files lead with `<!-- TEMPLATE: <name> | slots: … -->`; the `<!-- plan-html | … ratio: Nx … -->` token header is for **generated output**, not template source.
6. Single file, inline CSS/JS, `prefers-color-scheme` dark+light, system fonts.
7. Never push to origin; reconcile via PR.

### 0.3 Environment detection (Claude Code vs Antigravity) — the only places it matters
| Concern | Claude Code | Antigravity |
|:--|:--|:--|
| Subagents (Phase 1.2 / Verify) | `Task`/Agent tool (`general-purpose`) | its subagent mechanism; **if unavailable, do the fan-out sequentially yourself** |
| Round-trip UX | `sendPrompt()` **and** copy-paste | copy-paste **only** |
| Eval / harness shell | PowerShell + Node | `pwsh` if present, else the Node/Python harness |

**Hard rule:** never build a feature that works *only* via `sendPrompt()`. Copy-paste must always work.

## §1. The single source-of-truth contract (the core fix)
**Problem today:** `base-template.html` defines `exportMarkdown()`/`copyJSONState()` (not the names below); templates are standalone files that **do not include it** and each re-implements a lossy `exportMd()`; state is duplicated in the DOM and `plan-data`.

**New contract:** (1) state lives **only** in `<script id="plan-data" type="application/json">{…}</script>`; (2) `renderBody(data)` builds the DOM on load — the agent writes only the JSON; (3) `exportMd()` calls **DOM-free** `toMarkdown(data)` (data→string), `copyState()` serializes `plan-data` → lossless by construction.

**Sharing mechanism (standalone files can't `include` a base):** each template **inlines the canonical foundation block verbatim** and defines **only** its own `renderBody(data)` + `toMarkdown(data)`; it must **not** redefine `planData`/`copyState`/`exportMd`/`showToast`. `base-template.html` is the authoritative copy of the block.

```html
<script id="plan-data" type="application/json">{}</script>
<script>
function planData(){return JSON.parse(document.getElementById('plan-data').textContent||'{}');}
function showToast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2000);}
function copyState(){navigator.clipboard.writeText(JSON.stringify(planData(),null,2)).then(()=>showToast('JSON state copied'));}
function exportMd(){navigator.clipboard.writeText(toMarkdown(planData())).then(()=>showToast('Markdown copied'));}
document.addEventListener('DOMContentLoaded',()=>{renderBody(planData());if(typeof afterRender==='function')afterRender(planData());});
// EACH TEMPLATE DEFINES: renderBody(data) and DOM-free toMarkdown(data)
</script>
```

## §2. Phase 1 — Foundation & correctness (fixes D1–D7, D10)
1. **Branch:** work on a dedicated feature branch off the latest `main` — **never commit the overhaul to `main`**. First run `git rev-parse --abbrev-ref HEAD`: if you're already in a prepared worktree on its own feature branch, use it; otherwise create one (any clear name). Do **not** assume a specific branch name pre-exists — verify, don't hardcode.
2. **Rewrite `base-template.html`** to the canonical block (rename `exportMarkdown→exportMd`, `copyJSONState→copyState`; add `planData()` + the `DOMContentLoaded→renderBody` dispatch). Keep tokens/toolbar.
3. **Refactor templates + regenerate full-state fixtures — SUBAGENT FAN-OUT.** Spawn one subagent per template in parallel (Appendix E.1). Each returns **two files**: (a) the refactored `assets/templates/<name>.html` — inlines the foundation block, `renderBody(data)` rebuilds the existing DOM **preserving every CSS class/id the stylesheet targets**, DOM-free `toMarkdown(data)` serializes **every** schema field (explicitly including fields the old export dropped, e.g. `decision-record`'s options/pros/cons/consequences); (b) a **fully-populated** mock `test/output/<mock>.html` (every field; arrays ≥2; optional fields present) — *this replaces today's partial mocks like `{"phase":2,…}`, which cannot drive render/lossless checks.* Templates: `trade-off-matrix`, `decision-record`, `incident-timeline`, `status-report`, `wireframe-compare`, and `implementation-plan`. (Do **not** refactor `annotated-flowchart` — it is retired next.)
4. **Fix the eval `test/agentic-eval.ps1`** (do **before** step 5): on **line 72** change the literal `references\templates` → `assets\templates` (**do not touch `$root`/`$PSScriptRoot`**); expected-template list **add** `wireframe-compare.html`, **remove** `annotated-flowchart.html`; Part-3 artifacts **remove** the `auth-flow-chart.html` row and point remaining rows at the regenerated fixtures; add a per-artifact assertion that `plan-data` parses to a **non-empty** object. (This `.ps1` is structural/gate-only — the behavioral gate is §4 below.)
5. **Retire standalone `annotated-flowchart`:** delete `assets/templates/annotated-flowchart.html` and `test/output/auth-flow-chart.html`; remove its row from `assets/templates/index.md` **and bump `index.md`'s `version`+`updated` in this same step** (body changed → validate.py requires it).
6. **Sharpen `SKILL.md` + `index.md`** (bump both): (a) the **gate** (Appendix C); (b) **F2 — the `description` frontmatter** for reliable auto-invocation (Appendix F) and **delete the inert `trigger: AFK`**; (c) **F3 — the Output Rules** to state the lifespan-based output convention (Appendix G), keeping the skill path-agnostic.
7. **Add behavioral harness** `tests/verify_plan_html.mjs` (Node — preinstalled on CI ubuntu-latest; no `npm install`, because `toMarkdown` is DOM-free); wire it into `build-guard.yml` as a **new step in the `verify-dist` job after `tests/verify_scripts.py`** (note `test_subagent_spawning.py` is a workflow-phrase whitelist and does **not** cover the skill).
8. **Rebuild & sync:** `python build/build.py` → `python build/validate.py .` → confirm `git status --porcelain dist/ .claude-plugin/marketplace.json` shows only intended changes. Commit `src/` + `dist/` together.

**Acceptance:** §Verification 5.1–5.3 clean; harness proves lossless export + idempotent render for every Mode-A template; `annotated-flowchart` gone from `index.md` and `dist/`; no unaccounted `dist/` drift.

## §3. Phase 2 — Complex-plan path + reading ergonomics
1. **Navigation primitives → `html-patterns.md`** (bump version): sticky TOC, scroll-spy (vanilla IntersectionObserver), anchor links, reading-progress bar; inline, zero-dep.
2. **New `assets/templates/plan-document.html` (Mode B):** shell driven by `plan-data` (`{title, sections:[{id,title,kind,…}]}`); `renderBody` dispatches per `section.kind` (`steps`/`compare`/`callout`/`prose`/`deepdive`/`diagram`); TOC from sections; scroll-spy active state; nav `aria-label`; `toMarkdown` serializes all sections. Add to `index.md` (bump). Include a full-state mock.
3. **Knowledge Explorer pattern → `html-patterns.md`:** vanilla client-side search/filter over sections.
4. **Diagram components → `html-patterns.md`** (Mode-B only): inline-SVG `decision`/`branch`/`loop` skeletons + CSS linear. No standalone template; no Mermaid/CDN.
5. **Gate routing:** plans ≥ ~100 lines or multi-section → `plan-document`. Rebuild.

**Acceptance:** a ≥200-line plan renders as a navigable doc with working TOC + scroll-spy; a Mode-B plan embeds a diagram component showing a decision + branch + loop; the extended gate tests pass.

## §4. Phase 3 — Interactive editing (round-trip) — **generic editor only (Finding F1)**
> **Skill/workflow seam (F1).** The editor splits at *generic render* vs *domain apply*. The **skill** owns the generic board editor + round-trip protocol and knows only **columns and cards**. Any **domain apply** (map cards↔releases, audit, write ROADMAP/BACKLOG/GitHub) lives in the **`3a_version-planning` workflow**, which already owns the Release Auditor + milestone writes. Dependency direction: `3a → plan-html` (workflow delegates to skill — same pattern as `3d → micro-tdd`, `improve-workflows-skills §2`). This keeps `plan-html` portable and keeps irreversible writes behind `3a`'s user-gated HITL, not inside a model-invocable skill. *(This repo has no `docs/ROADMAP.md` / Release Auditor anyway — `BACKLOG_MAP.md` ships only as a `src/memory-templates/` project-instance template — so the apply is necessarily downstream.)*

1. **Generalize `micro-app-patterns.md`** (bump version) — define the **documented seam**: a domain-agnostic **board schema in** (`{columns:[{id,label}], cards:[{id,label,column,meta?}]}`) and a **canonical change payload out** (Copy-as-JSON / Copy-as-Prompt; one change per line, e.g. `card-007 -> col-2`). Both sides depend only on this neutral format, so they evolve independently. Document the **copy-paste-only** constraint.
2. **Ship a generic board-editor template** (a Mode-A `board` template + a worked demo in `test/output/`): drag cards between columns → live `<textarea>` mirrors moves → paste back → documented parser reconstructs the board state. HTML is an **ephemeral editor, never a store**. The same primitive serves a roadmap, sprint board, or triage board — anything board-shaped.

**Out of scope here (separate `3a` follow-up):** the roadmap *apply* — build board from BACKLOG/PRDs → invoke `plan-html` to render → on paste-back, map cards→releases → run `3a`'s **Release Auditor** → on a clean audit, write ROADMAP.md + BACKLOG `Milestone` + GitHub milestones. Tracked as an enhancement to `3a_version-planning`, not part of this skill proposal.

**Acceptance:** round-trip parse test (5.5) passes — the emitted change payload re-parses to the original board state; a malformed line is **rejected, not silently dropped**; the template contains **no domain words** ("release"/"feature"/"milestone") — only columns/cards; works via copy-paste in both environments.

## §5. Verification (deterministic-first)
Run at each phase end + a final gate. Earlier tiers are automatable/CI-runnable — do not rely on eyeballing.

**5.1 Static/structural:** `build.py` (no error) → `validate.py .` (pass) → `dist/` drift is intended; `pwsh …/agentic-eval.ps1` exits 0 (structural/gate only); grep **scoped to `src/skills/plan-html`**: no `http(s)://|cdn|<script src=|<link ` in templates, no `docs/` links, every `.md` versioned, every template has `prefers-color-scheme:dark`; token-header regex on **generated** `test/output/*.html`.
- **Portability (F1):** grep all of `src/skills/plan-html/**` for `ROADMAP|BACKLOG|milestone|release|\bGitHub\b` → **zero** matches (domain leakage = fail); no template hardcodes an output directory.
- **Triggering (F2):** `SKILL.md` `description` contains the trigger words (plan/roadmap/matrix/dashboard/comparison) + the `≥~100-line`/spatial condition, and the inert `trigger: AFK` is gone. Sanity-fire 3 representative "make me a … plan/roadmap/matrix" prompts → the skill is selected (manual or harness).

**5.2 Behavioral harness `tests/verify_plan_html.mjs` (the real gate for D2/D3/D4).** Per template + Mode-B doc, with a fully-populated fixture:
- **Lossless export:** extract the inline `<script>`, eval `toMarkdown` in a Node `vm` (no DOM — it's DOM-free), call `toMarkdown(fixture)`; recursively walk the fixture for every **content** leaf scalar and assert each appears in the output. **Exclude structural/dispatch keys** (`id` anchor-slugs, `kind` discriminators, booleans-as-UI-state) — including them produces false failures. *(Verified empirically: the same check false-failed on `id`/`kind` until excluded, then passed 71/71 content leaves on a dogfooded Mode-B doc.)* Top-level-key checks are insufficient — this must catch a dropped nested `ratings[o][c].score` or `kpis[].unit`.
- **Render idempotence** *(local/dev — jsdom or the env's browser MCP)*: load → assert content root non-empty → `root.innerHTML=''` → `renderBody(planData())` → assert non-empty and equal to first render. (Lossless export is the hermetic CI gate; render idempotence is a strong dev gate.)
- **Gate model:** extend the eval `Gate()` to take `lineCount` + `diagramOnly` and assert: human/non-spatial/120-line → `html`; human/non-spatial/40-line → `markdown`; human/`diagramOnly` → `markdown`; plus the ~100 boundary.

**5.3 Adversarial verification subagent (required, structurally independent).** Give it **only** the acceptance criteria + the `git diff`/paths — **not** your notes. It must **run `tests/verify_plan_html.mjs` itself** and paste exit codes/failing assertions, then try to falsify each claim (a dropped leaf; a template still scraping the DOM; a gate case routing wrong; a diagram that can't express a loop; any `dist/` file not regenerated). **"broken" or "unconfirmed" = blocker.** Prompt: Appendix E.2.

**5.4 Dual-environment:** `diff -r dist/claude-code/skills/plan-html dist/antigravity/skills/plan-html` is empty (scope to the **skill subtree** — the dist roots legitimately differ: `stratosphere-setup` is a command in claude vs a skill in antigravity, plus different manifests). No feature depends on `sendPrompt()`.

**5.5 Round-trip parse test (Phase 3):** fixture → emitter → parser → assert reconstructed == input; malformed line rejected.

**Final gate:** all applicable tiers clean for every shipped phase.

## §6. Ship
Commit per phase (`Co-Authored-By: Claude <noreply@anthropic.com>`); open a PR **from your feature branch → `main`** (`gh pr create --base main`); PR body = phases + pasted verification evidence. Never commit the overhaul to `main` or push to origin directly.

---

## Appendix A — `plan-data` schemas (Mode-A)
*Diff each against the live template's line-1 slot comment before fan-out.*
- **trade-off-matrix:** `{title, options:[{name,desc}], criteria:[{name,desc}], ratings:{[opt]:{[crit]:{score:1-5,note}}}}`
- **decision-record:** `{title, id, status, context, options:[{name,pros:[],cons:[]}], decision, consequences:[]}`
- **incident-timeline:** `{title, events:[{time,title,severity,body,milestone?:bool}]}`
- **status-report:** `{title, period, kpis:[{label,value,unit,trend,good}], sections:[{title,status,body}]}`
- **wireframe-compare:** `{title, options:[{name,desc,rationale,wireframe_regions:[{name,desc}]}], lenses:[{name,desc}], ratings:{[opt]:{[lens]:{score:1-5,note}}}}`
- **implementation-plan:** `{title, phases:[{name,status,items:[{text,done:bool}]}]}`

## Appendix B — primitive pointers
Foundation JS: §1. Reuse: `html-patterns.md` accordion/tabs/progress. Add (Phase 2): TOC, scroll-spy, anchor links, reading-progress, client-side filter, SVG diagram skeletons (decision/branch/loop).

## Appendix C — gate drop-in (SKILL.md)
The 4-row table in Part I §5, verbatim, plus: "A diagram on its own does NOT trigger HTML — it is only a component inside a complex-plan document. `<5×` size is a sanity ceiling, not the trigger."

## Appendix D — defect / finding → fix map
**Defects:** D1 eval path (P1.4) · D2 lossy export (§1 + P1.3, proven 5.2) · D3 no render-from-data (§1 + P1.3, proven 5.2) · D4 templates don't inherit base (§1 + P1.3) · D5 dual-source drift (§1) · D6 empty copyState (§1) · D7 eval gaps (P1.4) · D8 nav primitives (P2.1) · D9 standalone diagram (P1.5 + P2.4) · D10 gate trigger (P1.6, proven 5.2 gate model).
**Audit findings (vs `improve-workflows-skills`):** F1 skill/workflow split for the editor (§4 + Phase 3 + 5.1 portability) · F2 description-based triggering (§8 + P1.6 + Appendix F) · F3 output-location convention (§8 + P1.6 + Appendix G).

## Appendix E — ready-to-paste subagent prompts
**E.1 (template refactor + fixture, one per template):** "Refactor the standalone HTML template `src/skills/plan-html/assets/templates/<NAME>.html` onto a new contract, and produce a full-state mock. (1) State lives ONLY in `<script id='plan-data'>`. (2) Inline this foundation block verbatim and DO NOT redefine its functions: <PASTE §1 BLOCK>. (3) `renderBody(data)` rebuilds the template's existing DOM from `data`, **preserving every CSS class/id the stylesheet targets** (read the current file's CSS + slot comment). (4) `toMarkdown(data)` — **DOM-free** — serializes EVERY field in this schema, including any the old export dropped: <SCHEMA from Appendix A>. (5) Delete all bespoke export/copy/toast code. Keep zero-dep, dark+light, single-file. Then write `src/skills/plan-html/test/output/<MOCK>.html` populated with a fully-populated fixture (every field, arrays ≥2, optional fields present). Self-check: `toMarkdown(fixture)` contains every content leaf value; blanking the content root and calling `renderBody(planData())` rebuilds the page. Return both files."
**E.2 (adversarial verifier — give ONLY this prompt + the diff):** "You are a skeptical, independent reviewer. Inputs: the acceptance criteria in this plan's §5, and this diff/paths: <PATHS>. RUN `node tests/verify_plan_html.mjs` and paste its exit code and any failing assertions. Then try to FALSIFY each claim against `src/skills/plan-html/`: a `plan-data` content leaf `toMarkdown` drops; a template still reading the DOM for export; a gate example routing wrong; a diagram that cannot express a loop; any `dist/` file not regenerated from `src/`. Return: claim | holds/broken | file:line + harness output. Default to 'broken' if you cannot positively confirm. Trust only the files and the harness."

## Appendix F — `description` drop-in (SKILL.md frontmatter, F2)
Replace the defensive description with a front-loaded one (trigger conditions + leading words first, guard second), and **delete `trigger: AFK`**:
> `Use when presenting a complex or spatial plan to a human — roadmap, trade-off matrix, status dashboard, multi-section implementation plan, decision record, side-by-side comparison. Generates one self-contained interactive HTML file; fires on ≥~100-line or spatial human-facing output. Defaults to markdown for agent-loop content, repo docs, model input, and short/simple output.`

## Appendix G — output-location convention (SKILL.md Output Rules, F3)
Add to Output Rules — the skill stays **path-agnostic** (it writes where the caller says; the directory is the caller's/workflow's choice):
> "Write to a standalone `.html` file at the path the caller specifies. Convention by lifespan: **ephemeral** artifacts (decision aids, editors, throwaway comparisons) → `.tmp/` (gitignored) or OS temp; **durable** artifacts (tied to a feature/decision) → beside the artifact they document (e.g. `docs/design/…`). Invoking workflows set the concrete path (e.g. `2b` → `docs/design/BT-<n>-directions.html`)."
