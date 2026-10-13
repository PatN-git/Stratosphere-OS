---
type: plan
title: 1b Discovery Brief Sections and Brief Locator Plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-13
version: "1.0.0"
---

# Plan: give the discovery brief a home for what 1b already captures

**Status:** Slices **BT-164** (C1–C5) and **BT-165** (C6–C8), both under parent BT-010, the standing umbrella epic "Lifecycle - 1 Analysis". Not started. Both ship in PR #161 (`fix/0d-recommendation-brief`), with one release for the whole PR. This revises an Antigravity draft (session `0460c303`, `1b_framing_template_enhancement_plan.md`) after review; an independent subagent then reviewed this plan, and its fixes are folded in. Decisions D1–D3 below were settled with the user.

## Evidence (CleanTechHub briefs and sessions)
| Problem | Data |
|---|---|
| G2 facts lost | BT-234 (2026-10-13): 6 model call sites, auth via header vs URL query, 15 s vs unbounded timeouts, and vendor deprecation dates were found during the grill. The brief kept 2–3 sentences of Problem and 5 Prior Art bullets. |
| Success criteria dropped | BT-234: fail-loud validation and a watcher simulation (replaying a 3.5 → 3.6 model reroute) were agreed but had no section to go in. 1b Phase 2 probes "Success state", but the template has nowhere to put it. |
| Settled decisions crammed into invented headings | BT-215: "Card Hygiene Rule", "Job Inheritance Rule" and "Regional Sparsity Rule" were all filed under `## Constraints`. 5 of 14 briefs invented headings (e.g. `## Architectural Directives & Resolved Technical Decisions`, `## Constraints & Settled Angles`). |
| RAT vocabulary is demand-only | BT-168 (`taxonomy-foreign-key-drift.md`) recorded a "template deviation": the want was not in question, so the cheapest test was a read-only probe of the live system. |

## Decisions
- **D1 — A bounded technical section is allowed.** Add `## Established Facts (as of <date>)`. File paths are allowed there **as evidence only**. There is no separate decision log: rename `## Constraints` to `## Constraints & Settled Decisions`. It only holds decisions the user confirmed (G2), each with a one-line reason. 2a maps both into PRD §7 and restates paths as capability names, so the PRD stays path-free.
- **D2 — The work file is still deleted in Phase 7.** The brief is the only hand-off. A new Phase 6 gate checks that the work file's recorded content landed in the brief before the file is deleted.
- **D3 — `## Decoupled Follow-ups`.** Each line is `<topic>: <why decoupled> — existing: BT-<n> | candidate`. 1b never files issues. 2a maps the section to §9. 1b Phase 7 suggests `/3b-create-issue` for each `candidate`, and the user decides.
- **D4 — Scope Facets are views of one problem.** They sit as an optional sub-list under `## Problem`, and the heading name is unchanged. Independent problems are still split (Phase 1 step 3).
- **D5 — Brownfield cheapest tests.** Add `offline sample benchmark | read-only production probe | simulation harness` to the cheapest-test options, and add guidance on when to use them.
- **Dropped from the draft:** retaining the work file for 2a; the `Core Intent (synthesized)` line in Ask; a separate `Key Decisions` section; renaming `## Problem`; the mermaid diagram.

## Changes
Edit `src/` only. `dist/` is rebuilt by `build/build.py`. Line numbers drift, so re-anchor each edit by content. Use `improve-workflows-skills` while editing. Refresh `timestamp:` on every file whose version is bumped.

### C1 — `src/references/discovery_brief_template.md` (2.0.1 → 2.1.0)
- Leave the frontmatter block unchanged.
- Update the `description:` to mention facts, success state and follow-ups.
- The instruction says to write the body "verbatim"; amend it to "verbatim, omitting any section or sub-list marked *optional*".

New artifact body (sections not listed here stay verbatim):

```markdown
## Problem
<2–3 sentences. What hurts, who is affected, cost of inaction. Agreed vocabulary only. No solutions.>

**Scope facets (optional — views of this one problem, never separate problems):**
- **<Facet>:** <symptom / root cause / preventive dimension>

## Established Facts (as of <YYYY-MM-DD>)
<Optional — omit for greenfield. Current-system facts found by G2 lookups, so downstream phases do not re-investigate them. Each fact names its source. File paths are allowed here as evidence only.>

- <fact> — source: <file / query / doc URL>

## Chosen Framing
(unchanged)

## Success State
<Observable, measurable outcomes: how the maintainer, test suite or user confirms success. No implementation.>

1. <outcome>
2. <behaviour under failure or edge case>

## Prior Art
<Related BT-<n>, memory refs ([L-xx], [G-xx]), prior attempts. Current-system facts go in Established Facts.>

## Non-Goals (early signal)
(unchanged)

## Decoupled Follow-ups
<Wanted, but handled separately from this brief. Not non-goals. 1b files nothing.>

- <topic>: <why decoupled> — existing: BT-<n> | candidate

## Constraints & Settled Decisions
<User-locked boundaries and decisions the user confirmed during the grill (G2), each with a one-line reason so the PRD does not reopen them. No solution design.>

- **<Decision>:** <choice> — why: <reason; rejected alternative>
```

