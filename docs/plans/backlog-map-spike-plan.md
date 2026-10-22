---
type: plan
title: BT-189 Spike Execution Plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-20
version: "1.0.0"
---

# Execution plan: spike BT-189 (BACKLOG_MAP as a generated read-only cache)

Status: **done 2026-10-20.** H0–H3 passed; decision in `backlog-map-decision.md` (partial adopt of C).
- **Inputs:** the brief `docs/discovery/backlog-map-generated-cache.md` (its Success State, Constraints and Riskiest Assumption win over this plan) and the BT-189 issue body.
- **Scope:** run the spike up to the point where its decision record is approved and closed. Building B or C is a separate plan, written after `/3b` mints the slices; it cannot be planned before the decision.
- **Branch:** `feat/BT-190-lifecycle-status-pr-scope`. Commits stay local; there is no push in this plan.

## Roles
- **Router and grader:** the main session (Opus 5.5). It launches the subagents, grades each report against source, writes the decision record, and is the only writer to git, GitHub and `.memory/` (AGENTS §8).
- **Analysts:** Sonnet 5.5 subagents at high effort. They are read-only, may write scratch files only under `.tmp/bt189/`, may run read-only `gh` queries, and never commit. Each returns a report of at most 300 words; the detail goes in its scratch file.
- **You:**
  - decide at each halt;
  - make the adopt/reject/partial call at H3;
  - run `/3b-create-issue` after the spike closes.

## Quota protocol (5-hour window; do not spill into extra usage)
- At every halt the router calls `get_usage` and shows `percentUsed`, `resetsIn` and the change since the last halt.
- **Before a phase starts:**
  - at or above 85%, recommend waiting;
  - at or above 90%, the only options are *Wait for reset* or *Stop*;
  - if extra usage `spent` is above 0, stop immediately and say so.
- **Per-phase estimates:**
  - Phase 1 ≈ 2 × 80k Sonnet tokens;
  - Phase 2 ≈ 100k Sonnet tokens;
  - Phase 3 ≈ 40k Opus tokens;
  - Phase 4 ≈ 15k.

  These are tokens, not quota percent. H1 turns them into percent from the observed change.
- **Calibration at H1:** Phase 1 actually used about 360k Sonnet tokens (A1 186k, A2 174k) and moved usage 78% → 88%, so about 2.8% per 100k Sonnet tokens. With two repos, Phase 2 is now about 200k tokens, roughly 6% of quota.
- **Halt question (AskUserQuestion):**
  - *Continue*;
  - *Wait for reset*: the router stops, and you say "resume BT-189 at Phase N" after the reset;
  - *Stop*.

  The scratch files under `.tmp/bt189/` let a later session resume without redoing a phase.

## Phase 1: classify and inventory (2 analysts in parallel, background)
| Agent | Reads | Writes | Must return |
|---|---|---|---|
| **A1 RAT classifier** | `src/scripts/reconcile.py` (every function and CLI mode); `src/references/terminal-sync-invariant.md`; its call sites in 0b/0d/3a/3b/3c/4a; drift history in `docs/nightly/.last-run.json`, `LEARNINGS.md` and `STATUS.md` | `.tmp/bt189/s1-classification.md`: one row per unit, giving lines, class (`map-only` / `gh-post-condition` / `shared`) and file:line evidence | the share of `map-only` across script lines, prose lines and logged incidents; verdict PASS (all three at least 80%) or FAIL; the list of `gh-post-condition` units |
| **A2 Write inventory + verb fit** | every BACKLOG_MAP read and write in `src/` (workflows, skills, references, rules, scripts, memory-templates) | `.tmp/bt189/s2-inventory.md`: one row per site, giving file:line, read/write, field, class (`mirror write` / `local-only` / `gate`), and removable or needs a GitHub equivalent (ICE, Ref, sprint digit, BT-LOCAL) | BACKLOG-related characters per workflow and always-loaded; each distinct write kind mapped to one tracker verb with a GitHub and a local-markdown form, or the misfit named |

