---
description: Path rules that tag a PR as a hard-to-reverse change (`risk:one-way`). Matched against the PR's changed paths by 4a Phase 5; path rules only, never agent judgement.
version: "1.0.0"
timestamp: 2026-10-05
---

# Merge Risk Paths

A change that is hard to undo after merge (a database migration, a CI pipeline) must be read by a human before it lands. Detection is **mechanical**: match each path of `git diff --name-only <base>...HEAD` (`<base>` resolved as in 4a Phase 2) against the rules below. A matching path adds its tag to the PR's `risk:` list. No tag fires → `risk: [none]`.

| Path rule | Risk tag |
|---|---|
| `**/*.sql`, `**/migrations/**` | `db-migration` |
| `.github/workflows/**` | `ci` |

`**` spans directories (`**/*.sql` also matches a root-level `x.sql`). Rows are `<glob> → <tag>`; several globs in one cell share the tag.

## Project extensions
A project adds its own rules (e.g. scripts that write to live systems) as `<glob> → <tag>` lines under a `## One-way paths` heading in `.memory/ARCHITECTURE.md`. Read that section if present; the rules apply exactly as the table above. Nothing here is judged by the agent: if no glob matches, no tag fires.

## Consequence
Any tag other than `none` → label the PR `risk:one-way` (4a Phase 5 step 5) and name it in the ship output line.