Section order: Ask, Vocabulary, Actor, Problem, Established Facts, Chosen Framing, Success State, Prior Art, Non-Goals, Decoupled Follow-ups, Constraints & Settled Decisions, Open Questions, Riskiest Assumption, Recommended Next Step.

In Riskiest Assumption, change the cheapest-test line to `cheapest_test ∈ {landing page + waitlist | N DMs | fake-door button | rough mock shown to 5 | offline sample benchmark | read-only production probe | simulation harness}`.

### C2 — `src/workflows/1b-concept-framing.md` (1.2.1 → 1.3.0)
1. **Hand-off contract (top line):** replace the section and § list with a pointer to one copy: "`/2a-write-prd` seeds the PRD from this brief per its Phase 3 *Discovery-brief ingestion* mapping."
2. **Phase 1 step 8 (work file):**
   - The coverage checklist gains `Facts`, `Decisions` and `Follow-ups`.
   - The structure gains `## Established facts`, `## Settled decisions` and `## Decoupled follow-ups`.
   - The Write rule becomes "on checklist change, G2 lookup result, or decision lock".
3. **Phase 2:**
   - Under G2, record each lookup result with its source in the work file's `## Established facts` when it lands.
   - Record each user-confirmed decision with its reason in `## Settled decisions`.
   - Change the focus area "Internal Prior Art — code touching this, or prior attempts" to "Internal Prior Art — prior attempts and BT refs; current-code facts → `## Established facts`".
   - Add a focus area: "Decoupled follow-ups — wanted, but deferred to separate work".
4. **Phase 4.5:**
   - Step 2 becomes: "Propose the fastest test that fits the domain. Demand/greenfield: landing page, waitlist, N DMs, fake-door, rough mock. Brownfield/reliability, where the want is not in question: offline sample benchmark, read-only production probe, simulation harness. Must not take > 2 weeks."
   - Step 3 (Skeptical Challenger): add Established Facts to its Input. Give its Output's `cheapest_test` the full option set from C1.
5. **Phase 5 rules:**
   - Replace "No solution, modules, interfaces, or file paths." with "No solution design, modules or interfaces. File paths only in Established Facts, as evidence."
   - Add: "Problem: compound scope → Scope facets of one problem."
   - Add: "Constraints & Settled Decisions: only user-confirmed (G2), each with a reason."
6. **Phase 6 gates:**
   - Amend the Problem gate: "...no solution language; compound scope uses Scope facets."
   - Add `Established Facts each name a source and the section is dated (or omitted for greenfield).`
   - Add `Settled decisions were confirmed by the user and carry a reason.`
   - Add `Success State is observable and measurable.`
   - Add `Decoupled Follow-ups are each marked existing BT-<n> or candidate.`
   - Add, for the work-file path only: `Every entry under the work file's ## Established facts, ## Settled decisions and ## Decoupled follow-ups appears in the matching brief section; every [x] coverage item maps to a non-empty brief section (Research → Prior Art / Chosen Framing).`
7. **Phase 7:**
   - Step 5 (delete the work file) is unchanged.
   - Step 6 adds: "For each `candidate` follow-up, suggest `/3b-create-issue`; the user decides."

### C3 — `src/workflows/1c-concept-map.md` (1.1.2 → 1.2.0)
Phase 3 step 4 copies the 1b Phase 6 checklist inline. Bring it in line with C2.6:
- the amended Problem gate;
- every new gate except the work-file gate (1c has no work file).

### C4 — `src/workflows/2a-write-prd.md` (1.5.0 → 1.6.0)
Replace the Phase 3 "Discovery-brief ingestion" paragraph with:

> **Discovery-brief ingestion (if a brief was located):** use its Vocabulary throughout; seed §1 from Problem (including Scope facets) and Actor, §2 from Chosen Framing, §4 from Non-Goals, §5 and §8 from Success State, §6 story actors from Actor, §7 from Constraints & Settled Decisions (or a legacy `## Constraints`) and Established Facts (restate file paths as capability names — §7 stays path-free), §9 from Decoupled Follow-ups; absorb Open Questions into §10. Do not re-interview what the brief already settled (its distilled decisions are the source of truth). The RAT Carry-Over below already reads its `## Riskiest Assumption`.

This also covers the 2z PRD Drafter, which follows 2a Phase 3 (2z:20).

### C5 — `tests/workflows/test_discovery_brief_contract.py` (new)
Follow the existing style: `ROOT = Path(__file__).resolve().parents[2]`.

