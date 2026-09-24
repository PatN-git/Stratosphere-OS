# Plan — Unified Audit Pipeline: Report → Proposal → Maintenance Epic (4b + 4c → 3b)

**Status:** Approved for implementation. Not yet implemented.
**Branch:** `feat/spec-conformance-v4` — ships **inside PR #107** (v4.0.0). Build directly on that branch; no separate PR.
**Targets:**

| File | Version |
|---|---|
| `src/references/audit-to-slices.md` | **new** 1.0.0 |
| `src/references/arch-drift-report-template.md` | **new** 1.0.0 |
| `src/references/health-audit-report-template.md` | 2.0.0 → 2.1.0 |
| `src/references/feature-acceptance-audit.md` | 1.0.1 → 1.1.0 |
| `src/workflows/4b-audit-architecture-drift.md` | 1.0.9 → 1.1.0 |
| `src/workflows/4c-codebase-health-audit.md` | 1.0.0 → 1.1.0 |
| `src/workflows/3b-create-issue.md` | 2.4.0 → 2.5.0 |
| `src/workflows/0d-nightly-consolidation.md` | 1.1.2 → 1.1.3 |
| `README.md` (lifecycle table row 4 only) | — |
| `tests/test_audit_pipeline.py` | **new** |

Plugin `VERSION` in `build/build.py` stays **4.0.0** — this lands in the same release.

---

## 0. Read first (fresh-session orientation)

- **What you are editing.** StratOS lifecycle skills. Sources live in `src/workflows/*.md` (lifecycle skills) and `src/references/*.md` (shared references). **Never hand-edit `dist/`** — `python build/build.py` regenerates it.
- **How references ship.** A skill cites a reference as `references/<file>.md` (its own copy) or `.agents/skills/<skill>/references/<file>.md` (absolute — required whenever the path is handed to an isolated subagent). `build.py` walks citations transitively and copies each cited reference into every citing skill's `references/`. A new reference needs **no build change** — only a citation.
- **Versioning.** Every changed `.md` in `src/` bumps its frontmatter `version` and refreshes `timestamp` to the edit date. `validate.py` fails a changed dist artifact whose version did not move.
- **Load the dev playbook before editing:** invoke the `improve-workflows-skills` skill. Its **protected classes** (§4 of its playbook) apply to every edit below: sub-agent guardrails verbatim, leading-word tokens exact (`[UNCOVERED]`, `seam`, `[[A-xxx]]`), full context-pointer paths, one side-effecting write per numbered step with its own command literal.
- **Test-pinned phrases** — must survive unchanged (`tests/test_subagent_spawning.py`): in `4b`, `Context Isolation Rule`, `invoke an independent Staff-Level Architect subagent`, and the guardrail `Return findings + confidence only; do not modify production code or write refactor files (matches Phase 1/3 constraints).`

---

## 1. Problem

### 1.1 The two audits disagree on what they produce

| Skill | Durable findings artifact | Actionable slice proposal |
|---|---|---|
| `4c-codebase-health-audit` | `docs/audits/health-<YYYY-MM-DD>.md` (Phase 4.1) | **none** — Phase 5 tells the user to "create issues via /3b" by hand |
| `4b-audit-architecture-drift` | **none** — no history of drift per target | `.tmp/refactor-proposal.md`, Template B (Phase 3.1) |

### 1.2 Nothing consumes a proposal
`3b-create-issue` Phase 1.3 recognises two intake sources only: **PRD-sourced** or **raw idea/MVI**. `4b`'s hand-off lands on raw-idea, where:
- Phase 2.2 **Fallback (ODI absent): HALT** fires on every slice — audit findings carry no ODI score.
- Phase 2.4 Slice Draft Audit degrades to **No PRD** mode — soft `[UNCOVERED?]` against a restated intent, never against the findings.
- Phase 2.3 drafts to `.tmp/BT-<padded>-issue-drafts.md`, keyed to a parent that does not exist, so the proposal's Template B bodies are regenerated rather than minted verbatim.

### 1.3 Supporting defects
- **No stable finding IDs.** `health-audit-report-template.md` numbers `#` from 1 inside each impact table. No slice can cite the finding it resolves.
- **Path collision.** A single `.tmp/refactor-proposal.md` would be clobbered once two skills write proposals.
- **Retention breaks traceability.** `4c` Phase 4.3 deletes reports older than 90 days regardless of whether open issues still point at them.
- **Epics assume a PRD.** `4a`'s Feature Acceptance Audit (`feature-acceptance-audit.md`, Input) and `0d`'s "slicing incomplete" signal (`0d-nightly-consolidation.md`, Recommendation table) both read PRD content; an epic without a PRD breaks both.

