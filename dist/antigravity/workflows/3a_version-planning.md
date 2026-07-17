---
name: 3a_version-planning
description: Maps parent features to releases and roadmaps; owns MAJOR.MINOR of vX.Y.Z milestone.
type: workflow HITL
trigger: manual
version: "1.0.5"
timestamp: 2026-07-17
---

# Version Planning

**Hand-off contract:** Reads parent features from `.memory/BACKLOG_MAP.md` and `docs/prds/`. Updates `docs/ROADMAP.md`, creates milestone `vX.Y.0` in GitHub, assigns parent features, and updates BACKLOG_MAP Milestone column. Slicing in `/3b_create-issue` is gated to current release features only. Owns MAJOR (X) and MINOR (Y) digits; sprint digit (Z) is owned by `/3c_sprint-planning`.

**Scale-gate:** Run only when:
1. `count(parent features where tier:epic AND status != done AND not yet assigned to current release) ≥ 2`, OR
2. ≥ 2 parent features contend for same current-release scope.

Else skip: default to `v1.0.0` and proceed directly to `/3b_create-issue`.

**Milestone model** (canonical — the project's product-release tracker; a different namespace from any tool/library/plugin version and must not be conflated with one):
- `vX.Y.Z` milestone = release/sprint tracker.
- **X (MAJOR):** breaks the existing product/architecture contract.
- **Y (MINOR):** net-new, backward-compatible features.
- **Z (sprint):** owned by `/3c_sprint-planning` (Z = 0 is planned).
- No leading zeros, exactly three parts.
- Version planning creates `vX.Y.0` for parents; sprint planning creates `vX.Y.Z` (Z ≥ 1) for slices.

## Phase 0: Precondition
1. Confirm `.memory/BACKLOG_MAP.md` is loaded.
2. Confirm ≥ 1 `tier:epic` parent feature exists in BACKLOG_MAP. Else halt: *"No parent features to roadmap — run `/2a_write-prd` first."*

## Phase 1: Read Current State (no writes)
1. **Baselines** (do not collapse the two):
   - **Live product:** highest `vX.Y` closed in GitHub (or tagged `[SHIPPED]` in `docs/ROADMAP.md`).
   - **Numbering baseline:** highest assigned `vX.Y` (scan authority: ROADMAP.md -> GitHub matching ^v\d+\.\d+\.\d+$ -> BACKLOG_MAP Milestone column, ignoring Z). Default `v1.0`.
2. **Roadmap candidates:** parent features with status not `done`. Read their PRD §3, §6, §12, and `Blocked by`.
3. **Working file:** If > 5 candidates, write `BT-id, scope, size, Blocked-by, cut-line note` to docs/.roadmap.work.md (delete stale first). Else hold inline.
4. Write nothing else in this phase (the `.work.md` is scratch, not an output artifact).

## Phase 2: Classify Releases
1. **Group features:** propose feature-to-release mapping. Sequencing: baseline before differentiator across features; never defer a feature that enables the primary growth loop past the release in which the core product goes live.
2. **MAJOR vs MINOR** (compatibility test only; scope class does NOT influence this):
   - **MAJOR** (`X+1`, `Y->0`) if any feature requires a destructive schema change/migration to existing data; removes/renames an existing public contract (API route, CLI flag, exported interface, event); or removes/alters an existing user-facing capability.
   - **MINOR** (`Y+1`) otherwise.
   - Cold start → `v1.0`.
3. **Assemble proposal:** releases, parent features, justification, and MVP cut-line rationale.

## Phase 2.5: Release Auditor (subagent — quality gate before HITL)
1. **Auditor:** Invoke a Release Auditor subagent (via Antigravity `invoke_subagent` or Claude Code `Task` general-purpose). Input: the assembled proposal (release→feature mapping + MAJOR/MINOR justifications) inline. Reads: `docs/.roadmap.work.md` if present (else the candidate features' BACKLOG_MAP rows + PRDs) fresh from the file system. Guardrail: *"Report the audit findings only; do not edit any file, create milestones, or modify the roadmap."* Output: a findings list, each tagged `[BLOCKER]` or `[WARN]`, covering exactly these checks:
   - **Cross-release dependency:** any feature whose `Blocked by` points to a feature placed in a *later* release → `[BLOCKER]`.
   - **MAJOR/MINOR misclassification:** any release tagged MAJOR with no compatibility-breaking feature, or MINOR despite a breaking feature; **especially** flag any case where the X/Y choice appears driven by scope class rather than the §-compatibility test → `[BLOCKER]` if it changes the number, else `[WARN]`.
   - **Sequencing-rule violation:** a differentiator sequenced ahead of an unmet baseline across features, or a growth-loop-enabling feature deferred past the core go-live release → `[WARN]`.
   - **MVP cut-line coherence:** is the current release independently shippable (no dangling dependency on a deferred feature)? → `[BLOCKER]` if not.
2. **Resolve:** the main agent folds findings into the proposal — every `[BLOCKER]` must be resolved (re-place, re-classify, or explicitly justify and downgrade) before presentation.
3. **Present and Halt:** show, per release, `vX.Y`, parent features, MAJOR/MINOR justification, MVP cut-line rationale, and the auditor's findings + how each was resolved. Await user confirmation; never auto-commit an X/Y bump.

## Phase 3: Idempotent Re-run Guard
- Do not renumber active releases (Z ≥ 1 in GitHub). Only place unassigned features or apply user moves; ask if conflict arises.

## Phase 4: Commit & Sync
1. **Write `docs/ROADMAP.md`:** instantiate `.agents/workflows/.reference/ROADMAP-template.md`. Prepend OKF `type: roadmap`. Merge and preserve prose. Update release tags (`[PLANNED] / [ACTIVE] / [SHIPPED <date>]`), update Live product marker, and collapse newly-shipped releases to a single line in Shipped section (never delete shipped).
2. **GitHub:** if disconnected, skip. Create milestones vX.Y.0 in GitHub, assign parent issues, and update BACKLOG_MAP Milestone column (do not touch leaf slices).
3. **Comment:** post release placement and rationale on each assigned parent feature issue.
4. **Render:** invoke `plan-html` using `board` or `plan-document` to render read-only `docs/ROADMAP.html`.
5. **Cleanup:** delete `docs/.roadmap.work.md`.
6. **Hand-off:** *"Roadmap updated. Current release features ready to slice (run `/3b_create-issue`)."*

## Re-run Notes
- Skipping version planning defaults features to `v1.0` (with Z managed by 3c).
