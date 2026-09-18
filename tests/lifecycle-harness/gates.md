# L3 gate inventory

Every HALT / ASK / confirm point a driven phase can reach, and the answer the responder
gives it. Checked in so that "every gate has an answer" is **falsifiable** — an unmatched
question fails the run by name (E6), and the fix lands here.

Derived from the skill sources, not from memory. A run that discovers a gate missing from
this file has found a documentation defect as well as a harness one: record both (Slice 9).

Answer sources:
- `policy:pick-first` — deterministic, always option 1
- `policy:ice` — deterministic, fixed ICE values
- `policy:confirm` — deterministic, "Yes, proceed."
- `policy:budget` — the harness's stopping policy (`responder.STOP`)
- `proxy` — the isolated User Proxy, answering from `fixture/topic.md`

---

## `1b-concept-framing` — driven by Slice 0

| # | Gate | Source | Answer |
|:--|:---|:---|:---|
| 1b-G0 | Phase 0 Brainstorm Gate — concrete concept vs. vague | `1b:28-29` | Not a question to the user; the fixture's ask is concrete, so Phase 0 self-routes to Phase 1. If it does ask, `proxy` states the ask verbatim. |
| 1b-G1 | Phase 2 grill — open-ended then narrowing questions, **20–50, unbounded by design** | `1b:52,68` | `proxy` per question, then `policy:budget` at the cap. See the note below. |
| 1b-G2 | Phase 2 stop condition — "restate actor, problem, framing and they confirm" | `1b:64` | `policy:confirm`, or `policy:budget` if the cap arrives first. |
| 1b-G3 | Phase 3 — "these terms look cross-PRD reusable. Promote to GLOSSARY?" | `1b:96` | `policy:confirm` → yes. The fixture pins the vocabulary and its `Avoid:` list so `[[G-001]]` is deterministic. |
| 1b-G4 | Phase 4 — "propose 2–3 distinct problem framings; user picks one" | `1b:101-102` | `policy:pick-first` → 1. Rejected framings still get recorded, which is what the assertion checks. |
| 1b-G5 | Phase 4.5 RAT — runs by default, user may decline | `1b:106` | `policy:confirm` → do not decline. The fixture pins the riskiest assumption and its cheapest test. |
| 1b-G6 | Phase 4.5 — "propose fastest test, must not exceed 2 weeks" | `1b:109` | `proxy` → "N DMs", under one week, from the fixture. |
| 1b-G7 | Phase 6 Self-Review + User Gate | `1b:124` | `policy:confirm` → yes. |
| 1b-G8 | Phase 7 — propose `[[L-xxx]]` for LEARNINGS if the framing decision is reusable | `1b:140` | `policy:confirm` → yes. |

**On 1b-G1.** `1b`'s grill is deliberately unbounded and the *user* ends it, because agents
stop too early and an agent that decides it has asked enough is grading its own work. That
design is correct and unchanged. The cap here is the **harness's own stopping policy**,
exercised through the responder standing in for the user — it is not a change to the skill,
and `1b` never learns a budget exists.

---

## `0a-start-session` — greenfield and post-backlog

| # | Gate | Source | Answer |
|:--|:---|:---|:---|
| 0a-G1 | `Session Status: no-active-task` → next-step guidance, then **HALT before any side effect** | `0a:23` | No question is asked. The greenfield run's assertion is that nothing happened: STATUS.md unchanged, **no branch created** (`0a:24`). |
| 0a-G2 | An active task is resolved → restore it | `0a:26` | No question. The second run asserts STATUS.md updated and the existing branch checked out. `0a` never creates one. |

---

## `1a-research`

| # | Gate | Source | Answer |
|:--|:---|:---|:---|
| 1a-G1 | Propose-and-Confirm: domain + depth | `1a:35-39` | `policy:confirm`. The prompt pins **Quick Search** in the opening turn, so the proposal should match and the confirmation is a yes rather than a correction. |
| 1a-G2 | Deep mode presents a `## Plan` checklist for approval | `1a:38` | Not reached under Quick Search (`1a:46`, "Skip Phase 2"). If it IS reached, the run has found that the depth pin did not hold — record it (Slice 9) rather than answering. |

The refutation subagent (`1a:78`) is Phase 2 only, so it does not run here (fact 9).

---

## `2a-write-prd`

| # | Gate | Source | Answer |
|:--|:---|:---|:---|
| 2a-G1 | Scope tags unbacked by research → propose for confirmation | `2a:56` | `policy:confirm`. `1a` ran, so this should not fire; if it does, the hand-off is thinner than the chain assumes. |
| 2a-G2 | **Cost Approval Gate** — ongoing costs must be approved before locking the PRD | `2a:61` | `policy:confirm`. The fixture is deliberately a per-MAU pricing landscape so this gate genuinely fires instead of collapsing to `[Unknown]`. |
| 2a-G3 | §7 ADR flag — propose `[[A-xxx]]`/`[[L-xxx]]` for structural decisions | `2a:67` | `policy:confirm` → yes. |

---

## `2b-interface-design`

