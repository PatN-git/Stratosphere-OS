---
name: 0a-start-session
description: "Initialize session and load context from memory layer. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.2.0"
timestamp: 2026-10-22
---

# START SESSION

## Goal
Restore session context (read-only), then activate: restore the branch and transition the active slice's status.

**Zero Test/Build Invariant:** never run test suites, linters, or build scripts here — `/0a` is administrative context hydration and branch alignment only.

**Pre-check:** if `.memory/` is absent → output exactly `Repository uninitialized. Please run /stratosphere-setup first.` and HALT. This presence check is the only validation here — no skill or suite checks.

## Phase A — Hydrate (read-only)
1. **Resolve the task to resume** from the authoritative active set — the `status:in progress` issues (`wip` read, `references/tracker-verbs.md`; local backend with a remote: run `python .agents/scripts/issues.py sync` first): exactly one → use it; several (concurrent work) → list them and ask which to resume; none → no active task.
2. Run the `load-memory` skill for that task.

## Phase B — Activate (side effects)
1. If no task resolved (`Session Status: no-active-task`) → output next-step guidance (`/1a-research` or `/1b-concept-framing`) and HALT before any side effect.
2. **Branch restore (follow the chosen task, never STATUS):** read the slice's `milestone,parent` and the parent's milestone with one `gh issue view <n> --json milestone,parent` each (local: `issues.py get <id>`), then `python .agents/scripts/pr_body.py unit --slice BT-<padded> --milestone <M> --parent <P> --parent-milestone <PM> --branch <current>` (as 3d step 1; no `--type`/`--slug`).
   - `branch_ok` true → on the unit's branch already; nothing to do. `[SHIP-UNIT-ERROR]` or no active branch matches the unit's `globs` (among local + `origin/` branches, active = no merged PR) → stay on the current branch: `3d` creates it. `needs_milestone` is not a halt here. Several matches → ask which.
   - Another branch matches → `git status --porcelain --untracked-files=no`: changes outside `.memory/` and `.tmp/` → HALT `[DIRTY-TREE] this folder is on <b> with uncommitted changes; resume this task in a separate folder`. A STATUS session line for another task of Phase A's `wip` set holds the current branch → ask before checkout. Else check it out and pull; a failed checkout → HALT with git's message, never stash.
   - **NEVER create a branch** — `3d` owns branch creation; `0a` only restores an existing one.
3. **State transition (first-slice rule):** set the target slice (`BT-XXX`) to `status:in progress` with `set_status` (`references/tracker-verbs.md`); the GitHub form:
   `gh issue edit <n> --remove-label "status:planned" --remove-label "status:needs_spec" --remove-label "status:blocked" --remove-label "status:in review" --remove-label "status:done" --add-label "status:in progress"` (a closed slice is reopened by `/3d-implement-issue`).
   If it is a sub-issue, promote the parent epic (`BT-<parent>`) `planned → in progress` **only if the epic is not already at `in progress`, `in review`, or `done`** (never downgrade a further-along epic). Upsert this session's line in `.memory/STATUS.md` `Sessions` (`BT-n · branch · date`): edit only your own session line, never rewrite the file.

## Output Pattern
Context synced.
- Objective:
- Current state:
- Current branch:
- Next step:
- Needs verification: