---
name: 2a_write-prd
description: Turn project ideas into impactful PRDs.
type: workflow HITL
trigger: User. Do not run autonomously.
---

# Write PRD

**Hand-off contract:** `/3a_create-issue` reads §1, §6, §7, §8 to drive its Vertical Slice Quiz.

## Phase 1: Precondition & Mode
1. Confirm `.memory/BACKLOG_MAP.md` is loaded — else stop and prompt `/0a_start-session`.
2. Detect mode from `docs/prds/BT-<n>-<name>.md` existence:
   - **New** — draft from scratch
   - **Expand** — read file, fill thin sections and `> open:` markers
3. If feature warrants 2+ PRDs, suggest splitting before writing.
4. One clarifying question only if blocking. Everything else → `> open:` into §10.

## Phase 2: Reserve BT-<n>
Create the parent GitHub issue — its number becomes `BT-<n>`.
- **Title:** clean feature name (no bracket prefix; bracket IDs are sub-issue-only)
- **Labels (apply):** `area:<x>` (inferred from registry), `type:feature`, `status:in progress`; `phase:<x>` and `priority:<x>` only if confidently inferable — else `needs-triage`
- **Labels (never apply):** `size:*`, `type:HITL`, `type:AFK` (slice-level)
- **Body:** one-line summary + forward link to `docs/prds/BT-<n>-<name>.md`

Record issue URL for PRD front matter.

## Phase 3: Draft
Instantiate from `.agents/workflows/.reference/PRD-template.md`. Synthesize from conversation context, BACKLOG_MAP, LEARNINGS, and ADR-shaped memory entries. Reference [[BT-xx]], [[L-xx]], [[A-xx]], [[DR-xx]] inline where they constrain the work.

**Rules:**
- §7 is the only home for architectural content — ADRs fold in here, no separate ADR files
- Forbidden everywhere: file paths, code, module/interface designs, slice lists, per-slice AC, Data/Logic/UI breakdowns
- Unknown → `> open: <question>` inline; rolls to §10 at validation

**§7 ADR flag:** if §7 contains a decision with real alternatives and consequences, ask: *"Flag for memory index?"* Route by trust tier: propose [[A-xxx]] for [LAW]-tier structural decisions; [[L-xxx]] for [PATTERN]- or [GUESS]-tier.

## Phase 4: Validate
- [ ] §1 answers current experience / who / impact
- [ ] §3 goals are outcome-oriented, not solution-prescriptive
- [ ] §4 has ≥ 3 non-goals with rationale
- [ ] §6 in standard format, no per-story AC
- [ ] §7 free of module designs, file paths, code, slice content
- [ ] §8 is feature-level observable end-state (not per-slice)
- [ ] No slice lists anywhere in the doc
- [ ] All memory refs resolve to existing entries
- [ ] All `> open:` markers moved into §10
- [ ] §7 ADR flag raised if applicable

## Phase 5: Publish & Sync
1. Write `docs/prds/BT-<n>-<feature-name>.md`.
2. Update parent issue body: one-paragraph summary + doc link + §10 Open Questions.
3. Append to `.memory/BACKLOG_MAP.md`:
   ```
   | BT-<n> | <Feature name> | in progress | area:<x>, type:feature | <phase or —> | — | docs/prds/BT-<n>-<name>.md, [[L-xx]], [[A-xx]] |
   ```
4. Tell user: *"PRD `BT-<n>` ready. Run `/3a_create-issue` to slice."*

---

## Label Registry
See `.memory/BACKLOG_MAP.md`. Do not invent labels — ask user first if one seems needed.

## Re-run Notes
- Expand mode: never silently overwrite. Surface conflicts and ask.
- `status:done` and archive move (`docs/prds/archive/`) are lifecycle steps outside this skill.