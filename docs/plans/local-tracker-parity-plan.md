---
type: plan
title: Local tracker parity with GitHub mode
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-27
version: "1.0.0"
---

# Local tracker parity: plan

Status: decided 2026-10-27; minted as BT-221 (child of epic BT-194, `mode:HITL`, Lifecycle `0 Constitution & Memory`), ships in PR #216 (v5.0.0). Follows BT-194 (PR #216, v5.0.0), where setup asks the user to choose `tracker: github | local`.

## Problem

`tracker: local` is a supported setup answer, but it does less than GitHub mode. The local store is one 9-column table, `.memory/BACKLOG_MAP.md`. It has no issue body and no persistent comments, and no script handles its reads. A local user gets a weaker lifecycle: 4a has no acceptance criteria to audit, and `tracker_switch.py` loses every spec when the project moves to GitHub.

## Gaps in today's local backend (verified in `src/`)

| # | Gap | Evidence | Effect |
|:--|:--|:--|:--|
| G1 | **No persistent issue body.** Acceptance criteria, overview and ICE metrics live only in `.tmp/BT-<padded>-issue-drafts.md` | `tracker-verbs.md:34` (`set_body` → "the drafts file"); `3b-create-issue.md` step 6 deletes the drafts on gate pass | 4a's Business-Logic Auditor reads `### Acceptance Criteria` only through `gh issue view` (`4a-verify-and-ship.md:39`); `load-memory` step 2 reads "GitHub issue body". Locally the spec of a slice is gone once 3b finishes |
| G2 | **Comments go nowhere durable** | `tracker-verbs.md:31`: "append a dated line to the issue's draft file", which is in `.tmp/` | No audit trail and no "Shipped in" trace |
| G3 | **One shared table** | `BACKLOG_MAP.md` template | Every read loads the whole table (BT-189 measured 47k read tokens per 3z slice run in CleanTechHub, against 0.9k for scoped `gh` reads). Any two branches that touch it conflict |
| G4 | **No deterministic reads** | `ice_read.py candidates` is GitHub-only; local `wip`, `list`, `children` and `candidates` are agent scans of the table; local ICE is a stored cell (`3c-sprint-planning.md:34`) | Token cost, read errors and stale ICE; GitHub mode computes ICE on read |
| G5 | **No claim** | `tracker-verbs.md:35`: `claim` → no-op | Two sessions (or 3z and a human) can start the same slice |
| G6 | **Close deletes** | `post-merge-sync.md:15` deletes rows "per retention"; no close reason | Closed work and its rationale disappear; a blocker id can point at nothing |
| G7 | **Second local store for concept maps** | `concept-map-operations.md:45` keeps tickets in `## Tickets` of `docs/discovery/<slug>.map.md` | Two local formats for one concept |
| G8 | **Local mode reads GitHub** | `label-taxonomy.md` §"Label source of truth (local backend only)" syncs the registry with live GitHub labels | Contradicts "GitHub is not touched" (`tracker-verbs.md:14`) |
| G9 | **Backend prose in every workflow** | 48 "local backend …" parentheticals across `src/workflows`, `src/references` and `src/skills` | Text cost and drift risk; the verbs file was meant to hold this |
| G10 | **Lossy migration** | `tracker_switch.py:113` creates each issue with the body "Migrated from local tracker" plus ICE and Refs lines | Specs and comments are lost when a project moves to GitHub |

## What comparable skill sets do

Sources were fetched 2026-10-27 from mattpocock/skills, MrLesk/Backlog.md, steveyegge/beads, eyaltoledano/claude-task-master and github/spec-kit.

| Topic | Matt Pocock (local) | Backlog.md | Beads | Task Master | spec-kit | **StratOS local today** |
|:--|:--|:--|:--|:--|:--|:--|
| Unit of storage | one file per ticket, `.scratch/<feature>/issues/NN-slug.md` | one file per task, `backlog/tasks/` | Dolt DB, JSONL export | one `tasks.json` per tag | one `tasks.md` per feature | one table row |
| Body and acceptance criteria | yes (checkbox ACs) | yes (marked sections: AC, DoD, plan, notes, summary) | `--acceptance`, `--design`, notes | `details`, `testStrategy` | task line only | **no** (`.tmp/`, deleted) |
| Status | `Status:` line | frontmatter | field | field | checkbox | table cell |
| Parent/child | directory | dotted id plus `parentTaskId` | dotted id plus typed edge | nested `subtasks` | phases | `Parent` cell |
| Ready / next query | agent scan ("Frontier") | `task list --ready`, computed | `bd ready` | `task-master next` | file order plus `[P]` | agent scan; ICE stored |
| Claim | `Status: claimed`, saved first | assignee | `--claim`, compare-and-set | — | — | **no-op** |
| Comments | `## Comments`, appended | append-only section | comments | timestamped notes | — | **lost** (`.tmp/`) |
| Close | `## Answer` plus `resolved` | Done, then `archive/` (id kept) | `close --reason` | `set-status done` | `[X]` | Status `done`, row later deleted |
| Writes | agent edits markdown | CLI or MCP only | CLI only | CLI or MCP only | agent edits | agent edits table |
| Backend switch | setup writes `docs/agents/issue-tracker.md`; skills name verbs | — | — | — | `taskstoissues` export | `tracker:` key plus `tracker-verbs.md` (already good) |

