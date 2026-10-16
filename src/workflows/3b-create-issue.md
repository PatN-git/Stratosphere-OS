---
name: 3b-create-issue
description: "Standardize feature ideas into vertical slices with ICE prioritization. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "2.7.0"
timestamp: 2026-10-14
---

# Create issue

**Purpose:** Convert ideas into implementation-ready vertical slices synced with memory.

**Hand-off contract:** PRD-sourced → reads §1, §6, §7, §8, §10 and the parent's existing sibling slices; drafts full Build slices (only for items no sibling covers) to `.tmp/BT-<padded>-issue-drafts.md`, audits coverage + fidelity against §6 + §8, mints the approved drafts verbatim. Audit-sourced → the trigger names `.tmp/refactor-proposal-<stem>.md`; the proposal is the drafts file; audits coverage against the `Source:` report per `references/audit-to-slices.md`. Else checks against captured intent. Spikes skip drafting/audit.

## Phase 0: Load Memory
Run the `load-memory` skill to restore session context (read-only).

## Phase 1: Intake & Scope
1. **Intake:** Receive raw idea or MVI.
2. **Defensive epic promotion (idempotent guard):** If the parent epic is still `status:needs_spec` (a 2b promotion was missed or 2b was skipped), promote it `needs_spec → planned` now: `gh issue edit <parent> --remove-label "status:needs_spec" --add-label "status:planned"` and update its BACKLOG Status. No-op if already `planned` or further; skip for standalone slices with no parent. Audit-sourced: skip.
3. **Scope:**
   - PRD-sourced → load `docs/prds/BT-<padded>-<name>.md`, frozen design doc `docs/design/BT-<padded>-interface.md` and the discovery brief. Scope is PRD §1 (intent), §6, §7 (constraints), §8 + §10 and design blueprint; the brief supplies file-level facts, which the PRD keeps path-free.
     - Brief = the PRD frontmatter `discovery:` path (`—` = none); field absent → fallback: the `docs/discovery/*.md` (excluding `*.work.md` and `*.map.md`) whose frontmatter has `linked-prd: BT-<padded>`; if none, 2a's slug fuzzy-match (2a Phase 1 step 5).
   - Audit-sourced → load the proposal and the report named on its line 1; scope is every F-xx in the report.
   - Else raw idea/MVI is scope (no-PRD path). **Brief lookup:** a brief path the user names wins; else 2a Phase 1 step 5's slug match (several → user selects; none → no brief). Route by its frontmatter: `linked-prd: BT-<n>` → restart Phase 1 PRD-sourced for that BT; else `ready-for-prd` → name `/2a-write-prd` and HALT; `dropped` → HALT, proceed only on user confirmation; `exit-spike` → a Spike. An idea listed in its Decoupled Follow-ups seeds from Established Facts only.
4. **Siblings (PRD-sourced only; no PRD / audit-sourced / standalone: skip):** read `gh issue view <parent> --json subIssues` (`.nodes`, per `references/github-issue-relations.md`) and the BACKLOG rows with `Parent = BT-<parent>`; union by ID (gh offline → BACKLOG only). Existing Build-slice siblings already cover their scope (a Spike does not): Phase 2 drafts only §6/§8/design items no sibling covers.

