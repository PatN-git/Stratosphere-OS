---
type: plan
title: Tracker Parity Gaps and Real-GitHub Smoke Plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-29
version: "0.1.0"
---

# Plan: close the local/GitHub tracker gaps, and prove v5 on real GitHub

**Status:** draft v0.1, not yet reviewed. An independent review (Sonnet 5.5 high) runs after the weekly-limit reset.

**Inputs:**
- research `.tmp/v5fix/parity-research.md` in the bt221 worktree, with cited sources: Backlog.md, Beads, Task Master, git-bug, spec-kit, and the public roadmap skills;
- the PR #216 live-test record `.tmp/l3live/` (main checkout);
- `docs/plans/local-tracker-parity-plan.md`.

## Two parts, two ship units
| Part | What | When | Ships in |
|:--|:--|:--|:--|
| **B: proof** (item 2) | Real-GitHub smoke test, plus the live local runs never done, plus the F35 rule on more slices. Fix what they find. | **Before** merging PR #216 | PR #216 (v5.0.0) |
| **A: parity** (item 1) | Close the 5 accepted gaps | **After** the merge, as a new epic | v5.1.0 (MINOR: new verbs, nothing removed) |

B goes first: it tests what v5.0.0 ships. A is new behaviour and needs its own epic, minted with `/3b`.

## Part A: close the five accepted gaps
**Inspiration found:**
- No public roadmap skill has a local-tracker mode. The closest is `dirien/yet-another-agent-harness` `roadmap`, whose ROADMAP-vs-tracker drift idea feeds A4.
- The board idea follows Backlog.md (`backlog board`, `board export`).
- Merge detection builds on our own `issues.make_merged_of`.
- Two-way sync was rejected: git-bug and Beads both need a mapping store and a conflict policy.

| # | Gap today | Fix (recommended) | Size | Files |
|:--|:--|:--|:--|:--|
| A1 | **Local with no PR host:** 0b can't see a merge; the user closes epics by hand | `issues.py merged [--close]`, see A1 notes | M | `issues.py`, 4a step 6 (local), `post-merge-sync.md`, 0b step 1 |
| A2 | **Close semantics differ** (GitHub `Closes #n`; local 0b closes `features:`) | One rule, both backends: *"the merge closes; a workflow never closes an unmerged epic."* GitHub keeps `Closes #n`; local runs `issues.py merged --close`. tracker-verbs' Misfits `close` row becomes a normal verb row. No commit trailers: they would need an AGENTS §4 carve-out for 4a commits. | S | `tracker-verbs.md`, `post-merge-sync.md` |
| A3 | **No board locally** | `issues.py board`, see A3 notes | S | `issues.py`, tracker-verbs Reads |
| A4 | **Local gate is whole-store `issues.py check`, not the per-id expected-state gate** | Lift the local guard in `reconcile.py` (line 503) and accept `--expect` / `--expect-file` on the local store (`store.rows()`), widening the `parse_expect` id regex to `BT-LOCAL-<slug>`. Every workflow's gate line then reads the same on both backends; drop the "local: `issues.py check`" branches (3a, 3c, 0b, post-merge-sync, 4a step 9). Optional: a ROADMAP-vs-tracker drift line in 3a (from the roadmap skill). | M | `reconcile.py`, `_tracker_common.py`, the workflows above, tests |
| A5 | **`tracker_switch` is one-way** (local → GitHub) | **Decision D1:** (a) keep it one-way and say why in tracker-verbs (recommended: no user need seen, and a reverse switch drops the PR links); or (b) a one-shot `tracker_switch.py --to local` import, sketched in A5 notes. | (a) S / (b) M | `tracker-verbs.md` (+ `tracker_switch.py`, tests for b) |

**A1 notes:**
- The check is the existing git-ancestry test (`make_merged_of`), made robust:
  - 4a ship records the unit branch tip in the local PR-link comment: `Shipped on <branch> @ <sha>`, even with no PR host.
  - `merged` tests `git merge-base --is-ancestor <sha> origin/HEAD` (or the local default branch). That survives branch deletion.
- Squash merges can't be proven: advisory line only (commit-subject match), never an auto-close.
- 0b runs `merged --close` on both local variants, with or without a PR host. The PR body's `features:` path (F27) stays the PR-host source.
- No post-merge hook: it only fires on the merging client.

**A3 notes:**
- Read-only text kanban: one column per status, cards `id title [labels]`, about 40 lines.
- `--md <file>` writes the same as Markdown, like Backlog.md's `board export`.
- Deterministic, no model call. `plan-html` stays the human-facing renderer when someone wants HTML; it can read `--md`.

**A5 notes, option (b):**
- Dry run first.
- Read-only on GitHub.
- Marker-idempotent.
- Writes `tracker: local` last.
- PR links become plain text.