**What recurs across them:** one file per issue with status inside it; a body that holds acceptance criteria; a ready query computed on read; claim before work; close with a reason; archive instead of delete; and writes that go through a tool (or a strict template) rather than free editing.

**StratOS is already ahead on:** the backend abstraction (`tracker-verbs.md` gives each verb a GitHub form and a local form, the same idea as Pocock's "publish/fetch"), the label taxonomy, blocker-clearing rules (`reconcile.py --edges`), and a one-way switch to GitHub.

## Recommendation

Keep the verbs contract and the `BT-LOCAL-<slug>` id. **Replace the table with one markdown file per issue, and add one small script that handles every local verb and read.** The local issue file holds exactly what a GitHub issue holds, so workflows, auditors and the switch script see the same thing on both backends.

### 1. One file per issue (Pocock, Backlog.md)

`docs/issues/BT-LOCAL-<slug>.md`, tracked in git (decision D1):

```markdown
---
id: BT-LOCAL-login-form
title: Login form with email magic link
status: planned
labels: [type:feature, mode:AFK, tier:slice, size:medium, priority:high, scope:baseline, area:FE-login]
milestone: v1.0.0
parent: BT-LOCAL-auth-epic
blocked_by: [BT-LOCAL-session-store]
claimed_by: null
created: 2026-10-27
closed: null          # date, set by close
close_reason: null    # completed | not planned
---
<the body from references/issue-templates.md, verbatim: Overview, Acceptance Criteria, ICE metrics (I:/C:), Refs: line, Blocked by line>

## Comments
- 2026-10-27: Shipped in commit abc1234 on improvement/BT-LOCAL-auth-epic-…
```

- The body is the same text 3b would post to GitHub. G1 closes: 4a and `load-memory` read `### Acceptance Criteria` from the file. G10 closes: `tracker_switch.py` posts the body verbatim.
- `ICE` and `Ref` stop being cells. ICE is computed on read from `I:`/`C:` and `size:`, as in GitHub mode (this removes the `set_ice` misfit). Refs is the body's `Refs:` line, as in GitHub mode.
- The folder holds `docs/issues/README.md`: the project's `area:*` slugs (today's map Label Registry) and a pointer to `label-taxonomy.md`. It holds no issue list. G8 closes: the local registry is this file and never syncs with GitHub.
- Closed issues move to `docs/issues/archive/` and keep their id (Backlog.md). Nothing is deleted. Blocker checks read the archive too (G6).
- Resume notes stay in gitignored `.memory/resume/<id>.md` (decided in BT-218).

### 2. One script for local verbs and reads (Backlog.md, Beads, Task Master)

Add `src/scripts/issues.py`. It does every local read and write and prints the same JSON shapes the `gh … --json` reads return, so a workflow parses one shape on both backends.

| Kind | Commands |
|:--|:--|
| Reads | `get <id>`, `list [--label] [--status] [--milestone]`, `wip`, `children <id>`, `blockers <id>`, `ready` |
| Writes | `create --title --labels --milestone --parent --body-file` (returns the id; adds `-2`, `-3` … on a slug collision, archive included), `set <id> --status/--add-label/--remove-label/--milestone/--parent/--blocked-by`, `comment <id> --body`, `claim <id>`, `close <id> --reason`, `reopen <id>` |
| Check | `check`: one `status:*` per issue, label composition, known labels, parent exists, blocked-by acyclic, every id resolves |

