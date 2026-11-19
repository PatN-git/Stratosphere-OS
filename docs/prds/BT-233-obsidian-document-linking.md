---
type: prd
title: "BT-233: Obsidian-Compatible Docs Vault & Backlink Graph Architecture"
description: "Product Requirements Document establishing an opt-in Obsidian vault configuration over docs/ and .memory/, dual-track document wikilink and memory handle validation, OKF v0.2 MOC clustering, and link migration tooling."
bt: BT-233
generated:
  by: 2a-write-prd
  at: "2026-11-12T11:17:00-05:00"
resource: https://github.com/PatN-git/Stratosphere-OS/issues/233
discovery: docs/discovery/obsidian-document-linking.md
research: —
status: stable
version: "5.3.0"
---

# BT-233: Obsidian-Compatible Docs Vault & Backlink Graph Architecture

> [!NOTE]
> **Legend & Marker Definitions:**
> - `[BASELINE]` ↔ `scope:baseline` (high-pain, well-served — build to not lose)
> - `[DIFFERENTIATOR]` ↔ `scope:differentiator` (high-pain, under-served — build to win)
> - `[DEFERRED]` ↔ `scope:deferred` (temporal deferral, mirrored in §9, not sliced in this version)
> - `[unbacked]`: Scope tag or score assigned by judgment without research backing (confirmed by user in concept framing)
> - `[unverified estimate — confirm]`: A figure stated without a cited research source
> - `[Unknown]`: Data/value that is missing or not publicly available

## 1. Problem
- **Current experience:** Human creators experience cognitive friction and mental fragmentation when navigating interconnected markdown repositories across `docs/` and `.memory/`. While headless agents navigate via AST search and targeted grep, human developers lack an effortless, zero-daemon visual map of document relationships, PRD-to-research lineages, and architectural dependencies.
  - *Syntax & Validator Incoherence (Root Cause):* The memory validator (`validate_memory.py`) treats all bracketed tokens strictly as internal `.memory/` handles (`L-xxx`, `A-xxx`), triggering false-positive dangling reference errors whenever documents use standard document wikilinks (`[[<doc-stem>]]`).
  - *Tooling Maintenance Drag (Architectural Waste):* Legacy local HTML visualizers (`okf_view.py`) and custom IDE webviews require runtime rendering processes and ongoing maintenance overhead while offering zero utility to headless CLI agents.
  - *Progressive Disclosure Absence (Symptom):* Directory-level Maps of Content (MOCs) are ungenerated, forcing agents and humans to traverse raw directory listings rather than structured relationship hubs.
- **Who is affected:** Full-stack software engineers and system architects building applications with Google Antigravity, Claude Code, or Cursor, navigating interconnected markdown documentation, PRDs, research explorations, and memory governance rules.
- **Cost of inaction:** Developers waste hours mentally tracing architectural dependencies or maintaining fragile local HTML visualizers; documents remain disconnected silos; and agents cannot author natural wikilinks without failing deterministic memory validation.

## 2. Solution (user view)
Stratosphere-OS provides an optional, out-of-process knowledge graph experience via Obsidian, treating project documentation and memory as a dual-citizen knowledge base. Developers can navigate an interactive, color-coded visual graph of PRDs, research docs, and system architectural rules clustered around directory-level Maps of Content without running background daemons. AI agents and human authors write natural document wikilinks without brittle relative paths, while automated validation ensures all links resolve to real files without breaking memory cross-references. Teams can opt in during setup or update flows to generate shared vault settings, and maintainers can run a one-time migration utility to upgrade legacy links across existing repositories.

## 3. Goals
- **Zero-Daemon Visual Navigation:** Provide an instant, interactive visual graph of documentation and memory relationships in Obsidian without requiring background server processes or IDE-specific webview extensions.
- **Dual-Citizen Link Interoperability:** Enable both AI agents and human creators to write intuitive document wikilinks that resolve cleanly in Obsidian and pass deterministic memory validation.
- **Zero-Friction Scaffolding Opt-In:** Allow developers to opt in or out of Obsidian vault configuration during project setup and update flows, ensuring zero unwanted file overhead for plain-markdown users.
- **Automated Directory Progressive Disclosure:** Establish directory-level Maps of Content (MOCs) that serve as cluster centroids in the knowledge graph and low-token entrypoints for AI agents.
- **Safe Repository Link Modernization:** Provide a deterministic one-time migration capability to upgrade existing repositories to Obsidian-compatible wikilinks and MOCs without broken references.

## 4. Non-Goals
- **Real-Time Issue Tracker Synchronization Daemon:** Principled exclusion — No background synchronization daemon will be built between Obsidian UI and GitHub Issues; issue tracking remains strictly external per [[A-005]].
- **Mandatory Obsidian Runtime Requirement:** Principled exclusion — Obsidian installation will never be mandated for headless CI, terminal-only environments, or agent execution; markdown remains fully functional without it.
- **Proprietary Canvas and Note Formats:** Principled exclusion — StratOS will not adopt proprietary `.canvas` or binary formats that replace open markdown concepts or violate OKF v0.2.
- **General Backward Compatibility for Third-Party Consumers:** Principled exclusion — Backward compatibility shims for third-party consumers are omitted as StratOS has no external third-party installations.
- **Anti-Dark-Pattern & Vendor Neutrality:** Principled exclusion — StratOS will never enforce proprietary editor lock-in, telemetry collection, or closed-source plugin requirements for knowledge graph management.

## 5. Success Signals
- Clean validation pass by the memory linter verifying both memory handles and document wikilinks with zero false-positive dangling errors.
- Visual knowledge graph in Obsidian cleanly displaying active documentation nodes color-coded by OKF type and clustered around directory MOC centroids.
- Zero extra files or overhead introduced into projects whose creators select plain markdown during setup or update routines.
- 100% automated link conversion and MOC generation verified on test repositories via the migration utility without manual remediation.

## 6. User Stories

### Journey Step 1: Project Scaffolding & Vault Initialization
1. **[BASELINE]** As a software engineer initializing or updating a project, I want an explicit opt-in switch to scaffold an Obsidian vault configuration, so that my repository remains pure markdown without unnecessary files if I do not use Obsidian. (ODI: 9.3 [HIGH] [unbacked])
2. **[BASELINE]** As a developer adopting Obsidian, I want shared vault configurations tracked in version control while user workspace state and local caches are ignored, so that my team shares consistent graph visual styling without workspace file churn. (ODI: 8.7 [HIGH] [unbacked])
3. **[DEFERRED]** As an enterprise developer, I want custom vault presets with community plugin configurations synced across team workspaces, so that organization-specific Obsidian extensions are standardized. (ODI: - [unbacked])

### Journey Step 2: Knowledge Graph Visualization & Exploration
4. **[DIFFERENTIATOR]** As a system architect opening the repository in Obsidian, I want to explore an interactive visual graph scoped strictly to active documentation and memory, color-coded by concept type, so that I can visually trace architectural relationships and decision lineages without noise from source code, build artifacts, or archives. (ODI: 9.1 [HIGH] [unbacked])
5. **[BASELINE]** As a developer navigating through folders, I want directory-level Maps of Content (MOCs) serving as natural centroid hubs in the graph view, so that documents cluster cleanly around their parent topic areas. (ODI: 8.5 [HIGH] [unbacked])
6. **[DEFERRED]** As a visual thinker, I want automated spatial canvas board generation reflecting architecture topologies from markdown documents, so that I can arrange concepts visually on an infinite 2D plane. (ODI: - [unbacked])

### Journey Step 3: Document Authoring & Deterministic Validation
7. **[BASELINE]** As an author or AI agent drafting documentation, I want to use document wikilinks to reference other documents without computing brittle relative paths, so that cross-document links are human-readable and resilient to file reorganization. (ODI: 9.2 [HIGH] [unbacked])
8. **[BASELINE]** As a developer verifying repository integrity, I want the memory validation linter to verify that document wikilinks resolve to existing files while preserving strict bidirectional reciprocity checks for memory handles, so that dangling documents are caught without triggering false-positive memory errors. (ODI: 9.4 [HIGH] [unbacked])
9. **[BASELINE]** As an author referencing documents with colliding filenames across different folders, I want to use minimum folder path qualification so that both Obsidian and the validator resolve ambiguous links deterministically. (ODI: 8.4 [MED] [unbacked])
10. **[DEFERRED]** As an AI agent executing in the terminal, I want to query Obsidian's local REST API directly during runtime execution, so that I can traverse the live graph programmatically. (ODI: - [unbacked])

### Journey Step 4: Existing Repository Migration
11. **[BASELINE]** As a repository maintainer upgrading an existing StratOS repository, I want a deterministic migration utility to rewrite legacy markdown links into Obsidian wikilinks and regenerate directory MOCs with a dry-run preview, so that existing documentation is converted safely without manual editing. (ODI: 8.9 [HIGH] [unbacked])

