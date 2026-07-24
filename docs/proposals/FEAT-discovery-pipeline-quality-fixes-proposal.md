---
name: discovery-pipeline-quality-fixes-proposal
description: Three quality fixes to the discovery→design pipeline (1b grill depth, 1b→2a handover fidelity, 2b full-stack path coverage), benchmarked against Matt Pocock's current skills.
type: proposal
trigger: User. Do not run autonomously.
version: "1.0.0"
timestamp: 2026-07-24
---

# Workflow Proposal: discovery-pipeline quality fixes (1b / 2a / 2b)

**Status:** Open proposal. Not implemented. Self-contained — pick up in any session (incl. mobile / claude.ai/code).
**Origin:** Session review of three workflow-quality questions, benchmarked against Matt Pocock's current skills (`/grilling`, `/wayfinder`, `/to-spec`, `/handoff`) via web research on `github.com/mattpocock/skills` + `aihero.dev`. Prior lineage record: [`docs/research/archive/v1-1-learnings-and-concept-framing-exploration.md`](../research/archive/v1-1-learnings-and-concept-framing-exploration.md).
**Scope:** Edits to StratOS's OWN workflow source under `src/workflows/`; governed by the `improve-workflows-skills` discipline (per-file OKF version bump once per PR; rebuild `dist/` after edits). NOT product code.

> **Suggested next skills/workflows:** `improve-workflows-skills` (authoring discipline) → edit `src/workflows/*` → build to refresh `dist/` → `4a_verify-and-ship` to open the PR. Do NOT hand-edit `dist/` or `.agents/` (build outputs).

---

## Recommended sequencing (lowest-risk first)

1. **Q3 — 1b→2a handover fidelity** (additive read/link steps; touches only 2a). Safest.
2. **Q2 — 1b grill stop-conditions** (wording/gate change; touches only 1b).
3. **Q1 — 2b full-stack path coverage** (touches downstream readers 3b / 3d / 4a). Highest blast radius; do last.

Each is independent and can ship as its own commit on one branch, or as three separate PRs.

---

## Q1 — 2b covers UI *or* non-UI, never both (full-stack gap)

**Finding:** The [`src/workflows/2b_interface-design.md`](../../src/workflows/2b_interface-design.md) Phase 1 gate is mutually exclusive: no-UI → Path C; UI → Path A/B. Three things lock it to a single path:
- Phase 2.2 assigns the doc ONE `type` (`ui-generator-*` | `ui-manual` | `non-ui`).
- Phase 4 runs exactly one of the Path A / B / C sub-sections.
- The API/schema/seam contract exists ONLY in Path C step 1.

So a genuinely full-stack slice (new screen **+** new API/schema/adapter seam) gets its UI frozen and its backend contract never designed at 2b — it falls through to 3d improvisation. This collides with the framework's own vertical-slice philosophy. It is a gap, not a documented decision.

**Recommended fix (smallest reversible):** do not add a 4th path. Make Path C's contract block *additive* to the UI paths. Add one step to Paths A and B: *"If this feature introduces a new non-UI contract (API/schema/seam) not already covered, also produce a `## Interface Contract` block per Path C step 1."* One doc, both faces.
- Optional: widen the Phase 1 gate to detect a `hybrid` classification so the composite is deliberate.
- Watch: downstream readers (3b, 3d Phase 0, 4a) must tolerate a doc that carries both a UI blueprint block AND an Interface Contract block — verify each reads the sections it needs rather than assuming a single path type.

## Q2 — 1b stops grilling too early (contradicts its role model)

**Finding:** [`src/workflows/1b_concept-framing.md`](../../src/workflows/1b_concept-framing.md) Phase 2 stop conditions bias toward premature completion, diverging from Matt Pocock's current `/grilling` loop (its acknowledged role model).

| | Pocock `/grilling` (current) | StratOS 1b today |
|---|---|---|
| Primary stop | **Confirmed shared understanding** (positive gate; "won't act until you confirm") | Coverage checkboxes + "next Q wouldn't change the brief" |
| Question budget | **None by design** — "fifty questions… or three"; walks the full decision tree | "Focus areas covered at **minimum depth**" |
| Typical session | ~45 min, has asked 50+ questions before writing | 5-question check-in offering an off-ramp |

Sources: `aihero.dev/my-grill-me-skill-has-gone-viral`, `github.com/mattpocock/skills/releases/tag/v1.1.0`, `aihero.dev/skills-wayfinder`. v1.1 added exactly two sharpening changes to his loop — a **confirmation gate** and a **facts-vs-decisions split** (StratOS already has the split in G2 — keep it).

