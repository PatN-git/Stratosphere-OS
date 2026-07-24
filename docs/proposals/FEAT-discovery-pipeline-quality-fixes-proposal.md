---
name: discovery-pipeline-quality-fixes-proposal
description: Quality fixes to the discovery→design pipeline (1a/1b/1c/2a/2b) — five audit-verified correctness/protocol defects plus three depth improvements benchmarked against Matt Pocock's current skills.
type: proposal
trigger: User. Do not run autonomously.
version: "1.1.0"
timestamp: 2026-07-24
---

# Workflow Proposal: discovery→design pipeline quality fixes (1a / 1b / 1c / 2a / 2b)

**Status:** Open proposal. Not implemented. Self-contained — pick up in any session (incl. mobile / claude.ai/code).
**Origin:** Two review passes combined —
- **Part A (defects):** a source audit of the Discover phase (`1a`/`1b`/`1c`) that found five correctness/protocol defects, each verified against source `file:line` and cross-checked against the OKF and memory protocols.
- **Part B (depth):** a session review of three workflow-quality questions benchmarked against Matt Pocock's current skills (`/grilling`, `/wayfinder`, `/to-spec`, `/handoff`) via web research on `github.com/mattpocock/skills` + `aihero.dev`. Prior lineage record: [`docs/research/archive/v1-1-learnings-and-concept-framing-exploration.md`](../research/archive/v1-1-learnings-and-concept-framing-exploration.md).

**Scope:** Edits to StratOS's OWN workflow source under `src/workflows/` (and one shared reference under `src/references/`); governed by the `improve-workflows-skills` discipline (per-file OKF version bump once per PR; rebuild `dist/` after edits). NOT product code.

> **Suggested next skills/workflows:** `improve-workflows-skills` (authoring discipline) → edit `src/workflows/*` → build to refresh `dist/` → `4a_verify-and-ship` to open the PR. Do NOT hand-edit `dist/` or `.agents/` (build outputs).
>
> **Line numbers drift** — every edit below is anchored by content; re-confirm the line before touching it.

---

## 0. Summary (all findings)

**Part A — audit-verified defects** (correctness / protocol; mostly surgical one-liners):

| # | Sev | File | One-line |
|---|-----|------|----------|
| F1 | **P1 — correctness** | `1b:73` | Research-freshness gate reads a `updated:` frontmatter field that does not exist; research carries OKF `timestamp:`. |
| F2 | **P2 — protocol drift** | `1c:74` | `1c` convergence writes `GLOSSARY.md` with no user-confirmation step; `memory-protocol` requires one and `1b` enforces it. |
| F3 | **P2 — HITL gap** | `1c:68–76` | `1c` Converge has no self-review + approval gate before it writes the brief and **closes the map issue**; `1b` gates the same deliverable. |
| F4 | P3 — cosmetic | `1a:30` | Confidence tag `[MEDIUM]` is undefined; the file's set is `[HIGH\|MED\|LOW]`. |
| F5 | P3 — minor gap | `1b:103` / template | RAT subagent returns `est_setup_time` and enforces a ≤2-week cap, but the brief template has nowhere to record it. |

**Part B — Pocock-benchmarked depth improvements** (design changes; larger blast radius):

| # | Area | One-line |
|---|------|----------|
| Q3 | `1b`→`2a` handover | Contract declared in `1b` but not honored in `2a`; brief can silently depend on the live conversation. |
| Q2 | `1b` grill depth | Stop conditions bias toward premature completion vs the `/grilling` confirmation-gate model. |
| Q1 | `2b` path coverage | `2b` designs UI *or* non-UI, never both; full-stack slices lose their backend contract. |

---

## Recommended sequencing (lowest-risk first)

Ordered by blast radius. Each item is independent; ship as commits on one branch, or split by risk tier.

1. **F4, F5** — cosmetic tag + template line. Zero blast radius.
2. **F1** — one-line correctness fix, `1b` only.
3. **F2 + F3** — one coordinated edit to `1c` Phase 3 (add the approval gate; the glossary write becomes conditional on it).
4. **Q3** — additive read/link steps; touches only `2a`. Safest of Part B.
5. **Q2** — wording/gate change; touches only `1b`.
6. **Q1** — touches downstream readers `3b` / `3d` / `4a`. Highest blast radius; do last.

