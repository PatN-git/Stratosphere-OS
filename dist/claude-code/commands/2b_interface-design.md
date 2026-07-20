---
name: 2b_interface-design
description: Design the interface (UI layout or non-UI contract) of a feature, post-PRD and pre-slicing.
type: workflow HITL
trigger: manual
version: "1.2.0"
timestamp: 2026-07-17
---

# Interface Design

**Hand-off contract:** Writes path-aware design document to `docs/design/BT-<padded>-interface.md` by instantiating `.agents/workflows/.reference/design-doc-template.md`. Appends design path to parent GitHub issue body. Downstream workflows (`3b`, `3d` Phase 0, `4a`) read this document.

---

## Phase 0: Load Memory
Run `.agents/skills/load-memory/SKILL.md` to restore session context (read-only).

## Phase 1: Surface & Scope Gate
*Resume check: if docs/design/BT-<padded>-interface.md exists with status: draft, recover path/branch (from surface/body) and resume: Path B/C at Phase 4 (or 2.5); Path A at Phase 4 if "## Design Brief" exists, else Phase 3 (or 2.5).*

1. Load PRD from `docs/prds/BT-<padded>-<feature>.md`.
2. If no external surface/code change → skip (no design doc produced); **promote parent epic `needs_spec → planned`** (`gh issue edit <n> --remove-label "status:needs_spec" --add-label "status:planned"`; update BACKLOG Status) since the spec is complete with no design step; then handoff to `/3b_create-issue`.
3. If feature has no UI surface → Path C.
4. If UI surface, read "Design Source" from `.memory/DESIGN_RULES.md` §2 and branch:
   - `stitch` or `claude-design` → Path A (generator-assisted). A1 = Whole-page; A2 = Feature-on-existing. (If generator tools absent: A1 stays Path A; A2 prompts user, or defaults to Path B if AFK).
   - `native`  → Path B (Reference-driven native).
   - Unset → ask user, write choice back to §2, branch.

## Phase 2: Design Doc Initialization
1. Create `docs/design/BT-<padded>-interface.md` from template. Prepend OKF `type: interface-design`.
2. Populate metadata (slug, bt, prd, surface, status: draft, updated). Map: Path A -> ui-generator-page|ui-generator-feature; Path B -> ui-manual; Path C -> non-ui.
3. **Define Aha Moment & Time-to-Value:** identify aha moment (value in <30s). Design flow backward from it: no intro sliders, drop user straight into core flow. (Path C: aha = "time to first successful API call").
4. Fill narrative sections from PRD. Keep one body block.
5. Classify: bootstrap (empty/placeholder `.memory/DESIGN.md`) vs steady-state. If bootstrap, apply Phase 4 Greenfield Bootstrap Deltas.

## Phase 2.5: Diverge & Select Direction
*Runs before Stitch brief (Path A) or native freeze (Path B/C).*

1. **Gate Evaluation:**
   - **Whole-page** (Path A A1; Path B new-page) → Propose 3 distinct lo-fi layouts.
   - **Feature-on-existing** (Path A A2; Path B feature) → Skip unless ≥2 distinct layouts found.
   - **Path C (non-UI)** → Generate 3 architecture/API alternatives. Use PRD §12 cost warning.
2. Generate 3 Directions (wireframes, layout/structure only; for Path A/B, no tokens/visual style exploration):
   - Invoke plan-html: use wireframe-compare template or 3-column CSS grid (labeled regions + 1-line rationale, trade-off matrix row) to render docs/design/BT-<padded>-directions.html.
3. **5-Lens Check:** Evaluate against desirable, usable, feasible, viable, ethical.
4. **HITL Pick:** Show comparison. Record winner and rejected in docs under "## Direction Alternatives (Considered)".

## Phase 3: Design Brief & Pause (PATH A ONLY)
*(Path B and Path C skip directly to Phase 4: Harmonize & Freeze)*
1. Assemble brief for winning direction only. Specify: scope, regions/states/breakpoints, and §3 Immortal Components as hard constraints. Do not inline tokens. Follow `.agents/workflows/.reference/design-brief-guide.md` §A.
2. Feed design context:
   - Stitch: set .memory/DESIGN.md as Stitch Design System [[DR-011]]; Stitch MCP only pulls layout [[DR-015]].
   - Claude Design: run /design-sync first; never let Claude cold-implement (violates DR-004).
   - Bootstrap: if DESIGN.md empty, let generator propose initial visual language.
