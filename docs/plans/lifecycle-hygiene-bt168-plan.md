---
type: plan
title: Lifecycle Hygiene BT-168 Plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-13
version: "1.0.0"
---

# Plan: BT-168 lifecycle artifact-flow hygiene (H1, H2, H3 rest)

**Status:** planned and halted for the next session, at the user's request. BT-168 sits under standing epic BT-116 and ships in PR #161. Evidence: [`lifecycle-artifact-flow-audit.md`](lifecycle-artifact-flow-audit.md) §5. H4 and three of the H3 sub-items already landed in BT-166/BT-164.

**User decisions (2026-10-13):**
- **H1:** 3a owns release close, inside this slice.
- **H3:** `directions.html` becomes ephemeral, which reverses the earlier C3 "stays committed" decision in `lifecycle-run-defects-plan.md`.
- **H2:** hand-off lines become names-only, guarded by a generated two-way test.

**Bumps:** none of 1a (1.0.7), 2b (1.5.0), 3a (1.2.0), 3c (2.4.0), ROADMAP-template (2.0.0), plan-html (1.2.0) or okf-protocol (2.0.2) are bumped on this branch yet, so each gets one bump. 0b, 2a and the templates are already bumped, so they cost nothing extra. Verify with `git diff main -- <file>` before editing.

## Items (implementation order)
| # | Change | Files | Tests |
|---|---|---|---|
| 1 | **Blank `description:` fallback.** `okf_view._title_description` falls back to the first body paragraph: skip headings, blockquotes, HTML comments and tables; collapse whitespace; cut to about 160 chars. No template or workflow text changes. | `src/scripts/okf_viewer/okf_view.py`; add the current okf_view hash to `KNOWN_SHIPPED_SCRIPT_HASHES` in `scaffold.py` | `tests/scripts/test_okf_rebuild_indices.py`: 2–3 cases (explicit description wins, fallback paragraph, skipped constructs). Write them test-first. |
| 2 | **`directions.html` becomes ephemeral.** 2b renders it to `.tmp/render/docs/design/BT-<p>-directions.html`. The markdown `## Direction Alternatives (Considered)` stays the durable record. | 2b (~:48), okf-protocol (~:120, drop the example), plan-html (~:47, the example becomes `.tmp/…`), `tests/lifecycle-harness/assertions.py` (~:282 glob) | 2b path pin; no `docs/design/*directions.html` in `src/` |
| 3 | **H2 hand-off lines.** Lines in 1a, 2b, 3a and 3c become "Writes `<path>`. Read by: /x, /y." with no restated meaning. Body-only claims move into the body (3c's X.Y resolve rule → Phase 1.3) or are dropped (3a's false "3b gated to current release"). Also fix 1a's "Served/Pain matrices" wording (see ~1a:99) and 2b's missing 2c reader and `needs_spec→planned` write. New `tests/workflows/test_handoff_contracts.py`: a table {producer: artifact token} asserting that the named readers equal the workflow bodies containing the token (minus the producer and the orchestrators 2z/3z), and that the line has no `§` list. 2a's existing restated line stays out of the table (it has its own test). | 1a, 2b, 3a, 3c | the generated test |
| 4 | **H1 epic inputs.** 3a's `size` column (~3a:40) becomes `complexity (§12)`, from the PRD's existing Complexity Estimate. Cross-epic dependencies: 3a proposes `[NEW-DEP]` edges at its existing HITL halt, and on approval writes `addBlockedBy` plus the BACKLOG `Blocked by` column (copying 3c ~:74). Its reconcile gate adds `--fields milestone,blocked_by`. 2a still writes `Blocked by = —` at mint. | 3a | 3a has no `size` column; the amend-only clause and fields list are pinned |
| 5 | **H1 release close.** 3a's scale gate gains a condition: a release whose epics are all closed but whose `vX.Y.*` milestones are still open. In Phase 4, after the HITL halt, 3a closes them with `gh api -X PATCH repos/{owner}/{repo}/milestones/<n> -f state=closed`, then tags the ROADMAP row `[SHIPPED <date>]`. 0b step 1 adds one clause: when every epic in a `vX.Y.0` is done, suggest `/3a`. The milestone close is an outward write, so it runs only behind 3a's halt. | 3a, 0b (already bumped), ROADMAP-template (~:33, `[SHIPPED]` source wording) | gate-condition pin, 0b hint pin, close-command pin. The gh API path can't be tested offline, so assert wording only. |

**Loop:** run as one implementer pass (items 1–5; 3a is edited by items 3–5 with a single bump), then an independent review, fixes, gate (`build.py`, `validate.py`, full `pytest`) and commit as `feat(BT-168)` / `test(BT-168)`. After that, rerun the release, run `/4a` (HITL), and update the PR body (BT-162, BT-163 and BT-168 move from pending to shipped).