## Phase 2: Slice, Draft & Audit
**Audit-sourced:** skip steps 1 and 3 (the proposal is the draft). In step 2, take Impact and Confidence from `references/audit-to-slices.md` §6 — the ODI fallback HALT does not apply; still prompt for Size, then write Size and the ICE Score (Phase 3 step 1 formula) into each slice's ICE Priorities in the proposal.
1. **Slices List:** propose breakdown per slice:
   - **Title:** short name.
   - **Logic/user story:** end-to-end path.
   - **Blocked by:** prerequisite slices (a real `BT-<n>` for an existing sibling).
   - **§10:** an open blocking Question (not a `migration:` item; incl. an `untested | running | failed` RAT; no PRD: the brief's Open Questions and Riskiest Assumption stand in, non-blocking ones → slice Notes) → a Spike in this list, before any drafting. Each `migration:`-tagged item → a Build slice listed first (Slices 1..k), a blocker of every slice that touches the contract it changes. One that removes or renames an existing contract follows expand/contract: the additive slice leads, the destructive step is its own later slice, Blocked by every slice that moves callers; every migration slice's AC includes a tested down path. Migration slices have no ODI, so the step-2 fallback HALT asks the user for Impact and Confidence.
   - **Inheritance:** inherit scope-class + ODI score from PRD §6. No slices for `[DEFERRED]` stories.
   - **Minimum-slice floor (value, not LOC):** do not emit a slice with no independent verification/demo value beyond its sibling — fold it into the sibling or keep the feature whole (a one-line change is rarely its own slice). Judge by vertical value, never line count. **Do not over-fold across surfaces** (e.g. merging a backend slice with its UI slice to save cost) — that yields a multi-file/UI slice that triggers the full independent audit anyway and erodes isolation; fold only a child that has no standalone verification value.
   - **Maximum-slice ceiling:** split a draft whose title joins two outcomes with "and", or that has >3 AC, 2+ independent subsystems, or ~5+ hand-written non-test, non-generated files.
   - **Escalation rule (no-PRD path, Build slices only):** not a small slice when the Build slices depend on each other or split one outcome (Blocked-by edges between them, or one Success State item across them), add a new UI surface, or need an ADR or add external cost. Say so, name `/2a-write-prd` (then `/2b-interface-design` for a UI surface or design decisions) and HALT until the user narrows the scope or overrides. Independent bundle slices pass.
2. **Prioritization Metrics (Spikes: skip; size fixed at `size:medium`):**
   - **Impact from ODI:** Map story ODI score to Impact:
     - `ODI < 5` → `0.25`
     - `5 <= ODI <= 8` → `0.5`
     - `9 <= ODI <= 12` → `1.0`
     - `13 <= ODI <= 16` → `2.0`
     - `17 <= ODI <= 20` → `3.0`
     - (Note: scope-class governs ordering; baseline sequenced before differentiator).
   - **Confidence from ODI:** Map story ODI confidence to Confidence:
     - `[HIGH]` → `100%`
     - `[MED]` → `80%` (`[MEDIUM]` accepted as legacy)
     - `[LOW]` → `50%`
    - **Fallback (ODI absent): HALT** and ask the user for Impact and Confidence; never infer them (an inferred value can move the priority bucket). Resume drafting only after both are given:
      - **Impact:** ∈ {0.25 (min), 0.5 (low), 1.0 (med), 2.0 (high), 3.0 (crit)}
      - **Confidence:** ∈ {50% (guess), 80% (high), 100% (certain)}
   - Prompt for **Size** (Effort):
     - **Size:** ∈ {size:small (weight 1), size:medium (weight 2), size:large (weight 3)}
3. **Draft full specs to scratch (Spikes: skip):** expand each new slice (not an existing sibling) into a complete, self-contained Build slice in `.tmp/BT-<padded>-issue-drafts.md`, the issue body minted verbatim in Phase 3, every field inline:
   - Contracts/invariants (e.g. Zod/Pydantic/TS types), selectors/patterns, and edge cases from PRD §6/§8 + the frozen design blueprint.
   - **Brief seed:** Established Facts → Current state / Problem (file paths allowed in issue bodies). PRD-sourced: Constraints & Settled Decisions → Current state / Problem. No-PRD path: Problem → Overview; Success State → Acceptance Criteria; Constraints & Settled Decisions → constraints in The Path; Non-Goals → Notes.
   - **Minimum spec bar (no-PRD path):** every Build slice body carries a problem statement (Overview or Current state / Problem), at least one verifiable AC, and constraints or non-goals.
   - Governing `[[A-xxx]]`/`[[DR-xxx]]` citations (only IDs that exist in `.memory/`; a not-yet-written ADR is cited as plain text `ADR pending: <title>`, never a placeholder ID).
   - PRD §7 Boundaries: copy the Ask first and Never lines that touch the slice into its body. Ask first = HITL halts and asks; AFK returns `stuck`.
   - Verifiable AC incl. time-to-value + stress cases from the design doc.
   - Parent/Blocked-by (a not-yet-minted sibling is written `BT-<slice:N>`, N = its position in the slice list; the only placeholder a draft may carry).
   - The Dependencies `- **Design:**` line = the real design-doc path from Phase 1 step 3 (`—` if none or standalone; never a `BT-<…>` placeholder).
4. **Slice Draft Audit (Spikes: skip):** invoke an independent Slice Draft Auditor subagent (using the host's subagent mechanism).
   - **Reads** (fresh from disk, all if present): `.tmp/BT-<padded>-issue-drafts.md`; the **full** PRD `docs/prds/BT-<padded>-<name>.md`, interface design `docs/design/BT-<padded>-interface.md`, the discovery brief (as located in Phase 1 step 3), each existing sibling's issue body (PRD-sourced; `gh issue view <n>`), and research (the PRD frontmatter `research:` path; fallback `docs/research/*<slug>*.md` for PRDs without it).
   - **Precedence:** PRD > interface design > brief > research; on conflict, the higher source wins.
   - Guardrail: *"Report findings + one proposed fix each; do not create issues or edit any file."*
   - Score 0–100 per `references/confidence-scale.md` (audit scope: slice-draft coverage + fidelity to specs); report ≥ 80 across two dimensions:
   - **Breadth:** map **every `[BASELINE]` and `[DIFFERENTIATOR]` §6 story, §8 DoD item, and design blueprint element** to its covering slice (a draft, or an existing sibling cited by `BT-<n>`) or `[UNCOVERED]`, walking the **journey-grouped** §6 stories. `[DEFERRED]` stories / §9 Out-of-Scope are covered/excluded (**not** `[UNCOVERED]`).
   - **Depth:** each draft is a complete Build slice, faithfully captures the named contracts/invariants + edge cases, cites the governing `[[A-xxx]]`/`[[DR-xxx]]`, and carries verifiable AC (incl. time-to-value + stress cases). A draft over the ceiling → split finding with one proposed split; the user may keep it whole at step 5.
   - **Loop optimization:** re-spawn *only* on material change (slices added / removed / re-scoped, or bodies materially edited) — not cosmetic edits (renames, ICE tweaks).
   - **Resolution:**
     - `[UNCOVERED]` → add slice / defer to §9 / confirm out-of-scope / "covered by construction".
     - Scope creep (hits §4 Non-Goal / §9 Out-of-Scope) → `[SCOPE-CREEP]` cut.
     - Blocker (open §10 Question — not a `migration:` item — not already a Spike) → Spike.
     - Apply ≥ 80 draft-fixes to `.tmp`.
     - **Spec defect** (the PRD/design itself is ambiguous or self-contradictory, not the draft) → do not patch the draft; surface it and route to `/2c-reconcile-specs` or convert the slice to a Spike.
     - **Research-only finding** (a requirement/constraint present in research but absent from PRD + interface) → flag `[RESEARCH-GAP]` for HITL before implementing; never fold it into the draft unilaterally.
     - **Brief-only finding** (a constraint or settled decision present in the brief but absent from PRD + interface; Established Facts used as Current-state evidence are expected, not a gap) → flag `[BRIEF-GAP]` the same way.
   - **No PRD:** restate intent as a requirement list; map slices; the brief (if located) is the top source, so `[BRIEF-GAP]` and the precedence clause do not apply, and every Success State item and settled decision maps to a draft AC or constraint; check each draft body against the spec bar, a missing element is a finding; gaps → `[UNCOVERED?]` (soft) for user confirmation; no §-refs.
   - **Audit-sourced:** reads (fresh from disk) the proposal `.tmp/refactor-proposal-<stem>.md` and the report on its line 1, per `.agents/skills/3b-create-issue/references/audit-to-slices.md`; the PRD/research precedence clause does not apply. **Breadth:** every F-xx in the report maps to a slice or a §5 token, else `[UNCOVERED]`. **Depth:** each slice is a complete Build slice per §4 — `Resolves:` line with full report paths, evidence inline, one no-longer-reproduces AC per resolved F-xx; a slice over the ceiling → split finding.
5. **Approval Request:** present the audited drafts + coverage map. Confirm: requirements & end-state covered (no `[UNCOVERED]`); granularity; dependencies; modes (`mode:HITL`/`mode:AFK`); ICE scores. Audit-sourced: also confirm the epic (title, area, milestone per `references/audit-to-slices.md` §8) or its absence (§7). Halt until user approves.

## Phase 3: Implementation & Memory Sync
1. **Calculate ICE Score (Spikes: skip):** `ICE = (Impact * Confidence) / Effort weight` (Confidence as decimal; Effort: small=1, medium=2, large=3).
2. **Determine Priority Label (Spikes: skip):**
   - `ICE >= 0.5` → `priority:high`
   - `0.15 <= ICE < 0.5` → `priority:medium`
   - `ICE < 0.15` → `priority:low`
3. **Pre-mint guard (Build slice):**
   - (a) **Whole file, once:** `grep -noE 'BT-<[^>]+>|\[\[[A-Z]+-[xX]+\]\]' .tmp/BT-<padded>-issue-drafts.md | grep -vE ':BT-<slice:[0-9]+>$'` — any output → HALT and list it (only sibling `BT-<slice:N>` refs may remain).
   - (b) **Mint order:** if drafts cite siblings, state a topological order (blockers first; a cycle → HALT — Blocked-by must be acyclic) and mint in that order; after each mint, replace that slice's `BT-<slice:N>` with the returned `BT-<padded>` in every remaining draft.
   - (c) **Per slice, before each mint:** run the step (a) pattern on that slice's body without the exclusion — any hit (an unminted blocker included) → HALT. Substitution is the only permitted edit to an approved draft.
   - **Audit-sourced:** run (a)–(c) against the proposal path instead of `.tmp/BT-<padded>-issue-drafts.md`; in (a) also exclude `BT-<epic>` (`grep -vE ':BT-<(slice:[0-9]+|epic)>$'`), and HALT if `BT-<epic>` appears without a `## Epic` section. Only after (a) and the (b) order/cycle check pass, (b0): mint the epic (step 4) and replace every `BT-<epic>` in the proposal with the returned ID, then mint slices in the (b) order.
4. **Generate (Atomic Minting):** Execute `gh issue create --body-file .tmp/3b-issue-body.md` — write each issue's body (slice or epic) to that one scratch file, overwriting it per mint.
   - **Body source:** Build slice → the approved `.tmp/BT-<padded>-issue-drafts.md` draft **verbatim** (never regenerate), with raw ICE metrics in the issue body; Spike → compose the Spike body. Offline fallback: assign `BT-LOCAL-<n>`.
   - **CRITICAL:** Capture exact returned issue number and zero-pad to 3 digits (e.g. `BT-059`). Never guess issue number; GitHub shares IDs across Issues and PRs.
   - **Labels:** scope label (`scope:baseline` or `scope:differentiator`) + canonical labels: Primary Type (e.g. `type:feature`) + Execution Mode (`mode:HITL` or `mode:AFK`) + Tier (`tier:slice`) + Size (`size:small/medium/large`; Spikes: always `size:medium`) + Priority (`priority:high/medium/low` from the step-2 bucket; Spikes: skip) + **Status: `status:planned` for a Build slice; `status:needs_spec` for a Spike.**
   - **Milestone:** pass `--milestone "<vX.Y.0>"` on every slice mint. `<vX.Y.0>` = the parent's milestone (`gh issue view <parent> --json milestone -q .milestone.title`; 3a created it, so it exists; parent has none → `—`), standalone → `v1.0.0` (audit-sourced: the §8 default). Only for those defaults, confirm the milestone is open: `gh api --paginate 'repos/{owner}/{repo}/milestones?state=open' --jq '.[].title'`; absent, closed or `—` → omit the flag, write `—` in step 5 and surface it (never mint onto a closed release). Audit epic: see its command below.
   - **Sub-issue Linkage:** If derived from parent epic, link via the `addSubIssue` mutation per `references/github-issue-relations.md` (native `gh api graphql`; no `gh-sub-issue` extension).
   - **Audit epic (audit-sourced, when the proposal has `## Epic`):** mint it before any slice:
     ```bash
     gh issue create --title "<Epic Title>" --label "tier:epic,type:maintenance,area:<x>,status:planned" --milestone "<vX.Y.0>" --body-file .tmp/3b-issue-body.md
     ```
     Epic body per `references/audit-to-slices.md` §10. Audit slices then mint with the rules above, body = the proposal's `## Slice <N>` section verbatim: epic children link as sub-issues; `(standalone)` slices take no parent and no sub-issue link, and take the §8 milestone. Slice `type:bug` for Security/Correctness findings, else `type:maintenance`; scope label `scope:baseline`.
   - **Dependencies:** Wire blockers via the `addBlockedBy` mutation (same reference). Mirror "Blocked by: [IDs]" in the issue body and BACKLOG_MAP.
5. **Backlog Sync:** Append entry (`BT-<padded>`) to `.memory/BACKLOG_MAP.md` adhering to `[[memory-protocol.md#8-backlog-id-minting-late-binding]]` (first real entry: purge placeholders) — 9-column schema. Refresh `generated.at` (and `generated.by`) on any `.memory/` document this step mutates. sprint digit Z assigned by 3c.
   - **Labels column:** bucketed priority (Build slices only), size (Spikes: `size:medium`), type, execution mode, tier and scope label (never the status). **Status column:** the bare status token (`planned`/`needs_spec`). **ICE column:** the ICE details.
   - **`Parent`:** the single `BT-<parentPadded>` (or `—` for a standalone slice). **`Blocked by`:** the comma-list of bare sibling blocker IDs (or `—`). Milestone: the step-4 Milestone value (Spikes too; `—` when none).
   - Audit epic row: `| BT-<n> | <title> | planned | area:<x>, tier:epic, type:maintenance | vX.Y.0 | — | — | ICE: - | <cited laws or —> |`; report paths go in issue bodies, never in `Ref`.
6. **Terminal sync gate:** run `python .agents/scripts/reconcile.py --require-gh --ids <comma-list of created BT-<padded>, audit epic included>` (all fields — these are freshly created rows) per `references/terminal-sync-invariant.md`. Non-zero → heal per the reference and re-run, **at most 3 attempts**; still non-zero, or `[MIRROR-UNVERIFIED]` → halt and surface the drift. Never loop unbounded before hand-off.
   - **Scratch cleanup (on gate pass only):** `rm -f .tmp/BT-<padded>-issue-drafts.md .tmp/3b-issue-body.md` — the drafts and issue body are ephemeral and already minted; keep them if the gate halted so healing can re-read them.
7. **Hand-off:** Slices created. Run `/3c-sprint-planning` to sequence, or `/3d-implement-issue` for a single ready Build slice.

---

## LABEL REGISTRY
Use registry in `.memory/BACKLOG_MAP.md`. Do not invent labels. If label missing: propose adding to BACKLOG_MAP registry, await confirmation, create in GitHub, write to registry, then apply.

## Issue Templates
Follow canonical templates in `references/issue-templates.md`.