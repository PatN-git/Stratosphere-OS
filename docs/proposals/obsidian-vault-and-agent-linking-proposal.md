---
name: obsidian-vault-and-agent-linking-proposal
title: "Proposal: Obsidian-Compatible Knowledge Vault & Backlink Graph for Agent-First Workflows"
description: Architectural proposal to replace IDE-coupled graph visualization with an optional, zero-overhead Obsidian vault configuration over docs/ and .memory/, harmonizing OKF index.md MOCs, hybrid memory atomicity, and local tracker backlinks.
type: proposal
version: "1.0.0"
generated:
  by: Antigravity
  at: 2026-11-02
---

# Proposal: Obsidian-Compatible Knowledge Vault & Backlink Graph for Agent-First Workflows

**Status:** Open Proposal / Parked for Implementation  
**Track:** 0 Constitution & Lifecycle Hardening (BT-223)  
**Target Delivery:** Stage 0 / Setup Expansion  
**Author:** Antigravity Architect  

---

## 1. Executive Summary & Problem Statement

Stratosphere-OS initially visualized its knowledge graph and concept links through a custom VS Code extension and an ad-hoc local HTML graph renderer (`okf_view.py`). 

With the shift toward **agent-first workflows**—where primary development occurs inside headless CLI agents (Claude Code, Aider), cloud harnesses (Devin), and modern AI coding environments (Google Antigravity, Cursor, Codex)—IDE-specific plugins have become a point of friction:
1. **Tool Heterogeneity:** CLI and headless agents cannot execute or benefit from VS Code webview extensions.
2. **Context Fragmentation:** Agents operate on raw disk files, while humans desire a visual, high-level map of backlinks, orphan notes, and dependency hierarchies without running custom local webservers.
3. **High Maintenance Overhead:** Maintaining custom VS Code webviews and graph layout engines (`okf_viewer/`) drains framework maintenance budget away from core deterministic lifecycle tooling.

This proposal specifies an **optional, zero-overhead Obsidian vault integration** that treats the existing filesystem (`docs/` and `.memory/`) as a dual-citizen knowledge base:
- **For Agents:** Clean, token-efficient, standard Markdown with wikilinks (`[[filename]]`) and directory-level `index.md` summaries for progressive disclosure.
- **For Humans:** Instant out-of-process graph visualization, backlinks, unlinked mentions, and interactive canvas exploration in Obsidian—without requiring any proprietary daemon or IDE lock-in.

---

## 2. Key Architecture Pillars

### 2.1 The Setup Switch (Zero-Friction Opt-In)
Nobody is forced to use Obsidian. Plain Markdown is the universal standard.
- During `stratosphere-setup` (Checkpoint 0 in `scaffold.py`), alongside `tracker: github | local`, a configuration prompt is introduced:
  ```text
  Knowledge Graph / Vault Support:
    1. Plain Markdown (Default: zero overhead, agents read raw docs directly)
    2. Obsidian Vault Config (Scaffold .obsidian/ with graph coloring, shortest-path links, and gitignore)
  ```
- **If Disabled:** No `.obsidian/` folder is generated. The repository remains pure markdown.
- **If Enabled:** A lightweight `.obsidian/` configuration directory is scaffolded with:
  - `app.json`: Configures wikilinks (`useMarkdownLinks: false`) and `newLinkFormat: "shortest"`.
  - `graph.json`: Color-codes graph nodes by OKF `type` (`prd`: green, `architecture`: blue, `learnings`: orange, `research`: purple, `backlog`: red).
  - `core-plugins.json`: Enables native backlinks, graph view, and page preview.
  - Project `.gitignore` automatically ignores `.obsidian/workspace*.json` and cache directories while tracking the shared configuration.

### 2.2 `index.md` per Folder as Maps of Content (MOCs)
Open Knowledge Format (OKF v0.2) already reserves `index.md` as a frontmatter-free progressive disclosure file:
```markdown
# Product Requirements Documents (PRDs)
* [BT-108: Host-Agnostic Skill Distribution](BT-108-host-agnostic-skill-distribution.md) - Universal skill delivery spec.
* [BT-142: Zero-Cost Lint Gate](BT-142-zero-cost-lint-gate.md) - Deterministic pre-commit gate.
```
In Obsidian, `index.md` seamlessly acts as a **Map of Content (MOC)**:
- **Graph Topology:** In Obsidian's force-directed graph view, `index.md` becomes the natural centroid hub, clustering subfolder documents cleanly.
- **Agent Token Efficiency:** An agent cold-starting on a subfolder reads `index.md` (~150 tokens) to identify the relevant file instead of globbing and reading 40 separate documents.
- **Backlink Reciprocity:** Opening any child document displays `index.md` in Obsidian's Backlinks pane.

### 2.3 Monolithic vs. Atomic Memory (Pragmatic Hybrid Model)
To avoid the dual pitfalls of "token-heavy monolithic files" (e.g., 2,000-line memory files dumped into agent context) and "file-read thrashing" (agents having to make 40 separate tool calls to read individual learning snippets):
1. **Atomic Concepts (High Context, Low Churn):**
   - `docs/prds/BT-xxx-<slug>.md`
   - `docs/plans/<slug>.md`
   - `docs/research/<slug>.md`
   - `docs/discovery/<slug>.md`
   - `docs/decisions/ADR-xxx-<slug>.md` (Architecture Decision Records)
