# Plan — Unified lifecycle status + BACKLOG_MAP↔GitHub identity (status spine, review state, parent/blocked split)

Status: **APPROVED — ship as a MAJOR** (renames public contracts: label set + BACKLOG column schema). To be **merged with another all-files change under a single MAJOR bump** by a follow-up agent (see §Handoff / merge notes).
Author path: manual IDE execution (touches `src/**`; build regenerates `dist/**`).

## Problem (two coupled defects)

1. **Status is smeared across three uncoordinated axes** with three different vocabularies that don't even agree file-to-file:
   - doc frontmatter `status:` (`draft`/`ready-for-design`/`ready-for-slicing`; PRD *template* separately declares `ready-for-design|in-progress|complete`; design template declares `draft|ready-for-slicing|obsolete`),
   - GitHub issue `status:*` label,
   - BACKLOG_MAP `Status` column.
   Consequences: the parent epic is minted at `status:in progress` at PRD-draft time (an *inversion* — the container reads "building" while its design reads "not yet sliced"); `status:needs_spec` is a **dead label** (never applied by any workflow); the PRD `ready-for-design → ready-for-slicing` transition **dangles** (2b never advances it); doc statuses **never reach a terminal state** and go stale at `ready-for-slicing` forever.

2. **BACKLOG_MAP mis-models parent/child.** Hierarchy is stored as free text (`Sub-issue of BT-<parent>`) in a `Dependencies` column **shared with blocking deps**, written **only on the child**. The parent→children edge is dropped (GitHub stores it bidirectionally), the two relation types are conflated, and the prose format can't be reconciled byte-for-byte with `gh`.

Additionally surfaced while scoping: 4a's epic-completion gate (`4a_verify-and-ship.md` Phase 5, step 7) is a **chicken-and-egg** — it fires only when all sub-issues are *closed*, but sub-issues close only on PR *merge*, which the same step is trying to enable. The new `status:in review` state resolves this.

---

## Locked decisions

1. **One source of truth for work-status: the GitHub issue `status:*` label.** BACKLOG_MAP is a *projection* of it, not a co-authority. Docs never carry work-status.
2. **Doc frontmatter carries editorial state only:** unified `status: draft | approved | superseded` across PRD + interface-design. "What workflow runs next" is *derived from the epic's issue status label*, never stored on a doc.
3. **Add `status:in review`** to the registry; it is load-bearing (fixes the 4a deadlock) and de-overloads `in progress`. **Revive `status:needs_spec`** by giving it a real producer (epic birth).
4. **Split `Dependencies` into two structured columns — `Parent` and `Blocked by`.** Store the single-valued parent pointer on the child only; the parent's children are a *query* (`filter Parent = BT-<epic>`), never a stored list (avoids drift). Blocking is a separate comma-list of bare IDs.
5. **Identity contract:** seven BACKLOG_MAP columns (`ID, Title, Status, Labels, Milestone, Parent, Blocked by`) must be byte-identical mirrors of GitHub's structured fields — **`Milestone` is one of them and stays** (it was always a mirror column; the "GitHub-only" call applies to *doc frontmatter*, which carries no `milestone:`). `ICE` and `Ref` are the sanctioned local-only augmentation. **Closed issue ≡ `status:done`.** Drift is already surfaced by the existing `/0d` Phase 3.6 check (GitHub authoritative) — extend it, don't replace it.
6. **No hierarchical IDs** (`BT-059-01` stays forbidden, per memory-protocol §8) — flat IDs, hierarchy via the `Parent` column.
7. **`Parent = —` is first-class, not "missing".** Both epics and standalone slices/spikes carry `Parent = —`; they are disambiguated by `tier:` (`tier:epic` = feature root; `tier:slice` = standalone unit, own branch+PR per constitution §4). **No placeholder parent** is ever minted — a fake parent would be an edge GitHub doesn't have, breaking the identity contract.
8. **Template A spikes (`tier:slice` + `status:needs_spec`) are milestone-exempt and excluded from `/3c`** until resolved — same treatment as `concept:*`. Resolution either (a) converts in place to Template B (gains ICE + `status:planned` + milestone, enters sprint flow) or (b) spawns Template B child slices and closes `done`. Confirmed answers this round: label is **`status:in review`**; **`milestone` is GitHub-only** (not mirrored into doc frontmatter); **migration is a one-shot external script, never carried in StratOS**.

