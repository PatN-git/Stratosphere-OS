---
description: How to write a `.memory/GLOSSARY.md` entry — format, definition, scope, Avoid/Source, growth. Cited by 1b, 1c, 0b and setup.
version: "1.0.0"
timestamp: 2026-10-27
---

# Glossary Entry Rules

Trust tags, promotion and supersession → `.agents/rules/memory-protocol.md`.

## Format
One line under `## Active Entries`: `- **[[G-XXX]] [ASSUMED] [YYYY-MM-DD]** Term: definition. Avoid: synonym-1, synonym-2. Source: docs/discovery/<slug>.md or BT-n.` IDs are global and sequential. `Avoid:` and `Source:` are the only fields: promotion evidence (the tasks whose `Ref` cites the ID) is derived, never stored in the entry.

## Definition
One or two sentences: what the term IS in this domain, not how it is built. No code identifiers, file paths, table or column names, formulas, thresholds or TTLs; record those in `ARCHITECTURE.md` or `DATABASE_SCHEMA.md` and cite the governing `[[A-xxx]]`. In code, the term itself is the identifier.

## Belongs
- Names of user segments and roles
- Business-state vocabulary
- Terms with a project-specific or non-obvious meaning
- Categorization terms used across features and PRDs

## Does not belong
- Code identifiers, paths, or relationships between concepts → `ARCHITECTURE.md`
- Brand tokens → `DESIGN.md`
- One-off terms not expected to recur across docs
- Technical or framework terms with standard industry meanings

## Avoid and Source
- `Avoid:` lists the synonyms rejected when the term was canonicalized; required whenever any were rejected (always in 1b and 1c), omitted otherwise. Plain text per memory-protocol §2.
- `Source:` names where the term was agreed; never rewritten on promotion.

## Growth
Keep one flat list. When natural clusters emerge, group them under `### <area>` headings inside `## Active Entries`. Split into per-context glossaries plus a root `GLOSSARY-MAP.md` only when one term needs two meanings in two areas, recorded as an `[[A-xxx]]` decision.
