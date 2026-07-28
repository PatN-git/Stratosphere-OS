---
type: plan
title: "StratOS Plan — 3z Slice-Routing Efficiency (revised)"
description: "Right-size slices and remove the 0a relic so AFK orchestration cost is proportionate — without weakening independent verification."
timestamp: 2026-07-23
status: proposed
version: "1.0.0"
---

# StratOS Plan — `3z` Slice-Routing Efficiency (revised)

**Status:** proposed · **Owner:** StratOS framework
**Source:** handover plan from a live BT-037 retro (`cleantech_jobs`), reviewed critically against current StratOS `src/` and revised.
**Scope:** `src/workflows/3b_create-issue.md`, `src/workflows/3z_afk-loop.md`, `src/workflows/0d_nightly-consolidation.md`. No product-code changes.

> **What the review changed vs the source plan.** (1) **Dropped** the original R1 "collapse the Verify subagent into the implementer for low-risk slices" — it reintroduces mark-your-own-homework on *unattended* AFK work (where the independent auditor is the only safety net) and conflicts with the independent-auditor principle. (2) **Re-rooted the fix in slicing:** the auditor wasn't wasteful — it was disproportionate to a one-line slice. Right-size slices and the *same* independent auditor runs once over proportionate work. (3) Kept the `/0a` relic removal (verified against current source). (4) Corrected targets to `src/` (not `.agents/`, which is build output). (5) Folded in `docs/nightly/` preservation.

---

## 1. Context

BT-037 ("Global Visibility for Remote Jobs") ran as two `mode:AFK` slices through `3z`:

| Slice | Size | Real output | Assessment |
|---|---|---|---|
| BT-093 | small | **1 line** REST filter | over-processed — a full independent audit for a one-liner (~90k tok) |
| BT-094 | small | ~55 lines UI + support | fairly-processed — the independent audit caught a real grid bug |

The framework is not structurally wasteful; the waste is a **full audit on a slice too trivial to justify it**, compounded by a redundant `/0a` prefix.

## 2. Root cause

- **Trivial slice, full machinery.** `4a` Phase 1 already bypasses the deep audit for trivial non-security slices — **except** it forces the full audit when `mode:AFK` (correct: no human in the loop, so audit rigor is the substitute). BT-093 was `mode:AFK`, so a one-liner got the full treatment. The lever is **not** relaxing the AFK audit (that removes the only unattended safety net) — it is **not creating one-line slices in the first place**.
- **The `/0a` relic.** In `3z` §2A the dispatch runs `/0a_start-session` *then* `/3d_implement-issue`; but `3d` Phase 0 already self-hydrates (`load-memory`), owns branch **create**-or-restore, and runs the first-slice status + epic transition — and `/0a` is strictly weaker (Phase B never creates a branch, and its task-resolution is moot because `3z` passes an explicit `BT-<padded>`). In §2B, `/0a` is neutered to read-only, duplicating `4a` Phase 0's `load-memory`. The prefix is a v2-era carryover from before `3d`/`4a` self-hydrated.

## 3. Recommendations (revised, ordered by leverage)

### R1 — Value-based minimum-slice floor in `3b_create-issue`  *(primary lever)*
When ICE slicing would emit a slice with **no independent demo/verification value beyond its sibling**, fold it into the sibling or keep the feature whole. Criterion is **vertical value, not LOC** (StratOS slices by value; LOC is the wrong axis). BT-037 (~70 lines, backend filter + its UI surface) was arguably one coherent slice.
- **Effect:** the fixed per-slice orchestration cost (subagent bootstrap + independent audit) is paid once over proportionate work, not twice with half wasted on a triviality. This is what makes the independent auditor's cost acceptable — no need to weaken it.
- **Guard against over-folding:** do **not** merge a backend slice with a UI slice purely to save cost — that produces a multi-file/UI slice that (correctly) triggers the full auditor anyway, and erodes vertical isolation. Fold only when the child has no standalone verification value.
- **Anchor:** `src/workflows/3b_create-issue.md` (Phase 2 slice quiz / ICE section).

