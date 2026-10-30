---
description: The single write surface for issue state. Each write kind once, with its GitHub form and its local-backend form, plus the runtime halt rule, the misfits and the read forms. Workflows name a verb; this file says how the backend does it.
version: "1.0.0"
timestamp: 2026-10-22
---

# Tracker verbs

The backend is `tracker: github | local` in `.memory/ARCHITECTURE.md`. `reconcile.py` resolves it: the key; else a tracker branch (or a v5 map still to migrate) means local; else GitHub when `gh` is ready; else halt. Workflows state a write once, as a verb. Labels and milestones: `references/label-taxonomy.md`.

## Runtime rule
- **GitHub mode:** GitHub is the only store. Never write a local copy: no issue file, no `BT-LOCAL-*` id, no mirror file.
- A `gh` failure is retried 3 times with backoff (the scripts do it; by hand, retry the same way). Then halt and say so. Never fall back to a local write.
- **Local mode:** GitHub is not touched. One file per issue, `docs/issues/<id>.md` (closed: `archive/`), on the `<repo>/issues` branch (`tracker_branch:` in ARCHITECTURE.md), never in the working tree, so every branch sees one state. Ids are `BT-LOCAL-<slug>`: wherever a workflow or template writes `BT-<padded>` (ids, commit scope, branch, suite file, Parent/Blocked by), local mode uses the full `BT-LOCAL-<slug>`. `python .agents/scripts/issues.py` does every read and write; never edit an issue file, never check out the tracker branch. A refused write exits 1: halt and say so.

## Verbs
| Verb | GitHub form | Local form |
|:--|:--|:--|
| `create` | `gh issue create --title … --label … [--milestone …] --body-file .tmp/<name>.md`; the id is the returned number, zero-padded (`BT-007`). Never predict it: GitHub shares numbering with PRs | `issues.py create --title <t> --label <l,l> --body-file .tmp/<name>.md` (`--status`, `--milestone`, `--parent`, `--blocked-by` as needed) prints `BT-LOCAL-<slug>` (`-2` … on a clash) |
| `set_status` | `gh issue edit <n> --remove-label "status:<old>" --add-label "status:<new>"`; it owns the Single Status Invariant, so the old label goes first. The board Action moves the card | `issues.py set <id> --status <s>` (one field: the invariant holds in code) |
| `set_labels` | `gh issue edit <n> --add-label … --remove-label …` | `issues.py set <id> --add-label <l> --remove-label <l>` |
| `ensure_label` | `gh label create "<name>" --description …` after the user confirms; the live `gh label list` is the registry | `issues.py label area:<slug>` after the user confirms |
| `set_milestone` | `gh issue edit <n> --milestone "vX.Y.Z"` | `issues.py set <id> --milestone vX.Y.Z` (`—` unsets) |
| `ensure_milestone` | list with `gh api --paginate 'repos/{owner}/{repo}/milestones?state=open' --jq '.[].title'`, create with `gh api repos/{owner}/{repo}/milestones -f title=vX.Y.0` | nothing to create: the field value is the milestone |
| `close_milestone` | `gh api -X PATCH repos/{owner}/{repo}/milestones/<n> -f state=closed`, only at 0 open issues | derived: no open issue carries it |
| `set_parent` | `addSubIssue` (`removeSubIssue` to unlink), per `references/github-issue-relations.md` | `issues.py set <id> --parent <id>` (`—` unlinks) |
| `add_blocker` | `addBlockedBy` per `references/github-issue-relations.md` | `issues.py set <id> --add-blocker <id>` |
| `clear_blocker` | `removeBlockedBy` per `references/github-issue-relations.md`; `reconcile.py --edges` decides which edges clear | `issues.py set <id> --remove-blocker <id>` |
| `close` | `gh issue close <n> --reason completed` (`--reason "not planned"` for a drop); merging a PR with `Closes #<n>` closes too | `issues.py close <id> [--reason "not planned"]`: `done` plus date and reason, moved to `archive/` |
| `reopen` | `gh issue reopen <n>`, then `set_status` | `issues.py reopen <id> [--status <s>]` |
| `comment` | `gh issue comment <n> --body …`; a resume note: `--body-file .tmp/resume-BT-<n>.md` | `issues.py comment <id> --body-file .tmp/<name>.md` (or `--body`); a resume note overwrites `.memory/resume/<id>.md` (one file per issue, gitignored); a PR-link comment is a normal comment |
| `set_refs` | the issue body's `Refs: [[L-012]], [[A-003]]` line: replace that line through `set_body`; memory ids only, never doc paths | the same `Refs:` line, through `issues.py set <id> --body-file <f>` |
| `set_ice` | nothing stored: ICE is computed on read from the body's `- **Impact:** N` / `- **Confidence:** N%` bullets (the issue template) and the `size:` label | the same: nothing stored |
| `set_body` | `gh issue edit <n> --body-file .tmp/<name>.md` (doc links, `Refs:`, acceptance criteria live here) | `issues.py set <id> --body-file .tmp/<name>.md` |
| `claim` | `gh issue edit <n> --add-assignee @me` | `issues.py claim <id>` (compare-and-set: `in progress`, `claimed_by` = the branch); `[CLAIMED <id> by <x>]` → halt |

