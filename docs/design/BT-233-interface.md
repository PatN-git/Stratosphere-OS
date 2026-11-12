---
type: interface-design
title: "Design: BT-233 - Obsidian-Compatible Docs Vault & Backlink Graph Architecture"
description: "Path C non-UI interface contract specifying vault configuration assets, dual-track link validation engine, and migration CLI tooling."
generated:
  by: 2b-interface-design
  at: "2026-11-12T11:26:00-05:00"
status: stable
slug: obsidian-document-linking
bt: BT-233
prd: docs/prds/BT-233-obsidian-document-linking.md
surface: non-ui
version: "5.3.0"
---

# Design: BT-233 - Obsidian-Compatible Docs Vault & Backlink Graph Architecture

## Surface & Scope
This interface design specifies the non-UI architecture, configuration schemas, CLI interfaces, and validation engines for integrating an optional, zero-daemon Obsidian knowledge vault into Stratosphere-OS repositories.

**Target Seams & Subsystems:**
1. **Scaffolding Subsystem (`src/scripts/scaffold.py`):** Adds `--vault [none|obsidian|okf-html]` CLI flag, interactive setup/update prompts, `.obsidian/` template placement (`tier="preserved"`), `.gitignore` configuration management, and dynamic `userIgnoreFilters` generation.
2. **Vault Asset Templates (`src/assets/templates/obsidian/`):** Preconfigured `.obsidian/` JSON assets (`app.json`, `graph.json`, `core-plugins.json`) enforcing shortest-path wikilinks, OKF type color mapping, and graph query filtering (`path:docs OR path:.memory`).
3. **Memory & Link Validation Engine (`src/scripts/validate_memory.py`):** Reconciles token extraction into dual resolution tracks: (a) location-agnostic conceptual memory handles (`[[L-xxx]]`, `[[A-xxx]]`, `[[G-xxx]]`, `[[DR-xxx]]`) checked for bidirectional reciprocity, and (b) document wikilinks (`[[<doc-stem>]]` or `[[<doc-stem>|<alias>]]`, with minimum path prefix on collision) resolved against git-tracked files in `docs/**` and `.memory/**` without reciprocity.
4. **Repository Modernization Utility (`scripts/migrations/migrate_obsidian_links.py`):** Deterministic migration CLI supporting `--dry-run` and `--write` modes to rewrite legacy Markdown links into canonical Obsidian wikilinks and regenerate directory `index.md` Maps of Content (MOCs).

## Actors & Core Flows

### 1. The Human System Architect / PKM Explorer
- **Flow:** Launches `stratosphere-setup` or `stratosphere-update`, selects `Obsidian Vault`, and opens the project root in Obsidian.
- **Experience:** Obsidian immediately loads with an interactive force-directed graph color-coded by OKF type (`prd`: green, `architecture`: blue, `learnings`: orange, `research`: purple, `design-doc`: teal, `proposal`: magenta), cleanly clustered around directory MOC hubs (`index.md`) without any background Python server running.

### 2. The Headless AI Agent (Google Antigravity, Claude Code, Cursor)
- **Flow:** Authors a new PRD, research brief, or design doc referencing existing concepts.
- **Experience:** The agent writes natural wikilinks `[[frontier-interview-and-wayfinder-analysis|Wayfinder Analysis]]` without computing brittle relative paths (`../../docs/research/...`). When validating via `python src/scripts/validate_memory.py`, the linter verifies target file existence deterministically in `<10ms` without false-positive memory errors.

### 3. The Repository Maintainer
- **Flow:** Modernizing an existing StratOS repository (`Stratosphere-OS` or `CleanTechHub`).
- **Experience:** Runs `python scripts/migrations/migrate_obsidian_links.py --dry-run` to preview all link conversions and MOC regenerations, verifies zero dangling links, and runs `--write` to apply the update in a single atomic commit.

## Aha Moment & Time-to-Value
- **Aha Moment:** Within 30 seconds of running `stratosphere-setup`, the developer launches Obsidian, opens the project folder, and immediately sees a live, beautiful, force-directed graph of their system's architecture, PRDs, and learnings clustered around MOCs—with zero manual configuration, zero local webservers, and instant Ctrl+Click backlink navigation.
- **Time-to-Value Goal:** Time to first successful interactive graph visualization is < 30 seconds.

