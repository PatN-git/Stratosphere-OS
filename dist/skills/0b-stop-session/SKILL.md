---
name: 0b-stop-session
description: "Conclude session by codifying progress, updating memory, and linting. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.3.0"
timestamp: 2026-10-05
---

# STOP SESSION

## Goal
Leave next session with context to resume immediately. Ensure new entries are tagged, cross-referenced, and lint-clean.

> Trust tags, supersession, cross-reference, and lint protocols → `.agents/rules/memory-protocol.md`.

## Procedure

**First entry rule:** On first entry in `STATUS.md`, `LEARNINGS.md`, `GLOSSARY.md`, `ARCHITECTURE.md`, or `DESIGN_RULES.md`, delete placeholders only; preserve structure, guidelines, and format examples under `## Superseded`.

1. Compare completed vs. planned:
    - Comment plan, completed, and open steps on active GitHub issues, and note which issues were updated/closed.
    - **Done detection (no forcing):** a slice/epic is `done` only once its PR has **merged** and the issue auto-closed. For each issue **closed/merged** this session: mark its BACKLOG Status `done` (or delete the row per retention) and **clear its bare ID from every dependent's `Blocked by`** in `.memory/BACKLOG_MAP.md` and GitHub (`removeBlockedBy` mutation per `references/github-issue-relations.md`; safety net for the 4a in-review clearing). Do **not** force `status:done` on a slice still at `status:in review` (code shipped but unmerged) — leave it for the human merge. If all sibling sub-issues under `#parent` are closed/merged, prompt to confirm the parent epic `done` and reconcile `BT-<parent>` in `BACKLOG_MAP.md`.
    - **Post-merge follow-ups:** for each issue detected done this step, take the PR from its `Shipped in PR #<pr>` comment (4a step 6); dedupe PRs. Read each PR's `stratos-pr` block (`gh pr view <pr> --json body`; no block → skip). For each `post_merge` item, propose a follow-up issue (title + one-line body). On confirmation only, create it per the BACKLOG Label Composition Rules and 3b atomic minting, with this label set pinned so no label is dropped: `type:maintenance`, `mode:HITL`, `tier:slice`, `size:small`, `status:planned`; add its BACKLOG row in the same step.
2. Update `.memory/STATUS.md` (last sync, current branch, active issue, current focus, completed, blockers, next step).
3. **Friction gate:** run steps 3–4 only if this session hit friction: a failed approach, a costly wrong assumption, a defect fixed, or a reviewer/audit catch. Else skip silently. For each defect fixed, ask "what would have prevented it?". Route every candidate per `references/environment-fix-ladder.md`.
4. If a candidate reaches the LEARNINGS rung and is a durable lesson:
   - **Durability gate:** *Would this still be true after the work that prompted it ships?* If no (a current defect, a pending fix, in-flight state) → record it in the issue or `STATUS.md`, not `LEARNINGS.md`.
   - Propose the full entry text (next `[[L-xxx]]`, default tag `[ASSUMED]`, `Source: BT-xxx`); write to `.memory/LEARNINGS.md` only on confirmation. Never self-write.
   - Propose **at most one** LEARNINGS entry per session unless the user asks for more.
   - To remove an entry, move it to `## Superseded` with a `[REMOVED]` tombstone (see memory-protocol §3).
5. If term agreed, propose the entry and add to `.memory/GLOSSARY.md` on confirmation (assign next `[[G-xxx]]`, default tag `[ASSUMED]`, record rejected synonyms in `Avoid:` — same as 1b; if an `Avoid:` synonym likely already appears in code, offer the same one-time, module-scoped retrofit (propose-only); cross-reference `Source`).
6. If architecture changed:
   - Propose structural `[LAW]` changes; never self-write to `ARCHITECTURE.md`.
   - On confirmation, add `[[A-xxx]]` entry (follow supersession protocol).
   - If a step-4 learning is now codified by the new `[[A-xxx]]`, propose superseding it (`[[L-xxx]]` → `[[A-xxx]]`); apply on confirmation.
7. If DB schema or understanding changed, update `.memory/DATABASE_SCHEMA.md` (always `[LAW]`).
8. Propose UI structural (`[[DR-xxx]]`/immortal component) or brand token changes before updating `DESIGN_RULES.md`/`DESIGN.md`.
9. Verify: `python .agents/scripts/pr_body.py suite` prints a reusable suite result (reuse it); else run the suite. Then run memory lint: `python .agents/scripts/validate_memory.py`. Propose fixes for any reported errors, list warnings, and await confirmation.
10. Regenerate OKF Visualizer: `python .agents/scripts/okf_view.py` after lint passes.
11. Ensure `.memory/STATUS.md` allows resuming without re-discovery.

## Handoff Note Format
Session complete.
- What changed:
- Files touched:
- GitHub issues touched:
- Verification & Lint results:
- New learnings (ID, tag, one-line text):
- New glossary terms (with IDs and tags):
- Follow-ups proposed:
- Blockers:
- Next immediate step:

## Constraints
- **Security:** Redact sensitive information (e.g. API keys, passwords, personally identifiable information).
- **No silent memory rewrites:** crystallization, supersession, and lint fixes require user confirmation.