**Cross-set interactions to respect:**
- **F1 ↔ Q2** both live in `1b` Phase 2's "External Research" focus area. F1 fixes the freshness *field*; Q2 changes the *stop conditions*. Apply F1 first (surgical) so Q2's rewrite lands on a correct gate.
- **F3 ↔ Q3** the discovery brief is produced by BOTH `1b` and `1c`, and Q3's `2a` brief-locator/ingestion (below) is what makes *either* brief actually read downstream. Fixing F3 (so `1c` emits an approved brief) and Q3 (so `2a` ingests it) are complementary — a brief that is gated but never read, or read but never gated, only half-closes the loop.
- **F5 ↔ Q3** the brief template is the handover artifact; F5's `est. setup time` line rides in the same template Q3 makes `2a` ingest.

---

# Part A — audit-verified defects

## F1 — `1b` research-freshness gate keys on a nonexistent frontmatter field (P1)

**Where:** [`src/workflows/1b_concept-framing.md:73`](../../src/workflows/1b_concept-framing.md) (Phase 2, "External Research" focus area).

**Now:** *"One strong match → read only frontmatter `updated:` date; if <90 days old, ask: 'Research at docs/research/<slug>.md (updated <updated>)…'"*

**Why it is wrong (verified):**
- Research artifacts are written by `1a` from `research-competitive-template.md` / `research-problem-template.md`; both carry **`timestamp:`**, not `updated:` ([`research-competitive-template.md:5`](../../src/references/research-competitive-template.md), [`research-problem-template.md:5`](../../src/references/research-problem-template.md)).
- OKF declares `timestamp` the canonical last-meaningful-change field ([`okf-protocol.md:27`](../../src/rules/okf-protocol.md)). No `updated` field exists anywhere in the pipeline (grep of `src/workflows/` + `src/references/` returns this one line only).

**Impact:** The `<90 days` vs `>90 days` routing reads an absent key, so the load-bearing *reuse-vs-re-run-`/1a`* decision silently degrades. Highest-value fix in Part A.

**Fix (one line):** replace `updated:` → `timestamp:` and the interpolations `(updated <updated>)` → `(updated <timestamp>)`. No logic change.

## F2 — `1c` writes `GLOSSARY.md` without the memory-protocol confirmation gate (P2)

**Where:** [`src/workflows/1c_concept-map.md:74`](../../src/workflows/1c_concept-map.md) (Phase 3, step 4 "Crystallize Vocabulary").

**Now:** *"Write confirmed terms to `.memory/GLOSSARY.md` as `[[G-xxx]] [ASSUMED]`."*

**Why it is a drift (verified):**
- [`memory-protocol.md:80`](../../src/rules/memory-protocol.md): *"Never writes to any `.memory/` file without proposing and awaiting user confirmation … applies to content entries in LEARNINGS/ARCHITECTURE/DESIGN_RULES/GLOSSARY."*
- `1b` obeys explicitly — Phase 3 step 3 (`1b:89`, *"do not write without confirmation"*) and Phase 7 step 2 (`1b:132`, *"only after user confirmation"*).
- `1c` says *"write confirmed terms"* but **defines no step where confirmation is obtained**. The word "confirmed" is unbacked.

**Impact:** The concept-map path can commit speculative vocabulary to durable memory without the HITL gate `1b` enforces — a memory-protocol violation and a behavioral split between the two brief-producing paths.

**Fix:** In `1c` Phase 3, before step 4's write, add: *"Present crystallized terms for approval; write `[[G-xxx]] [ASSUMED]` only after the user confirms (per `memory-protocol` agent-authority rule)."* Reference `1b`/`memory-protocol` rather than duplicating prose.

## F3 — `1c` Converge has no self-review + user gate before writing the brief and closing the map (P2)

**Where:** [`src/workflows/1c_concept-map.md:68–76`](../../src/workflows/1c_concept-map.md) (Phase 3: Converge).

