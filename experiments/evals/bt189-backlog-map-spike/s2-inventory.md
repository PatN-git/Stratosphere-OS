# BT-189 s2 - BACKLOG_MAP inventory (analyst A2)

Scope: `src/` only (excludes `dist/`, `.agents/`, `.claude/worktrees/`). Read-only analysis. Line numbers are `src/` as of branch `feat/BT-190-lifecycle-status-pr-scope`.

## A. Site inventory

Kinds: `read` | `mirror write` | `local-only write` | `gate/heal` | `rule/definition`. Disposition: `removable` (a GitHub write/read already exists) | `needs GitHub equivalent (<what>)` | `offline-only`.

| # | file:line | kind | field(s) touched | disposition | note |
|--:|:--|:--|:--|:--|:--|
| 1 | `workflows/0a-start-session.md:23` | read | status | removable | active set = `status:in progress` issues; `gh issue list --label` gives it |
| 2 | `workflows/0a-start-session.md:29-31` | mirror write | status (+ parent epic status) | removable | `gh issue edit` literal at :30 |
| 3 | `workflows/0b-stop-session.md:27 (a)` | mirror write | status=done; blocked_by clear | removable | `removeBlockedBy` cmd printed by `reconcile --edges` |
| 4 | `workflows/0b-stop-session.md:27 (b)` | local-only write | row delete (retention) | removable | moot without a map; retention rule not defined anywhere in src |
| 5 | `workflows/0b-stop-session.md:28` | gate/heal | blocked_by | removable | reconcile gate after clear |
| 6 | `workflows/0b-stop-session.md:30` | mirror write | status=done (parent epic) | removable | merge auto-close + board Action |
| 7 | `workflows/0b-stop-session.md:31 (a)` | mirror write | status, reopen/close | removable | `gh issue reopen`/`close --reason "not planned"` literal |
| 8 | `workflows/0b-stop-session.md:31 (b)` | gate/heal | status | removable | `reconcile --fields status` |
| 9 | `workflows/0b-stop-session.md:32` | mirror write | new row: labels, status:planned, milestone | removable | issue created on GitHub in same step; `BT-LOCAL` not covered |
| 10 | `workflows/0d-nightly-consolidation.md:48-53` | gate/heal | all 5 mirror fields | removable | Phase 3.6 drift check; vanishes with the mirror |
| 11 | `workflows/0d-nightly-consolidation.md:73-75` | gate/heal | all 5 (map cells written from gh) | removable | `reconcile --heal` |
| 12 | `workflows/1b-concept-framing.md:36` | read | whole map | removable | Load Memory step |
| 13 | `workflows/1b-concept-framing.md:39` | read | title/labels (overlap scan) | removable | `gh issue list --search` |
| 14 | `workflows/1c-concept-map.md:37` | mirror write | map row (concept:map, status, milestone-exempt) | removable | `gh issue create` literal in concept-map-operations.md:22 |
| 15 | `workflows/1c-concept-map.md:38` | local-only write | BT-LOCAL row + `.map.md` file | offline-only | offline tracker form of create issue |
| 16 | `workflows/1c-concept-map.md:90` | mirror write | status=done | removable | `gh issue close` at :90 |
| 17 | `workflows/2a-write-prd.md:21` | read | whole map | removable | load |
| 18 | `workflows/2a-write-prd.md:33` | rule/definition | minting rule (never scan map) | removable | rule persists as 'id from `gh issue create`'; map clause drops |
| 19 | `workflows/2a-write-prd.md:45` | read | rows (synthesis input) | removable | `gh issue list` |
| 20 | `workflows/2a-write-prd.md:96-100` | mirror write | Status, Labels, Milestone (provisional v1.0.0), ICE `-`, Ref | needs GitHub equivalent (Ref; provisional milestone is map-only, GitHub epic has none until 3a) | row has 9 cols; only Ref is not on GitHub |
| 21 | `workflows/2a-write-prd.md:107` | rule/definition | Label Registry pointer | removable | `gh label list` |
| 22 | `workflows/2b-interface-design.md:26` | mirror write | status needs_spec->planned | removable | `gh issue edit` literal |
| 23 | `workflows/2b-interface-design.md:103` | mirror write | status needs_spec->planned | removable | `gh issue edit` literal |
| 24 | `workflows/2b-interface-design.md:106` | local-only write | Ref (memory ids) | needs GitHub equivalent (Ref) | no GitHub field; doc paths already live in the body |
| 25 | `workflows/2b-interface-design.md:110` | rule/definition | provisional milestone note | needs GitHub equivalent (other: provisional milestone) | drop 2a's map-only milestone or write it on GitHub |
| 26 | `workflows/3a-version-planning.md:35` | read | whole map | removable | load |
| 27 | `workflows/3a-version-planning.md:36` | read | labels (tier:epic exists?) | removable | `gh issue list --label tier:epic` |
| 28 | `workflows/3a-version-planning.md:41` | read | milestone (numbering fallback) | removable | GitHub milestones are the 2nd authority already |
| 29 | `workflows/3a-version-planning.md:57` | read | rows (auditor input) | removable | `gh issue view` |
| 30 | `workflows/3a-version-planning.md:71` | mirror write | milestone (epics) | removable | milestone create/assign on GitHub in same step |
| 31 | `workflows/3a-version-planning.md:72` | mirror write | blocked_by | removable | `addBlockedBy` |
| 32 | `workflows/3a-version-planning.md:74` | gate/heal | milestone, blocked_by | removable | reconcile gate |
| 33 | `workflows/3b-create-issue.md:24` | mirror write | status needs_spec->planned | removable | `gh issue edit` literal |
| 34 | `workflows/3b-create-issue.md:30` | read | Parent rows (siblings) | removable | `gh issue view --json subIssues` is the primary |
| 35 | `workflows/3b-create-issue.md:101` | rule/definition | `BT-LOCAL-<n>` offline fallback | offline-only | id minting offline |
| 36 | `workflows/3b-create-issue.md:111` | mirror write | blocked_by (+ body text) | removable | `addBlockedBy` |
| 37 | `workflows/3b-create-issue.md:112-115` | mirror write | full row: status, labels, milestone, parent, blocked_by, ICE, Ref | needs GitHub equivalent (ICE, Ref) | ICE raw metrics already in body (:101); Ref has no GitHub home |
| 38 | `workflows/3b-create-issue.md:116` | gate/heal | all 5 | removable | reconcile gate (fresh rows) |
| 39 | `workflows/3b-create-issue.md:123` | rule/definition | Label Registry + write new label to registry | removable | `gh label list`/`create` |
| 40 | `workflows/3c-sprint-planning.md:21` | read | whole map | removable | load |
| 41 | `workflows/3c-sprint-planning.md:26` | gate/heal | map entry + labels present ([MISSING-LABELS]) | removable | 'lacks map entry' clause vanishes; label check = `gh issue view` |
| 42 | `workflows/3c-sprint-planning.md:29` | read | blocked_by (fallback) | removable | `gh issue list --json blockedBy` is primary |
| 43 | `workflows/3c-sprint-planning.md:34` | read | ICE | needs GitHub equivalent (ICE) | recompute from body raw metrics + size label |
| 44 | `workflows/3c-sprint-planning.md:64` | rule/definition | [MISSING-LABELS] note | removable | wording only |
| 45 | `workflows/3c-sprint-planning.md:72` | mirror write | labels (priority:*) | removable | label edit on GitHub; no literal command |
| 46 | `workflows/3c-sprint-planning.md:73` | mirror write | milestone (sprint digit Z), status | removable | sprint digit = GitHub milestone `vX.Y.Z`; no extra equivalent |
| 47 | `workflows/3c-sprint-planning.md:74` | mirror write | blocked_by | removable | `addBlockedBy` |
| 48 | `workflows/3c-sprint-planning.md:76` | gate/heal | status, milestone, labels, blocked_by | removable | reconcile gate |
| 49 | `workflows/3d-implement-issue.md:22` | read | milestone, parent | removable | `gh issue view --json milestone,parent` fallback exists |
| 50 | `workflows/3d-implement-issue.md:26` | mirror write | status in progress (+ epic) | removable | `gh issue edit` literal |
| 51 | `workflows/3d-implement-issue.md:51` | read | requirement bare ids | removable | or issue (already 'map/issue') |
| 52 | `workflows/3z-afk-loop.md:30` | read | queue (status, ids) | removable | `gh issue list` |
| 53 | `workflows/3z-afk-loop.md:34` | read | exists + status | removable | `gh issue view` |
| 54 | `workflows/3z-afk-loop.md:40` | read | milestone, parent (unit key) | removable | as 3d:22 |
| 55 | `workflows/3z-afk-loop.md:51-53` | mirror write | status in progress (slice, parent epic) | removable | `gh issue edit` literal :52 |
| 56 | `workflows/3z-afk-loop.md:73` | mirror write | status=blocked | removable | `gh issue edit` + `gh issue comment` literals |
| 57 | `workflows/3z-afk-loop.md:77` | mirror write | status=blocked | removable | `gh issue edit` literal |
| 58 | `workflows/3z-afk-loop.md:118` | rule/definition | 0b updates BACKLOG_MAP | removable | wording |
| 59 | `workflows/4a-verify-and-ship.md:34` | read | parent | removable | `gh issue view --json parent` fallback |
| 60 | `workflows/4a-verify-and-ship.md:86` | mirror write | status=done (+close) | removable | `gh issue edit` + `gh issue close` literals |
| 61 | `workflows/4a-verify-and-ship.md:87` | mirror write | status=in review | removable | `gh issue edit` literal |
| 62 | `workflows/4a-verify-and-ship.md:88` | mirror write | blocked_by clear | removable | `removeBlockedBy` cmd |
| 63 | `workflows/4a-verify-and-ship.md:98` | mirror write | status in review (epic), blocked_by clear | removable | `gh issue edit` + `removeBlockedBy` |
| 64 | `workflows/4a-verify-and-ship.md:100-101` | gate/heal | status, blocked_by (+pr-link) | removable | reconcile gate; PR-link half is GitHub-only already |
| 65 | `workflows/4a-verify-and-ship.md:102` | read | parent, status (draft rule) | removable | `gh issue view --json subIssues` |
| 66 | `workflows/4b-audit-architecture-drift.md:26` | read | active items | removable | `gh issue list` |
| 67 | `workflows/4b-audit-architecture-drift.md:65` | read | in-progress rows (collision) | removable | `gh issue list --label` |
| 68 | `workflows/4b-audit-architecture-drift.md:75` | read | in-progress rows (collision) | removable | same |
| 69 | `workflows/4c-codebase-health-audit.md:57-58` | read | status:in progress modules | removable | `gh issue list --label` |
| 70 | `skills/load-memory/SKILL.md:21` | read | whole map (WIP conflicts) | removable | `gh issue list --label` |
| 71 | `commands/stratosphere-setup/SKILL.md:38` | rule/definition | template file list | removable | template removed |
| 72 | `commands/stratosphere-setup/SKILL.md:79` | rule/definition | connect-GitHub prompt text | removable | wording |
| 73 | `commands/stratosphere-setup/SKILL.md:83` | local-only write | local file-based issue tracking fallback | offline-only | the offline tracker backend |
| 74 | `commands/stratosphere-setup/SKILL.md:122` | rule/definition | memory file list | removable | list |
| 75 | `commands/stratosphere-setup/SKILL.md:214` | rule/definition | tracked-file rationale | removable | list |
| 76 | `commands/stratosphere-setup/SKILL.md:233` | local-only write | Label Registry (write confirmed label set) | removable | `gh label list` is the source; registry only needed offline |
| 77 | `commands/stratosphere-setup/SKILL.md:268` | local-only write | Label Registry (final resolved set) | removable | same |
| 78 | `commands/stratosphere-setup/SKILL.md:291-292` | mirror write | seed rows from GitHub issues (BT padded) | removable | read from GitHub, nothing to mirror |
| 79 | `commands/stratosphere-setup/SKILL.md:357` | rule/definition | registry authoritative after Checkpoint 6 | removable | rule |
| 80 | `commands/stratosphere-update/SKILL.md:19` | rule/definition | backlog data never overwritten | removable | wording |
| 81 | `commands/stratosphere-update/SKILL.md:119` | rule/definition | `.stratosphere-new` merge target | removable | file-merge machinery |
| 82 | `commands/stratosphere-update/SKILL.md:152` | gate/heal | BT id set + row count unchanged | removable | corroboration check; scaffold.py:234-257 backs it |
| 83 | `references/concept-map-operations.md:26` | mirror write | map row | removable | `gh issue create` literal :22 |
| 84 | `references/concept-map-operations.md:28` | local-only write | BT-LOCAL row | offline-only | offline create |
| 85 | `references/github-issue-relations.md:23` | local-only write | Parent/Blocked by cols + body text fallback | offline-only | gh-absent fallback |
| 86 | `references/issue-templates.md:24` | mirror write | status=done | removable | text in Spike template |
| 87 | `references/issue-templates.md:59` | rule/definition | Parent mirrors sub-issue + column | removable | wording |
| 88 | `references/issue-templates.md:60` | rule/definition | Blocked by mirrors edge + column | removable | wording |
| 89 | `references/pr-body-and-ship.md:31` | read | labels (tier:epic rows) | removable | already has `--epic` fallback when map absent (CI) |
| 90 | `references/terminal-sync-invariant.md:9-20` | gate/heal | all 5 (gate contract) | removable | whole reference exists only for the mirror |
| 91 | `references/terminal-sync-invariant.md:25-27` | gate/heal | heal (upsert map cell, `--source map` cmds) | removable | same |
| 92 | `references/terminal-sync-invariant.md:30-32` | rule/definition | boundaries; offline = self-attested | offline-only | offline: map is the only store |
| 93 | `rules/memory-protocol.md:51` | rule/definition | BT-xxx -> BACKLOG_MAP.md ownership table | removable | [always_on] |
| 94 | `rules/memory-protocol.md:91` | rule/definition | pre-authorised map writes (Ref/status) | removable | [always_on] |
| 95 | `rules/memory-protocol.md:107-110` | rule/definition | id minting; Parent/Blocked by columns | removable | [always_on]; minting stays, column wording goes |
| 96 | `rules/okf-protocol.md:55` | rule/definition | status in BACKLOG not frontmatter | removable | [glob] |
| 97 | `rules/okf-protocol.md:97` | rule/definition | type `backlog` registry row | removable | [glob] |
| 98 | `constitution/AGENTS.md` | rule/definition | none (0 mentions) | removable | [always_on] nothing to remove |
| 99 | `memory-templates/BACKLOG_MAP.md:18-35` | rule/definition | rules block (SOS:BLOCK backlog-rules) | removable | whole file is the mirror |
| 100 | `memory-templates/BACKLOG_MAP.md:37-51` | rule/definition | Label Registry + Milestone definition | removable | vocabulary needs a new home (reference file); GitHub is source |
| 101 | `memory-templates/BACKLOG_MAP.md:53-59` | rule/definition | table header (9 cols) | removable | ICE + Ref cols: see 2a/3b |
| 102 | `memory-templates/STATUS.md:13` | rule/definition | authoritative active set note | removable | wording |
| 103 | `memory-templates/LEARNINGS.md:27` | local-only write | temporary TODOs -> BACKLOG_MAP.md | needs GitHub equivalent (other: local TODO sink) | no GitHub form unless a TODO issue |
| 104 | `scripts/reconcile.py:1-45` | rule/definition | module contract | removable | docstring |
| 105 | `scripts/reconcile.py:71-101` | read | parse 9-col rows (status, labels, milestone, parent, blocked_by) | removable | `gh issue list --json` replaces parser |
| 106 | `scripts/reconcile.py:112-189` | read | open_ids, ship_unit, effective_blockers, edge_verdict, stale_blockers | removable | blocker predicate reads map rows; needs per-issue gh reads (cost) |
| 107 | `scripts/reconcile.py:190-256` | gate/heal | compare map vs gh (status, milestone, labels, parent, blocked_by, closed, pr_link) | removable | gate disappears |
| 108 | `scripts/reconcile.py:394-466` | gate/heal | gh_fix_commands: map -> GitHub cmds | removable | the cmds are the verbs themselves |
| 109 | `scripts/reconcile.py:469-545` | local-only write | upsert_cells / heal: rewrites map cells from gh | removable | only exists to fix drift |
| 110 | `scripts/reconcile.py:546-575` | read | edges_cmd (CLEAR/KEEP decisions) | removable | keep logic; swap row source |
| 111 | `scripts/reconcile.py:578-725` | gate/heal | main gate, MIRROR-DRIFT/UNVERIFIED, `[local-only]` path | removable | offline `[local-only]` self-check stays for offline backend |
| 112 | `scripts/pr_body.py:14` | rule/definition | docstring (tier:epic rows) | removable | doc |
| 113 | `scripts/pr_body.py:308-315` | read | backlog_rows (fails open) | removable | map optional already |
| 114 | `scripts/pr_body.py:318-324` | read | epic_ids (label tier:epic) | removable | `--epic` flag exists |
| 115 | `scripts/pr_body.py:327-336,356` | read | backlog_parents (parent) | removable | `gh issue view --json parent` |
| 116 | `scripts/validate_memory.py:84-98` | local-only write | autofix writes `[[id]]` into table cell parts[8] | needs GitHub equivalent (Ref) | NB parts[8] is ICE under the 9-col schema, Ref is parts[9]: probable stale index |
| 117 | `scripts/validate_memory.py:164` | gate/heal | BACKLOG_MAP in lint scope | removable | scope list |
| 118 | `scripts/validate_memory.py:205-260` | gate/heal | ID format, duplicate ids, taxonomy labels on rows | removable | label taxonomy has no GitHub-side lint |
| 119 | `scripts/validate_memory.py:489` | gate/heal | skip trust tags for backlog | removable | one line |
| 120 | `scripts/scaffold.py:36` | rule/definition | KNOWN_BLOCK_IDS (backlog-rules, label-canonical, backlog-header) | removable | drift-guarded by test |
| 121 | `scripts/scaffold.py:234-257` | gate/heal | cheap corroboration: BT id set + row count | removable | update-flow merge check |
| 122 | `scripts/okf_view.py:41-56` | read | ID definitions index from table rows | removable | skip file |

