---
name: 3a_version-planning
description: Maps parent features to product releases and generates the roadmap; owns the MAJOR.MINOR digits of the vX.Y.Z milestone.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.1"
timestamp: 2026-06-25
---

# Version Planning

**Hand-off contract:** Reads parent features (`size:large` BTs) from `.memory/BACKLOG_MAP.md` and their PRDs in `docs/prds/`. Produces/updates `docs/ROADMAP.md`, creates a release milestone `vX.Y.0` in GitHub per release and assigns each parent feature to its release (also writing `vX.Y.0` into the BACKLOG_MAP `Milestone` column), and gates which features `/3b_create-issue` may slice next (only features in the current release). Owns the MAJOR (X) and MINOR (Y) digits of the `vX.Y.Z` milestone; the sprint digit Z is owned downstream by `/3c_sprint-planning`.

**Scale-gate (optional, countable):** This workflow is a *routing decision*, not a standing cost — when the gate says skip, none of the phases below load, so the gate is effectively free (it is evaluated from `BACKLOG_MAP`, which is already in context; no extra reads, no subagent). Run this workflow only when **either** of these countable conditions holds:
1. `count(parent features where size:large AND status != done AND not yet assigned to the current release) ≥ 2` — i.e. there is more than the current release can absorb, **or**
2. ≥ 2 parent features are explicitly contending for the *same* current-release scope and a cut-line decision is needed.

If neither holds, skip: releases default to `v1.0` and all features target `v1.0.0`, and slicing proceeds straight to `/3b_create-issue`.

