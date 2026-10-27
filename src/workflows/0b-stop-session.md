---
name: 0b-stop-session
description: "Conclude session by codifying progress, updating memory, and linting. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.6.0"
timestamp: 2026-10-27
---

# STOP SESSION

## Goal
Leave next session with context to resume immediately. Ensure new entries are tagged, cross-referenced, and lint-clean.

> Trust tags, supersession, cross-reference, and lint protocols → `.agents/rules/memory-protocol.md`.

## Procedure

**First entry rule:** On first entry in `STATUS.md`, `LEARNINGS.md`, `GLOSSARY.md`, `ARCHITECTURE.md`, or `DESIGN_RULES.md`, delete placeholders only; preserve structure, guidelines, and format examples under `## Superseded`.

1. Compare completed vs. planned:
    - Post a resume note on each active issue with `comment` (`references/tracker-verbs.md` §Resume note): the block starting `<!-- stratos:resume -->` with `Branch / Done / Open / Next step / Blockers`, written to `.tmp/resume-BT-<n>.md` and sent with `--body-file` (local backend: `.memory/resume/<id>.md`); note which issues were updated/closed.
    - **Merge-time sync:** run `gh pr list --state closed --search "closed:>=<Last Sync date>" --json number,mergedAt,closingIssuesReferences,headRefName` (`Last Sync` from `.memory/STATUS.md`); any PR back (merged, or closed unmerged) → read `references/post-merge-sync.md` and run it; none → skip silently. `Last Sync` missing or not a date → run it anyway; `gh` unavailable → skip and say so in the handoff `Blockers` line. Use its results for the handoff `Blockers` and `Follow-ups proposed`.
2. Update `.memory/STATUS.md`, folder state only, by editing single fields and lines, never a whole-file rewrite:
    - Set `Last Sync` (today); set or clear `Blocker` and `Repo notes`.
    - Remove this session's line from `Sessions` when its slice left `in progress`; prune the other lines whose issue is not in the `wip` read (`references/tracker-verbs.md`) or whose date is older than 14 days.
    - Old-format STATUS (single-task fields or dated history instead of `Sessions`): propose the trimmed new-format file once and write it on confirmation.
3. **Friction gate:** run steps 3–4 only if this session hit friction: a failed approach, a costly wrong assumption, a defect fixed, or a reviewer/audit catch. Else skip silently. For each defect fixed, ask "what would have prevented it?". Route every candidate per `references/environment-fix-ladder.md`.
4. If a candidate reaches the LEARNINGS rung and is a durable lesson:
   - **Durability gate:** *Would this still be true after the work that prompted it ships?* If no (a current defect, a pending fix, in-flight state) → record it in the issue (the resume note) or `STATUS.md` `Repo notes`, not `LEARNINGS.md`.
   - Propose the full entry text (next `[[L-xxx]]`, default tag `[ASSUMED]`, `Source: BT-xxx`); write to `.memory/LEARNINGS.md` only on confirmation. Never self-write.
   - To remove an entry, move it to `## Superseded` with a `[REMOVED]` tombstone (see memory-protocol §3).
5. If term agreed, propose the entry and add to `.memory/GLOSSARY.md` on confirmation (assign next `[[G-xxx]]`, default tag `[ASSUMED]`, record rejected synonyms in `Avoid:` — same as 1b; if an `Avoid:` synonym likely already appears in code, offer the same one-time, module-scoped retrofit (propose-only); cross-reference `Source`).
6. If architecture changed:
   - Propose structural `[LAW]` changes; never self-write to `ARCHITECTURE.md`.
   - On confirmation, add `[[A-xxx]]` entry (follow supersession protocol).
   - If a step-4 learning is now codified by the new `[[A-xxx]]`, propose superseding it (`[[L-xxx]]` → `[[A-xxx]]`); apply on confirmation.
7. If DB schema or understanding changed, update `.memory/DATABASE_SCHEMA.md` (always `[LAW]`).
8. Propose UI structural (`[[DR-xxx]]`/immortal component) or brand token changes before updating `DESIGN_RULES.md`/`DESIGN.md`.
9. Verify: `python .agents/scripts/pr_body.py suite` prints a reusable suite result (reuse it); else, if this session changed no tracked file outside `.memory/` and `.tmp/` (commits included), report `suite: not run (no tracked change)`; otherwise run it via `python .agents/scripts/test_gate.py record --suite BT-<padded> -- <cmd>` (no slice: `record -- <cmd>`). Then run memory lint: `python .agents/scripts/validate_memory.py`. Propose fixes for any reported errors, list warnings, and await confirmation.
10. Regenerate OKF Visualizer: `python .agents/scripts/okf_view.py` after lint passes.
11. Ensure the resume note allows resuming without re-discovery.

## Handoff Note Format
Session complete.
- What changed:
- Files touched:
- GitHub issues touched:
- Verification & Lint results:
- New learnings (ID, tag, one-line text):
- New glossary terms (with IDs and tags):
- Framework feedback (skill · installed version · defect · evidence · suggested fix):
- Follow-ups proposed:
- Blockers:
- Next immediate step:

## Constraints
- **Security:** Redact sensitive information (e.g. API keys, passwords, personally identifiable information).
- **No silent memory rewrites:** crystallization, supersession, and lint fixes require user confirmation.