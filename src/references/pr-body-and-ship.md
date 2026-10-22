---
description: PR body format, `pr_body.py` build flags and verdicts, suite record, risk label and closing-link read-back for 4a Phase 5 step 5.
version: "1.1.0"
timestamp: 2026-10-20
---

# PR Body & Ship Details

Detail for 4a Phase 5 step 5. The body is for agents, not readers: closing lines, then one machine-readable block, rebuilt on every create/update (never appended).

## Body format
````text
Closes #<n>.                <- one line per shipped slice; the literal form, nothing after the period

```stratos-pr
features: [BT-<parentPadded>, ...]   # one per epic in the PR
head: <sha>
slices:
  - {id: BT-<padded>, parent: BT-<parentPadded>, summary: "<one line>", verdict: PASS|WAIVED|SKIP|DROPPED|PENDING, audit_rounds: <n>}   # parent: omitted when standalone
test: {cmd: "<cmd>", observed: "<observed summary line>", at: <sha>}
risk: [<tags>]              # from references/merge-risk-paths.md; [none] if no rule fires
post_merge: ["<manual step>"]   # [] if none; manual-QA items go here
deviations: ["<decision not in issue/design>"]   # from the 3d plan's ## Deviations; [] if no plan file
audit: {"BT-<padded>": {...}}   # optional: auditor findings per slice (see Audit findings); absent when none recorded
refs: [<only IDs that constrained the change>]
```
## Notes                     <- optional; bug fixes: root cause only
````

## Build
`pr_body.py build` rebuilds the slice list from `git log` (others keep their prior verdicts; commits not yet through 4a are `PENDING`), unions follow-ups with the prior block, writes the `Closes` lines, `test:` and `risk:`.
- **Verdicts:** `PASS` = audited clean; `WAIVED` = shipped on user authorization over gaps (Phase 4); `SKIP` = audit bypassed by the Value-Add Gate; `DROPPED` = deferred and closed not planned: a human sets it once in the prior body block (never `--verdict`), the row is kept and gets no `Closes` line. Commits scoped to any epic in `features:` (a `tier:epic` row in `.memory/BACKLOG_MAP.md`, or `--epic BT-<n>` when that file is absent, e.g. CI) are skipped, never a slice row. A `ship-only` run never audited: take verdict and rounds from the dispatcher (3z Step 3A).
- **Base:** `--base`, else the remote default branch (`origin/HEAD`), else the `main`/`master` candidates (it scopes the slice list and `risk:`). None resolves → `[PR-BODY-ERROR]` (status 2), never `risk: [none]`: pass `--base <default-branch>` then.
- **Parent flags:** `--parent` = the shipped slice's parent (joins `features:`; omit when standalone). `--close BT-<n>` (repeatable) = an epic this PR completes: adds `Closes #<n>.` after the slice lines. `--close-parent` = alias for `--close <--parent>`.
- **Optional flags:** `--manual-qa` (`needs_manual_qa` true: 3z Step 3A dispatch, or a manual-only AC the Phase 2 table marks `[NONE]`), `--post-merge "<step>"` (also `noticed: <line>` per the 3d plan's `Noticed, not touched`; `none` → omit), `--deviation "<decision>"` (one per line of the 3d plan's `## Deviations`; `none` → omit), `--ref <ID>`.

## Audit findings
Purpose: data for tuning the 4a audit itself (yield, cost per audit, audit frequency; epic BT-201). Recorded only; no gate reads it.
`audit:` is a top-level JSON line keyed by slice id, spelled as its slice row spells it. The slice row never changes: an in-row field would make an older `pr_body.py` (a vendored copy) fail the row and revert it to `PENDING`; older readers ignore the new line. Every field is omitted when unknown, never `0`:
- `spec_r1` / `spec_final`: Spec gaps ≥ 80 confidence in the first and the last audit round.
- `std_hard` / `std_judg`: Standards Hard breach and Judgment findings of the last round (`Dismissed` not counted).
- `watch`: Spec findings scored 60-79 that remain after the lead's check (4a Phase 3 §3); non-blocking, never a retry.
- `phase1`: the Phase 1 decision, `bypass` or `trigger:<name>` (`security`, `auth`, `billing`, `math`, `prd8`, `size`, `afk`); a bypassed slice records only this field.
- `std_tier`: the `auditor_model` tier the Standards auditor was dispatched with, absent when none was set; a tier name, never a vendor model ID.
- `input`: `lean` when the Spec auditor got the inline packet (diff, ACs, named tests, deviations), `full` when it read full files.

Pass the object with `--audit-file <F>` (`--audit-json '<json>'` is the same payload inline, but PowerShell strips its inner quotes). It replaces the shipped slice's entry; a rebuild without either flag keeps every prior entry. **HITL:** 4a keeps the object in `.tmp/4a-audit-BT-<padded>.json`, written at Phase 1 and rewritten after each audit (`spec_r1` is set once and never overwritten, so it survives the Phase 4 halt and re-audit). **AFK:** `audit-only` returns `{counts, standards, phase1, std_tier, input}`; 3z keeps them per slice (`spec_r1` from attempt 1, `spec_final` from the last attempt) and hands them to `ship-only`, which writes the same file. Tokens are measured offline, not logged. Keep entries compact: release PRs carry 13+ rows.

## Suite
`python .agents/scripts/pr_body.py suite` prints the reusable result: HEAD matches (or only release commits since) **and** the tree is clean outside `.memory/`, `docs/`, `.tmp/`. None → run the suite once through `python .agents/scripts/test_gate.py record --suite BT-<padded> -- <cmd>` (it writes `.tmp/3d-suite-BT-<padded>.json`; the `3d-` prefix stays so 3d and 4a share the file). Never delete these files. `build` reads it.

## Risk label
`risk:` follows `references/merge-risk-paths.md` (plus the project's `## One-way paths`). Not `[none]` → `gh label create risk:one-way --force --description "Hard-to-reverse change; human must read before merge"` (`--add-label` fails on a missing label), then `gh pr edit <n> --add-label risk:one-way`.

## Closing-link read-back
After `gh pr create` / `gh pr edit`, run `gh pr view <pr> --json closingIssuesReferences` and confirm the slice issue **and each closed epic** are listed. Not listed → correct the closing lines and re-check **once**; still unlisted → report `[NO-AUTOCLOSE #<n>]` in the ship output and leave it to `/0b` done-detection to close after merge (GitHub only auto-closes what is linked; #128/#129 were not, whatever the wording). Never loop.