**Total sites: 122**

| kind | sites |
|:--|--:|
| read | 33 |
| mirror write | 29 |
| local-only write | 11 |
| gate/heal | 19 |
| rule/definition | 30 |

| disposition | sites |
|:--|--:|
| removable | 109 |
| needs GitHub equivalent | 7 |
| offline-only | 6 |

Needs-GitHub-equivalent detail:

- needs GitHub equivalent (Ref; provisional milestone is map-only, GitHub epic has none until 3a): 1
- needs GitHub equivalent (Ref): 2
- needs GitHub equivalent (other: provisional milestone): 1
- needs GitHub equivalent (ICE, Ref): 1
- needs GitHub equivalent (ICE): 1
- needs GitHub equivalent (other: local TODO sink): 1

**Not map-aware (verified by grep, zero BACKLOG/map references):** `nightly_scan.py`, `nightly_state.py`, `test_gate.py`, `ci_gate.py`, `floor_guard.py`, `contract_check.py`, `check_suite.py` (its hit is an unrelated 'Mirrors build/build.py' comment), `src/constitution/*`, `src/github/sync-labels-to-project.yml` (label -> Project board Action; acts on GitHub labels, never reads the map).
**Outside `src/` but coupled (not inventoried):** `tests/framework/test_status_label_contract.py`, `test_bump_guard.py`, `test_update_flow.py`, `tests/lifecycle/*`, `tests/lifecycle-harness/*`, `tests/jules/test_jules_dispatch.py`, `tests/fixtures/legacy/validate_memory.v4.0.0.py`.

