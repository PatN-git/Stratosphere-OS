# OKF v0.1 — Spec Essentials (reference)

> **Why this file exists:** a faithful, condensed capture of the normative parts of
> Open Knowledge Format **v0.1** so that StratosphereOS's OKF conformance can be
> diffed against future spec releases. When OKF publishes a new version, compare it
> against this file and update the "Impact on StratosphereOS" notes.
>
> - **Source spec:** https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf (`SPEC.md`, `README.md`)
> - **Announcement:** https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/
> - **Spec version captured:** `0.1`
> - **Captured:** 2026-06-16
> - **Owner:** Google Cloud Data Cloud team (open, vendor-neutral spec)

---

## Core model

| Term | Definition (v0.1) |
|---|---|
| **Knowledge Bundle** | A self-contained, hierarchical collection of knowledge documents. The unit of distribution. |
| **Concept** | A single unit of knowledge within a bundle. Represented as **one markdown document**. |
| **Concept ID** | The file path **minus** the `.md` extension. e.g. `tables/users.md` → `tables/users`. |

One concept = one file. (This is the model StratosphereOS deliberately does **not** follow for its
aggregated registries — see the adoption plan; it accepts file-granular concepts as the tradeoff.)

## Frontmatter

Every concept document MUST begin with a YAML frontmatter block.

- **Required (the only mandatory field):**
  - `type` — short string identifying the concept kind. **Not** registered centrally; producers define their own vocabulary.
- **Recommended (priority order):**
  - `title` — human-readable display name
  - `description` — single-sentence summary
  - `resource` — URI uniquely identifying the underlying asset
  - `tags` — YAML list of short strings
  - `timestamp` — ISO 8601 datetime of last meaningful change
- **Extension rule:** producers MAY add arbitrary keys; **consumers MUST preserve unknown keys when round-tripping.**
  (This is what makes StratosphereOS's `[[ID]]`, trust tags, supersession, and a `stratos_version` field all spec-legal.)

## Body

Standard markdown. Conventional (non-enforced) section headings include `# Schema`, `# Examples`, `# Citations`.

## Reserved filenames

| Filename | Purpose | Frontmatter? |
|---|---|---|
| `index.md` | Directory listing for progressive disclosure. Body: `# Section Heading` then `* [Title](url) - description`. | **None**, except the **root** `index.md`, which is the **only** place `okf_version` may be declared. |
| `log.md` | Change history, newest first, grouped by ISO 8601 dates: `## 2026-05-22` then `* **Update**: …` / `* **Creation**: …`. | None. |

All other `.md` files are concepts.

## Cross-linking

- Links between concepts are **standard markdown links**. A link asserts a relationship; the *kind* is conveyed by surrounding prose, **not** by a typed-edge schema.
- **Absolute (bundle-relative)** links begin with `/` — the **recommended** form: `[customers](/tables/customers.md)`.
- **Relative** links are allowed: `[neighbor](./other.md)`.
- **Consumers MUST tolerate broken links.** (So StratosphereOS `[[G-001]]`-style links are legal but invisible/broken to OKF consumers — tolerated, not resolved.)

## Conformance (§9)

A bundle conforms to OKF v0.1 **if**:
1. Every non-reserved `.md` file contains parseable YAML frontmatter.
2. Every frontmatter block contains a **non-empty `type`** field.
3. Reserved filenames (`index.md`, `log.md`) follow their structures.

Consumers **MUST NOT** reject a bundle because of:
- Missing optional frontmatter fields
- Unknown `type` values
- Unknown additional frontmatter keys
- Broken cross-links

Everything else is **SHOULD**-level soft guidance.

## Versioning (§11)

- Scheme: `<major>.<minor>`.
- **Minor** bump = backward-compatible additions.
- **Major** bump = breaking changes.
- A bundle may declare its target version via `okf_version: "0.1"` — **only** permitted in the **root** `index.md` frontmatter.

## Distribution

A bundle may be shipped as: a git repository (recommended), a tarball/zip, or a subdirectory within a larger repo.

## Reference tooling shipped with the spec (not required to conform)

- **Enrichment agent** — walks a source (BigQuery first), drafts concept docs, second LLM pass enriches from seed URLs.
- **Static HTML visualizer** — single self-contained file; force-directed graph of concepts colored by `type`, with backlinks/search/filter.
- **Google Knowledge Catalog** ingests OKF bundles natively.

---

## When a new OKF version ships — checklist

Compare the new `SPEC.md` against this file and re-check StratosphereOS for:

- [ ] Did **required** fields change (anything beyond `type`)? → update the frontmatter contract in `memory-protocol.md` + templates.
- [ ] Did the **reserved filenames** set or their structure change (`index.md`, `log.md`, new ones)? → update scaffolder + lint.
- [ ] Did **cross-link** rules change (e.g. typed edges, link resolution, broken-link tolerance)? → re-evaluate `[[ID]]` interop.
- [ ] Did **conformance criteria** (§9 MUST/MUST-NOT) tighten? → update `validate_memory.py` OKF check.
- [ ] Did **`okf_version` placement** rules change? → update root `index.md` template.
- [ ] Bump the bundle's declared `okf_version` in the root `index.md` template once we adopt the new version.