2. **Consolidated References (High Density, Fast Ingestion):**
   - `.memory/ARCHITECTURE.md` (System laws, stack boundaries, vocabulary)
   - `.memory/GLOSSARY.md` (Ubiquitous language dictionary)
   - `.memory/DESIGN_RULES.md` (Structural UI invariants)
   - `.memory/BACKLOG_MAP.md` (Authoritative ledger for `tracker: local`)
3. **Episodic Learnings (`.memory/LEARNINGS.md`):**
   - Remains consolidated during early project stages.
   - Uses anchor tags (`[[LEARNINGS#^L-001|L-001]]` or standard `[[L-001]]` parsed by `validate_memory.py`) so both Obsidian and agent scripts resolve citations precisely.

### 2.4 Local Tracker Integration (`tracker: local`)
When `tracker: local` is active:
- `BACKLOG_MAP.md` remains the authoritative database table.
- Epic rows link to atomic PRD documents: `| BT-LOCAL-001 | Host-Agnostic Skill Distribution | ... | [[BT-LOCAL-001-skill-distribution]] |`.
- In Obsidian, opening the PRD note instantly displays all child slices from `BACKLOG_MAP.md` in the Backlinks panel, providing a visual dependency tree with zero custom code.

---

## 3. Implementation Plan & Scope of Changes

### Phase 1: Scaffolder & Setup Integration (`stratosphere-setup`)
- [ ] Add `--vault [none|obsidian]` flag and interactive prompt to `src/scripts/scaffold.py`.
- [ ] Bundle preconfigured `.obsidian/` template assets under `src/assets/templates/obsidian/`:
  - `app.json` (wikilinks enabled, shortest path).
  - `graph.json` (color groups for OKF types).
  - `core-plugins.json`.
- [ ] Update scaffold `.gitignore` template to ignore `.obsidian/workspace*.json`, `.obsidian/cache/`, and `.obsidian/graph-cache.json`.

### Phase 2: Memory & Link Validator Hardening (`validate_memory.py`)
- [ ] Update `validate_memory.py` link resolution engine:
  - Recognize bare filename wikilinks pointing into `docs/**` (e.g. `[[BT-108-host-agnostic-skill-distribution]]`).
  - Continue validating internal `[[L-xxx]]`, `[[A-xxx]]`, `[[DR-xxx]]`, and `[[G-xxx]]` anchors.
- [ ] Ensure non-destructive reconciliation during `/0b-stop-session` and `/0d-nightly-consolidation`.

### Phase 3: Visualizer Streamlining
- [ ] Retire or relegate `okf_view.py` and `okf_viewer/` to a legacy/fallback headless HTML generator.
- [ ] Document Obsidian workspace recommendations in `docs/okf-spec-essentials.md` and `AGENTS.md`.

---

## 4. Sources & Literature Review

### Academic Research & Theoretical Foundations
1. **Sahoo, P., et al. (2024).** *The Prompt Report: A Systematic Survey of Prompting Techniques.* arXiv:2406.06608.  
   - *Key Insight:* Prompt-heavy retrieval and runtime reasoning gymnastics suffer from severe token inflation (300%–500%) and context drift. Grounding agent memory in deterministic filesystem structures and AST-indexed references is significantly more reliable.
2. **Open Knowledge Format (OKF v0.2) Specification.** `docs/okf-spec-essentials.md` and `src/rules/okf-protocol.md`.  
   - *Key Invariant:* Directory `index.md` files as reserved progressive disclosure boundaries without frontmatter; non-reserved markdown files as typed concept documents.

### Community Implementations & Industry Precedents
3. **Karpathy, Andrej (2024–2025).** *The LLM Wiki / Context Vault Paradigm.*  
   - *Architecture:* Separation of raw reference materials from agent-maintained synthesized concept pages interconnected via bidirectional markdown links.
4. **Kepano (Obsidian CEO) / Obsidian Developer Community.** *Obsidian Flavored Markdown (OFM) & obsidian-skills.*  
   - Repository: `https://github.com/kepano/obsidian-skills`  
   - Specification of standard wikilink resolution rules, YAML frontmatter properties, and headless JSON Canvas schemas for AI agent interop.
5. **Claudian — Claude Code in Obsidian.**  
   - Repository: `https://github.com/Yizhe/claudian`  
   - Implementation demonstrating direct terminal agent integration against local Obsidian vaults, allowing Claude Code to inspect selections, update graph notes, and navigate backlinks.
6. **Model Context Protocol (MCP) Obsidian Integrations.**  
   - `mcp-obsidian` / `obsidian-rest-api` (via Obsidian Local REST API community plugin).  
   - Provides programmatic endpoints for LLM agents to execute semantic graph traversal and note creation over local vaults.
7. **Cursor Rules (`.cursor/rules/`) & Context Vault Best Practices.**  
   - Documentation: `https://docs.cursor.com/context/rules-for-ai`  
   - Demonstrates the industry shift toward co-locating markdown documentation vaults alongside source code, replacing proprietary editor database state.