**Grade (router):**
- Spot-check 8 rows from each file against the source. More than 1 wrong row sends the report back once via SendMessage.
- A1's verdict is recomputed from its own table.

**H1:** RAT verdict, inventory headline and usage reading.
- On PASS: *Continue to Phase 2*, *Wait* or *Stop*.
- On FAIL: also offer *Re-scope*, which makes Phase 2 measure "B or C plus a slimmer post-condition gate".

## Phase 2: measure A/B/C (1 analyst, background)
**H1 outcome (2026-10-20):**
- The RAT **failed**: map-only is 71% of `reconcile.py`, 70% of the prose and 56% of incidents (`.tmp/bt189/s1-classification.md`).
- Phase 2 is **re-scoped** to "B or C **plus** a slimmer post-condition gate" (about 254 lines survive).
- **CleanTechHub** (`PatN-git/cleantech_jobs`, local `C:\Users\patri\Dev\CleanTechHub`) becomes the primary consumer case: a 48 KB map, 163 rows, 168 issues (56 open), 8 nightly reports. StratOS is the second case.

**A3 Measurement.** Read-only in both repos; writes only to StratOS `.tmp/bt189/`. Every number is reported for **both repos**.
- **B:** build a prototype generator `gen_map.py`, using one paginated GraphQL query over every issue (state, labels, milestone, parent, blockedBy, title). Write `BACKLOG_MAP.generated.<repo>.md` and diff its 7 mirrored columns against each live map. Report the drift found, which is free evidence of what the hand-written map gets wrong. Measure wall time and `gh` calls.
- **A (baseline):** `reconcile.py --ids` on a typical 3z run's touched ids (slice, epic, 2 blockers), run against each repo's map. Count its `gh` calls from the code paths and time one run.
- **C:** the scoped `gh --json` queries that load-memory (WIP set) and 3c (open slices plus ICE recomputed from the issue body) would need. Compare their output characters with a whole-map read (CleanTechHub: about 12k tokens).
- **Slimmer gate:** for the surviving post-condition units (A1's list), state the expected-state source each multi-write phase would use instead of the map, and the extra prose that needs. Without this, the text saving (iii) is overstated.

**Grade (router):**
- Re-run `gen_map.py` once and confirm the timing and the diff.
- The router itself decides where ICE and Ref go, from A2 and A3.

**H2:** a table of numbers for A, B and C against criteria (i)–(iii), plus the usage reading.

## Phase 3: decision record (router)
`docs/plans/backlog-map-decision.md` contains:
- the recommendation (adopt, reject or partial) per criterion;
- the write inventory summary;
- the measured cost;
- where ICE and Ref go;
- the offline story (tracker backend, tracker verbs);
- the deletion list with sizes;
- any surviving post-condition gate;
- if adopting, a slice breakdown ordered expand/contract (generator or adapter first, then removal of mirror writes).

**Self-grade rubric (pass at 85 or above):**
- Brief Success State items 1–6, each backed by numbers: 60.
- Issue exit criteria (inventory, cost, ICE/Ref, offline, deletion list): 25.
- Slice breakdown ordered expand/contract, or a reject rationale: 15.

**H3 (your decision):** adopt, reject or partial. Your choice is final; the record is edited to match.

## Phase 4: close the spike (router)
1. Commit the decision record and this plan by explicit paths: `docs(BT-189): spike decision record for BACKLOG_MAP`. Check it with `git show --stat HEAD`.
2. Post a findings comment on BT-189 and close it. Move `status:needs_spec` to `status:done` on GitHub and in the map, then run `python src/scripts/reconcile.py --ids BT-189` until it exits 0.
3. Hand-off: you run `/3b-create-issue` with the decision record. The slices become BT-190 children with Lifecycle `3 Implement` set by hand, and BT-190 stays `in progress`. The build plan follows the parallel-implementer pattern (disjoint files, one grader per slice, ship once).
