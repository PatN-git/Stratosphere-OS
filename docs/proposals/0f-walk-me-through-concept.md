---
type: plan
title: 0f Walk Me Through — Concept Brief
description: "Concept and draft body for a user-invoked skill that makes the chain behind a result, or the behavior of a planned change, visible in few plain words, so a non-technical owner judges outcomes and choices instead of code."
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-22
version: "0.4.0"
---

# 0f Walk Me Through — concept brief (approved to build)

## Problem
StratOS users build things they cannot technically evaluate. Two failure modes (source: Supercompanies newsletter, 2026-10-01):
1. **Hidden choices.** The agent decides on the user's behalf; errors surface only by accident ("leads × conversions is wrong for B2C").
2. **Rubber-stamping.** Dense output gets a "sounds good". `0e-plain-english` covers this one.

0e makes a message readable. Nothing yet makes the **reasoning behind a result** inspectable, or lets the user **judge a change's behavior** before it ships.

## Objective (review yardstick)
| # | Objective | Checkable as |
|---|---|---|
| O1 | The user judges outcomes and choices, never code | Every call is answerable without reading code or knowing a term |
| O2 | The chain behind a result is visible, with real values | Each step names the rule and the value it acted on |
| O3 | Choices made on the user's behalf surface, domain ones first | Every choice that would change the outcome is marked, with its alternative |
| O4 | No rubber-stamp: few, answerable questions | ≤ 3 calls, each a pick; untested behavior first |
| O5 | Low drag, few words | No new tracker or file, no ship-path time, bounded reading, ≤ 200 words |
| O6 | No fabrication | Grounded in the code that actually runs; illustrative inputs labelled, phrased "would" |
| O7 | Fits StratOS | Lifecycle, HITL, user-invoked, read-only, host-agnostic |

## Shape: one skill, two directions
| Direction | User asks | Agent does | Example |
|---|---|---|---|
| **Trace** (after) | "Why did this happen?" | Walks the path that actually ran for one result, with its values | `/0f why did that Teamtailor job disappear?` |
| **Predict** (before or during) | "What will this do?" | 2–3 situations where another behavior was plausible, untested first | `/0f BT-195` |

A past result → Trace; a ticket, plan or change → Predict. A confirmed call is either already pinned by a test or becomes an acceptance criterion for `/3d-implement-issue`. 0f writes nothing.

## Word economy
Plain is not long. Both 0e and 0f follow the shared plain-language reference (below), whose economy rules are:
- **Replace, don't gloss.** A plain description is usually shorter than term + definition. Gloss only a term the user must keep using.
- **One idea per sentence, ≤ ~15 words.** Fragments and arrows are fine in lists (`Apply link present → next`).
- **Say a thing once.** Never restate the verdict; no reassurance; omit rather than pad.
- **Analogy only when it replaces a longer explanation.**
- **Caps are ceilings, not targets.**

Caps: 0f ≤ 200 words. 0e drops from 250 / 140 to **200 / 120** (proposed; its Picture section is the usual overrun).

## Worked example A — Trace (CleanTechHub, real code, illustrative job) · ~160 words
Rules from `src/lib/ingestion/lifecycleGuard.js` at `b3a26b9`; daily entry point `runLifecycleGuard` (`scripts/run-job-ingestion.js`). The real job row was not read.

> `/0f why did that Teamtailor job disappear?`
>
> **Verdict: the daily link check removes a job at the first rule that matches. This one (illustrative: record not read) would have gone because its page says the ad is no longer current.**
>
> **The chain** (illustrative: posted 1 May, checked 21 Oct)
> 1. Apply link present → next.
> 2. 180-day age cap → **never runs**: the check doesn't load the posting date. ⚖ The cap exists but is off.
> 3. Page loads normally → next.
> 4. Text says "nicht mehr aktuell" ("no longer current"), a phrase added 21 Oct → **removed**. ⚖ One phrase suffices; nothing double-checks.
>
> **Off-path choice:** two failed checks (refused, rate-limited, error, timeout) remove a job; one clean check resets the count.
>
> **How often:** unknown, run logs not read.
>
> **Your calls**
> 1. 180-day cap: make it work, or delete it?
> 2. Two failed checks: remove (as built), or flag for you?
> 3. "nicht mehr aktuell" alone: enough to remove (as built)?
>
> Say "more" on any step, or "pin <n>".

## Worked example B — Predict (StratOS BT-195, real behavior) · ~140 words
From `src/scripts/pr_body.py` (`tracker_facts`), `src/scripts/reconcile.py` (`resolve_backend`), `tests/scripts/test_pr_body.py`, 4a Phase 5 steps 4–5, at `d851013`.

