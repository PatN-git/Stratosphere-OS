---
description: Canonical gh commands for GitHub issue relations (sub-issue parent/child, blocked-by dependencies). Native `gh api graphql`; no `gh-sub-issue` extension.
version: "1.0.0"
timestamp: 2026-07-28
---

# GitHub Issue Relations

No native `gh sub-issue` subcommand or `--blocked-by` flag exists; no extension. Write via `gh api graphql`, read via `--json`. Mutations take node IDs: `ID=$(gh issue view <n> --json id -q .id)`.

**Add sub-issue** (`<child>` under `<parent>`):
`gh api graphql -f query='mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,subIssueId:$c}){issue{number}}}' -f p="$(gh issue view <parent> --json id -q .id)" -f c="$(gh issue view <child> --json id -q .id)"`

**Add blocked-by** (`<issue>` blocked by `<blocker>`):
`gh api graphql -f query='mutation($i:ID!,$b:ID!){addBlockedBy(input:{issueId:$i,blockingIssueId:$b}){issue{number}}}' -f i="$(gh issue view <issue> --json id -q .id)" -f b="$(gh issue view <blocker> --json id -q .id)"`

**Remove blocked-by** (clear `<blocker>` from `<issue>`): as above with `removeBlockedBy`.

**Read:** `gh issue view <n> --json subIssues` | `gh issue view <n> --json blockedBy`

**Fallback** (gh absent / mutation errors on older GHES): keep `Blocked by: <BT-ids>` text in the issue body + `Parent`/`Blocked by` columns of `.memory/BACKLOG_MAP.md`; reconcile later.
