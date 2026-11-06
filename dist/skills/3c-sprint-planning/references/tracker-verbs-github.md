---
description: The single write surface for issue state: the runtime halt rule, each write kind as a verb, the misfits and the read forms. Workflows name a verb; this file says how the backend does it.
version: "5.1.0"
timestamp: 2026-10-22
---

<!-- AUTO-GENERATED: DO NOT EDIT DIRECTLY. Compiled from src/references/tracker-verbs.md by build/build.py -->

# Tracker verbs (GitHub)

The backend is `tracker: github | local` in `.memory/ARCHITECTURE.md`. `reconcile.py` resolves it: the key; else a tracker branch (or a v5 map still to migrate) means local; else GitHub when `gh` is ready; else halt. Workflows state a write once, as a verb. Labels and milestones: `references/label-taxonomy.md`.

## Runtime rule
- GitHub is the only store. Never write a local copy: no issue file, no `BT-LOCAL-*` id, no mirror file.
- A `gh` failure is retried 3 times with backoff (the scripts do it; by hand, retry the same way). Then halt and say so. Never fall back to a local write.

## Verbs
- `create`: `gh issue create --title … --label … [--milestone …] --body-file .tmp/<name>.md`; the id is the returned number, zero-padded (`BT-007`). Never predict it: GitHub shares numbering with PRs
- `set_status`: `gh issue edit <n> --remove-label "status:<old>" --add-label "status:<new>"`; it owns the Single Status Invariant, so the old label goes first. The board Action moves the card
- `set_labels`: `gh issue edit <n> --add-label … --remove-label …`
- `ensure_label`: `gh label create "<name>" --description …` after the user confirms; the live `gh label list` is the registry
- `set_milestone`: `gh issue edit <n> --milestone "vX.Y.Z"`
- `ensure_milestone`: list with `gh api --paginate 'repos/{owner}/{repo}/milestones?state=open' --jq '.[].title'`, create with `gh api repos/{owner}/{repo}/milestones -f title=vX.Y.0`
- `close_milestone`: `gh api -X PATCH repos/{owner}/{repo}/milestones/<n> -f state=closed`, only at 0 open issues
- `set_parent`: `addSubIssue` (`removeSubIssue` to unlink), per `references/github-issue-relations.md`
- `add_blocker`: `addBlockedBy` per `references/github-issue-relations.md`
- `clear_blocker`: `removeBlockedBy` per `references/github-issue-relations.md`; `reconcile.py --edges` decides which edges clear
- `close`: `gh issue close <n> --reason completed` (`--reason "not planned"` for a drop). One rule, both backends: the merge closes; a workflow never closes an unmerged epic. GitHub closes natively when a PR with `Closes #<n>` merges
- `merged`: Server-side: GitHub PR merge closes linked issues (`Closes #<n>`)
- `reopen`: `gh issue reopen <n>`, then `set_status`
- `comment`: `gh issue comment <n> --body …`; a resume note: `--body-file .tmp/resume-BT-<n>.md`
- `set_refs`: the issue body's `Refs: [[L-012]], [[A-003]]` line: replace that line through `set_body`; memory ids only, never doc paths
- `set_ice`: nothing stored: ICE is computed on read from the body's `- **Impact:** N` / `- **Confidence:** N%` bullets (the issue template) and the `size:` label
- `set_body`: `gh issue edit <n> --body-file .tmp/<name>.md` (doc links, `Refs:`, acceptance criteria live here)
- `claim`: `gh issue edit <n> --add-assignee @me`
- `apply_moves`: n/a: the Projects board moves cards natively (a script uses `set_status`)

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
GitHub reads are scoped `--json` queries.
- `get`: `gh issue view <n> --json number,state,labels,milestone,parent,blockedBy,body`
- `list`: `gh issue list --label … --state … --json number,title,labels,milestone`
- `wip`: `gh issue list --state open --label "status:in progress" --json number,title,labels` (about 150 tokens)
- `resume_note`: the task's latest resume note. `gh issue view <n> --json comments --jq '[.comments[] | select(.body | startswith("<!-- stratos:resume -->"))] | last | .body'` (PowerShell 5.1: escape the inner quotes as `\"`); it reads every comment page (the REST comments list returns only the first 30). Empty → no note yet.
- `candidates`: `python .agents/scripts/ice_read.py candidates` on both backends: open leaf issues at `status:planned|needs_spec` (no `concept:*`, no `scope:deferred`), one line each with milestone and ICE computed on read (Impact × Confidence ÷ size weight from the body and the `size:` label; `—` for a Spike or a body without metrics); `[MISSING-LABELS]` lines for leaves lacking a required label.
- `children`: `gh issue view <n> --json subIssues`; a connection: read `.nodes`.
- `blockers`: `gh issue view <n> --json blockedBy`; a connection: read `.nodes`.
- Post-condition check after a multi-write phase: `reconcile.py --ids … --expect …` per `references/terminal-sync-invariant.md`.
