---
name: 2b_interface-design
description: Design the interface (UI layout or non-UI contract) of a feature, post-PRD and pre-slicing.
type: workflow HITL
trigger: User. Do not run autonomously.
---

# Interface Design

**Hand-off contract:** Writes a path-aware design document to `docs/design/BT-<padded>-interface.md` by instantiating `.agents/workflows/.reference/design-doc-template.md`. Appends the design path to the parent GitHub issue body. Downstream workflows (`3a`, `3c` Phase 0, `4a`) read this document.

---

## Phase 1: Surface & Scope Gate
*Resume check: if `docs/design/BT-<padded>-interface.md` already exists with `status: draft`, do NOT restart. Read it, recover the path/branch from `surface` and the body block, and resume — Path B/C at Phase 4; Path A at Phase 4 if a `## Stitch Brief (issued)` section is present in the doc, else Phase 3.*

1. Load PRD from `docs/prds/BT-<padded>-<feature>.md`.
2. If there is NO external surface/code change (docs-only/process) → skip this workflow; handoff to `/3a_create-issue`.
3. If the feature has NO UI surface (backend/api/workers/db/library) → Path C.
4. If it has UI, read "Stitch Status" from `.memory/DESIGN_RULES.md` §2 and branch:
   - `yes` → Path A (Stitch-assisted). Branch A1 = Whole-page (new page / full redesign); Branch A2 = Feature-on-existing-page.
   - `no`  → Path B (Reference-driven native).
   - *unset / still the placeholder* `<yes | no — set during /stratosphere-setup>` → ask the user once (AskUserQuestion / ask_question), write the answer back to §2, then branch per above.

## Phase 2: Design Doc Initialization
1. Instantiate `docs/design/BT-<padded>-interface.md` from the template.
2. Populate the metadata shell (`slug`, `bt`, `prd`, `surface` = `ui-stitch-page|ui-stitch-feature|ui-manual|non-ui`, `status`: `draft`, `updated`). Ensure `surface` matches the chosen path (Path A → `ui-stitch-page|ui-stitch-feature`; Path B → `ui-manual`; Path C → `non-ui`).
3. Fill the narrative sections (Surface & Scope, Actors & Core Flows, States/Edge Classes) from the PRD now — before any pause. Keep exactly ONE body block.
4. Classify the run: **bootstrap** = `.memory/DESIGN.md` still carries shipped placeholders (`<Project Name>`, `<font-family>`) or no project-specific tokens; **steady-state** = real project tokens populated (name set, fonts chosen). On bootstrap, also apply Phase 4's **Greenfield Bootstrap Deltas** block.