## Direction Alternatives (Considered)
- **Winner: Direction 1 — Pragmatic Hybrid / Dual-Track Architecture (Selected):**
  - Repository root serves as vault root.
  - Scoping achieved via `graph.json` query filter (`path:docs OR path:.memory`) and dynamic `userIgnoreFilters` in `app.json` (including `archive/`).
  - Canonical wikilinks `[[<doc-stem>|<alias>]]` with minimum folder prefix on collision.
  - Location-agnostic conceptual memory handles `[[<ID>]]` indexed via AST search; synthetic block anchors (`^ID`) prohibited.
  - Zero red-flag hits; 5/5 score across Desirable, Usable, Feasible, Viable, Ethical lenses.
- **Alternative 1: Direction 2 — Strict Path-Qualified / Pure Explicit (Rejected):**
  - Mandated full relative paths in every wikilink (`[[docs/prds/BT-233-obsidian-document-linking]]`).
  - *Reason Rejected:* Hits the *Information Leakage* red flag. Clutters plain-text markdown, causes high agent relative-path computation errors, and breaks all inbound references across the repository whenever folders are renamed or reorganized.
- **Alternative 2: Direction 3 — Subfolder Dedicated Vault with Symlinks (Rejected):**
  - Scoped `.obsidian/` inside `docs/`, attempting to bridge `.memory/` via OS directory symlinks.
  - *Reason Rejected:* Hits *Split Ownership* and *Two Ways to Do One Task* red flags. Major cross-platform failure on Windows (NTFS symlinks require admin/developer mode; Git for Windows defaults to `core.symlinks=false`, turning symlinks into corrupted plain text files on clone).

## States / Edge Classes

### UX / System Stress Matrix