**Recommended fixes (in impact order):**
1. **Make the confirmation gate the primary stop condition**, not coverage. Replace "minimum depth" with: *"Stop only when you can restate actor, problem, and framing back to the user and they confirm the shared understanding is correct and complete."*
2. **Delete stop-condition 2** ("next question would not change the brief") or subordinate it to the user gate — the user, not the agent, declares "enough" (prevents the agent answering its own questions).
3. **Reframe the 5-question check-in** from an off-ramp (*"or do I have enough?"*) to a direction check: *"Here's what's still fuzzy: [X, Y]. Keep drilling these, or are they intentionally open?"*
4. **State the "no fixed budget" norm explicitly** (à la `/wayfinder`'s "halt when the fog is pushed back"): e.g. *"A thorough grill is 20–50 questions; do not target brevity."*

Already ahead of the role model: V1/V2/V3 vocabulary stress-tests ≈ his `/grill-with-docs` ubiquitous-language pinning. Keep.

## Q3 — 1b→2a handover loses information (main leak)

**Finding:** Pocock's `grilling → to-spec` passes NO artifact — `to-spec` reuses the live in-session conversation. StratOS deliberately does the harder cross-session thing (durable `docs/discovery/<slug>.md`), which is correct for its architecture but inherits his `/handoff` principle: **"reference, don't duplicate; external artifacts are the source of truth."** Measured against that, four leaks:

1. **Contract declared in 1b, not honored in 2a (main leak).** [`1b`](../../src/workflows/1b_concept-framing.md) hand-off contract says 2a reads Vocabulary/Actor/Problem/Framing/Non-Goals. But [`2a`](../../src/workflows/2a_write-prd.md) reads the brief in ONE place only — the RAT carry-over. Phase 3 synthesizes "from **conversation**, BACKLOG_MAP, LEARNINGS, ADR" — the brief is not a named structural input. So the handoff silently depends on the conversation still being alive.
2. **No forward pointer.** 2a detects mode from *PRD existence*, never locates `docs/discovery/<slug>.md` by slug. A brief from a prior session may never be opened.
3. **Broken bidirectional link.** Brief carries `linked-prd: —`; 2a never writes the minted `BT-<n>` back, and never records the brief path in the PRD/issue.
4. **Open Questions can evaporate.** 1b writes brief Open Questions "for 2a §10"; 2a's §10 handling only moves 2a's own `> open:` markers. Ingesting the brief's Open Questions is nobody's explicit step.

Sources: `aihero.dev/skills-to-spec` ("does not interview you again… synthesises what is already known"), `aihero.dev/skills-handoff` ("referenced by path or URL, never copied").

**Recommended fixes:**
1. **Move ingestion into 2a and make it structural.** Add a Phase-3 sub-step: *"If `docs/discovery/<slug>.md` exists, read it and seed §1/§2/§4/§6/§7 from Vocabulary/Actor/Problem/Framing/Non-Goals; absorb its Open Questions into §10."* Enforce the contract on the consuming side.
2. **Give 2a a brief-locator step** (Phase 1): derive slug, fuzzy-match `docs/discovery/*.md`, read before drafting (same pattern 1b uses for research files).
3. **Close the link at mint time** (Phase 2, after `gh issue create`): write `BT-<padded>` into the brief `linked-prd:` and add the brief path to PRD frontmatter/issue body.
4. **Keep the distillation** — 1b's Synthesis Contract (distilled nuggets, no transcripts, work-file deleted) matches "only settled decisions survive." Don't change; just ensure what survives is actually read downstream.

---

## Decisions still open (for the phone session)

- [ ] Which fix(es) to implement, and one PR or three?
- [ ] Q1: additive `## Interface Contract` step only, or also add the `hybrid` gate classification?
- [ ] Q2: full rewrite of Phase 2 stop conditions, or minimal (fixes 1–2 only)?
- [ ] Confirm build/dist rebuild + `4a_verify-and-ship` is the intended ship path.

## Resume instructions

1. Open this repo in claude.ai/code or the Claude mobile app (branch: `fix/post-v3-polish`, or cut a fresh `feat/BT-…` branch).
2. Say: *"Implement the Q3 fixes from `docs/proposals/FEAT-discovery-pipeline-quality-fixes-proposal.md`"* (or Q2 / Q1).
3. Edit `src/workflows/*` (never `dist/` or `.agents/`), bump each touched file's OKF `version` once, rebuild `dist/`, then `/4a_verify-and-ship`.
