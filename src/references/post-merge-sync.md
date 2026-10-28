---
description: Merge-time tracker bookkeeping for 0b step 1: done detection, unblocking dependents, parent epic and release, abandoned feature PR, post-merge follow-ups. Read only when the 0b gate fires.
version: "1.1.0"
timestamp: 2026-10-22
---

# Post-merge sync

Verbs (`set_status`, `close`, `reopen`, `clear_blocker`, `create`) and the backend rule are in `references/tracker-verbs.md`; local-only steps are marked.

- **Done detection (no forcing):** an epic or standalone issue is `done` only once its PR has **merged** and the issue auto-closed. A child slice is already `done` + closed at 4a ship.
  - For each epic/standalone issue **merged** in the window of 0b's PR query (`closed:>=<Last Sync date>`; no date → its newest 30 closed PRs): `set_status` `done` (the merge closed it).
    - github: the ids come from the PR query 0b ran.
    - local: no merge closes a local id and the PR query has none; the ids are the `features:` list of each merged PR's `stratos-pr` block (`gh pr view <pr> --json body`; read once, the follow-ups step reuses it). `close` each.
    - local, no PR host: 0b cannot see a merge. Name the gap in the handoff `Blockers` line: the user runs `issues.py close <id>` after merging.
  - Then clear the edges that waited on it:
    - github: `python .agents/scripts/reconcile.py --ids <merged ids> --edges dependents`, `<merged ids>` = every id in the merged PRs' `closingIssuesReferences`, child slices included (a slice edge such as S ← A1 clears only at merge). Clear every `[CLEAR]` edge by running its `cmd:` (`clear_blocker`, `removeBlockedBy` per `references/github-issue-relations.md`); leave `[KEEP]`.
    - local: `git fetch -q origin` first (the merge check is git ancestry against `origin/HEAD`), then `python .agents/scripts/reconcile.py --edges dependents --all-open`; clear every `[CLEAR]` edge by running its `cmd:`, leave `[KEEP]`.
    - Offline → every edge is KEEP; say so in the handoff `Blockers` line.
  - **Gate** (`references/terminal-sync-invariant.md`), over the merged issues and every dependent cleared (local: `issues.py check` takes no ids, checks the whole store, exit 1 on any finding; it is the whole gate):
    - github: write the intended end state to `.tmp/0b-expect.txt` (`BT-<n>:status=done` per merged issue, `BT-<d>:blocked_by=<its blockers minus the cleared>` per dependent, its blockers read with `gh issue view <d> --json blockedBy`; `--edges dependents` lists only the edges to the merged ids), then run `python .agents/scripts/reconcile.py --ids <merged and cleared ids> --expect-file .tmp/0b-expect.txt`.
    - Non-zero → re-apply the missing write and re-run, **at most 3 attempts**, then surface the drift; `[GH-UNAVAILABLE]` (exit 3) → surface it, no retry.
  - Do **not** force `status:done` on a standalone issue or epic still at `status:in review` (code shipped but unmerged) — leave it for the human merge.
  - Confirm the parent epic `done` only after its feature PR merged (closed siblings alone are the normal pre-merge state): `set_status` `done` on `BT-<parent>` (local: `close`). Every epic of a `vX.Y.0` release `done` (epics with milestone `vX.Y.0`: github `gh issue list --milestone vX.Y.0 --label tier:epic --state all --json number,state,labels`; local `python .agents/scripts/issues.py list --label tier:epic --milestone vX.Y.0 --all`) → suggest `/3a-version-planning` (it closes the milestones).
  - **Abandoned feature PR:** an open epic whose feature PR (from a child's `Shipped in PR` comment) is CLOSED unmerged (`gh pr view <pr> --json state,mergedAt`) with no open PR on its head branch (`gh pr list --head <branch> --state open`) → prompt: (1) `reopen` the PR's slices (`set_status` `planned`; epic → `planned`) or (2) drop: `set_status` the epic `done` and `close` it as not planned. Confirmation only; Spikes stay closed. Then the gate over the touched ids: `.tmp/0b-expect.txt` with `BT-<n>:status=<new status>` and `python .agents/scripts/reconcile.py --ids <touched> --expect-file .tmp/0b-expect.txt`. Non-zero → re-apply, at most 3 attempts.
- **Post-merge follow-ups:** for each epic or standalone issue detected merged in that same window (never a slice closed at ship), take the PR from its `Shipped in PR #<pr>` comment (epic: any child's; dedupe) and read its `stratos-pr` block (`gh pr view <pr> --json body`, once per PR; none → skip). Per `post_merge` item propose a follow-up issue (title + one line); on confirmation only, `create` it per `references/label-taxonomy.md` composition rules and 3b atomic minting with labels `type:maintenance`, `mode:HITL`, `tier:slice`, `size:small`, `status:planned` (none dropped).
