# Plan: close child slices at ship

Draft: Sonnet 5.5 (high). Reviewed and revised by Opus 5.5 against the source on 2026-10-19.

## Goal
GitHub's sub-issue progress bar counts only closed issues, so an epic shows 0% until its feature PR merges. Fix: 4a closes a child slice as `done` when it ships it. The epic (open, `in progress` → `in review`) carries "not on main yet" until the merge closes it.

Done when:
- shipping a child slice leaves it `status:done`, closed as completed, and BACKLOG `done`;
- the epic's progress bar advances one slice per ship;
- standalone issues behave exactly as today;
- `scripts/check.sh` is green.

## 0. Context in the epic
This is **slice 1 of 3** of the epic in `lifecycle-status-pr-scope-epic.md`, and it lands first on the shared branch.
- The epic plan's Shared decisions and its **Consistency rulings** override this file wherever they differ. That covers final version numbers and the 4a/3z/0b combined wording.
- `/3d` creates the branch from `main` per the epic plan; do not reuse `feat/BT-179-…`, which is already merged.
- Bumps are per file per PR (D5). This slice's bumps below are the minimum; later slices may raise a bump's level but never add a second bump.

## 1. Lifecycle

| Actor | Child slice | Standalone issue | Epic |
|---|---|---|---|
| 3d | `in progress`. If the slice is closed (rework), relabel first, then `gh issue reopen` | `in progress` | `planned → in progress` (never downgrade) |
| 4a ship | `status:done` label + BACKLOG `done`, then `gh issue close <n> --reason completed`; clear dependents' `Blocked by` | `in review` (unchanged) | — |
| 4a Epic Check | all siblings `in review\|done` → PR ready + epic `in review` | — | `in review` |
| Merge | `Closes #slice` is a no-op (kept as a safety net) | closes the issue → done | closes via `--close-parent` → done |

## 2. Decisions
- **(a) CI fix after ship: no reopen.** The slice keeps its shipped status. A reopen would regress the progress bar mid-ship.
- **(b) Review asks for changes to a closed slice: reopen it with 3d, don't mint a new slice.** This reuses the existing rework path.
  - Order: relabel to `in progress` (also remove `status:done`), update BACKLOG, then `gh issue reopen` as the last write. The board Action restores the board column from the labels in the `reopened` event (`sync-labels-to-project.yml` L70-73).
