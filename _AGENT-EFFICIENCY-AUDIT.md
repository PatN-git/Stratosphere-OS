# Workflow Agent-Efficiency Refactor — Quality Audit

**Branch:** `refactor-workflows-agent-efficiency`
**Baseline:** `origin/main` @ `6180f6d` (local `main` verified identical to remote after `git fetch` — audit is against the current tip)
**Working tree:** uncommitted changes only (no branch commits; sits directly on `origin/main`)
**Scope reviewed:** all 16 workflows `src/workflows/0a…4b`, plus the two reference docs the branch also touched
**Method:** per-file `git diff origin/main` read line-by-line against the repo's own authoring rubric (`docs/improve-workflows-skills/README.md` + `glossary.md`) and the cited `src/rules/output-mode.md` ("No fillers", "Word economy"). Headline defects independently re-verified by grep. No files were modified by this audit.

> **Report placement note:** this file lives in `src/workflows/` per request. `build/build.py` auto-globs `*.md` here and expects workflow OKF frontmatter (`version:` stamp) — move or delete this report before the next build, or `build/validate.py` may miscount invocables.

---

## 1. Verdict

**The refactor achieves its stated goal but overshoots the rubric's hard limits in five files.**

- ✅ **Goal met.** The two files the prompt flagged (`1b`, `1c`) are genuinely de-wordified — human-centered rationale prose is gone and they now read as agent instructions without losing their process. Word-economy and no-filler discipline is applied well across the board; byte savings are real (25–60% per file).
- ⛔ **But it crossed the rubric's explicit "Never prune" line.** The rubric protects three classes as *the lever, not overstatement*: **sub-agent guardrails, safety invariants, and load-bearing exhaustiveness/completion criteria**. All three were cut somewhere:
  - **Sub-agent guardrails deleted** in `3a` (Release Auditor) and `1a` (Verify/Refute) — a dispatched sub-agent runs in isolated context and never sees surrounding prose, so its guardrail is its *entire* contract.
  - **Completion/exhaustiveness criteria gutted** in `3b` (Coverage Auditor contract → fragment), `3d` (Slice Completion Gate lost "exhaustive" + "never silently ship"), and `3a` (audit checks flattened).
  - **Safety invariant narrowed** in `4b` ("do not modify production code" → subagent-scope only).
- ⚠️ **`4b` is not a prune at all** — it is a semantic rewrite on what looks like a stale pre-`main` base: its version number went *backwards* (1.0.6 → 1.0.5) and it deleted a required context pointer.
- ⚠️ **Scope creep:** the branch also amended its own governing rubric (`README.md` new §4.5) to sanction the aggressive cutting it then applied. Not requested by the prompt.

**Recommendation: do not merge as-is.** Restore the items in §2 (targeted edits, not a redo), fix the two defects in §4, and reconcile `4b` against `main`. Six files are clean and can ship untouched.

---

## 2. Verdict table

| File | Verdict | Headline issue |
|---|---|---|
| 0a_start-session | ✅ clean-lean | — |
| 0b_stop-session | 🟡 mixed | shed qualifiers ("module-scoped", "same as 1b", `.agents/` path prefixes) |
| 0c_handoff | ✅ clean-lean | — |
| 0d_nightly-consolidation | ✅ clean-lean | (only a rationale cross-ref dropped) |
| 1a_research | 🟡 mixed | ⛔ Verify/Refute subagent "do not write any file" guardrail cut; + duplicated-clause defect |
| 1b_concept-framing | 🟡 mixed | goal met; softenings + leading word "relentless" dropped from description |
| 1c_concept-map | ✅ clean-lean | goal met; `grilling`→`Scan` heading nit |
| 2a_write-prd | 🟡 mixed | Phase 4 validate checklist pruned past self-sufficiency |
| 2b_interface-design | 🟡 mixed | Path C lost leading words `seam` + `depth/deep/shallow`; `(DR-008/DR-010)` pointer dropped |
| 3a_version-planning | ⛔ over-pruned | **Release Auditor subagent guardrail deleted**; audit checks flattened; growth-loop rule dropped |
| 3b_create-issue | ⛔ over-pruned | **Coverage Auditor output contract gutted to a fragment**; `[DEFERRED]→not-[UNCOVERED]` guard gone |
| 3c_sprint-planning | ✅ clean-lean | **exemplary** — halved with zero load-bearing loss |
| 3d_implement-issue | 🟡 mixed | Slice Completion Gate lost "exhaustive"/"never silently ship"; `[[G-xxx]]` dropped |
| 3z_afk-loop | ✅ clean-lean | (soft: dropped "(exhaustive)" + terminal-state enumeration) |
| 4a_verify-and-ship | 🟡 mixed | safety guards hold but terse; `[[L-xxx]]/[[A-xxx]]` → "vulnerability/audit refs" regression |
| 4b_audit-architecture-drift | ⛔ rewrite/over-reach | **version regressed 1.0.6→1.0.5**; `issue-templates.md` pointer deleted; safety invariant narrowed |

