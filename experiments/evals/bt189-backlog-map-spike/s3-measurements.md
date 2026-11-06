# BT-189 S3: measurements (analyst A3)

Read-only throughout. Scripts in this dir: `gen_map.py` (B), `diff_map.py`/`diff_extra.py` (drift), `count_rec.py` (counting wrapper over `reconcile.main`, only `--ids`/`--edges`, asserts no `--heal/--summary/--out`), `timeq.py` + `qa.jq`/`qb.jq`/`qc.graphql`/`qgate.graphql` (C), `s3_net.py` (net text). Raw outputs: `qa.*.out`, `qb.*.out`, `qc*.out`, `qgate.cth.out`. tokens = chars/4. Wall times: median of 3 runs unless noted. Repo state verified unchanged (`git status` in both; `-B` used so no `__pycache__`).

## 1. B: generated map

`gen_map.py`: one paginated GraphQL query (`issues(first:100)` + `labels`, `milestone`, `parent`, `blockedBy(first:50)`; `blockedBy`/`parent` exist in the schema), 9-column table, ICE/Ref = `—`.

| repo | issues | gh/GraphQL calls | wall (3 runs; median) | generated chars (tok) | live map chars (tok) |
|---|--:|--:|---|--:|--:|
| CTH | 168 | 2 (2 pages) | 1.96, 2.14, 1.87 -> **1.96 s** | 34,075 (8,519) | 47,371 (11,842) |
| StratOS | 111 | 2 | 1.57, 1.72, 1.37 -> **1.57 s** | 16,819 (4,205) | 19,350 (4,837) |

Generated files: `BACKLOG_MAP.generated.cth.md`, `BACKLOG_MAP.generated.stratos.md`. Live map table-only chars: CTH 41,559, StratOS 13,357 (the rest is Rules + Label Registry, which a generated map would not carry).

### Drift: live map vs GitHub (7 mirrored columns)

Compared with `status:*` stripped from Labels on both sides, closed = done, `—`/empty normalized. A mismatch is a map cell that differs from GitHub today.

**CTH (163 map rows, 168 issues, 56 open on GitHub / 57 open in map)**
- Rows only in map: 0. Rows only on GitHub: **5** (BT-060, 061, 062, 063, 078; all CLOSED, e.g. BT-078 is a jules-e2e test issue).
- 62 of 163 common rows differ in at least one column; 57 excluding Title. Of the open rows (57): labels 20, parent 15, blocked_by 7, milestone 3, status 1, title 1.
- Per column (all rows): **labels 49**, **blocked_by 23**, **parent 18**, **title 17**, **milestone 10**, **status 1**.
  - labels: gh_only `priority:*` 28, `size:*` 10; map_only `size` 13, `tier` 11, `mode` 11, `area` 9, `scope` 6. E.g. BT-002 gh_only `priority:high`; BT-007 map_only `mode:HITL, tier:slice`; BT-009 map_only `size:small` gh_only `priority:high, size:medium`.
  - blocked_by (all 23 are map_only: stale edges the map kept, GitHub cleared): BT-004 `BT-052`; BT-006 `BT-085, BT-086`; BT-007 `BT-040`; BT-008 `BT-001`; BT-011 `BT-054`.
  - parent: 17 map `—` where GitHub has a parent (BT-009 -> BT-073, BT-010 -> BT-074, BT-011 -> BT-054, BT-014 -> BT-074, BT-017 -> BT-074), 1 reverse.
  - title: 8 map titles are a prefix/substring of GitHub's (BT-004/016/023 lack `[Superseded] `; BT-037 lacks `BT-037: `), 3 truncated, 6 other (hand-shortened).
  - milestone: BT-004 map v1.1.1 gh v1.1.0; BT-016 v1.1.1/v1.1.0; BT-023 v1.1.1/v1.1.0; BT-030 v1.6.1/v2.0.1; BT-041 v2.0.0/v1.6.0 (8 differ, 2 gh none).
  - status: BT-245 map `in review`, GitHub `done` (closed).

