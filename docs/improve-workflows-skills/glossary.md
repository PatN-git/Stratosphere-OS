---
type: reference
title: Improving Workflows & Skills — Lexicon
description: Self-contained lexicon for authoring StratOS skills/workflows — discipline terms + the leading-word palette (the tokens to use, and the synonyms to avoid). Companion to README.md.
version: "1.0.0"
timestamp: 2026-06-23
---

# Lexicon — Improving Workflows & Skills

The companion to [`README.md`](README.md). Everything is defined **inline** — nothing external is needed to use this pair.

Use these as **leading words**: the same term here, in your prompts, and in your audits means one thing. When authoring, reach for a palette token (Part B) rather than a synonym — that's what makes the vocabulary *ubiquitous* across StratOS.

---

## Part A — Discipline terms

The vocabulary of the playbook itself.

- **Predictability** — the agent takes the same *process* every run (not the same output). The root virtue; cost and maintainability are symptoms of it.
- **Leading word** — a compact, pretrained concept reused as a token (never restated as a sentence); encodes a behaviour in the fewest tokens by recruiting priors the model already holds.
- **Completion criterion** — the condition that tells the agent a step is done; strong ones are *checkable* (done vs not-done is decidable) and *exhaustive* (covers every case).
- **Premature completion** — ending a step before it's genuinely done; resisted by a sharp completion criterion.
- **Progressive disclosure** — moving reference out of the body behind a **context pointer**, so the top stays legible; gated by the skill self-containment limit (README §1).
- **Context pointer** — an in-context reference naming out-of-context material; its *wording* (not its target) decides how reliably the agent reaches it.
- **Single source of truth** — each meaning lives in exactly one authoritative place; **duplication** is its violation.
- **No-op** — a line the model already obeys by default; pays load to say nothing. The test ("does it change behaviour vs the default?") is **model-relative** — settle by running, not debating.
- **Duplication** — the same meaning in more than one place (distinct from a leading word, which repeats a *token*, never the meaning).
- **Sprawl** — simply too long, even when every line is live and unique; cured by the ladder (disclose reference; split by branch/sequence).
- **Sediment** — stale lines that accrete because adding feels safe and removing feels risky.

---

## Part B — Leading-word palette

Reach for **these tokens**, not the listed synonyms. (Structural terms also live in `.memory/ARCHITECTURE.md` for *runtime* use; this is the authoring-time copy — keep them in step.)

### Structural / design
- **module** — anything with an interface + implementation; scale-agnostic (function, class, package, slice). *Avoid:* unit, component, service.
- **interface** — everything a caller must know to use a module: signature *plus* invariants, ordering, error modes, config, performance. *Avoid:* API, signature (too narrow).
- **implementation** — the body of code inside a module (distinct from **adapter**).
- **depth** / **deep** / **shallow** — leverage at the interface: a *deep* module hides a lot of behaviour behind a small interface; a *shallow* one's interface is nearly as complex as its implementation.
- **seam** — the location where a module's interface lives; where you can alter behaviour without editing in that place. *Avoid:* boundary (overloaded with DDD).
- **adapter** — a concrete thing satisfying an interface at a seam (a *role*, not a substance).
- **leverage** — what callers gain from depth: more capability per unit of interface learned.
- **locality** — what maintainers gain from depth: change/bugs/knowledge concentrate in one place.
- **deletion test** — imagine deleting the module: if complexity vanishes it was a pass-through; if it reappears across callers it earned its keep.
- **deepening** — turning a shallow module deep.

### Process / loop
- **tracer bullet** / **vertical slice** — a thin path through every layer that proves the whole end-to-end; the unit of work. *Avoid:* horizontal slice, thin layer.
- **red** / **green** / **refactor** — the TDD loop's binary observable states; "goes *red* on the bug" beats "a loop you believe in".
- **tight** (loop) — fast + deterministic + low-overhead feedback, in one word.
- **relentless** — the strength upgrade for a weak "be thorough" (which is usually a **no-op**).

### StratOS tokens
- **`[[G-xxx]]` / `[[A-xxx]]` / `[[DR-xxx]]`** — glossary / architecture-law / design-rule IDs; the link handle in docs & memory (use the *word* in code).
- **`Avoid:`** — a glossary term's banned-synonym list (this palette's own mechanism, applied to the product vocabulary).
- **BT-`<padded>`** — a backlog task / feature/slice identifier.
- **ICE** / **ODI** / **RAT** — prioritisation score / opportunity score / riskiest-assumption test.
- **scope-class** — `scope:baseline` vs `scope:differentiator` on a story/slice.
- **Immortal Components** — `DESIGN_RULES.md` §3 layout elements that must not be altered.
- **`[UNCOVERED]`** — a coverage-map gap marker (shared by `3b`'s Coverage Auditor and `3d`'s Slice Completion Gate).
- **coverage map** — the AC/requirement → covering-slice-or-test mapping a verifier produces.
- **ephemeral** — produced for the moment and not persisted (e.g. the completion gate's check writes nothing to the issue/PR).
- **exhaustive** — covers *every* case by name, never "looks complete".
- **OKF** — the Open Knowledge Format frontmatter convention (`type`/`version`/`timestamp`…).

---

## Provenance
Adapted from Matt Pocock's `github.com/mattpocock/skills` — `writing-great-skills` (the discipline + Part A) and `codebase-design` (Part B structural terms + the `_Avoid_` discipline). Read the originals **only when extending this lexicon**; for routine authoring, this pair is sufficient.
