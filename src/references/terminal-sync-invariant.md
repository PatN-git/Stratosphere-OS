---
description: Terminal sync invariant for workflows with a Publish/Commit & Sync phase (4a, 3b, 3c, 3a, 0b). Closes the completion-bias gap where one GitHub write of a multi-write phase silently drops. Backed by the deterministic gate `.agents/scripts/reconcile.py`.
version: "2.0.0"
timestamp: 2026-10-27
---

# Terminal Sync Invariant

A workflow that makes several GitHub writes in its terminal phase must leave GitHub in the state the phase intended. Completion bias makes a trailing write (a label transition, a link, a blocker edge) drop silently after the high-salience one succeeds, and the corruption reaches every downstream reader. The gate is **deterministic**: a script exit code, not a self-attested checkbox.

## Gate (`tracker: github`)
At the end of the sync phase, state the intended end state, then run it over the ids the phase touched:

```bash
python .agents/scripts/reconcile.py --ids BT-<padded>[,...] [--pr-id BT-<padded>] [--fields <subset>] \
    --expect "BT-<n>:<field>=<value>;..." | --expect-file <F> [--with-edges blockers|dependents]
```

- `--expect` / `--expect-file` (one item per line, `#` comments): the phase's own intended state. Fields: `status, milestone, labels, parent, blocked_by`; `labels` and `blocked_by` take comma lists. The gate never imposes a target state: conditional transitions (4a's epic flip only when all siblings are `in review`) are decided by the workflow.
- `--fields` = only the fields this phase wrote, so a gate never false-blocks on a field outside its concern (3a passes `milestone,blocked_by`, never `status`). With `status` the gate also asserts closed = done (`open on GitHub, expect=done`).
- **Pass every id this phase wrote**, not just the primary one: 4a passes the shipped slice, each epic it flipped to `in review`, and the dependents whose blocker edge it cleared.
- `--pr-id` = the single id that must carry a PR-link comment (the shipped slice). A PR-link comment contains the full `/pull/` URL (`https://github.com/<owner>/<repo>/pull/<n>`); a bare `#<n>` does not count.
- `--with-edges blockers|dependents` adds the D3 edge verdicts from the same single batched fetch (4a's ship gate: slice, flipped epics and dependents in one call).
- Output: `[MIRROR-OK ...]` or one `[MIRROR-DRIFT BT-<n>: <field> expect=<x> gh=<y>]` per drift. Non-zero exit: **HALT, do not close or ship**; re-apply the missing write and re-run, at most 3 attempts. Exit 3 (`[GH-UNAVAILABLE]`, after three retries) halts the same way: GitHub mode never falls back to a local copy.

## Boundaries
- **Never writes GitHub.** `reconcile.py` only reads it; a fix that belongs on GitHub is a `tracker-verbs.md` write the workflow performs.
- **An edge is stale only when `reconcile.py --edges` says CLEAR.** A `[KEEP]` edge is never removed; it clears at merge via 0b.
- **The local backend has no gate.** Its map rows are the store and nothing is compared; only `reconcile.py --edges` runs there (blocker guards, clearing).
