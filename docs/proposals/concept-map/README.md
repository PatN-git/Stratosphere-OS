---
type: proposal
name: concept-map-wayfinder-parity
description: Work copies implementing the 1c_concept-map optimization plan — Wayfinder parity plus a shared grilling-protocol extraction. Not applied to src/.
trigger: User. Do not run autonomously.
version: "1.0.0"
timestamp: 2026-07-30
---

# Proposal: `1c_concept-map` Wayfinder parity

**Status:** Work copies only. **Nothing under `src/` has been touched.** Apply by copying each `*.work.md` over its target below.
**Plan:** [`docs/plans/1c-optimization-plan.md`](../../plans/1c-optimization-plan.md) — items #1–#22 plus the shared-reference extraction.
**Sources:** `mattpocock/skills` `wayfinder/SKILL.md`, the `aihero.dev/skills-wayfinder` post, and the author's video walkthrough. Governed by `improve-workflows-skills`.

## Apply map

| Work copy | Target | Bump |
|---|---|---|
| `1c_concept-map.work.md` | `src/workflows/1c_concept-map.md` | 1.1.1 → **1.2.0** (behavior) |
| `concept-map-operations.work.md` | `src/references/concept-map-operations.md` | 1.0.1 → **1.1.0** (behavior) |
| `concept-map-template.work.md` | `src/references/concept-map-template.md` | 1.0.0 → **1.1.0** (behavior) |
| `discovery_brief_template.work.md` | `src/references/discovery_brief_template.md` | 1.0.4 → **1.1.0** (new section) |
| `grilling-protocol.work.md` | `src/references/grilling-protocol.md` (**new file**) | **1.0.0** |
| `1b_concept-framing.work.md` | `src/workflows/1b_concept-framing.md` | 1.1.0 → **1.2.0** (repoint only) |
| `agentic-test-plan.work.md` | not applied — test plan, stays in `docs/` | — |

After applying: `python build/build.py` then `python build/validate.py`. Never hand-edit `dist/` or `.agents/`.

## Plan item → where it landed

| Item | Landed in |
|---|---|
| #1 ticket body `## Question` + one-session sizing | `concept-map-operations` §2 |
| #2 load map low-res, orient to Destination, honour Notes, zoom-as-needed | `1c` Phase 2.1 |
| #3 fire research subagents in parallel at charting | `1c` Phase 1.5 + 2.7 |
| #4 `## Decision Trail` in the brief | `discovery_brief_template`, `1c` Phase 3.2 + gate 3.4 |
| #5 fog-or-ticket test | `1c` Phase 1.4, `concept-map-template` |
| #6 out-of-scope procedure (close + one line + not in Decisions) | `1c` Phase 2.6, `concept-map-operations` §6, template |
| #7 HITL/AFK per ticket type + never answer your own question | `1c` Phase 2.4 |
| #8 clear graduated fog patch; handle invalidation | `1c` Phase 2.6, `concept-map-operations` §7 |
| #9 re-read map before writing (concurrency) | `1c` Phase 2.6, `concept-map-operations` §5 |
| #10 refer by name | `1c` Invariants |
| #11 map body never lists open tickets (BT-LOCAL excepted) | `1c` Phase 1.3, `concept-map-operations` §1, template |
| #12 plan-don't-do invariant; decision ≠ implementation ticket | `1c` Invariants |
| #13 deterministic tie-break (lowest open issue number) | `1c` Phase 2.2, `concept-map-operations` §4 |
| #14 next-session invocation string; reuse `/0c_handoff` | `1c` Phase 2.7 |
| #15 `[<map>] [<ticket>]` args | `1c` Invocation + Phase 0.3 |
| #16 prefer prototype over grilling for look/behave | `1c` Phase 1.4 |
| #17 destination type + routed hand-off | `1c` Phase 1.1 + 3.7, template |
| #18 index-not-store | `1c` Invariants, template |
| #19 template section reorder (Decisions above fog) | `concept-map-template` |
| #20 abandon ramp | `1c` Phase 3.6 |
| #21 tracker-mode detection, held for session, recorded on map | `1c` Phase 0.2, `concept-map-operations` preflight, template |
| #22 upstream routing `> [!NOTE]` | `1c` header |
| extraction | `grilling-protocol.work.md`; `1b` + `1c` repointed |

## Deliberately not adopted

- **`research/<name>` throwaway branches** (in both upstream sources). AGENTS.md §4 makes `3d` the only branch creator and `4a` the only pusher; `1c` is a discovery workflow. The research subagent guardrail forbids branch creation outright. Findings stay in `docs/research/<map-slug>-<question-slug>.md`.
- **`disable-model-invocation`** — not used in this repo (playbook §1); a workflow is user-only by channel.
- **`wayfinder:*` labels** — StratOS uses `concept:*`, registered in `src/memory-templates/BACKLOG_MAP.md`.
- **Dropping the convergence phase** — Wayfinder ends at "the way is clear"; `1c` Phase 3 (brief + RAT + hard HITL gate + glossary) is the StratOS differentiator and is preserved verbatim.

## Prior art — no conflict

[`FEAT-discovery-pipeline-quality-fixes-proposal.md`](../FEAT-discovery-pipeline-quality-fixes-proposal.md) findings **F2** (glossary write needs the confirmation gate) and **F3** (Converge needs a self-review + user gate) already landed in `1c` v1.1.1. This change set preserves both verbatim and is additive to them.

## Verification status

- Verifiable now: frontmatter shape, pointer paths resolve, plan-item coverage, internal consistency.
- **Unverified:** no end-to-end run. Exercising this needs `gh` authenticated against a live tracker plus a human for the HITL gates. See [`agentic-test-plan.work.md`](agentic-test-plan.work.md).
- `build/validate.py` does not cover `docs/` — it only sees these files once they are applied to `src/`.