---

## 2. Target end state

```
/4b <dir>  ─┐                                  ┌─ docs/audits/arch-<slug>-<date>.md    (durable findings, F-01…F-NN)
            ├─ scan → score → tier → ID ───────┤
/4c         ─┘                                  └─ docs/audits/health-<date>.md
                                  │
                                  ▼
                 .tmp/refactor-proposal-<report-stem>.md   (epic header + coverage map + Template B slices)
                                  │   HITL: user reviews, runs /3b-create-issue <proposal>
                                  ▼
       3b audit-sourced intake → Slice Draft Audit (every F-xx covered) → approval
                                  │
                 ┌────────────────┴───────────────────┐
         🔴 slices: standalone                 🟠/🟡 slices: sub-issues of ONE
         (own branch + PR, ship now)           type:maintenance epic (one feature PR)
                                                        │
                                  3d → 4a; at the epic's last slice the Feature
                                  Acceptance Audit checks the report's claimed F-xx
```

Both audits write a findings artifact under **`docs/audits/`** (durable, OKF `type: audit-report`, already registered for `docs/audits/*.md` in `src/rules/okf-protocol.md`). Both write a proposal under **`.tmp/`** (ephemeral — once minted, the issues are the durable record).

---

## 3. Decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | `4b` assigns the **same four impact tiers** as `4c` (🔴 Critical / 🟠 High / 🟡 Medium / ⚪ Low) | One findings contract, one ICE mapping; `3b` never HALTs on audit input. |
| D2 | Non-Critical slices from one proposal are grouped under **one `type:maintenance` epic**; 🔴 slices stay **standalone** | AGENTS.md §4: one branch + PR per parent. Standalone would mean N PRs and no feature-level acceptance gate. Critical carve-out: a security fix must not wait behind Medium work in the same PR. |
| D3 | Epic only when the proposal has **≥ 2 non-🔴 slices**; one slice → standalone | An epic of one is ceremony. |
| D4 | The **audit report is the epic's spec of record** (replaces the PRD) | Lets `4a` and `0d` keep their logic with one input branch each. |
| D5 | Ships **in PR #107**, built on `feat/spec-conformance-v4` | Additive; #107 already renamed every path this touches. |

---

## 4. New file — `src/references/audit-to-slices.md`

Cited by `4b`, `4c`, `3b`, and `feature-acceptance-audit.md`. It must **not** cite either report template (the transitive walk would ship them into `3b`). Frontmatter: `description`, `version: "1.0.0"`, `timestamp`. Sections, in order:

### §1 Finding IDs
`F-01…F-NN`, assigned once per report after all filtering, ordered Critical → Low then confidence descending. IDs are never reused or renumbered after the report is written. External citation form: `<report-stem>#F-07` (stem = filename without `.md`).

### §2 Impact tiers
Move the **Impact Categories** table out of `health-audit-report-template.md` into here verbatim (Critical/High/Medium/Low criteria + the sentence *"Impact is independent of confidence…"*). Add a second column set for architecture drift:

| Impact | Health (`4c`) | Architecture drift (`4b`) |
|---|---|---|
| 🔴 Critical | (existing text) | A documented `[[A-xxx]]`/`[[DR-xxx]]` law ignored on an auth, payment, or data-mutation path |
| 🟠 High | (existing text) | A leaked `seam` or domain-boundary violation on a critical user path |
| 🟡 Medium | (existing text) | God-module, dependency-inversion violation, or duplicated logic across ≥ 3 modules |
| ⚪ Low | (existing text) | Locality or naming drift with no behavioural risk |

### §3 Findings row contract
Both report kinds use one table shape per impact section:

`| ID | File | Line(s) | Finding | Evidence | Confidence | Law | Recent? | Suggested Direction |`

- `Evidence`: the quoted symbol, signature, or ≤ 3-line excerpt that proves the finding.
- `Law`: `[[A-xxx]]`/`[[DR-xxx]]` that exist in `.memory/`, else `—`. Never a placeholder ID.
- `Recent?`: `✓` or blank in `4c`; always `—` in `4b`.

