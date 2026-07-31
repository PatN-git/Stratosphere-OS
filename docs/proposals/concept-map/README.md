---
type: proposal
name: concept-map-wayfinder-parity
description: Work copies implementing the 1c_concept-map optimization plan — Wayfinder parity plus a shared grilling-protocol extraction. Not applied to src/.
trigger: User. Do not run autonomously.
version: "1.1.0"
timestamp: 2026-07-30
---

# Proposal: `1c_concept-map` Wayfinder parity

**Status:** Work copies only. **Nothing under `src/` has been touched.** Apply by copying each `*.work.md` over its target below.
**Plan:** [`docs/plans/1c-optimization-plan.md`](../../plans/1c-optimization-plan.md) — items #1–#22 plus the shared-reference extraction.
**Sources:** `mattpocock/skills` `wayfinder/SKILL.md`, the `aihero.dev/skills-wayfinder` post, and the author's video walkthrough. Governed by `improve-workflows-skills`.

## Apply map

| Work copy | Target | Bump |
|---|---|---|
| `1c_concept-map.work.md` | `src/workflows/1c_concept-map.md` | 1.1.1 → **1.3.0** (behavior) |
| `concept-map-operations.work.md` | `src/references/concept-map-operations.md` | 1.0.1 → **1.1.0** (behavior) |
| `concept-map-template.work.md` | `src/references/concept-map-template.md` | 1.0.0 → **1.1.0** (behavior) |
| `discovery_brief_template.work.md` | `src/references/discovery_brief_template.md` | 1.0.4 → **1.1.0** (new section) |
| `grilling-protocol.work.md` | `src/references/grilling-protocol.md` (**new file**) | **1.0.0** |
| `1b_concept-framing.work.md` | `src/workflows/1b_concept-framing.md` | 1.1.0 → **1.2.0** (repoint only) |
| `AGENTS.work.md` | `AGENTS.md` (**constitution**) | 1.0.4 → **1.1.0** (§1 bounded-AFK clause, §6 standing authorization) |
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
| Phase 0 read the map's `Tracker mode` at step 2, before the map was discovered (step 3) or selected (step 4) | first split into its own step; then **moot** — the field is gone with the offline fallback (below) |
| research guardrail replaced by "same contract as Phase 1" cross-reference | restated verbatim at both dispatch sites — a subagent never sees surrounding prose |
| RAT dispatch missing dual-host phrasing, Input, and Output | brought to the repo standard, guardrail text unchanged |
| `/0c_handoff` invoked autonomously — AGENTS.md §1 does not sanction it | offered to the user, who invokes it |
| "credential location" written into an issue comment | env-var name only, never the value or file path |
| `<ticket>` "skips frontier selection" contradicted Phase 2.2 | header says "preselects"; `<map>` now explicitly jumps to Phase 2 |
| one-ticket invariant contradicted by Phase 2.7's unbounded batching | invariant is one dependency step, `research` excepted; batching removed |
| six rules duplicated between `1c` and the operations reference | `1c` points; the reference owns them |
| brief template asserted the tickets are "the source of truth", contradicting `2a:43` | softened to a capability — links are the primary source to zoom when a gist is not enough |

Also fixed from the test plan's findings: fog past the destination now has a retirement path (so convergence is reachable) and claims are released on an unresolved halt (so a ticket cannot be stranded off-frontier). Two further findings — the BT-LOCAL frontier predicate working by luck, and BT-LOCAL's advisory claims — were **dissolved** rather than fixed by cutting the fallback (below).

Two known non-blockers, deliberately not fixed here: `type: reference` / `type: concept-map` are absent from the OKF Type Registry, and `concept-map-template.md` carries `status:` in frontmatter against `okf-protocol.md`. Both are pre-existing repo-wide drift; fixing them belongs in a registry-alignment change, not this one.

## Plan item → where it landed