## 7. Constraints & Direction
- **Vault Root & Scope Boundary:** The repository root serves as the Obsidian vault root. Graph visualization and backlink exploration must be strictly scoped to documentation and memory spaces through graph query search filters and file ignore configurations, ensuring source code, build outputs, and archives are excluded.
- **Universal Plain Markdown:** Plain Markdown is universal: all documentation and memory files must remain 100% functional, readable, and editable without Obsidian installed.
- **Zero-Friction Opt-In:** Vault initialization and updates must remain strictly opt-in via interactive CLI prompt and command-line argument during project onboarding and refresh workflows.
- **Git Hygiene for Vault Settings:** Shared vault configuration schemas must be tracked in version control while user workspace state and local caches are ignored by version control.
- **Authoring Syntax Standard:** Authoring syntax standardizes on wikilinks `[[<doc-stem>|<alias>]]` inline in prose sentences, bare `[[<doc-stem>]]` in reference lists, and minimum vault-root path qualification `[[docs/<folder>/<doc-stem>|<alias>]]` for collision disambiguation.
- **Memory Handle Integrity:** Memory handles remain location-agnostic conceptual IDs (`[[L-xxx]]`, `[[A-xxx]]`, `[[G-xxx]]`, `[[DR-xxx]]`) indexed by AST search; synthetic block anchors (`^ID`) are prohibited.
- **OKF v0.2 MOC Centroids:** Directory-level `index.md` files conform to OKF v0.2 §4 as frontmatter-free Maps of Content (MOCs), acting as cluster centroids in the knowledge graph.
- **External Issue Provenance:** Bare issue identifiers (`BT-xxx`) remain unbracketed plain text as external tracker provenance pointers.
- **Deterministic Migration Tooling:** A deterministic migration capability must rewrite legacy markdown links and rebuild MOCs with dry-run verification before writing changes.
- **Proposed Architectural Law ([[A-006]]):** Propose [[A-006]] for `[LAW]` structural decision: Knowledge base linking strictly bifurcates into (1) Location-agnostic conceptual memory handles (`[[L-xxx]]`, `[[A-xxx]]`, `[[G-xxx]]`, `[[DR-xxx]]`) validated with bidirectional reciprocity, and (2) Document wikilinks (`[[<doc-stem>]]` or `[[<doc-stem>|<alias>]]`, with minimum vault-root path qualification `[[docs/<folder>/<doc-stem>|<alias>]]` on collision) resolving to git-tracked markdown files without reciprocity. Issue identifiers remain bare plain text (`BT-xxx`). Repository root is the vault root, scoped via documentation and memory search filters. Synthetic block anchors (`^ID`) are prohibited.
- **Boundaries:**
  - **Always:**
    - Always treat standard markdown as the primary source of truth, fully operational in headless and terminal environments without Obsidian.
    - Always keep vault configuration opt-in during project scaffolding and update flows.
    - Always use minimum path prefix disambiguation when referencing colliding document stems across different directories.
    - Always maintain memory handles as location-agnostic IDs resolved via AST search rather than block-level anchors.
    - Always run link migration in dry-run mode prior to applying in-place writes.
  - **Ask first:**
    - Ask first before executing in-place link rewrites on repositories with uncommitted working tree changes.
    - Ask first before introducing third-party Obsidian community plugins or non-core vault dependencies.
  - **Never:**
    - Never mandate Obsidian installation or running background daemons for CI or agent execution.
    - Never inject synthetic block anchors (`^ID`) into memory documents.
    - Never treat bare issue identifiers as bracketed wikilinks.
    - Never include application source code, build outputs, or archived notes in vault knowledge graph queries.
- **Refs:** [[A-005]], [[G-005]], [[G-006]], [[L-004]]

## 8. Definition of Done
- Project setup and update flows provide an interactive choice and CLI argument for Obsidian vault scaffolding, correctly creating git-tracked shared configurations while ignoring workspace caches.
- Memory validation deterministically parses and verifies both location-agnostic memory handles (`[[L-xxx]]`, `[[A-xxx]]`, `[[G-xxx]]`, `[[DR-xxx]]`) and document wikilinks (`[[<doc-stem>]]` or `[[docs/<folder>/<doc-stem>]]`), passing on valid references and failing on unresolvable stems.
- Bare issue identifiers (`BT-xxx`) are ignored by the link validator as external tracker provenance pointers.
- Opening the repository root in Obsidian renders a scoped knowledge graph filtered strictly to documentation and memory, excluding code, build artifacts, and archives.
- Directory `index.md` files conform to OKF v0.2 §4 as frontmatter-free MOCs that act as centroid hubs in Obsidian graph view.
- A deterministic link migration utility exists, supporting dry-run previews and in-place rewriting of legacy markdown links and MOC regeneration.
- Comprehensive automated test coverage verifies setup/update vault scaffolding, dual-mode link validation, collision disambiguation, and link migration routines.