| Adverse Condition | Failure Mode | Required Handling / Defensive Invariant |
| :--- | :--- | :--- |
| **1. Active duplicate stems across sibling directories** (e.g. `docs/discovery/foo.md` vs `docs/research/foo.md`) | Non-deterministic resolution in Obsidian; validator cannot resolve target deterministically. | **Minimum Path Qualification Invariant:** `validate_memory.py` detects multiple matches in `docs/**`. In default mode, issues a warning with candidate paths and suggested minimum prefix (`[[discovery/foo]]`). Under `--warnings-as-errors`, halts code 1. `migrate_obsidian_links.py` automatically injects shortest disambiguating path prefix. |
| **2. Active stem colliding with archived document** (`docs/proposals/foo.md` vs `docs/archive/foo.md`) | Bare `[[foo]]` links to deprecated archive note; false ambiguity warnings. | **Vault Ignore Alignment Invariant:** `validate_memory.py` and `migrate_obsidian_links.py` strictly ignore paths matching archive patterns (`*/.archive/*`, `docs/archive/*`, `.tmp/*`), mirroring Obsidian's `userIgnoreFilters` in `app.json`. Bare `[[foo]]` resolves cleanly to the active note. |
| **3. Reserved stem collisions on `index.md` or `README.md`** | Hundreds of collision matches; Obsidian generates circular hub tangles. | **Reserved Stem Disambiguation Invariant:** Bare `[[index]]` and `[[README]]` without path prefix are explicitly rejected with an error. Authors and MOC generators must qualify directory hubs using parent folder prefix (e.g. `[[docs/prds/index\|PRDs MOC]]`). |
| **4. Document stem colliding with Memory Handle namespace** (e.g. `docs/prds/L-001.md`) | Regex conflates conceptual memory handle `[[L-001]]` with a file wikilink. | **Namespace Reservation Invariant:** Pattern `^(L\|A\|G\|DR)-\d{3,}$` is strictly reserved for `.memory/` handles. `validate_memory.py` emits a purity error if any file under `docs/**` uses a filename stem matching this pattern. |
| **5. Dangling document wikilink to missing or deleted file** (`[[missing-doc]]`) | Dead link in Obsidian; unverified references escape to production. | **Dual-Track Validation Invariant:** `validate_memory.py` splits token parsing: memory handles resolve against `.memory/` AST definitions; other `[[stem]]` tokens resolve against git-tracked files in `docs/**` and `.memory/**`. Missing targets emit `[ERROR] Dangling document link`, exiting code 1. |
| **6. Link pointing to untracked or gitignored file** (e.g. `.tmp/notes.md`) | Link works locally for author but breaks on teammates' clones and CI runners. | **Git-Tracked Index Invariant:** Target resolution in `validate_memory.py` evaluates strictly against `git ls-files` (`tracked_files()`). Untracked or ignored files emit `which git does not track`. |
| **7. Case-sensitivity mismatch between link and disk** (`[[bt-233]]` vs `BT-233.md`) | Works silently on Windows, fails on Linux CI runners (GitHub Actions). | **Canonical Git-Casing Invariant:** `validate_memory.py` and migration utility validate link casing against exact canonical casing in `git ls-files` on all operating systems. Case mismatch emits a hard error. |
| **8. Windows backslashes in path-qualified links** (`[[docs\prds\BT-233]]`) | Fails in Obsidian (POSIX URI routing); breaks cross-platform compatibility. | **POSIX Normalization Invariant:** Path resolution strictly enforces forward slashes `/`. Any link token containing `\` is flagged as an invalid link syntax error. |
| **9. CRLF line endings introduced during migration on Windows** | Running migration on Windows converts files to `\r\n`, creating massive phantom git diffs. | **Line-Ending Preservation Invariant:** `migrate_obsidian_links.py` reads in universal newline mode, detects file's original line delimiter (`\n` vs `\r\n`), and writes back using original terminator. |
| **10. Running migration on a dirty working tree** | In-place link rewriting overwrites uncommitted work; rollback is impossible. | **Clean Working Tree Pre-Flight Gate:** `migrate_obsidian_links.py` checks `git status --porcelain`. Uncommitted changes abort code 1: `Error: Working tree is dirty. Commit or stash changes before running --write`. |
| **11. Mixed link syntaxes in same file** (wikilinks + URLs + bare `BT-233`) | Regex greedily mangles URLs; bare issue IDs get accidentally bracketed. | **Syntactic Boundary Isolation Invariant:** External URLs (`https://...`) and asset links (`.png`) are ignored. Bare issue tokens (`BT-\d+`) outside double brackets remain untouched per [[A-005]]. |
| **12. Wikilinks embedded in code blocks or HTML comments** (` ```[[example]]``` `) | Validator emits false dangling reference errors on documentation examples. | **Code Block & Comment Masking Invariant:** Fenced code blocks (` ```...``` `), inline code backticks (`` `...` ``), and HTML comments (`<!-- ... -->`) are stripped prior to link extraction. |
| **13. Headless CI runner execution without TTY** (`stdin.isatty()` is False) | Interactive prompt hangs CI runner waiting for input; job timeouts. | **Headless Auto-Bypass Invariant:** All CLI scripts detect `sys.stdin.isatty()`. In non-interactive environments, prompts are bypassed; CLI arguments take precedence, defaulting safely to `none` or lockfile state. |
| **14. Running validation in CI without Obsidian runtime** | Process crashes looking for Obsidian binaries or GUI sockets. | **Zero External Runtime Invariant:** `validate_memory.py` is a 100% self-contained standard-library Python script with zero external dependencies on Obsidian. |

## Handoff Notes for 3d/4a
- **For 3d (Implementer):**
  - Implement CLI switch in `src/scripts/scaffold.py`: `--vault [none|obsidian|okf-html]`.
  - Bundle `.obsidian/` template assets under `src/assets/templates/obsidian/`: `app.json`, `graph.json`, `core-plugins.json`.
  - In `scaffold.py`, place `.obsidian/` files with `tier="preserved"` so user customizations are never overwritten on update.
  - Update `scaffold.py` to append `.obsidian/workspace*.json`, `.obsidian/cache/`, `.obsidian/graph-cache.json` to `.gitignore` idempotently.
  - In `src/scripts/validate_memory.py`:
    - Mask fenced code blocks, inline code, and HTML comments before extracting handles.
    - Bifurcate `[[token]]` matches into Memory Handles (matching `^(L|A|G|DR)-\d{3,}$`) vs Document Wikilinks (all other bracketed tokens).
    - Strip anchor (`#...`) and alias (`|...`) before testing document existence.
    - Check target existence against `tracked_files()`. Check exact case against git index.
    - If a stem matches multiple tracked files, issue warning or error with suggested prefix.
  - Create `scripts/migrations/migrate_obsidian_links.py` with `--dry-run` and `--write` flags, clean working tree pre-check, and atomic two-phase commit.
