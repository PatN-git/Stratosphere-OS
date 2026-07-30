---
name: 1b_concept-framing
description: Grill the user relentlessly about the concept to lock vocabulary, problem statement, and framing before the PRD. Produces a discovery brief and candidate [[G-xxx]] glossary entries.
type: workflow HITL
trigger: manual
version: "1.2.0"
timestamp: 2026-07-30
---

# Concept framing

**Hand-off contract:** `/2a_write-prd` reads brief's Vocabulary, Actor, Problem, Chosen Framing, and Non-Goals to seed PRD §1, §2, §4, §6, §7.

> [!IMPORTANT]
> **STRICT LATE BINDING (SLUG-ONLY RULE):**
> Discovery briefs (`docs/discovery/<slug>.md`) are pre-creation artifacts. **DO NOT** pre-allocate, predict, or attach a numeric `BT-<n>` ID. The file must be named strictly by its semantic slug (`docs/discovery/<slug>.md`). Numeric `BT-<n>` binding occurs downstream in `/2a_write-prd` upon `gh issue create`.

---

## Load Memory (runs first)
Run `.agents/skills/load-memory/SKILL.md` to restore session context (read-only).

## Phase 0: Brainstorm Gate

*Gate: If the concept is already concrete and specific, skip to Phase 1.*
*Gate: If the concept is vague, exploratory, or the user asks for ideas, run the `concept-brainstorm` skill.*

1. Run the `concept-brainstorm` skill (read `.agents/skills/concept-brainstorm/SKILL.md` for instructions).
2. Once the winning idea is validated and approved by the user, proceed to Phase 1.

## Phase 1: Precondition & Scope

1. Ensure `.memory/BACKLOG_MAP.md` is loaded; if the Load Memory step skipped it (no active task yet), read it directly.
2. Read `.memory/GLOSSARY.md` to avoid re-definitions.
3. Capture raw ask verbatim. Restate in one sentence. If multiple independent problems, ask: *"This sounds like N problems. Which one are we grilling?"* Do not grill multiple problems in one session.
4. Scan BACKLOG_MAP for overlaps.
5. Small items start in `1b` without ODI.
6. If complex/foggy, recommend `/1c_concept-map`.
7. **Multi-sided check:** Ask: *"Is this a multi-sided product?"* If yes, read `.agents/workflows/.reference/multi-sided-discovery.md` and append focus areas. RAT tests both sides (10 DMs each). `1b` grills and flags both sides but does not assign per-side opportunity scores — scoring is a `/1a_research` activity (it has the evidence source; `1b` does not).
8. **Discovery Work File:**
   - Use for longer/generate path. Delete stale `docs/discovery/.<slug>.work.md` at start.
   - Path: `docs/discovery/.<slug>.work.md`.
   - Structure: ## Coverage checklist (Actor, Problem, Vocabulary, Prior Art, Research, Success, Constraints, Non-goals) with status [ ]/[~]/[x]/[skip], plus ## Ask (verbatim), ## Candidate vocabulary, and ## Candidate/Chosen framing sections.
   - Resume: continue from first open/in-progress checklist item.
   - Write: update distilled nuggets on checklist change or decision lock (never transcripts; keep it lean). Check-in every 5 questions.

## Phase 2: Grill

State synthesis of known facts and confirm — do not re-grill. Lead open-ended first, then narrow. Re-ask vague points. Use `## Coverage` to drive sequence if using work file.

**Grill mode (facts looked up, decisions asked — batched by dependency):**
- **Facts are never asked (per G2).** Anything discoverable — actor on a brownfield app, existing patterns, constraints in code — is looked up first; dispatch a subagent for anything expensive and don't block on it (only questions downstream of a running lookup wait). Only *decisions* go to the user.
- **Sharpen / short path:** grill one decision at a time.
- **Generate / longer path (work file present):** grill the **frontier** in rounds — every open decision whose prerequisites are settled (`## Coverage` is the settled set), asked as one numbered batch, each with your recommended answer (per G1). A decision waits for a later round only if its answer depends on a sibling still open this round (per G3). Where you can confidently infer an answer (common on brownfield), present it as a batch-confirm — *"here's what I inferred; correct any that are wrong"* — never a silent assumption. Collect → mark settled on `## Coverage` → recompute the frontier → next round.

**G1–G3 grilling guidelines: apply per `.agents/workflows/.reference/grilling-protocol.md`.**

**Stop conditions:**
1. **Primary gate — confirmed shared understanding:** stop only when you can restate actor, problem, and chosen framing back to the user and they confirm it is correct and complete. The user — never the agent — declares "enough"; do not stop merely because the next question "wouldn't change the brief" (that lets the agent answer its own questions).
2. User explicitly signals done ("enough", "write it up").
3. Focus areas covered **and** the confirmation in (1) obtained.

A thorough grill is typically 20–50 questions; do not target brevity. There is no fixed question budget — depth is bounded by shared understanding, not count.

**Check-in every ~5 questions (direction check, not an off-ramp):** *"Here's what's still fuzzy: [X, Y]. Keep drilling these, or are they intentionally open?"*