Findings worth a decision:

1. **Map-only values.** Three things exist only in the map: `ICE` (score; raw metrics are also in the issue body, 3b:101), `Ref` (memory ids; 2a:96, 2b:106, 3b:112, validate_memory autofix), and 2a's provisional milestone `v1.0.0` (2a:100 / 2b:110: GitHub epic has no milestone until 3a, so that cell is intentionally map != GitHub and 3a's gate only checks `milestone` after 3a assigns it).
2. **Blocker predicate reads the map.** `reconcile.py --edges` (3d:20, 3z:40, 4a:88/98, 0b:27) decides CLEAR/KEEP from map rows (parent, milestone, labels, status, blocked_by). Dropping the map means this becomes N `gh issue view --json` reads, or one `gh issue list --state all --json number,labels,milestone,parent,blockedBy,state` (single call, no per-id cost).
3. **Already map-optional.** `pr_body.py` fails open when the map is absent and has `--epic`; 3d/3z/4a already say 'BACKLOG row, else `gh issue view`'. These read sites are the cheapest to drop.
4. **Probable latent bug.** `validate_memory.py:84-98` autofix targets `parts[8]`; with a leading empty split cell and 9 columns that is ICE, not Ref (`parts[9]`).
5. **Retention rule undefined.** 0b:27 says 'before deleting any row (per retention)' but no retention rule for map rows exists in `src/` (grep).

