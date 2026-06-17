---
name: 1b_concept-framing
description: Interview the user relentlessly about the idea/problem space to reach shared understanding, lock vocabulary and framing before writing a PRD. Produces a discovery brief and candidate [[G-xxx]] glossary entries.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.0"
updated: 2026-06-17
---

# Concept framing

**Hand-off contract:** The `/2a_write-prd` workflow reads the brief's Vocabulary, Actor, Problem, Chosen Framing, and Non-Goals to seed PRD §1, §2, §4, §6, §7. The `/2a_write-prd` workflow warns if no brief exists and its §10 Open Questions are high.

---

## Phase 0: Brainstorm (Optional)

1. Infer intent from initial prompt:
   - **Sharpen:** concrete concept → skip to Phase 1.
   - **Generate:** vague/exploratory → run the Phase 0 brainstorm steps below.

2. **Extract constraints** (rapid-fire): target user, timeline, tech constraints, hard boundaries. Confirm. If constraints stay fuzzy, load `.agents/workflows/.reference/brainstorm-techniques.md` and use CHAIN.

3. **Check Backlog:** Scan `.memory/BACKLOG_MAP.md` for matching `BT-<n>`. If found and status is not `done`, surface the item (ICE details or `type:NEEDS_SPEC` spike label) and prompt: *"BT-<n> already covers this. Resume it or brainstorm alternative?"* (If resuming, skip steps 4-6 and proceed directly to Phase 1). If status is `done`, surface as prior art but continue brainstorming.

4. **Diverge:** Default path = Multi-Perspective Ideation (PM / Designer / Engineer lenses), 3-5 ideas per lens, presented in one table. Load `.agents/workflows/.reference/brainstorm-techniques.md` only to pick a situational technique from its Selection Guide when the default pass stalls or the user asks to go deeper. Do not run every technique.

5. **Pre-ICE Triage:** Rank top 5 ideas using Impact (1-5, agent) and Confidence (1-5, user). Do not compute or write a combined ICE score (Effort is not yet sized).

6. **Validate:** Ask: *"Is building this the right approach, or would a simpler solution work?"*
   Frame winner: Outcome → Opportunity → Solution → Experiments. Do not enter Phase 1 without approval.

## Phase 1: Precondition & Scope

1. Confirm `.memory/BACKLOG_MAP.md` is loaded — else stop and prompt `/0a_start-session`.
2. Read `.memory/GLOSSARY.md` — load existing [[G-xxx]] entries to avoid re-defining settled terms.
3. Capture the raw ask verbatim. Restate in one sentence. If it describes multiple independent problems, flag scope now: *"This sounds like N problems. Which one are we grilling?"* Do not grill multiple problems in one session.
4. Scan BACKLOG_MAP for related active PRDs or prior briefs. Surface overlaps before grilling.
5. **ODI Routing:** Note that opportunity scoring is optional and reserved for large/greenfield topics; small items start here in `1b` without ODI.
6. **Multi-sided check:** Ask: *"Is this a multi-sided product (e.g. marketplace)?"*
   - If **yes**, read `.agents/workflows/.reference/multi-sided-discovery.md`, append its focus areas to the grill, and have the RAT test both sides (≈10 DMs each). Note that per-side opportunity *scoring* is a `1a` activity, not `1b` — `1b` has no evidence source; it grills and flags the two sides, it does not assign opportunity numbers.
   - If **no**, proceed normally (avoids token bloat for standard apps).
