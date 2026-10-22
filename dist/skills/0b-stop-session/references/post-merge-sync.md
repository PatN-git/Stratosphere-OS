---
description: Merge-time GitHub bookkeeping for 0b step 1: done detection, unblocking dependents, parent epic and release, abandoned feature PR, post-merge follow-ups. Read only when the 0b gate fires.
version: "1.1.0"
timestamp: 2026-10-22
---

# Post-merge sync

Verbs (`set_status`, `close`, `reopen`, `clear_blocker`, `create`) and the backend rule are in `references/tracker-verbs.md`. In GitHub mode nothing here reads or writes `.memory/BACKLOG_MAP.md`; the local backend's map steps are marked.

- **Done detection (no forcing):** an epic or standalone issue is `done` only once its PR has **merged** and the issue auto-closed. A child slice is already `done` + closed at 4a ship.
  - For each epic/standalone issue **merged** this session (the ids come from the PR query 0b ran): `set_status` `done` (the merge closed it; local backend: mark its `BACKLOG_MAP.md` Status `done`).
  - Then clear the edges that waited on it:
    - github: `python .agents/scripts/reconcile.py --ids <merged ids> --edges dependents` (`--all-open` is a map-only run). Clear every `[CLEAR]` edge by running its `cmd:` (`clear_blocker`, `removeBlockedBy` per `references/github-issue-relations.md`); leave `[KEEP]`.
    - local backend: before deleting any row (per retention), run `python .agents/scripts/reconcile.py --edges dependents --all-open` and clear every `[CLEAR]` edge. Remove the bare ID from that dependent's `Blocked by` in `.memory/BACKLOG_MAP.md`. Then run its `cmd:` (`removeBlockedBy` per `references/github-issue-relations.md`); leave `[KEEP]`.
    - Offline → every edge is KEEP; say so in the handoff `Blockers` line.
  - **Gate** (`references/terminal-sync-invariant.md`), over the merged issues and every dependent cleared:
    - github: write the intended end state to `.tmp/0b-expect.txt` (`BT-<n>:status=done` per merged issue, `BT-<d>:blocked_by=<its blockers minus the cleared>` per dependent, its blockers read with `gh issue view <d> --json blockedBy`; `--edges dependents` lists only the edges to the merged ids), then run `python .agents/scripts/reconcile.py --require-gh --ids <merged and cleared ids> --expect-file .tmp/0b-expect.txt`.
    - local backend: `python .agents/scripts/reconcile.py --require-gh --ids <cleared dependents> --fields blocked_by`.
    - Non-zero → github: re-apply the missing write; local: heal per the reference. Re-run, **at most 3 attempts**, then surface the drift; `[MIRROR-UNVERIFIED]` → surface it, no heal.
  - Do **not** force `status:done` on a standalone issue or epic still at `status:in review` (code shipped but unmerged) — leave it for the human merge.
  - Confirm the parent epic `done` only after its feature PR merged (closed siblings alone are the normal pre-merge state): `set_status` `done` on `BT-<parent>` (local backend: reconcile its `BACKLOG_MAP.md` row). Every epic of a `vX.Y.0` release `done` → suggest `/3a-version-planning` (it closes the milestones).
  - **Abandoned feature PR:** an open epic whose feature PR (from a child's `Shipped in PR` comment) is CLOSED unmerged (`gh pr view <pr> --json state,mergedAt`) with no open PR on its head branch (`gh pr list --head <branch> --state open`) → prompt: (1) `reopen` the PR's slices (`set_status` `planned`; epic → `planned`) or (2) drop: `set_status` the epic `done` and `close` it as not planned. The local backend's rows follow the same statuses in `BACKLOG_MAP.md`. Confirmation only; Spikes stay closed. Then the gate over the touched ids: github → `.tmp/0b-expect.txt` with `BT-<n>:status=<new status>` and `python .agents/scripts/reconcile.py --require-gh --ids <touched> --expect-file .tmp/0b-expect.txt`; local backend → `python .agents/scripts/reconcile.py --require-gh --ids <touched> --fields status`. Non-zero → re-apply (github) or heal per `references/terminal-sync-invariant.md` (local), at most 3 attempts.
- **Post-merge follow-ups:** for each epic or standalone issue detected merged this step (never a slice closed at ship), take the PR from its `Shipped in PR #<pr>` comment (epic: any child's; dedupe) and read its `stratos-pr` block (`gh pr view <pr> --json body`; none → skip). Per `post_merge` item propose a follow-up issue (title + one line); on confirmation only, `create` it per `references/label-taxonomy.md` composition rules and 3b atomic minting with labels `type:maintenance`, `mode:HITL`, `tier:slice`, `size:small`, `status:planned` (none dropped); local backend: add its `BACKLOG_MAP.md` row in the same step.