## B. Text cost

Method: per `src/**/*.md` (workflows, skills, commands, references, rules, templates; `plan-html` and `arch-drift-report-template.md` excluded as false positives of the word 'backlog'). A line counts if it matches CORE = `BACKLOG|Backlog|Label Registry|map row|MIRROR-|mirror write/field/the/row`; GATE adds `reconcile.py|terminal-sync-invariant|Terminal sync gate|[HEALED|heal per` (text that exists only because of the mirror gate). **Sentence-level** = only the matching sentence(s) of each line (headline number); **full-line** = the whole line/bullet (upper bound). Characters = `len()` of text + 1 per line. Script: `.tmp/bt189/s2_count.py`.

### B1. Per-file table (all files with any match)

| file | file chars | CORE (sentence) | CORE (full line) | +GATE (sentence) | CORE+GATE (sentence) |
|:--|--:|--:|--:|--:|--:|
| workflows/3z-afk-loop.md | 13819 | 2026 | 2431 | 241 | 2267 |
| workflows/4a-verify-and-ship.md | 15978 | 1695 | 2278 | 571 | 2266 |
| references/terminal-sync-invariant.md | 4151 | 1145 | 2240 | 795 | 1940 |
| workflows/3c-sprint-planning.md | 7077 | 1522 | 2618 | 374 | 1896 |
| workflows/0b-stop-session.md | 6934 | 1405 | 2509 | 435 | 1840 |
| commands/stratosphere-setup/SKILL.md | 31056 | 1495 | 2429 | 0 | 1495 |
| memory-templates/BACKLOG_MAP.md | 6558 | 1378 | 1609 | 32 | 1410 |
| workflows/3b-create-issue.md | 18451 | 1166 | 1916 | 233 | 1399 |
| workflows/3a-version-planning.md | 9222 | 749 | 1611 | 317 | 1066 |
| workflows/3d-implement-issue.md | 9802 | 786 | 1368 | 95 | 881 |
| rules/memory-protocol.md | 6749 | 789 | 1140 | 0 | 789 |
| workflows/2b-interface-design.md | 10850 | 764 | 1020 | 0 | 764 |
| workflows/0d-nightly-consolidation.md | 7469 | 358 | 418 | 392 | 750 |
| workflows/2a-write-prd.md | 9448 | 571 | 966 | 0 | 571 |
| workflows/4b-audit-architecture-drift.md | 7614 | 540 | 540 | 0 | 540 |
| references/issue-templates.md | 3107 | 439 | 620 | 0 | 439 |
| workflows/0a-start-session.md | 2492 | 376 | 454 | 0 | 376 |
| commands/stratosphere-update/SKILL.md | 13208 | 352 | 659 | 0 | 352 |
| references/concept-map-operations.md | 3900 | 280 | 280 | 0 | 280 |
| workflows/1c-concept-map.md | 7308 | 247 | 392 | 0 | 247 |
| references/github-issue-relations.md | 1695 | 187 | 187 | 0 | 187 |
| memory-templates/STATUS.md | 965 | 183 | 395 | 0 | 183 |
| rules/okf-protocol.md | 9557 | 181 | 373 | 0 | 181 |
| workflows/1b-concept-framing.md | 13648 | 149 | 155 | 0 | 149 |
| references/pr-body-and-ship.md | 4113 | 140 | 570 | 0 | 140 |
| workflows/4c-codebase-health-audit.md | 7514 | 63 | 120 | 0 | 63 |
| skills/load-memory/SKILL.md | 1755 | 47 | 50 | 0 | 47 |
| memory-templates/LEARNINGS.md | 1568 | 37 | 37 | 0 | 37 |

