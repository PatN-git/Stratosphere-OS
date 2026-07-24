---
name: discovery-pipeline-quality-fixes-proposal
description: Surgical quality fixes for the Discover-phase pipeline (1a/1b/1c) — a broken research-freshness gate, two HITL/memory gate gaps in 1c convergence, and two cosmetic drifts. All findings verified against source file:line.
type: proposal
trigger: User. Do not run autonomously.
version: "1.0.0"
timestamp: 2026-07-24
---

# Workflow Proposal: Discovery-pipeline quality fixes (1a / 1b / 1c)

**Status:** Parked proposal. Not implemented. Pick up in a fresh session.
**Scope:** The Discover phase only — `1a_research`, `1b_concept-framing`, `1c_concept-map`, and the two shared references (`discovery_brief_template.md`, `multi-sided-discovery.md`). This document is self-contained.
**Method:** Each finding was read out of source and cross-checked against the OKF and memory protocols. Line numbers are from source (`src/workflows/`, `src/references/`, `src/rules/`) at `timestamp` above; re-confirm before editing since numbers drift.

> **Decisions the implementer should not re-open:**
> - These are *surgical* fixes (§SIMPLICITY-FIRST / §SURGICAL-EDITS). No restructuring of the Discover phase, no new subagents, no new references. The pipeline's shape is sound; only the listed defects are in scope.
> - `1b` is the reference implementation for the HITL brief-production gates. Where `1c` diverges (F2, F3), align `1c` **to** `1b` rather than inventing a third pattern.

---

## 0. Summary (severity-ordered)

| # | Sev | File | One-line |
|---|-----|------|----------|
| F1 | **P1 — correctness** | `1b:73` | Research-freshness gate reads a `updated:` frontmatter field that does not exist; research carries `timestamp:`. |
| F2 | **P2 — protocol drift** | `1c:74` | `1c` convergence writes `GLOSSARY.md` with no user-confirmation step; `memory-protocol` requires one and `1b` enforces it. |
| F3 | **P2 — HITL gap** | `1c:68–76` | `1c` Phase 3 (Converge) has no self-review + user approval gate before it writes the brief and **closes the map issue**; `1b` gates the same deliverable. |
| F4 | P3 — cosmetic | `1a:30` | Confidence tag `[MEDIUM]` is undefined; the file's tag set is `[HIGH\|MED\|LOW]`. |
| F5 | P3 — minor gap | `1b:103` / template | RAT subagent returns `est_setup_time` and enforces a ≤2-week cap, but the brief template has nowhere to record it, so the gate is not auditable downstream. |

---

## F1 — `1b` research-freshness gate keys on a nonexistent frontmatter field (P1)

**Where:** `src/workflows/1b_concept-framing.md:73` (Phase 2, "External Research" focus area).

**What it says now:**
> One strong match → read only frontmatter `updated:` date; if <90 days old, ask: "Research at docs/research/<slug>.md (updated <updated>). Still current, or refresh first?" … if >90 days, treat as stale and prompt to refresh.

**Why it is wrong (verified):**
- Research artifacts are written by `1a` from `research-competitive-template.md` / `research-problem-template.md`. Both templates carry **`timestamp:`**, not `updated:` (`src/references/research-competitive-template.md:5`, `src/references/research-problem-template.md:5`).
- OKF declares `timestamp` the canonical last-meaningful-change field (`src/rules/okf-protocol.md:27`: *"`timestamp` … OKF's canonical change-date field"*). There is **no `updated` field** anywhere in the Discover pipeline (grep of `src/workflows/` + `src/references/` returns this one line as the only `updated:` occurrence).

**Impact:** The `<90 days` vs `>90 days` routing reads an absent key. The freshness decision — *reuse existing research vs re-run `/1a_research`* — is load-bearing (it gates whether an entire research pass is skipped), and it silently degrades: the agent either treats every match as fresh (missing key) or improvises a date. This is the highest-value fix in the set.

**Fix (one line, surgical):** In `1b:73`, replace `updated:` → `timestamp:` and the two interpolations `(updated <updated>)` → `(updated <timestamp>)` (or `(timestamp <timestamp>)`). No logic change; the 90-day threshold and prompts stay.

---

## F2 — `1c` writes `GLOSSARY.md` without the memory-protocol confirmation gate (P2)

**Where:** `src/workflows/1c_concept-map.md:74` (Phase 3, step 4 "Crystallize Vocabulary").

**What it says now:**
> Crystallize Vocabulary: Write confirmed terms to `.memory/GLOSSARY.md` as `[[G-xxx]] [ASSUMED]`.

**Why it is a drift (verified):**
- `memory-protocol.md:80` — *"Never writes to any `.memory/` file without proposing and awaiting user confirmation … this confirmation rule applies to content entries in LEARNINGS/ARCHITECTURE/DESIGN_RULES/GLOSSARY."*
- `1b` obeys this explicitly: Phase 3 step 3 (`1b:89`, *"assign IDs with `[ASSUMED]` tag — do not write without confirmation"*) and Phase 7 step 2 (`1b:132`, *"Write confirmed `[[G-xxx]]` entries … only after user confirmation from Phase 3"*).
- `1c` says *"write confirmed terms"* but **defines no step where confirmation is obtained** — Phase 2 (Work) resolves tickets, Phase 3 (Converge) synthesizes and writes. The word "confirmed" is unbacked.

