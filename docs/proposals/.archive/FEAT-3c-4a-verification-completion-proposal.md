---
name: 3c-4a-verification-completion-proposal
description: Proposal for slice-completion and integration-verification gates across 3c_implement-issue and 4a_verify-and-ship.
type: proposal
trigger: User. Do not run autonomously.
version: "1.0.0"
updated: 2026-06-22
---

# Workflow Proposal: 3c / 4a verification & completion gates

**Status:** Parked proposal. Not yet implemented. Pick this up in a fresh session.
**Origin:** Surfaced during a review of `github.com/mattpocock/skills` v1 applied to StratOS (see "References" §8). This document is self-contained — you should not need to redo that research.

> **Note on numbering:** this proposal was written before the 3-series renumber (version-planning=3a, create-issue=3b, sprint-planning=3c, implement-issue=3d). Where it says "3c implement-issue" read **3d_implement-issue**; where it says "3a create-issue" read **3b_create-issue**. The logic is unchanged.

> **Scope of this proposal (keep it tight).** Two changes to the verification flow:
> 1. **Proposal 1 (recommended, low-risk):** add a slice-level **completion gate** to the implement workflow.
> 2. **Proposal 2 (optional, genuinely new):** add a **PRD-level integration verification** before merge.
>
> **Out of scope** (decided against — see §6 so you don't re-litigate): dissolving `4a` into the implement workflow; turning `4a` into an auto-invoked skill; adding a sub-agent re-audit at the end of the implement loop. These were considered and rejected with reasons.

---

## 1. Why this exists (the problem in one paragraph)

The implement→verify flow has a **gap at the bottom and a gap at the top**. At the slice level, the implement workflow can declare a slice "done" without ever confirming that every acceptance criterion (AC) in the slice issue is actually covered by a passing test — a classic *premature-completion* hole. At the feature level, every slice is verified **in isolation** by `4a_verify-and-ship`, but **nothing verifies that the assembled slices compose into the feature the PRD described** before the PR is merged. Neither gap is currently closed.

---

## 2. Current state of the flow (verified against the source, 2026-06-22)

Files: the implement workflow and `4a_verify-and-ship.md`. Both are `type: workflow HITL`, user-invoked (they install as slash commands on both Claude Code and Antigravity).

**Implement workflow (per slice):** Phase 0 Branch & Context Intake → RED → GREEN → REFACTOR → Fast-Track Protocols → Guardrails. It links *each test* to requirement IDs and verifies green + no regressions, then commits incrementally. **It has no exit step that checks the slice's full AC set is covered.**

**`4a_verify-and-ship` (per slice — confirmed, not per-PRD):**
- Phase 1 **Value-Add Gate**: skip pure UI/cosmetic; proceed only if the slice touches RLS / auth / billing / business-math / security boundaries / explicit PRD AC with edge cases / `[size:large][type:AFK]`.
- Phase 2 **Context Isolation Rule**: run natively only if "you have not run the implement workflow and have not edited files under **the slice's** source paths this session"; otherwise dispatch an independent **Strict Business-Logic Auditor** sub-agent (read-only; returns the AC↔test table only).
- Phase 3 **Output**: a compact **AC↔test table** (AC / Requirement → Test Target → Status → Confidence → Gap), gated to findings with confidence ≥ 80.
- Phase 4 **Handoff**: HALT; human sends it back to the TDD loop or approves.
- Phase 5 **Ship**: commit *slice* code+tests only, push, **one PR per feature branch** that **"accumulates each shipped slice"** (`Closes #<sliceIssue>` + parent `BT-<padded>`); bi-directional GitHub trace.

**The merge is the only "all slices" event, and it is not a check:** Phase 5 says — *"When all sibling slices under the parent are verified/closed, state: 'PR #<n> ready to merge (human)'."* That is an announcement, not a verification.

So the real shape is: each slice → implement → (user runs) `4a` verifies *that slice* and ships it into one accumulating feature PR → human merges once all sibling slices are in. `4b_audit-architecture-drift` is an optional structural pass after `4a`.

---

## 3. Findings (the learnings to carry forward)

- **F1 — the implement workflow has no slice-completion criterion.** It guarantees "tests pass," not "every AC is covered." Behaviors tested ≠ acceptance criteria covered (they aren't 1:1). The loop's stop point is implicit, so a slice can ship with an AC silently uncovered.
- **F2 — `4a` is slice-scoped and adjacent to the implement workflow.** The independent AC↔test audit already runs **per slice, as the very next step** after implementation. This is the decisive fact for §6: any *audit-style* check added inside the implement loop largely duplicates a check that runs moments later.
- **F3 — No integration-level verification exists.** Slices are verified in isolation; the composed feature is never checked against the whole PRD before merge. `3b_create-issue`'s Coverage Auditor checks that *slices cover the PRD at slicing time*; nothing checks that the *implementation satisfies the PRD at merge time*.
- **F4 — Isolation strength is a deliberate, ranked property.** Verification quality depends on who runs it: a **fresh session** (current `/4a`, never saw the code) > a **dispatched sub-agent** (some prompt contamination from the caller) > **inline self-grading** (full author bias). `4a`'s Context Isolation Rule exists precisely to stop the author grading their own homework.

---

## 4. Principles any solution must respect (do not re-derive or violate)

1. **Invocation model.** StratOS workflows install as `/` **commands** on both targets (Claude Code plugin commands; Antigravity copies them to `.agents/workflows/` and surfaces them as `/` commands — see `src/scripts/scaffold.py`). Commands are user-invoked by the channel, so **do not add `disable-model-invocation`** to a workflow, and a workflow cannot be "auto-invoked" mid-flow — only a *skill* (description-triggered, model-invocable) can be invoked inline by another workflow.
2. **`micro-tdd` (and any skill) must stay self-contained.** First-party skills register **globally** and can fire in projects never scaffolded by `stratosphere-setup`, so a skill must not hard-depend on a project-local file (`.agents/workflows/.reference/…` would be absent there). **Corollary:** if a new check is a *skill*, inline its rubric; if it is a *workflow*, it may safely point at a `src/references/` file (those are co-scaffolded with every workflow).
3. **Anchoring trap.** A pre-check must not **persist a verdict into the artifacts `4a` reads** (PR body, issue, comments). If it does, `4a`'s "fresh" auditor anchors on the prior verdict and its independence is lost. A pre-check fixes-or-flags **ephemerally**, within the loop.
4. **Side effects stay user-gated.** PR creation / pushing are irreversible-ish outward actions; they must remain in a user-invoked, HITL-gated step (today's `4a` Phase 5). Do not fold shipping into anything that auto-fires.
5. **Spend isolation where it matters.** Fresh-session `/4a` is the gold standard but costs a manual step; reserve the strongest isolation for high-risk surfaces (the existing Value-Add Gate already routes by risk).

---

## 5. Implementation mechanics (so you can act without hunting)

- **Edit `src/` only; never hand-edit `dist/`.** Build with `python build/build.py` (validated by `build/validate.py`); the build must be clean.
- Source map: workflows `src/workflows/<name>.md`; shared reference docs `src/references/<name>.md` → installed at `.agents/workflows/.reference/<name>.md` (scaffold globs the whole dir — new files are auto-included); memory templates `src/memory-templates/`.
- A workflow cites a reference by its **installed** path: `.agents/workflows/.reference/<name>.md`.
- **Branch, don't work on `main`.** Follow `AGENT.md` precedence and the constitution's ASK / no-silent-memory-rewrite rules.
- Coordinate with the implemented changes (from `docs/plans/mattpocock-learnings-implementation-instructions.md`): the implement workflow delegates its loop to `micro-tdd` — add Proposal 1 as a new *exit* phase, not inside the loop; `4a`'s confidence scale lives in `src/references/confidence-scale.md` — Proposal 2, if built as a workflow, can reuse it.

---

## 6. Considered and rejected (with reasons — settled, don't reopen)

- **Dissolve `4a` into the implement workflow (one continuous implement→verify→ship).** Rejected: breaks isolation (the author would grade its own code), and folds **PR side effects + the HITL gate** into the auto-flow, violating principles 3–4.
- **Turn `4a`'s audit into an auto-invoked skill called at the end of the implement loop.** Tempting (mirrors Matt's `implement → review` where review uses sub-agents), but: the *ship* half can't be a skill (side effects), and the *audit* half is redundant given F2. If ever pursued, the rubric must be inlined (principle 2) and the sub-agent dispatch made mandatory (since the implement session is always tainted) — but §F2 makes the payoff small.
- **Hybrid: keep `4a`, add a smaller sub-agent verify at the end of the implement loop.** Rejected as mostly token bloat: because `4a` runs the independent AC↔test audit **per slice immediately after** implementation (F2), a sub-agent audit inside the loop re-runs the adjacent check and risks the anchoring trap (principle 3). The non-redundant residue of this idea is Proposal 1 (a cheap *completion criterion*, not an audit).

---

## 7. Proposed changes

### Proposal 1 — Slice-completion gate in the implement workflow (recommended; low-risk; cheap)

**What.** Add a final exit criterion to the implement workflow (a new short phase, after the REFACTOR/loop, before "done"):

> **Completion gate.** Before declaring the slice done, confirm **every acceptance criterion in the slice issue maps to at least one passing test**. List each AC → covering test, or `[UNCOVERED]`. Any `[UNCOVERED]` → continue the TDD loop to cover it, or — if it can't be covered (design blocker) — surface it explicitly rather than shipping. This is a self-check performed **inline** (no sub-agent), and it **writes nothing into the PR/issue** (ephemeral; avoids anchoring `4a`).

**Why.**
- Closes F1 (premature completion) with a **checkable, exhaustive completion criterion** — the cheapest, most local defense (sharpen the bound before adding machinery).
- **Not a sub-agent**, precisely because of F2: the independent audit already runs next in `4a`. Duplicating it here would be bloat + anchoring risk. A self-check answers a *different* question ("did I, the author, finish?") than `4a`'s independent audit ("is it correct, bias-free?"), so the two compound rather than duplicate.
- Near-zero token cost (a checklist pass over AC the agent already has loaded), and it hands `4a` a cleaner input (fewer trivial gaps to wade through), improving `4a`'s signal.

**How.** Edit the implement workflow: add the gate as the workflow's final phase. Source the AC from the slice issue's "Acceptance Criteria (Verifiable)" section (Template B). Keep it ephemeral and inline. Build + validate.

**Risk.** Very low. The only failure mode is the gate being a no-op if the agent rubber-stamps it — mitigate by phrasing the criterion as exhaustive ("every AC, listed explicitly"), not vague ("looks complete").

### Proposal 2 — PRD-level integration verification before merge (optional; genuinely new)

**What.** A verification gate that runs **once, after all sibling slices under a parent `BT-<padded>` are verified/closed and before the human merges the feature PR**, checking that the *assembled* feature satisfies the **whole PRD** — the §6 journeys work end-to-end across slice seams, and no slice regressed another. Produces a PRD-level AC↔behavior report; HITL-gated; never auto-merges.

**Why.** Closes F3. Today's per-slice `4a` can pass every slice in isolation while the composed feature still fails at the seams between slices (state handed off between slices, ordering, integrated journeys). This check adds **new information** that no existing step provides — unlike a second per-slice check, which would be redundant (F2). It is the merge-time counterpart to `3b`'s slicing-time Coverage Auditor.

**Design questions to resolve in the new session (don't assume):**
- **Placement:** a new `4c` workflow? a "final-slice / integration" mode of `4a`? a step the human triggers at "ready to merge"? Prefer the option that keeps the per-slice flow unchanged and adds one gate at the parent-completion boundary.
- **Isolation:** fresh session (strongest, matches `4a` philosophy) vs. sub-agent. Given it runs at a natural break (all slices done), a fresh `/4c`-style session is cheap to justify.
- **Scope of the check:** PRD §6 journeys end-to-end + cross-slice seams + integrated regression run — not a re-audit of each slice's unit coverage (that's done).
- **Reuse:** if built as a workflow, it may point at `src/references/confidence-scale.md` (the extracted rubric) and read the PRD + frozen design doc.
- **Trigger condition:** only for multi-slice parents (a single-slice feature is already fully covered by its one `4a` run — skip to avoid bloat).

**Risk.** Medium (new surface, new tokens). Validate the need first: do you actually hit "slices passed individually but the feature doesn't hang together"? If slicing discipline (`3b` tracer-bullet vertical slices) is strong, the integration risk may be low enough to defer. Build only if the pain is real.

---

## 8. References

- Current source: the implement workflow, `src/workflows/4a_verify-and-ship.md`, `src/workflows/4b_audit-architecture-drift.md`, `src/workflows/3b_create-issue.md` (Coverage Auditor).
- Related work: `docs/plans/mattpocock-learnings-implementation-instructions.md` (the implement→`micro-tdd` delegation; confidence-scale + issue-templates references).
- Fuller analysis & rationale: `docs/plans/mattpocock-skills-v1-learnings-and-stratos-recommendations.md`.
- External inspiration: `github.com/mattpocock/skills` v1 — `implement` (delegates to `tdd` + `review`), `review` (sub-agent-based), and the user-invoked/model-invoked invocation model (`docs/invocation.md`). Key transferable principles: feedback latency ("the rate of feedback is your speed limit"), premature-completion defense (sharpen the completion criterion first), and side-effect skills stay user-invoked.

---

## 9. Recommended path

1. **Do Proposal 1** (slice-completion gate) — small, safe, closes the premature-completion hole, complements (not duplicates) `4a`.
2. **Hold Proposal 2** until you've confirmed the integration pain is real; then spec placement/isolation per §7 and build it as a single parent-completion gate.
