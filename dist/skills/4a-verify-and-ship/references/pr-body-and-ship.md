---
description: PR body format, `pr_body.py` build flags and verdicts, suite record, risk label and closing-link read-back for 4a Phase 5 step 5.
version: "1.0.0"
timestamp: 2026-10-06
---

# PR Body & Ship Details

Detail for 4a Phase 5 step 5. The body is for agents, not readers: closing lines, then one machine-readable block, rebuilt on every create/update (never appended).

## Body format
````text
Closes #<n>.                <- one line per shipped slice; the literal form, nothing after the period

```stratos-pr
feature: BT-<parentPadded>
head: <sha>
slices:
  - {id: BT-<padded>, summary: "<one line>", verdict: PASS|WAIVED|SKIP|PENDING, audit_rounds: <n>}
test: {cmd: "<cmd>", observed: "<observed summary line>", at: <sha>}
risk: [<tags>]              # from references/merge-risk-paths.md; [none] if no rule fires
post_merge: ["<manual step>"]   # [] if none; manual-QA items go here
deviations: ["<decision not in issue/design>"]   # from the 3d plan's ## Deviations; [] if no plan file
refs: [<only IDs that constrained the change>]
```
## Notes                     <- optional; bug fixes: root cause only
````

## Build
`pr_body.py build` rebuilds the slice list from `git log` (others keep their prior verdicts; commits not yet through 4a are `PENDING`), unions follow-ups with the prior block, writes the `Closes` lines, `test:` and `risk:`.
- **Verdicts:** `PASS` = audited clean; `WAIVED` = shipped on user authorization over gaps (Phase 4); `SKIP` = audit bypassed by the Value-Add Gate. A `ship-only` run never audited: take verdict and rounds from the dispatcher (3z Step 3A).
- **Optional flags:** `--manual-qa` (3d's `needs_manual_qa`), `--post-merge "<step>"`, `--deviation "<decision>"` (from the 3d plan's `## Deviations`), `--ref <ID>`.

## Suite
`python .agents/scripts/pr_body.py suite` prints the reusable result (HEAD, or release-only commits since). None → run the suite once and write `{"head_sha", "cmd", "observed"}` to `.tmp/3d-suite-BT-<padded>.json` (the `3d-` prefix stays so 3d and 4a share the file). Never delete these files. `build` reads it.

## Risk label
`risk:` follows `references/merge-risk-paths.md` (plus the project's `## One-way paths`). Not `[none]` → `gh label create risk:one-way --force --description "Hard-to-reverse change; human must read before merge"` (`--add-label` fails on a missing label), then `gh pr edit <n> --add-label risk:one-way`.

## Closing-link read-back
After `gh pr create` / `gh pr edit`, run `gh pr view <pr> --json closingIssuesReferences` and confirm the slice issue is listed. Not listed → correct the closing lines and re-check **once**; still unlisted → report `[NO-AUTOCLOSE #<n>]` in the ship output and leave it to `/0b` done-detection to close after merge (GitHub only auto-closes what is linked; #128/#129 were not, whatever the wording). Never loop.
