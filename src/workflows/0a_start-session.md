---
name: 0a_start-session
description: Initialize session and load context from memory layer.
type: workflow HITL
trigger: manual
version: "1.1.1"
timestamp: 2026-07-17
---

# START SESSION

## Goal
Restore session context (read-only), then activate: restore the branch and transition the active slice's status.

## Phase A — Hydrate (read-only)
Run `.agents/skills/load-memory/SKILL.md` to restore session context.

## Phase B — Activate (side effects)
1. If Phase A returned `Session Status: no-active-task` → output next-step guidance (`/1a_research` or `/1b_concept-framing`) and HALT before any side effect.
2. **Branch restore:** read STATUS `Current Branch`. If active/unmerged feature branch and repo not on it → check it out; if merged/unset → checkout default and pull. **NEVER create a branch** — `3d` owns branch creation; `0a` only restores an existing one.
3. **State transition (first-slice rule):** set the target slice (`BT-XXX`) to `status:in progress` in `.memory/BACKLOG_MAP.md` and GitHub:
   `gh issue edit <n> --remove-label "status:planned" --remove-label "status:needs_spec" --remove-label "status:blocked" --remove-label "status:in review" --add-label "status:in progress"`.
   If it is a sub-issue, promote the parent epic (`BT-<parent>`) `planned → in progress` **only if the epic is not already at `in progress`, `in review`, or `done`** (never downgrade a further-along epic). Update `Active issue` in `.memory/STATUS.md`.

## Output Pattern
Context synced.
- Objective:
- Current state:
- Current branch:
- Next step:
- Needs verification: