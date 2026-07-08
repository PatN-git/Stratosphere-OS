#!/usr/bin/env python3
"""One-time marker migration tool for StratosphereOS.

Matches known old-template block text in a project's `.memory/` files
and wraps them in-place with `SOS:BLOCK` markers, then seeds the lockfile.
"""
import json
import re
import sys
import hashlib
from pathlib import Path

# We import _versioning from src/scripts or the installed plugin scripts directory
possible_paths = [
    Path(__file__).resolve().parent.parent.parent / "src" / "scripts",
    Path.cwd() / ".agents" / "plugins" / "stratosphere-os" / "scripts"
]
for p in possible_paths:
    if p.exists():
        sys.path.insert(0, str(p))
        break

try:
    import _versioning
except ImportError:
    _versioning = None

# Known blocks to match and inject.
# Dict of filename -> { block_id -> block_text }
OLD_BLOCKS = {
    "BACKLOG_MAP.md": {
        "backlog-rules": (
            "- **PRESERVATION RULE:** Do NOT delete or modify operational instructions under Rules (such as Label source of truth syncing rules) or the `Milestone` definition line under Label Registry during setup or backlog updates. They must remain permanently as operational guidance.\n"
            "- When writing the first entry, populate the Label Registry with all labels used in this GitHub project.\n"
            "- **BT-id padding & Atomic Minting:** The GitHub issue number must be zero-padded to 3 digits (e.g., #7 becomes BT-007). All references, links, and filenames must use this padded format. **CRITICAL:** Never predict or pre-allocate `BT-<n>` IDs offline by scanning existing entries and calculating `MAX(BT_ID) + 1`. Because GitHub shares sequence numbers across both Issues and Pull Requests, guessing numbers locally guarantees collisions. IDs must be atomically captured strictly upon executing `gh issue create`.\n"
            "- Update when GitHub issues are created, closed, or change status.\n"
            "- Include only ID, Title, Status, Labels, Milestone, Dependencies, ICE, Ref — nothing else.\n"
            "- Use the Label Registry; do not invent labels.\n"
            "- The `Ref` column links to learnings, architecture rules, design rules, or glossary terms (e.g., L-012, A-003, DR-020, G-005). Doc paths (PRD/design) live in the GitHub issue body, not in Ref.\n"
            "- **Label source of truth:** After installation (Checkpoint 6), the Label Registry here reflects the live GitHub label set.\n"
            "  - If a label appears in **GitHub but not the registry** → add it to the registry (with user confirmation).\n"
            "  - If a label appears in the **registry but not GitHub** → create it in GitHub before using it in any issue.\n"
            "  - Never use a label in the Backlog table that is not in both the registry and GitHub.\n"
            "- **Single Status Invariant:** An issue must always have exactly one `status:*` label. When transitioning an issue to a new status in GitHub or the Backlog table, always remove the prior `status:*` label first."
        ),
        "label-canonical": (
            "- **Primary Type (`type:<class>`)**: `type:bug`, `type:content`, `type:feature`, `type:improvement`, `type:maintenance`, `type:research`\n"
            "- **Execution Mode (`type:<mode>`)**: `type:HITL` (Human-in-Loop required), `type:AFK` (Autonomous execution)\n"
            "- **Priority (`priority:xxx`)**: `priority:high` (Must have), `priority:medium` (Important), `priority:low` (Nice to have)\n"
            "- **Size (`size:xxx`)**: `size:large` (Architectural: Multi-feature/major schema), `size:medium` (Vertical: Standard Data/Logic/UI slice), `size:small` (Surgical: Local/Single-file)\n"
            "- **Scope (`scope:xxx`)**: `scope:baseline` (MVP end-to-end), `scope:differentiator` (differentiator to win), `scope:deferred` (out of scope/temporal deferral)\n"
            "- **Status (`status:xxx`)**: `status:planned`, `status:needs_spec`, `status:in progress`, `status:blocked`, `status:done`\n"
            "- **Milestone**: `vX.Y.Z` (`vMAJOR.MINOR.SPRINT`, e.g. `v1.2.3` = release 1.2, sprint 3). `MAJOR.MINOR` = the product release, owned by `/3a_version-planning`; `SPRINT` (Z) owned by `/3c_sprint-planning`. `vX.Y.0` = release planned, not yet sprinted. No leading zeros. Mirrors the GitHub milestone. This is the project's product-release tracker — not a tool/library version."
        ),
        "backlog-header": (
            "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
            "|:---|:---|:---|:---|:---|:---|:---|:---|"
        )
    },
    "DESIGN_RULES.md": {
        "design-principles": (
            "- **[[DR-001]] [LAW]** Kill AI Slop: no generic purple gradients, no *unchosen* or *Inter* default font (Inter is seen as AI slop and often an inherited tool default), no nested-card div soup. If a component looks like an AI built it, rewrite until it looks like a Senior Design Engineer built it.\n"
            "- **[[DR-002]] [LAW]** Use OKLCH for all color tokens — in `DESIGN.md`, `tailwind.config`, and CSS variables. OKLCH is accepted end-to-end by the tooling (external generators ingest it; the `@google/design.md` linter coerces it); **no hex conversion is needed**. Hex appears only if a generator emits it.\n"
            "- **[[DR-003]] [LAW]** Use fluid typography and fluid spacing scales — no fixed pixel values for cross-viewport layout. px values in `DESIGN.md` are **desktop anchors**; `design-theme` emits `clamp(min, fluid, max)` (min = max·0.66 floored at 12px; viewports 360→1280px).\n"
            "- **[[DR-004]] [LAW]** shadcn/ui components are the default. Raw HTML elements only when shadcn does not cover the use case.\n"
            "- **[[DR-005]] [LAW]** Tailwind tokens preferred over arbitrary values (`bg-[#3b82f6]`, `space-y-[17px]`).\n"
            "- **[[DR-006]] [LAW]** Semantic HTML over `<div>` soup. Use `<nav>`, `<main>`, `<aside>`, `<article>`, etc."
        ),
        "design-reference-rules": (
            "- **[[DR-007]] [LAW]** Extract data and feature-level layout. Pull content, visual styles, and the feature/page-body layout from the external generator. For GLOBAL structure (chrome: nav/sidebar/footer/page shell), defer to §3 Immortal Components when one exists.\n"
            "- **[[DR-008]] [LAW]** Structural Shield applies ONLY where an Immortal Component governs the structure — then discard a conflicting generator export. On a net-new page or an explicit full redesign (no governing Immortal Component, or intentional replacement), ADOPT the generator's layout instead of discarding it.\n"
            "- **[[DR-009]] [LAW]** Token Snap: Token Snap = **script does mechanical conversion, human curates** which tokens to keep. Applies to **any external source (Stitch / Claude Design)**. On a greenfield first-run the direction reverses — the generator/references seed the initial tokens (see the DESIGN.md round-trip note above). When `DESIGN.md` is supplied to the generator, output already conforms, so snap is only a fallback for un-tokened values.\n"
            "- **[[DR-010]] [LAW]** When any external design generator (Stitch / Claude Design) suggests a structural change to a global component (Navbar, Sidebar, Footer), this is drift, not intent. Do not propagate.\n"
            "- **[[DR-011]] [LAW]** Feed the chosen generator a current `DESIGN.md` as input context whenever possible. Name the exact **Google Fonts** family so it renders as a hard constraint ([[DR-016]]).\n"
            "- **[[DR-014]] [LAW]** Adopt-and-Register: A first-time or full-redesign layout accepted from the chosen generator is registered/updated as a §3 Immortal Component ([LAW]-tier, propose to user at design time in 2b, or via 0b/setup; register on user confirmation). Thereafter it shields future feature work (DR-008/010).\n"
            "- **[[DR-015]] [LAW]** Freeze-and-Read-from-Repo: Generator output is ingested once at 2b time (MCP if connected, else export/paste) and frozen into the repo; no lifecycle step reads live generator. The MCP is an optional ingest accelerator, never a runtime dependency. Claude Design's two-way Claude Code sync is **frozen** (ingest → snap → reconcile into the one SSOT; never live).\n"
            "- **[[DR-016]] [LAW]** Typography source — Google Fonts. Author every `DESIGN.md` `fontFamily` from the Google Fonts catalog (renderable by generators as a hard constraint; self-hostable via `next/font/google` / `@fontsource`). Non-GF brand fonts: keep the real family in the SSOT and declare a Google Fonts **stand-in for mockups only**, applying the real font at implementation. Pair wide choice with restraint: one display/serif + one neutral/sans."
        )
    },
    "ARCHITECTURE.md": {
        "arch-guidance": (
            "Crystallized, durable map of how the system is organized. All entries are `[LAW]`-tier.\n\n"
            "> Trust tags, supersession, and cross-reference rules → `.agents/rules/memory-protocol.md`.\n"
            "> If a rule could be debated or overridden, it belongs in `LEARNINGS.md` instead.\n"
            "> **PRESERVATION RULE:** Do NOT delete placeholder sections (`## Major Feature Areas`, `## State / Data Flow`, `## Backend / Database Boundaries`) or the format example line under `## Superseded` if there are no immediate entries during setup or updates. Keep them as placeholders until needed."
        ),
        "arch-vocabulary": (
            "- **Module:** A self-contained code unit (file, folder, component).\n"
            "- **Interface:** The contract surface exposed by a module.\n"
            "- **Depth (Deep/Shallow):** A deep module has a simple interface that hides significant complexity. A shallow module exposes all its internal details, increasing overall system complexity. We aim for deep modules.\n"
            "- **Seam:** An interface boundary separating two parts of the system, allowing them to be developed, tested, or mocked independently.\n"
            "- **Adapter:** A layer that maps between distinct domain interfaces, preserving the boundaries of each.\n"
            "- **Leverage:** Maximizing reuse of clean primitives to reduce codebase surface area.\n"
            "- **Locality:** Ensuring related data and operations stay close together to maximize readability and reasoning.\n"
            "- **Deletion Test:** A metric to test coupling: would deleting or replacing this module concentrate complexity elsewhere, or just move it? If it concentrates complexity, the module is not fully decoupled."
        )
    },
    "LEARNINGS.md": {
        "learnings-guidance": (
            "Episodic memory for project-specific lessons likely to matter again. Each entry carries a unique `L-xxx` ID, a trust tag, and (where applicable) a `Source: BT-xxx` cross-reference.\n\n"
            "> Trust tags, supersession, and cross-reference rules → `.agents/rules/memory-protocol.md`.\n"
            "> **PRESERVATION RULE:** Do NOT delete the format example line under `## Superseded` during setup or when adding entries. Keep it as a placeholder until real superseded entries exist.\n\n"
            "## What belongs here\n"
            "- API constraints discovered the hard way\n"
            "- Auth / RLS gotchas\n"
            "- Setup pitfalls\n"
            "- Recurring edge cases\n"
            "- Framework-specific traps\n\n"
            "## What does NOT belong here\n"
            "- Temporary TODOs → `BACKLOG_MAP.md`\n"
            "- Current task status → `STATUS.md`\n"
            "- One-off debugging logs unless they reveal a reusable rule\n"
            "- `[LAW]`-tier rules → `ARCHITECTURE.md` or `DESIGN_RULES.md`\n"
            "- Domain vocabulary → `GLOSSARY.md`"
        )
    },
    "GLOSSARY.md": {
        "glossary-guidance": (
            "Shared domain vocabulary. Terms used across discovery briefs, PRDs, sub-issues, and code. Each entry carries a `G-xxx` ID and trust tag.\n\n"
            "> Trust tags, supersession, and cross-reference rules → `.agents/rules/memory-protocol.md`.\n"
            "> GLOSSARY follows the same protocol as `LEARNINGS.md` — not exempt from trust tags.\n"
            "> **PRESERVATION RULE:** Do NOT delete the protocol instruction line above, the `Avoid:` formatting instructions, or the format example line under `## Superseded` during setup or entry seeding. Keep them permanently as operational guidance and placeholders.\n\n"
            "## What belongs here\n"
            "- Names of user segments and roles\n"
            "- Business-state vocabulary\n"
            "- Domain-specific terms with project-specific or non-obvious meanings\n"
            "- Categorization terms used across features and PRDs\n\n"
            "## What does NOT belong here\n"
            "- Code identifiers, function names, file paths, or domain/structural relationships between concepts → `ARCHITECTURE.md` (Depends-on / data-flow). The GLOSSARY is vocabulary only.\n"
            "- Brand tokens → `DESIGN.md`\n"
            "- One-off terms not expected to recur across docs\n"
            "- Technical/framework terms with standard industry meanings"
        )
    },
    "DATABASE_SCHEMA.md": {
        "dbschema-rules": (
            "- **PRESERVATION RULE:** Do NOT delete the format example line under `## Superseded` when populating schema tables. Keep it as a formatting placeholder until real superseded entries exist.\n"
            "- Check this file before proposing schema changes, writing migrations, or changing queries.\n"
            "- If code and this file disagree, verify the real schema first. Note conflicts as `[LAW]` learnings.\n"
            "- Update when schema changes are finalized."
        )
    }
}