- **For 4a (Auditor/Verifier):**
  - Verify `python src/scripts/scaffold.py --vault obsidian` generates valid `.obsidian/` directory and `.gitignore` entries.
  - Verify `python src/scripts/validate_memory.py` passes cleanly on valid document wikilinks (`[[BT-233-obsidian-document-linking]]`) and fails on dangling links (`[[non-existent-doc]]`).
  - Verify case-sensitivity enforcement catches lowercase link to uppercase filename.
  - Verify `migrate_obsidian_links.py --dry-run` produces non-mutating preview and `--write` safely converts markdown links without CRLF churn.
  - Verify zero external runtime dependencies on Obsidian in test suites.

---

### [Path C · Non-UI] Interface Contract

#### 1. Caller Usage (written first)

```powershell
# 1. Project Scaffolding with Obsidian Vault Opt-in
python src/scripts/scaffold.py --vault obsidian

# 2. Automated Project Update preserving existing vault choice
python src/scripts/scaffold.py --update

# 3. Deterministic Memory & Document Link Validation
python src/scripts/validate_memory.py
# (Or under strict gate mode)
python src/scripts/validate_memory.py --warnings-as-errors

# 4. Dry-run Preview of Repository Link Migration
python scripts/migrations/migrate_obsidian_links.py --dry-run

# 5. In-place Atomic Execution of Repository Link Migration
python scripts/migrations/migrate_obsidian_links.py --write
```

```markdown
<!-- Document Authoring Syntax Example -->
## References & Lineage
- Inline in prose: "As analyzed in [[frontier-interview-and-wayfinder-analysis|Wayfinder Analysis]], we apply G1–G3."
- Bare stem in reference bullet:
  - [[BT-108-host-agnostic-skill-distribution]]
  - [[target-verification-and-subagent-scoping]]
- Minimum path prefix for collision disambiguation:
  - [[discovery/host-agnostic-skill-distribution|Discovery Brief]]
  - [[research/host-agnostic-skill-distribution|Research Exploration]]
- Memory handle cross-reference:
  - Governed by [[A-006]] and [[G-005]].
- External tracker provenance:
  - Issue: BT-233
```

#### 2. Interface / API Signatures

##### A. Scaffolding CLI Interface (`src/scripts/scaffold.py`)
```python
def parse_args() -> argparse.Namespace:
    """
    Extends argument parser with vault opt-in switch:
      --vault {none,obsidian,okf-html}
    Defaults to None (prompted interactively if stdin is a TTY, else 'none' / lockfile state).
    """

def scaffold_obsidian_vault(project_root: Path, res: dict, dry: bool, update: bool = False) -> None:
    """
    Places .obsidian/ configuration files from assets into project_root/.obsidian/ using tier='preserved'.
    Updates project_root/.gitignore idempotently with vault cache exclusions.
    Generates dynamic userIgnoreFilters in app.json based on top-level project folders.
    """

def get_dynamic_ignore_filters(project_root: Path) -> list[str]:
    """
    Scans project_root directories. Any top-level folder other than 'docs', '.memory',
    and '.obsidian' (e.g. 'src', 'tests', 'build', 'dist', 'node_modules', '.tmp', 'archive')
    is returned as an ignore glob pattern for Obsidian app.json.
    """
```

##### B. Vault Configuration Asset Schemas

**`.obsidian/app.json`:**
```json
{
  "useMarkdownLinks": false,
  "newLinkFormat": "shortest",
  "showLineNumber": true,
  "userIgnoreFilters": [
    "^\\.git/",
    "^\\.tmp/",
    "^node_modules/",
    "^dist/",
    "^build/",
    "^src/",
    "^tests/",
    "^docs/.*/\\.archive/",
    "^docs/archive/"
  ]
}
```

**`.obsidian/graph.json`:**
```json
{
  "search": "path:docs OR path:.memory",
  "colorGroups": [
    {"query": "file:.memory", "color": {"a": 1, "rgb": 15918608}},
    {"query": "path:docs/prds", "color": {"a": 1, "rgb": 4048700}},
    {"query": "path:docs/research", "color": {"a": 1, "rgb": 10565885}},
    {"query": "path:docs/design", "color": {"a": 1, "rgb": 3125673}},
    {"query": "path:docs/discovery", "color": {"a": 1, "rgb": 14757340}},
    {"query": "path:docs/proposals", "color": {"a": 1, "rgb": 14766520}},
    {"query": "file:index.md", "color": {"a": 1, "rgb": 16777215}}
  ]
}
```