### B2. Totals

| group | CORE (sentence) | CORE (full line) | +GATE | CORE+GATE (sentence) |
|:--|--:|--:|--:|--:|
| workflows/ | 12417 | 18796 | 2658 | 15075 |
| references/ | 2191 | 3897 | 795 | 2986 |
| commands/ (setup, update) | 1847 | 3088 | 0 | 1847 |
| skills/ | 47 | 50 | 0 | 47 |
| rules/ | 970 | 1513 | 0 | 970 |
| memory-templates/ | 1598 | 2041 | 32 | 1630 |
| **all** | 19070 | 29385 | 3485 | 22555 |

**One total: 19,070 chars of BACKLOG-related text (CORE, sentence-level); 22,555 chars with the mirror-only gate text; 29,385 chars at full-line upper bound (CORE).** Of the CORE total, workflows = 12,417 (65%).

Top 5 workflows (CORE+GATE sentence chars; CORE alone in brackets): 3z-afk-loop 2,267 (2,026) | 4a-verify-and-ship 2,266 (1,695) | 3c-sprint-planning 1,896 (1,522) | 0b-stop-session 1,840 (1,405) | 3b-create-issue 1,399 (1,166).

Caveat: some GATE text also serves non-mirror duties (`reconcile --edges` blocker predicate, PR-link check), so CORE+GATE overstates what disappears with the map; CORE understates multi-sentence mirror bullets where only the first sentence names the map.