- `ready` covers 3c's `candidates` and 3z's queue (G4). It returns open leaf issues at `planned` or `needs_spec` whose blockers have cleared, with ICE computed on read. It reuses `ice_read.parse_metrics` and `reconcile`'s edge rule, not copies of them. It fails closed on an unknown blocker id (Backlog.md).
- `claim` is compare-and-set (Beads): it fails if the issue is already `in progress` or claimed, sets `status: in progress` plus `claimed_by: <branch>`, and saves before any work starts (G5).
- `close` sets the status, date and reason, appends the final comment, and moves the file to `archive/` (G6).
- `set_status` keeps the Single Status Invariant in code, not prose.
- Agents never hand-edit frontmatter (all three CLI tools have this rule). Writing the body for `create` (the 3b draft) stays a normal file write.

### 3. Workflows name verbs only (Pocock)

- In `tracker-verbs.md`, each local-form cell becomes a single `issues.py` call. Its Misfits section drops `set_ice`, `set_body`, `claim` and the comment gap.
- The 48 "local backend …" parentheticals are removed wherever the verb or read now covers them (G9). This needs a measured net text change; see memory "always-loaded text budget".
- 3b mints local issues with `issues.py create --body-file` from the approved draft. The drafts are deleted only after that, as today.
- Concept maps use the same issue files: the map issue carries `concept:map` and its decision tickets are children with `concept:*` labels. The `## Tickets` second store goes (G7).
- `BACKLOG_MAP.md` is retired. `reconcile.py --edges` and `resolve_backend` read `docs/issues/` (with no `tracker:` key, a present `docs/issues/` means local).

### 4. Migration and switch

- A one-shot `migrate_map_to_issues.py` turns a v5 map into issue files, pulling each body from any surviving draft or spec file, otherwise from the row. It ships for one release and is then deleted (memory "no token-bloat migrations"). `stratosphere-update` runs it once when it finds a map and no `docs/issues/`.
- `tracker_switch.py` reads issue files: it posts the body verbatim and the `## Comments` as one comment, and creates archived issues as closed issues so blocker history survives.

### Not adopted

- **Database or JSON store** (Beads' Dolt, Task Master's `tasks.json`): they need a binary or another runtime, and a single JSON file brings back the merge conflicts the per-file layout removes.
- **MCP server or web UI** (Backlog.md): a script is enough, and every host can run it.
- **Ids numbered per feature** (Pocock `01`, `02`): ids would not be unique across features, but branch names and commits need a global `BT-…` id.
- **Hash ids** (Beads): `BT-LOCAL-<slug>` is already collision-resistant across branches, readable, and was just settled in BT-194.
- **Triage roles** (Pocock `needs-triage`, `ready-for-agent`): `status:*` plus `mode:HITL|AFK` already covers them.
- **A generated index table for humans**: it is a sync layer, which BT-189 rejected for the same reason. `issues.py list` replaces it (decision D3).

## Branch staleness (D4)

If issue files live in the working tree, they are versioned per branch. A ticket created on branch A, or a status change made there, is invisible on branch B and on `main` until A merges. Today's map has the same flaw. BT-189 named this "branch dimension" as a root failure mode, and GitHub mode avoids it because GitHub issues have no branch.

| Option | How | Fixes | Costs |
|:--|:--|:--|:--|
| **A. Tracker ref** (recommended) | Issue files live at `docs/issues/` on a dedicated branch `<repo>/issues`, never in feature branches. `issues.py` writes with git plumbing (temporary index, `commit-tree`, then `update-ref` with the old value as a compare-and-set), so no checkout is needed. Reads use `git cat-file --batch`. Similar idea: Beads' `refs/dolt/data`, git-bug | One state for every branch and worktree, as on GitHub. Atomic claim comes free from the ref compare-and-set. No merge conflicts on issue files. The switch to GitHub reads one ref | About 100 lines of plumbing in `issues.py`. Issue changes leave the feature PR diff (the same as GitHub mode). Humans browse with `issues.py list` or `git worktree add`. Multi-machine use needs a push rule for `<repo>/issues` in AGENTS §4 |
| B. Read across branches | Files stay in the working tree. `issues.py` reads `docs/issues/` from every local and remote-tracking branch, merges by id (newest `updated` wins) and shows the source branch; `create` checks ids on all branches. A `.gitattributes` merge driver resolves issue-file conflicts the same way. Similar idea: Backlog.md `checkActiveBranches` | Roadmap visible from any branch; id collisions caught | A sync layer again (newest-wins rules, merge driver), the kind BT-189 measured as the main incident source. It sees committed state only |
| C. Store in the git common dir | `$(git rev-parse --git-common-dir)/stratos/issues/`: shared by all branches and worktrees, never versioned | Zero merge issues, no machinery | Not pushed, not backed up, gone on a fresh clone, no history |
| D. Plan on `main` only (rejected) | 3b/3c commit issue files to the default branch (extending the 2a/2b/3a documentation-artifact exception); status changes stay on feature branches | New tickets visible after a pull of `main` | Branch switching under concurrent sessions in one folder; statuses still diverge; widens the "nothing else pushes to the default branch" rule |

