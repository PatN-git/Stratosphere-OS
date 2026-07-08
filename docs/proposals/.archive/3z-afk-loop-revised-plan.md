# Revised Plan — AFK Loop (`3z_afk-loop`) + Status/Label Lifecycle

> **How to read this doc:** Each Part has three sections — **Why** (intent; do not skip), **What** (exact changes to make, each tagged with a finding ID + `file:line`), **Verify/Test** (the gate to pass before moving on). Do the Parts in order: **Part A first**, then Part B. Do not proceed past a red gate.

---

## Context & Locked Decisions (applies to both Parts)

The IDE implemented v1 of `3z_afk-loop` + the §1/§4 constitution edits. A rigorous review (three subagent tabletop simulations + static audit) found **5 blockers** and several majors, most rooted in a mismatch between the loop's ad-hoc progress words (`VERIFIED`/`blocked`) and the repo's real status-label model. Separately, the user locked an explicit kanban lifecycle. This plan fixes the label model first (Part A) because it dissolves several 3z blockers, then fixes the loop (Part B).

**Research grounding:**
- Dual-type validation lives in `src/scripts/validate_memory.py:207-227` (`primary_types`/`execution_modes` sets; exempts `size:large`). `type:NEEDS_SPEC` is a Primary Type there but used as a lifecycle state in `3c`/`1b`/`issue-templates`.
- No StratOS GitHub automation exists (only `build-guard.yml`). Status = **label**, transitions manual, no stale-label cleanup, no board auto-add. A proven reference Action exists at `CleanTechHub/.github/workflows/sync-labels-to-project.yml` (hardcodes IDs → must be generalized).
- The installer already has a brownfield label path: `Instantiate-StratosphereOS.md:199-241` "Checkpoint 6: Label Reconciliation".

**Decisions (LOCKED):**
1. **`needs_spec`** → reclassify `type:NEEDS_SPEC` → `status:needs_spec`; exempt `status:needs_spec` + `status:planned` rows from dual-type validation.
2. **First status** → keep `status:planned` (no rename). Lifecycle = `planned → needs_spec → in progress → blocked → done`.
3. **Projects sync** → build it NOW, generalized to work for any project with no per-project ID wiring.
4. **Label spelling** → space form `status:in progress` everywhere (matches registry + the working CleanTechHub option name); fix hyphenated `status:in-progress` in code.
5. **Supersession** → the `status:blocked` column replaces the earlier `type:AFK_CHECK` flag idea. `status:blocked` becomes a real 5th status.

---

# PART A — Status/Label Lifecycle Migration

## A1 · Why
Today "progress" is tracked two incompatible ways: the registry's `status:*` labels (`planned/in progress/done`) and the loop's in-memory words (`VERIFIED`/`blocked`), and `type:NEEDS_SPEC` is filed as a Primary *Type* even though it behaves as a lifecycle *state*. This mismatch is the root of 3z blockers **F2/F3/F6/F7** (unreachable completion criterion, broken local-only mode, invalid `status:blocked`, hyphen/space drift). Establishing one explicit, board-backed lifecycle — `planned → needs_spec → in progress → blocked → done` — as the single source of truth (labels), mirrored automatically to a GitHub Project, fixes those at the source and gives every workflow one vocabulary. Do this **before** Part B so the loop can be built on a correct model.

## A2 · What
Make these changes in `src/` only (never hand-edit `dist/`), each tagged with the finding it closes:

- **A2.1 — Registry** (`src/memory-templates/BACKLOG_MAP.md:35`): set Status = `status:planned, status:needs_spec, status:in progress, status:blocked, status:done`. Remove `type:NEEDS_SPEC` from the Primary Type line (`:30`). Preserve the "Label source of truth" operational bullets. *(Closes F6.)*
- **A2.2 — Validator** (`src/scripts/validate_memory.py:213-227`): drop `type:NEEDS_SPEC` from `primary_types`; **exempt rows whose status is `status:needs_spec` or `status:planned`** from the dual-type requirement (mirror the existing `size:large` exemption). No other validator logic changes (it ignores `status:*`).
- **A2.3 — Transitions + stale-label cleanup** (across workflows): every status write must **remove the prior `status:*` before adding the new one** (today they only add — latent bug, and required so A2.4's field mirror is deterministic). Touch points: `0a:19`, `2a:28`, `3c:19,61`, `3d:23`, `4a:80,82`, `0b:20`, `3z:38,47,48,55`. Standardize all to the **space form** `status:in progress` (fix hyphenated occurrences). *(Closes F7.)*
- **A2.4 — Generalized Projects sync Action** — NEW `src/github/sync-labels-to-project.yml` (project-instance template). Portable (no hardcoded IDs) by resolving IDs **by name at runtime**:
  - Trigger `issues: [opened, reopened, labeled, unlabeled]`; `actions/github-script@v7`.
  - Config via Variables + Secret: `vars.PROJECT_OWNER`, `vars.PROJECT_NUMBER`, `vars.PROJECT_OWNER_TYPE` (`org`|`user`), `secrets.PROJECT_TOKEN` (PAT with `project` scope — default `GITHUB_TOKEN` can't write Projects v2).
  - GraphQL: fetch `projectV2(number).fields` → build field-name→id + option-name→id maps live.
  - `addProjectV2ItemById` (auto-add issue; idempotent). For each `key:value` label, match single-select field by `key` and option by `value` (case-insensitive) → `updateProjectV2ItemFieldValue`.
  - Robustness: field/option not found → log + skip (never fail the run); project not found → fail clearly; `DRY_RUN` var logs intended writes without mutating. Option names should equal label values (`planned/needs_spec/in progress/blocked/done`) so no alias map is needed.
- **A2.5 — Brownfield migration (rides on Checkpoint 6, `Instantiate-StratosphereOS.md:199-241`):** the installer's Label Reconciliation surfaces this at setup:
  - **ADD** `status:needs_spec`, `status:blocked` (auto).
  - **MAP (rename)** `type:NEEDS_SPEC` → `status:needs_spec`, and legacy hyphen `status:in-progress` → `status:in progress`. A GitHub label **rename preserves issue assignments** → no per-issue loop. ⚠ Since A2.1 removes `type:NEEDS_SPEC` from the registry, Checkpoint 6 will offer MAP *or* DROP for it — instruct **MAP** (DROP would retire it).
  - **DROP** only after migrating issues off a label (Checkpoint 6 already states this).
  - Add three setup sub-steps Checkpoint 6 doesn't cover: (a) extend the Project's Status single-select with `needs_spec`/`blocked` options + install A2.4; (b) **opt-in** status backfill for label-less open issues (default `status:planned`, never forced); (c) a standalone "re-reconcile labels" entry so existing StratOS projects can adopt the lifecycle without a full re-install.
- **A2.6 — Build & propagate:** add a `copytree` for `src/github/*` → `dist/*/assets/templates/github/` in `build/build.py`; run `python build/build.py`. Bump `version`/`timestamp` on every changed `src/` file.

## A3 · Verify / Test  (gate after each — do not proceed on red)
- **A2.1 ✓** `python src/scripts/validate_memory.py` passes on the current backlog; Status line shows all 5; `type:NEEDS_SPEC` gone from Primary Type.
- **A2.2 ✓ (do BEFORE editing workflows)** add `tests/verify_scripts.py` fixtures: a `status:needs_spec` row with no execution mode PASSES; a `status:planned` backlog row PASSES; a normal slice still requires exactly one primary + one mode; a leftover `type:NEEDS_SPEC` is no longer a valid primary. `python tests/verify_scripts.py` green.
- **A2.3 ✓** `grep -rn "status:in-progress" src/` returns **zero**; spot-check that `0a/3d/3c/4a/0b/3z` remove-old-before-add; dry-run one transition on a scratch issue → only one `status:*` remains.
- **A2.4 ✓** `DRY_RUN=true` pointed at CleanTechHub's board resolves fields/options **by name, no hardcoded IDs**, and logs intended writes; then a throwaway project: opening an issue auto-adds it, a `status:*` change moves the card, a missing option is **skipped, not failed**.
- **A2.5 ✓** `gh label list` shows `status:needs_spec` + `status:blocked`; migrated `BACKLOG_MAP.md` + relabeled issues validate; no orphan `type:NEEDS_SPEC`.
- **A2.6 ✓** `python build/build.py` exits 0; `dist/*/assets/templates/github/` contains the Action; `python build/validate.py` + the build-guard workflow green; versions/timestamps updated.
- **Part A exit gate:** `validate_memory.py` + `verify_scripts.py` both green on a fixture backlog exercising all 5 statuses.

---

# PART B — `3z_afk-loop` Fixes  (do AFTER Part A)

## B1 · Why
The review proved `3z` v1 fails on literal execution: it ships from the wrong branch, its loop-completion criterion is unreachable, cosmetic slices have no legal path, and its subagent dispatches assume ambient state an isolated context can't see. Because `3z` is **prose executed by agents**, any ambiguity becomes a runtime failure (the three tabletop simulations reproduced all of it). These fixes make every path deterministic and reuse `4a`/`0a` correctly. Several label-level issues (F6/F7) are already closed by Part A.

## B2 · What
Edit `src/workflows/3z_afk-loop.md` (and the one `4a` line noted), each tagged with its finding:

- **B2.1 — [BLOCKER F1] Check out the feature branch before shipping.** In Step 3A, before `/4a` Phase 5 per feature, `git checkout <feat branch>` (the tree is left on the last-processed slice's branch; `4a:65` requires being on the parent feature branch). — `3z:52-54`.
- **B2.2 — [BLOCKER F2/F3] Terminal-outcome completion (not label-based).** A slice ends as `SHIPPED` (auto-PR), `VERIFIED-LOCAL` (local-only), or `status:blocked`. Loop-done = "every queued slice reached a terminal outcome" — replace "none left in-progress" (`3z:48`). The loop only *writes* `status:blocked`; shipped/verified-local slices stay `status:in progress` until a human merges (0b/merge → `done`). Makes local-only coherent: Step 3A skipped, slices recorded `VERIFIED-LOCAL`.
- **B2.3 — [BLOCKER F5] Cosmetic `[SKIP]` path.** Add `[SKIP]` to the Step 2B verdict enum (`3z:42`) and a Step 2C branch: `[SKIP]` (4a Phase 1 cosmetic bypass) → treat as `VERIFIED`, ship-eligible, no test required. Matches 4a's real output; stops cosmetic slices looping to blocked or faking `[PASS]`.
- **B2.4 — [MAJOR F10] Mode-aware ship auth.** Keep 4a's HITL Phase 4/5 halts for manual callers; add a recognized orchestrator pre-auth so `4a` Phase 5 skips its ship-confirmation halt under `3z`'s Step 1B authorization. Edit `4a:71`: "unless pre-authorized in Phase 4 **or by an orchestrating workflow**."
- **B2.5 — [MAJOR F8/F9] Self-contained dispatch + `/0a` targeting.** Both Step 2A/2B dispatches include the slice ID, **and** the orchestrator sets `STATUS.Active issue = BT-<padded>` before each dispatch (`/0a` reads the active task from STATUS; it has no issue arg — `0a:16-19`). Give the auditor (2B) the issue id + design-doc path (4a's INPUT). — `3z:38,42`.
- **B2.6 — [MAJOR F11] Auditor write hygiene.** The auditor's `/0a` loads context **read-only**; add to the 2B dispatch: "do not re-transition status or re-checkout." Prevents redundant GitHub label thrash. — `3z:42`.
- **B2.7 — [MAJOR F12] Gate the conflict scan on ship mode.** Step 3B `gh pr view` runs only in auto-PR mode; in local-only skip PR mergeability (optionally still compute cross-branch file overlap locally). — `3z:58-60`.
- **B2.8 — [MAJOR F13] Unknown/closed-issue preflight.** Add a Step 1B branch: issue not in BACKLOG_MAP / closed / nonexistent → `[ERROR] BT-<padded> not found or closed` + halt; never silently misclassify a missing-label issue as `type:HITL`. — `3z:27`.
- **B2.9 — [MINOR F4/F15] Work file → `.tmp/`, report before cleanup.** Move `docs/.3z-loop.work.md` → `.tmp/3z-loop.work.md` (AGENT.md §3; `docs/` risks being committed). Reorder so Phase 5 reads it **before** Phase 4 deletes it (currently delete `:64` precedes read `:68`).
- **B2.10 — [MINORS]**
  - F16: Phase 5 report distinguishes "verified by test" vs "cosmetic `[SKIP]`" so coverage isn't overstated. — `3z:39,68`.
  - F17: persist the implementer's `needs_manual_qa` (2A) into the work file so the Phase 5 checklist is reliable. — `3z:38,42,68`.
  - F18: HITL-halt message includes `/0a` + ordering (standalone-actionable). — `3z:27`.
  - F19/F20: update `tests/test_3z_orchestrator_simulation.py` to the new model + add cosmetic/local-only/branch-checkout cases; fix its UTF-8 print glitch; remove the duplicate "Do NOT run Phase 5." at `3z:42`.
- **Not a defect:** the `3d` `/4a`→`/4a_verify-and-ship` harmonization (v2.0.8) was authorized — leave as-is.

## B3 · Verify / Test
- **Tabletop ✓** re-run the **three subagent simulations** and confirm **F1–F13 do not reproduce**:
  - *batch auto-PR* → B2.1 (branch checkout), B2.2 (completion), B2.3 (cosmetic).
  - *local-only + HITL* → B2.2 (verified-local, no PR ops), B2.7 (no `gh` calls), B2.8 (unknown-issue error).
  - *auditor-contract* → B2.5 (dispatch carries slice id), B2.6 (read-only auditor), B2.3 (cosmetic verdict).
- **Test ✓** updated `tests/test_3z_orchestrator_simulation.py` passes (new model + added cases); UTF-8 glitch fixed.
- **Build ✓** `3z` version bumped; `build.py` propagates to both dist dirs + `versions.json`.
- **Part B exit gate:** one end-to-end dry simulation of a mixed sprint (pass / heal / circuit-break / cosmetic / HITL-skip across ≥2 features) yields a coherent ready-to-ship report with only registry-valid labels and no branch/ordering failures.

---

# PART C — Round 2 Fixes (post-implementation)

## C1 · Why
Parts A+B are implemented and pass the static validators + the structural test. But a mixed-sprint dry-simulation of the *actual prose* + a static pass found residual gaps that mostly undermine the new promise that **the board reflects real status**: the loop writes `status:blocked` to memory but never to the GitHub issue, and the "Single Status Invariant" is declared in `BACKLOG_MAP.md` but never enforced at the workflow write-sites (so transitions add a status without removing the old one — an isolated subagent won't infer the rule). Plus the installer wires the sync Action for brownfield only and never sets the secret/vars it needs. Fix all of these in one pass. (Decision: shipped-but-unmerged staying `status:in progress` is **accepted as-is** — no new review status.)

## C2 · What
- **C2.1 — [BLOCKER] Set the `status:blocked` LABEL on the GitHub issue at circuit-break** (not just BACKLOG_MAP + comment), removing the prior `status:*` first — otherwise a board keyed on `status:*` shows the blocked slice as `in progress`. — `3z:51`.
- **C2.2 — [MAJOR] Encode the Single-Status Invariant at every write-site.** GitHub labels are a **set** — adding `status:blocked` does NOT remove `status:in progress` (no native mutual-exclusion; the single-value constraint exists only on the downstream Projects field, where two status labels make the mirror nondeterministic). So each transition must explicitly remove-then-add, e.g. `gh issue edit <n> --remove-label "status:in progress" --add-label "status:blocked"`. The canonical rule stays in `BACKLOG_MAP.md:27`, but add the actionable remove-then-add step at each site (subagents run isolated and won't infer it). Sites: `0a:19`, `3d:23`, `3z` (2A dispatch + 2C blocked), `4a` (see C2.3). *(Optional belt-and-suspenders: the Action could strip other `status:*` on a `labeled` event so the board self-heals — but correctness must NOT depend on it, since greenfield/no-board projects run without the Action.)*
- **C2.3 — [clarify, per decision] Ship leaves status unchanged; "done" = issue closure.** Replace `4a:80`'s vague "set the issue/`BACKLOG_MAP.md` status appropriately" with: *"Leave the slice at `status:in progress`; do NOT set done on ship."* Accurate done-model (per `0b:20`): a **slice** becomes done when its PR merges and **auto-closes the issue** (`Closes #<slice>` in the PR body — ensure `4a` writes it); `0b` then removes the slice's `BACKLOG_MAP` row. **Slices never carry a `status:done` label** — `status:done` is applied only to **parent epics** in `BACKLOG_MAP`. `4a` performs no status-label write on ship.
- **C2.11 — [MAJOR] Board never reaches Done: the Action ignores issue close.** Because slice "done" = issue closure (C2.3), and the Action triggers only on `[opened, reopened, labeled, unlabeled]` (`sync-labels-to-project.yml:5`) — **not `closed`** — a merged/closed slice keeps its board Status at `in progress`. Fix: add `closed` to the Action triggers and set the Status field → `done` on close (and set it → the reopened status on `reopened`); OR require the project's native "Item closed → Done" Projects automation, documented at setup (C2.4/C2.5).
- **C2.4 — [MAJOR] Installer: board setup + Action install must apply to greenfield too.** Move Checkpoint 6's step 7 (board detect/extend, Action install, opt-in backfill) to a shared step run on **both** greenfield and brownfield paths. — `Instantiate…:206-210` (greenfield) vs `:245-250`.
- **C2.5 — [MAJOR] Installer must configure the Action, not just drop it.** Checkpoint 6 step 7(b): (i) copy `assets/templates/github/sync-labels-to-project.yml` → the project's `.github/workflows/`; (ii) `gh secret set PROJECT_TOKEN` + `gh variable set PROJECT_OWNER PROJECT_NUMBER PROJECT_OWNER_TYPE`. Without these the Action self-skips (no-op). — `Instantiate…:248`.
- **C2.6 — [MAJOR] Preflight: handle slices that are neither `type:AFK` nor `type:HITL`** (missing mode / `status:needs_spec` item) → explicit `[SKIP] BT-<padded> no execution mode — excluded` (halt with guidance if it's the single named issue). Today they fall through silently. — `3z:29`.
- **C2.7 — [MINOR] Preflight precedence clause:** state that execution mode (`AFK`/`HITL`) governs keep/skip; primary type (`feature`/`content`/…) is orthogonal (removes the `type:AFK, type:content` ambiguity). — `3z:29`.
- **C2.8 — [MINOR] `needs_manual_qa` = advisory, gated at merge.** Keep auto-ship (don't block the PR). Define it as *"human verification required before **merge**, not before ship."* Surface the manual-QA checklist **in the PR body** (via `4a` Phase 5's PR-body accumulation), not only the transient Phase-4 report, so the reviewer sees it where they decide to merge. Source the flag from the implementer (2A). (Optional rename `→ manual_qa_before_merge`.) — `3z:45,69`, `4a` Phase 5 PR body.
- **C2.9 — [MINOR] Fix `4a` Phase 5 duplicate step "3"** numbering (two step-3s). — `4a:71-72`.
- **C2.10 — [MINOR] Define the standalone "re-reconcile-labels" entry concretely** (a documented mode/flag), not prose only. — `Instantiate…:16`.
- **Note (accepted):** a previously `status:blocked` slice is re-queued on a later run (preflight excludes only `status:done`) — acceptable retry behavior; document it.

## C3 · Verify / Test
- Re-run the mixed-sprint dry-simulation and confirm: BT-203's **GitHub issue carries `status:blocked`** (and not `status:in progress`); every transition removed the prior `status:*`; a `status:needs_spec`/no-mode slice is explicitly `[SKIP]`ped; shipped slices remain `status:in progress` with open PRs.
- Installer: dry-walk **both** greenfield and brownfield → each installs the Action into `.github/workflows/` and sets `PROJECT_TOKEN` + the three vars; `DRY_RUN` sync resolves fields by name.
- `python tests/verify_scripts.py` + `python tests/test_3z_orchestrator_simulation.py` green — extend the harness with a no-execution-mode preflight case and an assertion that circuit-break sets the `status:blocked` label.
- `python build/build.py` + `python build/validate.py` green.

# PART D — `4a` Phase 5 Regression Fixes (Part C follow-up)

## D1 · Why
The Part C rewrite of `4a` Phase 5 (done to fix duplicate numbering, C2.9) went further and (a) **replaced the branch-safety gate** — the "never ship from `main`; must be on the feature branch" check that AGENT.md §4 and `3z` Step 3A depend on — with an **audit-isolation gate that belongs to Phase 2, not ship**, and (b) added a **Node-only `npm` test step**. Both must be corrected; R1 is a blocker because it breaks manual `3d→4a` shipping and silently dropped the on-`main` guard.

## D2 · What (exact edits to `src/workflows/4a_verify-and-ship.md` Phase 5)

**D2.1 — [BLOCKER] Restore the branch-safety gate as step 1.**
- FIND (current step 1, `4a:67`):
  > `1. Confirm the session has been read-only with respect to production code—i.e., you have not run `/3d_implement-issue` and have not edited files under the slice's source paths this session. If not, isolate: run in a clean workspace branch or subagent.`
- REPLACE WITH:
  > `1. **Branch isolation:** Enforce that the current branch is NOT `main`/`master` (`AGENT.md` branch rule) AND is the feature branch for this slice's parent. If on `main` → HALT and instruct the user to branch first.`
- Rationale: audit independence is already handled by Phase 2's Context Isolation Rule (`4a:25`). Phase 5 must NOT require a clean/isolated workspace — it commits uncommitted slice files and pushes, which requires the implementing workspace. The removed on-`main` guard is mandatory.

**D2.2 — [MINOR] Remove the hardcoded npm step.**
- FIND (current step 2, `4a:68`):
  > `2. Run `npm run lint` and `npm run test` (or build-tool equivalents).`
- ACTION: **Delete this line**, then renumber the remaining Phase 5 steps sequentially (current 3→2, 4→3, … 8→7). Tests were already driven green by `3d`/`micro-tdd`; a duplicate gate here is redundant and Node-only (StratOS is stack-agnostic).
- OPTIONAL (only if a final pre-push gate is genuinely wanted): instead of deleting, replace with a stack-agnostic line: `2. Run the project's lint + test suite (use micro-tdd's runner detection — npm/vitest/pytest/etc.); halt the ship on failure.` — but default is delete.

**D2.3 — [MINOR, optional] Close-reason guard in the sync Action.**
- In `src/github/sync-labels-to-project.yml` (`:54-55`), the `closed` handler forces Status→`done` for ANY close, including "closed as not planned." OPTIONAL: gate it on `context.payload.issue.state_reason === 'completed'` (else leave the field unchanged), so "not planned" closes don't show as Done.

## D3 · Verify / Test
- `grep -n "have not run" src/workflows/4a_verify-and-ship.md` → **no match** (the isolation-as-ship-gate line is gone).
- `grep -n "main.*master\|branch first" src/workflows/4a_verify-and-ship.md` → the branch-safety gate is present as Phase 5 step 1.
- `grep -n "npm run" src/workflows/4a_verify-and-ship.md` → **no match** (unless the stack-agnostic option was chosen).
- Phase 5 steps are numbered 1..N with no duplicates and no gaps.
- Dry-check the manual flow: running `/3d` then `/4a` in one session reaches Phase 5 and ships **without** demanding an isolated/clean workspace; `3z` Step 3A (checkout feature branch → `/4a` Phase 5) still passes the branch-safety gate.
- `python build/build.py` re-propagates `4a` to both dist dirs; `python build/validate.py` green.

## Out of Scope / Phasing
- Native Projects status-**field**-as-source-of-truth (vs labels) — not adopted; **labels remain source of truth**, the board mirrors them.
- Programmatic creation of the Project board + fields — documented (optionally scripted) at setup; the Action needs no IDs.
- Live-project data migration + secret/variable setup is a one-time op outside the framework templates.
