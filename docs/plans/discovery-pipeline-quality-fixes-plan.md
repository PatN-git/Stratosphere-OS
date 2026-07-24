# Plan — Discovery→Design pipeline quality fixes (tracker)

**Status:** Scoped + decisions locked (2026-07-24). Awaiting review — **no implementation yet**.
**Target:** Branch `claude/v3-polish-discovery-pipeline-kn3h6l` (base `main`), v3.0.x line. **One PR, all items** (D5).
**Source of truth:** [`docs/proposals/FEAT-discovery-pipeline-quality-fixes-proposal.md`](../proposals/FEAT-discovery-pipeline-quality-fixes-proposal.md) (v1.1.0) for the *why/evidence*. This file is the *tracker* — state, decisions, and the two designs (Q2 rewrite, Q4 adaptive grill) that were settled after the proposal was written.

> **Decisions locked:** D1 `1c` = hard HITL stop like `1b`. · D2 `1b` stop-conditions = **full rewrite** (all 4 fixes). · D3 Q4 = **frontier-batched grilling with inference-collapse** (dependency-driven, no structural tier — §2.1). · D4 = **no** `2a` spec reframe; coverage sufficient once Q1 lands (§2.2). · D5 = one PR + OKF version bumps. · D6 = ship via `improve-workflows-skills` → edit `src/` → rebuild `dist/` → `/4a`.
>
> Line numbers drift — re-anchor every edit by content.

---

## 1. Work items — status (all in one PR)

Ordered lowest-risk-first. All items are now unblocked.

| # | Item | File(s) | Sev | Status |
|---|------|---------|-----|--------|
| F4 | `[MEDIUM]` → `[MED]` tag | `1a` | P3 | ☐ ready |
| F5 | add `Est. setup time` to brief template | `discovery_brief_template.md` (+`1b` if contract touched) | P3 | ☐ ready |
| F1 | freshness gate `updated:` → `timestamp:` | `1b:73` | **P1** | ☐ ready |
| F2 | `1c` glossary write needs confirmation gate | `1c:74` | P2 | ☐ ready |
| F3 | `1c` Converge self-review + user gate (**hard HITL stop, mirror `1b` Phase 6**) | `1c:68–76` | P2 | ☐ ready (D1) |
| Q3 | `1b`→`2a` handover fidelity (4 fixes) | `2a` (+`1b`/brief link) | — | ☐ ready |
| Q2 | `1b` grill stop-conditions — **full rewrite** (all 4 fixes) | `1b` | — | ☐ ready (D2) |
| Q4 | frontier-batched grill + inference-collapse (dependency-driven) | `1b` | — | ☐ ready (D3, §2.1) |
| Q1 | `2b` full-stack path coverage (additive Interface Contract) | `2b` (+readers `3b`/`3d`/`4a`) | — | ☐ ready — **do last** (blast radius) |

**Implementation order within the PR:** F4 → F5 → F1 → F2 → F3 → Q3 → **Q2 → Q4** (Q2 before Q4 so the batch stop-condition lands on the confirmation gate, not the coverage checkboxes) → Q1 last.

**OKF version bump (once per PR, per touched file):** `1a`, `1b`, `1c`, `2a`, `2b`, `discovery_brief_template.md`. Then rebuild `dist/`.

---

## 2. Settled designs (post-proposal)

### 2.1 Q4 — frontier-batched grilling with inference-collapse (D3, revised after review)

**Design correction (2026-07-24 review):** the earlier "structural tier = always one-by-one" rule is **dropped**. It was *stricter* than Matt Pocock's own `batch-grill-me`, which is **purely frontier-based with no categorical exception** (*"a question whose answer depends on another still open in this round belongs to a later round"*). The objection that stands: for brownfield, actor/problem/framing are usually obvious, so forcing them one-at-a-time buys nothing. Community grill-me clones (RobMitt, coderocketai, …) add nothing here — all one-at-a-time copies of his stable skill. So the design follows Matt's frontier model, not a category rule.

**The rule — dependency-driven, not category-driven:**
1. **Facts are never asked (inference-collapse).** Anything discoverable — actor on a brownfield app, existing patterns, constraints in code — is looked up (or sub-agent-dispatched *in parallel, non-blocking*), so it never becomes a question. Matt's rule verbatim: *"Finding facts is your job, never the user's."* This is what makes the brownfield "obvious" case disappear from the queue entirely.
2. **A question serializes only on a genuine dependency edge**, never because it is "structural." Each round asks the whole **frontier** = every open *decision* whose prerequisites are settled, numbered, each with a recommended answer (G1). A question waits only if its answer depends on a sibling still open this round.
3. **Obvious decisions collapse to a batch-confirm.** Where the agent can confidently infer an answer (common brownfield), it pre-fills the recommended answer and presents actor/problem/framing as *one confirmation* — *"here's what I inferred; correct any that are wrong"* — not N serial questions.
4. Collect answers → mark settled on the `## Coverage` checklist → recompute frontier → next round. **Done** when the frontier is empty **and** the user confirms shared understanding (the Q2 gate).

