---
trigger: glob
globs: .memory/**/*,docs/**/*
paths:
  - ".memory/**/*"
  - "docs/**/*"
type: rule
title: Open Knowledge Format (OKF) Protocol
description: Specifications and type registries for OKF v0.1 conformance.
version: "1.0.3"
timestamp: 2026-07-17
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
- `timestamp` (required on distributed artifacts): ISO 8601 date of the last meaningful change. OKF's canonical change-date field; used by the build and bump-guard.
- `version` (required on distributed artifacts; best-effort on generated docs, see §5): StratOS extension; quoted SemVer.
- `tags` (optional): YAML list of short strings.
- `resource` (optional): URI to the underlying asset (e.g., issue URL, repo path) where one exists.

Other existing metadata keys (such as `issue_url`, `status`, `linked-prd`) are preserved alongside these fields.

**Canonical doc-status vocabulary (guidance; OKF stays value-agnostic).** Editorial `status:` on `prd` and `interface-design` docs uses one shared enum: `draft | approved | superseded`. Work-status (`status:*` GitHub labels / BACKLOG `Status`) never appears in doc frontmatter, and this editorial enum never appears on issues. The `discovery-brief` type keeps its own routing-outcome vocab (`ready-for-prd | exit-bug | exit-spike | dropped`), which records a routing decision, not editorial maturity.

### 2.1 Activation contract (`rule` and `workflow` types)

`rule` and `workflow` files declare **when they activate** via a single canonical `trigger` key drawn from one shared enum. This unifies what were previously two divergent uses of `trigger:` (rules carried an Antigravity enum; workflows carried free-text prose).

| `trigger` | Meaning | Applies to |
|:---|:---|:---|
| `always_on` | Always in context. | rules |
| `glob` | Active only for files matching `globs`. Requires `globs`. | rules |
| `model_decision` | The model decides from `description`. | rules |
| `manual` | Activated only by explicit user invocation (slash command / `@`-mention). | workflows (all) |

Rules that are **`glob`** also carry host-native activation fields as a **superset** so one file works in both hosts (each host ignores the other's keys):

- `globs` (Antigravity): comma-separated glob patterns, **unquoted**, e.g. `globs: .memory/**/*,docs/**/*`.
- `paths` (Claude Code): YAML list mirroring `globs`, e.g. `paths: [".memory/**/*", "docs/**/*"]`.

Host activation semantics (see also [AGENTS.md](/AGENTS.md) §8):

- **Antigravity** reads `trigger`/`globs` natively from `.agents/rules/`.
- **Claude Code** has no `trigger` concept. `glob` rules activate via `paths` when installed to `.claude/rules/`; `always_on`/`model_decision` rules are surfaced through the AGENTS.md §8 pointer directory (on-demand load) to preserve token efficiency, not duplicated into `.claude/rules/`.
- **Workflows** need no host field: they build to Claude slash commands (user-only by construction — the model cannot auto-invoke them) and to Antigravity workflows (manual `@`-mention). `trigger: manual` is therefore declarative in both. Autonomy that begins *after* user invocation (e.g. `3z`) is documented in the body, not the trigger.

## 3. Type Registry

Agents must use the following defined types. If no existing type fits, the agent must propose a new type to the user and, upon confirmation, add it to this registry. Agents must never invent or use a type silently.

| `type` | Applies to | Extra fields beyond the base contract |
|:---|:---|:---|
| `constitution` | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` | — |
| `rule` | `.agents/rules/*.md` (glob rules also `.claude/rules/*.md`) | `trigger` (required): `always_on` \| `glob` \| `model_decision` (see §2.1); if `glob`, also `globs` (Antigravity) **and** `paths` (Claude) |
| `workflow` | `.agents/workflows/*.md` | `trigger` (required): `manual` (see §2.1); `type` keeps its `HITL`/`AFK` qualifier, e.g. `workflow HITL` |
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
- **Root `index.md`**: The bundle entrypoint. It is the **only** file carrying `okf_version: "0.1"`.
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
