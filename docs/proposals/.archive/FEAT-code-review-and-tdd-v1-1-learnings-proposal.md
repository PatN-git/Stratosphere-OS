---
name: code-review-and-tdd-v1-1-learnings-proposal
description: Standalone, independently-shippable changes — a two-axis (spec + standards) verification review with a reusable code-smell baseline in 4a, and TDD seam pre-agreement + test cadence in micro-tdd.
type: proposal
trigger: User. Do not run autonomously.
version: "0.2.0"
timestamp: 2026-07-08
---

# Proposal: two-axis verification review + TDD seam/cadence

**Status:** **Implemented.** Retained as the implementation spec/record. **Self-contained** — describes the two changes (and one no-op decision) independently of any other context.

**Related work (out of scope here):** a separate proposal covers restructuring `concept-framing` into an investigation hub — [`wayfinder-concept-framing-hub`](FEAT-wayfinder-concept-framing-hub-proposal.md). **Do not touch discovery/concept-framing workflows for this proposal.** This proposal changes only `4a_verify-and-ship` and `micro-tdd`, and records one no-op decision about `3d`.

**What this proposal delivers:**
1. A second, independent **Standards** review axis in `4a_verify-and-ship` (code smells + repo standards), reported separately from the existing spec/security audit — §1.
2. **Seam pre-agreement** and an explicit **test cadence** in the `micro-tdd` skill — §2.
3. A recorded decision to **keep** the current `3d` in-loop refactor step (no change) — §3.

---

## 1. Two-axis verification review in `4a_verify-and-ship`