| # | Gate | Source | Answer |
|:--|:---|:---|:---|
| 2b-G1 | Phase 1 Surface & Scope Gate — no external surface → skip the design doc entirely | `2b:22,26` | No answer: the fixture HAS a surface (an evaluation function plus a ruleset schema), so the gate must route to Path C, not skip. A skip here fails the phase assertion. |
| 2b-G2 | Phase 2.5 HITL Pick among 3 generated directions | `2b:43-50` | `policy:pick-first` → 1. The rejected directions are still recorded under `## Direction Alternatives (Considered)`, which is what the assertion checks. |
| 2b-G3 | Immortal Component registration | `2b:71,79,96` | `policy:confirm`. Path C has no shell to register, so this should not fire. |
| 2b-G4 | Token direction / DESIGN.md seeding | `2b:95` | Not reached on Path C. If it fires, the non-UI path is leaking UI steps — a `stratos` finding. |

---

## `3b-create-issue`

| # | Gate | Source | Answer |
|:--|:---|:---|:---|
| 3b-G1 | Phase 2.2 ICE — Impact, Confidence, Effort per slice | `3b:61-65` | `policy:ice` → Impact 1.0, Confidence 80%, `size:small`, `mode:AFK`, fixed for every slice so the run does not vary on priority bucketing. |
| 3b-G2 | **Approval Request** — audited drafts + coverage map, "Halt until user approves" | `3b:58` | `policy:confirm` → yes. This is the one hard halt in `3b`. |
| 3b-G3 | `[UNCOVERED]` resolution — add slice / defer / confirm out of scope | `3b:56-57` | `policy:confirm`. A `[RESEARCH-GAP]` or **spec defect** routed to `/2c-reconcile-specs` is NOT answerable by policy: it is a finding, and the run records it. |
| 3b-G4 | Missing label → propose adding to the registry, await confirmation | `3b:76` | `policy:confirm` → yes. |
| 3b-G5 | Phase 3.5 terminal sync — non-zero → heal and re-run, **at most 3 attempts** | `3b:70` | Not a user gate. Bounded at the source since D3; the harness caps heal attempts as well (Slice 5) and fails by name rather than spinning. |

---

## `3d-implement-issue`

| # | Gate | Source | Answer |
|:--|:---|:---|:---|
| 3d-G1 | HITL slices show RED/GREEN test results | `3d:31` | Not a question. `policy:ice` pins `mode:AFK`, so this should not fire. |
| 3d-G2 | Avoid-drift check → propose renames at the REFACTOR/HITL gate, never auto-rename | `3d:42` | `policy:confirm` → yes. `1b` pins an `Avoid:` list, so this can genuinely fire. |
| 3d-G3 | Phase 3 Slice Completion Gate — confirm the slice against its AC | `3d:44-45` | `policy:confirm` → yes. Ephemeral, writes nothing. |

---

## `4a-verify-and-ship` — `audit-only` only

| # | Gate | Source | Answer |
|:--|:---|:---|:---|
| 4a-G1 | Phase 1 Value-Add Gate — cosmetic / high-risk / neither | `4a:22-26` | Not a user question; `4a` routes on the slice itself. |
| 4a-G2 | Phase 4 gap report — "Halt. Await human approval." | `4a:61` | `policy:confirm` → yes, authorising the report. Reaching it means the audit found gaps, which is a finding either way. |
| 4a-G3 | Phase 5.3 ship confirmation | `4a:72` | **Never reached** — L3 stops at `audit-only` (facts 7, 12). If the run reaches it, the gate name did not hold and the run must fail rather than answer. |

---

## `0b-stop-session`

| # | Gate | Source | Answer |
|:--|:---|:---|:---|
| 0b-G1 | Parent epic `done` confirmation when every sibling is closed | `0b:26` | `policy:confirm`. Nothing merges in an L3 run, so this should not fire. |
| 0b-G2 | Glossary term agreed → add `[[G-xxx]]`, offer a module-scoped retrofit | `0b:30` | `policy:confirm` → yes; the retrofit offer is propose-only. |
| 0b-G3 | Structural `[LAW]` change → propose, add `[[A-xxx]]` on confirmation | `0b:32-33` | `policy:confirm` → yes. |
| 0b-G4 | UI structural / brand token changes | `0b:35` | `policy:confirm`, but it should not fire on a non-UI fixture — if it does, the same leak `2b-G4` watches for has reached `0b`, and that is a finding. |
| 0b-G5 | Memory lint — propose fixes, list warnings, **await confirmation** | `0b:36` | `policy:confirm` → yes. |

`0b:53` makes this explicit: crystallization, supersession and lint fixes all require user
confirmation, so `0b` is the most gate-dense phase after `1b`.

---

## What is deliberately absent

`3a-version-planning`, `3c-sprint-planning`, `1c-concept-map` and `2c-reconcile-specs` are
outside the driven chain. Their gates are not enumerated here; a run that reaches one has
left the chain, which is itself the finding.

**This file is derived from the sources named in each row, not from a run.** Every row is
a prediction until a run confirms it. A gate the run hits that is missing here is a
documentation defect as well as a harness one — record both (Slice 9).