### §4 Proposal contract
- **Path:** `.tmp/refactor-proposal-<report-stem>.md`.
- **Line 1, exactly:** `Source: docs/audits/<report-stem>.md`
- **Then, in order:**
  1. `## Epic` — `Title:` (`Maintenance: <scope> — <date>`), `Area:` (one registry `area:` label), `Milestone (proposed):` (§8), `Overview:` one paragraph. Omit the section when D3's threshold fails.
  2. `## Coverage` — table `| Finding | Impact | Resolution |`, **one row per F-xx in the report**; Resolution is `Slice <N>` or an exclusion token (§5).
  3. `## Slice <N> — <title>` per slice — a complete Template B body per `references/issue-templates.md`, with these audit-specific rules:
     - **Current state / Problem** opens with `Resolves: <report-stem>#F-03, <report-stem>#F-07`, then each resolved finding's File/Line(s)/Evidence/Law **copied inline** (the report is a pointer, never the only copy).
     - **ICE Priorities** per §6.
     - **The Path:** mark untouched layers `N/A`.
     - **Acceptance Criteria:** one verifiable check **per resolved F-xx** proving it no longer reproduces (test, command, or grep with expected output), plus the Verification command. Time-to-Value and Stress Cases lines read `N/A — audit-sourced (no design doc)`.
     - **Dependencies → Parent:** `BT-<epic>` for epic children; `—` for 🔴 standalone slices. Blocked-by uses `BT-<slice:N>` as today.
- **Clustering:** group findings into slices by module / `seam`. Apply `3b`'s minimum-slice floor — never one slice per finding by default; never merge findings across unrelated modules to save a slice.

### §5 Coverage gate
Every F-xx maps to exactly one `Slice <N>` or one token: `[OPPORTUNISTIC]` (⚪ default), `[DEFERRED: <reason>]`, `[WONTFIX: <reason>]`. Any unmapped finding is `[UNCOVERED]`. A proposal with an open `[UNCOVERED]` is incomplete — never summarise as "mostly covered".

### §6 ICE mapping (a rule, not an inference)
- **Impact:** 🔴 3.0 · 🟠 2.0 · 🟡 1.0 · ⚪ 0.5 — a slice takes the **highest** tier among its resolved findings.
- **Confidence:** the **lowest** confidence among its resolved findings → ≥ 90 `100%` · 80–89 `80%` · 60–79 `50%`.
- **Size:** unchanged — prompted by `3b` Phase 2.2.

### §7 Critical carve-out and epic threshold
🔴 slices never take a parent. The epic is proposed only when ≥ 2 non-🔴 slices exist; otherwise every slice is standalone and `## Epic` is omitted.

### §8 Milestone default
The `vX.Y.0` of the `[ACTIVE]` release in `docs/ROADMAP.md`; if absent, `v1.0.0`. Confirmed by the user at `3b` Phase 2.5 approval. Maintenance epics never need a `3a` MAJOR/MINOR decision.

### §9 Retention pin
A report is **pinned** while any open issue body cites its path. Resolve the pinned set with:
```bash
gh issue list --state open --limit 500 --json body --jq '.[].body' | grep -oE 'docs/audits/[A-Za-z0-9._-]+\.md' | sort -u
```
`gh` absent or unauthenticated → **skip retention entirely** this run and say so (fail safe: keep). Never delete a pinned report.

---

## 5. New file — `src/references/arch-drift-report-template.md`

Owned by `4b` (mirrors `health-audit-report-template.md` for `4c`). Frontmatter: `description: Report template for 4b-audit-architecture-drift.`, `version: "1.0.0"`, `timestamp`. Content: the report skeleton, written to `docs/audits/arch-<target-slug>-<YYYY-MM-DD>.md` (`<target-slug>` = target path with `/` → `-`, leading `-` stripped):

```markdown
---
type: audit-report
title: "Architecture Drift — <target> — <YYYY-MM-DD>"
status: stable
generated:
  by: 4b-audit-architecture-drift
  at: <ISO 8601>
---

# Architecture Drift — <target> — <YYYY-MM-DD>

## Executive Summary
| | |
|:---|:---|
| Target | <target directory> |
| Files scanned | N |
| Dropped (backlog collision) | <BT-ids or "none"> |

| Impact | Count |
|:---|---:|
| 🔴 Critical | N |
| 🟠 High | N |
| 🟡 Medium | N |
| ⚪ Low | N |
| **Total** | **N** |

## 🔴 Critical
(findings table per audit-to-slices §3)
## 🟠 High
## 🟡 Medium
## ⚪ Low

## Next Step
Proposal: `.tmp/refactor-proposal-<report-stem>.md` → review, then `/3b-create-issue .tmp/refactor-proposal-<report-stem>.md`.
```