| Item | Landed in |
|---|---|
| #1 ticket body `## Question` + one-session sizing | `concept-map-operations` §2 |
| #2 load map low-res, orient to Destination, honour Notes, zoom-as-needed | `1c` Phase 2.1 |
| #3 research subagents in parallel, no waiting | `1c` Phase 2A.4 (moved there from Phase 1.5 by A3) |
| #4 `## Decision Trail` in the brief | `discovery_brief_template`, `1c` Phase 3.2 + gate 3.4 |
| #5 fog-or-ticket test | `1c` Phase 1.4, `concept-map-template` |
| #6 out-of-scope procedure (close + one line + not in Decisions) | `1c` Phase 2.6, `concept-map-operations` §6, template |
| #7 HITL/AFK split + never answer your own question | `1c` Invariants + Phase 1.4 labels + Phase 2A.4 (A1 made it a label) |
| #8 clear graduated fog patch; handle invalidation | `1c` Phase 2.6, `concept-map-operations` §7 |
| #9 re-read map before writing (concurrency) | `1c` Phase 2.6 + 2A.7, `concept-map-operations` §5 |
| #10 refer by name | `1c` Invariants |
| #11 map body never lists open tickets (no exception — fallback cut) | `1c` Phase 1.3, `concept-map-operations` §1, template |
| #12 plan-don't-do invariant; decision ≠ implementation ticket | `1c` Invariants |
| #13 deterministic tie-break (lowest open issue number) | `1c` Phase 2.2, `concept-map-operations` §4 |
| #14 next-session invocation string; offer `/0c_handoff` | `1c` Phase 2.7 |
| #15 `[<map>] [<ticket>]` args (+ `--drain`, A5) | `1c` Invocation + Phase 0.3 |
| #16 prefer prototype over grilling for look/behave | `1c` Phase 1.4 |
| #17 destination type + routed hand-off | `1c` Phase 1.1 + 3.7, template |
| #18 index-not-store | `1c` Invariants, template |
| #19 template section reorder (Decisions above fog) | `concept-map-template` |
| #20 abandon ramp | `1c` Phase 3.6 |
| #21 tracker preflight — halt without an authenticated `gh` (see *Offline support cut*) | `1c` Phase 0.2, `concept-map-operations` preflight |
| #22 upstream routing `> [!NOTE]` | `1c` header |
| extraction | `grilling-protocol.work.md`; `1b` + `1c` repointed |

## AFK posture (A1–A6)

Second pass, driven by StratOS's shift toward AFK workflows and agent-invoked workflows (`3z_afk-loop`, `x_jules-dispatch`). `1c` goes to **1.3.0**.

Governing idea: **AFK does not replace HITL tickets, it front-loads them.** Every HITL ticket has an AFK half — a `grilling` ticket's G2 facts and G1 recommendation, a `prototype` ticket's build — and draining that half means a human session opens on decisions only, never on legwork.

| | Change | Where |
|---|---|---|
| **A1** | Execution mode is a **label**, not prose: every ticket carries `mode:AFK` or `mode:HITL`, set per ticket and **never inferred from type** (`task` is genuinely either). An unlabelled ticket is never drained. This is what makes the frontier machine-partitionable, the same way `BACKLOG_MAP` is for `3z`. | `1c` Phase 1.4 + 2.6; ops §2, §4a; template |
| **A2** | **Attention, not context, is the bound.** One `mode:HITL` ticket per session; the AFK sub-frontier drains in parallel to exhaustion. This *reverses* the one-ticket-per-session rule adopted from Wayfinder two versions ago — that bound was about context economy in a human-attended session, which is not this system's constraint. | `1c` Invariants, Phase 2.7 |
| **A3** | New **Phase 2A: AFK Drain** — partition frontier → authorize once → drain in parallel → recompute → repeat until the frontier is human-only. Shaped after `3z` Step 1B: one gate up front, autonomous execution after, a report at the end. | `1c` Phase 2A |
| **A4** | **Terminal states + bounded attempts + demotion.** Exhaustive per-ticket states (`resolved` / `prepped` / `blocked-needs-human` / `out-of-scope`), max 3 attempts, and exhaustion **demotes** to `mode:HITL` instead of retrying or dropping. Fixes a real hang in the previous draft, which had no failure handling for a research subagent returning garbage. | `1c` Phase 2A.4–5 |
| **A5** | **Bounded AFK surface** `--drain` (Phase 0 + 2A only), callable without a user by a **scheduled routine**. Same shape as `x_jules-dispatch`: thin, bounded, guardrails restated at the boundary. `1c` stays `type: workflow HITL`, matching `3z`, which is `workflow AFK` yet carries a HITL gate — `type` tracks dominant posture, not purity. | `1c` Invocation; `AGENTS` §1 |
| **A6** | **Serialize map writes** — one write after the whole batch, not per ticket; parallel passes would race. | `1c` Phase 2A.6 |

