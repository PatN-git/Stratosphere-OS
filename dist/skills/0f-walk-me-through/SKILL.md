---
name: 0f-walk-me-through
description: "Walk a non-technical owner through the chain behind one result (why did this happen) or how a ticket or change will behave (what will this do), surfacing the choices made on their behalf as a few plain calls. Read-only. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.0.0"
timestamp: 2026-10-28
---

Make the reasoning behind a result, or the behavior of a change, judgeable by someone who cannot read code. Read-only: no edits, side-effecting commands, or answers on the user's behalf. Wording per `references/plain-language.md`.

**Direction:** a past result → Trace; a ticket, plan or change → Predict. `watch <n>` → Predict on the n-th Watch item of the last ship halt in this conversation: the slice's acceptance criteria, the file it names, that file's tests. Item not in the conversation → ask for it.

**Ground truth:**
- Trace from the entry point that actually runs (scheduler, route, command); confirm each rule's input is passed in. A rule that cannot fire is a finding: make it a call.
- Read the real record when a read path exists (the `data_read` key in `.memory/ARCHITECTURE.md` frontmatter): only the record asked about, never in bulk. No key or no access → an illustrative record, said in the Verdict, phrased "would".
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
