# Board real-mouse drag-and-drop check (BT-221 worktree, HEAD f7fe45d)

Method: scratch store `C:\t\v5dnd\repo` (built by `C:\t\v5dnd\setup.py`; 4 cards: Plain, hostile-title, Second, Gated = status blocked with `blocked_by` Plain). Board rendered with `issues.py board --web`, served from `http://127.0.0.1:8765/board.html` (the Browser pane cannot drive `file://`), driven with the Browser pane's `computer left_click_drag` (real Chromium 152 input). A capture-phase listener (read-only, added through javascript_tool; product code untouched) logged native drag events: every `dragstart / dragenter / dragover / drop / dragend` had `isTrusted === true`. No synthetic DragEvent was needed; every case below is genuine native HTML5 DnD.

| # | Case | Result | Evidence |
|---|------|--------|----------|
| 1 | Plain card Planned -> In Progress | PASS | trusted dragstart(card) -> dragenter/dragover/drop on `col-in progress`; card moved; payload = header + `BT-LOCAL-plain-card -> in progress` |
| 2 | Drag it back to Planned | PASS | trusted drop on Planned card; card back in Planned; payload `""` (empty, textarea value) |
| 3 | Hostile title card -> In Progress | PASS | label textContent equals the hostile string exactly; 0 child elements in labels, 0 `<img>`, 0 `<b>`, 0 `on*` attributes, `document.title` still "repo Backlog Board" (no PWNED), no page errors; payload line is the slug id only (`BT-LOCAL-script-img-src-x-onerror-document-title -> in progress`; no `<` or `&` in payload) |
| 4 | Drop outside any column (page header H1) | PASS | dragenter on H1, no `drop` event, `dragend` fired; columns and payload unchanged; 0 stray `.dragging` / `.dragover` classes |
| 5a | Two moves -> payload -> `apply-moves -` | PASS | payload (`C:\t\v5dnd\payload1.txt`): hostile -> in progress, Second -> in review. `--dry-run` listed both; real apply: `planned -> in progress`, `planned -> in review`, `[APPLY-MOVES] applied 2 move(s)`, `issues.py check` = `[CHECK-OK 4 issue(s)]`, `board` text matches the DOM columns |
| 5b | BLOCKED card dragged to In Progress | PASS (behaviour documented; see note) | Gated card (status blocked, blocked_by Plain, Plain still `planned`) dropped on In Progress: board accepts silently (no warning, no refusal). Payload (`payload2.txt`, 3 lines incl. 2 already-applied no-ops) applied: `BT-LOCAL-gated-card: blocked -> in progress`, `blocked_by` still `[BT-LOCAL-plain-card]`, check OK. Also `-> done` applied with no `--force`. |

## Observations

1. **Blocker is not enforced by apply-moves or the board.** `cmd_apply_moves` (`src/scripts/issues.py:819-889`) only refuses: unparseable line, unknown id/status, `claimed_by` another branch (without `--force`), and epic/standalone `in review -> done` that is not merged. There is no `blocked_by` rule, so an unresolved-blocker card can go to `in progress`/`done`; the open blocker stays on the issue. `ready` / `blockers` still report it. Not covered by any test (`tests/scripts/test_issues.py` only uses `-> blocked`). Design question rather than a bug; if wanted, minimal fix is one more check beside line 872: refuse `target in ('in progress','in review','done')` when `any(effective_status(store.issues[b]) != 'done' for b in issue['blocked_by'] if b in store.issues)` unless `force`.
2. **The board never shows blockers.** `_render_board_html` puts `meta.blocked_by` into the data (`issues.py:544`) but `renderBody` (`board.html:459-462`) renders only priority/parent, so a user cannot see a card is blocked before dragging it. Cosmetic.
3. **Payload holds every change versus page load**, including moves already applied to the store (page is a static snapshot). Re-applying is idempotent (`old == target` is skipped), so harmless; verified in 5b.
4. `dragend` is not delivered to the source after a successful drop (the card is re-rendered and detached); harmless because the re-render clears `.dragging`. After a no-drop (case 4) `dragend` fires and the class is cleaned.

## Tooling limits (not product defects)

- Browser pane cannot open `file://` (static snapshot only, page tools refused); used a throwaway `python -m http.server` on 127.0.0.1:8765, since stopped.
- With a viewport emulation (1900x800) the drag end point is mapped in the wrong frame (drop landed on the search input): reset to desktop (750x863 CSS px, scrollable columns; used `.board-layout.scrollLeft` to bring columns into view).
- `left_click_drag` moves in 1-2 jumps and releases immediately. Drags with a vertical component sometimes released after `dragenter` but before the next `dragover`, so no `drop` fired (3 such misses, all in cases where start and end differ in y and the midpoint lands in a column gap). Horizontal drags (same y) were reliable. Those misses are a browser/tool timing artifact (the drop needs a `dragover` at the final position), not a board behaviour.
- Only the first 4 columns could be visible at once in the narrow pane; Done column was not a drop target in the mouse runs (done via `apply-moves` text only).
- No screenshot for case 4 (DOM/event evidence only).

Screenshots: `dnd\00-initial-board.jpg`, `01-case1-plain-to-in-progress.jpg`, `02-case2-dragged-back-planned.jpg`, `03-case3-hostile-in-progress.jpg`, `05-case5-two-moves.jpg`, `06-case5-blocked-card-payload.jpg`.
Scratch artefacts: `C:\t\v5dnd\` (setup.py, payload1.txt, payload2.txt, repo/).