**`.obsidian/core-plugins.json`:**
```json
[
  "file-explorer",
  "global-search",
  "switcher",
  "graph",
  "backlink",
  "page-preview",
  "outline"
]
```

##### C. Link Validation Engine (`src/scripts/validate_memory.py`)
```python
_MEMORY_HANDLE_RE = re.compile(r'^(L|A|G|DR)-\d{3,}$')
_WIKILINK_TOKEN_RE = re.compile(r'\[\[([^\]\n]+)\]\]')

def mask_code_and_comments(content: str) -> str:
    """Strips fenced code blocks, inline code spans, and HTML comments before link parsing."""

def parse_wikilink_token(raw_token: str) -> tuple[str, str | None, str | None]:
    """
    Parses 'stem#section|alias' into (stem, section, alias).
    Normalizes forward slashes and strips whitespace.
    """

def resolve_document_wikilink(stem_or_path: str, tracked_files: set[str], doc_stems_map: dict[str, list[str]]) -> tuple[str | None, str | None]:
    """
    Resolves a document wikilink against git-tracked files.
    Returns (resolved_rel_path, error_or_warning_message).
    - If path-qualified (contains '/'), directly checks tracked_files.
    - If bare stem, looks up doc_stems_map:
      - 0 matches -> returns (None, 'Dangling document link')
      - 1 match -> returns (resolved_path, None)
      - >1 matches -> returns (resolved_path, 'Stem collision: multiple matches, use prefix to disambiguate')
    """
```

##### D. Migration Tooling Interface (`scripts/migrations/migrate_obsidian_links.py`)
```python
def main(argv: list[str] | None = None) -> int:
    """
    CLI options:
      --dry-run: (Default) Preview all conversions and MOC regenerations without modifying files.
      --write: Apply in-place modifications to docs/** and .memory/**.
      --project <path>: Path to project root (defaults to CWD).
      --force: Bypass clean working tree pre-check.
    Exit codes:
      0: Success
      1: Validation/pre-check error or unresolvable link
    """

def rewrite_markdown_links(file_path: Path, content: str, tracked_stems: dict[str, list[str]]) -> tuple[str, int]:
    """
    Transforms [Label](path/to/stem.md) into [[stem|Label]] (or [[folder/stem|Label]] on collision).
    Preserves external URLs (http/https/mailto) and image links without alteration.
    Returns (updated_content, replacement_count).
    """

def rebuild_moc_index(dir_path: Path, files: list[Path]) -> str:
    """
    Constructs a frontmatter-free OKF v0.2 MOC listing for dir_path/index.md using shortest-path wikilinks:
    # <Dir Name>
    * [[<doc-stem>|<Title>]] - <Description>
    """
```

