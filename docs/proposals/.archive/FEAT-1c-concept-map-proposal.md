---
name: concept-map-additive-sibling-plan
description: Executable plan to add 1c_concept-map — an additive discovery-phase workflow that maps a foggy, multi-session idea as decision tickets on the EXISTING StratOS tracker (GitHub issues + BT-ids + native dependencies, BT-LOCAL fallback) and converges to a discovery brief — leaving 1a/1b intact. Edits product source under src/.
type: proposal
trigger: User. Do not run autonomously.
version: "0.11.0"
timestamp: 2026-07-09
---

# Executable Plan: `1c_concept-map` (additive) + grilling improvements

> **For the implementing agent (cold start):** Self-contained executable plan. Read **Path & build model** and **Prerequisites**, then **WHY**/**HOW**, then execute **WHAT** top-to-bottom. Each WHAT step names exact files + acceptance criteria. Stop only where a step says **[ASK]**. You are *building a workflow*, never running it against a real idea. Optional background: [`../research/v1-1-learnings-and-concept-framing-exploration.md`](../research/v1-1-learnings-and-concept-framing-exploration.md).

## Path & build model — READ FIRST
- **Product source of truth is `src/`.** Edit ONLY under `src/`. `.agents/`, `dist/claude-code/`, `dist/antigravity/` are **build outputs — never hand-edit.**
- **Layout:** workflows → `src/workflows/`; skills → `src/skills/`; references → `src/references/` (flat); rules → `src/rules/`; constitution → `src/constitution/`; commands → `src/commands/`; memory templates → `src/memory-templates/`.
- **Auto-discovery.** `build/build.py` globs `src/workflows/*.md` and copies `src/references/` wholesale — no manifest to register a new file. `build/validate.py` fails on a missing `version:` stamp **or** a broken reference citation — so a reference must EXIST before a workflow cites it.
- **Citation convention:** inside workflow *content*, cite references/rules by their INSTALLED runtime path (as `1b` does) — `.agents/workflows/.reference/<file>`, `.agents/rules/<file>` — never the `src/` path. Runtime artifacts a workflow writes use `docs/...` / `.memory/...`.
- **After editing:** `python build/build.py` → `python build/validate.py` (green) → propagate via the install/update flow. Bump OKF `version` **and** `timestamp` on every changed file.

## Prerequisites — read before editing (all under `src/`)
1. `src/constitution/AGENT.md` — §1: *a user-invoked orchestrator workflow may sequence other workflows*. `1c` is such an orchestrator (like `3z`; see Step 7).
2. `src/rules/okf-protocol.md` — frontmatter + `type:` registry.
3. `src/workflows/1a_research.md`, `1b_concept-framing.md` — the workflows `1c` composes/edits; the slug rule; `1a`'s mandatory Phase-1 propose-and-confirm gate.
4. `src/workflows/3b_create-issue.md` — **the tracker machinery `1c` REUSES**: `gh issue create`, `gh sub-issue add` (the non-core **`gh-sub-issue` extension** — provisioned in Step 1), BT-id minting (GitHub's shared sequence, per `memory-protocol.md`), the Label Registry, BACKLOG_MAP sync, and the **BT-LOCAL fallback**. `1c` invents none of this. **`src/workflows/3c_sprint-planning.md`** reads active issues by label — it must be taught to skip `concept:*` (Step 7b). *(There is no `3a` epic-creation verb — `3a` only makes release milestones; do not cite it for issue creation.)*
5. `src/workflows/3d_implement-issue.md`, `4a_verify-and-ship.md` — the Slice Completion Gate (completion-criterion model) + the subagent-with-inline-instructions dispatch pattern.
6. `src/workflows/3z_afk-loop.md` — currently claims to be *"the sole orchestrator permitted to invoke other workflows"* → reconcile (Step 7).
7. `src/commands/instantiate/Instantiate-StratosphereOS.md` (Checkpoint 6 label reconciliation) + `src/commands/update/Stratosphere-Update.md` — where `concept:*` labels get provisioned per project (Step 1).
8. `src/references/discovery_brief_template.md` — convergence output template + the frontmatter shape new references mirror.
9. `src/memory-templates/BACKLOG_MAP.md` — the canonical **Label Registry** (add `concept:*` here) + the row format.
10. `docs/improve-workflows-skills/README.md` + `glossary.md` — authoring playbook (H7). `README.md` (root) — command matrix.

---

## WHY

**The gap.** StratOS discovery (`1a → 1b → 2a → …`) assumes an idea is articulable enough to grill in **one** `1b` session and write up. Some ideas are not: too big for one session and wrapped in fog — a web of *interdependent decisions*, several needing research, a prototype, or a provisioning task before they can be decided. Today such an effort blows the smart zone in one oversized grill, or is forced prematurely into a PRD.

**Reuse the wheel — no second source of truth.** StratOS already has a mature tracker: GitHub issues, BT-ids (minted from GitHub's shared sequence), `gh sub-issue add`, the Label Registry, BACKLOG_MAP, and a BT-LOCAL fallback for disconnected/Antigravity projects. `1c` **uses exactly that.** A decision ticket **is a GitHub issue** (BT-id) with a `concept:*` label; blocking uses **GitHub's native issue dependencies** (`gh issue create --blocked-by`, `gh issue edit --add-blocked-by`, `gh issue view --json blockedBy`); the map is a **tracking issue** (`concept:map`) with the decision tickets as **sub-issues**; disconnected projects fall back to the **same BT-LOCAL** mechanism `3b` already uses. There is **one** tracker and **one** knowledge store (docs/ briefs). No parallel `CT-*` id space, no markdown decision ledger.

**So what's actually new (and why it earns its keep)?** Only two things: (1) a **pre-PRD decision-ticket type** (`concept:*`) that is *investigation, not implementation* — so it skips the slice machinery (ICE, scope-class, estimation, sprinting) that `3b` applies to build work; and (2) the **wayfinding process** — chart the fog, resolve one decision per session in dependency order, converge to the normal discovery brief. **Benefit:** a foggy, multi-session idea is worked as dependency-ordered decisions *in the tracker the team already uses*, converging to the same `docs/discovery/<slug>.md` brief `1b` produces — instead of one oversized grill or a premature PRD.

**Additive, not a refactor.** `1a`/`1b` are untouched behaviourally; `1c` is one new workflow, reversible by deletion.

**Deferred end-state (out of scope).** Folding `1b` behind an automatic routing "hub" is a future option — not this plan.

---

## HOW — behaviour to implement

### H1. Two entry points, and routing between them
- **`/1b_concept-framing`** — unchanged: a **sharp, single-session** idea → grill → brief.
- **`/1c_concept-map`** — a **foggy, multi-session** idea → chart a map, work one decision per session, converge to the same brief.
- **Discriminator ("is there a dependency graph?"):** enumerate the open questions blocking the brief; classify each as *user-decidable now* or *blocked* (needs research / prototype / task / another decision). Flat list of independent, user-decidable questions fitting one session → **`1b`**; any blocked question, interdependencies, or won't-fit-one-session → **`1c`**; can't even enumerate → **`1c`**.
- **Correctable without wasting work:** `1b` gets a routing hint to recommend `/1c`. If `1c`'s breadth-first scan surfaces **no fog**, don't silently bounce — offer to finish inline as a `1b`-style brief now, or hand the captured notes to `/1b`.

### H2. Storage — the EXISTING tracker, reused (no new store)
The concept map is an **issue tree on StratOS's normal tracker**, with the normal GitHub-or-BT-LOCAL duality — identical to how `3a`/`3b` treat epics and slices.
- **The map = a tracking issue** labelled `concept:map` (created with `gh issue create --label concept:map` — the `3b` primitive; there is no `3a` epic-creation verb). Its **body** holds: *Destination* (fixes scope) · *Notes* (domain, skills to consult, any plan-don't-do override) · *Not yet specified* (fog) · *Out of scope* · *Decisions so far* — an **index** (one line + link per closed decision ticket). One **BACKLOG_MAP row** for the map: Labels cell = `concept:map` + a `status:*` label (`status:in progress` while charting/working → `status:done` on convergence); the map is **milestone-exempt**. `concept:*` issues are **exempt from the BACKLOG_MAP single-status invariant and from `3c` sprint candidacy** (Step 7b/7c).
- **Decision tickets = child issues** (`gh sub-issue add <map#> <ticket#>`), BT-ids, labelled `concept:<type>`. **They bypass `3b`'s slice machinery** (no ICE, scope-class, coverage audit, milestone, or per-ticket BACKLOG_MAP sync) — they are investigation, not build work. They are discoverable via the map's sub-issue list + dependency graph, not individually rowed in BACKLOG_MAP.
- **The answer lives on its ticket** — recorded as the issue's **resolution comment**, then the issue is **closed**. The map's *Decisions so far* only indexes it (gist + link). Single canonical home per decision: its issue. (Fully resolves the earlier "index vs store" muddle — the ticket stores, the map indexes.)
- **Blocking — native dependencies where the installed `gh` supports them, else the text convention.** GitHub's current docs expose `gh issue create --blocked-by <#>` / `gh issue edit <#> --add-blocked-by <#>` / `gh issue view --json blockedBy` (native "Blocked" state on the board) — **but verify at build time** (`gh issue create --help`); if the installed `gh` lacks them, encode blocking as the **text `Blocked by: [#ids]` field** that `3b`/`3c` already speak. **Frontier = query** in whichever encoding is live: open ∧ no open blocker ∧ unassigned. (Never assume the native flags without verifying; the text convention is the StratOS-consistent fallback.)
- **Claiming = `gh issue edit <#> --add-assignee @me`** before any work (the assignee *is* the claim; GitHub arbitrates concurrency, so parallel sessions on one map are safe).
- **create-then-wire** (ids must exist before `--add-blocked-by`); **refer by name** in everything the human reads (title wrapping the link, never a bare `#42`).
- **BT-LOCAL fallback (no GitHub / Antigravity):** reuse `3b`'s existing fallback verbatim — `BT-LOCAL-<n>` ids, blocking as the text `Blocked by:` field, the map body + tickets kept in a local `docs/discovery/<slug>.map.md` (fallback-only; when GitHub is connected the tracking issue is canonical and no local map file exists). This is the **same** fallback all BT work uses — not a new scheme.

### H3. Ticket types (each sized to one session; HITL or AFK)
| Type (`concept:<type>`) | HITL/AFK | How `1c` resolves it |
|---|---|---|
| `research` | AFK **behind a one-exchange HITL confirm** | Run `1a`'s Phase-1 propose-and-confirm gate **inline**; then execute per `1a` — Quick inline, or Deep by spawning a subagent given `1a`'s loop **as inline instructions** (a `Task` subagent can't call the `/1a_research` command). Output `docs/research/<map-slug>-<question-slug>.md` (namespaced so multiple research tickets in one map don't collide, yet still glob-discoverable by `1b`'s External-Research probe); link it in the ticket's resolution + the map index. |
| `grilling` | HITL — *default* | Grill (H4) to resolve one decision; never answer the human's side. |
| `prototype` | HITL | `plan-html` (UI) **or** `3b` Template A spike (logic); link the asset on the ticket. |
| `task` | HITL/AFK | Prerequisite work (provision access, move data) — the only type that *does*, only to **unblock a decision**; record resulting facts (URLs, credential location, row counts) in the resolution. |

### H4. Grilling improvements (add inline to BOTH `1b` and `1c`)
On top of `1b`'s existing discipline (one-question-at-a-time, name-the-vagueness, ~5-question check-in, confirmation gate):
- **G1 — Recommend an answer with every question** (recommended answer + why, then ask).
- **G2 — Facts vs Decisions:** *where a codebase exists*, a fact discoverable in it you **look up, never ask**; a decision is the user's — put each and wait. (Also guards an AFK agent against grilling itself.)
- **G3 — Walk the decision tree, resolving dependencies one at a time** (`1b`'s ambiguity-first ordering also remains valid — note both).

> **Known single-source-of-truth exception (deliberate).** G1–G3 + the grill discipline are *duplicated* in `1b` and `1c`. Playbook default is extraction; deferred by decision until `1c` proves out. Pre-agreed follow-up: extract to `src/references/grilling-loop.md`, repoint both.

### H5. Vocabulary discipline (add to `1b`; `1c` grilling tickets apply the same)
Keep the `GLOSSARY.md` `[[G-xxx]]` lifecycle. Add **V1** scenario stress-tests; **V2** code-contradiction check (*where a codebase exists*); **V3** glossary-conflict callout (a term clashing with an existing `[[G-xxx]]`).

### H6. Chart → work → converge (the `1c` lifecycle)
- **Discover & resume (start of every Work session):** first list open maps — `gh issue list --label concept:map --state open` (fallback: glob `docs/discovery/*.map.md`) — and present them **by name**, or accept a map #/URL argument; only enter Chart when none match (prevents duplicate maps from slug drift). Then load the chosen `concept:map` issue (or local fallback map) as the low-res view. No cross-store reconcile needed: the tracker is the single canonical store.
- **Chart (session 1):** name the **destination** first (fixes scope); **breadth-first** grill for open decisions + first steps (no fog → offer inline-finish/`/1b`, H1); create the `concept:map` tracking issue + its BACKLOG_MAP row; **create-then-wire** the specifiable decision tickets (create as sub-issues, then `--add-blocked-by`); **stop — resolve nothing.**
- **Work (sessions 2..n):** compute the frontier (H2); take the user-named or first frontier ticket; **claim it (`--add-assignee @me`)**; resolve by type (H3); **post the answer as the ticket's resolution comment and close it**; index it in the map's *Decisions so far*; propagate — create-then-wire newly-surfaced tickets, **graduate fog**, rule mis-scoped tickets **out of scope** (close + one line in *Out of scope*), invalidate/close superseded tickets; **advance the frontier one dependency step per session, then stop.** You MAY resolve several *independent, cheap* frontier tickets in one session while they fit the smart zone — but never a ticket together with anything downstream of it, and recompute the frontier before each pick (one *dependency step*, not rigidly one issue — a two-question grill shouldn't cost a whole session).
- **Fog removal:** resolve the **frontier**, never the whole path; after each resolution re-run the **fog-or-ticket test** ("state the question precisely *now*?") and graduate any patch now sharp.
- **Plan, don't do:** every ticket resolves a *decision*; the pull to "just build it" means you've hit the edge of the map — converge. Only `task` tickets act, only to unblock a decision.
- **Converge (frontier empty ∧ fog empty):** synthesize `docs/discovery/<slug>.md` from the brief template using the closed tickets (their resolution comments + linked assets) as primary sources; run **RAT** (Skeptical Challenger subagent, as `1b` Phase 4.5) + **vocabulary crystallization** (`[[G-xxx]]`); hand off `/2a_write-prd` (or exit ramps: bug → `3b` Template B, spike → Template A, drop). **Completion criterion:** the brief emits the full section set `/2a` reads — Vocabulary, Actor, Problem, Chosen Framing, Non-Goals, Riskiest Assumption — so `2a` consumes a map-derived brief identically to a `1b` brief (verified: no `2a` change needed).
- **Archive lifecycle** (mirror `1b`'s): on convergence → close the `concept:map` tracking issue (children already closed) and mark its BACKLOG_MAP row done; the `docs/discovery/<slug>.md` brief is the durable output. On **abandonment** → close the map issue with a one-line why.

### H7. Authoring standards (hold to `docs/improve-workflows-skills/`)
- **Instruction-only** shipped artifacts (rationale stays here). Cut **no-ops**.
- **Completion criterion per phase** (checkable), per H6's bounds, modelled on `3d`'s Slice Completion Gate.
- **Leading words:** `destination`, `frontier`, `fog`, `claim`, `concept:<type>`, plus the palette (`seam` not "boundary"; `module`/`interface` not "service/API"; `BT-<padded>`, `RAT`, `[[G-xxx]]`, `ephemeral` for the computed frontier).
- **Progressive disclosure:** push the `gh` verbs to the operations reference; map-body shape → `concept-map-template.md`; research → `/1a_research`.
- **Sub-agent guardrails are contracts** (RAT Challenger's *"report only; do not write files"*; the inline `1a` research procedure) — keep verbatim.
- **Mechanics:** bump `version`+`timestamp` on every changed file; build + validate green.

---

## WHAT — execute in order (edit under `src/` only)

### Step 1 — Provision `concept:*` labels + `gh-sub-issue` (setup creates; update propagates text, then reconciles)
*(Verified against `scaffold.py` + `Stratosphere-Update.md`: **update is a pure file-scaffold + `SOS:BLOCK` merge — it performs no GitHub operations**, so label/extension *creation* cannot live in update itself.)*
- **[ASK]** confirm the five names (`concept:map` / `concept:research` / `concept:grilling` / `concept:prototype` / `concept:task`) don't collide with the taxonomy (`type:`/`priority:`/`size:`/`status:`/`area:`/`scope:`).
- **Add `concept:*` to the `label-canonical` `SOS:BLOCK`** in `src/memory-templates/BACKLOG_MAP.md` (it is a known managed block — id `label-canonical`). Two automatic consequences:
  - **New projects:** setup's Checkpoint 6 creates every canonical-registry label in GitHub → `concept:*` created.
  - **Existing projects:** `scaffold.py --update` block-merges the changed `label-canonical` block → the registry **text** gains `concept:*` with no new code. *(The actual GitHub labels are NOT created by update — next bullet.)*
- **Extend setup's Version-Control provisioning** to `gh extension install yahsan2/gh-sub-issue` — the map tree leans on `gh sub-issue add`, a non-core extension setup does not currently install (a latent `3b` gap this plan makes load-bearing).
- **Existing-project GitHub reconcile — fix the update flow, don't work around it** (it is **pre-ship**, so change it). Add **Phase 5: GitHub Reconcile** to `Stratosphere-Update.md`: after the file merge/commit (Phase 4), invoke `stratosphere-setup --re-reconcile-labels` (the existing standalone mode — one implementation, DRY), **extended** to also (a) create any missing canonical `concept:*` labels and (b) ensure the `gh-sub-issue` extension; skip gracefully if `gh` is absent (as setup does). Now `/stratosphere-update` is **self-complete** — files **and** GitHub state in one pass, no separate manual reconcile — and it is **generic**: any future label/tooling added to the canonical registry reconciles on the next update automatically.
**Done when:** `concept:*` is in the `label-canonical` block; setup creates the labels + installs the extension on new projects; and the update flow's new **Phase 5 GitHub-reconcile** lands the labels + extension on existing ones with no manual step.

### Step 2 — Create the map-body template reference
**Create** `src/references/concept-map-template.md` (mirror `discovery_brief_template.md`'s frontmatter incl. `version:`). Body = the `concept:map` **tracking-issue body** (and the BT-LOCAL fallback map file), with sections: *Destination · Notes · Not yet specified (fog) · Out of scope · Decisions so far* (index: `- [<ticket title>](<#/link>) — <gist>`). Note that answers live on the tickets, not here.
**Done when:** the file exists, valid frontmatter, sections per H2.

### Step 3 — Create the map operations reference
**Create** `src/references/concept-map-operations.md` (frontmatter incl. `version:`). **First verify the installed `gh`** (`gh issue create --help`): if issue-dependency flags are absent, encode blocking as the text `Blocked by:` field `3b`/`3c` already speak and have the frontier query parse it; `gh sub-issue add` requires the extension from Step 1. The verbs (reuse `3b` primitives; prefer native dependencies where present), each with a BT-LOCAL fallback:
- **Map:** `gh issue create --label concept:map …` (+ BACKLOG_MAP row) │ fallback: local map file + row.
- **Ticket (create-then-wire):** `gh issue create --label concept:<type> …` → `gh sub-issue add <map#> <#>` → `gh issue edit <#> --add-blocked-by <#>` │ fallback: `BT-LOCAL-<n>` row with text `Blocked by:`.
- **Claim:** `gh issue edit <#> --add-assignee @me` │ fallback: advisory note (single-writer).
- **Frontier query:** `gh issue list`/`gh issue view --json blockedBy,assignees,state` → open ∧ no open blocker ∧ unassigned │ fallback: scan local rows.
- **Resolve:** `gh issue comment <#> --body "<answer>"` → `gh issue close <#>` → add the index line to the map body │ fallback: record on the local row + index.
**Done when:** every H2/H6 verb has a concrete `gh` command + fallback here.

### Step 4 — Register the OKF type
**Edit** `src/rules/okf-protocol.md`: add `concept-map` to the `type:` registry if enumerated, scoped `Applies to: docs/discovery/*.map.md` (fallback map file) — no overlap with `discovery-brief`'s `docs/discovery/*.md`. Freeform registry → note no change. **This is the OKF frontmatter `type:` for the fallback map *file* only** — the map **issue** carries the `concept:map` **label** (the new `concept:` dimension), never a `type:concept-map` label.
**Done when:** `type: concept-map` valid and scoped, and the issue-label vs frontmatter-type distinction is stated.

### Step 5 — Create the `1c_concept-map` workflow
**Create** `src/workflows/1c_concept-map.md` (frontmatter `type: workflow HITL`, `trigger: User. Do not run autonomously.`, `version: "1.0.0"`, `timestamp`). Implement HOW §H1–H7; cite references via `.agents/workflows/.reference/...`. Phases:
- **Hand-off contract:** converges to `docs/discovery/<slug>.md` → `/2a_write-prd`; composes `/1a_research`, `plan-html`, and the tracker verbs via `.agents/workflows/.reference/concept-map-operations.md`; reuses the existing tracker (no new store).
- **Phase 0 — Resume & route/mode:** load the map (Work); run the H1 discriminator (→ `/1b` if flat); derive slug; no map → **Chart**, else **Work**.
- **Phase 1 — Chart** (H6): destination-first grill (H4+H5) → breadth-first scan (no fog → offer inline/`/1b`) → create `concept:map` issue + BACKLOG_MAP row → create-then-wire tickets → **stop.**
- **Phase 2 — Work** (H6): frontier → **claim** → resolve by type (H3; research runs `1a`'s inline gate then subagent-with-inline-procedure) → **resolution comment + close** → index in map → propagate → **one ticket, stop.** Enforce **Plan-don't-do.**
- **Phase 3 — Converge** (H6): synthesize brief from `.agents/workflows/.reference/discovery_brief_template.md` (`type: discovery-brief`); RAT (Skeptical Challenger subagent — guardrail verbatim) + vocabulary crystallization; hand off `/2a_write-prd` or exit ramps; run **Archive lifecycle**.
**Done when:** covers Resume, Route, Chart, Work (claim + one-ticket-per-session + answer-on-ticket), Converge, Archive; reuses the tracker + `1a`/`plan-html`/`3b`; each phase ends on its completion criterion; instruction-only.

### Step 6 — Additive edits to `1b_concept-framing`
**Edit** `src/workflows/1b_concept-framing.md` (surgical, additive): Phase 2 → **G1, G2, G3**; Phase 2/3 → **V1, V2, V3**; Phase 1 → 3-line routing hint (*dependency graph → recommend `/1c_concept-map`*); bump `version`+`timestamp`.
**Done when:** all present, no phase removed/reordered, version+timestamp bumped.

### Step 7 — Reconcile sibling workflows for `concept:*`
- **7a — `src/workflows/3z_afk-loop.md`:** it claims to be *"the sole orchestrator permitted to invoke other workflows."* Reword to acknowledge **multiple sanctioned orchestrators under AGENT.md §1** (`3z` = sole *AFK/autonomous* orchestrator; `1c_concept-map` = user-invoked discovery orchestrator).
- **7b — `src/workflows/3c_sprint-planning.md`:** Phase 1 maps active GitHub issues; add an explicit exclusion so issues carrying any `concept:*` label are **skipped from sprint candidacy and `[NEEDS_SPEC]` alerts** (pre-PRD decisions, never sprint work).
- **7c — `src/memory-templates/BACKLOG_MAP.md`:** document that the `concept:map` row carries `concept:map` + `status:*` (in progress→done), is **milestone-exempt**, and that `concept:*` issues are **exempt from the single-status invariant** and the sprint scan. **Put this inside an existing `SOS:BLOCK` (e.g. `backlog-rules`)** — out-of-block text is byte-frozen by the update invariants and would NOT propagate to existing projects. Verify the label-sync Action (`sync-labels-to-project.yml`) tolerates `concept:*` issues; exclude if it mis-files them.
- **7d — Harmonise the blocking convention to native dependencies (`3b`/`3c`), per user request.** Today `3b` records blocking only as text (`Blocked by: [IDs]`, line 26) + the BACKLOG_MAP Dependencies column, and `3c`'s Dependency Sorting (line 25) reads that text. Upgrade both to the same native-with-fallback approach `1c` uses (one blocking convention across the tracker):
  - **`3b`:** after minting a slice with prerequisites, wire native deps (`gh issue edit <#> --add-blocked-by <#>`, or `--blocked-by` on create), **keeping** the text `Blocked by:` line + Dependencies column as the human-legible **mirror** + BT-LOCAL/old-`gh` fallback.
  - **`3c`:** read dependency order from `gh issue view --json blockedBy` when supported, else the text mirror.
  - Verify `gh` support at runtime (as `1c` does). Confirm `3z`'s Conflict Scan and any other Dependencies-column consumer still work against the retained text mirror.
- Bump `version`+`timestamp` on every file touched.
**Done when:** `3z` no longer contradicts `1c`; `3c` skips `concept:*`; BACKLOG_MAP documents the `concept:map` exemptions *inside a block*; `3b`/`3c` use native deps (text mirror retained) — one blocking convention across `1b`-family, `3b`, `3c`, `1c`.

### Step 8 — Register in docs
**Edit** `README.md`: add `/1c_concept-map` next to `/1b_concept-framing`. Confirm the `type:concept-map` map row is documented in `src/memory-templates/BACKLOG_MAP.md`.
**Done when:** the matrix lists `/1c_concept-map`.

### Step 9 — Build, validate, verify
1. `python build/build.py` → `python build/validate.py` (fix missing-`version`/broken-reference/structural errors); propagate via the install/update flow.
1b. **Update propagation (existing projects):** after `build.py` regenerates `versions.json`, `python <plugin>/scripts/scaffold.py --update --dry-run` on a scaffolded project must stage the new `1c_concept-map.md` + both new references as **created** files and refresh edited `1b`/`3b`/`3c`/`3z`/`okf-protocol.md`; confirm the `label-canonical` block-merge carries `concept:*` into the project's BACKLOG_MAP, and that the update run's new **Phase 5 GitHub-reconcile** creates the `concept:*` labels + ensures `gh-sub-issue` (skipping gracefully when `gh` is absent).
2. **Dry chart** (with a tracker): confirm `/1c_concept-map` on a small invented foggy idea creates a `concept:map` issue + BACKLOG_MAP row + decision sub-issues with `--blocked-by` edges, and **stops without resolving**.
3. **Dry work:** confirm it computes the frontier from `--json blockedBy`, claims one ticket (`--add-assignee`), records the answer as the **resolution comment**, closes it, indexes it, and **stops after one ticket**.
4. **BT-LOCAL path:** confirm the disconnected fallback reuses `3b`'s BT-LOCAL mechanism (no `CT-*` scheme) — local map file + `Blocked by:` text.
5. **Labels:** confirm `stratosphere-setup` (new project) and `stratosphere-update` (existing project) provision `concept:*`.
6. **`1b` intact:** still runs end-to-end + shows the grill/vocab additions + routing hint.
6b. **Blocking convention:** `3b` writes native deps (+ retained text mirror), `3c` reads native (else text); a slice blocked by an open prerequisite is correctly held and ordered.
7. **Cleanup:** delete dry-run scratch artifacts (and any test issues).
**Done when:** build+validate green, all dry checks pass, scratch removed.

---

## Decisions already made (do not re-open)
- **Product source is `src/`;** `.agents//dist/` are build outputs; workflows auto-glob; every plugin `.md` needs `version:`; references must exist before being cited.
- **REUSE the existing tracker — no second source of truth.** Decision tickets are GitHub issues (BT-ids) with `concept:*` labels, **native GitHub dependencies for blocking where `gh` supports them (else the text `Blocked by:` convention `3b`/`3c` use — verify at build)**, sub-issues under a `concept:map` tracking issue, and the existing **BT-LOCAL fallback**. **No `CT-*` id space, no parallel markdown ledger.** *(Reverses the earlier "markdown-canonical" framing — the answer to host-agnosticism is StratOS's existing GitHub-or-BT-LOCAL duality, not a new store.)*
- **The answer lives on its ticket** (resolution comment); the map body only **indexes** closed tickets. Convergence output = the existing `docs/discovery/<slug>.md` brief.
- **Concept tickets bypass `3b`'s slice machinery** (ICE/scope/coverage/milestone/per-ticket BACKLOG-sync); only the **map** gets a BACKLOG_MAP row. **`concept:*` issues are exempt from `3c` sprint candidacy and the BACKLOG_MAP single-status invariant** (Step 7b/7c); the `concept:map` issue carries a `status:*` lifecycle and is milestone-exempt. The `gh-sub-issue` extension is provisioned by setup (Step 1).
- **`concept:*` labels + `gh-sub-issue`:** setup creates/installs on new projects; the update flow (**pre-ship**) **gains a Phase-5 GitHub-reconcile** that runs `stratosphere-setup --re-reconcile-labels` (extended for extensions) after the file merge, so existing projects get labels + extension in one `/stratosphere-update` pass. File-level changes propagate deterministically via `scaffold.py` (registry text through the `label-canonical` block-merge; the new `1c` workflow + references as new `versions.json` managed files).
- **One blocking convention:** `3b`/`3c` upgraded to native GitHub dependencies (text `Blocked by:`/Dependencies-column retained as mirror + fallback), matching `1c` (Step 7d, per user request).
- **`1c` is a sanctioned orchestrator** like `3z` (AGENT.md §1); `3z`'s "sole orchestrator" wording is narrowed to AFK (Step 7).
- **Additive sibling, not a refactor;** name `1c_concept-map`; **one dependency step per session** (independent cheap tickets may batch within the smart zone; never a ticket with its downstream); charting resolves nothing.
- **Research reuses `1a`** behind its inline propose-confirm gate; **no new prototype skill** (UI → `plan-html`, logic → `3b` Template A).
- **Grilling duplicated in `1b`/`1c` for now** (deliberate SSOT exception); **G1–G3 into both**; extraction to `src/references/grilling-loop.md` once `1c` proves out.
- **Output contract unchanged:** converges to the discovery brief → `2a_write-prd`; **"PRD" not renamed**; `3a`/`3b`/`3c` not collapsed. `1c` has its own Archive lifecycle.

## Refinement log
- 2026-07-08 — created (hub-refactor framing).
- 2026-07-09 — v0.2.0/0.3.0: e2e source comparison; `concept:*` labels; routing probe + fog mechanics.
- 2026-07-09 — v0.4.0: staged additive approach; cold-start executable plan (WHY/HOW/WHAT).
- 2026-07-09 — v0.5.0: corrected edit target to `src/`; Path & build model.
- 2026-07-09 — v0.6.0: applied `docs/improve-workflows-skills` playbook (H7); renamed file → `FEAT-1c-concept-map-proposal.md`.
- 2026-07-09 — v0.7.0: integrated an adversarial review (operations reference; removed false "no native blocking" claim provisionally; reconciled `3z`; archive lifecycle; etc.).
- 2026-07-09 — **v0.8.0: applied user feedback.** (1) `1c` is explicitly a sanctioned orchestrator like `3z` (Step 7 simplified). (2) **GitHub native issue dependencies are real** (`gh --blocked-by`/`--add-blocked-by`/`--json blockedBy`) — blocking + frontier now use them. (3) **Removed the second source of truth:** dropped the `CT-*` markdown ledger; decision tickets are GitHub issues (BT-ids) reusing the existing tracker + BACKLOG_MAP + BT-LOCAL fallback; answers live on the ticket, the map indexes; added the explicit "what's actually new / benefit" rationale to WHY. (4) `concept:*` labels provisioned via `stratosphere-setup` + `stratosphere-update` (Step 1), not ad-hoc.
- 2026-07-09 — **v0.9.0: integrated a second adversarial pass.** Blocking is now **verify-native-`gh`-else-text-fallback** (not asserted as given); added the map **status lifecycle** + `3c`/single-status **exemptions** (Step 7b/7c); **discover-open-maps resume** (no duplicate maps from slug drift); **"one dependency step per session"** (cheap independent tickets may batch — fixes death-by-sessions / bootstrap token waste); **`gh-sub-issue` extension provisioned** in setup; `update` label reconcile = `stratosphere-setup --re-reconcile-labels`; dropped the wrong `3a`-epic analogy; clarified `concept:map` is an issue **label** vs the `concept-map` OKF frontmatter type; namespaced research output. Confirmed `/2a` needs no change.
- 2026-07-09 — **v0.10.0: user feedback + setup/update verification.** (1) **`3b`/`3c` migrated to native dependencies** (text mirror retained) so there is one blocking convention across the tracker (Step 7d). (2) **Verified setup/update against `scaffold.py` + `Stratosphere-Update.md`:** update performs **no GitHub ops** (pure file-scaffold + `SOS:BLOCK` merge), so Step 1 was corrected — `concept:*` lives in the `label-canonical` block (text propagates on update), GitHub label/extension creation happens via setup Checkpoint 6 (new) or `stratosphere-setup --re-reconcile-labels` (existing, prompted by update); the new `1c` workflow + references propagate automatically as new `versions.json` managed files; and Step 7c's exemption docs must live **inside** a block or the update invariants freeze them out. Added update-propagation + blocking-convention verify steps.
- 2026-07-09 — **v0.11.0:** the update flow is **pre-ship**, so instead of working around its file-only nature, **add Phase 5 (GitHub Reconcile) to `Stratosphere-Update.md`** — after the file merge it runs the existing `stratosphere-setup --re-reconcile-labels` (extended to ensure `gh` extensions), skipping gracefully without `gh`. Existing projects now get `concept:*` labels + `gh-sub-issue` in a single `/stratosphere-update`, and the mechanism is generic for any future label/tooling addition. Supersedes v0.10.0's manual-reconcile workaround.