## 9. Out of Scope
- **Deferred:** As an enterprise developer, I want custom vault presets with community plugin configurations synced across team workspaces (from §6 story #3).
- **Deferred:** As a visual thinker, I want automated spatial canvas board generation reflecting architecture topologies from markdown documents (from §6 story #6).
- **Deferred:** As an AI agent executing in the terminal, I want to query Obsidian's local REST API directly during runtime execution (from §6 story #10).
- **Decoupled Follow-up: Interactive Canvas Generation:** Automated generation of `.canvas` visual architecture layouts is deferred to future visual tooling enhancements.
- **Decoupled Follow-up: Agent REST Graph Traversal:** Integration with Obsidian Local REST API or MCP servers for runtime agent graph querying is deferred to subsequent agent tooling epics.

## 10. Open Questions
1. Should `validate_memory.py` issue a warning or a hard error when a bare `[[doc-stem]]` matches multiple files in `docs/**`? — Resolved: Warning with suggested minimum path prefix to disambiguate.
2. Should directory `index.md` MOCs use shortest-path wikilinks or relative markdown links to list their child documents? — Resolved: Shortest-path wikilinks `[[doc-stem]]` (conforming to Obsidian MOC hubs and tolerated by OKF v0.2 §7).

## 11. Further Notes
- **RAT Carry-Over (Riskiest Assumption):**
  - *Assumption:* Document stems across nested directory hierarchies (`docs/**` and `.memory/**`) are sufficiently unique for shortest-path wikilinks (`[[doc-stem]]`) to resolve deterministically in Obsidian and `validate_memory.py` without path qualification.
  - *Why Fatal:* Active stem collisions (`host-agnostic-skill-distribution`, `0f-walk-me-through-concept`, `index.md`) cause non-deterministic resolution in Obsidian and false ambiguity errors in `validate_memory.py`.
  - *Cheapest Test:* Read-only empirical stem collision scan across `docs/` and `.memory/` via production probe.
  - *Est. Setup Time:* 1 day (completed during concept framing on 2026-11-12).
  - *Status:* **Survived**. Empirical scan detected duplicates, which were successfully resolved by defining the minimum vault-root path prefix disambiguation rule (`[[docs/<folder>/<doc-stem>|<alias>]]`) and excluding `archive/` folders in vault ignore filters.
- **Prior Art & Heritage:** Evolved from parked slice under BT-242 and proposal `docs/proposals/obsidian-vault-and-agent-linking-proposal.md`. Aligned with [[A-005]] (removal of `BACKLOG_MAP.md`, issue state on GitHub) and OKF v0.2 specifications.

## 12. Viability & Cost
- **Complexity Estimate:** 4 / 10 (Anchors: simple CRUD/to-do list ≈ 2, complex offline sync/Instagram ≈ 9. Rationale: Scaffolding configuration templates in `scaffold.py`, regex and resolution enhancements in `validate_memory.py`, and a deterministic migration script; well-isolated file operations with minimal architectural blast radius).
- **Cost Table:**
  | Service / Resource | Free Tier Limit | Cost Threshold / Pricing | Source / Citation |
  | :--- | :--- | :--- | :--- |
  | Obsidian Desktop Application | Free for personal and non-commercial use | Free / $0.00 [Commercial license $50/user/yr if applicable] | [Obsidian Pricing Policy](https://obsidian.md/pricing) [unverified estimate — confirm] |
  | Local Filesystem & Git Storage | N/A (Local repo storage) | $0.00 (Zero hosting or cloud infrastructure cost) | Local disk / Zero daemon |
- **Architecture Cost Warning:** Zero ongoing runtime infrastructure cost. The feature relies purely on local-first static markdown files, static JSON configuration schemas, and offline Python scripts. No background daemons, servers, or paid API endpoints are introduced.
- **"Is There Money Here?" (Market Demand Signals):** Strong organic demand in the developer community for Obsidian-based personal knowledge management (PKM) and second brains, especially among developers utilizing AI coding assistants (Google Antigravity, Claude Code, Cursor) who seek zero-daemon visual maps of complex software architecture and decision records.
- **Profit Alignment:** Pure developer enablement and open-source empowerment. StratOS does not sell proprietary plugins or gate knowledge graph features; value accrues directly to developers through reduced cognitive friction, faster architectural onboarding, and elimination of brittle custom visualizer maintenance.