**Focus areas — probe in order of ambiguity; skip if clear:**
- **Actor identity** — role, segment, context (not "users").
- **Problem shape** — pain without solution (what hurts without X, and how often?).
- **Vocabulary** — pin terms that could mean multiple things; run the V1–V3 checks per `.agents/workflows/.reference/grilling-protocol.md`.
- **Internal Prior Art** — code touching this, or prior attempts.
- **External Research:** derive slug (kebab-case core problem as 2–5 word noun phrase). Fuzzy-match docs/research/*.md (ignore *.work.md). One strong match → read only frontmatter `timestamp:` date; if <90 days old, ask: "Research at docs/research/<slug>.md (updated <timestamp>). Still current, or refresh first?" and read body only after confirmation; if >90 days, treat as stale and prompt to refresh. Zero matches → probe 2-3 questions or suggest /1a_research. Multiple matches → list filenames, user selects.
- **Success state** — observable, measurable outcomes.
- **Hard constraints** — fixed boundaries.
- **Non-goals (early)** — explicit exclusions.

**Pushback format:**
- Vague term: open first — *"What do you mean by '[term]'?"* — then narrow: *"So [A] rather than [B]?"*
- Solution disguised as problem: *"That describes a solution. What's the pain if we don't build it?"*
- Vague scope: open — *"Which [noun]?"* — then narrow: *"All of them, or specifically [constraint]?"*

Never accept: vague actor nouns, solution-shaped problem statements, unmeasurable success criteria, undefined domain terms.

## Phase 3: Crystallize Vocabulary

1. Compile agreed definitions into 3–8 term list.
2. Present for approval.
3. Flag reusable terms for `.memory/GLOSSARY.md` (checking GLOSSARY.md's inclusion/exclusion lists): *"These terms look cross-PRD reusable. Promote to [[G-xxx]]?"* User decides per term; assign IDs with `[ASSUMED]` tag — do not write without confirmation.
4. Record rejected synonyms in `Avoid:` list.

## Phase 4: Choose Framing

1. Propose 2–3 distinct problem framings (not solutions). Example: *"UX gap (can't find X) vs. data-integrity issue (X is wrong) vs. process gap."*
2. User picks one. Record rejected framings.
3. If not PRD-worthy, recommend exit: bug → `/3b_create-issue` Template B; spike → Template A; drop.

## Phase 4.5: Riskiest Assumption Test (RAT)
Runs by default (gate). User may decline; if so, record decline. If AFK, log RAT decline as residual risk rather than skipping.

1. **Identify Riskiest Assumption:** Single assumption that makes concept fail.
2. **Determine Cheapest Test:** Propose fastest test (landing page, waitlist, N DMs, fake-door, mock). Must not take >2 weeks.
3. **Subagent - "Skeptical Challenger":** Invoke a subagent. Input: chosen framing, actor, problem. Guardrail: "Report only; do not write any file." Output: `{ riskiest_assumption, why_fatal, cheapest_test, est_setup_time }`.
4. **Present verdict:** Present challenge and cheapest test to user. Record in brief.

## Phase 5: Write Discovery Brief

Create `docs/discovery/<slug>.md` using `.agents/workflows/.reference/discovery_brief_template.md`. Prepend OKF frontmatter per `.agents/rules/okf-protocol.md` using `type: discovery-brief`.

**Rules:**
- Synthesis Contract: Build brief from work file and live transcript. Capture approved vocabulary and chosen framing durably at lock-time.
- Vocabulary section is mandatory.
- Problem: 2–3 sentences in agreed vocabulary. No implementation.
- Open Questions: residual ambiguity for `/2a_write-prd` §10.
- No solution, modules, interfaces, or file paths.

## Phase 6: Self-Review + User Gate

- [ ] Terms in brief appear in Vocabulary section.
- [ ] Actor is specific (not "users").
- [ ] Problem contains no solution language.
- [ ] Chosen Framing notes rejected alternatives.
- [ ] RAT and cheapest test documented with status (untested|running|survived|failed).
- [ ] Recommended Next Step is explicit.
- [ ] No unfiled Open Questions markers.

Present brief for approval.

## Phase 7: Hand-off & Memory Sync

1. Write `docs/discovery/<slug>.md` using semantic slug; no `BT-<n>`.
2. Write confirmed `[[G-xxx]]` entries to `.memory/GLOSSARY.md` only after user confirmation from Phase 3 (if this is the first real entry, purge the G-001 placeholder), each with its `Avoid:` list. If a newly-recorded synonym is likely already in code, offer a one-time module-scoped search and propose renames (propose-only; user confirms).
3. If framing decision is reusable, propose `[[L-xxx]]` for `.memory/LEARNINGS.md`.
4. If brief is long (≥100 lines), invoke `plan-html` using `plan-document` to render `docs/discovery/<slug>.html`.
5. Delete `docs/discovery/.<slug>.work.md`.
6. Guide user to next step: `/2a_write-prd`, `/3b_create-issue` (Template A/B), or dropped.

---

## Archive Lifecycle
- Lead to PRD → Archive when linked PRD archives.
- Bug/Spike → Archive when issue closes.
- Dropped → Archive immediately.

Active: `docs/discovery/<slug>.md` → Archived: `docs/discovery/archive/<slug>.md` when linked PRD archives.

## Notes
- Do not grill multiple problems. Decompose first.
- This skill produces no GitHub issue or `BT-<n>`.
- Terms already in `GLOSSARY.md` need no re-definition; cite existing `[[G-xxx]]`.