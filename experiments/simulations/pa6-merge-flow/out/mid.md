
## Final `issues.py list --all` (final store; `issues.py check` = `[CHECK-OK 12 issue(s)]`)
```
BT-LOCAL-clamp-a-number                done       CLOSED completed  claimed_by=None blocked_by=[]
BT-LOCAL-clamp-helper                  done       CLOSED completed  claimed_by=None blocked_by=[]
BT-LOCAL-count-words                   done       CLOSED completed  claimed_by=None blocked_by=[]
BT-LOCAL-document-slugify              planned    OPEN   None       claimed_by=None blocked_by=[]
BT-LOCAL-document-the-clamp-helper     planned    OPEN   None       claimed_by=None blocked_by=[]
BT-LOCAL-document-the-title-caser      planned    OPEN   None       claimed_by=None blocked_by=['BT-LOCAL-title-case-a-string']
BT-LOCAL-document-the-word-counter     planned    OPEN   None       claimed_by=None blocked_by=['BT-LOCAL-count-words']
BT-LOCAL-implement-slugify             done       CLOSED completed  claimed_by=None blocked_by=[]
BT-LOCAL-slugify-helper                done       CLOSED completed  claimed_by=None blocked_by=[]
BT-LOCAL-title-case-a-string           done       CLOSED completed  claimed_by=None blocked_by=[]
BT-LOCAL-title-caser                   in review  OPEN   None       claimed_by=None blocked_by=[]
BT-LOCAL-word-counter                  in review  OPEN   None       claimed_by=None blocked_by=[]
```

## Deviations from the earlier live run (b5 parta.md)
- None in behaviour: the same output lines (`[MERGED ...]`, `[PROBABLY-MERGED ... (squash commit <sha> matches id in origin/master; confirm before close)]`, `[NO-MERGES]`, `[CLEAR]`/`[KEEP]`), the same KEEP for the squash unit's dependent and the unmerged unit's dependent, U4 invisible until `git fetch`, `check` OK.
- Differences in the rig, not the product: (1) the epics carry no `mode:` label (the earlier R1 builder bug), so `check` passed from the start; (2) ships were scripted for all four units (the earlier run used Haiku for U1/U2), so 4a's no-PR halts (D1/D2) are out of scope here; (3) the U4 remote-tracking ref was dropped too (as `fetch.prune` would), so after the fetch only the recorded tip SHA can detect it, a stricter check than the earlier one, which left the stale tracking ref; (4) added checks: advisory-only `--close` writes no tracker commit, `--close` closes in one commit, the views and `apply-moves` writes nothing and refuses to drag the unmerged/advisory epics to done.
- Not exercised here (as before): a squash message without the epic id in `(<id>)` form, and the 0b skill text itself.

## Command trace (essential; setup `create`/`claim`/branch commits omitted, their ids are in `C:\t\pa6-driver\out\units.json`)
