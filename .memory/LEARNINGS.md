---
type: learnings
title: Learnings
description: Episodic project-specific lessons and insights.
generated:
  by: 0b-stop-session
  at: 2026-10-22
version: "1.0.3"
---
# LEARNINGS

## Purpose
<!-- SOS:BLOCK id=learnings-guidance v=1.1.0 -->

Episodic memory for project-specific lessons likely to matter again. Each entry carries a unique `L-xxx` ID, a trust tag, and (where applicable) a `Source: BT-xxx` cross-reference.

> Trust tags, supersession, and cross-reference rules → `.agents/rules/memory-protocol.md`.
> **PRESERVATION RULE:** Do NOT delete the format example line under `## Superseded` during setup or when adding entries. Keep it as a placeholder until real superseded entries exist.

## What belongs here
- API constraints discovered the hard way
- Auth / RLS gotchas
- Setup pitfalls
- Recurring edge cases
- Framework-specific traps

## What does NOT belong here
- Temporary TODOs → the tracker (`.agents/scripts/tracker.py`)
- Current task status → the issue's resume note
- One-off debugging logs unless they reveal a reusable rule
- `[LAW]`-tier rules → `ARCHITECTURE.md` or `DESIGN_RULES.md`
- Domain vocabulary → `GLOSSARY.md`

<!-- SOS:/BLOCK id=learnings-guidance -->

## Active Entries

- **[[L-001]] [ASSUMED] [2026-10-09]** Scaffold update tests in `tests/framework/test_update_flow.py` only examine files listed in the mock plugin's `versions.json`, and `setup_mock_plugin` lists only `BACKLOG_MAP.md`. A new test for a skill or constitution file must write its own manifest entry, or it passes even without the fix. Also add the test to the file's `__main__` list, which `tests/runners/verify_scripts.py` runs. Source: BT-154.
- **[[L-002]] [ASSUMED] [2026-10-16]** `commit(repo, subject, files)` in `tests/conftest.py` overwrites every listed file with `subject` plus random hex before committing, so any fixture content you wrote to those files first is destroyed. To commit real fixture content, write the files yourself, then run `git add -A` and `git commit` through the `git(repo, ...)` helper. Source: BT-187.
- **[[L-004]] [ASSUMED] [2026-10-22]** Rewriting a tracked file from Python in text mode on Windows (`open(p, "w")`) converts its LF line endings to CRLF and shows up as a whole-file diff; open it with `newline="\n"` or use the Edit tool. In a Bash heredoc, `\n` inside a Python string also becomes a real newline, which broke `floor_guard.py` once. Source: BT-214.

## Superseded
> Read only when explicitly asked.

- **L-XXX [SUPERSEDED BY L-YYY] [YYYY-MM-DD]** Original entry preserved. Reason: one line. Version: v0.X → v0.Y.
- **[[L-003]] [SUPERSEDED BY [[A-007]]] [2026-11-12]** Stratosphere-OS itself does not use GitHub milestones (the framework's `vX.Y.Z` release and sprint milestones from 3a/3b/3c are for consumer projects); none exist in this repo. 3d's `[NO-RELEASE]` halt (an epic's slice with no milestone) is therefore expected here: override it in chat and use the epic branch `<type>/BT-<parentPadded>-<slug>`. Slices of one epic ship in one PR. Reason: promoted to [LAW] in ARCHITECTURE.md (do not prompt `[NO-RELEASE]` alert here).
