---
description: The single write surface for local issue state. Local issues.py form for each write kind, runtime halt rule, misfits and read forms.
version: "5.0.0"
timestamp: 2026-10-30
---

# Tracker verbs (Local)

The backend is `tracker: local` in `.memory/ARCHITECTURE.md`. Labels and milestones: `references/label-taxonomy.md`.

## Runtime rule
- GitHub is not touched. One file per issue, `docs/issues/<id>.md` (closed: `archive/`), on the `<repo>/issues` branch (`tracker_branch:` in ARCHITECTURE.md), never in the working tree, so every branch sees one state.
- Ids are `BT-LOCAL-<slug>`: wherever a workflow or template writes `BT-<padded>` (ids, commit scope, branch, suite file, Parent/Blocked by), local mode uses the full `BT-LOCAL-<slug>`.
- `python .agents/scripts/issues.py` does every read and write; never edit an issue file, never check out the tracker branch. A refused write exits 1: halt and say so.

## Verbs
- `create`: `issues.py create --title <t> --label <l,l> --body-file .tmp/<name>.md` (`--status`, `--milestone`, `--parent`, `--blocked-by` as needed) prints `BT-LOCAL-<slug>` (`-2` … on a clash)
- `set_status`: `issues.py set <id> --status <s>` (one field: the invariant holds in code)
- `set_labels`: `issues.py set <id> --add-label <l> --remove-label <l>`
- `ensure_label`: `issues.py label area:<slug>` after the user confirms
- `set_milestone`: `issues.py set <id> --milestone vX.Y.Z` (`—` unsets)
- `ensure_milestone`: nothing to create: the field value is the milestone
- `close_milestone`: derived: no open issue carries it
- `set_parent`: `issues.py set <id> --parent <id>` (`—` unlinks)
- `add_blocker`: `issues.py set <id> --add-blocker <id>`
- `clear_blocker`: `issues.py set <id> --remove-blocker <id>`
- `close`: `issues.py close <id> [--reason "not planned"]`: `done` plus date and reason, moved to `archive/`
- `merged`: `issues.py merged [--close]`: checks ancestry of shipped branches and tip SHAs against the default branch; prints `[MERGED <id>]` (and with `--close` marks done and archives)
- `reopen`: `issues.py reopen <id> [--status <s>]`
- `comment`: `issues.py comment <id> --body-file .tmp/<name>.md` (or `--body`); a resume note overwrites `.memory/resume/<id>.md` (one file per issue, gitignored); a PR-link comment is a normal comment
- `set_refs`: the same `Refs:` line, through `issues.py set <id> --body-file <f>`
- `set_ice`: the same: nothing stored
- `set_body`: `issues.py set <id> --body-file .tmp/<name>.md`
- `claim`: `issues.py claim <id>` (compare-and-set: `in progress`, `claimed_by` = the branch); `[CLAIMED <id> by <x>]` → halt

## Resume note
Per-task progress and next step, written by 0b with `comment` and read by `load-memory` with `resume_note`. A fixed block, replaced whole on each write:
```
<!-- stratos:resume -->
Branch: / Done: / Open: / Next step: / Blockers:
```
`.memory/STATUS.md` never holds it: STATUS is folder state only.

## Misfits
These have no clean equal on the other backend; each is a named, accepted gap, not a bug.
- `close`: one rule, both backends: the merge closes; a workflow never closes an unmerged epic. Locally, 0b runs `issues.py merged --close` (ancestry check against default branch and recorded tip SHAs).
- `tracker_switch`: one-way only (local → GitHub). Reverse switch is omitted intentionally: GitHub issues with PR connections, discussions, and external links cannot be round-tripped without loss or dual-store conflict complexity; moving from GitHub to local starts a clean local store.
- PR operations (`gh pr create/edit/ready`, the `risk:one-way` label) are a VCS-host concept and not a tracker verb.

## Reads
Local reads are the same-named `issues.py` command (JSON).
- `get`: `issues.py get <id>` (includes comments)
- `list`: `issues.py list [--status <s>] [--label <l>] [--parent <id>] [--all]` (`--all` adds closed)
- `wip`: `issues.py wip`
- `board`: `issues.py board [--milestone <m>] [--parent <id>] [--md [file]]`
- `resume_note`: the task's latest resume note: `.memory/resume/<id>.md`. Empty → no note yet.
- `candidates`: `python .agents/scripts/ice_read.py candidates`: open leaf issues at `status:planned|needs_spec` (no `concept:*`, no `scope:deferred`), one line each with milestone and ICE computed on read (Impact × Confidence ÷ size weight from the body and the `size:` label; `—` for a Spike or a body without metrics); `[MISSING-LABELS]` lines for leaves lacking a required label. `issues.py ready` prints the same lines for the leaves whose blockers cleared, plus `[BLOCKED <id> <- <blocker>]`.
- `children`: `issues.py get <id>` (sub-issues)
- `blockers`: `issues.py get <id>` (blockers)
- Post-condition check after a multi-write phase: `reconcile.py --ids … --expect …` per `references/terminal-sync-invariant.md` (whole-store `issues.py check` is also available).
