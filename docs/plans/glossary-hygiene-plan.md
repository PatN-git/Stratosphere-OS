---
type: plan
title: Glossary Hygiene Plan
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-27
version: "1.1.0"
---

# Plan: glossary hygiene (size, content, promotion evidence)

Draft 1 by Opus 5.5; challenged and revised by an independent Opus 5.5 reviewer, 2026-10-27.

Line numbers are from the current tree; re-anchor by text. Review findings F1–F22 were in `.tmp/glossary-plan-challenge.md` (scratch).

## 1. Problem and evidence

| | StratOS `.memory/GLOSSARY.md` | CleanTechHub `.memory/GLOSSARY.md` |
|---|---|---|
| Active entries | 4 | 32 (~8/month since 2026-06-29) |
| Bytes (entries / fixed) | 2,870 (~0.9k / ~2.0k) | 9,886 (7,754 / 2,132) |

1. **Readers pay for writer guidance.** The belongs and does-not-belong lists, the preservation rule, the `Avoid:` footnote and the grouping note are for writers only. Readers still load them: `load-memory:19`, `1b:36`, `3d:59-60`.
2. **Entries carry implementation detail.** This breaks the template's own exclusion list and Pocock's "a glossary and nothing else". CleanTechHub examples:
   - G-022: `/api/submit`, centroid maths
   - G-030: table name, TTL
   - G-032: `calculateBatchSchedule`, `min(companyCount, 50)`
   - G-016–G-018
   - G-028/G-029: field lists
   - G-003 is tooling, not domain.
3. **`Occurrences:` duplicates derivable data.** memory-protocol §1 records *who/when* promoted (frontmatter `verified:`), but not *which tasks* count as evidence. The agents filled that gap inside the entry: 0b in `9c1edf8` (G-028/G-029), 0d in `e327a3f` (G-030–G-032).
   - **The snapshot has already diverged from BACKLOG_MAP `Ref`:**
     - G-028 lists 2 tasks; `Ref` has 8.
     - G-029 lists 2; `Ref` has 7.
     - G-032 is missing BT-259.
     - G-030 lists BT-070, which no `Ref` cites.
   - **Nothing reads it afterwards:** glossary entries never reach `[LAW]` (`0d:37`).
   - **0d had already recorded the same evidence** in its report (`nightly-2026-10-21.md:72-74`).
   - **`9c1edf8` also rewrote G-028/G-029 `Source:`** from the discovery brief to BT-234, which loses provenance.
4. **`Avoid:` rules contradict each other.** The template says `Avoid:` is optional (`GLOSSARY.md:38`). 1b and 1c write "each with its `Avoid:` list" (`1b:150`, `1c:89`), and the harness fails a 1b term without one (`assertions.py:240`).
5. **No split rule.** The template's `## Domain:` note uses H2, which closes `## Active Entries`.

## 2. Decisions

