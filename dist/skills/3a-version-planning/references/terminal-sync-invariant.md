---
description: Terminal sync invariant for workflows with a Publish/Commit & Sync phase (4a, 3b, 3c, 3a, 0b). Closes the completion-bias gap where one write silently drops. Gate: `.agents/scripts/reconcile.py`.
version: "2.1.0"
timestamp: 2026-11-09
---

# Terminal Sync Invariant

A workflow with multiple tracker writes in its terminal phase must leave the tracker in the intended state. Completion bias makes trailing writes (labels, links, edges) drop silently once the primary write succeeds. The gate is **deterministic**: an exit code, not a checkbox.

## Gate (`tracker: github` | `tracker: local`)
At the end of the sync phase, state the intended end state, then run it over the ids touched:

```bash
python .agents/scripts/reconcile.py --ids BT-<padded>[,...] [--pr-id BT-<padded>] [--fields <subset>] \
    --expect "BT-<n>:<field>=<value>;..." | --expect-file <F> [--with-edges blockers|dependents]
```

- `--expect` / `--expect-file` (one item per line, `#` comments): intended state. Fields: `status, milestone, labels, parent, blocked_by`; `labels` and `blocked_by` take comma lists. Conditional transitions (e.g. 4a's epic flip) are decided by the workflow.
- `--fields` = only fields written by the phase (3a passes `milestone,blocked_by`, never `status`). With `status`, also asserts closed = done (`open on GitHub, expect=done`).
- **Pass every id touched**, not just primary: 4a passes the slice, flipped epics, and dependents whose edges cleared.
- `--pr-id` = the id that must carry a PR link comment (shipped slice). Requires full `/pull/` URL or `Shipped on <branch> @ <sha>`; bare `#<n>` fails.
- `--with-edges blockers|dependents` adds D3 edge verdicts from the same read.
- Output: `[MIRROR-OK ...]` or `[MIRROR-DRIFT BT-<n>: <field> expect=<x> gh=<y>]`. Non-zero exit: **HALT, do not close or ship**; re-apply missing write and re-run (max 3 retries). Exit 3 (`[GH-UNAVAILABLE]`) halts likewise: GitHub mode never falls back to local.

## Boundaries
- **Never writes the tracker store.** `reconcile.py` only reads; fixes are tracker-verbs (`.agents/scripts/tracker.py`) writes performed by the workflow.
- **An edge is stale only when `reconcile.py --edges` says CLEAR.** A `[KEEP]` edge is kept until merge via 0b.
- **Local backend parity:** `reconcile.py` evaluates `--expect`, `--expect-file`, and `--with-edges` against `store.rows()`, reporting identical `[MIRROR-OK ...]` or `[MIRROR-DRIFT ...]` verdicts. Whole-store `issues.py check` remains available as an additional integrity check.