## Invariants (must hold after the change)

- **Single Status Invariant** (already in template): exactly one `status:*` per issue; remove the prior on transition.
- **Single writer per transition edge:** no two workflows write the same status edge (see §Transition ownership).
- **No work-status vocabulary in doc frontmatter; no editorial vocabulary on issues.** The two lifecycles never share tokens.
- **BACKLOG_MAP never stores a child list on an epic.** Reverse edge is derived.
- **Concept issues remain exempt** from the status invariant and lifecycle (existing rule preserved).

---

## Target state machines

### Epic (`tier:epic`)
```
needs_spec ──▶ planned ──▶ in progress ──▶ in review ──▶ done
     │            │             │              │
     └────────────┴─────────────┴──────────────┴──▶ blocked (any point)
```
| Status | Meaning | Set by |
|---|---|---|
| `needs_spec` | epic minted; PRD (+design if UI) not yet complete | 2a (mint) |
| `planned` | spec **and** design complete; ready to slice / slices exist | 2b freeze (UI) or 2a Publish (non-UI); 3a/3b keep |
| `in progress` | ≥1 child slice has entered 3d | 3d/0a (first slice start) |
| `in review` | all child slices `in review`; feature PR marked ready-for-review | 4a Epic Check |
| `done` | PR merged → all children auto-closed | merge (4a confirms) |
| `blocked` | blocking child / external dep | 3z / manual |

### Slice (`tier:slice`)
```
planned ──▶ in progress ──▶ in review ──▶ done
   │            │              │
 (needs_spec for Template A spikes)      └──▶ blocked
```
| Status | Meaning | Set by |
|---|---|---|
| `needs_spec` | Template A spike / high-uncertainty | 3b (Template A) |
| `planned` | created & (optionally) sequenced into a sprint | 3b (born), 3c (re-sync) |
| `in progress` | actively implemented | 3d/0a |
| `in review` | code complete + verified + committed/pushed to feature PR; awaiting merge | 4a ship |
| `done` | PR merged (issue auto-closed) | merge |
| `blocked` | 3z couldn't cover after retries | 3z |

**Registry delta:** add `status:in review`. Final set (6): `needs_spec, planned, in progress, in review, blocked, done`.

