---
type: discovery-brief
title: "Discovery: BACKLOG_MAP duplicates GitHub-owned fields and every write site pays for it"
description: "Frames the BT-189 spike: compare the hand-written map, a generated map and no map in GitHub mode, with tracker verbs so each write is stated once."
generated:
  by: 1b-concept-framing
  at: 2026-10-20
status: exit-spike
slug: backlog-map-generated-cache
linked-prd: —
concept-map: —
version: "4.9.0"
---

# Discovery: BACKLOG_MAP duplicates GitHub-owned fields and every write site pays for it

## Ask (verbatim)
> /1b-concept-framing bt-189

## Vocabulary
- **Mirror write:** the second write of a GitHub-owned field (status, labels, milestone, parent, blocked-by) into `.memory/BACKLOG_MAP.md`. Avoid: dual write, sync write ([[G-004]]).
- **Sync layer:** everything that exists to keep mirror writes honest: the `reconcile.py` gate, `terminal-sync-invariant.md`, the heal kinds, the 0d drift check, `--heal`.
- **Generated map:** a map rebuilt by a script from GitHub and never edited by agents. Avoid: cache, snapshot, mirror.
- **Tracker backend:** where issues live (GitHub or local markdown), chosen once at setup ([[G-002]]). Avoid: offline mode, BT-LOCAL mode (`BT-LOCAL` stays only as an ID prefix).
- **Tracker verb:** a backend-neutral read or write named in workflow prose, e.g. *set status*, *add blocker* ([[G-003]]).
- **Local-only columns:** `ICE` and `Ref`, the map columns with no GitHub field.
- **GitHub post-condition:** a check that a multi-write terminal phase landed on GitHub itself (closed ≡ done, PR-link comment, blocker CLEAR/KEEP, epic flip), independent of any map.

## Actor
A lifecycle-workflow agent (3a/3b/3c/3d/3z/4a/0b/0d) running in a `gh`-connected project, which makes a mirror write after every GitHub write. The framework maintainer pays in always-loaded tokens and upkeep, and consumer projects (e.g. CleanTechHub) inherit both.

## Problem
In a project whose tracker backend is GitHub, the map is a second copy of fields GitHub already owns. The sync layer and every mirror write are the standing price of keeping that copy honest, paid in workflow text, whole-map reads and script upkeep. Drift incidents are rare: the cost is prevention, not repair.

**Scope facets:**
- **Duplication (root):** GitHub-owned fields are held twice, so every write is made twice and checked.
- **Backend coupling:** workflows name both backends at each write site because there are no tracker verbs, so even a single-backend project carries text for two.

## Established Facts (as of 2026-10-20)
- BT-189 is an open Spike, `status:needs_spec`, with no parent and no milestone. Source: `gh issue view 189`.
- `.memory/` is gitignored, so the map is local to each working directory: 19,760 bytes, 59 rows, against about 111 GitHub issues. Source: `.gitignore:2`, `git ls-files .memory`, `gh issue list --state all`.
- `BACKLOG` appears 130 times across 36 `src/` files, and `src/scripts/reconcile.py` is 579 lines. Source: grep, wc.
- The sync layer originated when a 3z run dropped 4a's mirror write after the `gh pr` call (completion bias). Source: `docs/plans/terminal-sync-invariant-plan.md` §1.
- load-memory step 6 and 3c step 1 read the whole map. 3c reads ICE from it and writes priority, milestone and `Blocked by` back. Source: `src/skills/load-memory/SKILL.md:21`, `src/workflows/3c-sprint-planning.md:21,34,72-74`.
- `Ref` is set on 0 of 59 rows. 3b already writes raw ICE metrics into the Build-slice issue body. Source: awk over the map; `src/workflows/3b-create-issue.md:101`.
- Part of the gate checks GitHub post-conditions rather than map drift: `edge_verdict` and `pr_merge_state`, closed ≡ done, and the PR-link comment. Source: `src/scripts/reconcile.py:151,305`; `src/references/terminal-sync-invariant.md:2,21-22,33`.
- The BT-190 epic bumps `memory-templates/BACKLOG_MAP.md` from 1.3.3 to 1.4.0 (BT-188/191 touch the same writes). Source: `docs/plans/lifecycle-status-pr-scope-epic.md:107`.

## Chosen Framing
**F1 + F3.** The map is a duplicated source of truth for GitHub-owned fields (F1), and workflows hard-code two backends at every write site because there are no tracker verbs (F3). The spike compares three options:
- **A:** the hand-written map plus the sync layer (baseline).
- **B:** a generated map.
- **C:** no map in GitHub mode; agents run scoped live `gh --json` queries.

The comparison covers read cost, deletion size and text saving.

**Rejected framings:**
- F2, read-cost gap (agents need a cheap whole-backlog read): kept only as the lens that decides B against C, not as the problem.

