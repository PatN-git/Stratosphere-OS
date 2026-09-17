# Plan — Feature-Level Acceptance Gate (4a) + 0a Zero-Test Invariant

**Status:** Implemented on `feat/spec-conformance-v4` (PR #107).
**Targets:** `src/workflows/4a-verify-and-ship.md` (1.1.3 → 1.2.0), `src/workflows/0a-start-session.md` (1.1.0 → 1.1.1)
**Origin:** Lifecycle review — a PRD sliced into N children passes N slice-scoped `4a` audits and zero feature-scoped ones. The PR flipped ready for review on a **label count**, not on evidence the assembled feature meets the PRD.

Two independent one-file prose edits to lifecycle bookends, bundled.

---

## 1. Why

### 1.1 The 4a gap
`4a` Phase 2 resolves audit inputs per **slice**: slice diff, slice issue AC. Phase 5 Step 7 ("Epic Check") was pure bookkeeping — all siblings `status:in review` → `gh pr ready`. Nothing between those points asked *does the assembled feature satisfy the parent PRD?*

What fell through:
- PRD AC that no single slice owned (emergent / cross-cutting).
- Integration behaviour that only exists once slices 1 + 3 are both present.
- Slices that individually passed against a drifted reading of the PRD.

Regression was **not** the gap — the repo-wide suite runs on the full feature branch at every ship. The gap is *conformance*.

Wrong tools for it: `4c` is a periodic whole-repo health screen (signal drowns); `4b` is structural drift, not PRD conformance.

### 1.2 The 0a gap
`0a` is administrative hydration + branch alignment. Nothing forbade an agent from running the suite or a build to "establish state" — burning time and tokens before work starts, and producing red output that derails the session into unrequested debugging.

---

## 2. Change A — feature-level acceptance gate

**Placement:** Phase 5 Step 7, before `gh pr ready`.

**Why `ship-only` and not `audit-only`:** `3z-afk-loop` dispatches the named `audit-only` gate (Phases 1–4) **once per slice**. A feature-level audit there would fire N times per feature and stall AFK runs on a condition no single slice can satisfy. Step 7 already lives in `ship-only`, is already parent-scoped, is already conditional, and is the exact moment the PR becomes mergeable. Cost: one extra subagent pass per PRD, not per slice.

**Shipped text:** Step 7's opening gains `→ run the **Feature Acceptance Audit** below, then mark the feature PR ready…`, and the audit is an indented sub-block covering: one Strict Business-Logic Auditor subagent under the Phase 2 guardrail; input = parent PRD full AC set + interface design doc + whole-feature diff (`git merge-base HEAD origin/<default>`) with paths resolved by the parent; scope = cross-slice integration AC and PRD AC unclaimed by any slice, not a re-litigation of shipped slice tables; output = the Phase 3 §1 AC↔test table at ≥ 80 confidence.

**Halt semantics (follows D3):** gaps → halt and surface. PR stays draft, epic stays `status:in progress`, route to `/3b-create-issue` or `/3d-implement-issue`. Explicitly **no re-run to clear** — no unbounded loop, matching the bounded-attempt discipline this PR established for the terminal sync gate.

**Notes:**
- Standalone issues with no parent are unaffected — no Epic Check runs; they open non-draft.
- `3z-afk-loop` reaches Step 7 only through `ship-only`. A halt here is a legitimate AFK stop: PR draft, slice `in review`, human picks it up.

## 3. Change B — 0a Zero Test/Build Invariant

Appended to `## Goal`:

> **Zero Test/Build Invariant:** never run test suites, linters, or build scripts here — `/0a` is administrative context hydration and branch alignment only.

Host- and stack-agnostic on purpose — no `npm`/`vitest` literals. StratOS targets non-JS projects, and naming one stack invites treating unlisted stacks as permitted. Reinforces Phase A's "read-only" framing; Phase B's side effects (checkout, label edit) remain allowed.

---

## 4. Verification

| Check | Result |
|---|---|
| OKF frontmatter + version stamps | see §5 |
| Build regenerates `.agents/skills/` | see §5 |
| Full suite | see §5 |
| Behavioural | Deferred to the next real multi-slice feature: the last slice's `4a` must emit a feature-level AC↔test table before `gh pr ready`, and a `/0a` run must invoke no test or build command. |

No script, reference, or schema changes. Both edits are prose in `src/workflows/` — `.agents/` and `dist/` are build outputs and must not be hand-edited.

## 5. Out of scope
- A standalone `4d` feature-acceptance skill — rejected: no natural trigger, easy to forget, duplicates `4a`'s auditor plumbing. Folding into the existing conditional is strictly smaller.
- Any change to `4b` / `4c`.
- E2E/manual-QA tooling — the `[ ] Manual QA Required` PR checkbox stays the escape hatch.