> `/0f BT-195`
>
> **Verdict: BT-195 makes your shipping summary ask GitHub, not the local list, which tickets are features and which are parts. Three situations had an alternative; the first is untested.**
>
> 1. **No setting, no local list, GitHub down.** Not covered by a test. Carries on silently: the feature shows as an unfinished part and won't close on merge. Deliberate per the code. Alternative: stop.
> 2. **Setting says GitHub, GitHub down.** Tested. Code is already uploaded; the review page isn't created or updated. Alternative: use the local list with a warning; it may be stale and misfile work.
> 3. **Setting misspelled.** Tested. Stops and names the bad value.
>
> **Your calls**
> 1. Situation 1: carry on silently (as built), or stop?
> 2. Situation 2: stop (as built), or fall back with a warning?
>
> Say "more" on any situation, or "pin <n>".

## Draft skill body
Frontmatter as 0e: `layer: lifecycle`, `mode: HITL`, `disable-model-invocation: true`, `triggers: ["user"]`, Codex sidecar.

```markdown
---
name: 0f-walk-me-through
description: "Walk a non-technical owner through the chain behind one result (why did this happen) or how a ticket or change will behave (what will this do), surfacing the choices made on their behalf as a few plain calls. Read-only. Invoke only on explicit user request — never autonomously."
---

Make the reasoning behind a result, or the behavior of a change, judgeable by someone who cannot read code. Read-only: no edits, side-effecting commands, or answers on the user's behalf. Wording per `references/plain-language.md`.

**Direction:** a past result → Trace; a ticket, plan or change → Predict.

**Ground truth:**
- Trace from the entry point that actually runs (scheduler, route, command); confirm each rule's input is passed in. A rule that cannot fire is a finding: make it a call.
- Read the real record when a read path exists (the `data_read` key in `ARCHITECTURE.md`): only the record asked about, never in bulk. No key or no access → an illustrative record, said in the Verdict, phrased "would".
- Predict reads the ticket's acceptance criteria, the changed files and their tests only; over ~10 files, name what was skipped.
- Never state a value you did not read.

Output ≤ 200 words, in order:
1. **Verdict:** bold, ≤ 2 sentences: what decides the outcome; for Trace, which step decided it here.
2. **Trace — chain:** the steps that ran, one line each: rule → value seen → result. Stop at the deciding step; at most one off-path step, only if it carries a Choice.
   **Predict — situations:** 2–3 where another behavior was plausible, untested first, each `Tested` or `Not covered by a test`: what will happen, then the alternative.
3. **⚖ Choice:** inline, only where the alternative would change this outcome or a threshold the user sees. ≤ 3, each feeding a call; domain before technical.
4. **How often:** a count where logs or data give one; else `unknown` and why. Predict: omit.
5. **Your calls:** ≤ 3, ranked by impact, each a pick naming the current behavior "as built".
6. Close: `Say "more" on any step, or "pin <n>".`

Never judge the code right or wrong; that is the user's call. On "pin <n>": one acceptance criterion in the user's words (Given / When / Then), for the ticket or `/3d-implement-issue`. On "more": that step only, code path named.
```

## Decisions (2026-10-22)
1. **Build it.** Name `0f-walk-me-through`.
2. **Shared plain-language reference** `src/references/plain-language.md`, fanned out to **0e and 0f only**. 0e's `Rules:` section moves there; 0e points to it. Other HITL halts (4a ship, 3b, 1b/2a) do not adopt it; the user runs `/0e` on demand. Add a third consumer only on a recorded rubber-stamp miss. Not merged into `output-mode.md`: it is always loaded and serves technical and agent-to-agent output too.
3. **output-mode conflict:** none in substance (Advisory mode = verdict first; "Disclose omissions" = 0e "Left out" / 0f "How often"). One tension: §4 "shortest phrasing" vs replacing paths with descriptions, and rules outrank skills (AGENTS §2). Fix: §4 reads "the shortest phrasing that preserves intent **for the reader**". Two words in an always-loaded file.
4. **Data reads:** new optional OKF `architecture` key `data_read` (next to `tracker` in `okf-protocol.md`): how 0f reads one record, e.g. `supabase, read-only role`. The host's permission prompt is not the guard (auto mode skips it); the credential is. A read-only role only, never an admin or service-role key. Absent key → illustrative traces.
5. **4a touchpoint:** no detection of what the user can't judge. Code-quality findings never go to the user anyway. When Watch items exist, the ship halt adds one fixed line: `Unsure about one? /0f watch <n>`. Auditor prompts untouched (audit eval caution).

