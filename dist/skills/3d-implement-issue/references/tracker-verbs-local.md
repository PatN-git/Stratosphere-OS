---
description: The single write surface for issue state: the runtime halt rule, each write kind as a verb, the misfits and the read forms. Workflows name a verb; this file says how the backend does it.
version: "5.1.0"
timestamp: 2026-10-22
---

<!-- AUTO-GENERATED: DO NOT EDIT DIRECTLY. Compiled from src/references/tracker-verbs.md by build/build.py -->

# Tracker verbs (Local)

The backend is `tracker: github | local` in `.memory/ARCHITECTURE.md`. `reconcile.py` resolves it: the key; else a tracker branch (or a v5 map still to migrate) means local; else GitHub when `gh` is ready; else halt. Workflows state a write once, as a verb. Labels and milestones: `references/label-taxonomy.md`.

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
- `close`: `issues.py close <id> [--reason "not planned"]`: `done` plus date and reason, moved to `archive/`. The rule: the merge closes; a workflow never closes an unmerged epic. 0b runs `issues.py merged --close` (ancestry check against the default branch and the newest recorded tip SHA of the issue and of each child slice)
- `merged`: `issues.py merged [--close]`: checks ancestry of shipped branches and tip SHAs against the default branch; prints `[MERGED <id>]` (and with `--close` marks done and archives)
- `reopen`: `issues.py reopen <id> [--status <s>]`
- `comment`: `issues.py comment <id> --body-file .tmp/<name>.md` (or `--body`); a resume note overwrites `.memory/resume/<id>.md` (one file per issue, gitignored); a PR-link comment is a normal comment
- `set_refs`: the same `Refs:` line, through `issues.py set <id> --body-file <f>`
- `set_ice`: the same: nothing stored
- `set_body`: `issues.py set <id> --body-file .tmp/<name>.md`
- `claim`: `issues.py claim <id>` (compare-and-set: `in progress`, `claimed_by` = the branch); `[CLAIMED <id> by <x>]` → halt
- `apply_moves`: `issues.py apply-moves [<file>] [--dry-run] [--force]` (no file: stdin): the batch status writer for a person's moves, the payload copied from `board --web` (`<id> … -> <status>` lines, a `Please apply` header ignored). One bad line, unknown id or status, or refused move applies nothing and exits 1. `done` is `close`, away from it `reopen`; an `in review` epic or standalone issue moves to `done` only once `merged`, else `--force`. A move into `in progress`, `in review` or `done` is refused while a blocker is open (the `ready` verdict, judged on the batch end state), else `--force`; `set`, `close` and `reopen` are not guarded

## Resume note
Per-task progress and next step, written by 0b with `comment` and read by `load-memory` with `resume_note`. A fixed block, replaced whole on each write:
```
<!-- stratos:resume -->
Branch: / Done: / Open: / Next step: / Blockers:
```
`.memory/STATUS.md` never holds it: STATUS is folder state only.

## Misfits
These have no clean equal on the other backend; each is a named, accepted gap, not a bug.
- `tracker_switch`: one-way only (local → GitHub). Reverse switch is omitted intentionally: GitHub issues with PR connections, discussions, and external links cannot be round-tripped without loss or dual-store conflict complexity; moving from GitHub to local starts a clean local store.
- PR operations (`gh pr create/edit/ready`, the `risk:one-way` label) are a VCS-host concept and not a tracker verb.

## Reads
Local reads are the same-named `issues.py` command (JSON).
- `get`: `issues.py get <id>` (includes comments)
- `list`: `issues.py list [--status <s>] [--label <l>] [--parent <id>] [--all]` (`--all` adds closed)
- `wip`: `issues.py wip`
- `board`: `issues.py board [--milestone <m>] [--parent <id>] [--md [file]]`: text kanban columns, or a Markdown export; `issues.py board --web [--out <f>] [--open]`: an interactive HTML page (a browser opens only with `--open`) whose copied payload is the `apply_moves` input.
- `resume_note`: the task's latest resume note: `.memory/resume/<id>.md`. Empty → no note yet.
- `candidates`: `python .agents/scripts/ice_read.py candidates` on both backends: open leaf issues at `status:planned|needs_spec` (no `concept:*`, no `scope:deferred`), one line each with milestone and ICE computed on read (Impact × Confidence ÷ size weight from the body and the `size:` label; `—` for a Spike or a body without metrics); `[MISSING-LABELS]` lines for leaves lacking a required label.
- `ready`: `issues.py ready` prints the same lines for the leaves whose blockers cleared, plus `[BLOCKED <id> <- <blocker>]`.
- `children`: `issues.py children <id>` (`get` lists no sub-issues).
- `blockers`: `issues.py blockers <id>`.
- Post-condition check after a multi-write phase: `reconcile.py --ids … --expect …` per `references/terminal-sync-invariant.md` (whole-store `issues.py check` is also available).