Tally: **6 clean-lean · 7 mixed · 3 over-pruned/rewrite.**

---

## 3. HARD violations — must fix before merge

These are the rubric's protected classes. Each was independently confirmed.

### 3.1 `3a` — Release Auditor sub-agent guardrail deleted *(confirmed by grep)*
`origin/main` Phase 2.5 carried:
> **Guardrails:** *"Report the audit findings only; do not edit any file, create milestones, or modify the roadmap."*

The refactored Phase 2.5 auditor step has **no guardrail at all**. A dispatched auditor now has zero contract preventing it from editing files, creating GitHub milestones, or mutating the roadmap. **Restore verbatim.** (Contrast: `2b` and `3b` correctly kept their subagent guardrails — this omission is inconsistent within the same refactor.)

Also in `3a`:
- Exhaustive audit checks flattened — lost the scope-class trap check ("flag any case where the X/Y choice appears driven by scope class rather than the §-compatibility test"), the conditional severity `[BLOCKER] if it changes the number, else [WARN]`, and the checkable MVP test ("independently shippable — no dangling dependency on a deferred feature").
- Sequencing invariant half-dropped: "never defer a feature that enables the primary growth loop past the release in which the core product goes live" is gone from both the rule and the auditor check.
- Phase 1 "(no writes)" read-only contract dropped.

### 3.2 `1a` — Verify/Refute sub-agent guardrail cut *(confirmed by grep — no match remains)*
`origin/main` constraint ended: *"…do not write any file (parent owns the work file)."* The refactored constraint ends at the JSON return spec — the write-prohibition is gone. **Restore.** (The analogous RAT guardrail in `1b` *was* kept — again inconsistent.)
- Supporting cut: Budget-Tracking lost "and do not spawn a subagent" on the `remaining <= 0` branch.

### 3.3 `3b` — Coverage Auditor output contract gutted *(confirmed by grep)*
The subagent's *safety* guardrail survived (`"Report coverage map only; do not create issues or edit files."` ✅), but its *completion contract* collapsed to the garbled fragment:
> `Walking journey-grouped stories in output contract.`

Lost: the exhaustive mapping criterion ("map **every** `[BASELINE]`/`[DIFFERENTIATOR]` §6 story, §8 DoD item, and design blueprint element** to a covering slice or `[UNCOVERED]`") **and** the false-positive guard ("`[DEFERRED]`/§9 Out-of-Scope items are intentionally out — treat as covered, **not** `[UNCOVERED]`"). This is precisely the checkable-exhaustiveness the rubric forbids cutting. **Restore the mapping enumeration + the DEFERRED guard.**

### 3.4 `3d` — Slice Completion Gate enforcement weakened
The micro-tdd delegation (the marquee must-keep) is **intact and correctly worded** ✅. But the gate lost: the word **"exhaustive"**, the anti-shortcut guard **"list each by name, never summarize as 'looks complete'"**, and the ship-safety invariant **"never silently ship"**. Also the `[[G-xxx]]` citation on the Avoid-drift rename step was dropped. **Restore the three enforcement phrases + the `[[G-xxx]]` token.**

### 3.5 `4b` — rewrite on a stale base + narrowed safety invariant *(version regression confirmed by grep)*
- **Version went backwards: 1.0.6 → 1.0.5.** Combined with wholesale structural divergence, this strongly suggests the branch's `4b` descended from a pre-`main` copy and **clobbered** `main`'s 1.0.6 rather than pruning it.
- **`issue-templates.md` / Template-B context pointer deleted** — the required `.agents/workflows/.reference/issue-templates.md` citation is gone, replaced by a new output path.
- **Safety invariant narrowed:** "Do not modify production code / Do not write refactored code" is now stated only as the *subagent* constraint; the native/local execution path has no explicit do-not-modify guard.
- Behavior itself changed (named-directory audit → `git diff` audit; downstream handoff `/3b_create-issue` → `/4a` ship gate). **Reconcile against `main` deliberately — this file needs a decision, not a restore.**

---

## 4. Defects (bugs, independent of the pruning question)