3. Write brief into design doc under `## Design Brief (issued)` and halt.

## Phase 4: Harmonize & Freeze
*Steady-state flow. If bootstrap, apply Greenfield Bootstrap Deltas.*

### Path A (Generator-assisted):
1. Ingest layout:
   - **Stitch:** Ingest layout via Stitch MCP (`get_screen`). If `mcp:stitch/*` tools are not registered in active tool declarations, read `mcp_config.json` or `.env.local` for the Stitch Api Key and query the JSON-RPC endpoint directly via PowerShell.
   - **Claude Design:** Pull layout and code changes (never persist `/design-sync` live sync).
2. Token Snap — map generator hex/px to existing `DESIGN.md` tokens (DR-009). OKLCH is preserved on Claude Design; snap is only a fallback for untokened values.
3. Immortal Components: A1 → propose new shell as §3 Immortal Component; on confirmation, register in `.memory/DESIGN_RULES.md` §3 immediately. A2 → discard any generator changes to global shell components (DR-008/DR-010).
4. Run design-theme: python .agents/scripts/design/design_theme.py --design .memory/DESIGN.md --out <app-css-dir>/theme.tokens.css. Import theme.tokens.css below @import "tailwindcss" (or bottom of stylesheet).
5. Run UX / System Stress Test.
6. Freeze layout into Path A body block. design doc `status → approved` (editorial).
7. Generator output is read once/frozen. Downstream workflows (3b, 3d, 4a) read only frozen doc/DESIGN.md; 4b audits .memory/. Never access live generator.

### Path B (Reference-driven native):
1. Conform to frozen `DESIGN.md` + §3 Immortal Components.
2. Immortal Components: new page → propose registering new shell as §3 Immortal Component; on confirmation, register in `.memory/DESIGN_RULES.md` §3 immediately. feature → conform to / shield existing components.
3. Run UX / System Stress Test.
4. Write blueprint into Path B body block. design doc `status → approved` (editorial).

### Path C (Non-UI interface contract):
1. Define the interface and seam boundaries, API signatures, schemas, adapter layers (if mapping domains), I/O params, behavioral invariants, and the input edge-case matrix; evaluate interface depth (deep vs. shallow) and write into the Path C body block.
2. Run UX / System Stress Test.
3. Set design doc `status → approved` (editorial).

### UX / System Stress Test
1. Subagent - "Stress Tester": Invoke a subagent. Input: actors/flows/states, resolved blueprint. Reads: design doc fresh from the filesystem. Guardrail: "Report the matrix only; do not edit any file." Output: adverse condition -> failure mode -> handling (UI: bad signal/low battery/distracted; Path C: network partition/malformed payload/DB lock/retry storm).
2. **Extend design doc:** Write stress matrix into existing `## States / Edge Classes`.

### Greenfield Bootstrap Deltas
*Apply only when Phase 2 classified run as bootstrap:*
- Path B input: prompt user for design references (URLs, screenshots, brand cues) and pause (resume to continue).
- Token direction inverts (DR-009): extract tokens (Path A) or derive (Path B: OKLCH/fluid scales/fonts/layout) and propose seeding DESIGN.md. If brownfield, derive from codebase first.
- Immortal Components: propose registering shell; on confirmation, register in .memory/DESIGN_RULES.md §3 immediately.

## Phase 5: Publish & Sync
1. **Epic status transition (single writer for this edge):** the design freeze promotes the parent epic `needs_spec → planned`: `gh issue edit <n> --remove-label "status:needs_spec" --add-label "status:planned"`; set BACKLOG Status = `planned`. (2b never touches the PRD's editorial status — 2a owns that.)
2. **Commit & Push Doc:** `git add docs/design/BT-<padded>-interface.md && git commit -m "docs(BT-<padded>): interface design"`, then push to the **default** branch if `gh`/remote is connected (else local commit only). Never sweep unrelated drift into this commit.
3. Append design doc link to parent GitHub Issue body.
4. Append memory IDs to Ref column in `BACKLOG_MAP.md` (never put design doc path in Ref column).
5. Handoff: "Interface design complete. If ≥ 2 unassigned `tier:epic` features (`status != done`) now sit in the backlog, or ≥ 2 features contend for the current release's scope, run `/3a_version-planning` to place this on the roadmap first; otherwise run `/3b_create-issue` to slice."

---

## Archive Lifecycle
- Archive docs/design/BT-<padded>-interface.md to docs/design/archive/ when parent feature closes.