- **(c) Keep the `Closes #slice` lines.** They act as a safety net if the close step dropped, keep the PR's link to the issue, and standalone issues need them. No change to `pr_body.py`.
- **(d) Reads stay as they are (revised).** Epic Check (4a L88), the Draft rule (4a L102) and 3z L32/34/40/50 already accept `in review|done`. With no edit:
  - legacy in-flight `in review` slices keep working;
  - no tolerance prose is needed.
  - Only the stale clause "Build slices close only on merge" is dropped. *(The draft's rewrite of these reads to `done` was dropped.)*
- **Close inside step 7, not a new numbered step.** The close is the same status transition (`done ≡ closed`), so it doesn't need its own step. Renumbering steps 7-11 would ripple into ci-gate.md, the FAA reference and 4a's own citations. The new reconcile check (§4) is the deterministic backstop for a dropped close.

## 3. File changes (src/ only; bump each file once vs the new fork point)

### `src/workflows/4a-verify-and-ship.md` (minor)
- **L15 hand-off:**
  - child slice → `done` + closed on ship (the progress bar counts closed issues);
  - standalone → `in review`, and the merge closes it;
  - the epic stays open until the merge.
- **L85 step 7:**
  - Child slice: `gh issue edit <n> --remove-label "status:in progress" --add-label "status:done"`, update BACKLOG, then `gh issue close <n> --reason completed` (if connected; skip if already closed). Never use `not planned`: the board Action only maps completed closes to done.
  - Standalone: the current `in review` command.
  - Delete "Do not set `status:done` on ship …".
- **L86:** "now `in review`" → "now shipped (`done`; standalone `in review`)".
- **L88:** drop "Build slices close only on merge;". The rest stays.
- **L93:** "slice stays `in review`" → "slice keeps its shipped status".
- **L98:** "The epic moves to `done` on merge (`--close-parent`); its slices are already `done`."
- **L100 step 9:** update the coverage parenthetical only. The `--fields status,blocked_by` literal is unchanged.
- **Keep verbatim:**
  - the step 6 heading (the crosscheck indexes on it);
  - all `[...]` tokens;
  - "single writer for this edge".

### `src/workflows/3d-implement-issue.md` (minor)
- **L21:**
  - Add `--remove-label "status:done"` to the label edit.
  - Add: "Slice closed (rework of a shipped slice) → after the label edit and the BACKLOG update, `gh issue reopen <n>` (relabel first: the board Action restores the board column from the label at reopen)."
  - CI-fix clause: "its slice stays `in review`" → "keeps its shipped status; no reopen".

### `src/workflows/3z-afk-loop.md` (patch)
- L85: "move the slice to `status:in review`" → "ship-status the slice (child `done` + closed; standalone `in review`)".
- L86: "the last sibling reaches `in review`" → "… is shipped".
- L91: CI-fix "(the slice stays `in review`)" → "(keeps its shipped status)".
- L96: `_Done when:_` "all its slices `in review`" → "shipped".

### `src/workflows/0b-stop-session.md` (minor)
- **L26:** an epic or standalone issue is `done` only once its PR merged and the issue auto-closed. A child slice is already `done` + closed at 4a ship.
- **L29:** "slice still at `status:in review`" → "standalone issue or epic still at `in review`".
- **L30:** prompt for the epic `done` only once its feature PR has merged. Closed siblings alone are now the normal pre-merge state.
- **L31:** for an epic, take the PR from any child slice's `Shipped in PR` comment (the epic has none).
- **New Done-detection bullet, abandoned feature PR** (added 2026-10-20).
  - Trigger: an open epic whose feature PR is closed unmerged, with no open PR on its head branch.
  - Then prompt the user:
    - (1) Reopen the slices shipped in that PR. Relabel them `planned` first, then reopen; the epic goes to `planned`.
    - (2) Close the epic as not planned.
  - Act only on confirmation, then run reconcile on the touched ids.

### `src/references/ci-gate.md` (patch)
- L44: "Slice stays `in review`" → "Slice keeps its shipped status".

### `src/references/terminal-sync-invariant.md` (minor)
- Gate: with `--fields status`, the check also asserts `closed ≡ done`.
- Heal: `open on GitHub, map=done` heals with `gh issue close <n> --reason completed`. This is a GitHub write, so it runs only after the user approves (0d), or in-band in 4a.

### `src/memory-templates/BACKLOG_MAP.md` (minor; bump the `label-canonical` block too)
- L46: keep the `(lifecycle order` prefix (`test_status_label_contract.py` splits on it).
- Extend the parenthetical:
  - child slices go `in progress → done` (closed at ship);
  - `in review` = a standalone issue or an epic whose PR is open.

### Dropped from the draft
- **`pr-body-and-ship.md` read-back skip.** Not needed: `[NO-AUTOCLOSE]` is already informational, and 0b handles it.
  - Unverified: whether `closingIssuesReferences` lists closed issues. Check it once on the first real ship.

### Confirmed unchanged
- 0a, 3a, 3b, 3c, 0c, 0d, 3x;
- the FAA reference, issue-templates, github-issue-relations;
- `sync-labels-to-project.yml` (also byte-pinned to `.github/workflows`);
- rules, AGENTS.md;
- `pr_body.py`;
- jules-dispatch: no edit here. It treats CLOSED as done, which is **wrong** for blockers once this slice lands, because a child slice closes at ship before its code is on main. Slice 3 fixes it in the same PR, so the gap never reaches main.

## 4. Script: `src/scripts/reconcile.py`
This backstops a dropped `gh issue close`. Today the `--ids` gate never fetches `state`, and `--all-open` skips `done` rows, so nothing would catch a done-but-open slice.
- Add `open_on_github(row, gh)` next to `closed_on_github` (L121). It returns `"open on GitHub, map=done"` when `state == 'OPEN'` and the row is `done`.
- `KIND_PREFIXES` (L220): add `('open on GitHub', 'closed')`. This reuses the manual `closed` kind.
- `main()` ids path:
  - fetch with `want_state='status' in fields`. `fetch_issue` already takes `want_state` (L194); it is one more JSON field, not an extra call.
  - L551: `closed = (closed_on_github(...) or open_on_github(...)) if (args.all_open or 'status' in fields) else None`.
- Docstring: one line.

**Tests** (`tests/workflows/test_reconcile.py`):
- Update the 2-arg stubs at L574/L577 to `want_state=False`.
- Add a BACKLOG fixture row with status `done`.
- Cases:
  - unit `open_on_github`: done+OPEN → text; done+CLOSED, in review+OPEN, and no state → None;
  - `drift_kind("open on GitHub, map=done") == "closed"`;
  - `--ids --fields status,blocked_by`: done+OPEN → exit 1 `[MIRROR-DRIFT …open on GitHub, map=done]`; done+CLOSED → exit 0;
  - `--fields blocked_by` → `want_state` False; done+OPEN → exit 0.

**Crosscheck** (`tests/workflows/test_workflow_script_crosschecks.py`): one `# md-crosscheck:` test. It asserts that 4a's `gh issue close … --reason <x>` uses `completed`, and that the board Action maps `state_reason === 'completed'` to done. This guards a real coupling across files, not wording.

**Optional** (`tests/framework/test_sync_action.py`):
- `reopened` + `status:in progress` → in progress;
- `reopened` + `status:done` → done (documents why 3d relabels before reopening).

## 5. Verify
1. `python -m pytest tests/workflows/test_reconcile.py tests/workflows/test_workflow_script_crosschecks.py tests/framework/test_status_label_contract.py -n 0`
2. `python build/build.py && python build/validate.py .` (checks the per-file bumps and the markdown-only-test lint).
3. `bash scripts/check.sh` (the CI mirror, including dist drift).
4. 4a step 4 runs `scripts/release.py -y` at ship (minor plugin bump, expected 4.8.0 → 4.9.0). Commit regenerated `dist/` only via the build. Never hand-edit `dist/` or `.agents/`.

Commits (3d):
- `feat(BT-<n>): close child slices at ship so epic progress tracks shipped work`
- `feat(BT-<n>): reconcile flags a done row whose issue is still open`

## 6. Known gaps (accepted, unchanged from today)
- **A reopened slice leaves an already-ready feature PR ready.** The Draft rule only re-drafts it at the next 4a. This is the same hole as the old `in review` rework; 3d stays local and doesn't touch the PR.
- **Two Action runs on reopen (label edit, then reopen).** Order is deterministic only because the reopen is the last write. The labels stay the source of truth.
- **After the merge, the epic keeps its `status:in review` label until 0b/0d heal it.** This is existing behavior.
