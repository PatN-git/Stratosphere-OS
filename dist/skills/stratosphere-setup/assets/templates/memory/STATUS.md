---
type: status
title: Status
description: Folder state only (last merge sync, one session line per task in this folder, repo notes, blocker). Never issue state.
stale_after: <ISO 8601>   # the document hint only; session lines age out by their own date (0b)
generated:
  by: stratosphere-setup
  at: 2026-10-27
version: "2.0.0"
---
# STATUS

> Folder state only, local (gitignored). Issue state (title, status, next step) lives in the tracker; a task's progress and next step are its resume note on the issue. Sessions in one folder share its checked-out branch: work on another branch in a separate folder with its own `.memory/`. Edit only your own session line or a single field; never rewrite the whole file or add history.

- **Last Sync:**
- **Sessions:** <!-- one line per task in this folder: `BT-n · branch · date` -->
- **Repo notes:** <!-- folder-local caveats only (stale scripts, shell quirks, lint toolchain not provisioned) -->
- **Blocker (if any):**
