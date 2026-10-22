---
description: The single write surface for issue state. Each write kind once, with its GitHub form and its local-backend form, plus the runtime halt rule, the misfits and the read forms. Workflows name a verb; this file says how the backend does it.
version: "1.0.0"
timestamp: 2026-10-22
---

# Tracker verbs

The backend is `tracker: github | local` in `.memory/ARCHITECTURE.md`. `reconcile.py` resolves it: the key; else a present `BACKLOG_MAP.md` means local; else GitHub when `gh` is ready; else halt. Workflows state a write once, as a verb. Labels and milestones: `references/label-taxonomy.md`.

## Runtime rule
- **GitHub mode:** GitHub is the only store. Never write a local copy: no `BACKLOG_MAP.md` row or cell, no `BT-LOCAL-*` id, no mirror file.
- A `gh` failure is retried 3 times with backoff (the scripts do it; by hand, retry the same way). Then halt and say so. Never fall back to a local write.
- **Local mode:** `.memory/BACKLOG_MAP.md` is the store and GitHub is not touched. The 9-column row schema and its rules are in the map template; ids are `BT-LOCAL-<slug>` until `tracker_switch.py` moves the project to GitHub.

## Verbs
| Verb | GitHub form | Local form |
|:--|:--|:--|
| `create` | `gh issue create --title … --label … [--milestone …] --body-file .tmp/<name>.md`; the id is the returned number, zero-padded (`BT-007`). Never predict it: GitHub shares numbering with PRs | append the row; the id is `BT-LOCAL-<slug>` |
| `set_status` | `gh issue edit <n> --remove-label "status:<old>" --add-label "status:<new>"`; it owns the Single Status Invariant, so the old label goes first. The board Action moves the card | edit the Status cell |
| `set_labels` | `gh issue edit <n> --add-label … --remove-label …` | edit the Labels cell |
| `ensure_label` | `gh label create "<name>" --description …` after the user confirms; the live `gh label list` is the registry | add the label to the map's Label Registry, then use it |
| `set_milestone` | `gh issue edit <n> --milestone "vX.Y.Z"` | edit the Milestone cell |
| `ensure_milestone` | list with `gh api --paginate 'repos/{owner}/{repo}/milestones?state=open' --jq '.[].title'`, create with `gh api repos/{owner}/{repo}/milestones -f title=vX.Y.0` | the Milestone cell value is the milestone; nothing to create |
| `close_milestone` | `gh api -X PATCH repos/{owner}/{repo}/milestones/<n> -f state=closed`, only at 0 open issues | derived: no open row carries it |
| `set_parent` | `addSubIssue` (`removeSubIssue` to unlink), per `references/github-issue-relations.md` | edit the Parent cell (one value, on the child) |
| `add_blocker` | `addBlockedBy` per `references/github-issue-relations.md` | add the bare id to the Blocked by cell |
| `clear_blocker` | `removeBlockedBy` per `references/github-issue-relations.md`; `reconcile.py --edges` decides which edges clear | remove the id from the Blocked by cell |
| `close` | `gh issue close <n> --reason completed` (`--reason "not planned"` for a drop); merging a PR with `Closes #<n>` closes too | set Status to `done` (closed = done) |
| `reopen` | `gh issue reopen <n>`, then `set_status` | set Status back |
| `comment` | `gh issue comment <n> --body …` | append a dated line to the issue's draft file; a PR-link comment has no local form (no PR) |
| `set_refs` | the issue body's `Refs: [[L-012]], [[A-003]]` line: replace that line through `set_body`; memory ids only, never doc paths | edit the Ref cell |
| `set_ice` | nothing stored: ICE is computed on read from the body's `I:`/`C:` metrics and the `size:` label | edit the ICE cell |
| `set_body` | `gh issue edit <n> --body-file .tmp/<name>.md` (doc links, `Refs:`, acceptance criteria live here) | the issue's draft or spec file (`docs/prds/`, `docs/design/`, the drafts file); the table holds only a title |
| `claim` | `gh issue edit <n> --add-assignee @me` | no-op |

## Misfits
These have no clean equal on the other backend; each is a named, accepted gap, not a bug.
- `set_ice`: GitHub keeps no score; it is derived. Bodies in older formats return null, which falls into 3c's "recalculate if empty" path.
- `set_refs`: a pointer into `.memory/` has no GitHub field, so it is a body line. `validate_memory.py` lints Refs for the local backend only.
- `set_body`: the local table has no body; the draft and spec files stand in.
- `claim`: no owner column locally.
- `close`: on GitHub the unit PR merge closes epics (`Closes #<n>`) with no tracker call; locally 0b closes explicitly because there is no merge.
- PR operations (`gh pr create/edit/ready`, the `risk:one-way` label) are a VCS-host concept and not a tracker verb.

## Reads
GitHub reads are scoped `--json` queries; the local backend scans the table.
- `get`: `gh issue view <n> --json number,state,labels,milestone,parent,blockedBy,body`
- `list`: `gh issue list --label … --state … --json number,title,labels,milestone`
- `children`: `gh issue view <n> --json subIssues`; `blockers`: `gh issue view <n> --json blockedBy`. Both are connections: read `.nodes`.
- Post-condition check after a multi-write phase: `reconcile.py --ids … --expect …` (GitHub mode) per `references/terminal-sync-invariant.md`.