**Why it is a gap (verified):**
- `1b` gates the *same deliverable* (a `docs/discovery/<slug>.md` brief): Phase 6 "Self-Review + User Gate" (`1b:117–127`) — a 7-item checklist then *"Present brief for approval."*
- `1c` Phase 3 synthesizes the brief (step 2), runs a **report-only** RAT audit (step 3), writes `GLOSSARY.md` (step 4), **closes the `concept:map` issue** + sets `BACKLOG_MAP` to `done` (step 5), then hands off (step 6) — with **no self-review checklist and no approval checkpoint**.

**Impact:** Convergence emits a brief consumed by `/2a_write-prd` and irreversibly closes a tracked map issue, both without sign-off; the RAT audit's findings are report-only, so nothing forces resolution before ship. Strictly weaker than `1b`'s gate for an identical artifact.

**Fix:** Insert a gate between step 4 and step 5: reuse `1b` Phase 6's checklist (reference, don't copy) plus *"Present brief + RAT findings for approval; close the map only after the user confirms."*

## F4 — undefined confidence tag `[MEDIUM]` in `1a` (P3, cosmetic)

**Where:** [`src/workflows/1a_research.md:30`](../../src/workflows/1a_research.md). *"Quick claims cap at `[MEDIUM]`…"* — but the file's tag set is `[HIGH|MED|LOW]` (`1a:61`, reused at `1a:73–100`). **Fix:** `[MEDIUM]` → `[MED]`.

## F5 — RAT `est_setup_time` captured but has no home in the brief (P3, minor gap)

**Where:** [`1b:102–103`](../../src/workflows/1b_concept-framing.md) + [`discovery_brief_template.md:55–59`](../../src/references/discovery_brief_template.md). `1b` requires the cheapest test *"not take >2 weeks"* and its subagent returns `est_setup_time`, but the template's `## Riskiest Assumption` block has no field for it, so the gate is not auditable in the shipped artifact. **Fix (preferred):** add `- **Est. setup time:** <≤2 weeks>` to the template's Riskiest Assumption block; alternatively drop `est_setup_time` from the `1b:103` contract.

---

# Part B — Pocock-benchmarked depth improvements

## Q3 — 1b→2a handover loses information (main leak)

**Finding:** Pocock's `grilling → to-spec` passes NO artifact — `to-spec` reuses the live in-session conversation. StratOS deliberately does the harder cross-session thing (durable `docs/discovery/<slug>.md`), which is correct for its architecture but inherits his `/handoff` principle: **"reference, don't duplicate; external artifacts are the source of truth."** Measured against that, four leaks (verified: `2a` reads the brief only at [`2a:57`](../../src/workflows/2a_write-prd.md) RAT Carry-Over; Phase 3 synthesizes "from **conversation**, BACKLOG_MAP, LEARNINGS, and ADR" at `2a:38`, with the brief not a named structural input):

1. **Contract declared in 1b, not honored in 2a (main leak).** [`1b`](../../src/workflows/1b_concept-framing.md)'s hand-off contract says 2a reads Vocabulary/Actor/Problem/Framing/Non-Goals. But [`2a`](../../src/workflows/2a_write-prd.md) reads the brief in ONE place only — the RAT carry-over. So the handoff silently depends on the conversation still being alive.
2. **No forward pointer.** 2a detects mode from *PRD existence*, never locates `docs/discovery/<slug>.md` by slug. A brief from a prior session may never be opened.
3. **Broken bidirectional link.** Brief carries `linked-prd: —`; 2a never writes the minted `BT-<n>` back, and never records the brief path in the PRD/issue.
4. **Open Questions can evaporate.** 1b writes brief Open Questions "for 2a §10"; 2a's §10 handling only moves 2a's own `> open:` markers. Ingesting the brief's Open Questions is nobody's explicit step.

Sources: `aihero.dev/skills-to-spec` ("does not interview you again… synthesises what is already known"), `aihero.dev/skills-handoff` ("referenced by path or URL, never copied").