## Resume note
Per-task progress and next step, written by 0b with `comment` and read by `load-memory` with `resume_note`. A fixed block, replaced whole on each write:
```
<!-- stratos:resume -->
Branch: / Done: / Open: / Next step: / Blockers:
```
`.memory/STATUS.md` never holds it: STATUS is folder state only.

## Misfits
These have no clean equal on the other backend; each is a named, accepted gap, not a bug.
- `close`: on GitHub the unit PR merge closes epics (`Closes #<n>`) with no tracker call; locally no merge closes anything: 0b post-merge sync closes the epics in the merged PR's `features:` list; with no PR host the user closes them.
- PR operations (`gh pr create/edit/ready`, the `risk:one-way` label) are a VCS-host concept and not a tracker verb.

## Reads
GitHub reads are scoped `--json` queries; local reads are the same-named `issues.py` command (JSON).
- `get`: `gh issue view <n> --json number,state,labels,milestone,parent,blockedBy,body` (local adds `comments`)
- `list`: `gh issue list --label … --state … --json number,title,labels,milestone`; local: `issues.py list [--status <s>] [--label <l>] [--parent <id>] [--all]` (`--all` adds closed)
- `wip`: `gh issue list --state open --label "status:in progress" --json number,title,labels` (about 150 tokens); local: `issues.py wip`
- `resume_note`: the task's latest resume note. GitHub: `gh issue view <n> --json comments --jq '[.comments[] | select(.body | startswith("<!-- stratos:resume -->"))] | last | .body'` (PowerShell 5.1: escape the inner quotes as `\"`); it reads every comment page (the REST comments list returns only the first 30); local: `.memory/resume/<id>.md`. Empty → no note yet.
- `candidates`: `python .agents/scripts/ice_read.py candidates` on both backends: open leaf issues at `status:planned|needs_spec` (no `concept:*`, no `scope:deferred`), one line each with milestone and ICE computed on read (Impact × Confidence ÷ size weight from the body and the `size:` label; `—` for a Spike or a body without metrics); `[MISSING-LABELS]` lines for leaves lacking a required label. Local `issues.py ready` prints the same lines for the leaves whose blockers cleared, plus `[BLOCKED <id> <- <blocker>]`.
- `children`: `gh issue view <n> --json subIssues`; `blockers`: `gh issue view <n> --json blockedBy`. Both are connections: read `.nodes`.
- Post-condition check after a multi-write phase: `reconcile.py --ids … --expect …` (GitHub mode) per `references/terminal-sync-invariant.md`; local: `issues.py check` (exit 1 on a finding).