**StratOS (59 map rows, 111 issues, 7 open on GitHub / 5 open in map)**
- Rows only in map: 0. Rows only on GitHub: **52**, by design (the map keeps only a retained window of done rows, so this is retention, not drift).
- 15 of 59 common rows differ; 7 excluding Title. Open rows: 0 mismatches in every column.
- Per column: **title 9** (hand-shortened or the `z - ` prefix on BT-108), **labels 7** (map_only `3-implement`, a legacy label on BT-108, 118-121 ...), **milestone 7** (map `v1.0.0`, GitHub none), status 0, parent 0, blocked_by 0.
- Open-row set differs by 2 only because 2 open GitHub issues (#41, #77) have no map row.

Reading: StratOS map is faithful on every live row. CTH's map is wrong on 57 rows today (labels, parent and blocked_by dominate), mostly older rows and the 20 open-row label drifts, which is what the nightly summary already reports.

## 2. A: baseline (reconcile.py gate)

Read-only confirmed by code: `--ids` and `--edges` call only `gh auth status`, `gh issue view`, `gh pr view` and `parse_backlog` (read); writes exist only in `--heal` (map) and `--summary --out/--keys-out` (scratch). `pr_body` is imported lazily (`-B` used). There is no `--expect-pr` flag; `--pr-id` is the PR-link scope, and it does not change the call count (comments ride in the core `gh issue view`).

gh subprocess calls, from code and confirmed with the counting wrapper:

| invocation | gh calls |
|---|---|
| `--ids` (any gate) | 1 `gh auth status` + **3 per id** (`gh issue view` core, then `blockedBy`, then `parent`, one subprocess each) |
| `--ids X --pr-id X` (or without) | same: 1 + 3 per id (comments added to the core call) |
| `--edges blockers\|dependents` | 0 when the edge is same ship unit or the blocker is an epic/standalone or unshipped (every real case sampled: BT-243, BT-194, BT-035, BT-025, BT-241, StratOS BT-189/188). Cross-unit shipped child-slice blocker: 1 `gh auth status` once + 2 per blocker (comments, `gh pr view`) |

Measured (real runs from inside each repo, wrapper `count_rec.py`):

| run | CTH calls / wall | StratOS calls / wall |
|---|---|---|
| gate, 1 id (slice, `--pr-id`) | 4 / 2.67 s | 4 / 2.50 s |
| gate, 4 ids (slice, epic, 2 blockers) | **13 / 9.58 s** | **13 / 8.09 s** |
| `--edges blockers/dependents` | 0 / 0.03 s | 0 / 0.01 s |

CTH ids: slice BT-243, epic BT-051, blockers BT-241, BT-166. StratOS ids: slice BT-189, epic BT-190, blockers BT-188, BT-191.

Gate invocations in a 3z slice run (from `3z-afk-loop.md` L40/L50 and `4a-verify-and-ship.md` steps 7-9; 3d's blocker guard is skipped under 3z):
- once per run: Phase 1 step 3 `--edges blockers --ids <all slices>` (0 gh typical)
- per slice: 2A.0 frontier `--edges blockers` (1); 4a step 7 `--edges dependents --ids slice` (1); 4a step 8 `--edges dependents --ids <epics flipped>` (0, or 1 on the epic's last slice); 4a step 9 `--require-gh --ids ... --pr-id` gate (1, up to 3 on heal)
- so 4 or 5 `reconcile.py` invocations per slice (+1 per run), of which only the step-9 gate costs gh: **4 calls** (slice only, non-last slice), **7** (slice + epic), **10** (slice + epic + 1 cleared dependent), **13** (4 ids); heal retries multiply it by up to 3. Cross-unit shipped blockers add up to 5 per edges call. 0b adds a `--edges dependents --all-open` (0 typical) and a gate over cleared dependents.

Batching alone would cut A: a single aliased GraphQL query for the same 4 ids (`qgate.graphql`) is **1 call, 0.62 s, 192 chars** (vs 13 calls, 9.58 s).

## 3. C: scoped live queries

Whole-map read (what runs today): CTH 47,371 chars (11,842 tok), StratOS 19,350 (4,837 tok), ~0 s wall.

| query | CTH chars (tok) / wall | StratOS chars (tok) / wall | vs whole map (CTH) |
|---|---|---|---|
| (a) load-memory step 6: `gh issue list --state open --limit 500 --json number,title,labels,parent,blockedBy --jq @qa.jq` (in-progress set, its blockers, parent's blockers) | 605 (151) / 1.24 s | 110 (27) / 0.77 s | 1.3% |
| (b) 3c: `gh issue list --state open --limit 500 --json number,title,labels,milestone,parent,blockedBy,body --jq @qb.jq` (open `tier:slice` planned/needs_spec, minus `concept:*`/`scope:deferred`; labels, milestone, effective blockers; ICE = Impact*Confidence/Effort from body metrics + size label) | 5,969 (1,492), 29 rows / 1.39 s | 186 (46), 1 row / 0.80 s | 12.6% |
| (c) 3d/4a/3z single issue: `gh issue view N --json number,title,state,labels,milestone,parent,blockedBy --jq ...` | 239 (59) / 0.79 s | 180 (45) / 0.79 s | 0.5% |
| (c') same, one GraphQL call adding parent milestone, parent's blockers, blocker milestone/state/parent (everything `ship_unit` + `edge_verdict` need) | 81 (20) / 0.59 s | 51 (12) / 0.58 s | 0.2% |
| gate (4 ids, aliased GraphQL) | 192 (48) / 0.62 s | n/a | |

Notes:
- Body metric format (CTH BT-243, 241): `- **Impact:** 2.0 (...)`, `- **Confidence:** 100%`, `- **Effort Weight:** 2`, `- **ICE Score:** 1.0`. `qb.jq` recomputes ICE with `Impact*Confidence/Effort` (size small=1, medium=2, large=3); its BT-243 and BT-241 results (1.0) equal the body's own score. A body with `Confidence: 1.0` parses as 1.0, `100%` as 1.0. Spikes have no metrics (null, which is correct: Spikes skip ICE). Older bodies with other formats come back null, which is the "recalculate if empty" case.
- The raw `--json ... body` payload the CLI downloads is 192,069 chars on CTH; only the `--jq`-filtered text reaches the agent. gojq runs inside `gh`; no `jq` binary is needed.
- (a) lists the in-progress set and `parent_blockers`; it relies on the parent epic being open (an epic outside the open list shows `[]`).
- Per 3z slice run, assuming 4 map loads (3z orchestrator, 3d subagent, 4a audit subagent, 4a ship subagent; each self-hydrates via load-memory, no shared cache across subagents): reads A 47.4k tok CTH / 19.3k StratOS; C about 4x(a) + 4x(c) + gate = 0.9k CTH / 0.3k StratOS tok, at 9 gh calls (about 8.7 s CTH / 6.8 s StratOS).

## Per-3z-slice-run summary (typical last slice: assumptions above)

| | gh calls | wall | read tokens | net text chars |
|---|---|---|---|---|
| A CTH / StratOS | 13 / 13 (4 ids; 4 if slice only) | 9.6 s / 8.1 s | 47.4k / 19.3k | 0 |
| B CTH / StratOS | 10 / 10 (5 regenerations x 2 pages) | 9.8 s / 7.9 s | 34.1k / 16.8k | -13.4k net deleted upper (-11.7k conservative); -10.2k incl. adapter doc |
| C CTH / StratOS | 9 / 9 (batched gate 1) | 8.7 s / 6.8 s | 0.9k / 0.3k | -13.9k net deleted (incl. adapter doc) |

B stays at 10 calls only if the map is regenerated before every read; regenerating once per run and after each GitHub write gives about 4 calls / 4 s but a read-your-writes risk. Net text is framework text, identical for both repos; the repo-specific change is the deleted live map file (CTH 47,371 chars, StratOS 19,350) that no longer needs hand edits.

## 4. Slimmer gate: expected-state source

Today the map is both the intended-state oracle (map cell = what the phase just wrote) and the thing diffed. Without it, the gate needs `--expect` (inline `BT-n:field=value` pairs, or `--expect-file`) and compares GitHub's own fields (labels, state, milestone, parent, blockedBy, PR-link comment) to it. Extra prose, in chars:

| phase | expected-state source | extra prose |
|---|---|---|
| 3a | the roadmap work file `.tmp/3a-roadmap.work.md` (milestone assignment per parent + amended epic blockers): `--expect-file` of that table | ~220 |
| 3b | the issue drafts file `.tmp/BT-<padded>-issue-drafts.md` (labels, milestone, parent, blocked-by of each minted issue); `--expect-file` | ~260 |
| 3c | the sprint sequence the phase just printed (status, milestone, labels, blockers per slice), written once to `.tmp/3c-sprint.work.md`; `--expect-file` | ~260 |
| 4a | no file: derived by rule, inline `--expect BT-<slice>:status=done,closed;BT-<epic>:status=in review`; PR-link check stays `--pr-id`; cleared dependents asserted by `--edges dependents` returning no `[CLEAR]` | ~200 |
| 0b | cleared dependents: assert absent edge via `--edges dependents` (no CLEAR remains), plus parent epic `done` from the closed state | ~120 |
| **total** | | **~1,060** |

Surviving post-condition units from s1 and what feeds them without the map:
- closed == done: GitHub `state` + the `status:*` label (already in the core `gh issue view`); expected value comes from the `--expect` status.
- PR-link (`compare` L250-252, `_pr_state`, `pr_merge_state`, `make_merged_of`): unchanged, already GitHub-only.
- `ship_unit`, `effective_blockers`, `edge_verdict`, `stale_blockers`, `open_on_github`/`closed_on_github`: re-point `rows` to a dict built from the scoped query (c') (milestone, parent, parent milestone, blockedBy with state/parent/milestone): 1 batched GraphQL call per invocation instead of 0 gh calls today (this is the one place C is more expensive on gh calls than A). `--edges dependents` needs the reverse edge (`issue.blocking`) or an open-issue list (query a).
- Code size is about 254 non-blank lines (s1), of which these units are the 153.

## 5. Net text (criterion iii)

Method (`s3_net.py`, estimate +/- 30%): per file, s2's CORE+GATE sentence chars (22,555 total). Deleted: B = CORE+GATE minus read-site share (read sites stay as reads of the generated map) minus s1 survivors; C = CORE+GATE minus survivors (survivors: invariant doc 377, 0b 295, 3c 104, 4a 883, 3z 517 = 0.6 x the full-line lengths of the s1 call-site lines). Added: slimmer gate (section 4, ~1,060 in both); B: one freshness/regenerate sentence per reading workflow (~110 x 9) + generated-file header (500); C: scoped-query prose (about 2,000, per site 100-700) + tracker-verb adapter doc and offline-backend notes (3,200; counted in C, and shown separately for B because the verb set exists for backend swap, not for B itself).

| file | now | B del | B add | B net | C del | C add | C net |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 3z-afk-loop | 2,267 | 882 | 110 | 772 | 1,750 | 250 | 1,500 |
| 4a-verify-and-ship | 2,266 | 899 | 200 | 699 | 1,383 | 400 | 983 |
| terminal-sync-invariant (ref) | 1,940 | 1,563 | 0 | 1,563 | 1,563 | 0 | 1,563 |
| 3c-sprint-planning | 1,896 | 1,285 | 370 | 915 | 1,792 | 960 | 832 |
| 0b-stop-session | 1,840 | 1,545 | 120 | 1,425 | 1,545 | 120 | 1,425 |
| stratosphere-setup | 1,495 | 1,380 | 0 | 1,380 | 1,495 | 0 | 1,495 |
| BACKLOG_MAP template | 1,410 | 1,410 | 500 | 910 | 1,410 | 0 | 1,410 |
| 3b-create-issue | 1,399 | 1,232 | 260 | 972 | 1,399 | 260 | 1,139 |
| 3a-version-planning | 1,066 | 638 | 330 | 308 | 1,066 | 470 | 596 |
| 3d-implement-issue | 881 | 357 | 110 | 247 | 881 | 250 | 631 |
| memory-protocol (always-on) | 789 | 789 | 0 | 789 | 789 | 0 | 789 |
| 2b / 0d / 2a / 4b / 0a / others (17 files) | 5,306 | 3,966 | 550 | 3,416 | 5,306 | 550 | 4,756 |
| tracker-verbs doc (new) | 0 | 0 | 0 | 0 | 0 | 3,200 | -3,200 |
| **total** | **22,555** | **15,946** | **2,550** | **13,396** | **20,379** | **6,460** | **13,919** |

- Workflows only: B net 7,189, C net 10,216 chars.
- B is an upper bound: B keeps the map file, so rule/definition-only files (memory-protocol 789, okf 181, STATUS 183, setup 1,380, update 325, issue-templates 439) would lose about half; conservative B net about 11.7k. With the adapter doc charged to B too: 10.2k (8.5k conservative).
- Always-loaded (memory-protocol): both options remove its ~789 chars of BACKLOG rules (4.3% of the 18,312 always-loaded).
- C saves about 0.5k more than B because it deletes the template/rules and the freshness sentences, and costs about 3.9k more in new prose; the net is near equal. The difference is read tokens (C -97% per read) and the removed `.memory` file, not text.

## Blocked / caveats
- No hard blocker. `jq` binary absent (used `gh --jq`, gojq). `--expect-pr` does not exist in `reconcile.py`.
- The slimmer-gate `--expect` flag, `ship_unit` re-pointing and `issue.blocking` reverse edge were designed, not built or run; the gate numbers in section 4 are char estimates.
- B/C 3z call and token totals assume 4 map loads per slice run and the same-unit (0 gh) edge case; wall times include process start (about 0.6 s per gh call here).
- CTH and StratOS 3z numbers use the StratOS `src/scripts/reconcile.py` run from the CTH directory; CTH's installed `.agents/scripts/reconcile.py` copy was not read and may differ in version.