**Milestone model (canonical — this is the project's product-release tracker; it is a different namespace from any tool/library/plugin version and must not be conflated with one):**
- `vX.Y.Z` GitHub milestone = the project's release/sprint tracker.
- **X (MAJOR):** a release whose aggregate scope breaks the existing product/architecture contract.
- **Y (MINOR):** a release of net-new, backward-compatible features.
- **Z (sprint):** owned by `/3c_sprint-planning`; `Z = 0` means "release planned, not yet sprinted".
- No leading zeros (`v1.0.8`, never `v1.0.08`); exactly three integer parts; no `-sprint` suffix.
- **Two-tier milestones:** this workflow creates the *release* milestone `vX.Y.0` and assigns parent features to it. `/3c_sprint-planning` creates *sprint* milestones `vX.Y.Z` (Z ≥ 1) for leaf slices.

## Phase 0: Precondition
1. Confirm `.memory/BACKLOG_MAP.md` is loaded — else stop and prompt `/0a_start-session`.
2. Confirm at least one `size:large` parent feature exists in BACKLOG_MAP. If none, stop: *"No parent features to roadmap yet — run `/2a_write-prd` first."*

## Phase 1: Read Current State (no writes)
1. **Determine two distinct baselines** (do not collapse them):
   - **Live product** = the highest `vX.Y` whose release milestone is **closed** in GitHub (or, if GitHub is absent, the highest release tagged `[SHIPPED]` in `docs/ROADMAP.md`). This is what users are running today.
   - **Numbering baseline** = the highest `vX.Y` **assigned** anywhere (open or closed). Scan in order of authority: existing `docs/ROADMAP.md` → GitHub milestones matching `^v\d+\.\d+\.\d+$` → the BACKLOG_MAP `Milestone` column (ignore the `Z` digit when ranking). The *next* release is proposed relative to this. If nothing is assigned, cold-start at `v1.0`.
2. **Collect roadmap candidates.** From BACKLOG_MAP, take every `size:large` parent feature whose `status != done`. For each, read its PRD `docs/prds/BT-<padded>-<name>.md` §3 (Goals), §6 (scope-classed stories), §12 (viability/cost), and its `Blocked by` dependencies. (BACKLOG_MAP is the authoritative feature list; PRDs supply rationale.)
3. **Working file (volume guard).** If **> 5** candidate features are in scope, accumulate the distilled findings into an ephemeral working file `docs/.roadmap.work.md` (hidden, gitignored via the existing `*.work.md` rule) — one block per feature: `BT-id, scope, size, Blocked-by, one-line cut-line note`. Delete any stale `docs/.roadmap.work.md` at the start of the run first. This mirrors the `1a`/`1b` deep-run pattern: it keeps main context lean and gives Phase 2.5's auditor a single source to read. For ≤ 5 features, skip the file and hold candidates inline.
4. Write nothing else in this phase (the `.work.md` is scratch, not an output artifact).

## Phase 2: Classify Releases (propose; HITL)
1. **Group features into releases.** Propose which parent features belong to the current release vs future releases. Apply the **sequencing rule**: baseline-before-differentiator *across* features; never defer a feature that enables the primary growth loop past the release in which the core product goes live.
2. **Assign MAJOR vs MINOR to each proposed release** using ONLY the compatibility test (scope class does NOT influence this):
   - **MAJOR** (`X+1`, `Y→0`) if any feature in the release: requires a destructive schema change / data migration to existing data; OR removes/renames an existing public contract (API route, CLI flag, exported interface, event); OR removes/alters an existing user-facing capability.
   - Otherwise **MINOR** (`Y+1`).
   - Cold start with no prior release → `v1.0`.
3. **Assemble the proposed roadmap** (do not present yet): per release, `vX.Y`, the parent features, the MAJOR/MINOR justification, and the MVP cut-line rationale.

## Phase 2.5: Release Auditor (subagent — quality gate before HITL)
1. **Invoke a Release Auditor subagent** (using Antigravity's `invoke_subagent` or Claude Code's `Task` tool with the `general-purpose` type).
   - **Input:** pass the assembled proposal (release→feature mapping + MAJOR/MINOR justifications) *inline*.
   - **Reads:** instruct it to read `docs/.roadmap.work.md` if present (else the candidate features' BACKLOG_MAP rows + PRDs) fresh from the file system.
   - **Guardrails:** *"Report the audit findings only; do not edit any file, create milestones, or modify the roadmap."*
   - **Output Contract:** a findings list, each tagged `[BLOCKER]` or `[WARN]`, covering exactly these checks:
     - **Cross-release dependency:** any feature in an earlier/current release whose `Blocked by` points to a feature placed in a *later* release → `[BLOCKER]`.
     - **MAJOR/MINOR misclassification:** any release tagged MAJOR with no compatibility-breaking feature, or MINOR despite a breaking feature; **especially** flag any case where the X/Y choice appears driven by scope class rather than the §-compatibility test → `[BLOCKER]` if it changes the number, else `[WARN]`.
     - **Sequencing-rule violation:** a differentiator sequenced ahead of an unmet baseline across features, or a growth-loop-enabling feature deferred past the core go-live release → `[WARN]`.
     - **MVP cut-line coherence:** is the current release independently shippable (no dangling dependency on a deferred feature)? → `[BLOCKER]` if not.
2. **Resolve before halting:** the main agent folds the findings into the proposal — every `[BLOCKER]` must be resolved (re-place a feature, re-classify, or explicitly justify and downgrade) before presentation.
3. **Present the audited roadmap to the user and HALT.** Show, per release: `vX.Y`, parent features, MAJOR/MINOR justification, MVP cut-line rationale, **and** the auditor's findings + how each was resolved. Never auto-commit an X/Y bump — the user confirms or adjusts before Phase 4.

## Phase 3: Idempotent Re-run Guard
- On re-run, do NOT renumber releases that already have features assigned and any sprint activity (a `vX.Y.Z` with Z ≥ 1 exists in GitHub). Only: place *unassigned* features, or apply explicit user-directed moves. Surface any conflict (a feature already sliced/sprinted under a different release) and ask before changing it.

## Phase 4: Commit & Sync (only on user confirmation)
1. **Write `docs/ROADMAP.md`** by instantiating `.agents/workflows/.reference/ROADMAP-template.md`. **Merge, do not clobber:** preserve human-authored prose; update only the release→feature mapping and rationale blocks. Prepend OKF frontmatter per `.agents/rules/okf-protocol.md` using `type: roadmap`. Then reconcile status (from the Phase 1 baselines): tag each release `[PLANNED] / [ACTIVE] / [SHIPPED <date>]`, update the **Live product** marker to the highest shipped (or active) release, and **collapse any newly-shipped release into the `## Shipped` section** as a single terse line (drop its full feature detail — the GitHub milestone retains specifics). Never delete a shipped entry.
2. **GitHub gate:** if GitHub is not connected, skip steps 3–4 and note: *"GitHub not connected — roadmap recorded in `docs/ROADMAP.md` and BACKLOG_MAP only."*
3. **Create release milestones & assign parents.** For each release lacking one, create the GitHub milestone `vX.Y.0`. Assign each `size:large` parent feature issue to its release `vX.Y.0`, and write the same `vX.Y.0` into the `Milestone` column of its BACKLOG_MAP row. **Do not touch leaf slices** — they may not exist yet; `/3b_create-issue` creates them inheriting the parent's `vX.Y.0`, and `/3c_sprint-planning` moves them to `vX.Y.Z`.
4. **Comment** on each (re)assigned parent feature issue documenting the release placement and rationale (mirrors the 0b / 3c issue-comment pattern so GitHub history explains every milestone change).
5. **Render a read-only visual.** Invoke the `plan-html` skill to render `docs/ROADMAP.html` — a swimlane (releases as columns, parent features as cards with `scope`/`size`/status badges, dependency arrows) using the `board` or `plan-document` template. It is generated **strictly from `docs/ROADMAP.md`** every run and is **read-only / presentation-only**: `docs/ROADMAP.md` remains the single source of truth, the HTML is never read back, and it carries no editing affordance.
6. **Cleanup:** delete `docs/.roadmap.work.md` if it was created in Phase 1 (read-once-then-delete, per the `1a`/`1b` convention; `0d` also purges stray scratchpads as a backstop).
7. **Hand-off:** *"Roadmap updated. Features in the current release `vX.Y` are ready to slice — run `/3b_create-issue`. Future-release features are gated until their release is current."*

## Re-run Notes
- Re-runnable anytime as the backlog evolves; see the Phase 3 idempotency guard.
- Skipping this workflow entirely implies `v1.0` for all features (`/3b_create-issue` and `/3c_sprint-planning` default X.Y to `1.0`).
