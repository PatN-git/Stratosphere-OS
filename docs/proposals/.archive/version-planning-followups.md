---
title: Version-Planning Follow-Ups
description: Tracking out-of-scope issues surfaced during version-planning design.
version: "1.0.0"
timestamp: 2026-06-18
---

# Version-Planning Follow-Ups

Tracker for issues surfaced **during** the version-planning workflow design (see [`docs/proposals/dev-workflow/version-planning-implementation-plan.md`](../proposals/dev-workflow/version-planning-implementation-plan.md)) that are deliberately **out of scope** for that plan. Kept here so they are not lost. None of these block the version-planning build.

Each item: **Context → Problem → Proposed fix → Acceptance → Effort.** Update the Status line as they move.

---

## 1. `docs/PRD_MODEL.md` is stale relative to the unified milestone model
**Status:** done · deleted (obsolete conventions superseded by BACKLOG_MAP + 2a + 3b).

**Context.** `docs/PRD_MODEL.md` was authored before the `vX.Y.Z` milestone unification and the `3x→3a/3b/3c/3d` workflow rename.

**Problem.**
- References a `v1` milestone notion and `phase:xxx` labels that do not match the unified `vX.Y.Z` model or the BACKLOG_MAP Label Registry.
- References skills/workflows that do not exist (`write-prd`, `write-issue`, `extract-slices`) — the real workflows are `2a_write-prd`, `3b_create-issue` (post-rename), etc.
- It contains **no** renamed-workflow or `x.yy` strings, so it does **not** affect the version-planning plan's consistency gate — but it is misleading as living documentation.

**Proposed fix.** Decide the doc's role first:
- If it is meant to be authoritative guidance → rewrite it against the unified milestone model and the real workflow names, and move it out of `docs/templates`/untracked into its proper home.
- If it was a scratch/exploration note → delete it.

**Acceptance.** Either the file is removed, or `git grep -nE 'phase:|write-issue|extract-slices'` over it returns nothing and its milestone/label vocabulary matches `src/memory-templates/BACKLOG_MAP.md`.

**Effort.** Small (docs-only).

---

## 2. `src/scripts/scaffold.py` `--repair-lock` path has a `_versioning` call-signature mismatch
**Status:** done · resolved (signatures corrected and console warning added on skipped files).

**Context.** `src/scripts/_versioning.py` defines:
- `read_version(text, path)` → returns a **2-tuple** `(version, updated)`.
- `body_hash(text)` → takes **one** argument.

**Problem.** The repair branch in `scaffold.py` calls them with the wrong arity:
- `scaffold.py:186` → `v, u, form = _versioning.read_version(text, p)` unpacks **three** values from a 2-tuple → `ValueError: not enough values to unpack`.
- `scaffold.py:190` → `_versioning.body_hash(text, form)` passes **two** args to a 1-arg function → `TypeError`.

So `scaffold.py --repair-lock` (the `repair=True` path) crashes. Normal-mode scaffolding is unaffected, and the workflow-resolution glob (`^[0-4].*\.md$`) is rename-agnostic and verified fine — this is isolated to lock repair.

**Proposed fix.** Reconcile the contract. Either:
- (a) make `_versioning.read_version` / `body_hash` return/accept the third "form" value the caller expects (if a frontmatter-form concept is intended), **or**
- (b) update `scaffold.py:186,190` to the existing 2-tuple / 1-arg signatures (`v, u = read_version(text, p)`; `body_hash(text)`).
Pick whichever matches the intended design; (b) is the smaller change if no "form" concept is actually needed.

**Acceptance.** `python src/scripts/scaffold.py --repair-lock <project>` runs without raising; add/adjust a case in `tests/verify_scripts.py` to cover the repair path.

**Effort.** Small, but **own branch** — unrelated to version planning.

---

## 3. `0d_nightly-consolidation` staleness nudge for version planning
**Status:** done · resolved (Phase 3.6 version-planning detector added to 0d consolidator).

**Context.** `3a_version-planning` is intentionally **HITL** (`trigger: User. Do not run autonomously.`) — release scope, MVP cut-line, and MAJOR/MINOR are product decisions that need human sign-off. But pure-manual triggering risks a stale roadmap.

**Problem.** Nothing reminds the user to roadmap newly-added parent features.

**Proposed fix.** Add a **detector, not a runner** to `0d_nightly-consolidation` (chosen over `0b` because `0b` fires every session-stop and would be noisy). It counts parent features (`size:large`, `status != done`) that are unassigned to any release / absent from `docs/ROADMAP.md`; if non-zero, it emits a one-line nudge: *"N features unroadmapped — consider `/3a_version-planning`."* It makes **no** decisions and creates **no** milestones — purely a count + message, so it stays token-cheap.

**Acceptance.** `0d` surfaces the nudge when unroadmapped `size:large` features exist and stays silent otherwise; it never invokes `3a` autonomously. Bump `0d_nightly-consolidation.md`'s artifact version and rebuild/validate per the normal build flow.

**Effort.** Small (single additive section in one workflow).

---

## 4. Interactive `docs/ROADMAP.html` drag-and-drop editor (v2)
**Status:** open · the **read-only** render ships in the version-planning plan (Phase 4 step 5); this item is the **bidirectional editor** half.

**Context.** The read-only swimlane (generated from `docs/ROADMAP.md` via `plan-html`) gives a visual but no editing. The goal is to let the user **drag parent-feature cards between release columns** and have the agent apply the result.

**Problem (the hard part is read-back).** A static HTML file's drag state lives in the browser DOM, not on disk. `localStorage` is unreadable by the agent; a `sendPrompt()` "Apply" button works only in the Claude Code chat UI (not Antigravity). The portable mechanism is **copy-paste**, exactly as `2b_interface-design`'s Stitch path ingests when the MCP is absent.

**Proposed design (HTML is an ephemeral *editor*, never a store):**
1. `3a` generates the editor HTML **from** `docs/ROADMAP.md`.
2. User drags cards across release columns; a live textarea mirrors the result as a canonical, parseable block — one line per move, e.g. `BT-007 -> v1.1`.
3. User pastes the block back to the agent.
4. Agent parses it, runs the **Phase 2.5 Release Auditor** on the new mapping (manual drags are precisely where cross-release dependency bugs appear), and on a clean audit writes `docs/ROADMAP.md` + BACKLOG_MAP `Milestone` column + GitHub release milestones, then regenerates the HTML.
5. `docs/ROADMAP.md` stays the single source of truth throughout; the HTML is regenerated, never authoritative — this structurally prevents dual-source drift.

**Acceptance.** A round-trip (drag → paste → apply) updates ROADMAP.md/BACKLOG_MAP/GitHub consistently; an audit `[BLOCKER]` (e.g. a dependency-violating drag) halts the write and reports back; ROADMAP.md and the HTML never diverge as sources of truth. Works via copy-paste in both Claude Code and Antigravity (no reliance on `sendPrompt()`/browser MCP).

**Effort.** Medium — own slice. Reuses the `plan-html` micro-app patterns and the existing Release Auditor.