### 1.1 Current behaviour (context for the implementer)
`4a_verify-and-ship` (`.agents/workflows/4a_verify-and-ship.md`) is the HITL "verify then open/update the PR" workflow. Today it audits a single axis:
- **Phase 1 — Value-Add Gate:** skips pure cosmetic/UI changes straight to ship; otherwise proceeds when the change touches business logic, auth, RLS, billing/credits, security boundaries, explicit acceptance criteria, or is a large AFK slice.
- **Phase 2 — Execution:** a **Context Isolation Rule** decides whether to audit natively or via an isolated sub-agent. If this session wrote the code under audit (e.g. ran `3d_implement-issue` or edited the slice's source files), it MUST isolate the audit into an independent sub-agent — the **"Strict Business-Logic Auditor"** — scoped to the slice, read-only, non-committing.
- **Phases 3–5:** the auditor returns an **AC↔test coverage table** (acceptance-criteria vs the test that covers each, with a Gap/Security-Risk column); only findings scored **≥80 confidence** are reported; then a HITL halt (Phase 4) and gated ship (Phase 5).

This single axis answers *"do the tests faithfully cover the requirements and security boundaries?"* (call it the **Spec axis**). It does **not** review *code quality / maintainability* (naming, duplication, coupling, over-abstraction). Those live in a separate third-party cleanup skill (`code-simplifier`, run at the end of `3d`) and in `4b_audit-architecture-drift` (a macro, post-hoc, whole-directory structural audit) — neither runs as an independent quality axis at ship time on the slice diff.

### 1.2 Change — add an independent Standards axis (LOCKED design)
Add a **second, independent, parallel sub-agent** to `4a` — the **"Standards Auditor"** — that reviews the slice diff for code-quality violations, and report its findings in a **separate table** from the Spec axis. The two axes are aggregated **separately and never merged or re-ranked**, because a change can pass one and fail the other (correct behaviour, poor code — or clean code implementing the wrong thing).

This axis is implemented **inside `4a`** (not by modifying `code-simplifier`, which is a third-party skill we do not own or alter, and not by overloading `4b`, which is macro/structural and post-hoc).

**Steps for the implementer:**

**(a) Create the reusable baseline** at `.agents/workflows/.reference/code-smell-baseline.md` with this content:

> A universal code-smell checklist for slice-level review. Each applies unless a repo standards doc (`CODING_STANDARDS.md`, or `.memory/ARCHITECTURE.md` `[[A-xxx]]` rules) explicitly overrides it. Distinguish **hard breaches** (violate a documented rule) from **judgment calls** (heuristic smells) when reporting.
>
> 1. **Mysterious Name** — an identifier that doesn't reveal its intent or role.
> 2. **Duplicated Code** — the same structure repeated instead of shared/extracted.
> 3. **Feature Envy** — a function more interested in another module's data than its own.
> 4. **Data Clumps** — the same group of fields/args travelling together; should be one object.
> 5. **Primitive Obsession** — primitives used where a small domain type belongs.
> 6. **Repeated Switches** — the same `switch`/if-cascade on a type in several places.
> 7. **Divergent Change** — one module edited for many unrelated reasons (low cohesion).
> 8. **Speculative Generality** — abstraction/params/hooks added for imagined future needs.
> 9. **Message Chains** — `a.b().c().d()` coupling the caller to a deep object graph.
> 10. **Middle Man** — a unit that only delegates and adds nothing.

**(b) Add the Standards Auditor to `4a` Phase 2.** Alongside the existing Business-Logic (Spec) auditor, spawn a second independent sub-agent under the same rules already in `4a`:
- **Isolation:** independent sub-agent (Antigravity `invoke_subagent` / Claude Code `Task`, `general-purpose`), obeying the existing Context Isolation Rule.
- **Scope:** the **slice diff only** (new/modified files for this slice), never the whole repo — matching `4a`'s existing token discipline.
- **Reads:** `.agents/workflows/.reference/code-smell-baseline.md` plus any repo standards doc (`CODING_STANDARDS.md` / `.memory/ARCHITECTURE.md`).
- **Guardrails (match `4a`'s existing wording):** *"Review the slice diff for code-smell/standards violations only; do not edit code/tests, do not commit or push."*
- **Output contract:** a **separate** findings list — `File · Smell/Rule · Hard breach | Judgment call · One-line fix` — returned independently of the AC↔test table.
- Run it whenever Phase 2 runs (i.e. for non-cosmetic changes that clear Phase 1). Cosmetic changes that Phase 1 skips are exempt, as today.

**(c) Report separately in Phase 3.** Output two clearly separated sections, no merging, no re-ranking:
- **Spec / Business-Logic** — the existing AC↔test table (ship-blocking; ≥80 confidence, unchanged).
- **Standards / Code Smells** — the new table, **advisory**: surfaced at the Phase 4 HITL handoff for the human to accept, fix, or defer. It does **not** auto-block ship (the ship gate stays governed by the Spec axis). Hard breaches of a documented rule may be flagged as recommended-blocking, but the human decides at Phase 4.

### 1.3 Acceptance criteria
- Running `4a` on a slice containing a deliberate smell (e.g. a `a.b().c().d()` message chain) surfaces it under **Standards**, in a table separate from the AC↔test table, with no re-ranking/merging.
- The Standards auditor never edits files and is scoped to the slice diff (verify it does not read unrelated modules).
- A slice with clean code and a genuine AC gap still fails the Spec axis (Standards passing does not mask it), and vice-versa.
- `code-simplifier` and `4b` are untouched.

---

## 2. Seam pre-agreement + test cadence in `micro-tdd`

### 2.1 Current behaviour (context for the implementer)
`micro-tdd` (`.agents/skills/micro-tdd/SKILL.md`) is the Layer-3 autonomous TDD skill. Its **Fast-Track A (Silent Logic Cycle)** is: **RED** (write exactly one minimal failing test, run the suite, validate it fails for the right reason) → **GREEN** (simplest code to pass, re-run the suite, confirm no regressions) → **REFACTOR** (formatting/cleanup only). It runs under **Silent Execution Mode** (no step narration). It currently: (a) does **not** declare which interface boundary ("seam") a test targets before writing it, and (b) **re-runs the whole test suite on every cycle**.

### 2.2 Change
**(a) Seam pre-agreement.** Add a step **before RED** in Fast-Track A:
- *"**0. Declare Seam:** name the interface boundary being asserted (the function/module/contract under test). For HITL slices, surface it for confirmation; for AFK, log it in one line. Do not test below the agreed seam (internal implementation detail) — assert behaviour at the boundary."*
- Keep Silent Execution Mode intact: the AFK seam log is a single line, not narration. (`3d_implement-issue` already overrides Silent Mode for HITL slices to surface RED/GREEN, so HITL seam surfacing rides on that existing behaviour.)
- This complements the existing **"Stuck" Protocol** (which already fires when a test needs >3 mocked dependencies — usually a wrong-seam signal).

**(b) Test cadence.** Make the loop cadence explicit and cheaper than "whole suite every cycle":
- During the RED/GREEN loop, run the **single target test file** (not the full suite) for fast feedback.
- **Type-check regularly** during the loop (a compile/type error is the common cause of a mis-validated RED).
- Run **one full-suite sweep at the end** of the cycle to confirm no regression (this absorbs the current GREEN "no regression across remaining suite" check, moving it to the end rather than every iteration).
- This is strictly more token-efficient, matching `micro-tdd`'s stated token-optimization goal; the Anti-Regression loop is unchanged.

### 2.3 Acceptance criteria
- Fast-Track A begins by naming a seam (logged in AFK, surfaced in HITL) before any test is written.
- During the loop only the target test file runs; a single full-suite sweep runs once at cycle end; a type-check runs during the loop.
- Silent Execution Mode still holds for AFK (seam is one log line; no added narration).

---

## 3. Decision (recorded): keep the current `3d` in-loop refactor — NO change

`3d_implement-issue` Phase 2 performs refactoring + architecture checks **in the implementation loop**, and `micro-tdd`'s own REFACTOR step is already formatting-only. We considered relocating substantive refactor out of the implement loop into a review step, but **decided to keep the current `3d` Phase 2 in-loop refactor unchanged** — the tight feedback between just-written code and its cleanup is valued, and the code stays cohesive within the slice session.

**Action: none.** Recorded so the choice isn't re-litigated. (This is independent of §1: the new Standards axis in `4a` is a *review-time quality signal*; it does not move refactoring out of `3d`.)

---

## 4. Build order & independence
1. **§2 (seams + cadence in `micro-tdd`)** — smallest, fully standalone, no dependency on §1.
2. **§1 (Standards axis + `code-smell-baseline.md` in `4a`)** — standalone; two files: create the reference, edit `4a`.
3. **§3** — no work; decision only.

All three are independent of the concept-framing/wayfinder proposal.

---

## 5. Refinement log
- 2026-07-08 — carved out as the bucket of changes independent of the concept-framing/wayfinder restructure.
- 2026-07-08 — rewritten to be self-contained (implementable without prior context) and de-referenced from external sources. **Locked:** §1 uses Option A (Standards axis built inside `4a`; `code-simplifier` is third-party and left untouched). §3 **decided** — keep `3d` Phase 2 in-loop refactor, no change.
- 2026-07-08 — marked **Implemented**; cross-link repointed to the split-out [wayfinder proposal](FEAT-wayfinder-concept-framing-hub-proposal.md).
