---
name: plan-html-skill-improvement-proposal
description: Universal proposal and phased roadmap to finish the plan-html skill's half-built hybrid architecture, fix verified defects, and make HTML earn its place for complex human-facing plans.
type: proposal
version: "1.1.0"
updated: 2026-06-18
---

# Universal Proposal — `plan-html` Skill & Templates

> **For the executing agent:** You may have no prior context. Read §0–§3 before editing. The skill's source of truth is `src/skills/plan-html/`; `dist/{claude-code,antigravity}/…` and `.agents/…` are **built copies** — never hand-edit them, regenerate via the build. Per project memory, this local folder is **not** a clone of origin: land changes in `src/`, rebuild, and reconcile via **PR** (do not push from the worktree). `src/skills/**` **ships** into consuming projects, so SKILL.md/templates must stay self-contained — **no links to `docs/`** (this plan lives in `docs/` and never ships, so it may cite anything).
>
> Companion artifact: the verified defect log at `.gemini/antigravity/brain/c9f852a2-…/analysis_results.md` (annotated 2026-06-18). This plan supersedes its "to be addressed later" items with a concrete sequence.

---

## 0. Objective

Make `plan-html` reliably **more helpful to a human reading a complex plan** than a long markdown file — while adopting HTML **only where it is most effective** (the skill's founding intent; see memory `plan-html-purpose`).

Three things get us there: (1) **finish** the hybrid architecture that is already ~60% scaffolded, (2) **fix** the verified correctness defects, and (3) **add** the one capability the skill is missing for big plans — navigation — plus a first-class interactive-editing path.

This is a roadmap, not a one-shot edit. It is sequenced in three phases; Phase 1 unblocks the rest.

---

## 1. Where the skill is today (verified inventory)

### 1.1 What already exists — and is good
- **7 discrete templates** (`assets/templates/`): `implementation-plan`, `trade-off-matrix`, `annotated-flowchart`, `status-report`, `incident-timeline`, `decision-record`, `wireframe-compare`. *(Target: 6 — `annotated-flowchart` is retired to a Mode-B diagram component; see §3/§6.)*
- **A composition foundation that is already partly built** (this reframes the whole effort):
  - [`assets/base-template.html`](../../src/skills/plan-html/assets/base-template.html) — design tokens, dark mode, a `<main id="content">` slot, a `plan-data` state holder, and **generic** `exportMarkdown()` + `copyJSONState()` toolbar buttons.
  - [`references/html-patterns.md`](../../src/skills/plan-html/references/html-patterns.md) — composition **primitives**: accordion, tabs, progress bar.
  - [`references/micro-app-patterns.md`](../../src/skills/plan-html/references/micro-app-patterns.md) — the **interactive-editing round-trip protocol** (emit controls → user adjusts → Copy JSON State → paste back), with a config-editor example.
- **A sound decision gate** (`SKILL.md`, Four-Scenario) that already encodes the industry framework (HTML for human-facing + spatial; markdown otherwise).

> **Implication:** custom-composition and interactive editing are *already designed*. The job is to **unify and finish**, not invent.

### 1.2 Verified defects (from the annotated analysis, re-confirmed in `src/`)
| ID | Defect | Where |
|:--|:--|:--|
| **D1** | Eval loads templates from `references/templates` but they live in `assets/templates` → all Template-Index assertions fail | `test/agentic-eval.ps1:72` |
| **D2** | `exportMd()` is **lossy** in 5 templates (drops sections / options / consequences / scores / annotations) — it scrapes the DOM instead of reading `plan-data` | all but implementation-plan |
| **D3** | No template builds the DOM from `plan-data` on load; the agent hand-writes DOM **and** `plan-data`, doubling tokens | all 7 |
| **D4** | The 7 templates **don't inherit `base-template.html`** — each re-implements its own export/state/toast, which is the root of D2 | all 7 |
| **D5** | Dual-source drift: state lives in both DOM and `plan-data` with nothing syncing them | architectural |
| **D6** | `copyState()` copies `{}` silently when `plan-data` is left empty | all 7 |
| **D7** | Eval asserts `plan-data` *exists*, never that it is *populated*; `wireframe-compare` missing from checklist | `test/agentic-eval.ps1` |
| **D8** | No navigation primitives (TOC / scroll-spy / anchor nav) → long plans aren't navigable | `references/html-patterns.md` |
| **D9** | A diagram adds little over markdown **standalone** — it's valuable only embedded in a larger plan; `annotated-flowchart` is also linear-only (no decisions/branches/loops) | template + patterns |
| **D10** | Gate triggers on "spatial" but not on **scale/complexity** (the ~100-line failure mode of markdown) | `SKILL.md`, `index.md` |

### 1.3 Root diagnosis
**D2–D6 are one bug:** state lives in the DOM instead of in `plan-data`, and templates don't share the base. **D8–D9 are the value gap:** the skill presents small static artifacts well but does nothing for a *large, branching* plan — which is exactly the case the founding intent targets.

---

## 2. Guiding principles (from the source review)

Validated against: Anthropic's ["Unreasonable effectiveness of HTML"](https://claude.com/blog/using-claude-code-the-unreasonable-effectiveness-of-html), Thariq Shihipar's "How I AI" talk ([Lenny's](https://www.lennysnewsletter.com/p/how-i-ai-html-is-the-new-markdown) / [ChatPRD](https://www.chatprd.ai/how-i-ai/claude-code-anthropic-thariq-shihipar-on-replacing-markdown-with-html)), the "Markup is the new Markdown" essay, and GitHub analogs ([html-effectiveness-skill](https://github.com/ghoulvspol/html-effectiveness-skill), [md2html](https://github.com/haidang1810/md2html), [claude-html-report-skill](https://github.com/voidful/claude-html-report-skill)).

1. **HTML earns its keep on *engagement with complexity*, not prettiness.** The win condition is "the human actually reads and critiques a complex plan instead of rubber-stamping it." Optimize for navigation + interaction, not decoration.
2. **HTML only for human-facing + complex.** Markdown for agent-loop content, repo docs, human→model input, and short/simple output. Add a concrete trigger: **≥ ~100 lines _or_ genuinely spatial**.
3. **`plan-data` is the single source of truth.** Render the DOM from it on load; export from it. This is also the answer to HTML's one real objection (editability) — and the prerequisite for round-trip editing.
4. **Keep the human in the loop two ways:** *navigation* for reading large plans; *round-trip* (Copy as JSON / Copy as Prompt) for editing them.
5. **Stay lean and self-contained.** Zero CDN, single file, dark mode, print, system fonts, a11y. Restraint over maximalism.

---

## 3. Target architecture — the hybrid, finished

Three layers, one shared state mechanism.

```
base-template.html  ──►  render(data) + exportMd(data) + copyState()   [ONE implementation, inherited]
        │
        ├─ Mode A · Discrete templates  (single-purpose spatial artifacts)
        │     trade-off-matrix · decision-record · incident-timeline ·
        │     status-report · wireframe-compare
        │     each = base + a plan-data schema + a render(data)
        │
        └─ Mode B · Complex-plan document  (NEW first-class path for big plans)
              navigable shell: TOC + scroll-spy + anchor nav + progress
              composes per-section components chosen by content shape
              (step cards · comparison cards · risk/decision callouts ·
               collapsible deep-dives · DIAGRAMS — component only, never standalone)

Micro-app overlay (interactive editing)  ──►  any Mode A/B output can carry
        editing controls; round-trips via Copy as JSON / Copy as Prompt.
        Flagship instance: the ROADMAP / Kanban editor.
```

**The single state rule (fixes D2–D6 at once):** every output embeds complete state in `<script id="plan-data">`; a `render(data)` builds the DOM on `DOMContentLoaded`; `exportMd()` and `copyState()` read **`plan-data`**, never the DOM. The agent writes the JSON; the template does the rest.

**Mode B is the headline change.** It directly answers §5's "implementation-plan is too thin": a complex plan is not one template — it's a navigable document composed of components, following the content-shape→component mapping pioneered by `md2html` (numbered list → step cards; "A vs B" → comparison cards; "must/avoid" → callout; long appendix → collapsible).

**Diagrams are a Mode-B component only — never a standalone template.** A diagram alone rarely beats markdown; it earns HTML only as part of a larger plan. The standalone `annotated-flowchart` template is therefore **retired**, and its rendering folds into reusable diagram *components* (inline **SVG** for decision/branch/loop; **CSS** for simple linear flow) in `html-patterns.md`, composed into Mode B. (See §6.)

---

## 4. The gate, sharpened (addresses D10)

Keep the Four-Scenario gate; add a complexity axis. Proposed decision table for `SKILL.md` (self-contained — no `docs/` links):

| Consumer | Content | → Format |
|:--|:--|:--|
| Agent loop / repo doc / human→model input | any | **Markdown** |
| Human | < ~100 lines **and** not spatial | **Markdown** |
| Human | ≥ ~100 lines (long plan) **or** spatial (comparison, dashboard, multi-section) | **HTML** |
| Human | needs to *edit* structured content | **HTML micro-app** |

A **diagram on its own does not trigger HTML** — it is only a component inside a Mode-B plan. The `< 5× markdown size` guard stays, but is reframed as a *sanity ceiling*, not the trigger — complexity/engagement is the trigger.

---

## 5. Phased roadmap

### Phase 1 — Foundation & correctness (unify + fix)
*Mostly mechanical, highest ratio of value to risk; unblocks Phases 2–3.*
1. **Single source of truth in `base-template.html`:** add `render(data)` (builds `#content` from `plan-data` on load); rewrite `exportMd()`/`copyState()` to operate on `plan-data`. (D3, D5, D6)
2. **Refactor all 7 templates onto the base:** each defines its `plan-data` schema + a `render(data)`; delete the bespoke lossy exporters. (D2, D4)
3. **Fix the eval** `agentic-eval.ps1`: correct `references\templates` → `assets\templates`; update the expected-template list (**add** `wireframe-compare.html`, **remove** `annotated-flowchart.html` and drop the `auth-flow-chart.html` artifact check per §6); add an assertion that `plan-data` parses to a **non-empty** object. The eval is **not** in CI today (§8), so this restores a *manual* harness; optionally port it to Python to wire into `build-guard` (see §8). (D1, D7)
4. **Sharpen the gate** in `SKILL.md` + `index.md` per §4 (the ~100-line trigger). (D10)
5. **Rebuild** `dist/` + `.agents/`; bump OKF versions of edited artifacts per the build bump-guard.

**Acceptance:** eval green; for every template, `exportMd()` round-trips **losslessly** from `plan-data`; `copyState()` never copies `{}`; the ratio/justification header is still emitted; `dist/` and `.agents/` regenerate clean.

### Phase 2 — Complex-plan path + reading ergonomics (the headline value)
1. **Navigation primitives** added to `references/html-patterns.md`: sticky TOC, scroll-spy, anchor links, reading-progress bar. (D8)
2. **New `plan-document` template** (or a rebuilt `implementation-plan`): the navigable shell + content-shape→component composition.
3. **Knowledge Explorer pattern** (search / filter / anchor) for large plans, added to `html-patterns.md`.
4. **Diagram components (not a template):** add inline-SVG layout snippets (decision / branch / loop) + CSS linear to `html-patterns.md`, composable into Mode B only. **Retire the standalone `annotated-flowchart` template** and remove it from `index.md` — a diagram alone doesn't beat markdown. (D9)

**Acceptance:** a ≥200-line plan renders as a navigable document with working TOC/scroll-spy; the gate routes large plans to Mode B; a Mode-B plan can embed a diagram component showing a decision + branch + loop; `annotated-flowchart` no longer appears in `index.md`.

### Phase 3 — Interactive editing (round-trip)
1. **Generalize `micro-app-patterns.md`:** standard **Copy as Prompt** + **Copy as JSON** emitters and a canonical, parseable change-block format.
2. **Flagship — ROADMAP / Kanban editor:** drag parent-feature cards between release columns → a live textarea mirrors moves (one line per move) → user pastes back → agent parses, runs the existing **Release Auditor**, and on a clean audit writes `docs/ROADMAP.md` + BACKLOG_MAP `Milestone` + GitHub milestones, then regenerates the HTML. HTML is an ephemeral *editor*, never a store. (This realizes analysis §4.)

**Acceptance:** a drag→paste→apply round-trip updates ROADMAP.md / BACKLOG_MAP / GitHub consistently; an audit `[BLOCKER]` halts the write and reports back; sources never diverge; works via copy-paste in both Claude Code and Antigravity (no reliance on `sendPrompt()`/browser MCP).

---

## 6. Diagrams decision (recap of the rendered comparison)

**Scope first:** a diagram is **not** a standalone output (it rarely beats markdown alone) — it exists only as a **component embedded in a Mode-B plan** (§3). The comparison below therefore governs only how that *embedded* component renders, not whether a diagram template exists (it doesn't).

Three options were compared on the same branching+looping flow:

| | A · CSS primitives | **B · Inline SVG (recommended)** | C · Mermaid runtime |
|:--|:--|:--|:--|
| Branches / decisions / loops | linear only | **full** | full |
| Authoring effort | low | medium (coordinates) | low (text) |
| Auto-layout | — | no | yes |
| File weight | minimal | **~1–3 KB** | +~50 KB JS |
| Zero-dep / offline | yes | **yes** | only if inlined |
| Fits skill ethos | yes | **yes** | drift |

**Decision: diagrams are component-only; render the embedded component with B (inline SVG) for decision/branch/loop and A (CSS) for simple linear flow; C rejected.** B is the only expressive option that preserves the zero-dep ethos. Its one cost — the agent computing SVG coordinates — is bounded by shipping a small set of **pre-built SVG layout snippets** (decision / branch / loop) the agent fills in, rather than drawing freehand. Revisit C only if a future need for large auto-laid-out graphs emerges.

---

## 7. Deliberately kept / not doing
- **Keep:** zero-CDN, single-file, dark mode, print stylesheet, system fonts, a11y, and the Four-Scenario gate philosophy.
- **Retire:** the standalone `annotated-flowchart` template — diagrams become Mode-B components only (discrete templates 7 → 6).
- **Not doing:** standalone diagram output; Mermaid-by-default (CDN/weight); a GitHub-Pages publishing pipeline (conflicts with privacy/self-contained — noted as optional future); a full analyzer-only rewrite (we keep the curated discrete templates).

---

## 8. Risks & open questions
- **JS-disabled / progressive enhancement:** `render(data)` means a blank page without JS. Acceptable for interactive artifacts; optionally keep a `<noscript>` fallback that prints the `plan-data` as text.
- **SVG authoring quality (Mode B diagrams):** mitigate with layout snippets; re-evaluate C if complex graphs become common.
- **Token ceiling vs. complex plans:** Mode B may exceed `5×` markdown; reframe the ceiling around complexity (§4) so genuinely large human-facing plans aren't bounced to markdown.
- **Build/distribution discipline:** every `src/` change must rebuild `dist/` + `.agents/` and ship self-contained (no `docs/` links); reconcile via PR per memory `local-repo-disconnected`. **`build-guard` enforces this** — it rebuilds from `src/` and fails on any `dist/`/`marketplace.json` drift (`build-guard.yml`), so Phase 1.5's rebuild is mandatory, not optional.
- **Resolved (CI coverage):** `agentic-eval.ps1` is **not** run by CI. `build-guard.yml` runs `build/build.py`, `build/validate.py`, `tests/test_subagent_spawning.py`, `tests/verify_scripts.py` (which covers only `validate_memory.py` / `sync_skills.py` / `scaffold.py`), a dist-drift check, and the L1 install harness — none invoke the PowerShell eval. **Consequences:** (a) D1 is *not* failing CI; it only false-fails when the eval is run manually, so its severity is "the skill's own correctness harness is currently useless," not "CI is red"; (b) **plan-html has no automated CI coverage at all.** Wiring the eval into `build-guard` is worthwhile but the eval is PowerShell while CI is Python-on-Ubuntu — so the clean path is to **port it to Python** (matching `verify_scripts.py`), treated as an optional Phase 1 add-on, not a commitment.

---

## 9. Appendix — source map
- **Verified defects:** annotated `analysis_results.md` (§3 issues, §6 synthesis).
- **Principles:** Anthropic HTML blog; Thariq "How I AI" (Lenny's / ChatPRD); "Markup is the new Markdown".
- **Inspiration:** `html-effectiveness-skill` (9 patterns — Knowledge Explorer, Kanban-export), `md2html` (analyzer model, TOC/scroll-spy, content→component mapping), `claude-html-report-skill` (shareability — deferred).
