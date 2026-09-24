# Plan — Audit Report → Refactor Proposal → Maintenance Epic (4b + 4c)

**Status:** Proposed — stacked on PR #107 (`feat/spec-conformance-v4`). Not implemented.
**Targets:** `src/workflows/4b-audit-architecture-drift.md` (1.0.9 → 1.1.0), `src/workflows/4c-codebase-health-audit.md` (1.0.0 → 1.1.0), `src/workflows/3b-create-issue.md` (2.4.0 → 2.5.0), `src/workflows/0d-nightly-consolidation.md` (1.1.2 → 1.1.3), `src/references/health-audit-report-template.md` (2.0.0 → 2.1.0), `src/references/feature-acceptance-audit.md` (1.0.1 → 1.1.0), new `src/references/audit-to-slices.md` (1.0.0).
**Origin:** Review question — *"shouldn't 4b and 4c share one artifact logic: first a report, then a refactor proposal with slices?"* Yes, and reading the sources surfaced a larger gap behind it: nothing downstream consumes a refactor proposal.

---

## 1. Why

### 1.1 The asymmetry
| | Stage 1 — durable report | Stage 2 — slice proposal |
|---|---|---|
| `4c` | `docs/audits/health-<date>.md` | **none** — the user hand-translates rows into `/3b` input |
| `4b` | **none** — no history of drift per target | `.tmp/refactor-proposal.md` (Template B) |

### 1.2 What the question missed — `3b` has no audit intake
`3b` Phase 1.3 knows exactly two sources: **PRD-sourced** or **raw idea/MVI**. `4b`'s hand-off ("run `/3b-create-issue`") therefore lands on the raw-idea branch, where:
- Phase 2.2's ICE **Fallback (ODI absent): HALT** fires on every slice — audits carry no ODI.
- Phase 2.4's audit degrades to **No PRD** mode: soft `[UNCOVERED?]` against a restated intent, not against the findings.
- The drafts path `.tmp/BT-<padded>-issue-drafts.md` is keyed to a parent that does not exist, so the Template B bodies in the proposal are regenerated, not minted verbatim.

Adding a report to `4b` and a proposal to `4c` without fixing this produces two artifacts nobody reads.

### 1.3 Smaller defects on the same path
- **No stable finding IDs.** `4c`'s report table restarts `#` at 1 in each impact section; `4b` has no report. A slice cannot cite the finding it resolves, so traceability is unprovable.
- **Path collision.** A fixed `.tmp/refactor-proposal.md` shared by two skills clobbers.
- **Retention vs. traceability.** `4c` Phase 4.3 prunes reports at 90 days; an issue that only *links* its evidence loses it.

---

## 2. Decisions (recorded)

| # | Decision | Rationale |
|---|---|---|
| D1 | `4b` assigns the **same four impact tiers** as `4c` (🔴/🟠/🟡/⚪) | One report contract, one ICE mapping, no `3b` HALT on audit input. |
| D2 | Audit slices are grouped under **one maintenance epic per proposal**, not minted standalone | See §4. Standalone degenerates to N branches + N PRs (AGENTS.md §4) and loses the feature-level acceptance gate. |
| D3 | Land as a **stacked PR** with base `feat/spec-conformance-v4` | #107 renamed every file and reference path; building on `main` conflicts wholesale. #107 is already large. Change is additive — merge into #107 before release, or retarget to `main` as 4.1.0 after. |

---

## 3. The shared contract — `src/references/audit-to-slices.md`

One reference, cited by `4b`, `4c`, `3b` (and `feature-acceptance-audit.md`); `build.py`'s citation walk fans it out — no build change. Defines:

1. **Finding IDs.** `F-01…F-NN`, numbered once across the whole report (not per section). Cited externally as `<report-stem>#F-07`.
2. **Report row contract** (both kinds): `ID | Impact | File | Line(s) | Finding | Evidence | Confidence | Law | Recent? | Suggested direction`. `Law` carries `[[A-xxx]]`/`[[DR-xxx]]` or `—`. `Recent?` is `4c`-only (`—` in `4b`).
3. **Impact tiers.** The four categories stay authored in `health-audit-report-template.md`; this reference points at them and adds the `4b` reading: 🔴 an ignored architecture law on an auth/data path · 🟠 a leaked seam or boundary violation on a critical path · 🟡 god-module / duplication / DI violation · ⚪ locality or naming drift.
4. **Proposal contract.**
   - Path: `.tmp/refactor-proposal-<report-stem>.md`. Frontmatter-free (it is `.tmp/`), first line `Source: docs/audits/<report-stem>.md`.
   - Header block: proposed **epic** title + overview (the maintenance epic `3b` mints, §4).
   - Body: Template B slices per `references/issue-templates.md`, each with a `Resolves: F-03, F-07` line under **Current state / Problem**, finding evidence copied **inline** (the report link is a pointer, never the only copy).
   - **Clustering:** group findings into slices by module/`seam`, obeying `3b`'s minimum-slice floor — never one slice per finding by default.
