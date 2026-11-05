| # | Assertion | Verdict |
|:--|:--|:--|
| A0.1 | build: every slice was claimed on its unit branch before ship, cleared by ship | PASS |
| A0.2 | build: each slice carries a `Shipped on <branch> @ <sha>` comment with the full tip | PASS |
| A0.3 | build: four epics in review/open, four dependents blocked, `check` OK | PASS |
| A0.4 | baseline: `merged` and `merged --close` print [NO-MERGES] | PASS |
| A0.5 | baseline: all four dependents KEEP, none CLEAR | PASS |
| A1.1 | U1 merge commit: `merged` lists exactly [MERGED <U1 epic>] | PASS |
| A1.2 | `merged` without --close writes nothing: U1 epic still in review/open | PASS |
| A1.3 | `merged --close` prints [MERGED <U1 epic>] only | PASS |
| A1.4 | U1 epic closed: done, completed, archived, claimed_by cleared | PASS |
| A1.5 | U1 slice closed: done, completed, archived, claimed_by cleared | PASS |
| A1.6 | U1 closed in exactly one tracker commit | PASS |
| A1.7 | U2, U3, U4 epics untouched (in review/open) | PASS |
| A1.8 | U1 dependent [CLEAR]; U2/U3/U4 dependents [KEEP] | PASS |
| A1.9 | applying the printed cmd clears U1 dependent's blocked_by; others stay blocked | PASS |
| A2.1 | U2 squash: `merged` reports exactly the advisory [PROBABLY-MERGED ... confirm before close] | PASS |
| A2.2 | `merged --close` prints the advisory and does NOT close U2 epic | PASS |
| A2.3 | advisory-only `--close` wrote no tracker commit | PASS |
| A2.4 | re-run is stable (same advisory line, tracker head unchanged) | PASS |
| A2.5 | U2 dependent stays [KEEP] (squash is not an ancestor merge; advisory never frees it); U3/U4 KEEP | PASS |
| A3.0 | setup: U4 branch gone locally and in remote-tracking refs; project origin/master is stale vs the bare master | PASS |
| A3.1 | before fetch: U4 not detected by `merged` nor closed by `--close` | PASS |
| A3.2 | before fetch: U4 dependent stays [KEEP] | PASS |
| A3.3 | after fetch: U4 detected [MERGED] via the recorded tip SHA (branch is gone), U2 still advisory, U3 absent | PASS |
| A3.4 | `--close` after fetch: same two lines | PASS |
| A3.5 | U4 epic closed: done, completed, archived, claimed_by cleared | PASS |
| A3.6 | U4 slice closed: done, completed, archived, claimed_by cleared | PASS |
| A3.7 | U4 dependent [CLEAR]; U2 and U3 dependents [KEEP] | PASS |
| A3.8 | applying the printed cmd clears U4 dependent; U2/U3 dependents stay blocked | PASS |
| A4.1 | U3 never merged: epic in review/open, never listed by any `merged` run | PASS |
| A4.2 | U2 squash epic still in review/open after every `--close` (never auto-closed) | PASS |
| A4.3 | U1 + U4 slices and epics all closed; U2 slice closed, U3 slice closed (shipped) | PASS |
| A4.4 | `issues.py check` OK at the end | PASS |
| A5.1 | `board --md` writes the Markdown board with Done and In Review columns and the open dependents | PASS |
| A5.2 | `board --web --out` writes an HTML page that names the units | PASS |
| A5.3 | `apply-moves --dry-run` of one move reports it and writes nothing | PASS |
| A5.4 | `apply-moves` refuses to drag the unmerged U3 epic and the advisory-only U2 epic to done | PASS |
| A5.5 | no tracker write by any view (head unchanged) | PASS |
| A5.6 | no `gh` call anywhere in the run | PASS |

**38 PASS / 0 FAIL of 38**