**Contract test:**
- Headings: take only the template lines after `## Artifact body`. The yaml fence sits above that line, and the body has no fences.
- Section names: strip parenthetical suffixes with `^## (.+?)(?: \(.*\))?$`. This turns "Ask (verbatim)", "Non-Goals (early signal)" and "Established Facts (as of …)" into bare names.
- Target: the single line in `2a-write-prd.md` that starts `**Discovery-brief ingestion`.
- Pass condition: each section name appears in that line, or is in `NOT_INGESTED = {"Ask", "Prior Art", "Riskiest Assumption", "Recommended Next Step"}`. The two are not exclusive: Riskiest Assumption is named there and also read by RAT Carry-Over.

**Cheapest-test test:** the template's cheapest-test line contains all three brownfield options.

**Gate test:**
- 1b: the text between `## Phase 6` and `## Phase 7` mentions Established Facts, Success State and Decoupled Follow-ups.
- 1c: the text between `4. **Self-Review` and `5. **Crystallize` mentions the same three.

**Hand-off test:** 1b's hand-off contract line points to 2a's ingestion mapping and repeats no § list.

`tests/lifecycle-harness/spike_1b.py` `REQUIRED_SECTIONS` (Actor, Problem, Chosen Framing, Non-Goals, Riskiest Assumption) still passes: all those headings remain as substrings. No edit needed.

## Slice BT-165 — locate slug-named briefs in 2c and 2z
**Problem:**
- `2c-reconcile-specs` Phase 1 looks for the brief as `docs/discovery/BT-<padded>-*.md`. Briefs are slug-only (1b strict late binding), so 2c never finds one, and the brief silently drops out of reconciliation.
- `2z-write-spec` gives its PRD Drafter "discovery brief" as input, but never says how main locates it, and its 2c step inherits the broken locator.
- The link already exists: 2a Phase 2 writes `linked-prd: BT-<padded>` into the brief's frontmatter.
- This matters more after BT-164, because briefs will carry facts and decisions that 2c should check against the PRD.

**One locator rule**, worded the same in both files: *"the `docs/discovery/*.md` (excluding `*.work.md` and `*.map.md`) whose frontmatter has `linked-prd: BT-<padded>`; if none, 2a's slug fuzzy-match (2a Phase 1 step 5)."*

### C6 — `src/workflows/2c-reconcile-specs.md` (1.2.1 → 1.2.2)
In Phase 1 "Resolve target artifacts", replace `Discovery docs/discovery/BT-<padded>-*.md` with the locator rule. A missing brief stays a finding, not an error (unchanged).

### C7 — `src/workflows/2z-write-spec.md` (1.0.1 → 1.1.0)
- **Phase 0:** after hydrating, main resolves the brief once with the locator rule and records its path (or `none`) in the decision log, so a resumed run reuses it.
- **PRD Drafter input:** "discovery brief path (from the decision log)".
- Before 2a mints the ID, `linked-prd:` is not set yet, so the slug fuzzy-match is the path that applies. Say so in one clause.

### C8 — tests (extend `tests/workflows/test_discovery_brief_contract.py`)
- No file in `src/workflows/` contains `docs/discovery/BT-`.
- `2c-reconcile-specs.md` and `2z-write-spec.md` both contain `linked-prd`.

## Ship
- **One PR, one release.** Both slices land on `fix/0d-recommendation-brief` (PR #161), as the user decided, so the whole PR ships as a single release. No new branch: this overrides the 3d step 1 branch derivation, a recorded deviation.
- **Standing epic.** BT-010 is a standing umbrella epic with no BACKLOG row. Do not promote it (3d step 2). In 4a, build the PR body without `--close-parent`, and skip the Feature Acceptance Audit (4a epic check).
- **Commits** (follows the BT-152 precedent):
  - `docs(plans)` for this plan file.
  - `feat(BT-164)` for C1–C4 and `test(BT-164)` for C5.
  - `fix(BT-165)` for C6–C7 and `test(BT-165)` for C8.
- **Verify:** `python build/build.py`, `python build/validate.py`, `python -m pytest -q` (including `test_dist_bundle`). Commit `dist/` together with `src/`.
- **Release (once, last commit in the PR):**
  - Commit `1d4d1e2` already prepared v4.7.0, which is not tagged yet; the last tag is v4.6.1.
  - After all slices (and anything else the user adds) are in, rerun `python scripts/release.py` so the version reflects every artifact bump. Commit its output as `release: prepare vX.Y.0`. Its output is build.py VERSION, README, marketplace.json, dist/plugin.json and the external-skills.json pins.
  - `bump_guard` (CI) requires VERSION to be above the last tag.
- **4a body:** the `stratos-pr` block lists BT-164 and BT-165 as slices, and drops the "No BT issue" deviation for them (the 0d change itself stays issue-less).
- **Dry fit:** hand-map the BT-234 and BT-215 session content into the new template. Every item from the Evidence table must land in a named section, with no invented headings.
- Do not run the paid lifecycle harness (`spike_1b.py`) unless the user asks.
- Ship via `/4a` (HITL); a human merges the PR.
