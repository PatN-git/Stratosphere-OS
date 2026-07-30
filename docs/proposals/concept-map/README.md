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

### Apply-time gates (all four are mandatory)

1. **Apply `grilling-protocol.md` in the same commit as the `1b`/`1c` repoints.** `build/validate.py` hard-fails on a `.agents/workflows/.reference/` pointer whose target is missing, so splitting them breaks the build.
2. `python build/build.py`, then confirm `python build/validate.py` green. Never hand-edit `dist/` or `.agents/`.
3. **Bump the plugin `VERSION`** (`python scripts/release.py`). `build/bump_guard.py` fails CI when `dist/*/versions.json` moves without it, and six shipped artifacts change here.
4. **Register `1c`'s guardrails in `tests/test_subagent_spawning.py`.** `1c` is absent from its `WORKFLOWS` map while `1a`, `1b`, `2b`, `3a`, `3b`, `4a`, `4b` are all locked there; repo convention is that each dispatch guardrail string is test-asserted:
   ```python
   "src/workflows/1c_concept-map.md": [
       "Fire research subagents",
       "Do not create branches, commit, or push. Report the findings path + gist.",
       "Report findings only; do not edit files.",
   ],
   ```

## Review outcome

Reviewed against the plan by an independent subagent. Verdict: **46/100 safe to apply as first drafted; 88/100 with the blockers fixed.** All five blockers plus every worthwhile warning are now fixed in these work copies:

| Was | Fix |
|---|---|
| `status:dropped` invented — absent from the `BACKLOG_MAP.md` Label Registry, and `3b` forbids inventing labels | abandon ramp closes with the reason, sets Status `done`, notes `abandoned: <why>` on the row |
| `in-place-change` → "the change itself" — a discovery workflow editing code on an ungated branch, likely `main` | routes `/3b_create-issue` Template B → `/3d_implement-issue`; the no-code-edit rule is now in the Invariants |
| `/1a_research` Phase 1 inline deleted — left the research subagent with no scope and stranded an unsatisfiable HITL gate inside an isolated context | parent derives Phase 1 (topic, slug, questions, domain, depth) and passes it in; subagent runs Phase 2 only |
| bare-basename pointers in `1c` and the map template | full `.agents/workflows/.reference/…` paths (12 in `1c`); the template's matters most — its body is pasted into an issue and read with no repo context |
| Phase 0 read the map's `Tracker mode` at step 2, before the map was discovered (step 3) or selected (step 4) | detection at step 2, adopt-recorded-mode split into its own step 5 |
| research guardrail replaced by "same contract as Phase 1" cross-reference | restated verbatim at both dispatch sites — a subagent never sees surrounding prose |
| RAT dispatch missing dual-host phrasing, Input, and Output | brought to the repo standard, guardrail text unchanged |
| `/0c_handoff` invoked autonomously — AGENTS.md §1 reserves that for `3z` | offered to the user, who invokes it |
| "credential location" written into an issue comment | env-var name only, never the value or file path |
| `<ticket>` "skips frontier selection" contradicted Phase 2.2 | header says "preselects"; `<map>` now explicitly jumps to Phase 2 |
| one-ticket invariant contradicted by Phase 2.7's unbounded batching | invariant is one dependency step, `research` excepted; batching removed |
| six rules duplicated between `1c` and the operations reference | `1c` points; the reference owns them |
| brief template asserted the tickets are "the source of truth", contradicting `2a:43` | softened to a capability — links are the primary source to zoom when a gist is not enough |

Also fixed from the test plan's findings: fog past the destination now has a retirement path (so convergence is reachable), claims are released on an unresolved halt (so a ticket cannot be stranded off-frontier), the BT-LOCAL frontier predicate is stated as a rule rather than working by luck, and BT-LOCAL's advisory-claim limitation is documented.

Two known non-blockers, deliberately not fixed here: `type: reference` / `type: concept-map` are absent from the OKF Type Registry, and `concept-map-template.md` carries `status:` in frontmatter against `okf-protocol.md`. Both are pre-existing repo-wide drift; fixing them belongs in a registry-alignment change, not this one.

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
