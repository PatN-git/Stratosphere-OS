---
type: plan
title: STATUS.md for concurrent sessions (BT-218)
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-22
version: "1.0.0"
---

# STATUS.md for concurrent sessions: plan

Status: implemented 2026-10-27 (decisions: stale rule = issue not in progress or line older than 14 days; local resume note = `.memory/resume/<id>.md`); minted 2026-10-22 as BT-218 (slice S7 of epic BT-194, blocked by BT-198/BT-199, blocks BT-200), shipped in PR #216 (release v5.0.0).

## Problem

`.memory/STATUS.md` has one `Current Branch`, one `Active Issue`, one `Current Focus` and one `Next Immediate Step` per folder. In practice, several sessions run in one folder, often on one branch (see memory "shared index, concurrent sessions"), and one release branch holds slices of several epics. Commit d88ba01 (2026-07-20) made the tracker's `status:in progress` set the authority and demoted STATUS to a "single-session hint". The skills that write and read STATUS were only partly changed to match.

## Evidence

### StratOS (STATUS is gitignored, so the evidence comes from transcripts)

- 59 Write/Edit calls to `.memory/STATUS.md` from 21 sessions since 2026-09-29. Real overlaps where both sessions wrote: 45f6891f × 0c0ed7da (10-08, the second did a full-file `Write`) and 123177f0 × a8d1c6be (10-16). Today's file has a hand-written line, "BT-207 is being worked in another session: do not touch", which is coordination the format has no place for.
- The current file is 51 lines and about 11k characters, with 8 dated history paragraphs. That history is already in the issues, PRs and commits, and every session loads it.
- `0a` Phase B step 2 restores the branch named in `STATUS Current Branch`, not the branch of the task picked in Phase A.
- `3d` step 1 and `3z` Step 2A.1 still write `Active issue` per slice. d88ba01 says 3z no longer does, but line 53 still has it.
- `load-memory` reads neither STATUS nor issue comments. The progress comment 0b step 1 posts on the issue is never read back, so in practice the only way to resume a task is through the single-slot STATUS.
- The template says to use worktrees for concurrency. In StratOS the whole `.memory/` is gitignored, so a worktree has no `.memory/` and `0a` halts with "Repository uninitialized".

### CleanTechHub (STATUS is tracked in git: 190 versions, 2026-06-29..10-22)

- `.gitignore` has no `.memory/STATUS.md` entry. Setup only proposes adding it. Of the 190 commits that touch STATUS, 110 change only memory files, about one bookkeeping commit per slice. Each branch carries its own STATUS, and a `main` → `feat/BT-215` merge touched it.
- One folder, two branches, same day: on 2026-10-01 commits e1fd47a, ae158f2 and 57089f3 alternate between `feat/BT-215-…` and `maint/BT-197-…`, so sessions on different branches in one folder really happen.
- Release PR #244 holds 3 epics on one branch. On 2026-10-20 the single `Epic` header flipped 6 times. The single branch was right; the single per-task slot was wrong.
- STATUS copies the tracker: a "Shipped Slices" list with 13+ rows of titles and labels. Its peak size was 13.4k characters.

## 1b coverage (no full 1b run needed)

1b's own exit rule (Phase 4.3) sends work that isn't PRD-worthy to `/3b-create-issue` as a Build slice. This is brownfield framework work inside an existing epic, and the facts come from the repo. The 1b checks that still add value are done here:

| 1b item | Covered by |
|---|---|
| Actor | The owner running several Claude Code / Antigravity sessions in one folder, plus the 3z orchestrator. Its subagents never touch STATUS. |
| Problem | §Problem; the slot is per folder, the work is per task |
| Prior art | d88ba01; BT-169 cadence (0a/0b only at slice boundaries); BT-194 tracker verbs |
| Facts | §Evidence, each with a source |
| Success | §Goal, 4 checkable items |
| Non-goals | §Out of scope |
| Vocabulary (V3 clash) | "handoff" is taken twice: `/0c-handoff` (a `.tmp/handoff_*.md` file) and 0b's "Handoff Note Format" (chat output). The per-task issue comment is therefore called a **resume note**, and the folder record is called a **session line**. Neither term clashes with GLOSSARY.md. |
| Rejected framings | (a) Per-branch STATUS files: rejected, because sessions share one branch. (b) Delete STATUS entirely: rejected, because `Last Sync` is 0b's merge-sync cursor and folder caveats have no other home. (c) Use the `claim` verb (assignee) as the session lock: rejected, because one owner is the assignee of every issue, so it can't tell sessions apart. |
| RAT | Riskiest assumption: agents (Antigravity especially) edit only their own session line instead of rewriting the whole file. If one rewrites it anyway, it loses at most other sessions' lines. Nothing authoritative lives there: the next 0b re-prunes from the tracker, and 0a merely misses one "branch in use" warning. Accepted without a test; revisit only if a lost line causes a real branch yank. |

