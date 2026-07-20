# Plan — Subagent-Dispatch Token Efficiency

**Status:** Reviewed (critic feedback folded in) — ready to execute.
**Target:** Fold into PR #101 (branch `feat/lifecycle-context-triggers`, OPEN/MERGEABLE), VERSION 3.0.0.
**Origin:** A `/0d` nightly consolidation in a live project surfaced four dispatch-efficiency insights. This plan generalizes the sound ones inline and explicitly rejects one.

> **Critic pass applied.** A skeptical review challenged v1 of this plan. Changes carried over: (a) dropped the proposed shared reference in favor of inline guidance — speculative abstraction for ~2 consumers; (b) the two 4a auditors now get *different* input framing (full files vs diff); (c) merge-base becomes a non-fatal fallback chain, not one command; (d) inventory completed (1c added, 3a label corrected); (e) token framing right-sized — the real win is 4b; (f) the CI assertion targets the anti-discovery *semantic*, not a heading/filename.

---

## 1. Why

When a workflow hands work to an auditor subagent, some dispatchers pass **generic input categories** and let the subagent *discover* concrete artifacts:

- **4a Standards Auditor** — `Input: slice diff (new/modified files only)` → the subagent reconstructs the diff itself.
- **4b Staff-Level Architect** — audits a *target directory* → the subagent sweeps it file-by-file. **This is the dominant avoidable cost** (a directory sweep is many `list_dir`/read calls the parent could pre-resolve).

The parent already has cheap answers (branch, slice, changed files). By contrast, the **4a Business-Logic Auditor** and **3b / 2b** already pass explicit inputs — they're the reference pattern, not the problem.

### The four nightly insights, adjudicated

| # | Insight | Verdict |
|---|---|---|
| 1 | **Direct file-path injection** — parent computes concrete paths; subagent never discovers. | **Adopt** (inline in 4a Standards + 4b). |
| 2 | **Combine the two 4a auditors into one pass.** | **Reject.** Conflicts with the deliberate two-auditor decision locked into 4a + `tests/test_subagent_spawning.py`. Each guardrail is that agent's entire contract. #1 removes the duplicate-*discovery* cost that was #2's only real motivation — so the token argument for merging evaporates. |
| 3 | **Pass the `git diff` inline in the prompt.** | **Adopt in modified form.** Pass the diff *command* + path list, not pasted content; the subagent runs one scoped `git diff`. Raw-diff inlining reserved for trivially small diffs. |
| 4 | **Tighten 4a guidance so the parent pre-computes audit targets.** | **Adopt** as an explicit "resolve targets before invoke" step. |

### Answer to the standing question ("copying changes inline, or telling them where to read?")

**Telling them where to read.** Default is pointers: explicit paths, plus (for diff-oriented auditors) the exact `git diff` command the subagent runs. We do **not** paste file/diff content into the prompt, except a bounded small-diff exception.

---

## 2. How — inline convention (no new file)

There is **no new reference file.** The rule is thin, cited by effectively two files, and its git commands must stay host-adaptable (illustrative, not hard-baked) — which guts the DRY case for centralizing. Existing references (`confidence-scale.md`, `code-smell-baseline.md`) are substantive multi-consumer rubrics; a dispatch convention is not that. So we state the convention inline where it applies (AGENTS §5: Simplicity First, no speculative abstractions).

**The convention (applied inline in 4a Phase 2 + 4b):**

- **Resolve targets in the parent; never make the subagent discover.** The dispatching workflow passes concrete artifact paths; the subagent must not run repo-wide discovery (`grep -r`, directory sweeps) to *locate* its inputs.
- **Framing differs by auditor role:**
  - *Business-logic / correctness / architecture-shape* auditors get **named full-file paths** (issue/PRD, design doc, test files, impl files). They need whole-file context; a diff is optional orientation only — never "review changed lines first."
  - *Standards / code-smell* auditors get the **changed-file list + a scoped diff command** as their primary surface (they judge the delta).
