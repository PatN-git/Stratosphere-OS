---
description: Path rules that tag a PR as a hard-to-reverse change (`risk:one-way`). Matched against the PR's changed paths by 4a Phase 5; path rules only, never agent judgement.
version: "1.0.0"
timestamp: 2026-10-05
---

# Merge Risk Paths

Hard-to-undo changes (database migration, CI pipeline) need a human read before merge. Detection is **mechanical**: match each path of `git diff --name-only <base>...HEAD` (`<base>` per 4a Phase 2) against the rules below; a match adds its tag to the PR's `risk:` list. No match → `risk: [none]`.

| Path rule | Risk tag |
|---|---|
| `**/*.sql`, `**/migrations/**` | `db-migration` |
| `.github/workflows/**` | `ci` |

`**` spans directories (`**/*.sql` also matches a root-level `x.sql`). Rows are `<glob> → <tag>`; several globs in one cell share the tag.

## Project extensions
Projects add rules (e.g. scripts writing to live systems) as `<glob> → <tag>` lines under `## One-way paths` in `.memory/ARCHITECTURE.md`; read it if present, rules apply as in the table. No agent judgement: no glob match, no tag.