**Recommended fixes:**
1. **Move ingestion into 2a and make it structural.** Add a Phase-3 sub-step: *"If `docs/discovery/<slug>.md` exists, read it and seed §1/§2/§4/§6/§7 from Vocabulary/Actor/Problem/Framing/Non-Goals; absorb its Open Questions into §10."* Enforce the contract on the consuming side. *(Also covers `1c`-produced briefs — same artifact type; see F3 interaction.)*
2. **Give 2a a brief-locator step** (Phase 1): derive slug, fuzzy-match `docs/discovery/*.md`, read before drafting (same pattern 1b uses for research files — and now correct after F1).
3. **Close the link at mint time** (Phase 2, after `gh issue create`): write `BT-<padded>` into the brief `linked-prd:` and add the brief path to PRD frontmatter/issue body.
4. **Keep the distillation** — 1b's Synthesis Contract (distilled nuggets, no transcripts, work-file deleted) matches "only settled decisions survive." Don't change; just ensure what survives is actually read downstream.

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

## Q1 — 2b covers UI *or* non-UI, never both (full-stack gap)

**Finding:** The [`src/workflows/2b_interface-design.md`](../../src/workflows/2b_interface-design.md) Phase 1 gate is mutually exclusive: no-UI → Path C; UI → Path A/B. Three things lock it to a single path:
- Phase 2.2 assigns the doc ONE `type` (`ui-generator-*` | `ui-manual` | `non-ui`).
- Phase 4 runs exactly one of the Path A / B / C sub-sections.
- The API/schema/seam contract exists ONLY in Path C step 1.

So a genuinely full-stack slice (new screen **+** new API/schema/adapter seam) gets its UI frozen and its backend contract never designed at 2b — it falls through to 3d improvisation. This collides with the framework's own vertical-slice philosophy. It is a gap, not a documented decision.

**Recommended fix (smallest reversible):** do not add a 4th path. Make Path C's contract block *additive* to the UI paths. Add one step to Paths A and B: *"If this feature introduces a new non-UI contract (API/schema/seam) not already covered, also produce a `## Interface Contract` block per Path C step 1."* One doc, both faces.
- Optional: widen the Phase 1 gate to detect a `hybrid` classification so the composite is deliberate.
- Watch: downstream readers (3b, 3d Phase 0, 4a) must tolerate a doc that carries both a UI blueprint block AND an Interface Contract block — verify each reads the sections it needs rather than assuming a single path type.

---

## Decisions still open

- [ ] Which fix(es) to implement, and one PR or split by risk tier?
- [ ] Part A: implement the unambiguous defects (F1/F2/F4) now, and treat F3 as gated on the intent question below?
- [ ] F3: should `1c` convergence be a hard HITL stop like `1b` (recommended), or was it intentionally auto-closing for AFK runs? If the latter, F3 becomes "log the skip as residual risk" (the pattern `1b:99` uses for AFK RAT declines) rather than a blocking gate. **Confirm before implementing F3.**
- [ ] Q1: additive `## Interface Contract` step only, or also add the `hybrid` gate classification?
- [ ] Q2: full rewrite of Phase 2 stop conditions, or minimal (fixes 1–2 only)?
- [ ] Confirm build/dist rebuild + `4a_verify-and-ship` is the intended ship path.

## Resume instructions

1. Open this repo in claude.ai/code or the Claude mobile app. Branch: `claude/v3-polish-discovery-pipeline-kn3h6l` (where this proposal lives), or cut a fresh `feat/BT-…` branch. *(Note: the original `fix/post-v3-polish` line merged as PR #102 — do not reuse it.)*
2. Say: *"Implement the F1/F2 fixes"* or *"Implement the Q3 fixes from `docs/proposals/FEAT-discovery-pipeline-quality-fixes-proposal.md`"* (or any subset).
3. Edit `src/workflows/*` and `src/references/*` (never `dist/` or `.agents/`), bump each touched file's OKF `version` once per PR, rebuild `dist/`, then `/4a_verify-and-ship`.

## Residual risk / what remains unverified

- Part A line numbers were confirmed at `timestamp`; Part B findings were verified against the workflows in-session (`2a` brief-read locations re-confirmed at `2a:38`/`2a:57`). Re-anchor every edit by content.
- The Pocock benchmark (Part B) rests on the cited `aihero.dev` / GitHub sources captured during the origin session; treat the "50+ questions / no budget" characterization as his stated norm, not a StratOS measurement.
- F3's fix assumes convergence *should* be a hard HITL stop — see the open decision above.