Omit empty impact sections.

---

## 6. File-by-file edits

### 6.1 `health-audit-report-template.md` → 2.1.0
- **Delete** the `## Impact Categories` section; replace with one line: `Impact categories: references/audit-to-slices.md §2.` *(This reference is only shipped into `4c`; `4c` also cites `audit-to-slices.md` directly, so the pointer resolves.)*
- **Findings tables:** replace the header `| # | Pass | File | Line(s) | Finding | Confidence | Recent? | Suggested Fix |` with `| ID | Pass | File | Line(s) | Finding | Evidence | Confidence | Law | Recent? | Suggested Direction |` (row contract §3 plus the `4c`-only `Pass` column). Update the example row to `F-01` and fill the new columns.
- **Recommended Next Steps:** replace the four per-tier bullets with the Next Step block from §5 (health wording). Keep the `/4b-audit-architecture-drift` line and the `✓ Recent` line.
- `.last-run.json` schema: unchanged.

### 6.2 `4c-codebase-health-audit` → 1.1.0
- **`description`:** replace *"Produces a durable audit report categorized by impact; the developer drives fixes via /3b and /3d."* with *"Produces a durable audit report in docs/audits/ and a slice proposal for /3b-create-issue."* Keep the user-only sentence. ≤ 1024 chars.
- **`[!IMPORTANT]` block (line ~18):** state it writes `docs/audits/health-<YYYY-MM-DD>.md`, prunes unpinned reports there (Phase 4.3), and writes one `.tmp/refactor-proposal-<report-stem>.md`. Keep "Never modify production code, create issues, commit, or push" and the "not purely read-only" sentence.
- **Phase 3.2:** repoint to `references/audit-to-slices.md` §2.
- **New Phase 3.5 — Assign IDs:** `F-01…` per `references/audit-to-slices.md` §1, after 3.4.
- **Phase 4.3 Retention:** delete `docs/audits/health-*.md` older than 90 days **except** reports in the pinned set (`references/audit-to-slices.md` §9, command literal inline). `gh` unavailable → skip and output `[SKIP] Retention — gh unavailable; no reports deleted.`
- **New Phase 5 — Refactor Proposal** (own numbered steps):
  1. Scope: 🔴 + 🟠 + 🟡 findings; ⚪ → `[OPPORTUNISTIC]`. The trigger prompt may widen or narrow tiers.
  2. Cluster and write `.tmp/refactor-proposal-<report-stem>.md` per `references/audit-to-slices.md` §4–§8.
  3. **Completion criterion:** every F-xx appears in `## Coverage`; zero `[UNCOVERED]`.
- **Phase 5 Handoff → renumber to Phase 6.** Replace the three "Fix Critical / Create issues / Low" lines with:
  ```
  Proposal: .tmp/refactor-proposal-<report-stem>.md  (<S> slices, epic: yes|no)
  Review it, then run /3b-create-issue .tmp/refactor-proposal-<report-stem>.md
  ```
- **Clean Exit:** also write no proposal.

### 6.3 `4b-audit-architecture-drift` → 1.1.0
- **`description`:** *"Macro Audit. Scans a targeted directory for high-confidence structural drift, writes a durable findings report to docs/audits/, and generates a slice proposal for /3b-create-issue."* + the existing user-only sentence.
- **Phase 1 `_CONSTRAINTS_`:** add `- Write only docs/audits/arch-*.md and .tmp/.` Keep the existing four bullets.
- **Phase 2 `_INPUT_`:** add `.agents/skills/4b-audit-architecture-drift/references/audit-to-slices.md` (absolute path — it may be handed to the subagent). **Output Contract** bullet: findings + confidence **+ impact tier per §2**. Guardrail sentence: **unchanged, verbatim**.
- **Confidence section / Clean Exit Rule:** unchanged.
- **Phase 3 Output → replace with own-step writes:**
  1. Assign IDs per `references/audit-to-slices.md` §1.
  2. Write `docs/audits/arch-<target-slug>-<YYYY-MM-DD>.md` per `references/arch-drift-report-template.md`.
  3. Write `.tmp/refactor-proposal-<report-stem>.md` per `references/audit-to-slices.md` §4–§8 (all tiers in scope; ⚪ may be `[OPPORTUNISTIC]`). Completion criterion as `4c` Phase 5.3.
  4. Retention: delete `docs/audits/arch-*.md` older than 90 days except the pinned set (§9 command inline); `gh` unavailable → skip with the same `[SKIP]` line.
  - Keep the existing CONSTRAINT bullets (generate only after filtering + collision check; double-bracket law links) under step 3.
