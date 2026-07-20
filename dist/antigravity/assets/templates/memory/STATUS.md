---
type: status
title: Status
description: Per-session resume hint (last focus, next step). NOT the authoritative active-work set.
timestamp: 2026-07-17
version: "1.0.3"
---
# STATUS

> Per-working-directory resume hint — best-effort, local (gitignored), single-session. **Not** the source of truth for what's active: the authoritative in-flight set is the `status:in progress` issues in `.memory/BACKLOG_MAP.md`/GitHub (supports many concurrent tasks). For concurrent sessions (e.g. several `/3z` runs plus your own), use separate git worktrees so each keeps its own STATUS.md.

- **Last Sync:**
- **Current Branch:**
- **Active Issue / PRD:** <!-- this session's focus; a hint, not the global active set -->
- **Current Focus:**
- **Completed This Session:**
- **Open/Active Task Brief:**
- **Blocker (if any):**
- **Next Immediate Step:**
