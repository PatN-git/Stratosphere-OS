---
name: 0b-stop-session
description: "Conclude session by codifying progress, updating memory, and linting. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.9.0"
timestamp: 2026-11-10
---

# STOP SESSION

## Goal
Leave next session with context to resume immediately. Ensure new entries are tagged, cross-referenced, and lint-clean.

> Trust tags, supersession, cross-reference, and lint protocols → `.agents/rules/memory-protocol.md`.

## Procedure

**First entry rule:** On first entry in `STATUS.md`, `LEARNINGS.md`, `GLOSSARY.md`, `ARCHITECTURE.md`, or `DESIGN_RULES.md`, delete placeholders only; preserve structure, guidelines, and format examples under `## Superseded`.

1. Compare completed vs. planned:
    - Post a resume note on each active issue with `comment` (`.agents/scripts/tracker.py` §Resume note): the block starting `<!-- stratos:resume -->` with `Branch / Done / Open / Next step / Blockers`, written to `.tmp/resume-BT-<n>.md` and sent with `--body-file` (local backend: `.memory/resume/<id>.md`); note which issues were updated/closed.
    - **Merge-time sync:** run `gh pr list --state closed --search "closed:>=<Last Sync date>" --json number,mergedAt,closingIssuesReferences,headRefName` (`Last Sync` from `.memory/STATUS.md`; empty or not a date → no `--search`, `gh` returns its newest 30 closed PRs). Any PR back (merged, or closed unmerged) → read `references/post-merge-sync.md` and run it, then use its results for the handoff `Blockers` and `Follow-ups proposed`; none → skip silently.
        - Local backend: the merged ids are each merged PR's `stratos-pr` `features:` list plus `git fetch -q origin` (non-fatal: ignore a failure, offline or no origin, the check then runs on what is local) then `python .agents/scripts/issues.py merged --close`, which needs no PR host and runs even when none is back. A `[PROBABLY-MERGED <id>]` line (squash found by id, never auto-closed): ask the user to confirm the merge, then `python .agents/scripts/issues.py close <id>`; unconfirmed → leave it `in review`.
        - `gh` unavailable → skip the PR query and note in `Blockers`; locally `issues.py merged --close` still runs.
2. Update `.memory/STATUS.md`, folder state only, by editing single fields and lines, never a whole-file rewrite:
    - Set `Last Sync` (today), unless the merge sync was skipped (`gh` unavailable): then leave it unchanged and note the skip in `Repo notes`; set or clear `Blocker` and `Repo notes`.
    - Remove this session's line from `Sessions` when its slice left `in progress`; prune the other lines whose issue is not in the `wip` read (`.agents/scripts/tracker.py`) or whose date is older than 14 days.
    - Old-format STATUS (single-task fields or dated history instead of `Sessions`): propose the trimmed new-format file once and write it on confirmation.
3. **Friction gate & Diff-Based Verification:** run steps 3–4 only if this session hit friction: a failed approach, a costly wrong assumption, a defect fixed, or a reviewer/audit catch. Else skip silently. Run `git diff` and inspect actual code diffs to verify candidate lessons against real code modifications rather than model recall. For each defect fixed, ask "what would have prevented it?". Route every candidate per `references/environment-fix-ladder.md`.
4. If a candidate reaches the LEARNINGS rung and is a durable lesson:
   - **Durability gate:** *Would this still be true after the work that prompted it ships?* If no (a current defect, a pending fix, in-flight state) → record it in the issue (the resume note) or `STATUS.md` `Repo notes`, not `LEARNINGS.md`.
   - Propose entry (next `[[L-xxx]]`, default tag `[ASSUMED]`, `Source: BT-xxx`, negative constraints if any); write to `.memory/LEARNINGS.md` only on user confirmation. Never self-write.
   - To remove an entry, move it to `## Superseded` with a `[REMOVED]` tombstone (see memory-protocol §3).
5. If term agreed, propose the entry and add to `.memory/GLOSSARY.md` on confirmation (assign next `[[G-xxx]]`, default tag `[ASSUMED]`, record rejected synonyms in `Avoid:` — same as 1b; if an `Avoid:` synonym likely already appears in code, offer the same one-time, module-scoped retrofit (propose-only); cross-reference `Source`; per `references/glossary-entry-rules.md`).
6. If architecture changed:
   - Propose structural `[LAW]` changes; never self-write to `ARCHITECTURE.md`.
   - On confirmation, add `[[A-xxx]]` entry (follow supersession protocol).
   - If a step-4 learning is now codified by the new `[[A-xxx]]`, propose superseding it (`[[L-xxx]]` → `[[A-xxx]]`); apply on confirmation.
7. If DB schema or understanding changed, update `.memory/DATABASE_SCHEMA.md` (always `[LAW]`).
8. Propose UI structural (`[[DR-xxx]]`/immortal component) or brand token changes before updating `DESIGN_RULES.md`/`DESIGN.md`.
8b. Intermediate session files triage (.tmp/):
    - **Inspect & Triage Proposal:** inspect intermediate session files in `.tmp/` and prompt user via native question tool (`ask_question` on Antigravity; `AskUserQuestion` on Claude Code) with options:
      - `(Recommended) Delete Transient Scratch` — remove transient logs and scratch files.
      - `Relocate Durable Artifacts to docs/ (with OKF frontmatter)` — move durable designs/notes.
      - `Keep in .tmp/ for In-Flight Work` — retain for active follow-on work.
    - **Fallback (non-interactive hosts):** output 3-way triage options in markdown and halt for user response.
    - **Exemptions & Invariant:** active framework state files (`.tmp/3d-suite-*.json`, `.tmp/3z-loop.work.md`, `.tmp/3d-plan-*.md`, `.tmp/4a-audit-*.json`) are explicitly exempted from deletion candidates. Require user confirmation before deleting or relocating any file.
9. Verify: `python .agents/scripts/pr_body.py suite` prints reusable suite result (reuse it); else if no tracked file changed outside `.memory/` and `.tmp/`, report `suite: not run (no tracked change)`; otherwise run via `python .agents/scripts/test_gate.py record --suite BT-<padded> -- <cmd>` (no slice: `record -- <cmd>`). Run memory lint: `python .agents/scripts/validate_memory.py`. Report errors and warnings; await confirmation.
10. Regenerate OKF Visualizer: `python .agents/scripts/okf_view.py` after lint passes.
11. Ensure the resume note allows resuming without re-discovery.

## Handoff Note Format
Session complete.
- What changed:
- Files touched:
- GitHub issues touched:
- Verification & Lint results:
- Tmp files triaged (deleted / relocated / kept):
- New learnings (ID, tag, one-line text):
- New glossary terms (with IDs and tags):
- Framework feedback (skill · installed version · defect · evidence · suggested fix):
- Follow-ups proposed:
- Blockers:
- Next immediate step:

## Constraints
- **Security:** Redact sensitive information (e.g. API keys, passwords, personally identifiable information).
- **No silent memory rewrites:** crystallization, supersession, and lint fixes require user confirmation.