## Phase 3: Stitch Brief & Pause (PATH A ONLY)
*(Path B and Path C skip straight to Phase 4)*
1. Assemble a copy-pastable Stitch brief: scope (A1 whole-page vs A2 feature-region ONLY); the regions/states/breakpoints to design (pull from the States section just written); and the governing §3 Immortal Components stated as HARD layout constraints — shielded for A2; for A1, note net-new layout will be registered as an Immortal Component on resume. Do NOT inline `DESIGN.md` token values into the brief. Follow `.agents/workflows/.reference/stitch-brief-guide.md` §A for brief quality.
2. Instruct the user to set `.memory/DESIGN.md` as the project **Design System** in Stitch (UI → Modify → Design System); Stitch treats it as hard constraints ([[DR-011]]). The Stitch MCP, if connected, is for PULLING the generated design/code back at ingest (Phase 4) — it does not push context ([[DR-015]]). *(Bootstrap exception: if DESIGN.md is empty, skip this; pass any brand intent from the PRD and let Stitch propose the initial visual language — optionally use Stitch's "extract design system from URL" on a reference site to seed it.)*
3. Write the assembled brief into the design doc under a `## Stitch Brief (issued)` section (so it survives a context reset), then output it and HALT with resume instructions, e.g.: *'Stitch brief ready (saved to the design doc). Design in Stitch, then return and say resume to ingest and freeze.'*

## Phase 4: Harmonize & Freeze
*Steady-state flow. On bootstrap, also apply the **Greenfield Bootstrap Deltas** block below.*

### Path A (Stitch):
1. Ingest the layout (Stitch MCP if connected, else copy/paste export).
2. Token Snap — map Stitch hex/px to existing `DESIGN.md` tokens (DR-009).
3. Immortal Components: A1 → propose the new shell as a §3 Immortal Component to the user; **on confirmation, register it in `.memory/DESIGN_RULES.md` §3 immediately** (the design moment is when structure is decided — do not defer to 0b); A2 → discard any Stitch changes to global shell components (DR-008/DR-010).
4. Freeze the resolved layout/hierarchy into the Path A body block. `status` → `ready-for-slicing`.
5. Read Rule: Stitch is read ONCE and frozen. Downstream readers of this doc (`3a`, `3c`, `4a`) read ONLY the frozen doc, `DESIGN.md`, and `DESIGN_RULES.md`; `4b` audits `.memory/`. Never access live Stitch.

### Path B (Reference-driven native):
1. Conform to the frozen `DESIGN.md` + §3 Immortal Components. References are optional at steady-state — gather them only if the feature intentionally extends the system (the agent MAY fetch/inspect URLs to extract patterns).
2. Immortal Components: new page / full redesign → propose registering the new shell as a §3 Immortal Component to the user; on confirmation, register it in `.memory/DESIGN_RULES.md` §3 immediately (do not defer to 0b); feature-on-existing → conform to / shield existing components.
3. Write the blueprint into the Path B body block. `status` → `ready-for-slicing`.

### Path C (Non-UI interface contract):
1. Define API signatures, schemas, I/O params, behavioral invariants, and the input edge-case matrix; write into the Path C body block. `status` → `ready-for-slicing`.

### Greenfield Bootstrap Deltas
*Apply ONLY when Phase 2 classified this run as bootstrap (`.memory/DESIGN.md` empty/skeleton). The first UI feature establishes the design system — override the steady-state steps above:*
- **Path B input:** before anything else, prompt the user for design references (URLs/templates e.g. variant.com, screenshots, brand cues, explicit style descriptor) and PAUSE — *"Provide your design references, then say resume to continue."* The agent MAY fetch/inspect the URLs. *(Path A's empty-DESIGN.md input behavior is handled inline in Phase 3 step 3.)*
- **Token direction inverts (DR-009):** do NOT snap to existing tokens. Instead EXTRACT palette/type/spacing from the Stitch output (Path A), or derive an OKLCH palette (DR-002) + fluid scales (DR-003) + font pairing + layout primitives from the references (Path B, filtered through DR-001), and PROPOSE seeding `DESIGN.md` (propose-only; user confirms). For brownfield (existing code, empty DESIGN.md), derive the initial tokens from the codebase per `.agents/workflows/.reference/stitch-brief-guide.md` §B before proposing DESIGN.md. For Path B, record the reference URLs as provenance in `DESIGN_RULES.md` §2.
- **Immortal Components:** there are none to conform to yet — propose registering the initial shell as §3 Immortal Components to the user; **on confirmation, register it in `.memory/DESIGN_RULES.md` §3 immediately** (the design moment is when structure is decided — do not defer to 0b).

## Phase 5: Publish & Sync
1. Append the design doc link to the parent GitHub Issue body.
2. Append the design doc ref to the `Ref` column in `.memory/BACKLOG_MAP.md`.
3. Handoff: *"Interface design complete. Run `/3a_create-issue` to slice requirements."*

---

## Archive Lifecycle
- Archive `docs/design/BT-<padded>-interface.md` to `docs/design/archive/BT-<padded>-interface.md` when the parent feature `BT-<padded>` closes.