## Success State
1. A decision record in `docs/plans/` gives adopt, reject or partial against criteria (i)–(iii) below, with measured numbers for A, B and C.
2. (i) The full rebuild (B) or the scoped queries (C) cost no more wall time and `gh` calls than today's per-id `reconcile.py` reads on a typical 3z run.
3. (ii) Every map-diff check, mirror write and mirror heal is deleted. Any surviving GitHub post-condition gate is listed with its size and kept only if it meets the gate's own bar.
4. (iii) Always-loaded plus per-workflow text shows a net reduction, reported in characters per workflow (no numeric floor).
5. Every StratOS write (status, labels, milestone, parent, blocker, ICE) is shown to fit one tracker verb with a GitHub and a local-markdown implementation, or the misfit is named.
6. Partial adoption is allowed when one piece clears the bar on its own.

## Prior Art
- BT-189 issue body: the write inventory, the generator prototype and the ICE/Ref placement steps.
- BT-188, BT-191, BT-192 (epic BT-190): touch the same status and blocker writes; BT-192 adds the PR-merge edge verdicts.
- `docs/plans/terminal-sync-invariant-plan.md`: the origin and design of the sync layer.
- External pack M (pinned 5beb35b): the tracker backend (GitHub, GitLab, local markdown or prose) is chosen once at setup and recorded in one per-repo adapter doc that maps verbs to commands. Skills are written once against the verbs, and lists are live `gh --json` queries. There is no mirror, cache or reconcile step.
- External pack O (pinned aeac41d): one "task list target"; a designated tracker gets items *instead of* `tasks/todo.md`, and the plan keeps an index of tracker IDs rather than a duplicate checklist.

## Non-Goals (early signal)
- No implementation in the spike.
- No change to the label taxonomy or GitHub Project fields beyond where ICE and Ref land.
- STATUS.md and the other `.memory/` files are untouched.
- Porting CleanTechHub's label→Project sync Action stays separate.

## Decoupled Follow-ups
- Port CleanTechHub's label→Project sync Action: relevant only if ICE moves to a Project field. Candidate.
- `reconcile --all-open` breaks past 100 open rows: moot under B or C, still needed under A. Candidate.

## Constraints & Settled Decisions
- **Output of this run:** the brief sharpens BT-189 and its adopt/reject criteria; next is the spike, not a PRD. Why: the issue already exists as a spike.
- **Offline:** an alternative tracker backend chosen at setup, with each write stated once as a tracker verb. Why: pack M avoids two write versions this way; degrading or dropping offline was rejected.
- **Option set includes C.** Why: both external packs run without a map; the map's only claimed gain is read cost, which C tests directly.
- **ICE/Ref may be dropped, not only relocated.** Why: Ref is unused, and ICE already lives in the issue body.
- **Host-agnostic** (Claude Code + Antigravity). Why: StratOS targets both.
- **No added ship-path minutes.** Why: standing rule that gates are measured against CI time first.
- **A one-off map migration is a throwaway script,** not workflow prose. Why: no token-bloat migrations.
- **`.memory/` stays gitignored.** Why: local per working directory by design.
- **Sequencing:** the spike runs after BT-188/191; BT-189 and its follow-up slices become sub-issues of BT-190 and land on its branch and PR. Why: they touch the same writes; AGENTS §4 puts a parent epic's slices on one branch.

## Open Questions
1. Where do ICE and Ref land (a Project field, the issue body, or dropped)? Owner: spike. Blocking: N.
2. Under C, how does 3c rank the whole backlog without a single read (ICE parse cost across ~111 issue bodies)? Owner: spike. Blocking: N.
3. Do any historical `[MIRROR-DRIFT]` or `[HEALED]` logs exist to classify, or only code and prose? Owner: spike, step 1. Blocking: N.

## Riskiest Assumption
- **Riskiest Assumption:** that the sync layer exists because of the map, so removing the map (B or C) removes it.
- **Why Fatal:** if the gate's real job is GitHub post-conditions after multi-write phases, a gate, its prose and most of `reconcile.py` survive. Meanwhile adapter, offline-backend and scoped-query text is added, and criterion (iii) comes out flat or negative.
- **Cheapest Test:** offline sample benchmark. Classify every check in `reconcile.py`, every gate and heal sentence with its call sites in 3a/3b/3c/4a/0d, and every logged drift or heal entry as map-only or GitHub post-condition. Pass if map-only is at least 80% of lines, prose and incidents; otherwise re-scope to "B or C plus a slimmer post-condition gate" before any prototype.
- **Est. setup time:** 0.5 day.
- **Status:** untested (spike step 1).

## Recommended Next Step
- [ ] `write-prd`: problem is sharp, PRD-worthy
- [ ] `create-issue` Build slice: this is a bug
- [x] `create-issue` Spike: research needed first. BT-189 already exists, so link this brief from its body, parent it under BT-190, and run it after BT-188/191, starting with the RAT classification. BT-190 is `in review`: move it back to `in progress` when the follow-up siblings are minted.
- [ ] Dropped: do not build