## Slices (proposed epic, not minted)

| Slice | Content | Blocked by | Size |
|:--|:--|:--|:--|
| S1 | Issue-file format (OKF `type: issue` in `okf-protocol.md`), `docs/issues/README.md` template, `issues.py` reads (`get`, `list`, `wip`, `children`, `blockers`, `ready`) with gh-shaped JSON; unit tests | — | medium |
| S2 | `issues.py` writes (`create`, `set`, `comment`, `claim`, `close` plus archive, `reopen`) and `check`; `validate_memory`/lint hook | S1 | medium |
| S3 | Rewire: `tracker-verbs.md` local column; 3b, 3c, 3d, 3z, 4a, 0a, 0b, `load-memory`, `post-merge-sync`; concept-map operations; label-taxonomy local section; remove the parentheticals (measured) | S2 | large |
| S4 | `reconcile.py` and `resolve_backend` read `docs/issues/`; `tracker_switch.py` reads files (body, comments, closed); one-shot map migration; scaffold, setup and update; retire the `BACKLOG_MAP.md` template | S2 | medium |
| S5 | Lifecycle harness scenario on the local backend, end to end: 3b → 3c → 3d → 4a audit-only → 0b close plus switch dry run; release notes | S3, S4 | medium |

**Done when** the harness runs one slice end to end on `tracker: local`, with acceptance criteria read by the 4a auditor, the slice claimed, closed with a reason and archived, a blocker cleared and `ready` re-computed. A `tracker_switch.py --apply` dry run must reproduce each body byte for byte.

### Option A: lessons from tools that keep state off feature branches (fetched 2026-10-27)

| Lesson | Source | Design consequence |
|:--|:--|:--|
| Keeping state off feature branches gives every worktree and checkout one state | Beads: issue changes "are not committed to the current Git branch" | The store is a ref, never a working-tree folder |
| Hidden sync worktrees cause stale branch locks | Beads removed its `sync.branch` worktrees (`.git/beads-worktrees/`) | Writes use plumbing only; no worktree for the tracker branch |
| Compare-and-set on the ref is the concurrency primitive and must follow git's `.lock` protocol, not flock | git-bug `UpdateRef(old, new)`, reimplemented after go-git bugs | Shell out to `git update-ref <ref> <new> <old>` (the git binary does the lock); on a lost race, re-read and retry, never force |
| Custom ref namespaces need their own refspecs | git-bug `refs/bugs/*`, Beads `refs/dolt/data` | Use a normal branch `refs/heads/<repo>/issues`: default fetch and push cover it, and `gh`/GitHub can browse it |
| Divergence needs a defined merge | git-bug op-log CRDT; git-appraise line-per-item `cat_sort_uniq`; Beads cell-level; Backlog.md whole-file newest wins | One file per issue already makes most divergence a clean 3-way merge (different files). Same-file conflicts: frontmatter fields newest-`updated` wins, `## Comments` lines are a union. `issues.py sync` does this; no CRDT |
| Sync explicitly at session boundaries, not on every write | Beads ("sync before and after work sessions"), git-bug, git-appraise | `0a` fetches and merges `<repo>/issues`; the ref is pushed with the 4a ship push (behind the existing HITL confirmation) and by `0b` when a remote exists. Single-machine use never syncs |
| Sequential ids race across clones even with a fresh fetch; content-hash ids do not | Backlog.md `doctor --fix` renumbers; git-bug, Beads hash ids | `BT-LOCAL-<slug>` stays; a slug clash after a merge is a `check` finding that suffixes `-2` |
| Snapshot imports cannot express deletes | Beads' reason for dropping JSONL sync | No export/import layer; close is an explicit move to `archive/` |

## Open decisions

- **D1 Location.** Decided 2026-10-27: `docs/issues/`.
- **D2 Release.** Decided 2026-10-27: ships in PR #216 / v5.0.0.
- **D3 Human index.** Decided 2026-10-27: none; `issues.py list` replaces it.
- **D4 Branch staleness.** Decided 2026-10-27: option A, built to the lessons table above. The branch is `<repo>/issues` (user decision: no StratOS name in consumer repos); `<repo>` is the `origin` URL's last segment, else the top-level folder name, recorded by setup as `tracker_branch:` in `.memory/ARCHITECTURE.md`.