**Tests:** RED first for A1, A3 and A4. A1 needs merge, squash and deleted-branch cases. A4 is a contract test: the same `--expect` string passes on both backends.

**Live check after the build:** one local run, 4a ship with no PR host → human `git merge` → 0b closes the epic and frees its dependents. Haiku high in a sandbox, file relay.

## Part B: prove v5.0.0 (PR #216) where it is unproven
| # | Stage | What | How | Models |
|:--|:--|:--|:--|:--|
| B0 | Approval | The user approves creating one **private throwaway repo**, `PatN-git/stratos-smoke-<date>`, and its later deletion (by the user: `gh repo delete` needs the `delete_repo` scope) | lead asks | — |
| B1 | Real-GitHub smoke, scripted | See B1 steps | One script, `.tmp/smoke/smoke.py`, every call logged | Sonnet high writes the script; the lead runs it |
| B2 | Fake-gh calibration | Diff every real response B1 captured (error texts, JSON shapes, exit codes) against the fake `gh`. Fix each mismatch in the shim with a test. Known suspects: the label error wording (F32), `{owner}/{repo}` expansion, `closingIssuesReferences`, `statusCheckRollup` with no workflows. | Script diff plus shim fixes | Sonnet high |
| B3 | Live local runs, never driven | On fresh **local** sandboxes, see B3 stages | L3 rig, Haiku 5.5 high as the agent under test, file relay, `stage_checks` asserts per stage | Haiku high (under test); Sonnet high (rig changes) |
| B4 | F35 on more slices | See B4 steps | Harvest from B3's 3z log | Haiku high (auditors under test) |
| B5 | Fix round | Each finding: Sonnet high implements (RED → GREEN); Haiku high rubric-grades the diff; the lead runs build, validate, recorded tests and `check.sh`, then commits | as in the v5 fix plan | Sonnet / Haiku |
| B6 | Ship | `/4a-verify-and-ship` (audit-only, then ship-only) | as on 2026-10-28 | Sonnet high |

**B1 steps,** against the real repo with the user's own `gh`:
1. `tracker_switch` local → GitHub from a seeded local store: labels and milestones created, issues created, parent/blocker edges, a re-run creates nothing.
2. 3b-style minting through the verbs, then the `reconcile --expect` gate and `--with-edges`.
3. `ice_read candidates`.
4. A unit branch: push, `pr_body build`, `gh pr create`, `ci_gate` with no CI workflows, ready flip.
5. **The user merges** the PR on GitHub (workflows never merge).
6. 0b's merge query: `closingIssuesReferences` and `mergedAt`.
7. Post-merge sync, scripted.

**B3 stages:**
- L1 3a → L2 3c → L3 3z → 3d → 4a audit + ship, on 2 or 3 slices so F35 gets multi-slice data.
- L4 2a and 2b (epic minted locally).
- L5 0d nightly consolidation.
- Merge plus 0b was already proven live (R3).

**B4 steps:**
- Record every multi-round audit from B3's 3z: rounds-to-`[PASS]`, and whether any blocker was raised on unchanged lines.
- **Negative control:** seed one slice whose round-2 fix introduces a real new gap on changed lines, and require it to still block.
- Pass: no block caused only by drift on unchanged lines, and the control blocks.

## Order, gates and budget
**Order:** B0 → B1 → B2 → B3 → B4 → B5 → B6 → (the user merges PR #216) → `/3b` mints the A epic (A1–A4, plus A5 per D1) → build → live check → `/4a`.

**Approval points (outward actions):**
1. Creating the throwaway repo (B0).
2. The throwaway PR merge (B1 step 5, the user).
3. Pushes to PR #216 (B6).
4. Deleting the throwaway repo (the user).
5. Merging PR #216 (the user).
6. Minting the A epic and its issues (`/3b`, HITL).

**Limits now:** the weekly limit is at **94%** (resets Nov 3, 11:00 UTC); the 5-hour window is at 77%. **Nothing starts before the weekly reset,** or it runs on extra usage (money).

**Estimates (weekly points, from this PR's runs):**

| Stage | Estimate |
|:--|:--|
| B1 + B2 | 3 |
| B3 (about 40 Haiku runs) | 10 |
| B4 | 1 |
| B5 | 3–6 |
| B6 | 2 |
| A build + live check | 8 |
| **Total** | **≈ 27–30**, a third of a week |

**Stop rules:** before each stage, the lead reads usage. Stop at 95% of the 5-hour window, and before any stage that would take the weekly limit past 90%. Stop reports carry usage.

## Decisions needed
- **D1:** the A5 reverse switch: (a) keep it one-way and document why (recommended), or (b) build the one-shot import.
- **D2:** do B before merging PR #216 (recommended: it tests what v5.0.0 ships), or merge first and run B on `main`.
- **D3:** the throwaway repo's owner and visibility: private under PatN-git (recommended).
