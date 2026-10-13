---
type: plan
title: 1b Discovery Brief Sections and Brief Locator Plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-13
version: "1.0.0"
---

# Plan: give the discovery brief a home for what 1b already captures

**Status:** not started. Four slices under parent BT-010, the standing umbrella epic "Lifecycle - 1 Analysis":
- **BT-164**: C1–C5, C9–C11, C14–C16.
- **BT-165**: C6–C8, C12–C13. Blocks BT-164 and BT-166.
- **BT-166**: A1–A9.
- **BT-167**: B1–B3.

All four ship in PR #161 (`fix/0d-recommendation-brief`) as one release. Gap IDs (L/S/V/H) and evidence come from [`lifecycle-artifact-flow-audit.md`](lifecycle-artifact-flow-audit.md). Its H1–H4 items are deferred to BT-168 (under BT-116). This revises an Antigravity draft (session `0460c303`, `1b_framing_template_enhancement_plan.md`) after review; an independent subagent then reviewed this plan, and its fixes are folded in. Decisions D1–D3 below were settled with the user.

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

### C5 — `tests/workflows/test_discovery_brief_contract.py` (extend; BT-165's C8 creates it)
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

### C9 — 3b reads the brief (audit L4)
D1 deliberately keeps file paths out of the PRD, so file-level facts have to reach the slices straight from the brief.
- **3b Phase 1:** PRD-sourced runs also load the brief linked in the PRD frontmatter (`discovery:`, from C12).
- **Phase 2 step 3:** seed each Build slice's "Current state / Problem" from the brief's Established Facts (file paths are allowed in issue bodies) and Constraints & Settled Decisions.
- **Slice Draft Auditor:** also reads the brief. Precedence: PRD > design > brief > research. A fact in the brief that the PRD and design leave out is flagged `[BRIEF-GAP]` for HITL, in the same way as `[RESEARCH-GAP]`.

### C10 — RAT status values (audit L5)
2a "RAT Carry-Over": `untested | running | failed` → §10, blocking; `survived` → §11. Drop the non-value "validated". Both are edits to 2a, which C4 already touches.

### C11 — concept-map link (audit L6)
- **Template frontmatter:** add `concept-map: <#n | path> | —`.
- **1c Phase 3 step 2:** sets it when 1c writes the brief.
- **2c:** reads it, which supplies the "map the brief cites" that 2c:26 expects.

### C14 — 1c glossary `Avoid:` lists (audit H3)
1c Phase 3 step 5 writes `[[G-xxx]] [ASSUMED]` entries without the `Avoid:` list that 1b writes (1b Phase 7 step 2), but 3d's avoid-drift check (3d Phase 2.5) depends on that list. Add "each with its `Avoid:` list (rejected synonyms from the map's resolutions)". This rides on C3's 1c bump, so no extra version bump.

### C15 — brief provenance (audit H3)
The brief template's `generated.by: 1b-concept-framing` becomes `generated.by: 1b-concept-framing | 1c-concept-map`, and the writer picks one. 1c Phase 3 step 2 stamps `1c-concept-map`. This rides on C1's template bump.

### C16 — design template handoff heading (audit H3)
- **File:** `src/references/design-doc-template.md` (2.0.0 → 2.0.1).
- **Heading:** `## Handoff Notes for 3c/4a` becomes `## Handoff Notes for 3d/4a`.
- **Placeholder:** "...that 3c must implement" becomes "...that 3d must implement".
- **Why:** 3c (sprint planning) never reads the design doc. 3d implements from it, and 4a's auditors receive the full design doc.

## Slice BT-165 — deterministic artifact links (locator, PRD links, parent-keyed paths)
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

### C8 — tests (create `tests/workflows/test_discovery_brief_contract.py`; BT-165 runs first, and BT-164/166 extend it)
- No file in `src/workflows/` contains `docs/discovery/BT-`.
- `2c-reconcile-specs.md` and `2z-write-spec.md` both contain `linked-prd`.

### C12 — PRD frontmatter links (audit L2)
- **PRD template frontmatter:** add `discovery: <path> | —` and `research: <path> | —`.
- **2a:** fills both when it locates the files: Phase 1 step 5 finds the brief; add a research locator next to it using 1b's research-matching rule. Together with the brief's `linked-prd:`, this makes the link bidirectional.
- **Readers:** 2c, 2z, 3b and 4a read these fields first. The C6/C7 locator rule is only the fallback, for PRDs written before this change.

