---
name: 3a-version-planning
description: "Maps parent features to releases and roadmaps; owns MAJOR.MINOR of vX.Y.Z milestone. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.3.0"
timestamp: 2026-10-14
---

# Version Planning

**Hand-off contract:** Writes `docs/ROADMAP.md` (plus the `vX.Y.0` milestones, Phase 4). Read by: `/2b-interface-design`, `/3b-create-issue`.

**Scale-gate:** Run only when:
1. `count(parent features where tier:epic AND status != done AND not yet assigned to current release) ≥ 2`, OR
2. ≥ 2 parent features contend for same current-release scope, OR
3. a release is closable: it has ≥ 1 parent epic, all `done`, and every open `vX.Y.*` milestone reports `open_issues == 0` (nothing else closes milestones).

Condition 3 alone → close-out only: skip Phase 2 and the auditor; the Phase 2.5 step 3 halt presents the close-out; Phase 4 runs only steps 1, 2, 7, 8 and 9, then hands off: *"Release vX.Y closed."*

Else skip: default to `v1.0.0` and proceed directly to `/3b-create-issue`.

**Milestone model** (canonical — the project's product-release tracker; a different namespace from any tool/library/plugin version and must not be conflated with one):
- `vX.Y.Z` milestone = release/sprint tracker.
- **X (MAJOR):** breaks the existing product/architecture contract.
- **Y (MINOR):** net-new, backward-compatible features.
- **Z (sprint):** owned by `/3c-sprint-planning` (Z = 0 is planned).
- No leading zeros, exactly three parts.
- Version planning creates `vX.Y.0` for parents; sprint planning creates `vX.Y.Z` (Z ≥ 1) for slices.

## Phase 0: Precondition
1. **Hydrate:** Run the `load-memory` skill to restore session context (read-only), then confirm `.memory/BACKLOG_MAP.md` is loaded.
2. Confirm ≥ 1 `tier:epic` parent feature exists in BACKLOG_MAP. Else halt: *"No parent features to roadmap — run `/2a-write-prd` first."*

## Phase 1: Read Current State (no writes)
1. **Baselines** (do not collapse the two):
   - **Live product:** highest `vX.Y` closed in GitHub (or tagged `[SHIPPED]` in `docs/ROADMAP.md`).
   - **Numbering baseline:** highest assigned `vX.Y` (scan authority: ROADMAP.md -> GitHub matching ^v\d+\.\d+\.\d+$ -> BACKLOG_MAP Milestone column, ignoring Z). Default `v1.0`.
2. **Roadmap candidates:** parent features with status not `done`. Read their PRD §3, §6, §12 (Complexity Estimate), and `Blocked by`.
3. **Closable releases:** each release not yet `[SHIPPED]` with ≥ 1 parent epic, all `done`: list its open `vX.Y.*` milestones (`gh api repos/{owner}/{repo}/milestones --paginate`; match `title`, read `number` and `open_issues`). Any `open_issues > 0` → the release is not closable; surface it instead. None open → nothing to close. GitHub disconnected → skip.
4. **Working file:** If > 5 candidates, write `BT-id, scope, complexity (§12), Blocked-by, cut-line note` to `.tmp/3a-roadmap.work.md` (delete stale first). Else hold inline.
5. Write nothing else in this phase (the `.work.md` is scratch, not an output artifact).

## Phase 2: Classify Releases
1. **Group features:** propose feature-to-release mapping. Sequencing: baseline before differentiator across features; never defer a feature that enables the primary growth loop past the release in which the core product goes live.
   - **Late-discovered dependency:** a genuine prerequisite between epics not yet in the dependent's `Blocked by` → flag `[NEW-DEP] BT-<padded> ← BT-<prereq>`. Do **not** write it yet — it is proposed at the Phase 2.5 halt.
2. **MAJOR vs MINOR** (compatibility test only; scope class does NOT influence this):
   - **MAJOR** (`X+1`, `Y->0`) if any feature requires a destructive schema change/migration to existing data; removes/renames an existing public contract (API route, CLI flag, exported interface, event); or removes/alters an existing user-facing capability.
   - **MINOR** (`Y+1`) otherwise.
   - Cold start → `v1.0`.
3. **Assemble proposal:** releases, parent features, justification, and MVP cut-line rationale.

## Phase 2.5: Release Auditor (subagent — quality gate before HITL)
1. **Auditor:** Invoke a Release Auditor subagent (using the host's subagent mechanism). Input: the assembled proposal (release→feature mapping + MAJOR/MINOR justifications) inline. Reads: `.tmp/3a-roadmap.work.md` if present (else the candidate features' BACKLOG_MAP rows + PRDs) fresh from the file system. Guardrail: *"Report the audit findings only; do not edit any file, create milestones, or modify the roadmap."* Output: a findings list, each tagged `[BLOCKER]` or `[WARN]`, covering exactly these checks:
   - **Cross-release dependency:** any feature whose `Blocked by` (recorded or `[NEW-DEP]`) points to a feature placed in a *later* release → `[BLOCKER]`.
   - **MAJOR/MINOR misclassification:** any release tagged MAJOR with no compatibility-breaking feature, or MINOR despite a breaking feature; **especially** flag any case where the X/Y choice appears driven by scope class rather than the §-compatibility test → `[BLOCKER]` if it changes the number, else `[WARN]`.
   - **Sequencing-rule violation:** a differentiator sequenced ahead of an unmet baseline across features, or a growth-loop-enabling feature deferred past the core go-live release → `[WARN]`.
   - **MVP cut-line coherence:** is the current release independently shippable (no dangling dependency on a deferred feature)? → `[BLOCKER]` if not.
2. **Resolve:** the main agent folds findings into the proposal — every `[BLOCKER]` must be resolved (re-place, re-classify, or explicitly justify and downgrade) before presentation.
3. **Present and Halt:** show, per release, `vX.Y`, parent features, MAJOR/MINOR justification, MVP cut-line rationale, the auditor's findings + how each was resolved, each proposed `[NEW-DEP]` edge, and each release proposed for close (its open milestones). Await user confirmation per item; never auto-commit an X/Y bump or a milestone close.

## Phase 3: Idempotent Re-run Guard
- Do not renumber active releases (Z ≥ 1 in GitHub). Only place unassigned features or apply user moves; ask if conflict arises.

## Phase 4: Commit & Sync
1. **Release close (outward write; only for releases the user confirmed at the Phase 2.5 halt, never auto-run):** close each of its open `vX.Y.*` milestones: `gh api -X PATCH repos/{owner}/{repo}/milestones/<n> -f state=closed`. All-or-nothing per release: if any of its milestones reports `open_issues > 0`, close none of them and surface those milestones. GitHub disconnected → skip; the release stays unshipped.
2. **Write `docs/ROADMAP.md`:** instantiate `references/ROADMAP-template.md` — write its **Artifact frontmatter** block verbatim (already carries `type: roadmap`), then the **Artifact body**. Merge and preserve prose. Update release tags (`[PLANNED] / [ACTIVE] / [SHIPPED <date>]`; `[SHIPPED <date>]` only for a release whose milestones step 1 closed), update Live product marker, and collapse newly-shipped releases to a single line in Shipped section (never delete shipped).
3. **GitHub:** if disconnected, skip. Create milestones vX.Y.0 in GitHub, assign parent issues, and update BACKLOG_MAP Milestone column (do not touch leaf slices).
4. **Record confirmed dependencies (amend-only, user-confirmed):** for each `[NEW-DEP]` the user confirmed at the halt, add the edge on GitHub (`addBlockedBy` mutation per `references/github-issue-relations.md`) and append the bare `BT-<prereq>` to that epic's `Blocked by` column in `BACKLOG_MAP.md`. 3a may only **add** a blocker edge here, and only with explicit confirmation — `2a` remains the birth writer (`Blocked by = —` at mint), and blocker **clearing** stays with 4a / 0b / merge. Never remove a `Blocked by` entry in 3a. Skip any proposed edge the user declined.
5. **Comment:** post release placement and rationale on each assigned parent feature issue.
6. **Terminal sync gate:** run `python .agents/scripts/reconcile.py --require-gh --ids <comma-list of assigned parent BT-<padded>, plus each epic step 4 amended> --fields milestone,blocked_by` per `references/terminal-sync-invariant.md` (verifies the milestone and `Blocked by` mirrors only — 3a writes no other field). Non-zero → heal per the reference and re-run, **at most 3 attempts**; still non-zero, or `[MIRROR-UNVERIFIED]` → halt and surface the drift. Never loop unbounded.
7. **Render:** invoke `plan-html` using `board` or `plan-document` to render the read-only ephemeral companion `.tmp/render/docs/ROADMAP.html` (never committed; re-render from the `.md` whenever presenting it).
8. **Commit & Push Doc:** `git add docs/ROADMAP.md && git commit -m "docs: roadmap"`, then push to the **default** branch if `gh`/remote is connected (else local commit only). The roadmap is the cross-feature product changelog re-read by `/3a-version-planning` on default (Phase 2 "Live product" marker) — committing here keeps its `[SHIPPED]`/numbering baseline durable across a fresh clone or session. Never sweep unrelated drift into this commit.
9. **Cleanup:** delete `.tmp/3a-roadmap.work.md`.
10. **Hand-off:** *"Roadmap updated. Current release features ready to slice (run `/3b-create-issue`)."*

## Re-run Notes
- Skipping version planning defaults features to `v1.0` (with Z managed by 3c).