- **Phase 4 Handoff:** 2-line summary of flagged components **+ both paths**, then the same `/3b-create-issue <proposal>` line as `4c`. Keep "Await human instruction".
- The old `.tmp/refactor-proposal.md` path must not appear anywhere after this edit.

### 6.4 `3b-create-issue` → 2.5.0 — third intake: audit-sourced
- **Hand-off contract paragraph:** add *"Audit-sourced → the trigger names `.tmp/refactor-proposal-<stem>.md`; the proposal is the drafts file; audits coverage against the `Source:` report per `references/audit-to-slices.md`."*
- **Phase 1.2 (defensive epic promotion):** add `Audit-sourced: skip.`
- **Phase 1.3 Scope:** add the branch: `Audit-sourced → load the proposal and the report named on its line 1. Scope is every F-xx in the report.`
- **Phase 2.1–2.3:** add `Audit-sourced: skip 2.1 and 2.3 (the proposal is the draft); in 2.2 take Impact and Confidence from references/audit-to-slices.md §6 — the ODI fallback HALT does not apply; still prompt for Size.`
- **Phase 2.4 Slice Draft Audit:** add an audit-sourced input line (reads the proposal + the report, fresh from disk; PRD/research precedence clause does not apply) and redefine:
  - **Breadth:** every F-xx in the report maps to a slice or a §5 token; else `[UNCOVERED]`.
  - **Depth:** Template B-complete per §4 — `Resolves:` line present, evidence inline, one no-longer-reproduces AC per resolved F-xx.
  - Guardrail sentence: unchanged.
- **Phase 2.5 Approval:** audit-sourced also confirms the epic (title, area, milestone per §8) or its absence (§7).
- **Phase 3.3 pre-mint guard:** audit-sourced → run against the proposal path instead of `.tmp/BT-<padded>-issue-drafts.md`. Mint order gains step (b0): **mint the epic first** (below), then replace every `BT-<epic>` in the proposal with the returned ID; only then run (a).
- **Phase 3.4 Generate — epic mint (new sub-bullet, own command literal):**
  ```bash
  gh issue create --title "<Epic Title>" --label "tier:epic,type:maintenance,area:<x>,status:planned" --milestone "<vX.Y.0>" --body-file <tmp epic body>
  ```
  Epic body line 1 is the proposal's `Source:` line, followed by the Overview and the Coverage table. Epic slices then mint with the existing slice rules; sub-issue linkage per `references/github-issue-relations.md`. 🔴 slices: no parent, no sub-issue link. Slice `type:` = `type:bug` for Security/Correctness findings, else `type:maintenance`.
- **Phase 3.5 Backlog Sync:** epic row: `| BT-<n> | <title> | planned | area:<x>, tier:epic, type:maintenance | vX.Y.0 | — | — | ICE: - | <cited laws or —> |`. Slice rows as today. (Report paths go in issue bodies, never in `Ref` — BACKLOG_MAP rule.)
- **Phase 3.6 terminal gate:** `--ids` includes the epic.

### 6.5 `feature-acceptance-audit.md` → 1.1.0
Append to **Input**: *"Audit epic — the parent body's first line is `Source: docs/audits/<stem>.md` and no PRD exists → input is that report's F-xx rows claimed by the epic's slices (their `Resolves:` lines), per `references/audit-to-slices.md`, plus the whole-feature diff. Scope: each claimed finding no longer reproduces in the diff."* Verdict section unchanged. (`4a/SKILL.md` itself is untouched; the new citation fans `audit-to-slices.md` into `4a` automatically.)

### 6.6 `0d-nightly-consolidation` → 1.1.3
In the Recommendation table, the "slicing **incomplete**" row: append *"— for an audit epic (body line 1 `Source: docs/audits/…`), compare child slices to the number of `Slice` resolutions in its Coverage table instead of PRD §6."* No other change.

### 6.7 `README.md`
Lifecycle table, row **4. Ship & Audit**, last column: `Quality gap report, traceable PR, health audit report` → `Quality gap report, traceable PR, audit reports (docs/audits/) + slice proposals`. Do not bump the README badge.