### C13 — parent-keyed spec paths (audit L3)
3d step 3, the 4a Phase 2 auditor input and the 3z dispatch currently build `docs/prds|design/BT-<padded>-…` from the **slice** ID. They should:
- resolve `BT-<parentPadded>` from the slice's Parent (BACKLOG `Parent`, or `gh issue view --json parent`);
- then follow the PRD frontmatter.
A standalone slice has no PRD and states that.

C8 tests also assert:
- no `docs/prds/BT-<padded>` or `docs/design/BT-<padded>` remains in 3d, 4a or 3z;
- the PRD template carries `discovery:` and `research:`.

## Slice BT-166 — 3b/4a input contract (audit S1–S6, V1–V3, H4)
### A1 — 3b siblings (S1)
- **Phase 1:** read `gh issue view <parent> --json subIssues` and the BACKLOG rows with `Parent = BT-<parent>`.
- **Phase 2:** draft only for §6/§8 and design items that no existing slice covers.
- **Auditor breadth map:** counts an existing slice as covering, citing its `BT-<n>`.

### A2 — explicit PRD scope (S2)
- **Phase 1 scope:** §1, §6, §7, §8 plus §10. An open blocking §10 question becomes a Spike before drafting, not after the audit.
- **Hand-off lines:** align 2a's and 3b's with the body.

### A3 — design link (S3)
- **Build template `### Dependencies`:** add `- **Design:** docs/design/BT-<p>-interface.md | —`.
- **3d step 2:** keys its conditional read on that line. Replace "design reference in issue/BACKLOG Ref" (the Ref column holds memory IDs only).

### A4 — `[MED]` (S4)
3b's Confidence map becomes `[HIGH]` 100% / `[MED]` 80% / `[LOW]` 50%, and accepts `[MEDIUM]` as legacy.

### A5 — migration items (S5)
- **2c:** records a pre-Slice-1 migration as a PRD §10 item tagged `migration:`.
- **3b:** mints each one as Slice 1 (a blocker of every slice it touches).

### A6 — slice milestone (S6, unconfirmed)
- Check whether a 3b run's terminal gate flags `milestone` drift for Build slices minted without `--milestone`.
- If confirmed, pass `--milestone <vX.Y.0>` on `gh issue create`. If not, drop A6 and say so.

### A7 — slice AC source (V1)
- **4a business-logic auditor input:** the slice issue body's `### Acceptance Criteria` (primary, via `gh issue view <n>`) plus the parent PRD §6/§7/§8 and design (C13 paths).
- Rename the Phase 3 table to "Slice AC / Requirement".
- Phase 1 step 2 "explicit PRD AC" becomes "explicit slice AC".

### A8 — deviations and manual-QA (V2, H4)
- **4a step 5 `pr_body.py build` literal:** gains `--deviation "<each line of the 3d plan's ## Deviations>"` and `--manual-qa` when 3d or 3z flagged it.
- **Phase 2 business-logic auditor:** receives the plan's `## Deviations`, so a recorded, intentional deviation is judged rather than re-flagged.
- **Step 10:** deletes the plan only after the body build has succeeded.
- **3z final report:** lists the deviations inline instead of `plan_path`. Update `tests/workflows/test_3d_plan_phase.py` if it pins `plan_path`.

### A9 — Feature Acceptance Audit scope (V3)
In `src/references/feature-acceptance-audit.md`, "the parent PRD full AC set" becomes: §8 Definition of Done, §5 Success Signals, and the `[BASELINE]`/`[DIFFERENTIATOR]` §6 stories. This closes the loop from brief Success State (C1) → PRD §5/§8 (C4) → feature acceptance.

Tests:
- 3b names `subIssues`, §7, §10 and `[MED]`;
- the Build template has a `Design:` line;
- 4a step 5 carries `--deviation`;
- the FAA names §8 and §5.

## Slice BT-167 — standing epics and one-release PRs (audit V4, V5)
### B1 — standing-epic rule
A parent epic is **standing** when no `docs/prds/BT-<p>-*.md` exists and its body is not an audit epic (no line-1 `Source:`). Write the rule once, in `src/references/terminal-sync-invariant.md` or a new short reference, and cite it from each step. For a standing epic:
- **3d step 1:** the branch is keyed to the slice (`<type>/BT-<slice>-<slug>`), unless the user names an existing branch.
- **3d step 2:** never promote the epic.
- **4a step 8:** no Epic Check, no Feature Acceptance Audit, no `--close-parent`. The PR may open non-draft.
- **4a step 9 draft rule:** skip it.

This replaces the host-side memory note (Claude-only, invisible to Antigravity).