**Impact:** The two brief-producing paths behave differently on durable memory. `1c` can commit speculative vocabulary to `GLOSSARY.md` without the HITL gate that `1b` enforces — a memory-protocol violation on the concept-map path.

**Fix:** In `1c` Phase 3, before step 4's write, add a one-line approval step mirroring `1b` Phase 3: *"Present crystallized terms for approval; write `[[G-xxx]] [ASSUMED]` to `GLOSSARY.md` only after user confirms (per `memory-protocol` agent-authority rule)."* Prefer citing `1b`/`memory-protocol` over duplicating the V1–V3 prose already at `1c:54`.

---

## F3 — `1c` Converge has no self-review + user gate before writing the brief and closing the map (P2)

**Where:** `src/workflows/1c_concept-map.md:68–76` (Phase 3: Converge).

**Why it is a gap (verified):**
- `1b` gates the *same deliverable* (a `docs/discovery/<slug>.md` brief): Phase 6 "Self-Review + User Gate" (`1b:117–127`) runs a 7-item checklist and then *"Present brief for approval."*
- `1c` Phase 3 synthesizes the brief (step 2), runs a **report-only** RAT audit (step 3, *"Report findings only; do not edit files"*), writes `GLOSSARY.md` (step 4), **closes the `concept:map` issue** and sets its `BACKLOG_MAP` row to `done` (step 5), then hands off (step 6). There is **no self-review checklist and no user approval checkpoint** anywhere in the phase.

**Impact:** Convergence is a HITL milestone that (a) emits a brief consumed by `/2a_write-prd` and (b) irreversibly closes a tracked map issue — both without sign-off. The RAT audit's findings are report-only, so nothing forces them to be resolved before the brief ships. This is strictly weaker than `1b`'s gate for an identical artifact.

**Fix:** Insert a gate between step 4 and step 5: reuse `1b` Phase 6's checklist (reference it, don't copy) plus *"Present brief + RAT findings for approval; close the map only after the user confirms."* Keeps convergence a HITL stop instead of an auto-close.

---

## F4 — undefined confidence tag `[MEDIUM]` in `1a` (P3, cosmetic)

**Where:** `src/workflows/1a_research.md:30`.

**What it says now:** *"Quick claims cap at `[MEDIUM]` (no refutation pass)…"*

**Why:** The file's confidence tag set is `[HIGH|MED|LOW]` (`1a:61`), reused at `1a:73–100`. `[MEDIUM]` is not a member of that set — a lone drift in an otherwise consistent file.

**Fix:** `[MEDIUM]` → `[MED]`. No behavior change.

---

## F5 — RAT `est_setup_time` is captured but has no home in the brief (P3, minor gap)

**Where:** `src/workflows/1b_concept-framing.md:102–103` and `src/references/discovery_brief_template.md:55–59`.

**Why:** `1b` Phase 4.5 requires the cheapest test to *"not take >2 weeks"* (`1b:102`) and the Skeptical-Challenger subagent returns `est_setup_time` (`1b:103`). But the brief template's `## Riskiest Assumption` block has fields only for Riskiest Assumption / Why Fatal / Cheapest Test / Status (`discovery_brief_template.md:55–59`) — the estimate is dropped, so the ≤2-week gate is not auditable in the shipped artifact.

**Fix (pick one):**
- **Preferred:** add one line to the template's Riskiest Assumption block — `- **Est. setup time:** <≤2 weeks>` — so the gate is recorded and reviewable.
- Alternative: drop `est_setup_time` from the `1b:103` subagent output contract if it is genuinely disposable. (Preferred option is cheaper and keeps the constraint honest.)

---

## Implementation notes

- **Order:** F1 first (only correctness bug). F2/F3 are one coordinated edit to `1c` Phase 3 (add the approval gate; the glossary write becomes conditional on it). F4/F5 are trivial and can ride along.
- **Version bumps (OKF, once-per-PR, fork-point baseline):** F1 → `1b` patch; F2+F3 → `1c` patch; F4 → `1a` patch; F5 → `discovery_brief_template.md` patch (and `1b` if the subagent contract is touched). Follow the per-file once-per-PR policy already in force.
- **Verification:** F1 — after the edit, a research file with a `timestamp:` <90 days must trigger the reuse prompt (grep confirms no remaining `updated:` in the pipeline). F2/F3 — dry-run `1c` Converge and confirm it now stops for approval before closing the map. F4/F5 — grep/visual.
- **Out of scope (explicitly):** no new subagents, no Discover-phase restructuring, no changes to `1a`'s deep-research loop, budget cap, or triangulation rules — those read as sound.

## Residual risk / what remains unverified

- Line numbers will drift; the implementer must re-anchor each edit by content, not line.
- F3's fix assumes concept-map convergence *should* be a hard HITL stop like `1b`. That matches the "HITL milestone" framing in both workflows' headers, but if a deliberate design decision made `1c` convergence auto-closing for AFK runs, F3 should instead log the skip as residual risk (the pattern `1b:99` uses for AFK RAT declines) rather than block. Confirm intent with the user before implementing F3.
