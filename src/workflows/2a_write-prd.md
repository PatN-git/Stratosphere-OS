---
name: 2a_write-prd
description: Turn project ideas into impactful PRDs.
type: workflow HITL
trigger: manual
version: "1.2.0"
timestamp: 2026-07-17
---

# Write PRD

**Hand-off contract:** `/2b_interface-design` is next (designs interface). `/3b_create-issue` reads §1, §6, §7, §8.

## Phase 0: Load Memory
Run `.agents/skills/load-memory/SKILL.md` to restore session context (read-only).

## Phase 1: Precondition & Mode
1. Ensure `.memory/BACKLOG_MAP.md` is loaded; if Phase 0 skipped it (no active task yet), read it directly.
2. Detect mode from `docs/prds/BT-<n>-<name>.md` existence:
   - **New** — draft from scratch.
   - **Expand** — read file, fill thin sections and `> open:` markers.
3. If feature warrants 2+ PRDs, suggest splitting first.
4. One clarifying question only if blocking. Else → `> open:` into §10.

## Phase 2: Reserve BT-<padded> (Atomic Minting)
Execute `gh issue create` to create parent GitHub issue — capture exact returned issue number `#N` and zero-pad to 3 digits (e.g. `BT-059`).
> [!IMPORTANT]
> **ATOMIC MINTING RULE:** Never predict or guess next issue number by scanning `BACKLOG_MAP.md`. GitHub shares numbering across issues/PRs; local guesses collide. Numeric ID `BT-<padded>` is born strictly at creation time from the return value of `gh issue create`. If offline, use prefix `BT-LOCAL-<slug>` until synced.

- **Title:** clean feature name (no bracket prefix; bracket IDs are sub-issue-only).
- **Labels (apply):** `tier:epic`, `area:<x>` (inferred), `type:feature`, `status:needs_spec`; default priority to `priority:medium` if unknown. Never invent non-registry labels.
- **Labels (never apply):** `size:*`, `mode:*`.
- **Body:** one-line summary + link to `docs/prds/BT-<padded>-<name>.md`.

Record issue URL and minted ID for PRD front matter.

## Phase 3: Draft
Instantiate from `.agents/workflows/.reference/PRD-template.md`. Synthesize from conversation, BACKLOG_MAP, LEARNINGS, and ADR memory entries. Reference BT-xxx, [[L-xxx]], [[A-xxx]], [[DR-xxx]] inline.

**Rules:**
- §7 is the only home for architectural content — ADRs fold in here, no separate ADR files.
- Forbidden: file paths, code, module/interface designs, slice lists, per-slice AC, Data/Logic/UI breakdowns.
- Unknown → `> open: <question>` inline; rolls to §10 at validation.

**Journey Mapping & Scope-Classing (§6):**
- Group stories under chronological journey steps (Jeff Patton Story Mapping). For each step, ask *"What has to be true for the user to get through this step?"* to discover features.
- Assign scope tag (`[BASELINE]`, `[DIFFERENTIATOR]`, or `[DEFERRED]`) and record the ODI score (with its confidence tag) or `ODI: -`.
- If research (`1a`) exists, map scope tags using gap matrix and Opportunity scores. Else mark `[unbacked]` and propose for user confirmation. Never assert "differentiator" without evidence or user sign-off.
- Every `[DEFERRED]` story must be mirrored in §9 Out of Scope.

**Viability, Cost & Ethics (§4, §12):**
- **§12 Viability & Cost:** Summarize and cite `## Cost & Viability Signals` from `1a` research. Do not generate new pricing/market figures. Tag un-cited figures `[unverified estimate — confirm]`; mark missing as `[Unknown]`. Complexity score (1-10) is explicit estimate.
- **Cost Approval Gate:** If architecture generates ongoing costs (e.g. paid APIs, polling infra), surface the exact implications and get explicit user approval before locking into PRD.
- **Ethical & Dark Patterns:** Document anti-dark-pattern exclusions in §4 Non-Goals. Put profit-alignment in §12. Do not mix them: §4 is for principled exclusions; vendor lock-in is a §7 constraint / §12 viability concern.

