---
type: plan
title: Lifecycle Artifact Flow Audit
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-13
version: "1.0.0"
---

# Lifecycle artifact flow audit (phases 1–4)

**Question:** does the information gathered in phases 1–2 reach the steps that need it in 3b (slicing), 3d (build) and 4a (verify)?
**Method:**
- Read every `src/workflows/{1a…4c}.md` in full, plus the templates and scripts they load.
- Spot-checked the key findings against the files.
- `file:line` refers to `src/workflows/` unless a file is named.
- "unc." marks a finding not yet confirmed.

**Companion:** [`1b-discovery-brief-sections-plan.md`](1b-discovery-brief-sections-plan.md) (BT-164/BT-165) fixes the brief itself. This audit checks whether what the brief carries survives everything after it.

## 1. Chain at a glance

```
1a research ──► 1b/1c brief ──► 2a PRD ──► 2b design ──► 2c reconcile ──► 3a roadmap ──► 3b slices ──► 3c sprint ──► 3d build ──► 4a verify/ship
docs/research    docs/discovery   docs/prds   docs/design    (edits PRD/      docs/ROADMAP   GitHub issues  milestones   commits     PR + status
<slug>.md        <slug>.md        BT-<p>-*    BT-<p>-iface   design in place)  + milestones   + BACKLOG_MAP                 .tmp/3d-*   + FAA
```

Every artifact from 2a onwards is keyed by the **parent** ID `BT-<p>`. Research and briefs are keyed by **slug**. Slices have their own `BT-<s>`. Most of the gaps below sit at one of these two key changes (slug → BT, parent → slice).

## 2. Producer → consumer map (durable artifacts)

| Artifact | Producer | Sections written | Consumers | What they read |
|---|---|---|---|---|
| Research `docs/research/<slug>.md` | 1a:96 | Gap matrix, Opportunity (ODI + `[HIGH\|MED\|LOW]`), Cost & Viability | 1b:80 · 2a:56,60 · 2c:25 · 3b:53 (auditor only) | 1b: date, then body. 2a: scores and cost, **without a locator**. 2c: whole file. 3b: supplementary input to its auditor |
| Brief `docs/discovery/<slug>.md` | 1b:115 · 1c:73 | Ask, Vocabulary, Actor, Problem, Framing, Prior Art, Non-Goals, Constraints, Open Q, RAT, Next step; `linked-prd:` | 2a:27,46,65 · 2c:25 (**wrong path**) · 2z:20 | 2a: Problem/Vocab/Actor/Framing/Non-Goals → §1/§2/§4/§6/§7; Open Q → §10; RAT → §10/§11. **Constraints is never mapped.** No 3x/4x reader |
| Concept map (issue or `.map.md`) | 1c:36 | Destination, fog, decisions | 1c · 2c:26 | 2c reads "the map the brief cites", but the brief has no field that cites it |
| PRD `docs/prds/BT-<p>-*.md` | 2a:87 (2c edits) | §1–§12, `bt`, `resource` | 2b · 2c · 2z · 3a (§3, §6, §12) · 3b (§6, §8; auditor reads the full file) · 3d/4a (**slice-keyed path**) · FAA (parent-keyed) | 4a/FAA read "PRD AC", but the PRD has **no AC**: per-slice AC are forbidden in the PRD (2a:50) and live in the slice body |
| Design `docs/design/BT-<p>-interface.md` | 2b | surface, states/stress matrix, TTV, Handoff Notes | 2c · 3b (blueprint, TTV, stress) · 3d (**only if "referenced", and nothing writes the reference**) · 4a (UI-block check) | "Handoff Notes for 3c/4a": 3c never reads them |
| Parent epic issue | 2a:30 | summary, PRD/brief/design links, §10 | labels only (status, `type:`) | body links unused by any workflow |
| Roadmap + milestones | 3a | releases, epic milestones | 3a · 3c · 2b:106 · reconcile | 3a reads epic `size`/`Blocked by`, which nothing writes |
| Slice issues | 3b:69 | Overview, ICE, Current state, Path, AC, Dependencies; labels; sub-issue + blocked-by | 3c · 3d · 3z · 4a | AC, labels, relations. Build slices get **no `--milestone`** (unc.) |
| `.tmp/3d-plan-BT-<s>.md` | 3d:32 | plan + `## Deviations` | 3z (`plan_path`) · 4a:86 (**deletes it**) | Deviations should go into the PR via `--deviation`, but 4a's command line omits the flag |
| PR `stratos-pr` block | 4a:77 | slices, verdicts, deviations, post_merge | 0b:27 | `post_merge` |
| `.memory/*` | 0b, 1b, 2b, 3b, 3d, 4a | GLOSSARY, LEARNINGS, ARCHITECTURE, DESIGN*, SCHEMA, BACKLOG_MAP | `load-memory` (by task type) · 3d · 4a · 2a/2b/2c | stable; not a gap source |

## 3. 3b: is its input sufficient for slice proposals?