#### 3. Behavioral Invariants
1. **Plain Markdown Invariance:** Repositories must remain 100% readable, editable, and validatable without Obsidian desktop software installed.
2. **Opt-in Purity Invariance:** Running `scaffold.py` without `--vault obsidian` (or selecting None) must never create `.obsidian/` or modify `.gitignore`.
3. **Template Preservation Invariance:** `scaffold.py` places `.obsidian/` assets using `tier="preserved"`; existing user edits in `.obsidian/` are never overwritten during `--update`.
4. **POSIX Path Invariance:** All document wikilinks must use forward slashes `/`. Backslashes `\` are strictly rejected as invalid link syntax.
5. **Git-Tracked Authority Invariance:** Target existence for document wikilinks is evaluated strictly against `git ls-files` (`tracked_files()`). Untracked files, ignored files, and `.tmp/` files are rejected.
6. **Case-Sensitivity Invariance:** Link casing must match disk casing in `git ls-files` exactly, enforced uniformly across Windows, macOS, and Linux.
7. **Line-Ending Invariance:** In-place link migrations must preserve each target file's original line terminator (`LF` vs `CRLF`), preventing spurious git diffs on Windows.
8. **Clean Tree Invariance:** `migrate_obsidian_links.py --write` requires a clean working tree (`git status --porcelain` empty); dirty working trees halt with exit code 1.

#### 4. Input Edge-State Matrix

| Input State / Call | Preconditions | Postconditions / Expected Response | Exit Code |
| :--- | :--- | :--- | :--- |
| `scaffold.py --vault obsidian` | Clean or dirty repo root | Scaffolds `.obsidian/app.json`, `graph.json`, `core-plugins.json`; appends vault cache rules to `.gitignore`. | 0 |
| `scaffold.py --vault none` | Any repo root | Skips all `.obsidian/` placement; `.gitignore` untouched. | 0 |
| `scaffold.py --update` (existing `.obsidian/` present) | Existing vault config | Preserves existing `.obsidian/*.json` without overwrite; refreshes dynamic ignore rules if needed. | 0 |
| `scaffold.py` (Headless CI, no TTY, no flags) | `stdin.isatty() == False` | Automatically defaults to `none` (or lockfile state); never hangs waiting for input. | 0 |
| `validate_memory.py` on valid wikilink `[[BT-233-obsidian-document-linking]]` | File exists in `docs/prds/` | Resolves target; passes clean with 0 errors. | 0 |
| `validate_memory.py` on aliased wikilink `[[obsidian-document-linking\|Brief]]` | File exists in `docs/discovery/` | Strips `\|Brief`, resolves stem; passes clean. | 0 |
| `validate_memory.py` on heading anchor `[[ARCHITECTURE#Known Constraints]]` | `ARCHITECTURE.md` exists | Strips `#...`, resolves stem; passes clean. | 0 |
| `validate_memory.py` on dangling wikilink `[[missing-file]]` | File does not exist | Emits `[ERROR] Dangling document link: '[[missing-file]]'`; halts. | 1 |
| `validate_memory.py` on ambiguous stem `[[foo]]` (exists in discovery/ and research/) | Multiple matches in `docs/**` | Emits `[WARNING] Ambiguous stem 'foo' matches multiple files; qualify with folder prefix`. (If `--warnings-as-errors`, halts code 1). | 0 (or 1) |
| `validate_memory.py` on path-qualified link `[[discovery/foo\|Brief]]` | `docs/discovery/foo.md` exists | Resolves cleanly to specific target; no collision warning. | 0 |
| `validate_memory.py` on case-mismatched link `[[bt-233-obsidian]]` on Windows | Disk has `BT-233-obsidian.md` | Emits `[ERROR] Case mismatch against git index`; halts code 1. | 1 |
| `validate_memory.py` on backslash link `[[docs\prds\BT-233]]` | Any OS | Emits `[ERROR] Invalid backslash in wikilink; use POSIX forward slash /`; halts code 1. | 1 |
| `migrate_obsidian_links.py --dry-run` | Any working tree state | Scans all markdown files, logs proposed link replacements and MOCs; modifies 0 files. | 0 |
| `migrate_obsidian_links.py --write` (clean tree) | `git status --porcelain` empty | Atomically rewrites markdown links to wikilinks and regenerates directory `index.md` MOCs. | 0 |
| `migrate_obsidian_links.py --write` (dirty tree) | Uncommitted git changes | Aborts code 1: `Working tree is dirty. Commit or stash changes before running --write`. | 1 |

#### 5. Compatibility & Errors
- **Error Model:** Standardized JSON and human-readable text error diagnostics. The validator outputs standard CLI text diagnostics and ends with `# MACHINE {"clean": bool, "errors": [], "warnings": []}` for programmatic tooling consumption.
- **Backward Compatibility:** OKF v0.2 consumers treat wikilinks as unresolved plain text per OKF §7 toleration rules. Directory `index.md` MOCs remain 100% compliant with OKF progressive disclosure boundaries.

#### 6. Scrap Signals (for 3d)
This interface contract is wrong if:
1. Obsidian releases an upstream breaking change that prevents root-relative or shortest-path wikilinks from resolving across subfolders without custom plugins.
2. Obsidian graph view search queries (`path:docs OR path:.memory`) fail to filter out non-matching file nodes in standard Obsidian desktop releases.
3. The memory validator's regex or resolution engine introduces observable latency > 50ms across a 200-document repository.
*On a scrap signal hit: stop implementation, record findings in the 3d plan's `## Deviations`, and re-route to `/2c-reconcile-specs`.*
