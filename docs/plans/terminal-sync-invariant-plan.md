# Plan — Process-Integrity Gates (anti-drop-off / anti-skip)

**Status:** Reviewed + scoped — awaiting final approval. Do not implement yet.
**Target:** PR #102 (`fix/post-v3-polish`, base `main`), v3.0.1 line.
**Origin:** A live 3z run shipped a slice but dropped 4a Phase 5 Step 6 (issue/BACKLOG `status:in review` sync). Prose was correct — the agent skipped a trailing low-salience step after the high-salience `gh pr` call (completion bias). Broadened to the general class: *long tool-heavy workflows where the agent skips a step.*

> **Critic pass applied.** The gate is a **deterministic script** (not circular prose); heal = **upsert keyed by BT-id** (never append); **3z Rule B dropped** (3z runs 4a Phase 5 in its own context → inherits the gate); **0d is not the AFK backstop** (advisory/nightly); mirror-field count fixed **7→5**; end-state **deferred to the citing workflow**.

Two mechanism types, chosen by fit: **deterministic script** where the check is machine-diffable (near-zero runtime tokens, un-fakeable exit code), and **low-cost prose** where the failure is semantic and a line or two buys real quality. Explicitly *not* blanket checklists (they cause gate-fatigue → rubber-stamping).

---

## 1. Why
Workflows with a **"Publish/Commit & Sync"** terminal phase do a dual write: a high-salience GitHub call **plus** a low-salience `.memory/BACKLOG_MAP.md` mirror / label transition. Completion bias lands the GitHub call and drops the mirror — silently — and every downstream workflow reads the corrupted map. A prose "verify at the end" step is skipped by the same bias; the gate must be un-fakeable. Separately, other skip-classes (silent truncation, unverified test claims, silent RED) are cheaply reduced by targeted prose.

## 2. Mechanism A — deterministic mirror gate

### 2.1 New script `src/scripts/reconcile.py` → `.agents/scripts/reconcile.py`
Invoked at a sync phase's end, exactly like 4a already invokes `design_theme.py` as a hard halt.
- **Contract:** `python .agents/scripts/reconcile.py --ids BT-007[,…] [--expect-pr]`
- Parse those rows from `.memory/BACKLOG_MAP.md` (9-col); `gh issue view <n> --json labels,milestone,comments` (+ blocked-by).
- Assert the **5 mirror fields** agree: status label ↔ Status; milestone ↔ Milestone; non-status labels ↔ Labels; parent ↔ Parent; blocked-by ↔ Blocked by. (PR-link comment only with `--expect-pr`.)
- Divergence → **exit non-zero**, print `[MIRROR-DRIFT BT-<n>: <field> map=<x> gh=<y>]`.
- Offline / no-`gh` → BACKLOG internal-consistency only, print `[local-only]`, **exit 0**. Never writes.