### R2 — Remove the `/0a_start-session` prefix from `3z` §2A and §2B  *(the relic)*
- **§2A:** dispatch `/3d_implement-issue` directly (keep passing the explicit `BT-<padded>` and the `docs_read`/`red_confirmed` return contract). `3d` Phase 0 self-hydrates, creates/restores the branch, and runs the first-slice transition + epic promotion.
- **§2B:** dispatch `/4a_verify-and-ship` Phases 1–4 directly (read-only). `4a` Phase 0 self-hydrates. Preserve the `docs_read` return field (P4).
- **Do NOT touch** `3z` §1A (the orchestrator's own `/0a` bootstrap — legitimate, runs once) or `load-memory`'s self-gate.
- **Effect:** eliminates one redundant workflow invocation per subagent (4 for a 2-slice feature) and the duplicated branch/status logic between `0a` and `3d`/`4a`.
- **Anchor:** `src/workflows/3z_afk-loop.md` §2A step 1, §2B step 1.

### R3 — (Optional) Lean the Verify dispatch — independence preserved
Keep the **independent** Verify subagent always (fresh eyes on unattended work — non-negotiable). For clearly-small slices, dispatch it with **minimal inputs** — the slice diff + ACs + the named test files — rather than broad re-hydration, so a genuinely-small-but-valid slice still gets an independent check without a full context rebuild. Pure efficiency; **no** safety trade-off. Low priority — R1 makes it rarely necessary.
- **Anchor:** `src/workflows/3z_afk-loop.md` §2B dispatch inputs.

### R4 — Preserve `0d` nightly outputs for meta-learning  *(from a separate ask; folded in)*
`0d` Phase 2 currently writes its distilled proposal to ephemeral `.tmp/nightly_[date].md`. Instead:
- Write to **`docs/nightly/nightly-<date>.md`** (tracked) so a month of nightlies can be reviewed for recurring meta-patterns.
- Add `nightly/` to the `0d` Phase 3.5 `index.md` rebuild list.
- **Prune/archive** entries older than ~90 days so the review window stays bounded.
- **Anchor:** `src/workflows/0d_nightly-consolidation.md` Phase 2 + Phase 3.5.

## 4. Explicitly out of scope (rejected or unchanged)

- **Collapsing / skipping the independent Verify subagent for "low-risk" AFK slices** — REJECTED. It removes the only safety net on unattended work and reintroduces self-verification. R1 (right-sizing) removes the *motivation* for it instead.
- **Relaxing `4a` Phase 1's `mode:AFK ⇒ full audit` rule** — unchanged; AFK rigor compensates for the absent human.
- **`micro-tdd` Fast-Track A/B** — not the bottleneck (it optimizes the `3d` inner loop, not `3z`-tier cost).
- **`load-memory` self-gate, subagent context isolation** — already correct.
- **The PR-102 `reconcile.py` mirror gate** (`4a` Phase 5 / `3z` ship pass) — unaffected by any change here.

## 5. Acceptance criteria

- [ ] `3z` §2A/§2B no longer invoke `/0a_start-session`; a slice run still restores/creates the branch, sets `status:in progress`, and promotes the parent epic exactly once (via `3d` Phase 0), and `4a` verify still self-hydrates.
- [ ] `3z` §1A still runs the orchestrator `/0a` bootstrap.
- [ ] `3b` folds or refuses a slice with no independent verification value beyond its sibling — verified on a synthetic trivial feature; a legitimately-independent small slice is still emitted.
- [ ] Every AFK slice (including small ones) still spawns the independent Verify subagent.
- [ ] `0d` writes nightly output to tracked `docs/nightly/`, indexes it, and prunes >90-day entries.
- [ ] Re-running a BT-093-class *feature* (now one proportionate slice) shows materially lower total tokens than the ~90k×2 baseline — driven by fewer slices + no `/0a` relic, not by weaker verification.

## 6. Open questions / caveats

- **`docs/nightly/` privacy:** confirmed tracked (committed). Nightly output is transcript-derived; if any retro could contain sensitive snippets, revisit whether it should be gitignored-local instead.
- **Slice-floor threshold** is a judgment call ("no independent demo value"), not a hard number — tune against a few real slices before treating it as a rule.
- **Token figures** from the source retro are transcript-KB-derived (exclude system prompts / tool schemas / cached reads); the relative breakdown and structural conclusion hold regardless.