## Rejected alternatives
| Alternative | Why rejected |
|---|---|
| `0f-tell-me-your-assumptions` (recall on demand) | After the fact the model rationalizes; it lists the safe assumptions, in a volume that invites rubber-stamping, and only when the user remembers to ask |
| Decision log captured at decision time | A new tracker that grows; duplicates 3d `## Deviations` (already in the PR body) and the code itself. Trace reads the code on demand instead |
| Known-answer examples from the user | The owner builds tickets they don't understand and holds no answer key. Survives as Predict: the agent proposes situations, the user judges them |
| Domain-skeptic auditor in 4a | Audit eval (BT-201): a second agent confirms 77–90% of what it is shown; auditor prompt changes are frozen until an experiment passes; no labelled corpus of domain-assumption errors to measure it |

## Riskiest assumption
**0f's own trace is accurate enough to trust.** It is the article's problem pointed back at 0f: a confident, plain explanation that is wrong is worse than none, because it gets believed. Evidence: v0.1 had four wrong claims (O6 4/10). The two worked examples were hand-fixed after review, so they prove nothing on new cases (same trap as the BT-201 arm-P leakage).

**Hold-out test (cheapest, < 1 h):** after the build, run 0f on 3 fresh cases not used in drafting: at least 1 Trace and 1 Predict, at least 1 outside StratOS (CleanTechHub). A fresh-context subagent fact-checks every claim against the code.
- **Pass:** no wrong claim about behavior; every illustrative value labelled; each output ≤ 200 words; every call answerable without code.
- **Fail:** any wrong behavior claim → fix the body's Ground truth rules and re-run on new cases, not the same ones.
- Status: `untested`.

## Non-goals
- Other HITL skills (4a ship, 3b, 1b/2a) do not adopt the plain-language reference.
- No change to 4a auditor prompts, thresholds or Watch scoring; only the one pointer line.
- 0f writes nothing: no tracker, log, file or issue. "pin" hands text to the user.
- No detection of what the user can or cannot judge.
- No bulk data reads, no write-capable credentials.
- Not a code review: 0f never judges the code right or wrong.

## Build scope (one slice)
| File | Change | Bump |
|---|---|---|
| `src/references/plain-language.md` | New: 0e's rules + the economy rules above | new |
| `src/workflows/0e-plain-english.md` | Rules → pointer; caps 200 / 120 | minor |
| `src/workflows/0f-walk-me-through.md` | New, body above | new |
| `src/rules/output-mode.md` | §4 "for the reader" | patch |
| `src/rules/okf-protocol.md` | `data_read` key row | minor |
| `src/workflows/4a-verify-and-ship.md` | One Watch-line pointer at the ship halt | patch |

Then `python build/build.py`, `build/validate.py` green. **Acceptance:** the hold-out test above passes. The two worked examples are format references only, not evidence.

## Findings surfaced while drafting (real, outside this brief)
- **CleanTechHub: the 180-day cap is dead in production.** `runLifecycleGuard` selects `id, apply_link, status, check_failures` (`lifecycleGuard.js:312`); `posted_at` is never loaded. Needs a ticket in that repo.
- **StratOS BT-195: untested silent fallback.** No tracker key, no BACKLOG_MAP, gh unavailable → `resolve_backend` returns `None` ("halt"), but `tracker_facts` treats anything but `github` as local (`pr_body.py:365`). The comment says intended; no test pins it. Owner's call pending.

## Review log
- **v0.1.0 → independent review (fresh-context subagent).** O1 7 · O2 5 · O3 6 · O4 8 · O5 7 · O6 4 · O7 8. Example A claimed the 180-day cap fires (it never runs) and narrowed the failure rule to 401/403; example B said "nothing ships" (code is pushed before the PR body) and missed the untested fallback. Root cause: traced from the function, not the entry point; illustrative records phrased as fact.
- **v0.2.0.** All six review edits applied; claims re-verified against the code.
- **v0.3.0 (this version).** Owner decisions folded in; renamed 0f; word economy added (shared rules, 0f cap 300 → 200, 0e caps 250 / 140 → 200 / 120 proposed); examples cut to ~160 and ~140 words (whitespace count incl. markup). Not re-reviewed.
- **v0.4.0.** Filled the 1b-equivalent gaps instead of running 1b (concrete, not PRD-worthy, 1b would exit to 3b): rejected alternatives, riskiest assumption with hold-out test (now the slice's acceptance), non-goals. Mint via `/3b-create-issue` as a raw idea pointing at Build scope; standalone slice.
- **Minted 2026-10-22 as BT-217** (one slice, `mode:HITL`, `size:medium`, ICE skipped, Lifecycle `0 Constitution & Memory`).
