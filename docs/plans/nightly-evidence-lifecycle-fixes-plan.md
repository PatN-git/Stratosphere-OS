---
type: plan
title: Nightly Evidence — Lifecycle Fixes Plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-13
version: "1.0.0"
---

# Plan: lifecycle-skill fixes driven by CleanTechHub nightly evidence

**Status:** Slice **BT-162** (parent BT-116). Blocks BT-163. The source is all six CleanTechHub reports (`docs/nightly/nightly-2026-07-25` … `-10-13`), read in full and cross-checked against `src/`. The 0d rework itself is out of scope here and lives in [`0d-rework-plan.md`](0d-rework-plan.md).

## Verdict
Five framework changes are justified. Each has evidence from at least two nights or a confirmed bug. None needs a new skill. One is a deterministic bug fix (F1). The rest are wording or contract changes (F2–F5).

## Framework changes (StratOS `src/`), in priority order

| # | Change | Evidence | Target | Size | Verified? |
|---|---|---|---|---|---|
| F1 | **reconcile.py false label drift.** `status:*` is stripped from GitHub labels (`:108`) but not from map labels (`:46`). Every row whose Labels cell carries a status reports phantom drift. Strip it on both sides; status is already compared separately (`:97`). Add a test row that has `status:` in Labels. | 18/79 D-items on 10-09 and 11/74 on 10-13 are status-only. BT-051 carries `status:needs_spec` on GitHub yet shows `map_only=['status:needs_spec']`. | `src/scripts/reconcile.py` `compare()`; `tests/` reconcile suite | S | **Confirmed** (code read) |
| F2 | **Fix-ladder rung 3 is too loose.** Agents treat a `[PATTERN]` LEARNINGS id as "existing law". They cite it and write nothing, every night. Rule: rung 3 = `[LAW]` entries only. A finding that matches a LEARNINGS id is a recurrence and must go to rung 1 or 4. | Shell quoting: 09-17 (39 failures, which created L-013/L-014), then 10-05, 10-09 and 10-13 were all re-routed to rung 3. Re-reads: L-015 was created 09-17 and routed to rung 3 on 10-13. | `src/references/environment-fix-ladder.md` §Rungs 3 + §Rules (cited by 0b and 0d) | S | Confirmed (text read) |
| F3 | **Split rung 4. A consumer project never acts on StratOS.** Today rung 4 says "file it against StratOS". That mixes two causes, and no project ever did it (`gh issue list`: nothing filed). Replace it with: **(a) Host/tooling behaviour** (shell quoting, missing Chrome, scheduler limits) → rung 1 *locally* (hook, setup check, local rule); it is environment, not framework. **(b) Defect in an installed StratOS skill** (stale path, missing guard, wrong contract) → a **Framework feedback notice**: a short, self-contained note the project owner can forward to the StratOS maintainer. It names the skill, its installed version (from `stratosphere-setup/versions.json`), the defect, the evidence (session/step) and a suggested fix. Nothing is filed or sent automatically, no repo is named, and installed skills are never edited locally (updates overwrite them). | git-diff exit-1 (10-09), scaffold flag hallucination (10-09): skill defects, never surfaced to the owner. Shell quoting (4 nights): host behaviour misrouted as framework. | `environment-fix-ladder.md` rung 4 + §Rules; consumers 0b step 4, 0d Phase 2/4 | S | Confirmed (gh) |
| F4 | **Shell-quoting needs a rung-1 control.** `src/` has no PowerShell/inline-script guidance at all, and LEARNINGS entries have not changed behaviour. Extend the existing bullet in `src/constitution/AGENTS.md` §3 **Intermediates** (line 29), which already sends scratch files to `.tmp/`. No new rule file is needed: "Store all temporary files, scratch logs, scraped data, **and scratch scripts** in `.tmp/` … **Multi-line or quote-heavy code: write it to `.tmp/<name>.py\|js` and run the file, never inline via `python -c` / `node -e`.**" It is host-neutral and adds one clause to always-loaded text. A Claude Code PreToolUse hook stays optional if the failure recurs after this. | 4 consecutive nights. | `src/constitution/AGENTS.md` §3; constitution version bump; char-budget test | XS | Confirmed (grep: no matches in src/; no fitting file in `src/rules/`) |
| F5 | **4a never clears epic-level blockers.** Step 7 removes only the *slice* id from dependents. When a dependent is blocked by an *epic*, the GitHub edge survives the epic shipping. Extend step 8 (epic flips to `in review`) to clear the epic id from dependents (map + `removeBlockedBy`), and add the epic id to the step 9 `--ids`. **Spike first:** confirm from BT-215's history that no other step was meant to clear it. | 07-25: 10× "stale blocker BT-055". 10-05 onward: `gh=['BT-215']` stale, 8 rows a night on 10-09 and 10-13. | `src/workflows/4a-verify-and-ship.md` steps 7–9 | S | **Hypothesis** |
| F6 | **Upstream the okf_viewer nested-YAML fix.** CleanTechHub commit `2143aca` (top-level keys only, `indent == 0`) is missing from `src/scripts/okf_viewer/document.py`. The next StratOS update will likely overwrite the local fix. | Diff confirmed by the analysis agent. | `src/scripts/okf_viewer/document.py` + test | XS | Diff confirmed; overwrite behaviour unverified |
| F7 | **Stale local rules after a framework move (candidate).** CleanTechHub's local always-on `.agents/rules/workflow-fidelity.md` still points at `.agents/workflows/` and underscore command names, which is the likely cause of the 10-13 stale-path failure. A setup/update lint that flags consumer `.agents/rules/*` referencing removed framework paths would catch this class of problem. | 10-13 Phase 1 #1 (`.agents/workflows/3d_implement-issue.md`). | `src/commands/stratosphere-setup` update path, or `validate_memory.py` | S | Root cause is a hypothesis |

