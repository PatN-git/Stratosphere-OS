---
name: 2a_write-prd
description: Turn project ideas into impactful PRDs.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.0"
updated: 2026-06-17
---

# Write PRD

**Hand-off contract:** `/2b_interface-design` is the next stage (designs the interface from this PRD). `/3a_create-issue` later reads §1, §6, §7, §8 to drive its Vertical Slice Quiz.

## Phase 1: Precondition & Mode
1. Confirm `.memory/BACKLOG_MAP.md` is loaded — else stop and prompt `/0a_start-session`.
2. Detect mode from `docs/prds/BT-<n>-<name>.md` existence:
   - **New** — draft from scratch
   - **Expand** — read file, fill thin sections and `> open:` markers
3. If feature warrants 2+ PRDs, suggest splitting before writing.
4. One clarifying question only if blocking. Everything else → `> open:` into §10.

## Phase 2: Reserve BT-<padded>
Create the parent GitHub issue — its number becomes zero-padded to 3 digits (e.g., #7 becomes `BT-007`).
- **Title:** clean feature name (no bracket prefix; bracket IDs are sub-issue-only)
- **Labels (apply):** `size:large` (parent features are always large), `area:<x>` (inferred from registry), `type:feature`, `status:in progress`; `priority:<x>` only if confidently inferable — else default unknown priority to `priority:medium`; never invent a non-registry label
- **Labels (never apply):** `size:medium`, `size:small`, `type:HITL`, `type:AFK` (slice-level)
- **Body:** one-line summary + forward link to `docs/prds/BT-<padded>-<name>.md`

Record issue URL for PRD front matter.

## Phase 3: Draft
Instantiate from `.agents/workflows/.reference/PRD-template.md`. Synthesize from conversation context, BACKLOG_MAP, LEARNINGS, and ADR-shaped memory entries. Reference BT-xxx, [[L-xxx]], [[A-xxx]], [[DR-xxx]] inline where they constrain the work.

**Rules:**
- §7 is the only home for architectural content — ADRs fold in here, no separate ADR files
- Forbidden everywhere: file paths, code, module/interface designs, slice lists, per-slice AC, Data/Logic/UI breakdowns
- Unknown → `> open: <question>` inline; rolls to §10 at validation

**Journey Mapping & Scope-Classing (§6):**
- Group stories under chronological journey steps (Jeff Patton Story Mapping). For each step, ask *"What has to be true for the user to get through this step?"* to discover features.
- Assign each story a scope tag (`[BASELINE]`, `[DIFFERENTIATOR]`, or `[DEFERRED]`) and record the ODI score (with its confidence tag) or `ODI: -`.
- If research (`1a`) exists, map scope tags using the competitor gap matrix and Opportunity scores. If no research backs a scope tag or score, mark it `[unbacked]` and propose it for explicit user confirmation. Never assert "differentiator" without evidence or user sign-off.
- Every `[DEFERRED]` story must be mirrored in §9 Out of Scope.

**Viability, Cost & Ethics (§4, §12):**
- **§12 Viability & Cost:** Summarize and cite the `## Cost & Viability Signals` from the linked `1a` research. Do **not** generate new pricing or market figures here. Tag any un-cited figure `[unverified estimate — confirm]`; missing values must be marked `[Unknown]`. The complexity score (1-10) is an explicit estimate.
- **Cost Approval Gate:** If the chosen architecture or product direction generates ongoing costs (e.g., paid APIs, polling infrastructure), surface the exact implications and **get explicit user approval before locking it into the PRD**.
- **Ethical & Dark Patterns:** Document any anti-dark-pattern exclusions in §4 Non-Goals (e.g., no hard-to-cancel subscriptions, fake urgency, pre-checked boxes). Put the profit-alignment ("wins vs loses" analysis) in §12. (Do not mix them: §4 is for principled exclusions; vendor lock-in is a §7 constraint / §12 viability concern).

**RAT Carry-Over:**
- Read the `## Riskiest Assumption` from the discovery brief (`1b`). If untested, carry it into §10 as a blocking open question; if validated, place it in §11 as a reference.


**§7 ADR flag:** if §7 contains a decision with real alternatives and consequences, ask: *"Flag for memory index?"* Route by trust tier: propose [[A-xxx]] for [LAW]-tier structural decisions; [[L-xxx]] for [PATTERN]- or [ASSUMED]-tier.

## Phase 4: Validate

- [ ] §1 answers current experience / who / impact
- [ ] §3 goals are outcome-oriented, not solution-prescriptive
- [ ] §4 has ≥ 3 non-goals with rationale, including anti-dark-pattern exclusions
- [ ] §6 stories are journey-grouped; every story carries a scope-class tag; no per-story AC; no slice lists
- [ ] Every [DEFERRED] story is mirrored in §9
- [ ] §7 free of module designs, file paths, code, slice content
- [ ] §8 is feature-level observable end-state (not per-slice)
- [ ] §12 Viability & Cost populated (complexity, cost table, arch warning, money check, profit alignment)
- [ ] Ethical: dark-pattern exclusions in §4; profit-alignment in §12
- [ ] No slice lists anywhere in the doc
- [ ] All memory refs resolve to existing entries
- [ ] All `> open:` markers moved into §10
- [ ] §7 ADR flag raised if applicable


## Phase 5: Publish & Sync
1. Write `docs/prds/BT-<padded>-<feature-name>.md`. Prepend OKF frontmatter per `.agents/rules/okf-protocol.md` using `type: prd`. Set frontmatter status mapping feature-type: UI feature → `ready-for-design` (run `/2b_interface-design`); non-UI/Path C → `ready-for-slicing` (2b optional).
2. Update parent issue body: one-paragraph summary + doc link + §10 Open Questions.
3. Append to `.memory/BACKLOG_MAP.md` (if this is the first real entry, delete the shipped example rows):
   ```
   | BT-<padded> | <Feature name> | in progress | area:<x>, type:feature, size:large | 1.00 | - | ICE: - | [[L-xxx]], [[A-xxx]] |
   ```
   (Note: Use plain ASCII hyphens `-`, not em-dashes `—` in any BACKLOG row text. Milestone defaults to `1.00` instead of `-` for current release. Ref column is for memory IDs only; doc paths go in the GitHub issue body.)
4. Tell user: *"PRD `BT-<padded>` ready. Run `/2b_interface-design` to design."* (Skip prompting for 2b if feature is non-UI/Path C).


---

## Label Registry
See `.memory/BACKLOG_MAP.md`. Do not invent labels — ask user first if one seems needed.

## Re-run Notes
- Expand mode: never silently overwrite. Surface conflicts and ask.
- `status:done` and archive move (`docs/prds/archive/`) are lifecycle steps outside this skill.