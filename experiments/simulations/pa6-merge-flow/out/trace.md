```
## init the tracker branch
$ issues.py init   (rc=0)
  [INIT pa6/issues]
## U1 ship: Shipped comment
$ issues.py comment BT-LOCAL-implement-slugify --body Shipped on feature/BT-LOCAL-slugify-helper-slugify @ e8530de258fa6f7dd34a222f2d565fcebf297648   (rc=0)
  BT-LOCAL-implement-slugify
## U1 ship: slice done
$ issues.py set BT-LOCAL-implement-slugify --status done   (rc=0)
  BT-LOCAL-implement-slugify
## U1 ship: slice close
$ issues.py close BT-LOCAL-implement-slugify   (rc=0)
  BT-LOCAL-implement-slugify
## U1 ship: epic in review
$ issues.py set BT-LOCAL-slugify-helper --status in review   (rc=0)
  BT-LOCAL-slugify-helper
## U2 ship: Shipped comment
$ issues.py comment BT-LOCAL-count-words --body Shipped on feature/BT-LOCAL-word-counter-words @ f0dc67a15524f74749fcf20a7005c8ab286d390b   (rc=0)
  BT-LOCAL-count-words
## U2 ship: slice done
$ issues.py set BT-LOCAL-count-words --status done   (rc=0)
  BT-LOCAL-count-words
## U2 ship: slice close
$ issues.py close BT-LOCAL-count-words   (rc=0)
  BT-LOCAL-count-words
## U2 ship: epic in review
$ issues.py set BT-LOCAL-word-counter --status in review   (rc=0)
  BT-LOCAL-word-counter
## U3 ship: Shipped comment
$ issues.py comment BT-LOCAL-title-case-a-string --body Shipped on feature/BT-LOCAL-title-caser-title @ 6ce6fdc5f339e6ee4865ccf7e765b380c2ad4822   (rc=0)
  BT-LOCAL-title-case-a-string
## U3 ship: slice done
$ issues.py set BT-LOCAL-title-case-a-string --status done   (rc=0)
  BT-LOCAL-title-case-a-string
## U3 ship: slice close
$ issues.py close BT-LOCAL-title-case-a-string   (rc=0)
  BT-LOCAL-title-case-a-string
## U3 ship: epic in review
$ issues.py set BT-LOCAL-title-caser --status in review   (rc=0)
  BT-LOCAL-title-caser
## U4 ship: Shipped comment
$ issues.py comment BT-LOCAL-clamp-a-number --body Shipped on feature/BT-LOCAL-clamp-helper-clamp @ 5e452bdbab215c77b1290ca26af95cf0099f7ec0   (rc=0)
  BT-LOCAL-clamp-a-number
## U4 ship: slice done
$ issues.py set BT-LOCAL-clamp-a-number --status done   (rc=0)
  BT-LOCAL-clamp-a-number
## U4 ship: slice close
$ issues.py close BT-LOCAL-clamp-a-number   (rc=0)
  BT-LOCAL-clamp-a-number
## U4 ship: epic in review
$ issues.py set BT-LOCAL-clamp-helper --status in review   (rc=0)
  BT-LOCAL-clamp-helper
## check (baseline)
$ issues.py check   (rc=0)
  [CHECK-OK 12 issue(s)]
## merged (baseline, nothing merged)
$ issues.py merged   (rc=0)
  [NO-MERGES]
## merged --close (baseline)
$ issues.py merged --close   (rc=0)
  [NO-MERGES]
## reconcile --edges dependents --all-open (baseline)
$ reconcile.py --edges dependents --all-open   (rc=0)
  [KEEP BT-LOCAL-document-slugify <- BT-LOCAL-implement-slugify] cross-unit: BT-LOCAL-implement-slugify PR not merged
  [KEEP BT-LOCAL-document-the-clamp-helper <- BT-LOCAL-clamp-a-number] cross-unit: BT-LOCAL-clamp-a-number PR not merged
  [KEEP BT-LOCAL-document-the-title-caser <- BT-LOCAL-title-case-a-string] cross-unit: BT-LOCAL-title-case-a-string PR not merged
  [KEEP BT-LOCAL-document-the-word-counter <- BT-LOCAL-count-words] cross-unit: BT-LOCAL-count-words PR not merged
## HUMAN merge U1: merge commit
$ git merge -q --no-ff feature/BT-LOCAL-slugify-helper-slugify -m Merge branch 'feature/BT-LOCAL-slugify-helper-slugify'   (rc=0)
## HUMAN push master (U1)
$ git push -q origin master   (rc=0)
## merged (after U1 merge commit)
$ issues.py merged   (rc=0)
  [MERGED BT-LOCAL-slugify-helper]
## merged --close (after U1)
$ issues.py merged --close   (rc=0)
  [MERGED BT-LOCAL-slugify-helper]
## reconcile --edges dependents --all-open (after U1)
$ reconcile.py --edges dependents --all-open   (rc=0)
  [CLEAR BT-LOCAL-document-slugify <- BT-LOCAL-implement-slugify] cross-unit: BT-LOCAL-implement-slugify PR merged
    cmd: python .agents/scripts/issues.py set BT-LOCAL-document-slugify --remove-blocker BT-LOCAL-implement-slugify
  [KEEP BT-LOCAL-document-the-clamp-helper <- BT-LOCAL-clamp-a-number] cross-unit: BT-LOCAL-clamp-a-number PR not merged
  [KEEP BT-LOCAL-document-the-title-caser <- BT-LOCAL-title-case-a-string] cross-unit: BT-LOCAL-title-case-a-string PR not merged
  [KEEP BT-LOCAL-document-the-word-counter <- BT-LOCAL-count-words] cross-unit: BT-LOCAL-count-words PR not merged
## apply the printed [CLEAR] cmd
$ issues.py set BT-LOCAL-document-slugify --remove-blocker BT-LOCAL-implement-slugify   (rc=0)
  BT-LOCAL-document-slugify
## HUMAN merge U2: squash
$ git merge -q --squash feature/BT-LOCAL-word-counter-words   (rc=0)
  Squash commit -- not updating HEAD
  
  Automatic merge went well; stopped before committing as requested
## HUMAN squash commit
$ git commit -q -m feature(BT-LOCAL-word-counter): Word counter (#2)   (rc=0)
## HUMAN push master (U2)
$ git push -q origin master   (rc=0)
## merged (after U2 squash)
$ issues.py merged   (rc=0)
  [PROBABLY-MERGED BT-LOCAL-word-counter] (squash commit fb3df74 matches id in origin/master; confirm before close)
## merged --close (after U2 squash)
$ issues.py merged --close   (rc=0)
  [PROBABLY-MERGED BT-LOCAL-word-counter] (squash commit fb3df74 matches id in origin/master; confirm before close)
## merged --close (re-run, idempotent)
$ issues.py merged --close   (rc=0)
  [PROBABLY-MERGED BT-LOCAL-word-counter] (squash commit fb3df74 matches id in origin/master; confirm before close)
## reconcile --edges dependents --all-open (after U2 squash)
$ reconcile.py --edges dependents --all-open   (rc=0)
  [KEEP BT-LOCAL-document-the-clamp-helper <- BT-LOCAL-clamp-a-number] cross-unit: BT-LOCAL-clamp-a-number PR not merged
  [KEEP BT-LOCAL-document-the-title-caser <- BT-LOCAL-title-case-a-string] cross-unit: BT-LOCAL-title-case-a-string PR not merged
  [KEEP BT-LOCAL-document-the-word-counter <- BT-LOCAL-count-words] cross-unit: BT-LOCAL-count-words PR not merged
## HUMAN merge U4 on the remote only (temp clone)
$ git merge -q --no-ff origin/feature/BT-LOCAL-clamp-helper-clamp -m Merge branch 'feature/BT-LOCAL-clamp-helper-clamp'   (rc=0)
## HUMAN push (temp clone -> bare)
$ git push -q origin master   (rc=0)
## HUMAN delete U4 branch on the remote
$ git push -q origin --delete feature/BT-LOCAL-clamp-helper-clamp   (rc=0)
## delete U4 branch locally
$ git branch -q -D feature/BT-LOCAL-clamp-helper-clamp   (rc=0)
## drop the U4 remote-tracking ref (fetch.prune equivalent)
$ git update-ref -d refs/remotes/origin/feature/BT-LOCAL-clamp-helper-clamp   (rc=0)
## merged (U4 merged remotely, project NOT fetched)
$ issues.py merged   (rc=0)
  [PROBABLY-MERGED BT-LOCAL-word-counter] (squash commit fb3df74 matches id in origin/master; confirm before close)
## merged --close (U4 not fetched)
$ issues.py merged --close   (rc=0)
  [PROBABLY-MERGED BT-LOCAL-word-counter] (squash commit fb3df74 matches id in origin/master; confirm before close)
## reconcile --edges dependents --all-open (U4 before fetch)
$ reconcile.py --edges dependents --all-open   (rc=0)
  [KEEP BT-LOCAL-document-the-clamp-helper <- BT-LOCAL-clamp-a-number] cross-unit: BT-LOCAL-clamp-a-number PR not merged
  [KEEP BT-LOCAL-document-the-title-caser <- BT-LOCAL-title-case-a-string] cross-unit: BT-LOCAL-title-case-a-string PR not merged
  [KEEP BT-LOCAL-document-the-word-counter <- BT-LOCAL-count-words] cross-unit: BT-LOCAL-count-words PR not merged
## git fetch -q origin
$ git fetch -q origin   (rc=0)
## merged (after fetch)
$ issues.py merged   (rc=0)
  [MERGED BT-LOCAL-clamp-helper]
  [PROBABLY-MERGED BT-LOCAL-word-counter] (squash commit fb3df74 matches id in origin/master; confirm before close)
## merged --close (after fetch)
$ issues.py merged --close   (rc=0)
  [MERGED BT-LOCAL-clamp-helper]
  [PROBABLY-MERGED BT-LOCAL-word-counter] (squash commit fb3df74 matches id in origin/master; confirm before close)
## reconcile --edges dependents --all-open (after U4 fetch)
$ reconcile.py --edges dependents --all-open   (rc=0)
  [CLEAR BT-LOCAL-document-the-clamp-helper <- BT-LOCAL-clamp-a-number] cross-unit: BT-LOCAL-clamp-a-number PR merged
    cmd: python .agents/scripts/issues.py set BT-LOCAL-document-the-clamp-helper --remove-blocker BT-LOCAL-clamp-a-number
  [KEEP BT-LOCAL-document-the-title-caser <- BT-LOCAL-title-case-a-string] cross-unit: BT-LOCAL-title-case-a-string PR not merged
  [KEEP BT-LOCAL-document-the-word-counter <- BT-LOCAL-count-words] cross-unit: BT-LOCAL-count-words PR not merged
## apply the printed [CLEAR] cmd
$ issues.py set BT-LOCAL-document-the-clamp-helper --remove-blocker BT-LOCAL-clamp-a-number   (rc=0)
  BT-LOCAL-document-the-clamp-helper
## check (final)
$ issues.py check   (rc=0)
  [CHECK-OK 12 issue(s)]
## list --all (final)
$ issues.py list --all   (rc=0)
  [{"id": "BT-LOCAL-clamp-a-number", "title": "Clamp a number", "status": "done", "labels": ["type:feature", "tier:slice", "mode:HITL", "size:small"], "milestone": null, "parent": "BT-LOCAL-clamp-helper", "blocked_by": [], "claimed_by": null, "created": "2026-11-04", "updated": "2026-11-04T14:06:04+00:00", "closed": "2026-11-04", "close_reason": "completed", "state": "CLOSED"}, {"id": "BT-LOCAL-clamp-helper", "title": "Clamp helper", "status": "done", "labels": ["type:feature", "tier:epic"], "milestone": null, "parent": null, "blocked_by": [], "claimed_by": null, "created": "2026-11-04", "updated": "2026-11-04T14:06:57+00:00", "closed": "2026-11-04", "close_reason": "completed", "state": "CLOSED"}, {"id": "BT-LOCAL-count-words", "title": "Count words", "status": "done", "labels": ["type:feature", "tier:slice", "mode:HITL", "size:small"], "milestone": null, "parent": "BT-LOCAL-word-counter" ...
## board --md
$ issues.py board --md C:\t\pa6-1\out\board.md   (rc=0)
  [BOARD] wrote C:\t\pa6-1\out\board.md
## board --web --out
$ issues.py board --web --out C:\t\pa6-1\out\board.html   (rc=0)
  [BOARD] wrote C:\t\pa6-1\out\board.html (12 card(s))
## apply-moves --dry-run (one move)
$ issues.py apply-moves C:\t\pa6-driver\moves-ok.txt --dry-run   (rc=0)
  BT-LOCAL-document-the-title-caser: planned -> in progress
  [APPLY-MOVES] dry run: 1 move(s) would apply, nothing written
## apply-moves --dry-run (drag unmerged epics to done)
$ issues.py apply-moves C:\t\pa6-driver\moves-refused.txt --dry-run   (rc=1)
  [ERROR] apply-moves refused, nothing applied:
    line 1: BT-LOCAL-title-caser is in review and not merged (its merge closes it; `issues.py merged --close` does it); use --force to override
    line 2: BT-LOCAL-word-counter is in review and not merged (its merge closes it; `issues.py merged --close` does it); use --force to override
```
