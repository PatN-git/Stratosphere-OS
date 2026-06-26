---
name: 2b_interface-design
description: Design the interface (UI layout or non-UI contract) of a feature, post-PRD and pre-slicing.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.1.3"
timestamp: 2026-06-18
---

# Interface Design

**Hand-off contract:** Writes a path-aware design document to `docs/design/BT-<padded>-interface.md` by instantiating `.agents/workflows/.reference/design-doc-template.md`. Appends the design path to the parent GitHub issue body. Downstream workflows (`3b`, `3d` Phase 0, `4a`) read this document.

---

## Phase 1: Surface & Scope Gate
*Resume check: if `docs/design/BT-<padded>-interface.md` already exists with `status: draft`, do NOT restart. Read it, recover the path/branch from `surface` and the body block, and resume — Path B/C at Phase 4 (or Phase 2.5 if direction not yet selected); Path A at Phase 4 if a `## Design Brief (issued)` section is present in the doc, else Phase 3 (or Phase 2.5 if direction not yet selected).*


1. Load PRD from `docs/prds/BT-<padded>-<feature>.md`.
2. If there is NO external surface/code change (docs-only/process) → skip this workflow; handoff to `/3b_create-issue`.
3. If the feature has NO UI surface (backend/api/workers/db/library) → Path C.
4. If it has UI, read "Design Source" from `.memory/DESIGN_RULES.md` §2 and branch:
   - `stitch` or `claude-design` → Path A (generator-assisted). Branch A1 = Whole-page (new page / full redesign); Branch A2 = Feature-on-existing-page. (If the generator's tools/MCP are absent: Path A1 stays Path A; Path A2 prompts user, or defaults to Path B if AFK [record re-route in design doc]).
   - `native`  → Path B (Reference-driven native).
   - *unset / still the placeholder* `<stitch | claude-design | native — set during /stratosphere-setup>` → ask the user once (AskUserQuestion / ask_question), write the answer back to §2, then branch per above.

## Phase 2: Design Doc Initialization
1. Instantiate `docs/design/BT-<padded>-interface.md` from the template. Prepend OKF frontmatter per `.agents/rules/okf-protocol.md` using `type: interface-design`.
2. Populate the metadata shell (`slug`, `bt`, `prd`, `surface` = `ui-generator-page|ui-generator-feature|ui-manual|non-ui`, `status`: `draft`, `updated`). Ensure `surface` matches the chosen path (Path A → `ui-generator-page|ui-generator-feature`; Path B → `ui-manual`; Path C → `non-ui`).
3. **Define the Aha Moment & Time-to-Value:** Ask *"What is the single moment the user first feels this was worth it, and how fast can they reach it after signup (aim: first 30 seconds)?"* Design the flow backward from it: strip blockers between entry and aha, no carousels/intro slideshows, drop the user into the core thing. (Path C: aha = "time to first successful API call / first integration").
4. Fill the narrative sections (Surface & Scope, Actors & Core Flows, Aha Moment & Time-to-Value, States/Edge Classes) from the PRD now — before any pause. Keep exactly ONE body block.
5. Classify the run: **bootstrap** = `.memory/DESIGN.md` still carries shipped placeholders (`<Project Name>`, `<font-family>`) or no project-specific tokens; **steady-state** = real project tokens populated (name set, fonts chosen). On bootstrap, also apply Phase 4's **Greenfield Bootstrap Deltas** block.

## Phase 2.5: Diverge & Select Direction
*Runs after narrative sections, before the Stitch brief (Path A) or native freeze (Path B/C). This is a surface-openness gate.*

1. **Gate Evaluation:**
   - **Whole-page / new page / full redesign** (Path A branch A1; Path B new-page) → **Always diverge**: Propose 3 structurally distinct lo-fi layout directions.
   - **Feature-on-existing** (Path A branch A2; Path B feature) → **Default skip** (design space is small and shielded by Immortal Components). Only offer divergence if you detect ≥2 functionally distinct and viable layouts.
   - **Path C (non-UI/Backend)** → Generate 3 architecture/API alternatives (e.g. synchronous REST vs. RPC vs. asynchronous event-bus). Use the PRD §12 cost warning to inform the choice.
2. **Generate 3 Directions (Fidelity note: wireframe-level sketches, system fonts, layout/structure only, no pixel comps):**
   - **UI (Path A/B):** Resolve the core flow in the simplest layout optimized for the aha moment, using representative content. If greenfield (empty `DESIGN.md`), wireframes fix layout/structure only (no tokens); Stitch's visual language exploration is reserved for the winning layout (2-3 visual treatments of the chosen structure, not 3 layouts).
   - **Invoke `plan-html` skill:** Use the `wireframe-compare` template if available, or compose a custom 3-column CSS-grid board saving to `docs/design/BT-<padded>-directions.html`. Columns show layout regions as labeled boxes (header/nav/content/CTA) + 1-line rationale. Include a `trade-off-matrix` row scoring the 5 lenses.
3. **5-Lens Gut-Check & Select:** Evaluate each direction against the 5 lenses: desirable, usable, feasible, viable, and ethical.
4. **HITL Pick:** Show the user the comparison. The user selects a direction or cherry-picks elements. Combine into a single winner. Record the winning direction and rejected alternatives in the design doc under `## Direction Alternatives (Considered)`.


## Phase 3: Design Brief & Pause (PATH A ONLY)
*(Path B and Path C skip straight to Phase 4)*
1. Assemble a copy-pastable brief for the **winning direction only** (do not request 3 variants in one canvas). Specify: scope (A1 whole-page vs A2 feature-region ONLY); the regions/states/breakpoints to design (pull from the States section just written); and the governing §3 Immortal Components stated as HARD layout constraints — shielded for A2; for A1, note net-new layout will be registered as an Immortal Component on resume. Do NOT inline `DESIGN.md` token values into the brief. Follow `.agents/workflows/.reference/design-brief-guide.md` §A for brief quality.

2. Feed design context per design source:
   - **Stitch:** Instruct the user to set `.memory/DESIGN.md` as the project **Design System** in Stitch (UI → Modify → Design System) ([[DR-011]]). The Stitch MCP, if connected, is for PULLING the generated design/code back at Ingest (Phase 4) — it does not push context ([[DR-015]]).
   - **Claude Design:** Run `/design-sync` to sync the current design system (tokens + existing code) first; never let Claude Design cold-implement components (violates DR-004).
   - *Bootstrap exception:* if `DESIGN.md` is empty, skip this and let the generator propose the initial visual language.
3. Write the assembled brief into the design doc under a `## Design Brief (issued)` section, then output it and HALT with resume instructions.

## Phase 4: Harmonize & Freeze
*Steady-state flow. On bootstrap, also apply the **Greenfield Bootstrap Deltas** block below.*

### Path A (Generator-assisted):
1. Ingest the layout:
   - **Stitch:** Ingest the layout (Stitch MCP if connected, else copy/paste export).
   - **Claude Design:** Pull layout and code changes (never persist `/design-sync` live sync inside CI or mcpServers config; keep it frozen).
2. Token Snap — map generator hex/px to existing `DESIGN.md` tokens (DR-009). (Note: px values in DESIGN.md YAML are anchor targets; the Tailwind impl uses fluid clamps per DR-003 — not a conflict). OKLCH is preserved on Claude Design; snap is only a fallback for untokened values.
3. Immortal Components: A1 → propose the new shell as a §3 Immortal Component to the user; **on confirmation, register it in `.memory/DESIGN_RULES.md` §3 immediately** (do not defer structural decisions); A2 → discard any generator changes to global shell components (DR-008/DR-010).
4. Run `design-theme`:
   ```bash
   python .agents/scripts/design/design_theme.py --design .memory/DESIGN.md --out <app-css-dir>/theme.tokens.css
   ```
   Determine the app's CSS directory (e.g. Next.js `app/`, Vite `src/`, etc.) and ensure the project's main stylesheet `@import`s `./theme.tokens.css` below the `@import "tailwindcss";` directive (or at the bottom of the stylesheet).
5. Run the **UX / System Stress Test** (see below).
6. Freeze the resolved layout/hierarchy into the Path A body block. `status` → `ready-for-slicing`.
7. Read Rule: Generator output is read ONCE and frozen. Downstream readers of this doc (`3b`, `3d`, `4a`) read ONLY the frozen doc, `DESIGN.md`, and `DESIGN_RULES.md`; `4b` audits `.memory/`. Never access the live generator.

### Path B (Reference-driven native):
1. Conform to the frozen `DESIGN.md` + §3 Immortal Components. References are optional at steady-state — gather them only if the feature intentionally extends the system (the agent MAY fetch/inspect URLs to extract patterns).
2. Immortal Components: new page / full redesign → propose registering the new shell as a §3 Immortal Component to the user; on confirmation, register it in `.memory/DESIGN_RULES.md` §3 immediately (do not defer structural decisions); feature-on-existing → conform to / shield existing components.
3. Run the **UX / System Stress Test** (see below).
4. Write the blueprint into the Path B body block. `status` → `ready-for-slicing`.

### Path C (Non-UI interface contract):
1. Define the interface and seam boundaries, API signatures, schemas, adapter layers (if mapping domains), I/O params, behavioral invariants, and the input edge-case matrix; evaluate interface depth (deep vs. shallow complexity mapping) and write into the Path C body block.
2. Run the **UX / System Stress Test** (see below).
3. Set `status` → `ready-for-slicing`.

### UX / System Stress Test
Before freezing and setting `status` → `ready-for-slicing` in any path:
1. **Subagent — "Stress Tester":** Invoke a subagent (using Antigravity's `invoke_subagent` or Claude Code's `Task` tool with the `general-purpose` type).
   - **Input:** Provide the actors/flows/states and the resolved blueprint summary.
   - **Reads:** The design doc fresh from the filesystem.
   - **Guardrails:** *"Report the matrix only; do not edit any file."*
   - **Output Contract:** A path-aware matrix: `adverse condition → failure mode → required handling`.
     - *UI (Path A/B):* bad signal, low battery, distracted/"rough day".
     - *Path C (non-UI):* network partition, malformed payload, DB lock, retry storm.
2. **Extend the design doc:** Write this stress matrix directly into the existing `## States / Edge Classes` section (do not create a duplicate section).


### Greenfield Bootstrap Deltas
*Apply ONLY when Phase 2 classified this run as bootstrap (`.memory/DESIGN.md` empty/skeleton). The first UI feature establishes the design system — override the steady-state steps above:*
- **Path B input:** before anything else, prompt the user for design references (URLs/templates e.g. variant.com, screenshots, brand cues, explicit style descriptor) and PAUSE — *"Provide your design references, then say resume to continue."* The agent MAY fetch/inspect the URLs. *(Path A's empty-DESIGN.md input behavior is handled inline in Phase 3 step 2.)*
- **Token direction inverts (DR-009):** do NOT snap to existing tokens. Instead EXTRACT palette/type/spacing from the generator output (Path A), or derive an OKLCH palette (DR-002) + fluid scales (DR-003) + font pairing + layout primitives from the references (Path B, filtered through DR-001), and PROPOSE seeding `DESIGN.md` (propose-only; user confirms). For brownfield (existing code, empty DESIGN.md), derive the initial tokens from the codebase per `.agents/workflows/.reference/design-brief-guide.md` §B before proposing DESIGN.md. For Path B, record the reference URLs as provenance in `DESIGN_RULES.md` §2.
- **Immortal Components:** there are none to conform to yet — propose registering the initial shell as §3 Immortal Components to the user; **on confirmation, register it in `.memory/DESIGN_RULES.md` §3 immediately** (do not defer structural decisions).

## Phase 5: Publish & Sync
1. Append the design doc link to the parent GitHub Issue body.
2. Append relevant memory IDs (e.g. the new DR-xxx) to the `Ref` column in `.memory/BACKLOG_MAP.md` (do NOT put the design doc link in Ref).
3. Handoff: *"Interface design complete. If ≥ 2 unassigned `size:large` features (`status != done`) now sit in the backlog, or ≥ 2 features contend for the current release's scope, run `/3a_version-planning` to place this on the roadmap first; otherwise run `/3b_create-issue` to slice."*

---

## Archive Lifecycle
- Archive `docs/design/BT-<padded>-interface.md` to `docs/design/archive/BT-<padded>-interface.md` when the parent feature `BT-<padded>` closes.
