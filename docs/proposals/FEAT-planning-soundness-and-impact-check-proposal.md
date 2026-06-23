---
name: planning-soundness-and-impact-check-proposal
description: Upstream scaffolding to make a weaker long-horizon planner produce sound plans — headed by a planning-time Impact/Interdependency check (subagent).
type: proposal
trigger: User. Do not run autonomously.
version: "1.0.0"
timestamp: 2026-06-23
---

# Workflow Proposal: planning soundness via upstream scaffolding (+ an impact check)

**Status:** Parked proposal. Not implemented. Pick up in a fresh session.
**Origin:** Decided after reviewing Matt Pocock's skills + the user's observation that Antigravity (Gemini) is weaker than Claude Code at producing long, sound plans. This document is self-contained.

> **Decisions already locked (do not re-open):**
> - `plan-html` stays a single, focused **planning-support** skill — NOT split, and NO separate prototype skill (runnable-throwaway needs are covered by `3b` Template A spikes + `micro-tdd`). `plan-html` is a *rendering* layer; it helps a human *engage with* a plan but cannot make the model's plan *content* sounder.
> - The chosen lever for weak planning is **upstream workflow scaffolding** (this proposal) — not plan-html rendering, not model-routing.
> - **Headline / do-first:** the smallest change with the biggest impact is a **planning-time Impact/Interdependency check** (§2). The broader template/checklist tightenings (§3) are secondary.

---

## 1. Why this exists

A weaker long-horizon planner is **reliable at filling bounded, well-specified slots and at being interviewed, and unreliable at free-composing a long, coherent plan in one pass.** Two failure shapes follow: (a) it *omits* (skips a section, an edge case, a dependency), and (b) it reasons **locally** — about the new thing it's adding, not about the **blast radius** on existing code. (b) is the expensive one: it's the main source of rework (the ~30% rework gap Claude Code avoids vs Gemini-class agents is largely "got the interdependencies right the first time"). The fix is to **scaffold the model into structure** rather than trust its free-form reasoning — and the single highest-leverage piece of that scaffold is making the **ripple onto existing code** an explicit, checked planning step.

Web note (for the next agent): the "Antigravity is weaker at long plans" claim is the user's empirical signal, **not** a web-backed fact — public sources show Claude Code more accurate / less rework on SWE-bench, but market Gemini 3 as strong on long-horizon planning, and Antigravity is preview-stage. Treat the scaffolding as robust-to-any-model, not as an Antigravity patch.

---

## 2. The high-impact small fix — a planning-time Impact / Interdependency check (DO FIRST)

### 2.1 The gap (verified against the workflows)
| Existing check | What it covers | Why it is NOT impact analysis |
|---|---|---|
| `1b` Internal Prior Art | "what code already touches this?" | Awareness of related code, not "what breaks if I change it" |
| `3a`/`3b`/`3c` "Blocked by" | issue/feature *sequencing* dependencies | Not *code* interdependencies |
| `3d` Anti-Regression + "existing tests stay green" | regressions caught at implement time | **Late** (post-plan), **test-bound** (misses untested ripple), reactive |
| `4b` dependency-inversion / cross-domain imports | post-hoc *structural drift* on settled code | Not *pre-build change-impact* |

→ **Nothing maps, at planning time, what existing code a planned change ripples into.** That is the gap.

### 2.2 What to add: an **Impact Auditor** subagent
A read-only subagent that, given the *planned* change, maps the blast radius onto existing code and writes it into the durable plan artifact so every downstream step inherits it.

