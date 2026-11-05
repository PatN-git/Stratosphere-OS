p='findings.md'
s=open(p,encoding='utf-8').read()
row=("| F40 | G4 | product (docs) | minor | post-merge-sync.md scopes the dependents pass to \"each epic/standalone issue merged\" (`reconcile --ids <merged ids> --edges dependents`), but a cross-unit edge on a child slice (S ← A1, KEEP at 4a ship) only becomes clearable at merge, and terminal-sync-invariant/tracker-verbs say 0b clears it then. A strict reading leaves S blocked forever. Haiku cleared it by judgment (the PR's `closingIssuesReferences` listed #2 too). | not fixed. Proposed: `--ids` = every id in the merged PR's `closingIssuesReferences` (epics, standalone and child slices). |\n")
s=s.replace("## Learnings", row+"## Learnings",1)
s+="""
## Follow-up G4 — merge_sim + 0b, GitHub (2026-10-28)
- Orchestrator: `merge_sim.py <root> 6` → PR #6 MERGED into bare master @ 2a53b20, closed #1 (#2 already closed at ship); then `git checkout master` in the project (operator action standing in for the human; local master NOT pulled — 0b has no pull step, so its suite step ran in a temp worktree at the feature tip; harmless).
- Haiku 0b (3.6 min, 128k): no wip → no resume note; merge sync with empty `Last Sync` → no date window (F18 rule worked); epic A → done; dependents CLEAR: B ← A (3a's NEW-DEP) and S ← A1 (see F40); gate `[MIRROR-OK BT-001,BT-003,BT-005]`; Last Sync = today; session line pruned; friction gate hit, LEARNINGS declined; **BT-222 entry** `- **[[G-001]] [ASSUMED] [2026-10-28]** Bucket key: … Avoid: hash key, shard key. Source: BT-001.`; retrofit not raised (no synonym in code); validate_memory clean; suggested `/3a` (release v1.0 all done).
- **stage_checks G4: all 19 PASS.** F27 (local post-merge) stays suspected: chain L was cut.
- Haiku skill_defects triaged: F40 logged; "same as 1b" points to the 1b workflow, and glossary-entry-rules.md is linked (trivial); empty-wip resume note and the suite-on-merged-branch case are wording nits.
"""
open(p,'w',encoding='utf-8').write(s)
