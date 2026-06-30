---
type: rule
title: Memory Protocol
description: Single source of truth for how the agent reads, writes, and maintains the `.memory/` layer.
timestamp: 2026-06-23
version: "1.0.4"
---

# Memory Protocol

Single source of truth for how the agent reads, writes, and maintains the `.memory/` layer. For Open Knowledge Format (OKF) conformance rules, see [okf-protocol.md](okf-protocol.md).

## 1. Trust Tags

Every entry in `LEARNINGS.md`, `GLOSSARY.md`, `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, and `DESIGN_RULES.md` carries exactly one trust tag.

`DESIGN.md` is **exempt** — external spec, validated by `npx @google/design.md lint`.

| Tag | Meaning | Where it lives |
|:---|:---|:---|
| `[LAW]` | Never violate. Hard constraint from code, DB, framework, or design governance. | `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, `DESIGN_RULES.md`. `LEARNINGS.md` only for code-vs-DB conflicts. |
| `[PATTERN]` | Established practice. Override requires justification. | `LEARNINGS.md`, `GLOSSARY.md`. |
| `[ASSUMED]` | Speculative or unverified. | `LEARNINGS.md`, `GLOSSARY.md`. |

### Promotion rules

- **New entries default to `[ASSUMED]`.**
- **`[ASSUMED] → [PATTERN]`**: cite ≥2 occurrences across distinct tasks. Agent may self-promote with evidence.
- **`[PATTERN] → [LAW]`**: explicit human confirmation required. Agent NEVER self-promotes to `[LAW]`. `GLOSSARY.md` entries never reach `[LAW]` — vocabulary is not architectural law.

### Demotion / challenge

- Agent SHOULD challenge a `[ASSUMED]` conflicting with observed code behavior.
- Agent MAY propose demoting a `[PATTERN]` violated successfully ≥2 times without harm.
- `[LAW]` is never demoted — it is superseded (§3).

## 2. Cross-References

| ID | Lives in |
|:---|:---|
| `BT-xxx` | `BACKLOG_MAP.md` |
| `[[L-xxx]]` | `LEARNINGS.md` |
| `[[A-xxx]]` | `ARCHITECTURE.md` |
| `[[DR-xxx]]` | `DESIGN_RULES.md` |
| `[[G-xxx]]` | `GLOSSARY.md` |

**ID Format:** Real entries use numeric IDs (`[[L-001]]`); `-XXX` suffixes are reserved placeholders the validator ignores. Never ship a real entry with a non-numeric ID.

- `[[ID]]` is ONLY for memory-to-memory links (L/A/DR/G ↔ L/A/DR/G), which the validator resolves and checks for reciprocity. BT/issue IDs are always BARE — first column, Dependencies, and the `Source:` field (e.g. `Source: BT-007`, never `Source: [[BT-007]]`) — because provenance is a one-directional external pointer, not a peer concept-link.

### EXAMPLES Bidirectional linking

- Entry born from a task: `Source: BT-042`.
- Task depending on an entry: `Ref: [[L-012]], [[G-005]], [[DR-020]]`.
- Lint validates all links every `/stop-session`.

### Naming Conventions
- **Ubiquitous language (leading words):** When naming code identifiers (variables, functions, files, types), use the canonical GLOSSARY term verbatim; never introduce a synonym listed in that term's `Avoid:` field. `[[G-xxx]]` is the link handle in docs/memory; in code, the word itself is the identifier. `Avoid:` values are always plain text — never bracketed.

## 3. Supersession (in-file)

When a rule changes, move the old entry to `## Superseded` in the **same file**:
- `[SUPERSEDED BY [[ID]]]` tag
- One-line reason
- Date or version

`## Superseded` is read only when explicitly triggered. No separate archive file.

## 4. Lint (at /stop-session)

Enforced deterministically by `.agents/scripts/validate_memory.py`. Propose fixes for any reported errors, list any warnings, and await confirmation.

## 5. What never happens

- Never self-promotes to `[LAW]`.
- Never deletes to supersede — moves to `## Superseded` with tag.
- Never silently rewrites memory during crystallization or lint.
- Never reads `## Superseded` unless explicitly asked.
- Never writes to any `.memory/` file without proposing and awaiting user confirmation. (Note: BACKLOG_MAP Ref/status updates performed by a lifecycle workflow (2a/2b/3a/3b/3c/4a Publish & Sync steps) are pre-authorized and need no per-write confirmation; this confirmation rule applies to content entries in LEARNINGS/ARCHITECTURE/DESIGN_RULES/GLOSSARY).
- Never write secrets, API keys, tokens, or PII to any `.memory/*` file. Redact before recording a learning.

## 6. Retrieval & Scale
- Never read `## Superseded` unless the task explicitly needs history.
- Resolve refs by ID, not by file — e.g. to follow a `[[L-xxx]]` reference, grep for that exact ID; do not read the whole memory file.

## 7. Placeholder Preservation & Scaffolding Rule
- **Never delete structural headings, comments, or guidelines:** When populating or updating any memory file during project setup or ongoing development, you MUST PRESERVE all section headings (even if empty, such as `## Major Feature Areas`, `## State / Data Flow`, `## Backend / Database Boundaries`, `## Shapes`, `## Components`, `## Do's and Don'ts`), HTML/markdown comments (e.g., `<!-- shadcn variable names... -->`), guidance text (e.g., `<Rationale...>`, `Avoid:` instructions), governance rules/bullet points, and the format example lines under `## Superseded`. They must remain in place as placeholders and guidance until needed or replaced by real domain content.
- **What to remove:** When writing real active content into a memory file, remove ONLY the dummy active items in that section (e.g., `BT-XXX`, `[[L-XXX]] Example placeholder`, `[[G-XXX]] Example Term`, `[[A-XXX]] Example placeholder`). Real entries are always superseded per §3 (moved to `## Superseded`), never deleted.

## 8. Backlog ID Minting (Late Binding)
- **No local number guessing:** Never compute `MAX(BT_ID) + 1` from local files; GitHub shares integer sequence numbers across both Issues and Pull Requests.
- **Slug-first before creation:** Pre-creation artifacts (`/1b` discovery briefs, draft PRDs) use semantic slugs only (e.g., `docs/discovery/<slug>.md`). Never assign `BT-<n>` padding before creation.
- **Atomic minting:** Bind `BT-<padded>` strictly at creation time from the return value of `gh issue create`. If offline, use `BT-LOCAL-<n>`.