- **Primary home — `2b_interface-design`.** Ripple is *born* when a contract changes, and `2b` covers all code changes (UI via Path A/B, backend/API via Path C; only docs-only/process skips it). Invoke the Impact Auditor in Phase 4 (Harmonize & Freeze), and write its output into a **new `## Impact & Interdependencies` section** of the frozen design doc (`docs/design/BT-<padded>-interface.md`). Downstream `3b`/`3d`/`4a` already read this doc — so **one insertion propagates** through the whole flow.
- **Backstop — `3b_create-issue` (optional, light).** For changes that reached `3b` *without* a `2b` design doc (e.g., a standalone bug routed straight from `1b`'s exit ramp via Template A/B), add a one-line slice-level impact flag feeding the slice's **Notes**/**Dependencies**. Keep it light; `2b` is the rich home.

### 2.3 Subagent contract (match the existing StratOS pattern — see 4a/4b/3b)
- **Invoke:** an independent, read-only subagent (Antigravity `invoke_subagent` / Claude Code `Task`, `general-purpose`).
- **Input:** the planned interface/change (the design-doc draft); the codebase **scoped to the affected module/contract** (never the whole repo); `.memory/ARCHITECTURE.md` (declared boundaries / `[[A-xxx]]`); `.memory/GLOSSARY.md` (domain terms). `.agents/workflows/.reference/confidence-scale.md` for scoring.
- **Guardrails:** *"Map impact only; do not edit code or write files."*
- **Output Contract — an impact map**, each finding severity-scored: 
  - **Consumers/callers** of the changed interface (who depends on it);
  - **Shared surfaces touched** — contracts/types, shared modules, data/schema, global state;
  - **Breaking-change risks** (signature/behavior/contract changes that would break callers);
  - **Downstream features/areas** affected (by `[[BT]]`/area, cross-referenced to BACKLOG_MAP).
- **Audit scope line (per the confidence-scale convention):** *"Audit scope: how this planned change affects existing callers, contracts, shared modules, data, and downstream features. A Report-grade (≥80) finding is a concrete, evidenced ripple that would break or silently alter existing behavior."* Score 0–100 per `confidence-scale.md`; report only ≥ 80.

### 2.4 Minimizing mistakes / cost (same discipline as the other audits)
- **Scope to the affected module/contract**, never the whole repo (token cost + noise).
- **Read-only, propose-only** — it flags ripple and where regression tests are needed; it never edits.
- **Confidence-gated (≥80)** so it surfaces real risks, not a list of every file that mentions a word.
- **Agent judgment** to exclude false ripple (same-named-but-unrelated symbols, third-party names) — this is why it's a subagent, not a grep.
- **Whole-symbol matching**, not substring.

### 2.5 How it differs from existing subagents (so it isn't "we already have this")
- vs `2b` **Stress Tester**: stress = robustness of the **new** design under adverse conditions; impact = blast radius on **existing** code. Complementary; both run in `2b` Phase 4.
- vs `3b` **Coverage Auditor**: coverage = do slices cover the **spec** (§6/§8); impact = does the change break **existing** code *outside* the spec. Opposite direction.
- vs `3d` **Anti-Regression**: regression = existing **tests** stay green at implement time (late, test-bound); impact = a planning-time map of what **could** break, *including untested paths* — and it tells `3d`/`4a` **where to add regression tests**, strengthening the net instead of relying on it.
- vs `4b` **drift audit**: `4b` = post-hoc structural drift on settled code; impact = pre-build change-ripple. Different timing and purpose.

### 2.6 Why this is the "small fix, big impact"
One new subagent + one new design-doc section, threaded through hand-off contracts that already exist. It attacks the dominant rework cause (missed interdependencies), is exactly what a weak local-reasoning planner omits, and is *cheaper than re-architecting the templates*. Do this before §3.

---

## 3. The broader scaffolding tightenings (secondary)

These tighten what already exists; they are lower priority than §2. Unifying principle from §1: **bounded slots + exhaustive checklists + decomposition + interview-extracted soundness** beat free-form long-form reasoning.

1. **Section-by-section authoring, not one-shot drafts (`2a_write-prd`).** Make the model fill each PRD section against a crisp slot spec + a one-line example ("§2 Solution: 2–3 sentences, user perspective, no implementation"), validating per section — rather than composing the whole §1–§12 doc in one pass. A weak model nails a constrained slot and fumbles a long narrative. (Tighten the PRD-template slot specs in `.agents/workflows/.reference/PRD-template.md`.)
2. **Exhaustive, checkable completion checklists as the anti-omission defense.** Harden `2a` Phase 4 validate and `3b`'s Coverage Auditor so criteria are exhaustive ("every §6 story has scope-class + ODI; every `[DEFERRED]` mirrored in §9; every open question in §10"). This is Matt's "sharp completion criterion" applied to planning.
3. **Decomposition over length.** Keep each artifact short and push detail downstream (brief → PRD → interface → slices), chained by the existing hand-off contracts. Several short bounded steps beat one long plan for a weaker model — so resist letting any single workflow carry everything.
4. **Let the grill extract soundness (`1b`).** The relentless one-question-at-a-time interview sources soundness from the *dialogue*, not the model's solo reasoning. Tighten the coverage axes and the "name the ambiguity, re-ask until sharp" discipline. (Consider adding an **"Existing-code impact"** axis to 1b's grill so the ripple question is raised at concept time too — a cheap upstream complement to §2.)

---

## 4. Principles & mechanics (for the implementing session)

- **Numbering (post-renumber):** version-planning=`3a`, create-issue=`3b`, sprint-planning=`3c`, implement-issue=`3d`. PRD=`2a`, interface=`2b`.
- **Edit `src/` only**, rebuild `dist/` via `python build/build.py`, confirm `build/validate.py` + install-harness green. Bump OKF `version`+`timestamp` on every changed file.
- **Reuse, don't duplicate:** the Impact Auditor scores via the shared `confidence-scale.md` (with its own one-line audit-scope, per the established pattern); add an `## Impact & Interdependencies` section to `design-doc-template.md`.
- **Subagent discipline** (consistent with 4a/4b/3b): Invoke + read-only Guardrails + Output Contract; scoped, confidence-gated, propose-only; the guardrail is the subagent's whole contract (isolated context) — never drop it.
- **Do not** wire the impact check into `4b` (structural audit, discards lexical/low-confidence signals) or make it a full-repo scan.

---

## 5. Recommended sequence
1. **§2 Impact Auditor at `2b`** (+ design-doc section). Smallest change, biggest rework reduction. Ship and feel the effect first.
2. (Optional) §2.2 light backstop in `3b` if direct-to-issue changes are common.
3. **§3 tightenings**, in order: PRD slot specs (3.1) → completion checklists (3.2) → 1b impact axis (3.4). Decomposition (3.3) is mostly "resist scope creep in each workflow," not an edit.

---

## 6. Open questions for the implementing session
- **Impact scope heuristic:** how does the subagent bound "the affected module/contract" — from the design doc's named interfaces + ARCHITECTURE areas? Define the scoping rule so it never defaults to the whole repo.
- **Backstop necessity:** is the `3b` light backstop (§2.2) worth it, or does `2b` coverage (all code changes route through it) make it redundant? Decide based on how often you create issues without a `2b` design doc.
- **1b impact axis (3.4):** add to the grill now, or defer until §2 proves the value at `2b`?

---

## 7. References
- Workflows: `src/workflows/2b_interface-design.md` (Phase 4 + Stress Tester), `3b_create-issue.md` (Coverage Auditor), `3d_implement-issue.md` (Anti-Regression via micro-tdd), `4b_audit-architecture-drift.md` (structural drift), `1b_concept-framing.md` (Internal Prior Art axis).
- Reference docs: `.agents/workflows/.reference/PRD-template.md`, `design-doc-template.md`, `confidence-scale.md`.
- Related proposal: `docs/proposals/dev-workflow/3c-4a-verification-completion-proposal.md` (the per-slice vs integration verification gaps — the impact check complements its findings).
- Web review (planning quality): [Augment](https://www.augmentcode.com/tools/google-antigravity-vs-claude-code), [DataCamp](https://www.datacamp.com/blog/claude-code-vs-antigravity), [Google Developers — Antigravity](https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/) — evidence is thin on the specific "weaker long plans" claim; treat the scaffolding as model-agnostic.