### B2 — release rerun
4a step 4 changes from "once per PR" to: rerun `python scripts/release.py -y` at every ship, and commit as `release: prepare v<x>` only if its output changed. It derives from the last tag, so a rerun is idempotent.

### B3 — tests
- the standing-epic predicate (PRD absent and not an audit epic);
- 4a's draft rule cites the exemption;
- step 4 says rerun.

## Implementation loop (agreed 2026-10-13)
Run the slices one at a time, in the order 165 → 164 → 166a (A1–A6) → 166b (A7–A9) → 167. They share files (2a, 3b, 4a, 1c), so they cannot run in parallel. For each slice:
1. **Start:** set the slice to `status:in progress` in GitHub and BACKLOG_MAP.
2. **Implement:** a fresh Sonnet implementer subagent gets its plan section and the audit doc, and uses `improve-workflows-skills`.
   - It edits `src/` and `tests/` only, re-anchoring each edit by content.
   - No git writes, no GitHub, no `dist/` (the lead rebuilds it).
   - If the plan is ambiguous, it returns a question rather than guessing.
3. **One bump per file per PR:** before bumping a file, check `git diff main -- <file>`. Bump only if `version:` is unchanged against main. If a later slice adds behaviour to a file an earlier slice bumped as a patch, raise the level (e.g. 1.2.2 → 1.3.0), but never add a second increment. Refresh `timestamp:` regardless.
4. **Review:** a fresh read-only reviewer scores the slice against its plan items and the issue's Acceptance. The lead verifies the findings and fixes the confirmed ones. At most 2 fix rounds, then HITL.
5. **Gate and commit:**
   - Run `python build/build.py`, `python build/validate.py`, `python -m pytest -q`.
   - The lead commits per slice with explicit paths (`src/`, `tests/`, `dist/`; `.agents/` is untracked), then checks `git show --stat HEAD`.
   - Push only at the end, unless the user asks earlier.
6. **Manual steps** are not handed to the subagent. The C-series dry fit is for the lead or the user. A6 is an investigation; report it as confirmed or dropped.
7. **After the loop:**
   - full test suite;
   - rerun `release.py` once;
   - `/4a` (HITL) and update the PR body;
   - retire the host-side standing-epic memory note once BT-167 has landed.

## Ship
- **One PR, one release.** All four slices land on `fix/0d-recommendation-brief` (PR #161), as the user decided, so the whole PR ships as a single release. No new branch: this overrides the 3d step 1 branch derivation, a recorded deviation.
- **Order:** BT-165 → BT-164 → BT-166 (both blocked by 165) → BT-167 → release. BT-167 must be in before `/4a` ships PR #161, so the standing-epic handling is the framework's rule rather than a manual deviation.
- **Standing epic.** Until BT-167 lands, apply its rule by hand: BT-010 is a standing epic with no BACKLOG row, so don't promote it, use no `--close-parent`, and skip the Feature Acceptance Audit.
- **Commits** (follows the BT-152 precedent):
  - `docs(plans)` for the plan and audit files.
  - `feat(BT-164)` for C1–C4, C9–C11 and C14–C16; `test(BT-164)` for C5.
  - `fix(BT-165)` for C6, C7, C12 and C13; `test(BT-165)` for C8.
  - `feat(BT-166)` / `fix(BT-166)` for A1–A9, plus `test(BT-166)`.
  - `feat(BT-167)` for B1–B2; `test(BT-167)` for B3.
- **Verify:** `python build/build.py`, `python build/validate.py`, `python -m pytest -q` (including `test_dist_bundle`). Commit `dist/` together with `src/`.
- **Release (once, last commit in the PR):**
  - Commit `1d4d1e2` already prepared v4.7.0, which is not tagged yet; the last tag is v4.6.1.
  - After all slices (and anything else the user adds) are in, rerun `python scripts/release.py` so the version reflects every artifact bump. Commit its output as `release: prepare vX.Y.0`. Its output is build.py VERSION, README, marketplace.json, dist/plugin.json and the external-skills.json pins.
  - `bump_guard` (CI) requires VERSION to be above the last tag.
- **4a body:** the `stratos-pr` block lists BT-164 to BT-167 as slices, and drops the "No BT issue" deviation for them (the 0d change itself stays issue-less).
- **Dry fit:** hand-map the BT-234 and BT-215 session content into the new template. Every item from the Evidence table must land in a named section, with no invented headings.
- Do not run the paid lifecycle harness (`spike_1b.py`) unless the user asks.
- Ship via `/4a` (HITL); a human merges the PR.