### B3. Always-loaded text

Always-on = `trigger: always_on` rules + the constitution (`AGENTS.md`, loaded via `CLAUDE.md` `@AGENTS.md`). `okf-protocol.md` is `trigger: glob` (`.memory/**`, `docs/**`) so it is conditional, listed for reference.

| file | chars | loading | BACKLOG-related (sentence) | (full line) |
|:--|--:|:--|--:|--:|
| constitution/AGENTS.md | 8965 | always (constitution) | 0 | 0 |
| rules/memory-protocol.md | 6749 | always_on | 789 | 1140 |
| rules/output-mode.md | 2598 | always_on | 0 | 0 |
| rules/okf-protocol.md | 9557 | glob (.memory/**, docs/**) | 181 | 373 |
| constitution/CLAUDE.md + GEMINI.md | 486 | pointer files (one per host) | 0 | 0 |

**Always-loaded total: 18,312 chars** (AGENTS.md 8,965 + memory-protocol 6,749 + output-mode 2,598), of which **789 chars (4.3%) are BACKLOG-related**, all in `memory-protocol.md` (lines 51, 91, 107-110). `AGENTS.md` has none. Conditional okf-protocol adds 181 more when `.memory`/`docs` are touched. Not counted: the 1,609-char `BACKLOG_MAP.md` template rules/registry block and the live `.memory/BACKLOG_MAP.md` (every row is read by 0a/1b/2a/3a/3c/3z/load-memory; size grows with the backlog, not measured here).

## C. Verb fit

Every distinct WRITE kind the workflows make to issue state. GitHub literals are the `gh`/GraphQL forms present in `src/` today (file:line). 'Local' = plausible form in a local-markdown backend (the Backlog table row).

| # | write kind | tracker verb | GitHub form today (file:line) | local-markdown form | fit |
|--:|:--|:--|:--|:--|:--|
| 1 | create issue | `create(kind, title, body, labels, milestone, parent, blockers) -> id` | `gh issue create --title .. --label .. --milestone .. --body-file .tmp/3b-issue-body.md` (3b:100, epic literal 3b:108; 2a:31; concept-map-operations.md:22,38); id = returned number, zero-padded | append row; id `BT-LOCAL-<slug>` | fit (verb returns the id). Gap: no `BT-LOCAL -> BT-nnn` promote-on-connect workflow exists ('until synced', 2a:33) |
| 2 | set status | `set_status(id, status)` (backend removes the other `status:*`) | `gh issue edit <n> --remove-label status:* ... --add-label status:X` (0a:30, 3d:26, 3z:52/73/77, 4a:86-87/98, 2b:26/103, 3b:24, 0b:31); board Action then moves the Project column (`src/github/sync-labels-to-project.yml`) | edit Status cell | fit; verb must own the single-status invariant (0a:30 lists 5 removes by hand) |
| 3 | add/remove label (non-status) | `set_labels(id, add, remove)` | `gh issue edit <n> --add-label/--remove-label` (3c:72 priority, no literal; reconcile.py:454); registry side: `gh label list`/`gh label create` (setup:238, 3b:123) | edit Labels cell + Label Registry list | fit. Label *creation* (`ensure_label`) is a separate admin verb (setup-time) |
| 4 | set milestone | `set_milestone(id, name)` + `ensure_milestone(name)` + `close_milestone(name)` | `gh issue edit <n> --milestone` (reconcile.py:450; `--milestone` at mint 3b:104); create: no literal (3a:71, 3c:73); close: `gh api -X PATCH repos/{owner}/{repo}/milestones/<n> -f state=closed` (3a:69); list: `gh api repos/{owner}/{repo}/milestones` (3a:43, 3b:104) | edit Milestone cell; milestone open/closed derived (no open_issues count; compute from rows) | fit with 3 verbs. `open_issues==0` close precondition (3a:20) is a query the local backend computes |
| 5 | set parent | `set_parent(child, parent)` / `clear_parent` | `addSubIssue` GraphQL (github-issue-relations.md:12; 3b:105, 1c:41; reconcile.py:460); `removeSubIssue` (rel.md:14) | edit Parent cell (single value) | fit |
| 6 | add blocker | `add_blocker(id, blocker)` | `addBlockedBy` GraphQL (rel.md:17; 3a:72, 3b:111, 3c:74, 1c:41; reconcile.py:463) | append bare id to Blocked by cell | fit |
| 7 | clear blocker | `clear_blocker(id, blocker)` | `removeBlockedBy` GraphQL (rel.md:19; 4a:88/98, 0b:27; reconcile.py:465,572) | remove id from Blocked by cell | fit as a write. The CLEAR/KEEP *decision* (ship unit, PR merged) uses git + `gh pr view` state, backend-neutral only if the read verbs return milestone/parent/labels |
| 8 | set ICE | `set_ice(id, score, I, C)` or derive-on-read | NONE today: ICE is written only to the map ICE column (3b:113) plus raw metrics in the issue body at creation (3b:101); 3c:34 reads the map | edit ICE cell | MISFIT: local-only column. GitHub form would be an issue-body edit (`gh issue edit --body-file`, not used anywhere) or a Project number field; cheaper: no verb, recompute from body metrics + size label (3c:34 already recomputes when empty) |
| 9 | set Ref (memory ids) | `set_refs(id, ids)` | NONE: Ref column is local-only; doc paths already live in the issue body (BACKLOG_MAP template rule) | edit Ref cell (2a:96, 2b:106, 3b:112, validate_memory autofix) | MISFIT: pointers into `.memory/` have no GitHub field. Options: body line `Refs: L-012, A-003`, or keep Ref in a non-map place; offline = cell |
| 10 | close / reopen | `close(id, reason)` / `reopen(id)` | `gh issue close <n> --reason completed` (4a:86); `--reason "not planned"` (0b:31); `gh issue close <ticket#>` (concept-map-operations.md:92); `gh issue reopen <n>` (3d:26, 0b:31) | Status = done (`closed == done`, template rule) | partial MISFIT: on GitHub the unit PR merge closes epics via `Closes #<n>` (4a:96, pr-body-and-ship.md:43) with no tracker call; a local backend has no PR so 0b done-detection must call `close` explicitly |
| 11 | comment (PR-link, notes) | `comment(id, body)` | `gh issue comment <n> --body "Shipped in PR #<pr> - <url>"` (4a:84); `[STUCK]` (3z:73); sprint sync (3c:75, no literal); resolution (concept-map-operations.md:88) | append dated line under a per-issue log, or no-op | fit as a verb. PR-link content is GitHub-only (needs a PR URL); the gate's `--pr-id` check (reconcile.py) is GitHub-only and has no local meaning |
| 12 | set issue body | `set_body(id, body)` / `append_body` | no literal `gh issue edit --body` in src; prose at 2a:95 (summary + doc link), 2b:105 (design link), 3b `--body-file` at create | MISFIT: the table has only Title. Needs a per-issue body file (e.g. `docs/issues/BT-LOCAL-n.md`) | MISFIT: issue bodies carry Acceptance Criteria (read by 4a:38 via `gh issue view`), Dependencies/Design path (3d:26), PRD/design links; local-markdown backend needs body storage, not just a row |
| 13 | assign (claim) | `claim(id)` | `gh issue edit <N> --add-assignee @me` (1c:51; concept-map-operations.md:55) | no Owner column | MISFIT (minor): no local column; local form = no-op or a 'claimed' note |
| 14 | PR create/edit/ready/label | NOT a tracker verb | `gh pr create/edit/ready`, `gh label create risk:one-way` + `gh pr edit --add-label` (4a:79-102, pr-body-and-ship.md:40) | n/a (4a has `local-only` mode) | MISFIT by design: pull requests are a VCS-host concept; keep outside the tracker verb set |
| 15 | read verbs (support) | `get(id)`, `list(filter)`, `children(id)`, `blockers(id)` | `gh issue view --json milestone,parent,subIssues,blockedBy,state` (3d:22, 3b:30, 4a:90, rel.md:21); `gh issue list --label/--state --json` (1c:25, 3c:29, 4b:81) | table scan | fit; needed to replace the 33 read sites |

**Verb set:** create, set_status, set_labels (+ensure_label), set_milestone (+ensure/close_milestone), set_parent, add_blocker, clear_blocker, close/reopen, comment, plus reads (get/list/children/blockers). **MISFITS:** set ICE (local-only column), set Ref (local-only column), set issue body (no table equivalent), claim (no column); partial misfit: close (merge auto-close is GitHub-only); PR operations are out of scope for the tracker interface.