## Goal (verifiable)

1. Two sessions in one folder, working different slices, never overwrite each other's resume info: each writes only its own session line, and per-task detail lives on the issue.
2. `0a` resuming BT-x checks out BT-x's ship-unit branch, or halts with a clear reason when that would yank another session's branch or uncommitted work.
3. `load-memory` reads the latest resume note of the active task, in both tracker modes.
4. STATUS ≤ 3,000 characters with no history; `validate_memory.py` warns past the budget and when STATUS is tracked by git.

## Design

### Rule: STATUS holds folder state, never issue state

This rule follows BT-194's runtime rule ("GitHub mode: GitHub is the only store … no mirror file"). What a folder is doing (which session has which branch checked out here) is not issue state, and neither tracker can store it, so it stays local in both modes. Anything about the issue itself goes through a tracker verb.

| Data | GitHub mode | Local mode |
|---|---|---|
| Which tasks are in flight | `status:in progress` label (`get`/`list`) | the map's Status cell |
| Per-task progress and next step (resume note) | `comment` verb → issue comment | `comment` verb → dated line in the issue's draft file |
| Which session in this folder holds which task and branch | STATUS session line | STATUS session line (same) |
| 0b merge-sync cursor | STATUS `Last Sync` | STATUS `Last Sync` (0b's merge sync needs `gh`, so it is skipped) |

### 1. STATUS shape

```
- **Last Sync:** 2026-10-22
- **Sessions:**
  - BT-197 · improvement/BT-194-tracker-backend-no-map · 2026-10-22
  - BT-207 · improvement/BT-212-… · 2026-10-22
- **Repo notes:**            # folder-local caveats only (stale .agents/ scripts, shell quirks)
- **Blocker (if any):**
```

- A session line is exactly `BT-n · branch · date`: no title, status or next step, because those are issue state.
- `Current Branch` is dropped: `git branch --show-current` is the truth.
- Also dropped: `Active Issue / PRD`, `Current Focus`, `Completed This Session`, `Open/Active Task Brief`, `Next Immediate Step`.
- Write rule: upsert or remove only your own line (matched by `BT-n`), or edit a single field. Never rewrite the whole file and never add history.

### 2. Resume note (per task, through the tracker)

- 0b step 1 already comments on the issue. That comment becomes a fixed block marked `<!-- stratos:resume -->` with `Branch / Done / Open / Next step / Blockers`, written with the `comment` verb.
- `load-memory` step 2 also reads the latest resume note, with a scoped read so it doesn't load the whole thread:
  - GitHub: `gh api repos/{owner}/{repo}/issues/<n>/comments --jq '[.[] | select(.body | contains("stratos:resume"))] | last | .body'`.
  - Local: the last `stratos:resume` entry in the issue's draft file.
  - Add this read to `tracker-verbs.md` §Reads as `resume_note`.

### 3. 0a follows the chosen task

Phase B step 2 becomes:
1. Resolve the task's unit branch with 3d step 1's lookup (`pr_body.py unit` + glob over active branches). Reference it; don't copy it.
2. Already on that branch → nothing to do. Not found → stay put (3d creates it).
3. Different branch:
   - If `git status --porcelain` shows changes outside `.memory/` and `.tmp/` → HALT `[DIRTY-TREE] this folder is on <b> with uncommitted changes; resume BT-x in a separate folder`.
   - If a session line dated today holds the current branch → ask before checking out.
   - Otherwise check out.

Phase B step 3 then upserts this session's line.

### 4. Writers

| Who | Today | After |
|---|---|---|
| 0a Phase B.3 | "update STATUS as resume hint" | upsert own session line |
| 3d step 1 | write `Current Branch` / `Active issue` | upsert own session line |
| 3z Step 2A.1 (orchestrator) | write `Active issue` / `Current Branch` | upsert the slice's session line (subagents still never touch STATUS) |
| 0b step 1 | free-form issue comment | resume note block (`comment` verb) |
| 0b step 2 | rewrite all fields | `Last Sync`; remove own line if the slice left `in progress`; prune lines whose issue is no longer `in progress` (tracker `get`) or older than `stale_after` |
| 0b step 11 | "STATUS allows resuming" | "the resume note allows resuming" |

### 5. Lint (deterministic)

`validate_memory.py`:
- warn when STATUS > 3,000 characters;
- warn when `.memory/STATUS.md` is tracked by git (`git ls-files --error-unmatch`), with the one-line fix.

### 6. Template + docs

- `src/memory-templates/STATUS.md`: the new shape. Replace the worktree advice with: "sessions in one folder share its checked-out branch; work on another branch in a separate folder that has its own `.memory/`".
- `environment-fix-ladder.md` rung 5 and the `LEARNINGS.md` template line "Current task status → STATUS.md" point to the resume note.
- The setup gitignore wording stays (the lint now backs it up).

## Fit in BT-194

- **New slice S7**, a sub-issue of BT-194, HITL, size M. `pr_body.py unit` then resolves it to the same branch, `improvement/BT-194-tracker-backend-no-map`, and the same PR, #216.
- **Blocked by S4 (BT-198) and S5 (BT-199).** They edit the same files (load-memory, 0a, 0b, 3d, 3z, harness `assertions.py`), and S7 builds on their scoped reads.
- **S6 (BT-200) is also blocked by S7.** S6 is the contract and already lists `src/memory-templates/STATUS.md`. Running S7 first keeps the template edit in one place: S6 drops STATUS from its file list, or confirms only.
- **S3 (BT-197) is complementary.** It moves the "no gh → local tracking" note out of STATUS into the `tracker:` key, so STATUS loses another non-folder fact.
- **Release:** already MAJOR (v5.0.0) because of S6. S7 adds one release-note line: STATUS format changed; old files lint-warn until trimmed.
- **Order:** S1 → (S2 ∥ S3) → (S4 ∥ S5) → **S7** → S6.

## Files

`src/workflows/0a-start-session.md`, `0b-stop-session.md`, `3d-implement-issue.md`, `3z-afk-loop.md`, `src/skills/load-memory/SKILL.md`, `src/references/tracker-verbs.md` (§Reads `resume_note`), `src/memory-templates/STATUS.md`, `src/memory-templates/LEARNINGS.md`, `src/references/environment-fix-ladder.md`, `src/scripts/validate_memory.py`, tests below. OKF versions bump once per PR.

## Tests

- `validate_memory.py`: budget warning; tracked-file warning (temp git repo).
- `tests/lifecycle-harness/assertions.py`: today it checks that "0a updated STATUS" and "0b wrote STATUS fields". Change both to check for a session line for the slice and no `Active Issue` or `Current Branch` field.
- Prose pins (`tests/workflows` style):
  - 0a names `[DIRTY-TREE]` and resolves the branch from the task, not STATUS;
  - 3d and 3z write no `Active issue`;
  - load-memory reads `stratos:resume`;
  - no workflow writes a title or status into STATUS.

## Out of scope

- StratOS's own worktrees lacking `.memory/` (dogfood-only, because `.memory/` is fully ignored here). Note it in dev docs (e.g. `mklink /J`); no product change.
- Migration code. StratOS's own STATUS is trimmed by hand once. For consumers, the lint warning prompts it, and 0b proposes the trimmed file the first time it meets the old format (first-entry rule, applied on confirmation).
- Untracking CleanTechHub's STATUS: a consumer step to do in that repo after it updates. Commit the staged `git rm --cached` with a plain `git commit`, never with a pathspec.

## Decisions

- Branch: fold into PR #216 as S7 under BT-194 (owner, 2026-10-22).
- Budget: 3,000 characters (owner, 2026-10-22).
- Session line: `BT-n · branch · date`, folder state only, the same in both tracker modes. Per-task detail goes through the `comment` verb (proposed above; confirm when minting).