- **Diff by command, not paste.** Where a diff is used, instruct the subagent to run `git diff <base>...HEAD -- <paths>` rather than pasting content. Small-diff exception: a few lines may be inlined when the read round-trip clearly costs more than the tokens.
- **Base ref is a non-fatal fallback chain**, not one command. Prefer merge-base with the tracked upstream; fall back to the local default branch; if neither resolves (offline / `origin` unfetched / AFK `BT-LOCAL`), fall back to "files changed on this branch" — and **never abort the audit** because the base ref is unresolvable. Phrase as guidance the agent adapts to `main`/`master` and host.
- **Contracts stay separate.** Inputs only — never merge the two 4a auditor roles (rejection of nightly #2). Injected targets already remove the duplicate-discovery cost.

---

## 3. What — per-workflow changes

| Workflow | Change | Bump |
|---|---|---|
| **`src/workflows/4a_verify-and-ship.md`** | Phase 2: add a "resolve `Audit Targets` before invoke" step — parent computes the changed-file list (fallback chain above). **Business-Logic Auditor**: keep full named files (issue/PRD, design doc, tests, impl) — make them explicit paths, no "diff-first". **Standards Auditor**: pass changed-file list + the scoped `git diff` command as its surface. **Two separate subagents retained.** | patch |
| **`src/workflows/4b_audit-architecture-drift.md`** | Parent passes the explicit changed-file list for the target directory (fallback chain) instead of "scan the directory"; subagent must not sweep to locate inputs. | patch |
| **`tests/test_subagent_spawning.py`** | Add a **semantic** assertion: 4a Phase 2 instructs the parent to resolve/pass concrete audit targets and that the subagent must not run repo-wide discovery. Do **not** assert a heading label or filename. Keep the two-subagent + guardrail asserts. | n/a |
| `src/workflows/3b_create-issue.md` | Compliant reference pattern (explicit PRD/design paths). **No edit.** | — |
| `src/workflows/2b_interface-design.md` | Compliant (explicit design-doc path). **No edit.** | — |
| `src/workflows/3a_version-planning.md` | Compliant *enough* — has a minor discover branch (`else the candidate features' BACKLOG_MAP rows + PRDs`), but it's a proposal audit, low cost. **No edit.** | — |
| `src/workflows/1c_concept-map.md` | Two dispatchers (research subagent ~L56; RAT Audit ~L72). Research = web (no file discovery); RAT gets the brief path. **No edit** — no discovery gap. | — |
| `src/workflows/1b_concept-framing.md`, `1a_research.md` | Inline / web inputs. **No change.** | — |
| `src/workflows/3z_afk-loop.md` | Step 2B already passes `BT-<padded>` + design-doc path to `/4a`, which self-computes targets (robust via the fallback chain). **No change.** | — |

**Scope discipline:** material edits touch **only 4a + 4b** (the two real discovery gaps) plus one test. No new file. Two file bumps, not four.

---

## 4. Verification

- `python build/build.py` — regenerate both host bundles.
- `python build/validate.py .` — per-file bump enforced vs committed.
- `python build/bump_guard.py`
- **Full CI suite locally** (lesson from the earlier PR-101 CI break — don't push on a partial local run): `test_subagent_spawning.py`, `test_plan_html_delegation.py`, `verify_scripts.py`, `verify_plan_html.mjs`, plus anything else in `.github/workflows/build-guard.yml`.
- Confirm dist-drift check passes (4a/4b changes propagated to both `dist/claude-code` and `dist/antigravity`).

**Success = green `verify-dist` on the pushed commit; PR #101 body updated to note the dispatch-efficiency change.**

---

## 5. Defended decisions (from the critic pass)

- **Reject nightly #2** (merging the auditors) — correct and test-locked; injecting targets removes its only motive. Keep the two-guardrail contract.
- **Pointers over paste** — avoids prompt bloat + stale content.
- **Leave compliant workflows untouched** — Surgical Edits; avoids needless bumps in an already-large MAJOR.
- **3z needs no target-passing** — delegates to /4a, which self-computes robustly once the fallback chain lands.

## 6. Residual risk

- These learnings are orthogonal to lifecycle/context/triggers; folding into a MAJOR broadens it. Acceptable (user's call) because 4a/4b are already modified in #101.
- The token win is modest for 4a (Standards saves a couple of calls) and real for 4b (eliminates a directory sweep). Framing is right-sized accordingly.