### 2.2 New reference `src/references/terminal-sync-invariant.md` (~18 lines, v1.0.0)
The heal protocol behind the script:
- **Gate:** run `reconcile.py --ids <touched>`; non-zero = **halt, do not close/ship**.
- **Heal:** per `[MIRROR-DRIFT]`, apply the missing write as an **upsert keyed by `BT-<padded>`** (find-or-replace — never append), then **re-run until exit 0**.
- **End-state is defined by the citing workflow, not here** (e.g. 4a's conditional epic-flip). The reference asserts *mirror agreement*, never a hard-coded target.
- **Offline** degrades to self-attestation (no GitHub to cross-check) — acknowledged.

### 2.3 Script wire-in
| Workflow | Terminal step | Reconciles | Bump |
|---|---|---|:---:|
| `4a_verify-and-ship` | Phase 5 Step 8 | shipped slice: `in review` + PR comment (`--expect-pr`) + blocker-clear | 1.1.0→1.1.1 |
| `3b_create-issue` | Phase 3 end | created slice(s): labels + parent + blocked-by + milestone (upsert) | 2.1.0→2.1.1 |
| `3c_sprint-planning` | Phase 5 end | sequenced slices: milestone + status + confirmed blocked-by edges | 2.1.0→2.1.1 |
| `3a_version-planning` | Phase 4 end | roadmapped epics: milestone assignment | 1.0.5→1.0.6 |

**Optional cheap add-ons** (mirror applies, lower severity — include if you want full coverage): `2a` (epic BACKLOG row; not its doc-push), `2b` (epic promotion mirror), `1c` (concept-map close). ~1 line + one bump each.

## 3. Mechanism B — good-ratio prose gates

| # | Gate | Where | Bump |
|---|---|---|:---:|
| **P1** | **Disclose omissions** — new §4 bullet: *"If you cap, sample, truncate, or withhold anything (top-N, 'and more', sub-threshold findings), state the count and what was dropped. Never present a partial set as complete."* Universal — one always-on rule covers every workflow's output. | `output-mode.md` §4 | 1.0.4→1.0.5 |
| **P2** | **Observed test result** — ship/hand-off records the *actual* pass/fail summary line from the run, not a "tests pass" claim. | `4a` Phase 5 + reinforce `3d` hand-off | 4a covered above; `3d` already bumped this PR (2.1.1) — no re-bump |
| **P3** | **AFK RED recording** — in silent/AFK mode, return the RED observation (failing assertion + "failed for absent functionality, not compile error") in the slice JSON (`red_confirmed`). | `micro-tdd` FT-A + `3d` Step 2A return contract | micro-tdd 1.1.1→1.1.2; 3d no re-bump |
| **P4** | **3z names the reference docs read** — Step 2A/2B subagent return JSON adds `docs_read: []` (PRD, design doc, LEARNINGS, ARCHITECTURE, etc. actually opened); Phase 4 Final Report names them per slice. Lets the user confirm the right PRD/design artifacts were used (or catch a skipped frozen design doc). | `3z` Step 2A/2B contracts + Phase 4 | 1.0.14→1.0.15 |

## 4. Regression lock
Extend the `test_subagent_spawning.py`-style check: assert each script-wired workflow calls `reconcile.py`, and that `3z` carries `docs_read`. **Locks wiring only** — behavior is guaranteed by the script exit code at runtime; the test is not a substitute for that.

## 5. Explicitly NOT doing
- **Test-suite-green-at-ship *script* (#2)** — **cut entirely** (not a follow-up). P2 is the cheap prose form of the same concern; the heavier script (needs a stored per-project test command) is out of scope.
- **0d rework** — Phase 3.6 stays the advisory nightly report; the in-band `reconcile.py` is the real-time gate. (Small nicety: correct 0d's "7 mirror fields" wording to **5**.)
- **Generic terminal checklists** — fatigue → rubber-stamping. No.
- **Already-gated** — design-token `design_theme.py`, 3d coverage map, 4a AC×test table + withholding note, single-writer/idempotency guards, `.tmp` cleanup. Untouched.
- **2a/2b doc-push check** — their fragile write (commit to `default`) is a different concern the mirror gate doesn't cover; out of scope.

## 6. Build / verify
- `reconcile.py` offline unit tests (both agree / each field diverging / offline exit-0).
- `build.py` (script + reference into both hosts), `validate.py .` (one bump per changed `.md`, vs fork-point), `bump_guard.py .` (VERSION 3.0.1 > 3.0.0 — `reconcile.py` covered as a new framework artifact).
- Full CI suite + the new wiring test.

## 7. Scope decision (for approval)
- **Script (`reconcile.py`):** core set **4a, 3b, 3c, 3a** — recommended. Tier-3 (`2a, 2b, 1c`) optional cheap add-ons.
- **Prose:** **P1** (universal), **P2**, **P3**, **P4** (3z provenance).
- **Out:** #2 test-green script, generic checklists, doc-push check.

## 8. Residual risks
- Gate protects the issue↔BACKLOG mirror, not doc-pushes (2a/2b) — acknowledged.
- Offline create (`BT-LOCAL`) degrades to self-attestation — acknowledged.
- `reconcile.py` must parse the 9-col markdown table robustly; a parser bug could false-block a ship → mitigated by unit tests + the offline exit-0 path.