- **D1. One glossary file per project; no split.** Pocock and DDD split by bounded context (one word, two meanings), never by length. 3d's Avoid-drift check, 1b's V3 conflict check and the global `G-xxx` ID space all need the whole vocabulary. Multi-file support is built only when D4 step 3 fires.
- **D2. `Occurrences:` is not adopted and is removed where it exists.** Evidence is *derived*: the distinct tasks whose `Ref` cites the ID (local: BACKLOG_MAP `Ref` cell; github: the issue body's `Refs:` line, `tracker-verbs.md:32`). Who and when stays in the frontmatter `verified:` list (memory-protocol §1). The task list is named in the 0d report, or in the promotion commit message when 0d is not the promoter. It never goes in the entry.
- **D3. The template holds entries plus a 2-sentence header.** Writer rules move to one shared reference cited by every writer: 1b, 1c, 0b and setup. The header keeps the two most-violated rules (vocabulary only; project-specific terms only), so ad-hoc writers still see them.
- **D4. Growth path:**
  1. Flat list.
  2. `### <area>` groups under `## Active Entries` once natural clusters emerge (no count, no lint).
  3. Per-context files plus `GLOSSARY-MAP.md`, only when a term needs two meanings in two areas, recorded as an `[[A-xxx]]` decision.

## 3. Work items (StratOS, one slice)

### W1. Shared writer reference: new `src/references/glossary-entry-rules.md`

Contents:
- **Format.** One line: `- **[[G-xxx]] [TAG] [date]** Term: definition. Avoid: … Source: …`. `Avoid:` and `Source:` are the only fields.
- **Definition.** One or two sentences on what the term IS in the domain. No code identifiers, paths, table or column names, formulas, thresholds or TTLs. Those go to `ARCHITECTURE.md` or `DATABASE_SCHEMA.md`, and the entry cites the `[[A-xxx]]`.
- **Belongs / does not belong.** Moved from the current block.
- **`Avoid:`.** Required when synonyms were rejected (always the case in 1b and 1c); omitted otherwise. For the never-bracketed rule, point to memory-protocol §2 instead of restating it.
- **`Source:`.** Never rewritten on promotion.
- **Growth path.** D4, one bullet.

Fan-out: citing `references/glossary-entry-rules.md` in a workflow or command body copies the file into that skill (`build/build.py:152-201`). No manifest entry is needed.

### W2. Slim the template: `src/memory-templates/GLOSSARY.md`

- **Block → two sentences:**
  - "Shared domain vocabulary: one `[[G-xxx]]` entry per project-specific term, with a trust tag (`.agents/rules/memory-protocol.md`)."
  - "Vocabulary only: no code identifiers, file paths, table/column names, formulas or thresholds (→ `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`). Writers follow `references/glossary-entry-rules.md`."

  The header must not contain the literal `Avoid:`, or the harness check stays vacuous (F10).
- **Remove** the preservation line, the grouping note and the `Avoid:` footnote.
- **Keep** both headings, "Read only when explicitly asked", and one placeholder line each under Active and Superseded.
- **Target:** ≤ 1,000 bytes for the whole file (from 2,128; a probe measured 946).
- **Version:** minor bump; set the block's `v=` to match.
- **Existing projects:** `scaffold --update` swaps a pristine block and leaves everything outside it alone (`scaffold.py:1059-1063, 1146-1152`). Lines outside the block are cleaned by hand (W7). No migration script.

### W3. Point the writers at the reference (patch bumps)

- **1b:101:** "checking GLOSSARY.md's inclusion/exclusion lists" → "per `references/glossary-entry-rules.md`".
- **1b:150:** "G-001 placeholder" → "`G-XXX` placeholder".
- **1c:89 and 0b:36:** add "per `references/glossary-entry-rules.md`".
- **Setup Checkpoint 5.1 (`stratosphere-setup/SKILL.md:211`):**
  - Step 2: write entries "per `references/glossary-entry-rules.md`".
  - Step 4: replace the quoted, now-deleted lines with "keep the header block and the `## Superseded` example line".
- **0d:38:** "`[ASSUMED]` cited by ≥2 distinct tasks" → "`[ASSUMED]` cited in `Ref` by ≥2 distinct tasks".

### W4. Promotion rule: `src/rules/memory-protocol.md` (always_on)

- **§1, edit in place.** Change "cite ≥2 occurrences across distinct tasks" to "≥2 distinct tasks whose `Ref` cites the ID; name them in the 0d report or promotion commit, never in the entry".
- **§7:** drop "`Avoid:` instructions" from the protected-guidance example.
- **Budget:** `tests/framework/test_contract_s6.py:44` (≤ 6,149 chars; now 5,910). Net change about +40.
- **Version:** minor bump.

### W5. Validator warning: `src/scripts/validate_memory.py`

- **Check.** In the GLOSSARY branch (`:561`), scan each non-placeholder active G entry's `content` for `\.\s+([A-Z][a-z]+):\s`. A field other than `Avoid` or `Source` produces this warning: "unknown field `<X>:` in G-xxx; glossary entries carry only Avoid:/Source: (promotion evidence is derived from Ref)". It is a warning only.
- **Tests.** One test that `Occurrences:` warns, and one test that a clean entry with `Avoid:` and `Source:` does not.
- **Fresh scaffold.** It stays exit 0 (`test_fresh_scaffold_lint.py:21`).
- **Not built:** length and group-count warnings. The length warning would fire on 0 of 36 real entries at 300 chars, and on good entries at lower limits. A group-count warning nags every 0b and fails the harness `check_0b` on exit 2.

### W6. Verification

- **Build and tests:** `python build/build.py`, then `build/validate.py` and the full `pytest`.
- **Template size:** the built template is ≤ 1,000 bytes.
- **Prune diff gate:** run the playbook §4 post-prune diff gate on the template diff. Every removed span must land in W1 or be a named no-op or duplicate.
- **Real-data check:** run the validator on a `.tmp/` copy of CleanTechHub `.memory/`. Expect exactly 5 W5a warnings (G-028–G-032) and no new warning on StratOS `.memory/`. Record both in the PR.

### Delivery

- **Slice:** one standalone `improvement` slice minted via 3b. The plan is already reviewed, so skip the ICE prompts.
- **Branch:** `improvement/BT-<n>-glossary-hygiene`, created by 3d. Not on `improvement/BT-194-*`.
- **Version bumps:** once per PR per changed file.

## 4. CleanTechHub follow-up (separate repo and session, after the StratOS release)

### W7. One-off cleanup

Proposal first; write only on confirmation (memory-protocol §5).

1. Run `scaffold --update`; the block is pristine, its hash matches the lock. Then hand-delete the outside-block grouping note and `Avoid:` footnote.
2. Remove `Occurrences:` from G-028–G-032. Restore G-028/G-029 `Source:` to the discovery brief.
3. Trim definitions to their domain meaning. Move implementation facts to `ARCHITECTURE.md` or `DATABASE_SCHEMA.md` where they are not already there, and cite `[[A-xxx]]`. Check the existing ones first: G-017 already cites A-012 and G-028 cites A-014.
   - A trim is an in-place edit.
   - A change of meaning is a supersession (§3).
4. G-012: move "candidate, active candidate" into `Avoid:`.
5. G-003 (tooling): supersede it with a `[REMOVED]` tombstone pointing to A-008, or keep it if the user wants it.
6. Optional: `### <area>` groups under `## Active Entries`.

Success: entry bytes at least 30% lower than 7,754, and the validator shows no W5a warnings.

## 5. Deferred

- Multi-file glossary and `GLOSSARY-MAP.md` (until D4 step 3).
- Have 3d's Avoid-drift check read only the `Avoid:` lines instead of the whole file. This is the cheapest read saving once the glossary grows.
- Domain-scoped partial reads in `load-memory` (revisit at ~80 entries).
- A `Ref` counter script for 0d. **UNVERIFIED:** whether GitHub issue search matches `G-028` inside `[[G-028]]`.
- 0d's 7-day `[ASSUMED]` removal rule applied to vocabulary (`0d:39`). It pushed G-030–G-032 into promotion on day 7. This needs a separate decision.
- LEARNINGS guidance moved the same way.

## 6. Success criteria

1. The template file is ≤ 1,000 bytes, and the post-prune diff gate accounts for every removed span.
2. No StratOS file defines `Occurrences:`. memory-protocol §1 names where promotion evidence comes from and where it is recorded.
3. All writers (1b, 1c, 0b, setup) cite `glossary-entry-rules.md`, and none quotes deleted template text.
4. The validator warns on unknown glossary fields (tested), and the fresh scaffold stays lint-clean.
5. Build, validate and pytest are green.
