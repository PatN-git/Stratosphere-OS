---
trigger: glob
globs: .memory/**/*,docs/**/*
paths:
  - ".memory/**/*"
  - "docs/**/*"
title: Open Knowledge Format (OKF) Protocol
description: Specifications and type registries for OKF v0.2 conformance.
version: "2.0.0"
timestamp: 2026-09-15
---

# Open Knowledge Format (OKF) Protocol

This protocol defines how StratosphereOS implements the Open Knowledge Format (OKF) v0.2.

## 1. Conformance Scope

> **Known gap:** `validate_memory.py` returns early when `.memory/` is absent, so the
> `docs/` conformance walk never runs in the framework repo itself. Slice 12 decouples
> them. Until then, `docs/` conformance here is enforced by review, not by the linter.
The OKF bundle scope is **exactly** the `.memory/` and `docs/` directories, and within them **only `.md` files**. Every concept document in that scope (excluding reserved files and foreign content) must conform to this protocol.

**Out of scope — these carry no OKF `type:`:** the repo-root constitution files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`), `.agents/rules/*`, `.agents/skills/*`, `src/*`. Framework artifacts are governed by `metadata.stratos.*` (see `AGENTS.md` §2), not by OKF. Their `version:` and `timestamp:` are **build fields** stamped by `build/build.py`, not OKF change-records.

## 2. Frontmatter Contract
Every concept document must begin with a YAML frontmatter block containing:

- `type` (required): A non-empty string from the Type Registry.
- `title` (recommended): Human-readable display name, matching the file's first `#` heading.
- `description` (recommended): A single-sentence summary of the concept.
- `generated` (required on in-scope documents): OKF v0.2's change-record, a **nested mapping**, not a scalar:
  ```yaml
  generated:
    by: <invoking workflow name>
    at: <ISO 8601>
  ```
  `by` names the **invoking workflow** (its frontmatter `name`), never a subagent that contributed content. Supersedes v0.1's `timestamp:`, which is retired inside the bundle scope and survives only as a build field on out-of-scope files (§1).
- `version` (required on distributed artifacts; best-effort on generated docs, see §5): StratOS extension; quoted SemVer.
- `tags` (optional): YAML list of short strings.
- `resource` (optional): URI to the underlying asset (e.g., issue URL, repo path) where one exists.

Other existing metadata keys (such as `issue_url`, `status`, `linked-prd`) are preserved alongside these fields.

**Doc-status vocabulary (normative in v0.2).** `status:` takes exactly one of OKF v0.2's values: `draft | stable | deprecated`. v0.1 was value-agnostic here; v0.2 is not.

| Legacy value | Replacement |
|:---|:---|
| `approved` | `stable` |
| `active` | `stable` |
| `superseded` | `deprecated` |
| `stale` | `deprecated` |
| `draft` | `draft` (unchanged) |

Work-status (`status:*` GitHub labels / BACKLOG `Status`) **never** appears in doc frontmatter, and the editorial enum never appears on issues. **Exception:** the `discovery-brief` type keeps its routing-outcome vocab (`ready-for-prd | exit-bug | exit-spike | dropped`), which records a routing decision rather than editorial maturity.

`sources` (optional): supersedes a body `# Citations` / `## Sources` section. Each entry requires `resource`; `id`, `title`, `author`, `last_modified` are optional.

`verified` (optional): a list of independent confirmation events, `[{by, at}]`. Distinct from `generated` — `generated` records who *produced* a document, `verified` who *checked* it. In `.memory/`, a trust-tag promotion (`[ASSUMED]` → `[PATTERN]`/`[CONFIRMED]`) appends an entry (see `memory-protocol.md` §2).

`stale_after` (optional): an absolute ISO 8601 instant. The document is stale when `now >= stale_after`. Use it only where staleness is genuinely checkable — `.memory/STATUS.md` and sprint documents — never as a decorative field.

**Not adopted:** OKF v0.2's attestation family (`runtime`, `parameters`, `computation`, `executor`, `attester`). It exists for attested computation over data assets; StratOS has no such artifact. Recorded so the decision is not re-litigated.

### 2.1 Activation contract (`rule` files)

Files in `.agents/rules/` are **out of OKF scope** (§1) but still declare when they activate, via `trigger`:

| `trigger` | Meaning |
|:---|:---|
| `always_on` | Always in context. |
| `glob` | Active only for files matching `globs`. Requires `globs`. |
| `model_decision` | The model decides from `description`. |

`glob` rules carry host-native activation fields as a **superset** so one file works in both hosts (each ignores the other's keys):

- `globs` (Antigravity): comma-separated patterns, **unquoted**, e.g. `globs: .memory/**/*,docs/**/*`.
- `paths` (Claude Code): YAML list mirroring `globs`.

**Antigravity** reads `trigger`/`globs` from `.agents/rules/`. **Claude Code** has no `trigger` concept; `glob` rules activate via `paths` from `.claude/rules/`, while `always_on`/`model_decision` rules surface through the `AGENTS.md` §8 pointer directory. Cursor, Codex, Devin and Copilot reach rules through `AGENTS.md`, which they all read.

**Skill invocation is not governed here.** A skill's manual-only status is declared in its own frontmatter — `disable-model-invocation`, `triggers`, and the Codex `agents/openai.yaml` sidecar. See `AGENTS.md` §1 and §8.

## 3. Type Registry

**Registered types apply only inside the bundle scope (§1).** A template that *mints* an
in-scope document carries the emitted document's `type:` — that is the artifact's type,
not the template's, and it stays. Framework artifacts outside the scope (constitution,
rules, skills, non-template references) carry **no** `type:` at all.


Agents must use the following defined types. If no existing type fits, the agent must propose a new type to the user and, upon confirmation, add it to this registry. Agents must never invent or use a type silently.

| `type` | Applies to | Extra fields beyond the base contract |
|:---|:---|:---|
| `status` | `STATUS.md` | — |
| `backlog` | `BACKLOG_MAP.md` | — |
| `learnings` | `LEARNINGS.md` | — |
| `glossary` | `GLOSSARY.md` | — |
| `architecture` | `ARCHITECTURE.md` | — |
| `database-schema` | `DATABASE_SCHEMA.md` | — |
| `design-rules` | `DESIGN_RULES.md` | — |
| `design` | `DESIGN.md` | conforming (tolerated by the `@google/design.md` linter) |
| `prd` | `docs/prds/*.md` | `resource` (issue URL), `status` |
| `discovery-brief` | `docs/discovery/*.md` (**excluding** `*.map.md`) | `status`, `linked-prd` |
| `research` | `docs/research/*.md` | — |
| `interface-design` | `docs/design/*.md` (interface designs) | — |
| `design-doc` | `docs/design/*.md` (other design docs) | — |
| `roadmap` | `docs/ROADMAP.md` | — |
| `audit-report` | `docs/audits/*.md` | — |
| `concept-map` | `docs/discovery/*.map.md` | `status`, `slug` |
| `plan` | `docs/plans/*.md` | — |
| `proposal` | `docs/proposals/*.md`, `docs/nightly/*.md` | — |
| `reference` | in-scope reference material under `docs/` (e.g. `docs/okf-spec-essentials.md`) | — |

## 4. Reserved Files
- **Root `index.md`**: The bundle entrypoint. It is the **only** file carrying `okf_version: "0.2"`.
- **Directory `index.md` files** (e.g. `.memory/index.md`, `docs/prds/index.md`): Used for progressive disclosure. These files must **not** carry frontmatter and are listings only.
- **`log.md`**: If present, carries change history. It must not contain frontmatter.
- **Non-markdown files inside the bundle scope are excluded.** `docs/**/*.html` (e.g. `docs/ROADMAP.html`, rendered PRDs), `docs/audits/.last-run.json`, and `.memory/*.jsonl` (e.g. `jules-ledger.jsonl`) are durable and in-scope by directory but **cannot carry frontmatter**. They are not concept documents and are exempt from §2.

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
