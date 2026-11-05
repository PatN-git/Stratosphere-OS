---
type: plan
title: BT-240 v5.0.0 handoff plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-11-04
version: "1.0.0"
---

# BT-240 (S5 of BT-194): handoff plan for v5.0.0 (PR #216)

Status: proposed 2026-11-04 (not yet executed). Companion: `docs/plans/bt241-apply-moves-blocker-plan.md` (#241 lands in v5.0.0 as option A; this plan sequences it with the handoff).

Marks: **[V]** verified on 2026-11-04 by a command or file:line; **[U]** not verified. Outward actions (push, PR/issue edits, issue close, deletions, release edit, new issues) are flagged **needs the owner's OK** and batched in section 1.

## 0. Verified state (2026-11-04, HEAD `d51938d`)

- [V] PR #216: head `d51938d` == local HEAD, **ready (not draft)**, `CLEAN`, `verify-dist` and `install-harness-l1` SUCCESS, base `main`, title starts `BREAKING v5.0.0`. The branch is fully pushed (`git status -sb`: nothing ahead).
- [V] `origin/main` = `132dcb8`, an ancestor of HEAD; #231 and #235 heads are ancestors (folded, still open). `delete_branch_on_merge: true`; merge commit, squash and rebase are all allowed.
- [V] `build/build.py` `VERSION = "5.0.0"`; latest tag/release `v4.10.1`; no `v5.0.0` tag. `release.yml` runs on every push to `main`, no-ops if the tag exists, else builds, validates, checks dist drift and calls `softprops/action-gh-release@v2` with `generate_release_notes: true` and no `body` (notes = merged PR titles only).
- [V] The PR body has the explicit line `Closes #194.` (body line 16) plus `Closes` lines for 195-200, 218, 221, 222, 229, 234, 236-239. #240 and #241 are NOT closing refs; both are already sub-issues of #194 (`gh api repos/PatN-git/Stratosphere-OS/issues/194/sub_issues`). #241 is `status:needs_spec`, body still says `Parent: -`.
- [V] The PR body Notes still say #240/#241 are "planned" and "the owner decides whether they land before the merge" (both need the refresh). The "apply-moves blocker semantics (decision pending)" unverified item is in `docs/proposals/v5-completion-plan.md:30`, not in the PR body.
- [V] `RELEASING.md` v5.0.0 section (`:79-135`) has no Jules/3x line. `docs/proposals/v5-completion-plan.md` is stale (section 9 decision 1: enforcement out of v5.0.0; section 11 still says `51cb32f`/`4bd4fb7` not pushed, Stage 3 "groups 1-6", Stage 4 not started).
- [V] #240's own body expects the RELEASING.md and plan-status doc edits to be committed with this slice.
- [U] Whether GitHub flips #231/#235 to merged on the #216 merge; whether `scaffold --update` prunes a consumer's installed `3x-jules-dispatch` (likely via orphan pruning, `scaffold.py:1149-1202`); the size of `C:\t` (135 entries; about 1.8 GB per the issue).

## 1. Owner decision round (ONE round, 7 decisions, each with a recommendation)

| # | Decision | Recommendation |
|:--|:--|:--|
| D1 | #241 = option A (refuse guarded moves while a blocker is open; definition `effective_blockers` + `edge_verdict != OK`, judged on the batch end state; blanket `--force`), landing in v5.0.0 | Yes. Fallback B only if you accept a documented gap and a behaviour change on a released command in 5.1 |
| D2 | Second epic FAA when #241 ships (4a Epic Check, `4a-verify-and-ship.md:94-95`) | Run the 4a rule as written (cost 5-12% **[U]**); alternative: a scoped FAA (children #236-#241 plus delta since the first FAA) recorded as a deviation in the PR body. Pre-authorize `gh pr ready --undo` if it finds gaps >= 80 |
| D3 | OK for the pre-merge outward batch: (a) rewrite the #241 body to option A and flip `status:needs_spec` -> `status:planned`; (b) post the #240 per-item comment and close #240 `status:done`; (c) push the branch (fast-forward) and let 4a rebuild the PR #216 body (head, `test:`, slices incl. BT-241, Notes) and set #241 done/closed, #194 `in review` | Yes, all three |
| D4 | OK for the post-merge batch: edit the v5.0.0 Release body (section 5), fix stale status labels on #194/#222/#229/#234 (`set_status done`), and note-and-close #231/#235 if GitHub did not flip them | Yes |
| D5 | Cleanup (after the merge): backup target (a plain local folder, not OneDrive-redirected `Documents` **[U]**, e.g. `C:\stratos-v5-evidence-2026-11-04\`), then the listed batches (section 7) one by one | Yes: backup first, then batch 1, batch 2, worktrees/branches |
| D6 | OK to open new issues for the appendix follow-ups marked "new issue" (after the merge; one issue per group, not per line; none under #10/#12/#13/#14/#17/#116) | Yes, after v5.0.0 ships |
| D7 | Keep the CleanTechHub manual-evidence numbers (4 gh calls, 2.9 s vs 13 calls, 9.6 s) in the public release notes | Strike them (manual evidence, scratch file) |

Owner-only actions, not decisions: the merge (**Create a merge commit**, never squash/rebase; keep the title `BREAKING v5.0.0: ...`); `claude plugin validate .` on a machine with the `claude` CLI (absent here; paste the result in the #240 comment or a later comment); deleting `PatN-git/stratos-smoke-20261030` (`gh repo delete` needs `delete_repo` scope, irreversible: the agent never runs it).

## 2. Goal and exit criteria

Goal: the owner merges #216 with no open decision; #241 and the doc debt are in the same push; nothing is lost when scratch is cleaned; consumers update later from a written checklist.

Exit criteria:
1. D1-D7 answered in chat.
2. #241 shipped (companion plan), #240 closed BEFORE that ship with a per-item comment (done / owner action with the exact command / deferred with reason) for each item of #240's Logic Layer.
3. Pre-merge gate green: head == PR head, ready, CLEAN, both checks SUCCESS, `origin/main` still `132dcb8`, `VERSION 5.0.0 > 4.10.1`; `closingIssuesReferences` contains 194 and 241, not 240.
4. Release notes text exists (section 5); the PR body migration pointer is intact.
5. After the merge: section 6 checks pass or failures are reported; cleanup done with OK or left as owner actions with commands.

## 3. Ordered steps

Owner: user = the human; lead = lead session; impl = Sonnet implementer (no git writes); sub = read-only subagent. Quota = share of one 5-hour window **[U]**. Freeze `main`: nothing else merges before #216.

| # | Step | Owner | Outward? | Verify | Quota |
|:--|:--|:--|:--|:--|:--|
| 1 | Read usage; confirm nothing moved: `git status --short` empty, `git fetch -q origin`, `git rev-parse HEAD origin/improvement/BT-194-tracker-backend-no-map` equal, `git merge-base --is-ancestor origin/main HEAD` | lead | no | commands as written | <1% |
| 2 | Decision round (section 1) | user | n/a | answers in chat | <1% |
| 3 | Rewrite #241 body to option A, flip to `status:planned` (companion step 1) | lead | **needs the owner's OK** (D3a) | `gh issue view 241 --json labels,body` | 1% |
| 4 | 3d on #241 on the existing branch (RED -> GREEN -> docs -> `check.sh` -> local commits), companion steps 2-5 | impl + lead | no | companion section 4 criteria; `check.sh` ALL CHECKS PASSED | 5-7% |
| 5 | Docs commit: RELEASING.md "Removed" line (Google Jules integration: `3x-jules-dispatch`, dispatch pack, no replacement), release-note lines for section 5 additions if RELEASING lacks them, `v5-completion-plan.md` sections 9/11 final state; commit type from #240's `type:` label, `<type>(BT-240): ...` | lead | no | read-back diff | 1% |
| 6 | CLI re-check of DnD case 5b on `C:\t\v5dnd` (before any cleanup) (companion step 7) | lead | no | exit codes per companion | 1% |
| 7 | Delta audit-only on `d51938d..HEAD` (companion step 8) | sub | no | `[PASS]` | 2-3% |
| 8 | Draft artifacts in `.tmp\handoff\`: `release-notes-v5.0.0.md` (section 5), `240-comment.md` (template, section 8), `cleanup-commands.ps1` (section 7, NOT executed) | lead | no | files exist; checklist commands match `RELEASING.md` v5.0.0 | 2% |
| 9 | Post the #240 comment and close #240 `status:done` (BEFORE the #241 ship so the Epic Check sees every sibling shipped) | lead | **needs the owner's OK** (D3b) | `gh issue view 240 --json state,labels,comments`: CLOSED, `status:done`, comment present | 1-2% |
| 10 | 4a ship-only for #241: suite record, push (fast-forward), Epic Check + FAA on #194 (per D2), CI gate, body rebuild (keep `Closes #194.`, add `Closes #241.`, no `Closes #240`, Notes refreshed), #241 done + closed | lead | **needs the owner's OK** (D3c) | `gh pr view 216 --json headRefOid,isDraft,mergeStateStatus,statusCheckRollup,closingIssuesReferences,body` | 3-4% + FAA 5-12% |
| 11 | `agy plugin validate dist` (expect `[ok]`, 27 skills); repeat step 1 plus the gate in exit criterion 3 right before the merge | lead | no | as stated | 1% |
| 12 | Merge #216 with **Create a merge commit**; run `claude plugin validate .` when a CLI is at hand | user | owner only | section 6 | n/a |
| 13 | Post-merge reads (section 6); writes per D4 | lead | **needs the owner's OK** per write | section 6 table | 3-4% |
| 14 | Edit the v5.0.0 Release body (section 5) | lead | **needs the owner's OK** (D4) | `gh release view v5.0.0 --json body` contains the BREAKING section | 1% |
| 15 | Backup, then cleanup batches (section 7) | lead | **needs the owner's OK** per batch (D5) | section 7 verify | 1-2% |
| 16 | Open follow-up issues (appendix) | lead | **needs the owner's OK** (D6) | `gh issue list` | 1-2% |
| 17 | Update auto-memory: `MEMORY.md` index and `project-v5-completion-plan.md` (v5.0.0 shipped, follow-ups, consumer update pending) | lead | no | index line updated | <1% |

Total before the merge about 18-32% of a window with the FAA (about 13-20% without); after about 6-9%. Wall time about 2-3 h before the merge including CI (about 5-10 min per run) and `check.sh` (about 321 s). Consumer updates stay deferred (owner rule).

## 4. Consumer update checklist (user runs it, only when the owner decides to update; nothing here is urgent)

Order from `RELEASING.md` v5.0.0 ("Upgrade order for a consumer"): StratOS's own install first, then each consumer.
1. StratOS itself (already `tracker: github`, no `migrate`/`tracker_switch`): refresh the plugin/skills copy by the project's install method **[U]** which path applies; `python .agents/scripts/scaffold.py --update`; expect a `needs_review_constitution` notice (AGENTS.md section 4 wording), an AGENTS.md merge review (it halts in this repo today; `.agents/` scripts were refreshed by copy, per the PR `post_merge:`) and an unmarked-STATUS notice: accept the trimmed STATUS 0b proposes, `git rm --cached .memory/STATUS.md` if tracked.
2. CleanTechHub (from its project root, after the plugin update): `scaffold.py --update` (same notices); check `tracker:` in `.memory/ARCHITECTURE.md` first **[U]**; `issues.py migrate` only if it has a `BACKLOG_MAP.md` and no `tracker: github`; `tracker_switch.py` (dry run), review, then `--apply` (skip if it stays `tracker: local`); then `PatN-git/cleantech_jobs#267` (glossary cleanup, runs after `scaffold --update`).
3. Removed v4 pieces that now fail: `reconcile.py --heal/--summary/--require-gh`, `nightly_state.py drift`, 0d's drift check: do not call them from custom scripts.
4. A new local-tracker project **[U]** (content not fixed anywhere read): setup asks the tracker backend, pick `local`; `issues.py init`; work with `issues.py`; connect `gh` later and use `tracker_switch.py`; merge release PRs with a merge commit so `merged --close` works.
5. After consumers move: the `cleantech_jobs` measurement and the PR body `after merge:` items are closed by the user.

## 5. Release notes for v5.0.0 (paste after `release.yml` finishes)

Mechanism: `release.yml` creates the Release with generated notes only. After it finishes: `gh release view v5.0.0 --json body --jq .body > .tmp\handoff\generated.md`, prepend the text below, `gh release edit v5.0.0 --notes-file .tmp\handoff\release-notes-v5.0.0.md` (**needs the owner's OK**, D4; the UI works too). Check: not draft, not prerelease, Latest. Fill `<N>`/`<head>` from the final head's suite record.

```markdown
## BREAKING: StratOS v5.0.0 - tracker backends without BACKLOG_MAP

With `tracker: github`, GitHub is the only store of issue state: no `BACKLOG_MAP.md`; workflows read through scoped `gh --json` queries and a post-condition gate (`reconcile.py --expect`) checks each multi-write phase. A new local backend (`tracker: local`) never touches GitHub and keeps one markdown file per issue (frontmatter, full body, comments) on the `<repo>/issues` branch, read and written only through `python .agents/scripts/issues.py`.

### What is new
- `tracker: github | local` in `.memory/ARCHITECTURE.md` (set by `stratosphere-setup`).
- `issues.py` verbs for the local tracker: `get`, `list`, `wip`, `children`, `blockers`, `ready`, `branch`, `create`, `set`, `comment`, `claim`, `close`, `reopen`, `label`, `init`, `check`, `sync`, `migrate`, `merged`, `board`, `apply-moves`.
- `tracker_switch.py`: move a local tracker to GitHub (dry run by default, `--apply` writes; safe to re-run).
- `issues.py board [--md | --web]` kanban view with a display-only "blocked by" badge; `apply-moves` writes drag-and-drop moves back and refuses a move into in-progress, in-review or done while a blocker is open, unless `--force`.
- `merged [--close]` closes issues by git ancestry: merge the release PR with a **merge commit**, not a squash (a squash only gives an advisory `[PROBABLY-MERGED]`).
- `ice_read.py` computes ICE on read (both backends); one combined, faster ship gate in 4a.
- `STATUS.md` holds folder state only; a task's progress is a resume note on its issue. Old-format STATUS files keep working and lint-warn until trimmed.
- Glossary writer rules in one shared reference; `validate_memory` warns on glossary fields other than `Avoid:` / `Source:`.
- Scaffold installs `.memory/** text eol=lf`.
- A batch of 33 one-clause wording fixes from the live-test backlog.

### Default every consumer hits
An install with a `BACKLOG_MAP.md` and no `tracker:` key resolves to `local`; `scaffold --update` prints a NOTE. Run `tracker_switch.py` (dry run, then `--apply`) to use GitHub.

### Removed (no shims)
- The `BACKLOG_MAP.md` template and the map-vs-GitHub diff; `reconcile.py --heal`, `--summary`, `--all-open --summary`, `--require-gh`.
- `nightly_state.py drift` and the `drift` key of `.last-run.json`; 0d's backlog drift check and heal.
- The Google Jules integration: the `3x-jules-dispatch` skill, its tests and dispatch pack. Projects using Jules dispatch must stop; there is no replacement.

### Upgrade (updating the plugin alone is NOT enough)
Order: StratOS's own install first, then each consumer (details: RELEASING.md, section "v5.0.0").
1. `python .agents/scripts/scaffold.py --update`. Expect a `needs_review_constitution` notice (AGENTS.md section 4 wording) and an AGENTS.md merge review; accept the trimmed STATUS file 0b proposes and untrack a tracked one (`git rm --cached .memory/STATUS.md`).
2. A project with a `BACKLOG_MAP.md` and no `tracker: github`: `python .agents/scripts/issues.py migrate` (the map moves to `.memory/archive/`), or stay local with `tracker: local`.
3. To use GitHub issues: `python .agents/scripts/tracker_switch.py` (dry run), then `--apply`.
4. Migrated issues carry the map row's fields, ICE metrics and `Refs:`; issue bodies the map never stored cannot be recovered.

### Known gaps (not verified in this release)
- Antigravity host run of the v5 skills; `claude plugin validate` was not run (CLI not available on the build machine); `agy plugin validate dist` passes (27 skills).
- Concurrent worktrees on the `<repo>/issues` branch; a real v4 -> v5 consumer upgrade; `resume_note` on threads over 30 comments; F35 retry on a real gap at the final code.
- Windows access-violation flakes (exit 3221225477) in subprocess tests on the dev machine pass alone and in CI.

### Verification summary
Full local suite (`scripts/check.sh`) <N> tests plus install-harness L1 155/0 at <head>. Live Haiku regressions at pin `8c1a7ae` (before the folds and the Stage 3 fixes): L1 33/33, L2 29/29, L3 51/51, L5 21/21. Real GitHub smoke on a throwaway repo: three rounds, about 260 verb records, 0 blocking failures. CI green on PR #216.

Next: v5.1.0 (Antigravity install/marketplace work, PR #232, and BT-217) after a real Antigravity test.
```

Corrections from the earlier draft: not "205 verb records" (three rounds, about 260 **[V]** PR body); test count is the final head's, not 1144; live-suite numbers are pinned to `8c1a7ae` **[V]** PR body.

## 6. Post-merge verification (agent, read-only first; writes per D4)

| Check | Command | Expected |
|:--|:--|:--|
| Merge commit | `gh pr view 216 --json state,mergedAt,mergeCommit,title`; `git fetch origin; git cat-file -p origin/main` | MERGED; 2 parents; title starts `BREAKING v5.0.0` |
| Release workflow | `gh run list --workflow release.yml --limit 3`; `gh run watch <id>` | success on the merge commit (first real run for v5.0.0 **[U]**) |
| Tag + Release | `gh release view v5.0.0 --json tagName,targetCommitish,isDraft,isPrerelease,body`; `git ls-remote --tags origin v5.0.0` | tag on the merge commit, not draft, Latest |
| Folded PRs | `gh pr view 231 --json state`; same for 235 | MERGED (**[U]**); if OPEN: comment "shipped in v5.0.0 via #216" and close (D4), then confirm #229/#234 CLOSED |
| Issues closed | `gh issue view N --json state,labels` for 194, 222, 229, 234, 241 | CLOSED. A merge-close leaves the stale `status:in review`/`in progress` label (BT-239 finding): fix with `set_status done` per `src/references/post-merge-sync.md` "Done detection" (`:11-14`), then `reconcile.py --ids ... --expect-file ...` as 0b does; needs OK |
| Board | Projects board or `gh project item-list`; `sync-labels-to-project.yml` (maps only completed closes) | cards in Done; if not, check Actions runs (needs `PROJECT_TOKEN`; #229/#234 cards were out of sync once, cause unknown) |
| Epic #194 | `gh issue view 194 --json state,stateReason` | CLOSED by the PR; FAA ran at #241's ship (not skipped) |
| Remote branch | `git ls-remote --heads origin improvement/BT-194-tracker-backend-no-map` | empty (auto-delete **[U]** effect) |
| Other PRs | `gh pr list --state open`; `gh pr view 232 --json mergeStateStatus` | #232 conflicts with `main` as expected (11 files, 13 hunks per the merge-plan review): its session merges `origin/main`, version -> 5.1.0 |
| Local sync | main checkout: `git switch main`, `git pull --ff-only` (needs it clean; it is on the BT-234 branch today) | main == merge commit |
| Harness pin | `git -C C:\t\l3src rev-parse HEAD` | `8c1a7ae` |

If the release did not appear: tag already exists or version collision. Do not retag or force; report first.

## 7. Cleanup (all deletions AFTER the merge; every deletion needs the owner's OK, D5; nothing here is run by this plan)

Keep: `C:\t\l3src` (pinned `8c1a7ae`), `C:\t\b217` (BT-217 worktree), `C:\t\l3main` (v4 baseline at `b7329af`) until the real v4 -> v5 consumer upgrade is done, `C:\t\pytest-of-patri`, today's active scratch, worktrees of other PRs (`remove-jules`, main checkout, `strange-napier-c68e89`).

1. **Backup first** to the D5 folder (plain local disk). `robocopy <src> <dst> /E /R:1 /W:1 /NFL /NDL`, then compare file counts. Copy: the whole `bt221\.tmp` (plans, `4a-aud-delta*`, `audit-*`, `0-4-*` bodies, `3d-suite-*.json`: `git worktree remove` deletes the git-ignored `.tmp` **[U]** whether it refuses without `--force`), `C:\Users\patri\Dev\Stratosphere-OS\.tmp\l3live\`, `C:\t\l3src\.tmp\l3live\`, and the loose files in `C:\t` listed by exact name: `g2rows.py`, `g3rows.py`, `g3rrows.py`, `g4rows.py`, `gh-store-g1.bak`, `gl`, `b1rows.py`, `b234rows.py`, `shim_committed.py`, `issues.new.py`. `.tmp/` is ignored by `.gitignore` line 1 **[V]**.
2. **List before delete.** Show exact names and sizes. The globs `g*`, `d*`, `fix*` also match those loose files: use directory-only listings (`Get-ChildItem C:\t -Directory`) and exclude the backed-up files.
3. **Batch 1 (regenerable sandboxes)**: `C:\t\l3-*` (about 47-50 dirs incl. `l3-31kn1r56-bak`), `l3b-*`, `pa6-1`, `pa6-driver`, `v5board`, `v5verify`, and `v5dnd`/`v5dnd2` ONLY after the #241 CLI re-check (step 6). Check `git worktree list` first: no listed worktree may be in the batch. Fast delete: `robocopy <emptydir> <target> /MIR /NFL /NDL /NJH /NJS` then `Remove-Item <target>`.
4. **Batch 2 (per-run scratch)**: directories `audmut_*`, `g*`, `fix*`, `gate*`, `d*`, `bt221*`, `b4-*`, `specaud`, `smoke3`; ask before `bt217-micro-run` (BT-217 evidence).
5. **Worktrees/branches (after merge)**: first `git switch main` in the main checkout (`git branch -d` refuses a checked-out branch), `git pull --ff-only`; then `git worktree remove .claude/worktrees/bt221` and `...\remove-jules`; local `git branch -d` (safe) for `improvement/BT-194-...`, `improvement/BT-222-glossary-hygiene`, `maintenance/BT-229-remove-jules`, `improvement/BT-234-scaffold-memory-eol-lf`. Never delete `deferred/BT-175-spec-lint`, #232's branch, BT-217's branch or `chore/prune-low-value-tests`. #231/#235 remote heads stay until those PRs are closed and the user deletes them.
6. **Throwaway repo** `PatN-git/stratos-smoke-20261030`: owner action, later (keep until no further real-GitHub test is needed, e.g. for 5.1.0).
7. **Verify**: `Get-ChildItem C:\t -Directory` shows only the keep list; `git worktree prune`, `git worktree list` clean; `C:\t\l3src` still `8c1a7ae`; the backup opens and counts match.

## 8. Template of the #240 closing comment

```
S5 handoff, result per item:
- Merge readiness: pending #241 ship; the final head, CI and ready state are recorded in the PR #216 body after it. Owner action: merge with "Create a merge commit"; title "BREAKING v5.0.0: ...". `main` frozen at 132dcb8.
- Release notes: done as text (.tmp/handoff/release-notes-v5.0.0.md); owner/agent action after release.yml: `gh release edit v5.0.0 --notes-file ...` (generated notes list titles only).
- Consumers: owner action, deferred until all PRs are released: RELEASING.md "v5.0.0" order; cleantech_jobs#267 after scaffold --update.
- Cleanup: backup + list ready; deletions after the merge with the owner's OK per batch; throwaway repo PatN-git/stratos-smoke-20261030 is an owner action.
- Plugin validators: agy ok (27 skills); claude plugin validate: not run (CLI absent), owner action.
- #241: option A, shipped via 4a after this comment (Epic Check + FAA on #194).
- Docs: RELEASING.md Jules removal and v5-completion-plan.md final state committed.
- Memory index: updated after the merge.
Unverified: Antigravity host run, concurrent worktrees on <repo>/issues, real v4->v5 consumer upgrade, #231/#235 auto-marked merged, FAA result.
```

## 9. Risks

1. Squash/rebase by mistake: breaks `merged --close` and the title lineage. Mitigation: the hand-off says "Create a merge commit"; all three methods are enabled **[V]**, so nothing prevents it.
2. Release notes miss the migration: generated notes show titles only. Mitigation: step 14.
3. #194 closes with an open child or without the Epic Check: mitigated by closing #240 first, shipping #241 through 4a, and the FAA (D2).
4. Stale status labels after the merge-close (BT-239): section 6 row; writes need OK.
5. Something merges to `main` first (version collision, tag no-op): freeze `main`; repeat the gate right before the merge.
6. The FAA finds gaps: `gh pr ready --undo`, fix, re-run (D2 pre-authorizes the undo).
7. GitHub parses a closing keyword plus an issue number even inside backticks in a PR body: write issue refs without a closing keyword (see appendix E).
8. Cleanup deletes evidence or a live worktree: backup first, directory-only listings, `git worktree list`, `git worktree remove` instead of `rm`, keep list explicit.
9. Unverified claims ship as v5.0.0: they are named in "Known gaps" and the PR `post_merge:`.
10. Quota: the FAA is the largest unknown (5-12% **[U]**). Permission blocks (`release.py -y` was blocked twice earlier): this plan does not re-run `release.py` (the bump is in the branch; bump-guard is green in CI **[V]**).
11. Windows: run tests with `TMP=TEMP=C:\t` (MAX_PATH); concurrent sessions share the index: commit with explicit paths.

## 10. Definition of done

- #240 CLOSED with the per-item comment, closed before #241's ship; #241 shipped as option A; `closingIssuesReferences` of #216 has 194 and 241 and not 240.
- PR #216 body refreshed by 4a (head, `test:`, Notes); `check.sh` green and CI green at the final head; `agy plugin validate dist` ok.
- `RELEASING.md` carries the Jules removal; `v5-completion-plan.md` is current.
- Release-notes text and consumer checklist delivered; cleanup done with OK or listed with commands; the evidence backup exists before any deletion.
- After the owner's merge: section 6 checks run and reported; the `v5.0.0` Release has the migration text; #194, #222, #229, #234, #241 CLOSED with `status:done` and correct board positions; #231/#235 merged or closed with a note; memory index updated.
- Everything unverified is named (Antigravity host, `claude plugin validate`, board-sync timing, #231/#235 auto-merge, FAA cost/result, Windows delete behavior of ignored files).

## Appendix: Follow-ups without an issue (excluding CleanTechHub)

None of these blocks v5.0.0. "New issue" = open one after the merge (D6).

- (A) Wording/doc backlog (new issue): 0d wording gaps (commit rule, empty-findings path, PATTERN to LAW cross-file); 4a `--close` local Closes lines; 3z Step 2B template `std_tier`; weak pins (Bar header, ci-gate section 1); PARTIAL undefined in the 4a status vocabulary; `.tmp/4a-pr-body-*` cleanup when no PR; "PR host / local-only / gh not connected" wording.
- (B) Code health noticed (new issue): `reconcile.py` about 582 lines over A-003's 400 with no exception row; `scaffold.py` about 1659 lines; `tracker_switch.py` mixes gh sync and local rewrite; `validate_memory` autofix writes `[[ID]]` into the ICE column instead of Ref; keep `-m integration` in the 4a checklist (no issue; a checklist line).
- (C) Verification gaps (new issue): Antigravity host run; `claude plugin validate` (CLI absent); a red `--attempt 2` after a real second push; conflict/`base_stale` ci_gate verdicts; 3z `[CI-FIX]` dispatch; Phase 2 audit subagents and the feature acceptance audit on real GitHub; F35 retry on a real gap at the final code; first real `release.yml` run for v5.0.0; `ci_gate --wait` does not shorten the 60 s checks-not-registered grace (document) and `log_tail` carries a BOM/ANSI (cosmetic).
- (D) Test infrastructure (new issue): fake `gh` gaps: `pr merge`, `stateReason`/`closedAt`/`mergeCommit` fields, complex `--jq`, graphql reads, `gh pr checks`, `run view`, `project list`, duplicate label/milestone create errors, response-shape drifts.
- (E) Process/docs (new issue): GitHub parses a closing keyword plus issue number even inside backticks in a PR body: add a rule to `pr-body-and-ship.md`; merge-closed issues keep a stale status label unless post-merge sync sets `done` (verify 0b/`post-merge-sync` does; the board sync Action maps only closes, and #229/#234 cards were out of sync for an unknown cause).
- (F) Other PRs/epics (no new issue where one exists): #232 ships as 5.1.0 after fixes (title says BT-223 but content is BT-230; track naming contradicts the install-harness README; bridge docs removed while the script ships; unverified Antigravity marketplace claim; 4.7 MB PNGs; real Antigravity test); BT-217 rebases onto v5 `main` (cheapest after #231 is on `main`; no issue needed); untracked docs in the main checkout (`docs/plans/pr216-live-test-plan.md`, `0f-walk-me-through-*.md`, `docs/proposals/obsidian-vault-and-agent-linking-proposal.md`) are not committed anywhere: decide where they land (no issue needed, a one-line owner call); back up `.tmp\l3live` before cleanup (step 15).