7. **Discovery Work File Scope-Gate:**
   - Use the work file for longer / interruptible grills (the Generate / greenfield path). A short "sharpen-only" session may skip it.
   - If utilizing the work file, delete any stale `docs/discovery/.<slug>.work.md` file for this slug at start-of-run.
   - **Path:** `docs/discovery/.<slug>.work.md` (hidden, ephemeral).
   - **Structure:**
     - `## Coverage (grill axes)`: A checklist seeded with standard axes (Actor, Problem shape, Vocabulary, Internal prior art, External research, Success state, Hard constraints, Non-goals), each with status `[ ]` open / `[~]` in-progress (+ partial nugget) / `[x]` covered at minimum depth (+ nugget) / `[skip]` (+ one-line why). Multi-sided branch appends per-side axes.
     - `## Ask (verbatim)` (captured once), `## Candidate vocabulary (unapproved)`, `## Candidate framings`, `## Chosen framing` (pending until Phase 4).
   - **Loop & Resume:** The top-ranked open axis by current ambiguity drives "which axis next". On restart, read the checklist and continue from the first open/in-progress item. "All axes covered or skipped" is the stop condition.
   - **Write Trigger (Convention 9):** Append distilled state (store distilled nuggets, never transcripts; keep it lean) on a checklist status change or a decision lock. The existing ~5-question check-in is the floor.


## Phase 2: Grill

One question at a time. Where Phase 1 context gives you sufficient signal on a focus area, state your synthesis and ask the user to confirm or correct — don't re-ask what you already know. Where signal is insufficient, **lead open-ended** — let the user surface their own framing before you narrow. Follow with MC only to confirm once they've answered freely. Name vagueness explicitly — re-ask until the answer is sharp. If utilizing the work file, the checklist under `## Coverage (grill axes)` drives the grilling sequence.


**Stop conditions (first one hit ends grilling):**
1. User signals done: "enough", "write it up", or equivalent.
2. Next question would not change the brief.
3. All focus areas are covered at minimum depth.

**Check-in every ~5 questions:** *"Want to keep grilling, or do I have enough to draft the brief?"*

**Focus areas — probe in order of ambiguity; skip if already clear:**