**What 3b reads today:**
- PRD §6 and §8 plus the frozen design (3b:25) for drafting.
- Memory `[[A/DR]]` IDs for citations.
- The auditor additionally reads the full PRD (§4/§9/§10 used in resolution) and the research file.
- `load-memory` adds BACKLOG_MAP and LEARNINGS.

**Verdict:** the slicing and audit loop is solid: breadth/depth audit, precedence rule, pre-mint guard, minimum-slice floor. The **inputs** are not sufficient. Six gaps:

| # | Gap | Evidence | Effect |
|---|---|---|---|
| 3b-1 | The discovery brief is never read. After BT-164, file-level facts (call sites, runtime realities) reach the PRD only as path-free §7 text | 3b:25,53; plan D1 | Slice "Current state / Problem" is re-investigated by 3d, or missed |
| 3b-2 | **Existing siblings are not read.** No `subIssues` / BACKLOG `Parent=` check before slicing | 3b:22-57 | Re-runs, expand mode, or an FAA "new slice" route can duplicate or overlap shipped slices |
| 3b-3 | §7 (the only home for ADRs and architecture, 2a:49) and §10 (open questions) are not named for drafting; §10 appears only in audit resolution | 3b:25,52 vs 2a:49 | Constraints reach the drafts only if the auditor catches them; blockers turn into Spikes late |
| 3b-4 | No design link is written into the slice body, yet 3d reads the design only "if referenced" | 3d:21-23; issue-templates.md:31-63 | 3d can skip the frozen blueprint |
| 3b-5 | ODI confidence map uses `[MEDIUM]`; 1a and the PRD template emit `[MED]` | 3b:45; 1a:64; PRD-template.md:69 | `MED` stories hit the "ODI absent" HALT, or are mis-mapped |
| 3b-6 | 2c "pre-Slice-1 migration" records have no PRD home and no 3b reader. Research `<slug>` is undefined for 3b/2c because the PRD carries no slug | 2c:34,62; 3b:53 | Migrations dropped; research may never be found |

## 4. 4a: what it consumes

**Slice audit (Phase 2):**
- The business-logic auditor gets "Issue/PRD (`docs/prds/BT-<padded>-…`)", design, tests/implementation, LEARNINGS and the confidence scale.
- The standards auditor gets the scoped diff and the smell baseline.
- **FAA (Step 8):** parent PRD "full AC set", design, and the whole-feature diff.
- **Ship:** `pr_body.py` (suite record, prior body), BACKLOG, `subIssues`.

| # | Gap | Evidence | Effect |
|---|---|---|---|
| 4a-1 | **The AC source is mislabelled.** The auditor's named input is the PRD, but slice AC live in the slice issue body (the PRD forbids AC) | 4a:36,46; 2a:50 | The auditor may audit against §6 stories instead of the minted AC |
| 4a-2 | **PRD/design paths use the slice ID.** `<padded>` in 4a/3d/3z is the slice; the docs are keyed by the parent (the FAA uses `parentPadded` correctly) | 4a:36; 3d:22; 3z:60 vs FAA:19 | The path does not resolve, so the auditor works without spec context |
| 4a-3 | Deviations and manual-QA are dropped: the step 5 command omits `--deviation`/`--manual-qa`, then step 10 deletes the plan "because deviations are in the PR" | 4a:77,86; pr-body-and-ship.md:23,33 | The PR body loses the 3d deviations; the auditor also never sees them, so intentional deviations get re-flagged |
| 4a-4 | FAA reads the "PRD full AC set"; the PRD has §8 DoD and §5 Success Signals, not "AC" | FAA:19; PRD-template | Ambiguous scope. After BT-164, brief Success State → §5/§8, so the FAA must name those sections to close the 1b→4a loop |
| 4a-5 | **Standing epics are not modelled.** Epic Check, `--close-parent`, FAA and the draft rule all assume a feature epic. Today only Claude-side memory guards this, which is invisible to Antigravity | 4a:83-85; 3d:20-21 | The draft rule keeps a standing-epic PR draft forever, and the FAA runs without a PRD. Affects PR #161 now |
| 4a-6 | Release bump is "once per PR"; for a multi-slice, one-release PR the earlier bump goes stale (`release.py` re-derives from the last tag, so a rerun is safe) | 4a:74; scripts/release.py:88-115 | The version understates the PR's artifact bumps |

## 5. Gap → recommendation map

**Priority:** P1 means information is lost or an input is unresolvable on the main path; P2 means degraded or ambiguous; P3 is hygiene.
**Home:** where the fix belongs. **164/165** = extend those slices in PR #161. **New-A/B** = proposed new slices (§6).