### Spikes & standalone units (Template A)
A `tier:slice` may have **no parent** (`Parent = —`) — a standalone unit with its own branch+PR (constitution §4). A Template A spike additionally sits at `status:needs_spec` and is **milestone-exempt + excluded from `/3c`** (mirrors the `concept:*` exemption) until it is resolved:
- **Child spike** (blocks a PRD's slices): `Parent = BT-<epic>`, roadmapped under its epic; on resolution converts to Template B or closes and unblocks siblings.
- **Standalone spike** (parked idea): `Parent = —`; on resolution either converts in place to a Template B standalone slice (gains ICE + `planned` + milestone) or spawns a new epic + Template B children and closes `done`.

`/3c` must therefore operate on `tier:slice AND status ∈ {planned}` (never auto-flip `needs_spec` → `planned`).

---

## Target BACKLOG_MAP schema

Header row changes from a single `Dependencies` column to two:

```
| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |
```

- **Parent** — single `BT-<parentPadded>` for slices; `—` for epics/standalone. Mirrors gh sub-issue parent.
- **Blocked by** — comma-list of bare `BT-<padded>`; `—` if none. Mirrors gh blocked-by.
- **Column convention (unchanged, but make it explicit for implementers):** the `Status` column holds the **bare** status token (`in progress`), i.e. the `status:` label with its prefix stripped; the `Labels` column carries every **non-status** label and must **not** duplicate the status. So the GitHub `status:*` label maps to the `Status` column, not `Labels` — the drift check compares accordingly.
- Total table = **9 columns** = the **7 gh-mirror columns** + the **2 local-only** (`ICE`, `Ref`).
- Example rows:
  - Epic: `| BT-042 | Feature name | needs_spec | tier:epic, type:feature, area:FE-x | v1.2.0 | — | — | ICE: - | [[A-003]] |`
  - Slice: `| BT-051 | Slice title | in progress | tier:slice, type:feature, mode:HITL, size:medium | v1.2.3 | BT-042 | BT-050 | ICE: 0.5 (I:1.0, C:100%) | [[L-012]] |`

---

## Target doc frontmatter

### PRD — `docs/prds/BT-<padded>-<slug>.md`
```yaml
type: prd
title: "BT-<padded>: <Feature name>"
bt: BT-<padded>                 # join key to the epic issue / BACKLOG_MAP
resource: <GitHub issue URL>
status: draft | approved | superseded   # editorial ONLY
timestamp: <YYYY-MM-DD>
version: "x.y.z"
```
- 2a writes `draft`; flips to `approved` at Publish validation. 2b never touches PRD status.

### Interface design — `docs/design/BT-<padded>-interface.md`
```yaml
type: interface-design
title: "Design: BT-<padded> - <Feature Name>"
bt: BT-<padded>
prd: <path to PRD>
surface: ui-generator-page | ui-generator-feature | ui-manual | non-ui
status: draft | approved | superseded
timestamp: <YYYY-MM-DD>
version: "x.y.z"
```
- 2b writes `draft` at init; flips to `approved` at freeze — and the *same freeze* advances the **epic issue** to `status:planned`.

### Slices
No separate doc. Canonical record = GitHub issue body (Template A/B) + BACKLOG_MAP row. Do not introduce per-slice `.md` files (would be a third dual-write surface with no reader).

---

## Transition ownership (single writer per edge)

| Edge | Owner | Also does |
|---|---|---|
| create epic → `needs_spec` | 2a Phase 2 | PRD `status: draft` |
| PRD validated (non-UI) → epic `planned` | 2a Phase 5 | PRD → `approved` |
| PRD validated (UI) → epic stays `needs_spec` | 2a Phase 5 | PRD → `approved` |
| design frozen → epic `planned` | 2b Phase 4 | design → `approved` |
| **2b skipped (no external surface, hands to 3b) → epic `planned`** | 2b Phase 1 step 2 | (no design doc produced) |
| **defensive: epic still `needs_spec` at slicing → `planned`** | 3b Phase 1 (entry) | idempotent guard; covers any missed promotion above |
| slices created → slice `planned`/`needs_spec` | 3b Phase 3 | writes `Parent`, `Blocked by` cols |
| first slice starts → slice `in progress`; epic `planned→in progress` | 3d/0a | — |
| coverage fails → slice `blocked` | 3z | — |
| slice shipped → slice `in review` | 4a step 6 | updates feature PR |
| all siblings `in review` → epic `in review` + PR ready | 4a step 7 | `gh pr ready` |
| PR merged → slices+epic `done` (auto-close) | merge | 4a/0b confirm |
| nightly **drift check** (read-only): compare 7 mirror cols vs `gh`, emit `[DRIFT]` — never overwrites | 0d Phase 3.6 | — |

---

## Per-file edits

### Workstream A — status lifecycle + review state
| File | Change |
|---|---|
| `src/workflows/2a_write-prd.md` | Phase 2: mint epic `status:needs_spec` (was `in progress`). Phase 5: PRD frontmatter `status: draft`; **non-UI** → flip epic `needs_spec→planned`; BACKLOG row Status `needs_spec` (or `planned` non-UI). |
| `src/workflows/2b_interface-design.md` | Replace `status → ready-for-slicing` (lines 66/73/78) with: design doc `status → approved` **and** epic issue `needs_spec→planned`. Phase 2 init keeps `status: draft`. **Also** the Phase 1 step 2 skip/handoff path (no external surface) must promote epic `needs_spec→planned` before handing to 3b. |
| `src/workflows/3b_create-issue.md` | Slices born `status:planned` (Template A spike → `needs_spec`, milestone-exempt). **On entry (Phase 1): defensively promote parent epic `needs_spec→planned` if still there (idempotent guard for any missed 2a/2b promotion).** |
| `src/workflows/3c_sprint-planning.md` | Operate on `tier:slice AND status:planned` only; **never auto-flip `needs_spec`→`planned`** (excludes Template A spikes, same as `concept:*`). |
| `src/workflows/3d_implement-issue.md` | First-slice rule: slice→`in progress`; parent epic `planned→in progress` only if not already past it. |
| `src/workflows/0a_start-session.md` | Align: epic→`in progress` only via first-slice rule (keep the remove-prior-label list; add `in review` to the removal set for safety). |
| `src/workflows/4a_verify-and-ship.md` | Step 6: slice→`status:in review` (was "leave at in progress"). Step 7: gate on **all siblings `in review`** (was "closed"); epic→`in review` + `gh pr ready`; `done` deferred to merge. Update Hand-off contract line 12. |
| `src/workflows/3z_afk-loop.md` | Terminal set includes `in review`; retry/preflight excludes `in review` and `done` (not just `done`). |
| `src/workflows/0b_stop-session.md` | `done` detection = issue closed/merged; don't force `done` on unmerged slices. |
| `src/memory-templates/BACKLOG_MAP.md` | Registry: add `status:in review`; document lifecycle order in a comment. |

### Workstream B — doc frontmatter unification
| File | Change |
|---|---|
| `src/references/PRD-template.md` | `status:` → `draft \| approved \| superseded`; add `bt:`; drop `ready-for-design`/`in-progress`/`complete`. |
| `src/references/design-doc-template.md` | `status:` → `draft \| approved \| superseded` (rename `obsolete`→`superseded`); confirm `bt:` present. |
| `src/rules/okf-protocol.md` | Add one line under §2 documenting the canonical doc-status vocab (`draft/approved/superseded`) for `prd`, `interface-design`, `discovery-brief`. (OKF stays value-agnostic; this is guidance.) |
| `src/workflows/1b_concept-framing.md` | Align discovery-brief `status` if it uses the old vocab (verify during execution). |

### Workstream C — BACKLOG_MAP parent/blocked split
| File | Change |
|---|---|
| `src/memory-templates/BACKLOG_MAP.md` | Split header block `Dependencies` → `Parent` + `Blocked by`; update Rules "Include only ID, Title, Status, Labels, Milestone, **Parent, Blocked by**, ICE, Ref"; update example row; add identity-contract note (7 cols mirror `gh` incl. Milestone; ICE+Ref local; closed≡done). |
| `src/rules/memory-protocol.md` | §8: "hierarchy tracked exclusively via the **`Parent`** column" (was `Dependencies`); §2 bare-ID note: `Parent`/`Blocked by` columns (was `Dependencies`). |
| `src/workflows/3b_create-issue.md` | Phase 3 step 4: write `Parent = BT-<parentPadded>` and `Blocked by = <ids>` in the two columns (was free-text `Dependencies`). |
| `src/workflows/2a_write-prd.md` | Epic BACKLOG row: `Parent = —`. |
| `src/workflows/3a_version-planning.md`, `3c_sprint-planning.md` | Any BACKLOG row-shape references updated to the 9-column header. |
| `src/workflows/0d_nightly-consolidation.md` | **Extend the existing Phase 3.6 drift check** (already grounds map against GitHub, emits `[DRIFT]`, GitHub authoritative) to also compare the two new columns `Parent` + `Blocked by` (and `Labels`) — not just status/milestone. Reuses the mechanism you already rely on; no new reconciliation pass, no per-run bloat (it's the dedicated HITL maintenance workflow). |

### Pre-flight discovery (run FIRST — this plan's file list may be incomplete)
This is a contract rename; enumerated files above are the known hits, not a guarantee. Before editing, grep `src/**` for stragglers and fold any into the right workstream:
```
rg -n "Dependencies|Sub-?issue of"          src/   # BACKLOG column refs (Workstream C)
rg -n "ready-for-slicing|ready-for-design"  src/   # old doc-status vocab (Workstream B)
rg -n "status:in progress|status:needs_spec|status:planned|status:blocked|status:done" src/  # status label writers (Workstream A)
rg -n "in-progress|complete|obsolete"       src/references/  # old template status enums
```

### Build / versioning
- Every touched `src/**` file needs a `version:` bump (build stamps `dist/**`; bump-guard blocks unbumped shipped changes).
- **Semver: LOCKED = MAJOR.** Renames public contracts (label set + BACKLOG column schema) → passes 3a's own MAJOR compatibility test. **Do not run `build/build.py` or bump `VERSION` in isolation** — this ships batched with the other all-files change under ONE MAJOR bump (see Handoff notes).

---

## Migration (one-shot, external — NOT carried in StratOS)

Only one existing install (the CleanTech test project). Migration is a **throwaway script run once against that repo, then deleted** — no permanent migration workflow, no `/0d` sub-step, no ongoing token cost in the StratOS product.

Deliverable: `docs/plans/migrate-backlog-oneshot.py` (this repo, delete after use). Design:
- **File transforms (deterministic, auto-applied with `--write`; dry-run default):**
  1. Split BACKLOG_MAP `Dependencies` → `Parent` + `Blocked by` (parse `Sub-issue of BT-x` → Parent; remainder → Blocked by), rewrite header to 9 columns.
  2. Remap PRD/design frontmatter `status: ready-for-design|ready-for-slicing` → `approved`; leave `draft` as-is; `obsolete` → `superseded`.
- **GitHub-side (judgment + external writes — EMITTED as a reviewable `gh` command script, never auto-executed):**
  1. `gh label create "status:in review"`.
  2. Per epic at `status:in progress` with no child in 3d → suggested relabel to `needs_spec`/`planned` (human confirms before running).
- Idempotent: re-running on an already-migrated repo is a no-op.
- Run order: **after** the `src/**` changes ship (script targets the new schema).

---

## Verification

- **Flow test:** run 2a→2b→3b→3d→4a on a throwaway feature (the repo's `.tmp/flow-test` harness) and assert:
  - epic status walks `needs_spec → planned → in progress → in review`;
  - slice walks `planned → in progress → in review`;
  - BACKLOG_MAP `Parent`/`Blocked by` populate correctly and match `gh sub-issue list` / blocked-by;
  - no doc frontmatter ever carries a work-status token; no issue ever carries `draft`/`approved`.
- **4a deadlock regression:** confirm the Epic Check now fires (marks PR ready) *before* merge, on all-siblings-`in review`.
- **Drift detection:** hand-corrupt a BACKLOG row's `Parent`/`Blocked by`/status/milestone, run `/0d`, assert Phase 3.6 emits `[DRIFT]` for each (GitHub authoritative; advisory, not auto-fixed).
- **Lint:** `validate_memory.py` + build (`build/build.py`) pass; bump-guard green.

---

## Handoff / merge notes (for the agent combining this with the other all-files plan)
- **Single MAJOR bump.** Both plans ship together; bump `VERSION` and run `build/build.py` **once**, at the end of the combined change — not per-plan. Don't double-bump.
- **Likely file overlaps** to reconcile (both plans probably touch these): `src/workflows/2a`, `3b`, `0d`, `src/rules/memory-protocol.md`, `src/rules/okf-protocol.md`, `src/memory-templates/BACKLOG_MAP.md`. Apply both sets of edits to the same file in one pass; re-run the §Pre-flight discovery greps after merging to confirm nothing was missed.
- **Order:** land `src/**` edits (this plan's Workstreams A–C) → build → verify → then run the one-shot migration against CleanTech (never before the build, since it targets the new schema).
- **Do NOT commit** `docs/plans/migrate-backlog-oneshot.py` into `dist/`; it lives in `docs/plans/` and is deleted after the single CleanTech run (it's excluded from build globs, but confirm).
- **`.memory/BACKLOG_MAP.md` in THIS repo** is on the old schema too — it gets migrated by the same one-shot script (or by hand), separate from the `src/memory-templates/` template edit.

## Resolved (all questions closed)
- **Semver:** LOCKED **MAJOR**; batched with the other all-files change under one bump. ✔
- **Label spelling:** `status:in review` (matches `status:in progress`). ✔
- **Milestone:** stays a BACKLOG_MAP mirror column (kept honest by `/0d` Phase 3.6 drift check); "GitHub-only" means simply *not* mirrored into doc frontmatter. ✔
- **Migration:** one-shot external throwaway script (`docs/plans/migrate-backlog-oneshot.py`), deleted after the single CleanTech run; nothing carried in StratOS. ✔
- **Spikes / `Parent = —`:** no placeholder parent; Template A spikes milestone-exempt + `/3c`-excluded until re-specced (Locked decisions 7–8). ✔
- **2b-skip gap:** epic promotion to `planned` covered on the 2b skip path + a defensive idempotent guard at 3b entry. ✔
