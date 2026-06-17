---
type: rule
title: Open Knowledge Format (OKF) Protocol
description: Specifications and type registries for OKF v0.1 conformance.
timestamp: 2026-06-16
---

# Open Knowledge Format (OKF) Protocol

This protocol defines how StratosphereOS implements the Open Knowledge Format (OKF) v0.1.

## 1. Conformance Scope
The OKF bundle scope consists of the `.memory/` directory and the `docs/` directory. Every concept document within this scope (excluding reserved files and foreign content) must conform to this protocol.

## 2. Frontmatter Contract
Every concept document must begin with a YAML frontmatter block containing:

- `type` (required): A non-empty string from the Type Registry.
- `title` (recommended): Human-readable display name, matching the file's first `#` heading.
- `description` (recommended): A single-sentence summary of the concept.
- `version` (recommended): The StratosphereOS release the file belongs to (quoted string, e.g., `"1.0.0"`).
- `timestamp` (recommended): ISO 8601 format (YYYY-MM-DD) of the last meaningful change.
- `tags` (optional): YAML list of short strings.
- `resource` (optional): URI to the underlying asset (e.g., issue URL, repo path) where one exists.

Other existing metadata keys (such as `issue_url`, `status`, `linked-prd`) are preserved alongside these fields.

## 3. Type Registry

Agents must use the following defined types. If no existing type fits, the agent must propose a new type to the user and, upon confirmation, add it to this registry. Agents must never invent or use a type silently.

| `type` | Applies to | Extra fields beyond the base contract |
|:---|:---|:---|
| `constitution` | `AGENT.md`, `CLAUDE.md`, `GEMINI.md` | — |
| `rule` | `.agents/rules/*.md` | — |
| `workflow` | `.agents/workflows/*.md` | `trigger` (required); `type` keeps its `HITL`/`AFK` qualifier, e.g. `workflow HITL` |
| `status` | `STATUS.md` | — |
| `backlog` | `BACKLOG_MAP.md` | — |
| `learnings` | `LEARNINGS.md` | — |
| `glossary` | `GLOSSARY.md` | — |
| `architecture` | `ARCHITECTURE.md` | — |
| `database-schema` | `DATABASE_SCHEMA.md` | — |
| `design-rules` | `DESIGN_RULES.md` | — |
| `design` | `DESIGN.md` | conforming (tolerated by the `@google/design.md` linter) |
| `prd` | `docs/prds/*.md` | `resource` (issue URL), `status` |
| `discovery-brief` | `docs/discovery/*.md` | `status`, `linked-prd` |
| `research` | `docs/research/*.md` | — |
| `interface-design` | `docs/design/*.md` (interface designs) | — |
| `design-doc` | `docs/design/*.md` (other design docs) | — |

## 4. Reserved Files
- **Root `index.md`**: The bundle entrypoint. It is the **only** file carrying `okf_version: "0.2"`.
- **Directory `index.md` files** (e.g. `.memory/index.md`, `docs/prds/index.md`): Used for progressive disclosure. These files must **not** carry frontmatter and are listings only.
- **`log.md`**: If present, carries change history. It must not contain frontmatter.

## 5. Version Semantics
- **System/Template Files**: Stamped at build time by `build/build.py` based on the system `VERSION` constant.
- **Generated Docs** (e.g., PRDs, designs created by workflows): Stamped at generation time with the installed plugin version read from the manifest `plugin.json`. If the manifest cannot be resolved at runtime, the `version` field is omitted (since `type` is the only strict conformance requirement).
- **Exemptions**: `DESIGN.md` is exempt from automatic version stamping to prevent conflicts with the Google DESIGN.md specification.

## 6. Inbound External Bundles (`docs/knowledge/`)
- External OKF bundles are stored in `docs/knowledge/<source>/` (where `<source>` is the name of the external bundle).
- Foreign contents are kept in their native OKF structure, excluded from automatic version stamping, and excluded from local OKF lint checks.
- **Promotion Ritual**: When an external concept becomes load-bearing, copy it into the appropriate local registry (e.g. `.memory/GLOSSARY.md`) as a `[ASSUMED]` entry and document its provenance with `Source: docs/knowledge/<source>/<path>`.

## 7. Cross-Reference Interoperability
- Internal memory cross-references (`[[ID]]` syntax, e.g. `[[L-001]]`) remain unchanged and are used for local bidirectional validation.
- External OKF consumers treat `[[ID]]` links as unresolved plain text. OKF-compliant outbound links must be standard markdown links (e.g., `[Glossary](/GLOSSARY.md)`).