| ID | P | Gap | Recommendation | Home |
|---|---|---|---|---|
| L1 | P1 | 2c cannot find the brief (slug vs `BT-` glob) | One locator rule (`linked-prd:` frontmatter, then slug fuzzy-match) | 165 |
| L2 | P1 | Research and brief have no deterministic link to the PRD; 2a/2c/3b glob with undefined `<slug>` | 2a writes PRD frontmatter `discovery:` and `research:` (paths, or `—`) when it locates them; 2c/2z/3b/4a read those fields instead of globbing. With `linked-prd:` this makes the link bidirectional | 165 |
| L3 | P1 | 3d/4a/3z build PRD/design paths from the slice ID | Resolve `BT-<parentPadded>` via the slice's `Parent` and read the PRD frontmatter-linked docs | 165 |
| L4 | P1 | Brief facts and decisions never reach slices (3b-1) | 3b Phase 1 loads the linked brief. The drafter seeds slice "Current state / Problem" from Established Facts (paths allowed in issue bodies). The auditor reads it too. Precedence: PRD > design > brief > research | 164 |
| L5 | P2 | Brief Constraints never mapped; RAT `running`/`failed` unhandled; 2a's "validated" is not a status value | Already C4 for Constraints. 2a RAT: `untested\|running\|failed` → §10 blocking, `survived` → §11 | 164 |
| L6 | P2 | 2c expects the brief to cite the concept map; no field does | Brief frontmatter `concept-map: #<n> \| —`, written by 1c | 164 |
| S1 | P1 | 3b ignores existing sibling slices (3b-2) | Phase 1 reads `gh issue view <parent> --json subIssues` plus BACKLOG `Parent=` rows. Drafts cover only uncovered §6/§8 items. The auditor counts existing slices as covering | New-A |
| S2 | P2 | §7/§10 not explicit in drafting (3b-3); hand-off line ≠ body | Scope = §1, §6, §7, §8 plus §10 (open blocking question → Spike up front); align the 2a/3b hand-off lines | New-A |
| S3 | P2 | No design link in the slice body (3b-4) | Build template `Dependencies` gains `Design: docs/design/BT-<p>-interface.md \| —`; 3d keys its conditional read on it | New-A |
| S4 | P2 | `[MED]` vs `[MEDIUM]` (3b-5) | 3b maps `[MED]` (accept `[MEDIUM]` as legacy) | New-A |
| S5 | P3 | 2c migration records have no home or reader (3b-6) | 2c writes them as PRD §10 items tagged `migration:`; 3b mints them as Slice 1 | New-A |
| S6 | P3 | Build slices minted without `--milestone` (unc.) | Verify against `reconcile.py`; if confirmed, pass `--milestone` | New-A |
| V1 | P1 | AC source mislabelled (4a-1) | Auditor input = slice issue body AC (primary) + parent PRD §6/§7/§8 + design. Rename the table to "Slice AC" | New-A |
| V2 | P1 | Deviations/manual-QA dropped (4a-3) | Put `--deviation`/`--manual-qa` in the step 5 command; pass the plan's `## Deviations` to the auditor; delete the plan only after the body is built | New-A |
| V3 | P2 | FAA reads "AC" the PRD doesn't have (4a-4) | FAA scope = §8 DoD + §5 Success Signals + `[BASELINE]`/`[DIFFERENTIATOR]` §6 stories | New-A |
| V4 | P1 | Standing epics not modelled (4a-5) | Deterministic rule: a parent with no PRD that is not an audit epic counts as **standing**. Then: no epic promotion (3d), branch keyed to the slice, no `--close-parent`, no FAA, and the draft rule ignores it | New-B |
| V5 | P2 | Release "once per PR" (4a-6) | Rerun `release.py` at every ship (idempotent against the last tag); commit only if the output changed | New-B |
| H1 | P3 | 3a reads epic `size`/`Blocked by` that nothing writes; milestones never closed, so `[SHIPPED]` has no input | Decide whether 3a owns epic sizing and milestone close | backlog |
| H2 | P3 | Hand-off contract lines drift from bodies (1a, 1b, 2a, 2b, 2c, 3a, 3b, 3c, 4a) | Make each hand-off line point to its consumer's section instead of restating it; extend the C5 contract-test pattern | backlog |
| H3 | P3 | Orphans: `directions.html`; design "Handoff Notes for 3c/4a" (should say 3d); blank `description:` in all templates; 1c GLOSSARY entries without `Avoid:`; 1c briefs stamped `generated.by: 1b` | One hygiene slice | backlog |
| H4 | P3 | 3z reports `plan_path` after 4a deleted the file | Report deviations inline instead of the path | backlog |

## 6. Slicing (decided 2026-10-13)

| Slice | Gaps | Plan items |
|---|---|---|
| BT-164 (extended) | L4, L5, L6; H3 (1c `Avoid:`, brief provenance, design handoff heading) | C9–C11, C14–C16 |
| BT-165 (extended: deterministic artifact links) | L1, L2, L3 | C6–C8, C12–C13 |
| BT-166 (3b/4a input contract) | S1–S6, V1–V3, H4 | A1–A9 |
| BT-167 (standing epics + release rerun) | V4, V5 | B1–B3 |
| BT-168 (backlog, under BT-116, `status:needs_spec`) | H1, H2 (rest), H3 (`directions.html`, blank `description:`) | — |

Implementation detail lives in [`1b-discovery-brief-sections-plan.md`](1b-discovery-brief-sections-plan.md). All four slices ship in PR #161 as one release.