### What hardened rather than softened

Autonomy makes two rules load-bearing that were previously only stylistic:

- **An AFK pass may prepare a `mode:HITL` ticket; it may never resolve or close one.** Direct analogue of `3z:15` ("never autonomously execute non-`mode:AFK` slices"). Without it, the agent answering its own grilling question stops being a bug and becomes the default path — and the map degenerates into a hallucinated spec.
- **Phase 3's convergence gate stays a hard HITL stop.** AFK may draft the brief and run the RAT; it may not pass the gate or close the map. This is what the prior proposal's F3 fixed — `--drain` stops at Phase 3 step 1 and reports the map is ready to converge.

### Constitution change — needs explicit approval

`AGENTS.work.md` amends the **constitution**, the top of the precedence order, so it carries more risk than the rest of this set:

- **§1** previously sanctioned exactly one form of workflow-invoking-workflow (a user-invoked orchestrator). It now sanctions a second — a **bounded AFK surface** — behind five conditions that all must hold: `mode:AFK`-only; never resolves/closes/approves `mode:HITL` work; never passes a hard HITL gate, writes `.memory/` content, or merges; every unit reaches a stated terminal state with bounded attempts and demotion on exhaustion; guardrails restated at the boundary. Unlabelled work is never AFK-eligible.
- **§6** gains **standing authorization** — durable consent scoped to one artifact (a map's `AFK drain: authorized`), which explicitly cannot license resolving `mode:HITL` work, passing a hard gate, or merging.
A1–A4 and A6 need none of this — they sit inside `1c`'s own authorized run. If you reject the constitution change, drop `AGENTS.work.md` and the `--drain` flag; Phase 2A still works, just user-invoked only.

**`3z` is deliberately not touched.** An earlier draft of this set amended `3z:13` to let it call `--drain`. That was wrong twice over: `3z` is post-spec execution (`3d` + `4a`) and `1c` is pre-spec discovery, so they sit on opposite sides of the spec boundary — and more concretely, `3z` builds its queue from `BACKLOG_MAP` slices, while concept child tickets are deliberately not rowed there, so `3z` could never *discover* a drainable map. The permission would have been decorative, and dead permission in a near-constitutional file is worse than none: a future agent reads it as evidence a hook exists. The intended caller of `--drain` is a **scheduled routine**; §1's clause is written for any authorized caller, so nothing in `3z` needs to change.

## Offline support cut

The previous draft carried a `BT-LOCAL` fallback: a parallel markdown tracker for when `gh` is unreachable. It is **removed**. `1c` now requires an authenticated `gh` and halts otherwise.

Reasoning: the fallback's premise was being offline, but an agent that cannot reach GitHub cannot reach its own model either — the state it defended against is one where no workflow runs at all. What remains is `gh` merely being absent or unauthenticated, and that is better answered by a preflight halt with guidance than by a second implementation of the tracker.

The cost of keeping it was disproportionate here. Elsewhere (`2a`, `3b`) `BT-LOCAL` is one placeholder id string. In `1c` it was a whole parallel tracker — tickets, blocking edges, claims, statuses, questions, resolutions, plus a frontier query implemented by parsing a markdown table. It also could not deliver the artifact's actual value: a shared URL and the tracker's native blocking, which renders the frontier visually without opening the map.

What this dissolved rather than fixed:

- The **undefined `## Tickets` schema** — six fields referenced across three files, defined nowhere, and load-bearing because both the frontier query and A1's mode partition parsed it. Gone with the fallback.
- The **split-brain hazard** (map charted in one mode, worked in the other) and the `Tracker mode` field that existed only to prevent it. Gone.
- **Advisory claims** — a file-based claim could not enforce mutual exclusion. Claims are now always remote-arbitrated, so a double-resolve is a bug rather than an accepted limitation.
- **Out-of-scope leaving the frontier by luck** of a `status == open` predicate. An out-of-scope ticket is now simply a closed issue.

Net effect on the set: `concept-map-operations` roughly halves, `1c` Phase 0 loses a step, and the test plan drops two scenarios (SC-06 retired, SC-04 inverted into a preflight-halt assertion) while gaining a stronger one — SC-04 now fails if the agent *reinvents* a local fallback. `2a` and `3b` keep their `BT-LOCAL-<n>` id placeholders; those are a different and much smaller mechanism, and are out of scope here.

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