**RAT Carry-Over:**
- Read `## Riskiest Assumption` from discovery brief (`1b`). If untested, carry to §10 as blocking; if validated, place in §11.

**§7 ADR flag:** if §7 contains structural decisions with alternatives, ask to flag: propose [[A-xxx]] for `[LAW]` structural decisions; [[L-xxx]] for `[PATTERN]` or `[ASSUMED]`.

## Phase 4: Validate

- [ ] §1 answers current experience / who / impact
- [ ] §3 goals are outcome-oriented, not solution-prescriptive
- [ ] §4 has ≥ 3 non-goals with rationale, including anti-dark-pattern exclusions
- [ ] §6 stories journey-grouped with scope tags; no per-story AC; no slice lists
- [ ] [DEFERRED] stories mirrored in §9
- [ ] §7 free of module designs, paths, code, slice content
- [ ] §8 is feature-level observable end-state (not per-slice)
- [ ] §12 Viability & Cost populated (complexity, cost table, arch warning, money check, profit alignment)
- [ ] Ethical: dark-pattern exclusions in §4; profit-alignment in §12
- [ ] No slice lists anywhere in the doc
- [ ] All memory refs resolve to existing entries
- [ ] `> open:` markers moved to §10
- [ ] §7 ADR flag raised if applicable

## Phase 5: Publish & Sync
1. Write `docs/prds/BT-<padded>-<feature-name>.md`. Prepend OKF `type: prd` per `.agents/rules/okf-protocol.md`. Set frontmatter `bt: BT-<padded>` and editorial `status: approved` (the PRD passed Phase 4 validation; editorial status is `draft` only while unvalidated). PRD frontmatter never carries a work-status token.
2. **Epic stays `status:needs_spec`.** 2a never promotes it — `/2b_interface-design` owns `needs_spec → planned` (at design freeze for Path A/B/C, or on its no-surface skip path). `3b` has a defensive guard as backstop.
3. **Commit & Push Doc:** `git add docs/prds/BT-<padded>-<feature-name>.md && git commit -m "docs(BT-<padded>): PRD"`, then push to the **default** branch if `gh`/remote is connected (else local commit only). PRDs are cross-feature inputs read by `/3a_version-planning` on default — committing here (not on a feature branch) keeps them visible. Never sweep unrelated drift into this commit.
4. Update parent issue body: summary + doc link + §10 Open Questions.
5. Append to `.memory/BACKLOG_MAP.md` (first real entry: delete dummy row `BT-XXX`) — 9-column schema, Status `needs_spec`, epic carries `Parent = —` and `Blocked by = —`:
   ```
   | BT-<padded> | <Feature name> | needs_spec | area:<x>, tier:epic, type:feature | v1.0.0 | — | — | ICE: - | [[L-xxx]], [[A-xxx]] |
   ```
   Milestone is vMAJOR.MINOR.SPRINT (no leading zeros; `/3a_version-planning` owns MAJOR.MINOR and may reassign, `/3c_sprint-planning` owns the sprint digit). Default to highest vX.Y as vX.Y.0 (provisional), or v1.0.0. Ref is memory IDs only; doc paths go in GitHub body.
6. **Invoke `plan-html` skill:** If PRD is ≥100 lines or has arch decisions, invoke `plan-html` using `plan-document` to render `docs/prds/BT-<padded>-<feature-name>.html`.
7. Tell user: *"PRD `BT-<padded>` ready. Run `/2b_interface-design` to design (Path C covers non-UI interface contracts; only a feature with no external surface skips it)."*

---

## Label Registry
See `.memory/BACKLOG_MAP.md`. Do not invent labels — ask user first if one seems needed.

## Re-run Notes
- Expand mode: never silently overwrite. Surface conflicts.
- `status:done` and archive move (`docs/prds/archive/`) are lifecycle steps outside this skill.