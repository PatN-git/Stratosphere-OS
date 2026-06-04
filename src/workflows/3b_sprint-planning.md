---
name: 3b_sprint-planning
description: Scans BACKLOG_MAP & GitHub, filters by dependencies/priority, sequences a 10-day capacity block into GitHub phases.
type: workflow HITL
trigger: User. Do not run autonomously.
---

# Sprint Planning

**Hand-off contract:** Modifies `.memory/BACKLOG_MAP.md` and assigns GitHub issues to a milestone in format `x.yy` (`x` = version, `yy` = sprint).

## Phase 1: Context Intake & Triage Scan
1. Read `.memory/BACKLOG_MAP.md` if not already loaded.
2. Extract rows where `status != done`.
3. **Audit Strategy:**
   - Map matching active GitHub issues. If a GitHub issue lacks an entry in `BACKLOG_MAP.md` or lacks both `type:xxx` and `size:xxx` labels → immediately exclude and print: `[NEEDS_SPEC] BT-<n> - <title>`.
   - List all existing issues labelled as `[NEEDS_SPEC]` to surface to user.

## Phase 2: Filter & Sort Engine
1. **Dependency Sorting:** Evaluate dependency chains (`Blocked by`). If prerequisites are not `status: done` → tag candidate item `[BLOCKED]`.
2. **Priority Array:** Sort all remaining unblocked candidate items by priority weighting: `high` → `medium` → `low`.
3. **Context Grouping:** Cluster sequenced tasks matching identical `area:xxx` tags to compress token burn overhead.

## Phase 3: Capacity Calculation & Safeguards
*Max Sprint Budget = 10 engineering days (80 hours total).*
- **Cost Weights:** `size:large` = 12 hours | `size:medium` = 6 hours | `size:small` = 1 hour.
- **Guardrail Protocol:** Identify all issues containing BOTH `size:large` and `type:AFK`. Flag these items explicitly asking for confirmation.

## Phase 4: Sequence Proposal
Output a compressed structural readout of items matching capacity thresholds and an explicit order if needed:

```markdown
[TARGET SPRINT MILESTONE: <x.yy>]

- [AFK] BT-<n> | <title> (<size>) | Area: <area> | Type: <type> | Priority: <priority>
- [HITL] BT-<n> | <title> (<size>) | Area: <area> | Type: <type> | Priority: <priority>

[CRITICAL ALERTS]
⚠️ WARNING: BT-<n> is size:large but labeled type:AFK. Confirm auto-execution!
🗒️ Note: BT-<n> labeled `[NEEDS_SPEC]` must be enriched before inclusion in sprint planning.
```

## Phase 5: Commit & Synch

Halt execution. Prompt user for confirmation. When confirmed:
1. Update issue metadata directly inside GitHub.
2. Ensure milestone <x.yy> exists, assign matching issues, set status:planned inside .memory/BACKLOG_MAP.md and GitHub.
3. Output termination note: Sprint <x.yy> locked. Ready for execution.