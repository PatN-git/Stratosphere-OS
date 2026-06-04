---
name: 1a_discover-idea
type: workflow
description: Interview the user relentlessly about the idea/problem space to reach shared understanding, lock vocabulary and framing before write-prd. Produces a discovery brief and candidate [[G-xxx]] glossary entries.
---

# SKILL: Discover idea

**Hand-off contract:** The `/Write PRD` workflow reads the brief's Vocabulary, Actor, Problem, Chosen Framing, and Non-Goals to seed PRD §1, §2, §4, §6, §7. The `/Write PRD` workflow warns if no brief exists and its §10 Open Questions are high.

---

## Phase 1: Precondition & Frame

1. Confirm `.memory/BACKLOG_MAP.md` is loaded — else stop and prompt `/0a_start-session`.
2. Read `.memory/GLOSSARY.md` — load existing [[G-xxx]] entries to avoid re-defining settled terms.
3. Capture the raw ask verbatim. Restate in one sentence. If it describes multiple independent problems, flag scope now: *"This sounds like N problems. Which one are we grilling?"* Do not grill multiple problems in one session.
4. Scan BACKLOG_MAP for related active PRDs or prior briefs. Surface overlaps before grilling.

## Phase 2: Grill

One question at a time. Where Phase 1 context gives you sufficient signal on a focus area, state your synthesis and ask the user to confirm or correct — don't re-ask what you already know. Where signal is insufficient, **lead open-ended** — let the user surface their own framing before you narrow. Follow with MC only to confirm once they've answered freely. Name vagueness explicitly — re-ask until the answer is sharp.

**Stop conditions (first one hit ends grilling):**
1. User signals done: "enough", "write it up", or equivalent.
2. Next question would not change the brief.
3. All focus areas are covered at minimum depth.

**Check-in every ~5 questions:** *"Want to keep grilling, or do I have enough to draft the brief?"*

**Focus areas — probe in order of ambiguity; skip if already clear:**

- **Actor identity** — "users" is not an actor. Push to role, segment, context.
- **Problem shape** — "we need X" is a solution. Push to "what hurts without X, and how often?"
- **Vocabulary** — every domain term that could mean two things gets pinned once.
- **Prior art** — what's been tried? What code already touches this?
- **Success state** — "better" is not a state. Push to an observable change a sceptic would accept.
- **Hard constraints** — what is genuinely fixed vs. assumed fixed?
- **Non-goals (early)** — what is explicitly NOT being asked for?

**Pushback format (name the ambiguity, then narrow):**
- Vague term: open first — *"What do you mean by '[term]'?"* — then narrow: *"So [A] rather than [B]?"*
- Solution disguised as problem: *"That describes a solution. What's the pain if we don't build it?"*
- Vague scope: open — *"Which [noun]?"* — then narrow: *"All of them, or specifically [constraint]?"*

Never accept: vague actor nouns, solution-shaped problem statements, unmeasurable success criteria, undefined domain terms.

## Phase 3: Crystallize Vocabulary

1. Compile agreed definitions from Phase 2 into a 3–8 term list.
2. Present for explicit user approval — one pass.
3. Flag reusable terms for `.memory/GLOSSARY.md`: *"These terms look cross-PRD reusable. Promote to [[G-xxx]]?"* User decides per term. Assign IDs with [GUESS] tag — do not write without confirmation.

## Phase 4: Choose Framing

1. Propose 2–3 distinct problem framings (not solutions). Example: *"UX gap (can't find X) vs. data-integrity issue (X is wrong) vs. process gap (X exists but not surfaced to the right person)."* Each framing implies a different PRD shape — say so.
2. User picks one. Record rejected framings — they show future readers what was considered.
3. If grilling reveals the problem is not PRD-worthy, name the exit ramp:
   - Known bug → *"Recommend `create-issue` Template B directly."*
   - Unknown approach → *"Spike needed. Recommend `create-issue` Template A."*
   - Wrong direction → *"Recommend not building. Closing here."*

## Phase 5: Write Discovery Brief

Instantiate from `.agents/workflows/.reference/discovery_brief_template.md` at `docs/discovery/<slug>.md`.

**Rules:**
- Vocabulary section is mandatory. Every other section may be brief if signal is clear.
- Problem is 2–3 sentences in agreed vocabulary only. No implementation.
- Open Questions = residual ambiguity that `/Write PRD` absorbs into PRD §10.
- No solution content, no module/interface hints, no file paths.

## Phase 6: Self-Review + User Gate

- [ ] Every term in the brief appears in the Vocabulary section
- [ ] Actor is specific (not "users")
- [ ] Problem contains no solution language
- [ ] Chosen Framing notes rejected alternatives
- [ ] Recommended Next Step is explicit
- [ ] No unfiled `> open:` markers

Present the brief: *"Review the discovery brief. Any changes before I hand off?"* Wait for approval. Re-review if changes are requested.

## Phase 7: Hand-off & Memory Sync

1. Write `docs/discovery/<slug>.md`.
2. Write confirmed [[G-xxx]] entries to `.memory/GLOSSARY.md` — only after user confirmation from Phase 3.
3. If a framing decision is reusable across features, propose [[L-xxx]] for `.memory/LEARNINGS.md`. Rare — only if user signals it's a pattern.
4. Tell the user the next step:
   - **/Write PRD** → *"Discovery brief ready at `docs/discovery/<slug>.md`. Run `/Write PRD` to draft the PRD."*
   - **/Create issue Template B** → *"This is a bug. Run `/Create issue` with Template B."*
   - **/Create issue Template A** → *"Spike recommended. Run `/Create issue` with Template A."*
   - **Dropped** → *"Closing here. Brief at `docs/discovery/archive/<slug>.md`."*

---

## Archive Lifecycle

| Outcome | Archives when |
|---|---|
| Led to a PRD | When the linked PRD archives (feature shipped) |
| Exit to bug or spike | When the linked issue closes |
| Dropped | Immediately |

Active: `docs/discovery/<slug>.md` → Archived: `docs/discovery/archive/<slug>.md`

## Notes

- Do not grill multiple problems in one session. Decompose first.
- This skill produces no GitHub issue and no BT-<n>. That is `/Write PRD`'s job.
- Terms already in GLOSSARY.md (loaded in Phase 1) do not need re-definition — cite the existing [[G-xxx]] in the brief.