**Already landed (no action):** 4a now does the PR-link comment before reconcile (step 6 before step 9, the 09-17 finding). Index rebuild is scripted. No session roster.

## CleanTechHub-local (not StratOS; for that project's backlog)
- Fix or delete `.agents/rules/workflow-fidelity.md` (stale paths). This is the quick fix for F7's symptom.
- One-time drift heal after F1 ships: 19 rows are missing `priority:*` and 15 are missing `parent` in the map, and BT-215 blockers are stale.
- Investigate why every GitHub `size:*` label became `size:medium` between 10-09 and 10-13 (18 new D-items, cause unknown).
- `ingest-tier4.js`: fail fast with a `.env.local` hint. Chrome is absent at its default path, so browser MCPs need a fallback (local rung 1, per F3a).
- Decide L-017 (`[ASSUMED]` since 09-22, cites BT-163/BT-168): promote to `[PATTERN]` or tombstone it.

## Sequencing
1. **F1** first. It is a confirmed bug and removes about 15% of drift noise, which makes everything downstream readable.
2. **F2 + F3** as one PR (the same reference file).
3. **F4**.
4. **F5** after its spike.
5. **F6, F7** opportunistically.

## Success criteria
- F1: the 10-13 reconcile run on CleanTechHub drops the 11 status-only D-items; the test is green.
- F2/F3: on the next nightly where shell quoting recurs, the run produces a local rung-1 recommendation, not "existing law covers it". A skill defect produces a Framework feedback notice and no outward action. No `src/` file names a StratOS repo or filing target.
- F4: the constitution char-budget test passes; within two weeks the nightlies show no new inline-quoting failures.
- F5: after an epic ships, `reconcile.py --ids <dependents> --fields blocked_by` is clean.

## Implementation spec (re-planned 2026-10-13, after BT-164..167)
A read-only planning pass re-verified every item against the current branch. The 0d commit `3561941` already added 0d's `## Framework feedback` section, and BT-167 changed 4a steps 7–9. **Scope:** F1, F2+F3, F4, F5, F6. **F7 is dropped** (user decision): CleanTechHub fixed the symptom in BT-235, and its intentional `.agents/workflows/` stubs would trip the lint.