### 6.8 `tests/test_audit_pipeline.py` (new; pytest, no network)
Against both hosts' `dist/*/skills/`:
1. `4b`, `4c`, `3b` SKILL.md each cite `audit-to-slices.md`. *(Presence of the shipped copy is already covered by `test_skill_conformance.py::test_every_cited_reference_ships` — do not duplicate it.)*
2. No skill contains the retired literal `.tmp/refactor-proposal.md`.
3. `4b` and `4c` both contain `docs/audits/` and `.tmp/refactor-proposal-<report-stem>.md`.
4. `audit-to-slices.md` contains the tokens `[UNCOVERED]`, `[OPPORTUNISTIC]`, `Resolves:`, `Source: docs/audits/`.
5. `3b-create-issue` does **not** ship `health-audit-report-template.md` or `arch-drift-report-template.md` (guards the §4 no-cite rule).

---

## 7. Implementation order

1. `git checkout feat/spec-conformance-v4 && git pull`.
2. Invoke `improve-workflows-skills`.
3. Write `audit-to-slices.md`, then `arch-drift-report-template.md`.
4. Edit `health-audit-report-template.md` (moves §2 out — do this after step 3 so the content has a home).
5. Edit `4c`, `4b`, `3b`, `feature-acceptance-audit.md`, `0d`, `README.md`.
6. Add `tests/test_audit_pipeline.py`.
7. `python build/build.py` and commit `dist/` in the same commit as its sources.
8. Gate (§8). Fix and re-run until clean.
9. Commit (`feat(4b,4c,3b): unified audit pipeline — report, proposal, maintenance epic`), push `feat/spec-conformance-v4`.
10. Update PR #107 (§9) and set this plan's **Status** to `Implemented on feat/spec-conformance-v4 (PR #107).`

---

## 8. Verification

### Deterministic gate — must pass before push
| Check | Command |
|---|---|
| Full gate (build, validate, bump-guard, pytest, verify_scripts, plan-html, install-harness L1, dist drift) | `bash scripts/check.sh` |
| Pinned subagent phrases | covered by pytest (`test_subagent_spawning.py`) |
| No retired path | `grep -rn 'refactor-proposal\.md' src/ dist/` → no output |
| Fan-out | `ls dist/claude-code/skills/{3b-create-issue,4a-verify-and-ship,4b-audit-architecture-drift,4c-codebase-health-audit}/references/audit-to-slices.md` → four paths |

### Done criteria
- Every row of the Targets table changed and at its target version; `timestamp` refreshed.
- Every edit in §6 applied; every protected phrase from §0 intact.
- Gate green; `dist/` committed and drift-free.

### Behaviour — manual, pending first real use
The L3 lifecycle harness does not drive `4b`/`4c`; these stay unverified until run on a real project, and the PR text must say so:
- `/4c-codebase-health-audit` → report with global F-IDs + proposal with a full Coverage table.
- `/4b-audit-architecture-drift <dir>` → `arch-*` report + proposal.
- `/3b-create-issue <proposal>` → no ICE HALT; epic minted first; slices linked; 🔴 standalone; `reconcile.py --require-gh` → `[MIRROR-OK]`.
- One audit epic through `3d` → `4a`: the Feature Acceptance Audit reads the report, not a PRD.

---

## 9. PR #107 update

Add a section **"Unified audit pipeline (added late)"** to the PR body, after "Feature-level acceptance gate": the §1 problem in three bullets, the §2 diagram, D1–D4, and the **Not behaviourally verified** note from §8. Add the plan link. Do not rewrite other sections.

---

## 10. Out of scope / known limits

- **Branch/commit prefix for `type:maintenance`.** `3d` builds `<type>/BT-<parent>-<slug>` from the parent's `type:` label, and no mapping table exists (`feat` is the only abbreviation in use). Audit epics will branch as `maintenance/BT-<n>-<slug>` and commit as `maintenance(BT-<n>): …`. Accepted; normalising prefixes is a separate change.
- **`3a` treats maintenance epics like features** if it runs over them. Not changed — §8 assigns a milestone at mint, so `3a`'s "unassigned epic" trigger does not fire for them.
- **Epic body as data.** `4a` and `0d` key off body line 1 `Source: docs/audits/…`. A human editing it out reverts both to PRD behaviour. Accepted for v4.0.0.
- Not added: a `.last-run.json` for `4b` (dated filenames suffice); auto-running `/3b` from an audit (stays HITL per AGENTS.md §1); threshold changes (`4c` ≥ 60, `4b` ≥ 80).