**Why this is reliable *and* addresses the brownfield objection:**
- Ordering falls out of dependency edges + fact-lookup, not a "is this complex?" judgment — "does B depend on A" is more objective than a category call, and "settled" is anchored to the Coverage checklist (`1b:46`), the frontier substrate StratOS already has (`1c:46,64`).
- **Greenfield** self-serializes: structural answers are *uncertain*, so they gate later questions and land first. **Brownfield** self-collapses: structural answers are *known* → inferred + batch-confirmed. Same rule, both behaviors — no special case.
- Facts-vs-decisions (G2) already exists in `1b`; this leans on it harder (parallel sub-agent dispatch, non-blocking) rather than adding new machinery.

**Named risks + mitigations:**
- *Over-batching genuinely dependent questions* → the frontier rule itself prevents it (dependent question waits for its prerequisite).
- *Wrong inference presented as fact* → inference-collapse presents inferred answers for **confirmation**, never silently assumes them; the Q2 confirmation gate is the backstop before the brief is written.
- *Scope:* default for the generate/longer path (work file present = frontier substrate); the sharpen/short path has too few decisions to batch and stays conversational. Not gated behind a flag.

### 2.2 D4 — does `2a` PRD + `2b` design doc cover enough to implement? (**yes, once Q1 lands**)

Mapping StratOS artifacts against Pocock's `to-spec` sections and against what `3d` needs:

| `to-spec` section | StratOS home | Verdict |
|---|---|---|
| Problem Statement | PRD §1 | ✅ |
| Solution (user view) | PRD §2 | ✅ |
| User Stories | PRD §6 (scope tags + ODI, journey-mapped) | ✅ richer |
| Implementation Decisions (modules/API/schema/architecture) | `2b` design doc — Surface & Scope, Actors & Core Flows, **Path C Interface Contract** | ⚠ **gap = Q1**: Interface Contract is emitted for non-UI only; full-stack *UI* slices get the layout blueprint but no API/schema contract → `3d` improvises. |
| Testing Decisions | `2b` "Handoff Notes for 3c/4a" + `3c` sprint-planning + `micro-tdd` (RED) | ✅ process-covered (no dedicated artifact section; weakest-covered area) |
| Out of Scope | PRD §4 (principled) + §9 (temporal) | ✅ richer |
| Further Notes | PRD §11 | ✅ |

Plus StratOS adds §3 Goals, §5 Success Signals, §7 Constraints+ADR, §8 Definition of Done, §10 Open Questions, §12 Viability & Cost, and `2b` Aha-Moment / Direction-Alternatives / Stress-Matrix — a **superset** of `to-spec`.

**Conclusion:** Coverage is sufficient for implementation **once Q1 closes the Interface-Contract gap for full-stack UI slices.** That reframes Q1 from "nice full-stack fix" to **the load-bearing coverage fix** — it is what makes the artifact set implementation-complete. No spec reframe (D4 = no).

**Optional, low-priority (not a work item):** the `2b` "Handoff Notes for 3c/4a" section is freeform; it *could* explicitly name test targets (Pocock's "Testing Decisions"). Deferred — `micro-tdd` + `3c` already cover it procedurally; revisit only if under-tested slices are observed.

---

## 3. Decision log (resolved 2026-07-24)

| # | Decision | Outcome |
|---|----------|---------|
| D1 | `1c` convergence gate | **Hard HITL stop**, mirror `1b` Phase 6 self-review + approval before closing the map. (F3 ready.) |
| D2 | `1b` stop-conditions scope | **Full rewrite** — all 4 fixes (confirmation gate primary; delete stop-cond-2; reframe 5-Q check-in to direction-check; state "no fixed budget, 20–50 Q" norm). |
| D3 | Batched grill | **Yes, reliably — via Matt's pure-frontier model, not a structural tier** (that earlier idea dropped as too rigid on review). Dependency-driven rounds + inference-collapse: facts looked up (never asked), obvious brownfield decisions batch-confirmed, genuine dependencies serialize themselves. Default for generate/longer path. (§2.1) |
| D4 | Spec reframe / coverage | **No reframe.** Coverage sufficient once Q1 lands; Q1 is the load-bearing coverage fix. (§2.2) |
| D5 | Packaging | **One PR**, all items, OKF version bumps per touched file. |
| D6 | Ship path | Confirmed: `improve-workflows-skills` → edit `src/` (never `dist/`/`.agents/`) → rebuild `dist/` → `/4a_verify-and-ship`. |

---

## 4. Sources (benchmark research)

- [The /grilling Skill](https://www.aihero.dev/skills-grilling) · [grilling/SKILL.md](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)
- [batch-grill-me (in-progress)](https://github.com/mattpocock/skills/tree/main/skills/in-progress/batch-grill-me)
- [The /to-spec Skill](https://www.aihero.dev/skills-to-spec) · [to-spec/SKILL.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md)
- [v1.1.0 CHANGELOG](https://github.com/mattpocock/skills/blob/main/CHANGELOG.md) · [Release v1.1.0](https://github.com/mattpocock/skills/releases/tag/v1.1.0)
- [/wayfinder](https://www.aihero.dev/skills-wayfinder) (the map layer) · [Pocock on wayfinder + central map](https://x.com/mattpocockuk/status/2072716979195326905)
- Community grill-me clones surveyed (all one-at-a-time, no batching innovation): [RobMitt/grill-me-skill](https://github.com/RobMitt/grill-me-skill) · [coderocketai/claude-skills](https://github.com/coderocketai/claude-skills/blob/main/grill-me/SKILL.md)