**Corrections to the draft above:**
- **Acceptance "no `src/` file names a StratOS repo":** narrow it to "…as a filing target for consumer findings". Legitimate update paths name the repo.
- **F2 evidence:** shell quoting was rung 3 only on 10-13. The pattern (cite a `[PATTERN]`, write nothing) holds.
- **F3:** the 0d side is done, and 0b needs no change. Name the skill's own `version:` frontmatter, not `versions.json`.
- **F4:** no test capped §3 before this. Edit the root `AGENTS.md` too.
- **F5:** the 07-25 BT-055 evidence is slice-level, so drop it.
- **F6:** `scaffold.py` flags modified scripts as NEEDS-REVIEW and does not overwrite them.

| # | Change | Files (bump) | Tests |
|---|---|---|---|
| F1 | `reconcile.py` `compare()`: drop `status:*` from the **map** label set before comparing (status is compared separately). Leave `parse_backlog` unchanged. | `src/scripts/reconcile.py` | `tests/workflows/test_reconcile.py`: a row with `status:planned` in Labels vs a matching GitHub issue gives `[]` |
| F2+F3 | `environment-fix-ladder.md`. **Rung 1** absorbs host/tooling behaviour (local hook, setup check or project rule). **Rung 3** = a `[LAW]` entry or core rule, on its first miss; a `[PATTERN]`/`[ASSUMED]` LEARNINGS id is not law. A finding that matches any LEARNINGS id, or a law cited on an earlier night, is a recurrence and goes to rung 1 or 4, never 3. **Rung 4 renamed "Framework feedback":** a defect in an installed StratOS skill, recorded as skill · installed `version:` · defect · evidence · suggested fix wherever the citing workflow records findings (0d report, 0b handoff). Never file it, name a repo, or edit the installed skill. | ladder 1.0.0 → 1.1.0 | `tests/workflows/test_environment_fix_ladder.py`: `[LAW]`, recurrence, "against StratOS" absent, rung-4 fields mirror 0d's |
| F4 | Constitution §3 **Intermediates**: add scratch scripts to `.tmp/`; "never inline multi-line or quote-heavy code in a shell command (`python -c`, `node -e`): write it to `.tmp/` and run the file". Same text in root `AGENTS.md`. | constitution already bumped on the branch (3.3.2); root unversioned | `tests/framework/test_host_hygiene.py`: clause present in both, plus a **whole-file cap of ~9,200 chars per constitution** (user decision A + (ii)) |
| F5 | **4a step 8:** after the epic flips to `in review`, clear `BT-<parent>` from every dependent's `Blocked by` (map + `removeBlockedBy`), as in step 7. **Step 9 `--ids`** includes the dependents cleared in step 7 or 8. **terminal-sync-invariant:** heals clear a stale blocker on both sides (map cell and GitHub edge). **0b step 1:** after its post-merge clearing, run `reconcile.py --require-gh --ids <cleared dependents> --fields blocked_by` and heal at most 3 times (user decision: 4a + 0b gate). The standing-epic skip in step 8 stays. | 4a (1.4.0) and terminal-sync (1.1.0) already bumped; 0b first bump (patch or minor, implementer's call) | step 8 epic-clear, step 9 dependents, 0b gate |
| F6 | Port CleanTechHub `2143aca` (only top-level `indent == 0` keys count as frontmatter fields) into `src/scripts/okf_viewer/document.py`, **plus** reset `current_key=None; list_items=[]` in the indented branch (user decision). | script (unversioned) | `tests/scripts/test_okf_rebuild_indices.py`: nested `title:`/`description:` under a parent key keeps the top-level title; no stray top-level `by`/`at` |

**Order:** F1 → F2+F3 → F4 → F5 → F6 (one slice, one implementer, one review).