5. **Coverage gate** (reuses the `[UNCOVERED]` leading word): every finding maps to exactly one slice or one exclusion token — `[OPPORTUNISTIC]` (⚪ default), `[DEFERRED: <reason>]`, `[WONTFIX: <reason>]`. A proposal with an open `[UNCOVERED]` is incomplete; never summarize as "mostly covered".
6. **ICE mapping** (deterministic rule, not inference — compatible with `3b`'s "never infer"):
   - Impact: 🔴 3.0 · 🟠 2.0 · 🟡 1.0 · ⚪ 0.5 — a slice takes the **max** tier of the findings it resolves.
   - Confidence: min finding confidence in the slice → ≥ 90 `100%` · 80–89 `80%` · 60–79 `50%`.
   - Size stays a prompt (`3b` Phase 2.2), unchanged.
7. **Critical carve-out.** 🔴 findings become **standalone** slices (no parent) so a security fix is never held behind the epic's Medium work in one feature PR. Ships via `/3d` → `4a` immediately.

---

## 4. The maintenance epic (D2)

Grouping is correct — the earlier "standalone" default only avoided touching `3b`/`4a`/`0d`. What an audit epic needs, per consumer:

| Consumer | Today assumes | Audit epic gets |
|---|---|---|
| Epic issue | minted by `2a` with a PRD | minted by `3b` audit intake: `tier:epic`, `type:maintenance` (already in the label registry), `area:<x>`, `status:planned`; body = proposal header + `Source:` link |
| Spec of record | `docs/prds/BT-<n>-*.md` | the audit report `docs/audits/<report-stem>.md` |
| Branch (`3d` Phase 0.1) | `<type>/BT-<parent>-<slug>` | `maintenance/BT-<epic>-<report-stem>` — no `3d` change, it already keys off the parent's `type:` |
| Milestone | set by `3a` for features | current release from `docs/ROADMAP.md` (else `v1.0.0`) — maintenance needs no MAJOR/MINOR call, so no `3a` pass |
| `4a` Feature Acceptance Audit | parent PRD AC + interface design | the report's `F-xx` rows claimed by the epic's slices; gap = a claimed finding still reproducible in the whole-feature diff |
| `0d` "slicing incomplete" signal | children < PRD §6 stories | children < proposal slice count (read from the epic body) — no PRD → no false positive |

**Epic threshold:** mint an epic only when the proposal has **≥ 2 non-🔴 slices**. One slice → standalone (an epic of one is ceremony).

---

## 5. Per-file changes

### 5.1 `4b-audit-architecture-drift` → 1.1.0
- Phase 1 `_CONSTRAINTS_`: add **"Write only `docs/audits/arch-*` and `.tmp/`."**
- Phase 2: subagent also returns an **impact tier** per finding (D1). Keep the guardrail sentence verbatim — protected, asserted by `tests/test_subagent_spawning.py`.
- Phase 3 splits into own-step writes (one write, one step):
  1. Write report `docs/audits/arch-<target-slug>-<YYYY-MM-DD>.md` (`type: audit-report`, already registered for `docs/audits/*.md`) per `references/audit-to-slices.md`.
  2. Write proposal `.tmp/refactor-proposal-<report-stem>.md` per the same reference.
  3. Retention: delete `docs/audits/arch-*.md` older than 90 days **unless** its stem is cited by a non-`done` `.memory/BACKLOG_MAP.md` row (§5.4).
- Clean Exit unchanged (no report on zero findings).
- Phase 4 hand-off names both paths + the F-count per tier; routes to `/3b-create-issue <proposal path>`.

### 5.2 `4c-codebase-health-audit` → 1.1.0
- `[!IMPORTANT]` ownership note: add the one `.tmp/refactor-proposal-*` write.
- New **Phase 5 — Refactor Proposal** (Handoff → Phase 6): cluster findings per §3.4; default scope 🔴+🟠+🟡, ⚪ → `[OPPORTUNISTIC]`; trigger prompt may widen/narrow tiers. Coverage gate §3.5 is the step's completion criterion.
- Phase 6 hand-off: replace "Fix Critical now / Create issues via /3b" with the proposal path + `/3b-create-issue <proposal path>`.
- Phase 4.3 Retention: same pinning rule as §5.1 step 3 — a report cited by a non-`done` BACKLOG row is kept.
- Clean Exit: no proposal either.

### 5.3 `health-audit-report-template` → 2.1.0
- `#` → `ID`, global `F-xx` numbering; add `Evidence` + `Law` columns (§3.2).
- "Recommended Next Steps" → points at the proposal, drops the per-tier `/3b` prose.

### 5.4 `3b-create-issue` → 2.5.0 — third intake: **Audit-sourced**
- **Hand-off contract / Phase 1.3:** trigger names a `.tmp/refactor-proposal-*.md` → load it + its `Source:` report. Scope = the report's findings.
- **Phase 1.2 defensive promotion:** skip (audit epic is minted `planned`).
- **Phase 2.1–2.3:** the proposal **is** the drafts file — skip drafting; ICE from §3.6 (no HALT).
- **Phase 2.4 Slice Draft Audit:** reads proposal + report. **Breadth** = every `F-xx` maps to a slice or an exclusion token, else `[UNCOVERED]`. **Depth** unchanged. Research/PRD precedence clause does not apply.
- **Phase 3.3 pre-mint guard:** point the grep at the proposal path.
- **Phase 3.4:** when §4's threshold holds, mint the epic **first**, then slices as sub-issues (`addSubIssue`); 🔴 slices standalone. Labels per §4.
- **Phase 3.5 BACKLOG sync:** epic row + slice rows as today; Parent column = the epic. Every audit-sourced row's Links column carries the report stem — this is what pins the report against retention (§5.1, §5.2).

### 5.5 `feature-acceptance-audit` → 1.1.0 (+ `4a` patch bump per `bump_guard`)
Input clause gains: *parent has no PRD and carries a `Source: docs/audits/…` link → input is that report's claimed `F-xx` rows + the whole-feature diff.* Rest unchanged.

### 5.6 `0d-nightly-consolidation` → 1.1.3
"Slicing incomplete" row: for an epic whose body carries `Source: docs/audits/…`, compare children to the proposal slice count, not PRD §6.

### 5.7 Tests / build
- New assertion (extend `tests/test_skill_conformance.py` or a small `tests/test_audit_pipeline.py`): `4b`, `4c`, `3b` each cite `references/audit-to-slices.md`; the built `dist/*/skills/{4b,4c,3b}-*/references/` each contain it.
- `test_subagent_spawning.py`: unchanged phrases must still pass.
- Regenerate `dist/` with `build/build.py`; plugin `VERSION` stays 4.0.0 if merged into #107, 4.1.0 if it lands after.

---

## 6. Out of scope
- An `.last-run.json` equivalent for `4b` — dated filenames already give per-target history.
- Auto-running `/3b` from `4b`/`4c` — the hand-off stays HITL (AGENTS.md §1).
- Changing `4c`'s ≥ 60 / `4b`'s ≥ 80 thresholds.

---

## 7. Verification

| Check | How |
|---|---|
| Frontmatter + version stamps | `python build/validate.py` |
| Fan-out | `python build/build.py`; `audit-to-slices.md` present in all three built skills |
| Full gate | `bash scripts/check.sh` (build, validate, pytest, verify_scripts, install-harness L1, dist drift) |
| Behaviour, `4c` path | run `/4c-codebase-health-audit` on a real project → report + proposal; every `F-xx` resolves to a slice or token; `/3b-create-issue <proposal>` mints epic + sub-issues without an ICE HALT; `reconcile.py --require-gh` → `[MIRROR-OK]` |
| Behaviour, `4b` path | `/4b-audit-architecture-drift <dir>` → `arch-*` report + proposal; same `3b` checks |
| Epic close-out | one audit epic taken through `3d` → `4a`; Feature Acceptance Audit reads the report, not a PRD |

**Not covered by L3:** the lifecycle harness never runs `4b`/`4c`; behaviour rows above are manual until it does.

---

## 8. Risks
- **Epic body as data.** §4's `0d` and `4a` branches key off a `Source: docs/audits/…` line in the epic body. If a human edits it out, both fall back to PRD behaviour and misfire. Mitigation: `3b` writes it as the body's first line; `0d` reports `[DRIFT]` on an audit epic with no PRD and no `Source:`.
- **Retention pinning depends on BACKLOG hygiene.** Reports are kept while a non-`done` row cites them (§5.1/§5.2). A row left stale keeps a report forever — harmless; a row dropped early lets a live epic's report be pruned — survivable, because evidence is inline in every slice (§3.4).
