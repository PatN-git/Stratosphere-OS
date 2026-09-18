# Plan — PR #107 Review Response

**Status:** Applied on `feat/spec-conformance-v4` (PR #107). All 13 threads answered on GitHub.
**Input:** 13 inline comments from @PatN-git on PR #107, 2026-09-17.
**Shape:** 11 of 13 are one theme — *prose economy*: the constitution and several skills explain host differences and guard against agent mistakes at a length that costs tokens on every load. Two are questions of fact.

Ordered by what I'd do first, not by file.

---

## Group 1 — Fix now, cheap and uncontested (4 comments)

### 1.1 `4a:77` — "step 7 is now very long and complex"
**Agreed — this is my own regression.** Step 7 is now ~1,950 characters in one numbered step: a 699-char line plus five sub-bullets I appended for the Feature Acceptance Audit.

**Fix:** extract the audit spec to `src/references/feature-acceptance-audit.md`, exactly as `terminal-sync-invariant.md` already handles the sync gate's heal protocol. Step 7 keeps one sentence and a pointer:

> → run the **Feature Acceptance Audit** (`references/feature-acceptance-audit.md`), then mark the feature PR ready…

Step 7 drops back to roughly its pre-change length; the detail loads only when the gate actually fires. `4a` 1.2.0 → 1.2.1.

### 1.2 `1a:97` + `1b:115` — "It already carries `type: research` — do not prepend a second one. Is this needed?"
**Agreed, cut both.** "Write the template's Artifact frontmatter block **verbatim**" is already unambiguous. A negative instruction naming the exact wrong action is a known way to *suggest* it. Two lines, two skills, no behaviour change.

### 1.3 `1a:103` — "— it supersedes the body `## Sources` section. Is this needed? If it's gone in this version…"
**It is not gone** — `## Sources` is still live in both templates (`research-competitive-template.md:113`, `research-problem-template.md:69`). So the clause is currently load-bearing: it tells the agent which of two places wins.

**But the underlying duplication is the real defect.** Frontmatter `sources:` is the OKF record; a body `## Sources` section is a second, unvalidated copy of the same data that some agent will eventually fill instead.

**Fix (better than deleting the sentence):** remove `## Sources` from both templates, *then* drop the clause — it has nothing left to supersede. Resolves the comment and removes the ambiguity that made the clause necessary.

### 1.4 `src/dev-skills/improve-workflows-skills/SKILL.md:2` — "where is the glossary?"
**It exists**: `docs/improve-workflows-skills/glossary.md`, referenced from the skill at line 23.

One real nit: it lives in repo `docs/`, not in the skill's own `references/`, which is the v4 convention every other skill now follows. This skill is dev-only and never ships to a consumer project, so nothing is broken — but it is the one skill that doesn't look like the others. **Recommend:** move it to `src/dev-skills/improve-workflows-skills/references/glossary.md` for consistency, or leave and accept the exception. Low stakes either way.

---

## Group 2 — Constitution compression (4 comments, one coordinated edit)

`AGENTS.md` is loaded on **every** turn in **every** consumer project. It is the highest-leverage file in the repo for token economy, and four comments land on it.

### 2.1 `AGENTS.md:14` + `AGENTS.md:69` — host-enforcement detail, stated twice
§1 carries the full enforcement matrix inline (`disable-model-invocation` / `triggers` / `openai.yaml` / Antigravity caveat); §8 then restates the Antigravity caveat at greater length.

**These two comments have one fix.** §1 keeps the *rule*; §8 keeps the *mechanism*:

> **§1:** …These dictate the step-by-step lifecycle. **Do not execute them autonomously.** Enforcement is host-dependent and, on Antigravity, advisory only — see §8.

and §8 gets a 6-row table (host → field → enforced?) replacing both the §1 matrix and the §69 paragraph.

On your "*this line is not needed yet*" for `:69` — I'd **keep the fact, lose the paragraph.** "Antigravity can model-invoke a HITL skill" is a real hole that will bite someone; a table row costs ~8 tokens and the current paragraph costs ~90. Deleting it outright is the one change here I'd push back on.

### 2.2 `AGENTS.md:40` — Documentation-artifact exception "seems long"
**Agreed.** 91 words to say: one generated doc per run, never code, default branch, local if no remote. Compress to ~30 while keeping all four constraints — they are load-bearing, the prose around them isn't.

### 2.3 `AGENTS.md:67` — "can we explain this rule section better so it is truly host agnostic — do research how the others process rules"
**Agreed, and it needs the research you asked for.** The current line is a list of vendor mechanisms (`trigger`/`globs`, `paths:`, "the rest read this file"), which is the opposite of host-agnostic — it will rot as each vendor changes.

**Approach:** spike how Cursor, Codex, Devin, OpenClaw and Copilot actually load persistent rules today, then rewrite as *one rule with a placement table*, the same shape §8's skills line already uses successfully: one canonical body, placement differs, content never does. Deliverable is a short findings note plus the rewritten line.

This is the only item in the plan that is research-gated — I'd do Groups 1 and 3 first so it doesn't block them.

---

## Group 3 — Questions of fact (2 comments)

### 3.1 `2b:86` — "do any of the status changes have impact on the GitHub Projects integration?"
**No integration exists in StratOS today** — nothing in the repo reads or writes a Projects board; status lives in issue labels and `.memory/BACKLOG_MAP.md`, mirrored by `reconcile.py`.

The relevant context: a proven label→Projects sync Action exists in **CleanTechHub** and has long been the candidate to port here. If it lands, it will key on exactly the `status:*` labels these workflows set — so the answer becomes *yes*, and the label vocabulary becomes an integration contract rather than an internal convention.

**Recommend:** no change to `2b`. Worth its own issue for the port, so the dependency is recorded before someone renames a label.

### 3.2 `CLAUDE.md:2` — "do we need a similar CLAUDE.md / GEMINI.md for CODEX, Cursor, Devin?"
Today: `AGENTS.md` is the body; `CLAUDE.md` and `GEMINI.md` are 2-line pointers to it.

Codex reads `AGENTS.md` natively, so it needs nothing. Cursor and Devin have their own conventions that may or may not require a pointer file. **This is the same research as 2.3** — same hosts, same question (how does each host load always-on context?), and the answer determines both the rules-placement table and whether two more pointer files are needed. **Fold into 2.3 and answer once.**

---

## Sequencing

| Order | Work | Blocked by |
|---|---|---|
| 1 | Group 1 (4 fixes) | nothing |
| 2 | Group 2.1 + 2.2 (AGENTS.md compression) | nothing |
| 3 | Host-rules research spike | nothing, but do after 1–2 |
| 4 | Group 2.3 + 3.2 rewrite | spike |
| 5 | Issue for the Projects-sync port (3.1) | nothing |

Groups 1–2 are prose-only, land in this PR, and need `build.py` + `check.sh`. The spike and its rewrite are better as a follow-up than as more scope on a MAJOR already under review.

## Outcome

All 13 addressed in #107. Two departures from the plan as written:

- **`0a:10` (OKF `timestamp` vs `generated`) was missing from this plan** and is comment 13. Answered, no change: `okf-protocol.md` §1 puts skills, rules, constitution and `src/*` out of OKF scope, so their `timestamp:` is a build field, not a retired change-record. Unifying would touch 65 files and make skills carry a field they're exempt from — a throwaway migration after merge if wanted, not agent passes.
- **The glossary move (1.4) was attempted and reverted.** `docs/improve-workflows-skills/` is a deliberate self-contained pair — `README.md` links `glossary.md` four times and says so at `README.md:147`. The skill is dev-only and never ships; the pair beats matching the shipped-skill layout.

Filed from the review: **#109** (port the CleanTechHub label→Projects sync Action) records that `status:*` labels become an integration contract the moment it lands.

Gate after the changes: `VALIDATION OK`, 314 passed, verify_scripts / plan-html / install-harness L1 98-0 all green, `dist/` rebuilt for both hosts.