- **Actor identity** — "users" is not an actor. Push to role, segment, context.
- **Problem shape** — "we need X" is a solution. Push to "what hurts without X, and how often?"
- **Vocabulary** — every domain term that could mean two things gets pinned once.
- **Internal Prior Art** — what code already touches this? What has been tried internally?
- **External Research** — derive canonical slug from the restated ask using the same rule as `/1a_research` Phase 1 (kebab-case core problem as 2–5 word noun phrase).
  1. Glob `docs/research/*.md` (filenames only — filenames are slugs, ignoring `*.work.md`). Fuzzy-match against the slug/ask.
  2. Exact or one strong match → Read ONLY that file's frontmatter (specifically the `updated:` date). If updated more than 90 days ago, consider it stale and prompt to refresh. Otherwise, prompt: *"Research at docs/research/<slug>.md (updated <updated>). Still current, or refresh first?"* Read the body only after user confirms; then cite findings and skip the probe.
  3. Zero matches → Run 2-3 question probe; if signal is weak, suggest `/1a_research`.
  4. Multiple matches → List filenames, user selects.
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
3. Flag reusable terms for `.memory/GLOSSARY.md` (checking GLOSSARY.md's inclusion/exclusion lists): *"These terms look cross-PRD reusable. Promote to [[G-xxx]]?"* User decides per term. Assign IDs with [ASSUMED] tag — do not write without confirmation.

## Phase 4: Choose Framing

1. Propose 2–3 distinct problem framings (not solutions). Example: *"UX gap (can't find X) vs. data-integrity issue (X is wrong) vs. process gap (X exists but not surfaced to the right person)."* Each framing implies a different PRD shape — say so.
2. User picks one. Record rejected framings — they show future readers what was considered.
3. If grilling reveals the problem is not PRD-worthy, name the exit ramp:
   - Known bug → *"Recommend `/3a_create-issue` Template B directly."*
   - Unknown approach → *"Spike needed. Recommend `/3a_create-issue` Template A."*
   - Wrong direction → *"Recommend not building. Closing here."*

## Phase 4.5: Riskiest Assumption Test (RAT)
This runs **by default** (it is a gate, not an opt-in). The user may decline the test; if so, record the decline + the untested assumption in the brief. If running AFK, log it as a residual risk rather than skipping silently.

1. **Identify Riskiest Assumption:** Ask: *"What is the single riskiest assumption that, if wrong, makes this entire feature/concept fail?"* For multi-sided products, the assumption is usually "both sides show up".
2. **Determine Cheapest Test:** Propose a test that is extremely fast to set up.
   - **cheapest_test** ∈ {`landing page + waitlist`, `N DMs`, `fake-door button`, `rough mock shown to 5`}.
   - **Setup Time Rule:** If the test takes ~2 weeks to set up, it is a project, not a test — find a cheaper one. For multi-sided products, the test is typically 10 DMs to each side.
3. **Subagent — "Skeptical Challenger":**
   - **Invoke:** Invoke a subagent (using Antigravity's `invoke_subagent` or Claude Code's `Task` tool with the `general-purpose` type).
   - **Input:** Pass inline the chosen framing, the actor, and the problem statement.
   - **Reads:** None required.
   - **Guardrails:** *"Report only; do not write any file."*
   - **Output Contract:** `{ riskiest_assumption, why_fatal, cheapest_test, est_setup_time }`
4. **Present verdict:** Present the subagent's challenge and the proposed cheapest test to the user. Record the result in the brief.


## Phase 5: Write Discovery Brief

Instantiate from `.agents/workflows/.reference/discovery_brief_template.md` at `docs/discovery/<slug>.md`. Prepend OKF frontmatter per `.agents/rules/okf-protocol.md` using `type: discovery-brief`.

**Rules:**
- Vocabulary section is mandatory. Every other section may be brief if signal is clear.
- Problem is 2–3 sentences in agreed vocabulary only. No implementation.
- Open Questions = residual ambiguity that `/2a_write-prd` absorbs into PRD §10.
- No solution content, no module/interface hints, no file paths.
- **Synthesis Contract (Convention 9):** Build the brief from the work file (spine/floor) when used, and enrich from the live transcript (conversation-bound). Approved vocabulary definitions and chosen framings must be captured durably at lock-time, as they cannot be reconstructed after a context loss.


## Phase 6: Self-Review + User Gate

- [ ] Every term in the brief appears in the Vocabulary section
- [ ] Actor is specific (not "users")
- [ ] Problem contains no solution language
- [ ] Chosen Framing notes rejected alternatives
- [ ] Recommended Next Step is explicit
- [ ] Riskiest Assumption and cheapest test documented with status (untested | running | survived | failed)
- [ ] No unfiled Open Questions markers


Present the brief: *"Review the discovery brief. Any changes before I hand off?"* Wait for approval. Re-review if changes are requested.

## Phase 7: Hand-off & Memory Sync

1. Write `docs/discovery/<slug>.md`.
2. Write confirmed [[G-xxx]] entries to `.memory/GLOSSARY.md` — only after user confirmation from Phase 3 (if this is the first real entry, purge the G-001 placeholder).
3. If a framing decision is reusable across features, propose [[L-xxx]] for `.memory/LEARNINGS.md`. Rare — only if user signals it's a pattern.
4. Delete the temporary `docs/discovery/.<slug>.work.md` file (if it exists).
5. Tell the user the next step:
   - **/2a_write-prd** → *"Discovery brief ready at `docs/discovery/<slug>.md`. Run `/2a_write-prd` to draft the PRD."*
   - **/3a_create-issue Template B** → *"This is a bug. Run `/3a_create-issue` with Template B."*
   - **/3a_create-issue Template A** → *"Spike recommended. Run `/3a_create-issue` with Template A."*
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
- This skill produces no GitHub issue and no BT-<n>. That is `/2a_write-prd`'s job.
- Terms already in GLOSSARY.md (loaded in Phase 1) do not need re-definition — cite the existing [[G-xxx]] in the brief.