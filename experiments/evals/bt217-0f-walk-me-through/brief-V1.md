# Brief: explain code behavior to a non-technical owner

A non-technical product owner asks the 14 questions in `C:\t\bt217-micro-run\questions.md`. Answer each one from the real code, in 2–4 plain sentences, as you would state it in a walkthrough: what happens, under which exact conditions, and any exception. Name a file or setting only where the owner needs it.

Read-only: never edit, check out, install or run anything that changes files in the repos. Reading files, searching and `git log`/`git show` are fine.
Off limits (unrelated scratch, not source): any `.tmp/` folder in either repo, and `C:\t\bt217-micro-run\` except the files named in this brief. Exclude `.tmp/` and `node_modules/` from every search.

## Rules (follow exactly)
- Trace from the entry point that actually runs (scheduler, route, command); confirm each rule's input is passed in.
- Read the line behind every rule, number, weight and condition you state. Keep its exact condition (e.g. "unless known to fail", not "if it works") and what overrides it (an earlier rule or status that wins regardless). No line → drop the claim.
- Examples come only from the code, tests or record read; any other is illustrative: labelled, phrased "would".
- No "all", "every", "only", "never" or "any" unless the code says so; otherwise name the exception or narrow the claim.
- Never state a value you did not read.
- **Self-check before answering:** list each claim with its file:line in your notes file. Re-open each line and confirm the plain wording keeps its exact condition, number and override. Fix or drop any that do not.
- **Quote first:** before answering a question, copy verbatim into your notes the lines that decide it (conditions, constants, early returns, and the callers that pass the inputs), each with file:line. Answer only from those quotes; drop anything you could not quote.
- Never infer behavior from a function, variable, file or field name: open the body and read what it does.
## Output
- Notes (your working, any format): `C:\t\bt217-micro-run\notes\ans-<ID>-notes.md`
- Answers: `C:\t\bt217-micro-run\out\ans-<ID>.md`, exactly this shape and nothing else (no file:line, no notes):

```
## 1
<2–4 plain sentences>
## 2
...
## 14
...
```

Reply with one line: done, and any question you could not answer.
