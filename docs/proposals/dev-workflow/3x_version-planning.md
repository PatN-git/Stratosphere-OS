---
name: 3x_version-planning
description: Proposal for roadmap version planning and release sequencing.
type: workflow HITL
trigger: User. Do not run autonomously.
---

# Workflow Proposal: 3x_version-planning


This workflow is currently parked and is not wired into the live execution path.

---

## 1. Purpose
The cross-feature **release and roadmap** layer. It operates at a higher altitude than `2a` (which is per-feature and too local) and `3b` (which is per-sprint and too tactical). It composes which parent features make up `v1` (MVP), `v2`, etc.

---

## 2. Altitude & Position
- **Target:** Operates on **parent features** (`size:large` BTs in `BACKLOG_MAP.md`), not individual vertical slices.
- **Positioning:** Runs after interface design (`2b`), before issue slicing (`3a`). It gates which features get sliced by `3a` so that next-release features are not sliced prematurely.
- **Re-runnable:** Can be re-run at any time as the backlog evolves.

---

## 3. Scale-Gate
Optional. Skip this workflow until the backlog holds more than one release's worth of features, or multiple concurrent features compete for the `v1.0` release scope.

---

## 4. Milestone Digit Ownership
- **Release Digit (x):** Owned exclusively by `3x_version-planning` (or defaults to `1` if `3x` is skipped).
- **Sprint Digit (yy):** Owned exclusively by `3b_sprint-planning`.
- **Milestone Format:** `x.yy` (e.g., `1.02` is Version 1, Sprint 2).
- **Default Rule:** Skipping `3x` implies `x = 1`. Slices default to `1.yy` milestones. No orphaned digits.

---

## 5. Output
Generates `docs/ROADMAP.md` mapping:
`Release -> Features (with MVP cut-line rationale)`
Writes/syncs the release digit onto features and their slices in GitHub and the `BACKLOG_MAP.md`.

---

## 6. Sequencing Rule
- Baseline-before-differentiator applies **across** features within a release.
- **Growth Loop Gate:** Features/stories enabling the primary growth loop must not be deferred past the release in which the core product goes live.

---

## 7. Naming & Integration Notes
- When this workflow is activated and built out:
  - Linearly-correct home is to rename it `3a_version-planning`.
  - Shift current `3a_create-issue` to `3b`.
  - Shift current `3b_sprint-planning` to `3c`.
  - Shift current `3c_implement-issue` to `3d`.
  - Execution order: version planning (roadmap) -> create issue (slice) -> sprint planning (sequence) -> implement.
- This rename is deferred to active build-time to avoid churning working workflow schemas and `dist/` trees during proposal state.
