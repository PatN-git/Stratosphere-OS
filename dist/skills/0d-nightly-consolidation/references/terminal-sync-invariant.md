---
description: Terminal sync invariant for workflows with a Publish/Commit & Sync phase (4a, 3b, 3c, 3a). Closes the completion-bias gap where the high-salience GitHub write lands but the low-salience BACKLOG_MAP mirror / label transition drops. Backed by the deterministic gate `.agents/scripts/reconcile.py`.
version: "1.2.0"
timestamp: 2026-10-20
---

# Terminal Sync Invariant

A workflow that writes **both** GitHub and `.memory/BACKLOG_MAP.md` in its terminal phase must leave them in agreement. Completion bias makes the trailing mirror write drop silently after the GitHub call succeeds; the corruption then propagates to every downstream reader. The gate below is **deterministic** — a script exit code, not a self-attested checkbox (the same bias that skips the write skips a prose check).

## Gate
At the end of the sync phase, over the ids this phase touched:

```bash
python .agents/scripts/reconcile.py --ids BT-<padded>[,...] [--pr-id BT-<padded>] [--fields <subset>]
```

- Non-zero exit → **HALT. Do not close/ship.** The output lists each `[MIRROR-DRIFT BT-<n>: <field> map=<x> gh=<y>]`.
- **Pass every id this phase wrote**, not just the primary one — e.g. 4a passes the shipped slice **plus** each dependent whose `Blocked by` it cleared (slice or epic id) **plus** each epic it flipped to `in review`.
- `--fields` = only the mirror fields this phase wrote (default: all 5 — `status,milestone,labels,parent,blocked_by`). Scoping keeps a gate from false-blocking on drift in a field outside its concern (e.g. 3a passes `--fields milestone,blocked_by`, never `status`).
- With `--fields status` the gate also asserts closed ≡ done: a `done` row whose issue is still open on GitHub is drift (`open on GitHub, map=done`).
- `--pr-id` = the single id that must carry a PR-link comment (the shipped slice); co-passed ids are not required to carry it. A PR-link comment is one whose body contains the full `/pull/` URL (`https://github.com/<owner>/<repo>/pull/<n>`); a bare `#<n>` does not count.

## Heal
For each `[MIRROR-DRIFT]`, apply the missing write as an **upsert keyed by `BT-<padded>`** — find-or-replace the row/field. **Never append** (appending double-writes the row). A stale blocker is healed on both sides: remove the id from the map cell **and** the GitHub edge (`removeBlockedBy`). Then **re-run `reconcile.py` until it exits 0.** Log each fix as `[HEALED <field> BT-<n>]`.

Batch heal (0d, after the user approves): `reconcile.py --heal --kind <status|milestone|labels|parent|blocked_by> --source gh (--ids … | --all-open)` is that upsert for one kind, from GitHub, on the map only. When GitHub is the side to fix (the map is right), `--source map` prints the exact `gh`/GraphQL commands; run them only after the user approves. `open on GitHub, map=done` heals by `gh issue close <n> --reason completed` (a GitHub write: in-band in 4a; after user approval in 0d). Manual kinds (stale_blocker, closed, pr_link, absent, not_found, other) heal by hand. After a batch heal, re-run `reconcile.py --ids <healed> --fields <kind>` once; no loop.

## Boundaries
- **End-state is the citing workflow's, not this file's.** The gate asserts only that GitHub and BACKLOG *agree* for the touched ids — it never imposes a target status. Conditional transitions (e.g. 4a's epic-flip only when all siblings are `in review`) are decided by the workflow; only pass ids to reconcile once the phase's intended writes are done.
- **Offline / no `gh`** → the script checks BACKLOG internal consistency and exits 0 with `[local-only]`. There is no GitHub to cross-check, so this case is inherently self-attested — eyeball the row you wrote.
- **Never writes GitHub.** `reconcile.py` only reads it. `--heal` writes `.memory/BACKLOG_MAP.md` only (see Heal); fixes that belong on GitHub are printed as commands, never run.
- `/0d` runs the same audit nightly across all rows as a human-facing backstop — it is advisory, not an in-band substitute for this gate.