def normalize_text(text):
    if text.startswith("\ufeff"):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n")

def main():
    if not _versioning:
        print("Error: _versioning module not available.")
        sys.exit(1)
        
    project = Path.cwd()
    lock_file = project / ".agents" / ".stratosphere-lock.json"
    if not lock_file.exists():
        print(f"Error: Lockfile not found at {lock_file}.")
        sys.exit(1)
        
    try:
        lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading lockfile: {e}")
        sys.exit(1)
        
    migrated_count = 0
    
    for filename, blocks in OLD_BLOCKS.items():
        p = project / ".memory" / filename
        if not p.exists():
            continue
            
        text = p.read_text(encoding="utf-8")
        if "SOS:BLOCK" in text:
            # Idempotency guard: skip already-marked files
            print(f"Skipping {filename} — already contains SOS:BLOCK markers.")
            continue
            
        norm_text = normalize_text(text)
        
        # We will wrap each block
        # To avoid problems with BOM and CRLF, we match normalized versions
        updated_norm_text = norm_text
        success = True
        
        # Lock entry for the file
        proj_path = f".memory/{filename}"
        lock_entry = lock_data.get("artifacts", {}).get(proj_path)
        if not lock_entry:
            print(f"Warning: lockfile entry for {proj_path} is missing. Setting version=unknown.")
            lock_entry = {"version": "unknown", "sha256_at_install": "unknown"}
            lock_data.setdefault("artifacts", {})[proj_path] = lock_entry
            
        locked_v = lock_entry.get("version", "unknown")
        
        for bid, btext in blocks.items():
            norm_btext = normalize_text(btext)
            
            # Find count of matches
            matches = list(re.finditer(re.escape(norm_btext), updated_norm_text))
            if len(matches) == 0:
                print(f"Error: Block '{bid}' not found in {filename}. User may have customized it.")
                success = False
                break
            elif len(matches) > 1:
                print(f"Error: Multiple matches ({len(matches)}) found for block '{bid}' in {filename}.")
                success = False
                break
                
            # Exact match found, inject markers
            start_marker = f"<!-- SOS:BLOCK id={bid} v={locked_v} -->\n"
            end_marker = f"\n<!-- SOS:/BLOCK id={bid} -->"
            
            # Replace the single match
            updated_norm_text = updated_norm_text.replace(norm_btext, start_marker + norm_btext + end_marker)
            
        if success:
            has_bom = text.startswith("\ufeff")
            # Detect dominant newline of the original file
            crlf_count = text.count("\r\n")
            lf_count = text.count("\n") - crlf_count
            is_crlf = crlf_count > lf_count
            
            if is_crlf:
                final_text = updated_norm_text.replace("\n", "\r\n")
            else:
                final_text = updated_norm_text
                
            if has_bom:
                final_text = "\ufeff" + final_text
                
            # Write back
            p.write_text(final_text, encoding="utf-8")
            print(f"Successfully injected markers in {filename}")
            
            # Seed baseline hash in lockfile blocks map
            # Lock entry should have version and sha256_at_install updated
            lock_entry["version"] = locked_v
            lock_entry["sha256_at_install"] = _versioning.body_hash(final_text)
            
            # Seed blocks map
            blocks_map = lock_entry.setdefault("blocks", {})
            for bid in blocks.keys():
                blocks_map[bid] = _versioning.block_hash(final_text, bid)
                
            migrated_count += 1
            
    if migrated_count > 0:
        lock_file.write_text(json.dumps(lock_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Migration completed. Updated {migrated_count} lockfile entries.")
    else:
        print("No files migrated.")

if __name__ == "__main__":
    main()
