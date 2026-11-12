---
type: discovery-brief
title: "Discovery: Obsidian-compatible document linking and knowledge graph architecture"
description: "Frames the adoption of Obsidian-compatible wikilinks, OKF v0.2 MOCs, setup/update opt-in scaffolding, and validate_memory.py link reconciliation."
generated:
  by: 1b-concept-framing
  at: "2026-11-12T11:01:00-05:00"
status: ready-for-prd
slug: obsidian-document-linking
linked-prd: BT-233
concept-map: —
version: "5.3.0"
---

# Discovery: Obsidian-compatible document linking and knowledge graph architecture

## Ask (verbatim)
> /0a-start-session and review BT-233 (the initial plan is older than StraTOS v5.3 run /1b-concept-framing - I'm currently using the open google introduced OKF framework which I want to continue but also a older IDE oriented VS Code  extension linking/graph logic. I want to adopt a document linking method that works with Obisidian so users can easier navigate through their docs & memory markdownfiles e.g. read research docs and prds and see their relationship. I want this to be a opt-in during each setup and update flow. I want a onetime effort for this repo and my own consumer reop Cleantechhub to rewrite existing links but don't need a general backward compatibility as no other user is using StratOS currently.

## Vocabulary

- **Document Wikilink:** A double-bracketed note reference (`[[<doc-stem>]]` or `[[<doc-stem>|<alias>]]`, with minimum vault-root path qualification `[[docs/<folder>/<doc-stem>|<alias>]]` for disambiguating collisions) resolving to a distinct git-tracked markdown document in `docs/**` or `.memory/**`.
- **Memory Handle:** An internal location-agnostic cross-reference token `[[<ID>]]` (where ID is `L-xxx`, `A-xxx`, `DR-xxx`, or `G-xxx`), defined inside consolidated `.memory/*.md` files and parsed deterministically by `validate_memory.py` without requiring brittle synthetic block anchors (`^ID`).
- **Map of Content (MOC):** Directory-level `index.md` files serving as clustering hubs and progressive disclosure entrypoints without frontmatter, conforming to OKF v0.2 §4.
- **Vault Scoping:** Preconfigured Obsidian configuration filters (`path:docs OR path:.memory` in `graph.json` and dynamic `userIgnoreFilters` in `app.json` ignoring code, build artifacts, and archive directories) ensuring only active documentation and memory participate in the vault.
- **Setup/Update Opt-In:** An interactive prompt and CLI switch (`--vault [none|obsidian|okf-html]`) in `scaffold.py` managing `.obsidian/` assets during `stratosphere-setup` and `stratosphere-update` flows.
- **One-Time Link Migration:** A deterministic migration script (`scripts/migrations/migrate_obsidian_links.py`) with `--dry-run` and `--write` flags that rewrites legacy markdown file links and rebuilds MOCs across `Stratosphere-OS` and `CleanTechHub`.

## Actor
Full-stack software engineer and system architect building applications with Google Antigravity, Claude Code, or Cursor, navigating interconnected markdown documentation, PRDs, research explorations, and memory governance rules.

## Problem
Human creators experience cognitive friction and mental fragmentation when navigating interconnected markdown repositories across `docs/` and `.memory/`. While headless agents navigate via AST search and targeted grep, human developers lack an effortless, zero-daemon visual map of document relationships, PRD-to-research lineages, and architectural dependencies.

**Scope facets:**
- **Syntax & Validator Incoherence (Root Cause):** The memory validator (`validate_memory.py`) treats all bracketed tokens strictly as internal `.memory/` handles (`L-xxx`, `A-xxx`), triggering false-positive dangling reference errors whenever documents use standard document wikilinks.
- **Tooling Maintenance Drag (Architectural Waste):** Legacy local HTML visualizers (`okf_view.py`) and custom IDE webviews require runtime rendering processes and ongoing maintenance overhead while offering zero utility to headless CLI agents.
- **Progressive Disclosure Absence (Symptom):** Directory-level Maps of Content (MOCs) are ungenerated, forcing agents and humans to traverse raw directory listings rather than structured relationship hubs.

## Established Facts (as of 2026-11-12)
- On branch `bt233_obsidian_document_linking` with BT-233 transitioned to `status:in progress` — source: `git branch --show-current`, `gh issue view 233`.
- `validate_memory.py` currently flags any bracketed `[[token]]` not defined in `.memory/*.md` as a dangling reference error — source: `src/scripts/validate_memory.py:598-604`.
- Open Knowledge Format (OKF v0.2 §7) specifies standard markdown links between concepts but explicitly requires consumers to tolerate broken or bracketed links (e.g. `[[G-001]]`) — source: `docs/okf-spec-essentials.md`.
- Empirical stem collision scan across `docs/` and `.memory/` detected existing duplicate stems (`host-agnostic-skill-distribution`, `0f-walk-me-through-concept`, `README.md`, `index.md`) — source: `Get-ChildItem -Recurse -Filter *.md | Group-Object BaseName`.
- Obsidian shortest-path link resolution natively supports minimum path qualification relative to the vault root (e.g. `[[docs/discovery/host-agnostic-skill-distribution]]`) to disambiguate collisions — source: Obsidian link resolution specification.
- Project scaffolding and update routines are unified under `scaffold.py` (`stratosphere-setup` and `--update`) — source: `src/scripts/scaffold.py:596-788`.
- Stratosphere-OS system version is `5.3.0` — source: `build/build.py:VERSION`.

## Chosen Framing
**Developer Experience & Navigation Gap (Cognitive Ergonomics):**
We commit to providing a decoupled, out-of-process knowledge graph experience in Obsidian while maintaining strict OKF v0.2 compliance. The filesystem (`docs/` and `.memory/`) serves as a dual-citizen knowledge base: token-efficient, deterministic markdown for AI agents, and instant, interactive visual graph exploration for humans.

**Rejected framings:**
- *Pure Validator Tolerance (Syntax-only framing):* Rejected because merely patching `validate_memory.py` to ignore `[[stem]]` without configuring Obsidian vaults, graph color taxonomies, and MOCs leaves human navigation fragmented.
- *Total Tooling Elimination (Dropping all visualizers):* Rejected because human creators still need a visual relationship map, and CI environments still benefit from automated MOC index rebuilding.

## Success State
1. **Scaffold Opt-in:** Running `python src/scripts/scaffold.py --vault obsidian` (or selecting Obsidian in setup/update prompts) scaffolds a preconfigured `.obsidian/` directory (`app.json`, `graph.json`, `core-plugins.json`) and updates `.gitignore` to track shared settings while ignoring workspace caches.
2. **Deterministic Link Validation:** `python src/scripts/validate_memory.py` passes cleanly on both memory handles (`[[L-001]]`) and document wikilinks (`[[BT-108-host-agnostic-skill-distribution]]` or `[[docs/discovery/host-agnostic-skill-distribution|Skill Distribution]]`), while failing with explicit errors on genuinely dangling references or unresolvable stems.
3. **Graph Scoping & Visual Clustering:** Opening the repository root in Obsidian renders a graph scoped strictly to `docs/` and `.memory/`, with nodes color-coded by OKF `type` and clustered cleanly around directory `index.md` MOC hubs.
4. **Migration Execution:** Running `python scripts/migrations/migrate_obsidian_links.py --write` rewrites existing Markdown links across `Stratosphere-OS` and `CleanTechHub` into valid Obsidian wikilinks and regenerates all directory `index.md` MOCs without broken references.

## Prior Art
- **BT-233:** Original parked slice under BT-242 (`Obsidian-compatible docs vault & backlink graph architecture`).
- **`docs/proposals/obsidian-vault-and-agent-linking-proposal.md`:** Architectural proposal for Obsidian integration (v2.0.0).
- **[[A-005]] [LAW]:** Issue state lives on GitHub only; `BACKLOG_MAP.md` is retired; memory links operate strictly over `docs/**` and `.memory/**`.
- **OKF v0.2 Spec:** `docs/okf-spec-essentials.md` and `src/rules/okf-protocol.md`.

## Non-Goals (early signal)
- Real-time bidirectional sync daemon between Obsidian UI and GitHub issue tracker.
- General backward compatibility for third-party StratOS consumers (none exist).
- Mandating Obsidian installation for headless CI or agent-only environments.
- Proprietary Obsidian canvas formats replacing standard markdown concepts.

## Decoupled Follow-ups
- Obsidian Local REST API / MCP plugin integration for automated agent graph queries — candidate.
- Automated visual `.canvas` layout generation for architectural maps — candidate.

## Constraints & Settled Decisions
- **Authoring Rule:** Agents must author document wikilinks using `[[<doc-stem>|<alias>]]` inline in prose sentences, and bare `[[<doc-stem>]]` in reference lists. If stem is duplicated, minimum path prefix is required — why: eliminates agent relative-path calculation errors while preserving natural prose readability.
- **Memory Handle Integrity:** Memory handles remain location-agnostic conceptual IDs (`[[L-xxx]]`, `[[A-xxx]]`, `[[G-xxx]]`) indexed by AST search; synthetic `^ID` block anchors are rejected — why: agents frequently drop synthetic block anchors during text editing, causing cascading link failures.
- **OKF v0.2 Retention:** OKF frontmatter and directory `index.md` MOCs remain authoritative; `okf_view.py` is retained as the MOC index builder and headless fallback — why: maintains open standard conformance and CI validation.
- **Vault Root & Dual Scoping:** Vault root is the repository root; `graph.json` applies `"search": "path:docs OR path:.memory"` and `scaffold.py` dynamically populates `userIgnoreFilters` in `app.json` (including `archive/`) — why: automatically ensures client code folders and archived notes do not clutter the documentation vault.
- **Setup & Update Switch:** `scaffold.py` introduces an interactive switch and `--vault [none|obsidian|okf-html]` CLI argument — why: guarantees zero unwanted overhead for users who prefer raw markdown.
- **One-Time Migration Tooling:** A dedicated migration script (`migrate_obsidian_links.py`) rewrites existing links and rebuilds MOCs for `Stratosphere-OS` and `CleanTechHub` — why: avoids runtime backward-compatibility shims.

## Open Questions
1. Should `validate_memory.py` issue a warning or a hard error when a bare `[[doc-stem]]` matches multiple files in `docs/**`? — owner: implementer, blocking: N.
2. Should directory `index.md` MOCs use shortest-path wikilinks or relative markdown links to list their child documents? — owner: implementer, blocking: N.

## Riskiest Assumption
- **Riskiest Assumption:** Document stems across nested directory hierarchies (`docs/**` and `.memory/**`) are sufficiently unique for shortest-path wikilinks (`[[doc-stem]]`) to resolve deterministically in Obsidian and `validate_memory.py` without path qualification.
- **Why Fatal:** Active stem collisions (`host-agnostic-skill-distribution`, `0f-walk-me-through-concept`, `index.md`) cause non-deterministic resolution in Obsidian and false ambiguity errors in `validate_memory.py`.
- **Cheapest Test:** read-only production probe
- **Est. setup time:** 1 day (probe completed during concept framing)
- **Status:** survived (resolved via shortest-path disambiguation rule and archive folder exclusion in vault ignore filters).

## Recommended Next Step
- [x] `write-prd` — problem is sharp, PRD-worthy (proceed to `/2a-write-prd` for BT-233)
- [ ] `create-issue` Build slice — this is a bug
- [ ] `create-issue` Spike — research needed first
- [ ] Dropped — do not build
