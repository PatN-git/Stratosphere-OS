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

## Phases not yet driven

`0a`, `1a`, `2a`, `2b`, `3b`, `3d`, `4a`, `0b` are enumerated in Slice 3, once Slice 0's
approach is proven against the hardest case. Gates already known from planning, to be
confirmed against source rather than assumed:

| Phase | Gate | Source | Intended answer |
|:---|:---|:---|:---|
| `1a` | Propose-and-Confirm: domain + depth | `1a:36-40` | `policy:confirm`; fixture pins Quick Search |
| `2b` | Phase 2.5 HITL Pick among 3 generated directions | `2b:46-50` | `policy:pick-first` |
| `3b` | Phase 2.2 ICE fallback, once per slice | `3b` Phase 2.2 | `policy:ice` |
| `4a` | Phase 5.3 ship confirmation | `4a:71` | Never reached — L3 stops at `audit-only` |
