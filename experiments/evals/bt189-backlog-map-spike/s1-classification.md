# BT-189 S1: classification of the sync layer (map-only vs gh-post-condition)

Analyst A1. Read-only on the repo. Method scripts: `.tmp/bt189/s1_count_reconcile.py`, `s1_count_invariant.py`, `s1_count_items.py` (rerunnable).

Classification rule, applied the same way everywhere:
- `map-only`: reads, writes, parses or diffs the map, or checks map-vs-GitHub field equality, or exists for the nightly drift report.
- `gh-post-condition`: a lifecycle predicate over GitHub state that stays meaningful with no map: closed == done, PR-link comment, blocker edge CLEAR/KEEP by PR merge state, stale GitHub edge. Where the code takes `rows` as input, the logic survives and only the input source would move to `gh` fields (flagged "re-point").
- `shared`: gh helpers, CLI plumbing, imports. Reported, excluded from every percentage.

Source notes:
- `src/scripts/reconcile.py` is 730 lines (631 non-blank), not ~579. Line counts below are non-blank lines.
- `docs/nightly/` does not exist in Stratosphere-OS and no `.last-run.json` is tracked here. The nightly reports live in the sibling repo `C:\Users\patri\Dev\CleanTechHub\docs\nightly\` (7 reports, 2026-07-25 to 2026-10-19; its `.last-run.json` holds only `{"last_run": ...}`, no drift map). Those were read, read-only, as the nightly evidence.
- `.memory/LEARNINGS.md` (2 entries, both test-harness traps) and `.memory/STATUS.md` record no map/GitHub drift or heal event. Zero incidents from them.

## Totals and verdict

| measure | map-only | gh-post-condition | shared (excluded) | map-only share |
|---|---:|---:|---:|---:|
| (a) reconcile.py classified lines | 377 | 153 | 101 | **71.1%** (377/530) |
| (b) gate/heal prose: invariant doc (line-weighted) | 7.06 | 3.09 | 3.89 | 69.6% |
| (b) gate/heal prose: call-site lines (24 classified + 2 shared) | 17 | 7 | 2 | 70.8% (17/24) |
| (b) combined | 24.06 | 10.09 | 5.89 | **70.5%** (24.06/34.15) |
| (c) incidents, root-cause clusters (18) | 10 | 5 | 3 ambiguous | **55.6%** (10/18, ambiguous counted against) |

Sensitivity (does not change the verdict):
- (a) strict reading, only code that never reads `rows` counts as gh-post-condition (52 lines): map-only 90.2%. (b) strict: about 88%. (c) is class-by-cause, so strict does not move it.
- (c) excluding the 3 ambiguous: 66.7% (10/15). Treating all 3 ambiguous as map-only: 72.2% (13/18). Even flipping the two soft gh calls as well (origin incident, 07-25 stale blockers): 83.3% (15/18).
- (c) real drift only, excluding the 4 tool-defect fixes: 6 of 14 = 42.9%.
- (c) item-weighted (every D-item instance across the nightly reports): 157 map-only, 30 gh, 31 ambiguous of 218 = 72.0%. Excluding ambiguous 84.0%. This measure is dominated by one old map repeated for 3 nights (parent/priority never populated 84, status:* false positive 43, stale map blocker 25), so it is secondary.

**Verdict: FAIL.** Required: all three shares >= 80%. Primary values: (a) 71.1%, (b) 70.5%, (c) 55.6%. Only the strict code reading clears 80% on (a) and (b); (c) fails under every reading but the most generous.

Reading of the result: removing the map removes most of the sync machinery (all parsing, upsert, heal, summary, nightly-age code, and the field-equality diff), but not all of it. The riskiest assumption is confirmed in part: the blocker predicate, closed == done, PR-link, and stale GitHub blocker edges survive, and 5 of 18 incidents (the stale `BT-215` family, the PR-link ordering, the dropped 4a status step) are GitHub-side misses that a map-less gate would still have to catch.

## Surviving post-condition gate (gh-post-condition units)

reconcile.py, 153 non-blank lines of 631 (24%):

| unit | file lines | non-blank |
|---|---|---:|
| docstring: --pr-id/closed==done, --edges usage, --edges paragraph | L9-12, L23, L34-37 | 9 |
| SHIPPED | L64 | 1 |
| ship_unit (re-point) | L124-136 | 13 |
| effective_blockers (re-point) | L139-144 | 6 |
| _no_pr_state | L147-148 | 2 |
| edge_verdict | L151-176 | 26 |
| stale_blockers (re-point) | L179-187 | 9 |
| closed_on_github (re-point to `status:done` label) | L190-195 | 6 |
| open_on_github (re-point) | L198-203 | 6 |
| compare: PR-link check | L250-252 | 3 |
| _pr_state | L296-302 | 7 |
| pr_merge_state | L305-321 | 17 |
| make_merged_of | L324-335 | 11 |
| edges_cmd (header + blockers/dependents) | L546-548, L553-575 | 26 |
| CLI --pr-id, --edges | L585, L608-610 | 4 |
| main: merged_of + --edges dispatch, stale emit, closed==done check | L633-635, L642-643, L711-712 | 7 |
| **total** | | **153** |

Shared infrastructure it still needs (not counted): `_gh_json`, `fetch_issue`, `gh_available`, `issue_number`, `_bt`, `_graphql`, `_edge`, `STATUS_RE`, `_pr_body`, imports, CLI plumbing, plain output: 101 lines. A slimmer gate is therefore about 254 non-blank lines (153 + 101), 40% of today's 631.

Surviving prose: invariant doc about 3.1 lines (closed == done, PR-link, stale-edge removal on both sides, edge stale only when CLEAR) plus 7 call-site lines (0b:27, 3c:30, 4a:84, 4a:88, 4a:98, 3z:40, 3z:50).

Not covered by the surviving gate (needs new, small expected-state asserts, not counted above): the multi-write landing checks in 3a/3b/3c/4a (labels, parent link, blocked-by edges, milestone, status label). Today the map is the intended-state oracle for these (`compare` diffs map vs GitHub). Without a map the intended state must come from the phase's own draft/plan. This is the main ambiguity, see the last section.

## 1. reconcile.py (non-blank counts)

| unit | lines (file) | non-blank lines | class | evidence |
|---|---|---|---|---|
| shebang + docstring title | L1-2 | 2 | shared | plumbing |
| docstring: assert GH matches map mirror | L4-6 | 3 | map-only | map-vs-GH equality contract |
| docstring: --fields = mirror fields written | L8 | 1 | map-only | scopes the map diff |
| docstring: --pr-id PR-link check + closed==done | L9-12 | 4 | gh-post-condition | GitHub-internal post-conditions |
| docstring: offline = map internal-consistency | L14 | 1 | map-only | map-only fallback |
| docstring: contract pointer | L15 | 1 | shared | plumbing |
| docstring usage: --ids/--pr-id/--fields | L17-19 | 3 | shared | CLI plumbing |
| docstring usage: --all-open --summary, --heal | L20-22 | 3 | map-only | map sweep and map heal |
| docstring usage: --edges | L23 | 1 | gh-post-condition | blocker decision list |
| docstring: --heal paragraph | L25-32 | 8 | map-only | map upsert / print GH cmds to match map |
| docstring: --edges paragraph | L34-37 | 4 | gh-post-condition | D3 blocker predicate, PR merge state |
| docstring: --summary paragraph | L39-41 | 3 | map-only | nightly drift counts/ages |
| docstring close | L42 | 1 | shared | plumbing |
| imports | L43-50 | 8 | shared | plumbing |
| STATE_DEFAULT | L52 | 1 | map-only | nightly drift state file |
| _nightly_state | L55-59 | 5 | map-only | only --summary/--date need it |
| STATUS_RE | L61 | 1 | shared | status:* label parse, used by both sides |
| NONE_TOKENS, ALL_FIELDS | L62-63 | 2 | map-only | map cell tokens, mirror field set |
| SHIPPED | L64 | 1 | gh-post-condition | D3 predicate constant |
| _bt | L67-68 | 2 | shared | id formatting |
| _row_cells | L71-81 | 11 | map-only | parses a map table row |
| parse_backlog | L84-100 | 17 | map-only | parses the map |
| issue_number | L103-105 | 3 | shared | BT id to issue number |
| _norm | L108-109 | 2 | map-only | normalises map cell tokens |
| open_ids | L112-114 | 3 | map-only | open rows of the map |
| _pr_body (lazy import) | L117-121 | 5 | shared | plumbing |
| ship_unit | L124-136 | 13 | gh-post-condition | D1 ship unit for the blocker predicate (reads rows; re-point to gh fields) |
| effective_blockers | L139-144 | 6 | gh-post-condition | own + parent epic blockers (reads rows; re-point) |
| _no_pr_state | L147-148 | 2 | gh-post-condition | default merged_of |
| edge_verdict | L151-176 | 26 | gh-post-condition | D3 predicate, PR merge state decides cross-unit |
| stale_blockers | L179-187 | 9 | gh-post-condition | edge whose verdict is OK still stored (reads rows; re-point) |
| closed_on_github | L190-195 | 6 | gh-post-condition | closed==done (as written compares row status) |
| open_on_github | L198-203 | 6 | gh-post-condition | done but still open = dropped gh issue close |
| compare: status/milestone/labels/blocked_by/parent | L206-249 | 37 | map-only | map-vs-GH field equality |
| compare: PR-link check | L250-252 | 3 | gh-post-condition | comment with /pull/ URL on the issue |
| compare: return | L254 | 1 | map-only | tail of the diff |
| _gh_json | L257-268 | 12 | shared | gh helper |
| fetch_issue | L271-286 | 16 | shared | gh helper |
| gh_available | L289-293 | 5 | shared | gh helper |
| _pr_state | L296-302 | 7 | gh-post-condition | gh pr view state (sole consumer: merge-state predicate) |
| pr_merge_state | L305-321 | 17 | gh-post-condition | last /pull/ comment -> PR merged/open/none |
| make_merged_of | L324-335 | 11 | gh-post-condition | memoised merge-state lookup |
| KIND_PREFIXES, CHRONIC_NIGHTS | L338-342 | 5 | map-only | drift-kind taxonomy for the nightly report |
| drift_kind | L345-347 | 3 | map-only | classifies a drift text |
| classify | L350-361 | 12 | map-only | nightly age of a drift item |
| summarize | L364-387 | 24 | map-only | nightly drift summary |
| HEAL_KINDS, HEAL_CELL | L390-391 | 2 | map-only | map column indexes |
| _gh_state | L394-409 | 16 | map-only | GH value used to heal a map cell |
| _cell_text | L412-418 | 7 | map-only | map cell text |
| _map_text | L421-423 | 3 | map-only | map cell text |
| _graphql | L426-431 | 6 | shared | GH mutation command builder (used by CLEAR cmd and by heal) |
| _edge | L434-438 | 5 | shared | GH mutation command builder (used by CLEAR cmd and by heal) |
| gh_fix_commands | L441-466 | 26 | map-only | commands that make GH match the map |
| upsert_cells | L469-483 | 15 | map-only | rewrites map cells |
| heal | L486-543 | 58 | map-only | --heal gh: upsert map; --heal map: print cmds to match map |
| edges_cmd: header | L546-548 | 3 | gh-post-condition | D3 verdict runner |
| edges_cmd: absent-from-map ids | L549-552 | 4 | map-only | EDGES-ABSENT is a map concept |
| edges_cmd: blockers / dependents | L553-575 | 23 | gh-post-condition | BLOCKER-*/CLEAR/KEEP + removeBlockedBy cmd |
| main: def, parser, --ids | L578-581 | 4 | shared | CLI plumbing |
| CLI --all-open | L582-584 | 3 | map-only | sweep of map rows |
| CLI --pr-id | L585 | 1 | gh-post-condition | PR-link target |
| CLI --fields, --backlog | L586-588 | 3 | map-only | mirror fields, map path |
| CLI --require-gh | L589-591 | 3 | map-only | refuse unverified mirror |
| CLI --summary/--out/--keys-out/--state/--date/--heal/--kind/--source | L592-607 | 16 | map-only | nightly + heal |
| CLI --edges | L608-610 | 3 | gh-post-condition | blocker verdicts |
| main: parse_args, --edges exclusivity | L611-613 | 3 | shared | CLI plumbing |
| main: default fields | L614 | 1 | map-only | mirror fields |
| main: heal/summary/date validation | L615-628 | 14 | map-only | map-only flags |
| main: fields, parse_backlog, ids from map | L630-632 | 3 | map-only | reads the map |
| main: merged_of + --edges dispatch | L633-635 | 3 | gh-post-condition | blocker decision |
| main: --heal dispatch | L636-640 | 5 | map-only | map heal |
| main: emit comment | L641 | 1 | map-only | summary grouping |
| main: stale_blockers emit (--all-open) | L642-643 | 2 | gh-post-condition | stale blocker edge |
| finish(): plain output | L645-652 | 8 | shared | output plumbing |
| finish(): summary/--out/--keys-out | L653-672 | 20 | map-only | nightly report files |
| main: offline branch | L674-685 | 12 | map-only | map internal consistency, require-gh |
| main: exit_code, loop head | L687-689 | 3 | shared | plumbing |
| main: absent-from-map / BT-LOCAL | L690-696 | 7 | map-only | map-row concepts |
| main: fetch_issue per id | L697-705 | 9 | shared | gh fetch plumbing |
| main: row exists but GH issue not found | L706-710 | 5 | map-only | map row with no issue |
| main: closed==done check | L711-712 | 2 | gh-post-condition | state vs done |
| main: compare + emit drift | L713-719 | 6 | map-only | map diff |
| main: summary all-fetch-failed guard | L720-724 | 5 | map-only | nightly report guard |
| main: ok_line, finish | L725-726 | 2 | shared | plumbing |
| __main__ | L729-730 | 2 | shared | plumbing |

Lines per class: map-only 377, gh-post-condition 153, shared 101 (total 631 non-blank). Mixed functions split by range: `compare` (L206-254: 38 map-only, 3 gh PR-link), `edges_cmd` (4 map-only, 26 gh), `main` (split in 25 rows), docstring (split by paragraph).

## 2. src/references/terminal-sync-invariant.md (34 lines)

Counted per sentence, each physical line apportioned by character share. Frontmatter (L1-5), title, headings, code fence and command (L7, 11, 14-16, 24, 29: 12 lines) are structural and shared, omitted from the table. Prose totals: map-only 7.06, gh-post-condition 3.09, shared 3.89 (14.04 prose lines). 17 map-only, 7 gh, 8 shared sentences.

| line | class | line weight | sentence / bullet |
|---|---|---|---|
| L9 | map-only | 0.29 | dual-write must leave GH and map in agreement |
| L9 | map-only | 0.37 | trailing mirror write drops; corruption propagates |
| L9 | shared | 0.35 | gate is a script exit code, not a checkbox |
| L12 | shared | 1.00 | scope: ids touched |
| L18 | shared | 0.40 | halt, do not close/ship |
| L18 | map-only | 0.60 | MIRROR-DRIFT map=x gh=y output |
| L19 | shared | 1.00 | pass every id the phase wrote |
| L20 | map-only | 1.00 | --fields subset of mirror fields |
| L21 | gh-post-condition | 1.00 | closed == done (open on GitHub, map=done) |
| L22 | gh-post-condition | 0.47 | PR-link comment with /pull/ URL |
| L22 | gh-post-condition | 0.53 | full /pull/ URL, bare #n does not count |
| L25 | map-only | 0.32 | upsert the missing write keyed by BT id |
| L25 | map-only | 0.14 | never append a row |
| L25 | gh-post-condition | 0.31 | stale blocker: remove map cell AND GitHub removeBlockedBy edge |
| L25 | shared | 0.13 | re-run until exit 0 |
| L25 | map-only | 0.11 | log [HEALED field BT-n] |
| L27 | map-only | 0.32 | --heal --source gh = map upsert for one kind |
| L27 | map-only | 0.22 | --source map prints gh commands to match the map |
| L27 | gh-post-condition | 0.21 | dropped gh issue close healed by gh issue close |
| L27 | map-only | 0.13 | manual kinds heal by hand |
| L27 | map-only | 0.13 | re-run once, no loop |
| L30 | shared | 0.17 | end-state is the citing workflow's |
| L30 | map-only | 0.31 | gate asserts GH and BACKLOG agree |
| L30 | shared | 0.52 | workflow decides conditional transitions; pass ids once writes done |
| L31 | map-only | 0.50 | offline: BACKLOG internal consistency only |
| L31 | map-only | 0.50 | offline is self-attested |
| L32 | shared | 0.32 | reconcile only reads GitHub |
| L32 | map-only | 0.68 | --heal writes the map only; GH fixes printed |
| L33 | gh-post-condition | 0.38 | edge stale only when --edges says CLEAR |
| L33 | gh-post-condition | 0.19 | KEEP edge never removed |
| L33 | map-only | 0.44 | map missing a KEEP edge = blocked_by drift |
| L34 | map-only | 1.00 | 0d nightly audit across all rows is advisory |

## 3. Call sites in workflows (src/workflows/)

Selection: every line citing `reconcile.py`, `terminal-sync-invariant.md`, the "terminal sync gate", `[MIRROR-*]`, `--heal` or a heal. Not counted as citations: `0d:3` (description verb "Reconcile sessions"), `0b:30` ("reconcile `BT-<parent>`" as a verb), `3a:76` ("unrelated drift" in a git commit), `4a:102` (draft rule, no gate cite), `3z:85`.

| file:line | what it cites | class | evidence |
|---|---|---|---|
| 0b-stop-session.md:27 | `--edges dependents --all-open`, clear `[CLEAR]` (map edit + `removeBlockedBy`) | gh-post-condition | blocker edge CLEAR by PR merge state; the map edit is incidental |
| 0b-stop-session.md:28 | gate `--fields blocked_by` on cleared dependents, heal, 3 attempts | map-only | map-vs-GH blocked_by equality |
| 0b-stop-session.md:31 | abandoned PR: gate `--fields status` after reopen/close | map-only | map-vs-GH status equality (the reopen/close writes are not the gate) |
| 0d-nightly-consolidation.md:16 | approved heals may modify files | map-only | heal writes the map |
| 0d-nightly-consolidation.md:49 | `--all-open --summary --out --keys-out` | map-only | nightly map sweep |
| 0d-nightly-consolidation.md:52 | CHRONIC item forces heal-or-decline | map-only | nightly age of map drift |
| 0d-nightly-consolidation.md:59 | recommendation order includes drift heals | map-only | heal batches |
| 0d-nightly-consolidation.md:60 | quick fix includes drift heal | map-only | heal batches |
| 0d-nightly-consolidation.md:66 | one recommendation per heal batch by kind | map-only | heal batches |
| 0d-nightly-consolidation.md:72 | apply heal per invariant §Heal | map-only | heal |
| 0d-nightly-consolidation.md:73 | `--heal --kind ... --source gh` | map-only | upserts map cells |
| 0d-nightly-consolidation.md:74 | `--source map` prints gh commands | map-only | makes GH match the map |
| 0d-nightly-consolidation.md:75 | manual kinds heal by hand | map-only | heal routing |
| 0d-nightly-consolidation.md:76 | re-run after batch heal | map-only | heal verification |
| 3a-version-planning.md:74 | gate `--fields milestone,blocked_by`, heal, 3 attempts | map-only | map-vs-GH equality |
| 3b-create-issue.md:116 | gate on created ids, all fields | map-only | map-vs-GH equality (map is the intended-state oracle, see ambiguity) |
| 3b-create-issue.md:117 | scratch cleanup on gate pass | shared | cleanup keyed to whichever gate exists |
| 3c-sprint-planning.md:30 | `--edges blockers` frontier | gh-post-condition | blocker verdict by merge state |
| 3c-sprint-planning.md:76 | gate `--fields status,milestone,labels,blocked_by` | map-only | map-vs-GH equality |
| 4a-verify-and-ship.md:84 | PR-link comment posted so the gate's `/pull/` check passes | gh-post-condition | PR-link comment on the issue |
| 4a-verify-and-ship.md:88 | `--edges dependents`, clear `[CLEAR]` (map + `removeBlockedBy`) | gh-post-condition | blocker CLEAR at ship |
| 4a-verify-and-ship.md:98 | epic flip to `in review`, then `--edges dependents` | gh-post-condition | status-label transition plus blocker CLEAR |
| 4a-verify-and-ship.md:100 | gate `--fields status,blocked_by --pr-id` | map-only | dominant effect is map-vs-GH equality; PR-link and closed==done sub-checks are gh (mixed line) |
| 4a-verify-and-ship.md:101 | non-zero: heal, 3 attempts, `[MIRROR-UNVERIFIED]` halt | map-only | heal loop |
| 3z-afk-loop.md:40 | blocker satisfaction from `--edges blockers` | gh-post-condition | blocker verdict |
| 3z-afk-loop.md:50 | frontier check `--edges blockers` | gh-post-condition | blocker verdict |
| 3z-afk-loop.md:88 | ship-only halt list incl. `[MIRROR-UNVERIFIED]`, terminal-gate failure | shared | generic halt routing |

Counts: map-only 17, gh-post-condition 7, shared 2 (26 lines). Map-only share of classified: 17/24 = 70.8%.

## 4. Logged incidents

Unit = distinct root cause (carried repeats across nights are one incident). Class = what actually went wrong. "tool defect" = the sync layer's own diff or gate misbehaved; scored map-only because the machinery belongs to the map-vs-GH diff.

| # | source | incident | what went wrong | class |
|---|---|---|---|---|
| 1 | docs/plans/terminal-sync-invariant-plan.md:14 (2026-09-15, origin) | live 3z run shipped a slice but dropped 4a Phase 5 step 6 (issue/BACKLOG `status:in review` sync) | the step carried both the GitHub label transition and the map row; the plan names "label transition" explicitly | gh-post-condition (soft: map row dropped too) |
| 2 | CleanTechHub nightly 07-25 | 10 stale blockers (BT-055 x9, BT-049 x1) on done blockers; 07-29 shows 0 | blocker edge never cleared at ship; detector was BACKLOG-only, heal protocol clears both sides | gh-post-condition (soft: both sides stale) |
| 3 | nightly 09-17 | BT-160 `milestone map=- gh=v1.2.0` | GH correct, map write dropped | map-only |
| 4 | nightly 09-17 (sessions 83bcb14d, b960c7d7) | gate ran before the PR-link comment, `pr-link absent` | GH comment not yet written when the gate ran | gh-post-condition |
| 5 | nightly 09-17 | BT-112/113/141 closed on GitHub, "reconciled as done" in the map | map lagged a correct GH close | map-only |
| 6 | nightly 10-05, 10-09, 10-13 (healed 10-13) | stale GH blocker BT-215 on 7 rows (BT-051, 005, 160, 204, 208, 212, 213) | `removeBlockedBy` on GitHub never ran (4a never cleared epic-level blockers; F5); map was cleared | gh-post-condition |
| 7 | nightly 10-05 | BT-197 `status map=in_progress gh=planned` | disagreement, direction and cause not recorded | ambiguous |
| 8 | nightly 10-09 | stale GH blocker BT-198 on BT-199 and BT-200 | GH edge to a done blocker never removed | gh-post-condition |
| 9 | nightly 10-09/13/19 | `parent map=None gh=BT-xxx` and `priority:*` gh_only on old rows BT-002..BT-081 (84 instance-nights) | rows never populated in the map | map-only |
| 10 | nightly 10-09/13/19 | `blocked_by map=[..] gh=[]` on 9 rows (25 instance-nights); 10-19 analysis: "blockers cleared on GitHub, update map" | GH cleared, map stale | map-only |
| 11 | nightly 10-09/13/19 | `status:*` in map labels reported as label drift (43 instance-nights) | reconcile.py false positive, fixed by BT-162 F1 (60096a7) | map-only (tool defect) |
| 12 | nightly 10-13/19 | every GH `size:*` is `size:medium` vs map small/large (27 instance-nights) | GitHub-side bulk change, cause unknown, "GitHub not assumed correct"; no post-condition would detect it | ambiguous |
| 13 | nightly 10-19 | milestone `v1.6.1` (map) vs `v2.0.1` (GH) on BT-047/043/030 | GH issues migrated, map stale | map-only |
| 14 | nightly 10-19 | BT-245 closed on GitHub (PR #246 merged), map `in review` | map not flipped to `done` after merge | map-only |
| 15 | nightly 10-09/13/19 | BT-098 `parent map=BT-081 gh=None` | missing `addSubIssue` or stale map, never resolved | ambiguous |
| 16 | git e5027c6 (2026-09-16) | reconcile exited 0 `[local-only]` when gh unreachable, gate verified nothing | gate fail-open (added `--require-gh`) | map-only (tool defect) |
| 17 | git 36eb8bb (BT-125, 2026-09-29) | real `gh` `blockedBy` shape `{nodes}` crashed `compare` | diff parsed GH shape wrongly | map-only (tool defect) |
| 18 | git 93c303f (2026-07-14) | false `[DRIFT]` alerts in 0d v1.0.6 | drift detector false positives | map-only (tool defect) |

Totals: 18 incidents. map-only 10 (6 real drift, 4 tool defects), gh-post-condition 5 (rows 1, 2, 4, 6, 8; rows 1 and 2 soft), ambiguous 3 (rows 7, 12, 15).

Other `git log --all --oneline | grep -i -E "drift|heal|mirror|reconcile"` hits (23 total), none an incident:
- Same incidents as above, not double counted: 60096a7 (BT-162, fixes rows 6 and 11), 0280bac (its tests).
- Features and tests of the sync layer: 8b89268 (BT-163 batch heals), a296f1d, aa577d2, 995a645, a908c37 (BT-142), c527222 (BT-144 follow-ups), a460b02 (BT-141).
- Unrelated "drift"/"mirror"/"reconcile": 1a3b94f (dist drift), 7ce95f4 (spec_lint) (paraphrased deferred mirrors), a604687 (DATABASE_SCHEMA parity), 685dacb (scaffold lockfile), e5849e7, 38a1517, c5b9ff9, a3ad356 (2c reconcile-specs), 6704629 (orphan-guard), 2372c5c (release for 36eb8bb), 7ce770b (4c audit).
- Design-motivated, not an incident: BT-188 (close at ship) and BT-192 (blocker timing) plans. They add `open on GitHub, map=done` and `--edges`, both gh-post-condition units, but their stated origin is the sub-issue progress bar and same-unit blocker timing, not a logged drift event.

## 5. Ambiguities resolved

1. Units that read `rows` but whose predicate is lifecycle-semantic (`ship_unit`, `effective_blockers`, `stale_blockers`, `closed_on_github`, `open_on_github`, `edges_cmd`): classed gh-post-condition ("re-point"), because the condition (blocker merged, closed == done, edge stale) is stated on GitHub state. The strict as-written reading is given as sensitivity in the totals block.
2. `compare` per-field checks (status, milestone, labels, blocked_by, parent): classed map-only. They are equality diffs of two stores. The same facts could be re-asserted as expected-state vs GitHub, but then the source of "expected" is each phase's draft, a new input, not existing code. This is the one place the hypothesis could be rescued: if 3a/3b/3c/4a post-conditions were rewritten against drafts, the gh-post-condition set would grow and the share would fall further, not rise.
3. Mixed call-site lines (4a:100, 0b:27): one class by dominant effect (equality diff -> map-only; edge decision -> gh).
4. Incidents with a soft gh call (rows 1, 2): the evidence names a GitHub-side miss (label transition, uncleared edge) but the map was stale too; counted gh-post-condition. Flipping them to map-only still gives 83.3% only if the 3 ambiguous also flip.
5. Duplicate counting: nightly repeats are one incident; the item-weighted figure is reported only as a secondary measure.
6. The nightly evidence is from CleanTechHub, a consumer project, because StratOS has no `docs/nightly/`. No StratOS-side drift incident exists in LEARNINGS/STATUS.