1. **`1a` duplicated clause** *(confirmed)* — line 74 reads `If \`remaining <= 0\` or remaining <= 0, skip refutation.` The second clause is a copy error (and isn't even backticked). Fix to a single condition.
2. **`4b` version regression** — see §3.5. Note `build/validate.py` passed green, so it does **not** enforce version monotonicity; this would have shipped silently.

---

## 5. Leading-word regressions (rubric §3 — use the token, not a synonym)

| File | Regression |
|---|---|
| 4a | `[[L-xxx]]/[[A-xxx]]` references → "vulnerability/audit refs" (law tokens synonym-swapped out of the PR-body spec) |
| 2b | `seam` → "boundaries"; `depth / deep / shallow` analysis instruction dropped entirely (Path C) |
| 3d | `[[G-xxx]]` citation dropped from Avoid-drift rename |
| 1b | `relentless` dropped from description (body uses "Grill" consistently, but the palette token is gone; shipped skill registration still says "relentlessly") |
| 4b | `[[A-003]]` + "deletion test" heuristic removed |
| 1c | `Breadth-First Grilling` → `Breadth-First Scan` (token preserved elsewhere — low severity) |

**Shared pointer loss:** both `1a` and `1b` dropped the `.agents/rules/okf-protocol.md` reference when compressing "Prepend OKF frontmatter per …" — worth restoring (context pointer the agent otherwise must recall from memory).

---

## 6. Frontmatter & build status

- **Version bumped:** 15/16 files correct. **Only `4b` regressed** (1.0.6 → 1.0.5).
- **Timestamp:** all → `2026-07-09`. Files already at that date (`1b`, `1c`, `3b`, `3c`, `3z`, `4a`) were not re-stamped, but the value equals the current date so they are effectively compliant.
- **`dist/` rebuilt:** yes — both `dist/claude-code/commands/` and `dist/antigravity/workflows/` regenerated; line counts match `src/`. **Exception:** `1b`'s shipped skill registration still reads "Interview the user relentlessly…", suggesting a description-source that the src edit didn't reach — verify the dist description matches intended.
- **`build/validate.py`:** **green** (19 + 17 invocables, 9 external skills). Note it does not catch the `4b` version regression.

---

## 7. Scope creep (not in the prompt)

The prompt asked to lean **workflows 0–4** using the rubric as *reference*. The branch also **edited the rubric itself**:
- `README.md` → added new **§4.5 "Word-Level Economy"** (article/preposition/filler-verb audits, etc.); v1.2.0 → 1.3.0.
- `glossary.md` → added "Article/preposition audit" + "Cross-workflow boilerplate" entries; v1.0.0 → 1.1.0.

Rubric integrity is preserved (the "Never prune:" line and leading-word palette are untouched, and §4.5 carves out "unless they prevent a documented agent failure mode"). But this is a **self-justifying change** — the governing standard was amended to sanction the cutting style then applied to `4a`/`4b`. Flag for explicit review; consider splitting it into its own change so the workflow-leaning and the rubric-amendment are decided separately.

---

## 8. What's exemplary (keep as the pattern)

- **`3c_sprint-planning`** — halved word count with **zero** load-bearing loss and every leading token intact. This is the target the other files should match.
- **`1b` / `1c`** — the flagged files: human-centered prose genuinely removed, process fidelity (interview loop completion criterion, discovery brief, `[[G-xxx]]` output, RAT guardrail) intact.
- **`3d`** — the micro-tdd delegation preserved exactly (the canonical must-keep), even though the gate around it was over-cut.

---

## 9. Suggested fix order

1. **Restore 3 deleted/gutted guardrails & contracts** (`3a` auditor guardrail, `1a` refute guardrail, `3b` coverage contract + DEFERRED guard) — highest risk, verbatim restores.
2. **Reconcile `4b` against `main`** — decide rewrite-vs-prune; fix the version regression; restore the `issue-templates.md` pointer and the universal do-not-modify invariant.
3. **Restore `3d` enforcement phrases** ("exhaustive", "never silently ship", "list each by name") + `[[G-xxx]]`.
4. **Fix the `1a` duplicated-clause bug.**
5. **Restore leading-word tokens** (§5) and the shared `okf-protocol.md` pointer.
6. **Restore `2a` validate specifics** ("with rationale", §12 enumeration, §4/§7/§12 placement rule) and `3a` growth-loop + Phase-1-no-writes.
7. **Decide on the rubric amendment** (§7) separately from the workflow leaning.
8. Rebuild `dist/` and re-run `validate.py`; verify the `1b` shipped description no longer says "relentlessly" if that was intended to change.
