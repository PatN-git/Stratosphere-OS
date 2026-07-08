---
type: proposal
title: Optimize the StratosphereOS Update Flow
description: Deterministic-first, agent-fallback update pipeline for preserved memory files, a dedicated /stratosphere-update command, and cross-host rule-loading parity. Self-contained implementation plan.
status: draft
timestamp: 2026-07-08
version: "2.0.0"
---

# Proposal: Optimize the StratosphereOS Update Flow

> **This document is self-contained.** It assumes no prior conversation. An engineer or agent
> opening this repo cold should be able to execute it end-to-end using only this file plus the
> source files it names. Read §0 first — it establishes the vocabulary and repo model everything
> else depends on.

---

## 0. Orientation for an executing agent (READ FIRST)

### 0.1 What StratosphereOS (StratOS) is
StratOS is an agentic-orchestration framework distributed as a **plugin** for two host IDEs —
**Claude Code** and **Google Antigravity**. When a user installs the plugin and runs the
`/stratosphere-setup` command in a target project, StratOS scaffolds a durable "memory layer"
(`.memory/`), a constitution (`AGENT.md`/`CLAUDE.md`/`GEMINI.md`), workspace rules
(`.agents/rules/`), and lifecycle workflows (`.agents/workflows/`) into that project. This proposal
fixes how an **already-scaffolded** project pulls in **later** versions of those framework files.

### 0.2 Repo & build model (critical — get this right)
- **`src/` is the single source of truth.** Never edit `dist/` by hand.
- **`python build/build.py`** compiles `src/` into two plugin distributions:
  - `dist/claude-code/` — invocable files live in `commands/`.
  - `dist/antigravity/` — invocable files live in `workflows/`.
- **`versions.json` is GENERATED** by `build.py` (see `build/build.py` step 7). It walks every
  `.md` in each dist, reads the `version:` from YAML frontmatter, and records
  `{version, sha256 (body_hash), timestamp}`. **You never hand-edit `versions.json`.** To "register"
  a file's version you add/na bump its frontmatter `version:` and re-run the build. Every `.md` in the
  plugin MUST have a frontmatter `version:` or the build raises.
- **`build/validate.py`** is a bump-guard: if a file's content hash changed vs the committed
  baseline but its `version:` was not bumped, the build/CI fails. So: **any content edit to a
  versioned file requires bumping that file's `version:`.**

### 0.3 Key source paths (all relative to repo root)
| What | Source path | Ships to |
|:---|:---|:---|
| Deterministic scaffolder | `src/scripts/scaffold.py` | `dist/*/scripts/scaffold.py` |
| Version/hash helpers | `src/scripts/_versioning.py` | `dist/*/scripts/_versioning.py` |
| Memory templates (8 files) | `src/memory-templates/*.md` | `dist/*/assets/templates/memory/*.md` |
| Constitution | `src/constitution/{AGENT,CLAUDE,GEMINI}.md` | `dist/*/assets/templates/constitution/*.md` |
| Workspace rules | `src/rules/*.md` | `dist/*/assets/templates/rules/*.md` |
| Lifecycle workflows (0a–4b) | `src/workflows/*.md` | Claude: `dist/claude-code/commands/`; Antigravity: `dist/antigravity/workflows/` |
| Installer command | `src/commands/instantiate/Instantiate-StratosphereOS.md` | Claude: `commands/stratosphere-setup.md`; Antigravity: `skills/stratosphere-setup/SKILL.md` |
| Memory lint | `src/scripts/validate_memory.py` | `dist/*/scripts/` |
| Install tests | `tests/install-harness/` | — |

### 0.4 How scaffolding & updating work TODAY (the mechanism you are changing)
`scaffold.py` is run from a project root and copies bundled templates into the project. Its core
routine `place(src, dst, ..., tier)` (around `src/scripts/scaffold.py` lines 71–101) has **three tiers**:

- **`preserved`** — `.memory/*.md`. **If the destination exists, it is skipped outright**
  (`res["exists"]`, returns immediately). Never overwritten, even with `--update`. (`.gitignore` and
  `.gitattributes` are also never overwritten, but via separate create-if-missing logic near lines
  287–307, not the `place()` tier system — don't route them through the new preserved-delta mode.)
- **`managed`** — `.agents/rules/`, `.agents/workflows/`, `.agents/workflows/.reference/`,
  `.agents/scripts/`. With `--update`, overwritten in place when bytes differ.
- **`constitution`** — `AGENT.md`/`CLAUDE.md`/`GEMINI.md`. If bytes differ, flagged `NEEDS-REVIEW`;
  never auto-overwritten.

`scaffold.py` also maintains a **lockfile** `.agents/.stratosphere-lock.json` via
`generate_lockfile()` (lines ~142–207). Shape:
```json
{
  "installed_plugin_version": "1.0.0",
  "artifacts": {
    ".memory/BACKLOG_MAP.md": {
      "version": "1.1.3",
      "sha256_at_install": "<whole-file body_hash hex>",
      "blocks": {                         // ADDED by this proposal (§1 Lever 2)
        "backlog-rules":   "<sha256 of normalized inter-marker content>",
        "label-canonical": "<...>",
        "backlog-header":  "<...>"
      }
    }
  }
}
```
The lockfile records the framework version a project file was installed at. **This proposal adds the
`blocks` map** (per-block content hashes) — the interface the update flow's pristine detection depends
on (§1 Lever 2). Note the **path mapping**:
`versions.json` keys are bundle-relative (`assets/templates/memory/BACKLOG_MAP.md`); lockfile keys are
project-relative (`.memory/BACKLOG_MAP.md`). `scaffold.py`'s `map_bundled_to_project()` converts
between them.

The **update path today** lives inside the setup command
`src/commands/instantiate/Instantiate-StratosphereOS.md` (search for "Update & Drift check", ~lines
98–109). It runs `scaffold.py --update --dry-run`, then compares bundled `versions.json` against the
lockfile to detect updates/drift, and asks the user before applying.

`src/scripts/_versioning.py` provides:
- `normalize(text)` — strips a UTF-8 BOM and converts CRLF/CR → LF.
- `split_frontmatter(text)` → `(frontmatter, body)`.
- `read_version(text, path)` → the frontmatter `version:` and `timestamp:`.
- `body_hash(text)` — SHA-256 **after stripping `version` and `timestamp` from frontmatter**, so a
  version bump alone never changes the hash.

### 0.5 The three problems this proposal fixes
1. **`.memory/` files never receive framework updates.** Because they are `preserved`, `scaffold.py`
   skips them forever. Framework content that lives *inside* them (operational rules, registries,
   design doctrine) is frozen at install-time.
2. **The re-prompt loop.** `generate_lockfile(repair=False)` only *adds* missing lockfile entries; it
   never rewrites existing ones (the `if proj_path not in lock_data...` guard). So a preserved file's
   locked `version` stays at install-time. The setup command then sees `bundled 1.1.3 > locked 1.1.1`
   and offers the update **every run**. `--repair-lock` doesn't help: it re-reads the version from the
   file's *own* frontmatter, which — since the file was never touched — still says `1.1.1`.
3. **Framework rules and living data are entangled in one file.** e.g. `.memory/BACKLOG_MAP.md` holds
   template-owned `## Rules` + canonical label registry **and** the user's `## Backlog` rows +
   reconciled `area:` labels. Any update must edit the framework part without disturbing user data.

### 0.6 Vocabulary used throughout
- **Marker / block** — an HTML-comment sentinel pair wrapping framework-owned content inside a
  `.memory` file (defined in §3, Lever 1). Content **outside** a block is project data, never touched.
- **Pristine block** — the user's block content equals the previously-shipped template's block
  content (user never customized it) → safe to replace deterministically.
- **Conflict block** — the user edited inside the block → needs an agent to merge.
- **Baseline advance** — after updating a file, writing its new `version:` into both the file's
  frontmatter and its lockfile entry. This is what stops the re-prompt loop.

### 0.7 Environment notes
- Host OS is Windows; the primary shell is PowerShell. `python` invokes Python 3.
- The repo may live on Google Drive / OneDrive (slow FS; `build.py` already tolerates locks).
- Work happens in `src/`; after `src/` edits, run `python build/build.py` and commit both `src/` and
  the regenerated `dist/`.

---

## 1. Decision

Adopt an **optimized agentic-merge update flow**: deterministic in the common case, with an agent
used **only** for genuine conflicts, and a hard invariant that makes user-data loss structurally
impossible. Two alternatives were considered and rejected:

- **Relocate framework rules out of `.memory/` into `.agents/`** — rejected: a cross-cutting refactor
  of ~6 of 8 templates plus every workflow that cites them, and it force-loads the relocated rules
  into every Antigravity session (`.agents/rules/` is Antigravity's always-resident folder).
- **A markdown-heading-aware scaffolder** — rejected: a heading matcher breaks on any heading rename,
  and heading-level granularity is insufficient because some sections (e.g. the Label Registry) mix
  framework dimensions with project-reconciled data *within one section*.

The chosen design rests on three levers.

### Lever 1 — Sentinel markers around framework blocks
Wrap template-owned content in rename-proof HTML-comment anchors:
```markdown
<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->
... framework operational rules ...
<!-- SOS:/BLOCK id=backlog-rules -->
```
- `id` is a stable identifier for the block (unique within the file).
- `v` records the template version the block content corresponds to.
- Everything **outside** a block is project data and is **never** in edit scope.

**Comparison rule (do not skip):** the START marker's `v=` stamp differs between template versions
(`v=1.1.2` vs `v=1.1.3`), so comparing the *whole block* byte-for-byte would flag **every** block as
changed. Pristine detection MUST compare only the **inter-marker content** — the lines strictly
between the START and END markers, marker lines themselves **excluded**.

> **EXACT hashing input (must be pinned — a validation run proved ambiguity here manufactures false
> conflicts on pristine blocks).** Define inter-marker content as: take the lines strictly between the
> START and END marker lines, `normalize()` them (strip a leading UTF-8 BOM; CRLF/CR → LF), then join
> with `\n` **with no leading or trailing newline**; hash the UTF-8 bytes of that string with SHA-256.
> This *identical* function MUST be used in all three places — seeding at install, reading `H_base`,
> and recomputing on baseline-advance — or a block that ends in a newline before its END marker will
> hash differently at read vs seed and be misclassified as a conflict. Ship this as a single helper in
> `_versioning.py` (e.g. `block_hash(text, block_id)`); never re-implement it inline. Include a worked
> example hash in the docstring so drift is caught.

### Lever 2 — hash-based 3-way, using per-block baseline hashes in the lockfile
**Critical constraint:** `scaffold.py` runs from the installed plugin **inside the target project**
(e.g. CleanTechHub). That project has **no copy of, and no git history for, the old template** — the
plugin ships only the *current* template. And the existing lockfile stores only a **whole-file** hash
(`sha256_at_install` over the entire normalized file), which changes whenever any backlog row changes,
so it cannot tell whether one *block* was customized. Therefore pristine-vs-conflict **cannot** be
decided by diffing against an old template.

**Fix — store a per-block baseline hash in the lockfile.** Extend each lockfile artifact with a
`blocks` map of `{ block-id → sha256(normalized inter-marker content) }`, written at install and
re-written at every baseline-advance (§2.2 Phase 3). This makes the classification a pure hash
comparison with three inputs, all locally available: the user's current block hash `H_user`, the
lockfile baseline hash `H_base`, and the bundled new-template block hash `H_new` (computed from the
shipped template).

**Check `H_user == H_new` FIRST (dominating pre-check).** Before the four rows below, if the user's
block already equals the new-template block, the block is **already at target** — do nothing to its
content (still advance the baseline in Phase 3). This case has no row in a `{==,≠}H_base × {==,≠}H_base`
table because it only shows up as `H_user vs H_new`, and a gate run proved that without this pre-check a
crash-recovered or double-committed block (where `H_user == H_new ≠ H_base`) is misclassified as a
*conflict* and sent through a needless merge that can corrupt an already-correct block. It also cleanly
handles "user and template independently made the identical edit."

Then the four `H_base`-relative rows:

| `H_user` vs `H_base` | `H_new` vs `H_base` | Meaning | Action |
|:---|:---|:---|:---|
| equal | differs | **pristine + template changed** | deterministic swap: replace user's whole block (markers included, `v=` advances); zero LLM |
| equal | equal | pristine, no template change | nothing to do for this block |
| differs | equal | user customized, template unchanged | leave user's block untouched (nothing to port) |
| differs | differs (and `H_user ≠ H_new`) | **conflict** | agent edits **only that block** via an anchored `Edit` on the marker span (never a full-file `Write`), porting the framework delta while preserving the user's edit; present a diff for confirmation |

No old-template text is ever needed. The already-at-target pre-check plus the pristine (top row) case
cover the dominant, fully deterministic paths.

### Lever 3 — Invariant guardrail (cheap seatbelt)
An adversarial validation run showed that an invariant listing *specific* protected fields (BT-id set,
row count, `area:` set, DR-id set) is **insufficient**: a conflict-merge agent that also rewrote a
data row's *other* fields (status, ICE, title) — or a §3 entry's body — would pass every named check
while silently corrupting user data. The invariant must therefore be **structural, not field-by-field**:

1. **Out-of-block byte-identity (the core seatbelt).** Everything *outside* the changed blocks MUST be
   **byte-identical, compared RAW** (do **not** `normalize()` the comparison — a gate run showed that
   normalizing both sides lets the writer silently convert the user's untouched project data from
   CRLF→LF and strip its BOM while the check still passes; that is real data mutation the invariant is
   named to prevent). Preserve the file's original EOL/BOM on write; reserve `normalize()` for
   block-hash computation only. **Two explicit exemptions** (framework-managed, not project data): the
   frontmatter `version:` field, and the `v=` attribute on the marker lines of *changed* blocks — both
   are advanced by Phase 3 and must be excluded from this check, or every run would abort on its own
   version bump. Everything else outside changed blocks (backlog rows, the `area:` line,
   `Design Source`/`Design References`, §3 Immortal Components, unchanged blocks incl. their markers) is
   protected verbatim — including intra-row field edits the old per-field list missed.
2. **Marker integrity.** For every known block id: exactly one well-formed START/END pair, correctly
   ordered, no duplicates, no orphan/missing END — checked before AND after. **Also reject any SOS
   marker with an *unknown* id** (a gate run noted a bad merge could introduce a stray/typo marker that
   passes a known-ids-only check and collides with a future id). (A dropped END marker on one run would
   otherwise make the *next* run's parser swallow following blocks and delete data.)
3. **Cheap corroborating checks** (fast, human-readable failures): the `BT-xxx` id set and
   `## Backlog` row count for `BACKLOG_MAP.md`; the §3 `[[DR-xxx]]` id set for `DESIGN_RULES.md`.

On any mismatch: abort and report; write nothing (see the atomic-commit rule in §2.2). This makes
drop-a-row / hallucinate-a-row / corrupt-a-field impossible-by-construction rather than
trusted-not-to-happen.

---

## 2. Detailed design

### 2.1 Marker placement (which files, which blocks)

**Principle: uniform mechanism; exclusions only for structural reasons, never for "low churn."** The
update pipeline (§2.2) applies to *all* preserved files, and baseline-advance (Phase 3) runs for every
one so the re-prompt dies everywhere. Markers go in every memory file that has a **separable**
framework block **and** where markers are **safe**. Marking is a one-time authoring cost with no
runtime downside; per-file exceptions are what create inconsistency.

Applying that test to all eight templates in `src/memory-templates/` → **six marked, two excluded**:

| File | Framework block(s) to wrap | Marked? |
|:---|:---|:---:|
| `BACKLOG_MAP.md` | `## Rules`; canonical Label-Registry dimensions; `## Backlog` header row | ✅ |
| `DESIGN_RULES.md` | §1 Principles (`DR-001`–`006`); §2 Reference Rules (`DR-007`–`016`) | ✅ |
| `ARCHITECTURE.md` | `## Purpose`+PRESERVATION; Architectural Vocabulary; belongs/not-belongs | ✅ |
| `LEARNINGS.md` | `## Purpose`+PRESERVATION; belongs/not-belongs | ✅ |
| `GLOSSARY.md` | `## Purpose`+PRESERVATION; belongs/not-belongs | ✅ |
| `DATABASE_SCHEMA.md` | `## Rules` block | ✅ |
| `STATUS.md` | — none: framework labels are interleaved per-line with user values (`- **Last Sync:** <value>`); no standalone block to wrap | ❌ structural |
| `DESIGN.md` | follows the external `@google/design.md` spec, is already HTML-comment-heavy, and a stray/leading HTML comment can silently empty that linter's parse | ❌ safety |

The two **unmarked** files still get baseline-advance so they stop re-prompting: on a version bump
they are treated like the constitution tier — flagged `NEEDS-REVIEW`, diff surfaced, applied only on
user confirmation, then the baseline advanced.

**Authoring instruction (per marked file):** open the source template under
`src/memory-templates/`, wrap the block(s) named above with `<!-- SOS:BLOCK id=<id> v=<current
version> -->` … `<!-- SOS:/BLOCK id=<id> -->`, then bump the file's frontmatter `version:` (required by
the bump-guard). Use these block ids: `backlog-rules`, `label-canonical`, `backlog-header`,
`design-principles`, `design-reference-rules`, `arch-vocabulary`, `arch-guidance`,
`learnings-guidance`, `glossary-guidance`, `dbschema-rules`.

**Worked example — `BACKLOG_MAP.md` (note the required `area:` reorder).** The current
`## Label Registry` lists `area:` first, then the canonical dimensions. Since `area:` is
**project-reconciled data** (it must never revert to template defaults) and the canonical dimensions
are framework, reorder so `area:` sits *outside* the block:

_Before (current `src/memory-templates/BACKLOG_MAP.md`, abbreviated):_
```markdown
## Rules
- **PRESERVATION RULE:** ...
- **BT-id padding & Atomic Minting:** ...
- **Single Status Invariant:** ...

## Label Registry
- **Area (`area:xxx`)**: area:FE-<page_name>, area:BE-<domain> ...
- **Primary Type**: type:bug, type:feature, ...
- **Priority**: priority:high, ...
- **Size**: size:large, ...
- **Status**: status:planned, ...

## Backlog
| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |
|:---|:---|:---|:---|:---|:---|:---|:---|
| BT-XXX | Example ... |
```
_After (markers added, `area:` moved out of the block):_
```markdown
## Rules
<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->
- **PRESERVATION RULE:** ...
- **BT-id padding & Atomic Minting:** ...
- **Single Status Invariant:** ...
<!-- SOS:/BLOCK id=backlog-rules -->

## Label Registry
- **Area (`area:xxx`)**: area:FE-<page_name>, area:BE-<domain> ...   <!-- project data: OUTSIDE block -->
<!-- SOS:BLOCK id=label-canonical v=1.1.4 -->
- **Primary Type (`type:<class>`)**: type:bug, type:content, type:feature, type:improvement, type:maintenance, type:research
- **Execution Mode (`type:<mode>`)**: type:HITL, type:AFK
- **Priority (`priority:xxx`)**: priority:high, priority:medium, priority:low
- **Size (`size:xxx`)**: size:large, size:medium, size:small
- **Scope (`scope:xxx`)**: scope:baseline, scope:differentiator, scope:deferred
- **Status (`status:xxx`)**: status:planned, status:needs_spec, status:in progress, status:blocked, status:done
- **Milestone**: vX.Y.Z semantics ... (load-bearing definition line — framework, keep per PRESERVATION RULE)
<!-- SOS:/BLOCK id=label-canonical -->

## Backlog
<!-- SOS:BLOCK id=backlog-header v=1.1.4 -->
| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |
|:---|:---|:---|:---|:---|:---|:---|:---|
<!-- SOS:/BLOCK id=backlog-header -->
| BT-XXX | Example ... |   <!-- data rows: OUTSIDE block -->
```
The real `## Label Registry` has **8** bullets (above): only `area:` is project data (outside the
block); the other seven — Primary Type, Execution Mode, Priority, Size, Scope, Status, and the
Milestone definition line — are framework and go **inside** `label-canonical`. Copy the exact current
text from `src/memory-templates/BACKLOG_MAP.md` rather than this abbreviation.

**`DESIGN_RULES.md`:** wrap §1 (`DR-001`–`DR-006`) as `design-principles`, and the §2 rule bullets
(`DR-007`–`DR-016`, which excludes `DR-012`/`DR-013` — those numbers appear only in a §3 note about
purging examples) as `design-reference-rules`.
> **Data-loss warning (do NOT wrap these):** §2 opens with `**Design Source:**` and
> `**Design References (native projects):**`, and includes the `Applicability:` / `DESIGN.md
> round-trip:` paragraphs named by the file's PRESERVATION RULE. `Design Source`/`Design References`
> are **user data written during setup** (Instantiate Checkpoint 8). They sit *inside* §2 above
> DR-007. Keep them — and those paragraphs — **outside** the `design-reference-rules` block, exactly
> like the `area:` line in BACKLOG_MAP. Wrap only the DR-007…DR-016 bullet prose.

`DR-xxx` IDs do **not** move; workflows that cite `[[DR-xxx]]` keep working. (The earlier blanket claim
"only the prose inside the blocks is template-owned" is **wrong** for §2 — hence this warning.)

**`ARCHITECTURE.md`, `LEARNINGS.md`, `GLOSSARY.md`, `DATABASE_SCHEMA.md`:** wrap only the top-of-file
framework guidance (Purpose, PRESERVATION RULE, "what belongs / does NOT belong", and — ARCHITECTURE —
the Architectural Vocabulary). Everything from the first data section onward (`## Active Entries`,
`## Tables`, `## Tech Stack`, real `[[A-xxx]]`/`[[L-xxx]]`/`[[G-xxx]]` entries) stays outside.

### 2.2 Phase design (the update flow)

**Compute-then-commit ordering (atomicity — required).** A validation run showed that writing in
Phases 1/3 and only verifying in Phase 4 both violates "verify before write" and creates a cross-run
hazard: if the flow replaces a block then crashes before advancing the baseline, the next run recomputes
`H_user == H_new != H_base` and misclassifies the (correct) file as a **conflict**, forcing a needless
merge. Therefore Phases 1–3 compute the **proposed** new bytes for every file + the proposed lockfile
**in memory**; Phase 4 verifies the proposed bytes; only then does the flow commit.

**Commit is not a single atomic OS operation** — a gate run correctly flagged that "rename all files
AND the lockfile" is N+1 separate `os.replace` calls, and a crash between them leaves some files new
and the lockfile old (exactly the crash-recovery state). Two rules make this safe rather than
"impossible":
- **Order: write all memory files first, the lockfile LAST**, as the single logical commit point. The
  lockfile is what Phase 0 reads to decide scope, so until it lands the run is simply "not yet
  committed."
- **Recovery is guaranteed by the `H_user == H_new` pre-check (Lever 2):** if a crash lands files but
  not the lockfile, the next run sees each already-written block as already-at-target → no content
  change, just advances the baseline → converges silently and idempotently. (This is why that
  pre-check is a correctness requirement, not an optimization.) Optionally, a commit-intent journal
  under `.tmp/` can detect and finish a torn commit, but the pre-check alone makes the torn state
  self-healing.

| Phase | Layer | Action |
|:---|:---|:---|
| **0. Compute scope** | deterministic | Run `scaffold.py --update --dry-run`. Produce the worklist: `managed` files that are `STALE`, `constitution` files `NEEDS-REVIEW`, and preserved files where bundled `version` > locked `version` (see §2.3 for the path-key mapping used in this comparison). |
| **1. Classify + stage** | deterministic | For each marked block in an in-scope preserved file, classify with the §1 Lever 2 hash table (`H_user`/`H_base`/`H_new`, using the pinned `block_hash` helper). Stage pristine+changed blocks for a deterministic swap **in memory**. Also stage normal `managed`-tier refreshes (workflows/rules/scripts). |
| **2. Merge residue** | agentic (conflicts only) | For each conflicted block, stage a merge **within that block only** (see §2.3a on how the agent gets a base to merge against); present a per-file diff for confirmation. Constitution **and** unmarked preserved files (`STATUS.md`, `DESIGN.md`) that bumped are surfaced as `NEEDS-REVIEW` diffs, per-file, applied only on confirmation. |
| **3. Stage baseline advance** | deterministic | For **every** in-scope preserved file — **unconditionally, even when zero blocks changed** — stage: frontmatter `version:` → bundled version; lockfile entry `version` + each block's recomputed hash in `blocks` + recomputed `sha256_at_install`. *This unconditional advance (not "advance only after a block is updated") is the actual fix for the re-prompt loop — a validation run confirmed a naive implementation that gates the advance on a block edit leaves unchanged-but-bumped files stale forever.* Unmarked files advance only after their Phase-2 confirmation. |
| **4. Verify, then commit** | deterministic | Run the Lever-3 invariants (out-of-block byte-identity + marker integrity) + `validate_memory.py` on the **proposed** bytes. On any failure, abort and write nothing. On success, commit all staged files + the lockfile atomically. |

### 2.3 `scaffold.py` changes (`src/scripts/scaffold.py`)
   **This proposal moves the version comparison for preserved files INTO `scaffold.py`.** Today the
   comparison (`versions.json` vs lockfile) lives in the setup command; that command-layer comparison
   is **deleted** and re-homed here so there is exactly one owner. Concretely:
1. **Install-time per-block hashing (create path).** When `scaffold.py` first writes a marked template
   into a project, it parses the blocks and records each block's `sha256(normalized inter-marker
   content)` into the lockfile artifact's new `blocks` map (§0.4). This establishes the baseline that
   pristine detection needs.
2. **Preserved-file delta mode** (behind `--update`). For each preserved file where bundled `version` >
   locked `version`, parse it for `SOS:BLOCK`/`SOS:/BLOCK` pairs and classify **each block** by the
   hash table in §1 Lever 2 using `H_user` (recompute from the file), `H_base` (from the lockfile
   `blocks` map), and `H_new` (from the bundled template). Pristine+changed ⇒ deterministic swap;
   conflict ⇒ record for the agent; otherwise no-op. A preserved file with **no** markers keeps today's
   behavior (skip / `LEFT AS-IS`) **plus** the §2.4 guard notice if it is also stale. Parser must
   tolerate: multiple blocks per file; a missing/unterminated END marker (→ malformed: skip file +
   report, never partial-write); duplicate/nested ids (→ malformed). **Write-back newlines:** detect
   the file's existing dominant newline (CRLF vs LF) and write swapped blocks with the **same** ending
   so the change does not produce a whole-file line-ending churn in git; hashing/comparison always uses
   `normalize()` so this never affects classification.
3. **Baseline advance** (Phase 3, **unconditional**). For every in-scope preserved file — *even when
   zero blocks changed* — rewrite its frontmatter `version:` to the bundled version, recompute and store
   each block's hash into the lockfile `blocks` map, and recompute `sha256_at_install`. Do **not** gate
   this on "a block was updated" (that leaves unchanged-but-bumped files stale → re-prompt forever).
   Extend `--repair-lock` accordingly.
4. **Path-key mapping (required for Phase 0).** The version comparison joins `versions.json` (keys like
   `assets/templates/memory/BACKLOG_MAP.md`) to the lockfile (keys like `.memory/BACKLOG_MAP.md`). Reuse
   `scaffold.py`'s existing `map_bundled_to_project()` for the join; do **not** basename-match (two files
   sharing a basename would collide). Fail loudly on an unmappable key.
5. **Shared hash helper.** Implement the pinned `block_hash(text, block_id)` (Lever 1 EXACT rule) once
   in `_versioning.py` and call it everywhere (install seed, `H_base` read, advance). This is the
   single most bug-prone spot — a validation run manufactured false conflicts from a trailing-newline
   discrepancy between seed and read.
6. **Machine-readable worklist.** `--update --dry-run` writes a structured summary (stdout + a JSON
   file under `.tmp/`) of `{file, block, state, old_v, new_v}` so the command layer drives Phase 2
   without re-deriving state.
7. **Invariant hook** (Phase 4). Add a `--verify` mode (or fold into `--update`) that runs the Lever-3
   invariants: **out-of-block byte-identity** (all content outside changed blocks unchanged) + **marker
   integrity** (one ordered START/END pair per id, before and after) + the cheap corroborating id/row
   checks.
8. **Commit order + recovery.** Compute all proposed bytes in memory, verify, then temp-write + rename
   the **memory files first and the lockfile last** (single logical commit point). Because the commit is
   N+1 renames (not jointly atomic), rely on the Lever-2 `H_user == H_new` pre-check to make a torn
   "files-new/lock-old" state self-heal on the next run; optionally journal pending renames under `.tmp/`.
9. **Edge cases the gate surfaced — specify all three:**
   - **Version compare is semver**, not string (`1.1.10 > 1.1.9`).
   - **`sha256_at_install`** is over the **raw committed bytes** of the final file (EOL/BOM included), recomputed on every advance; document it so it doesn't drift per-platform.
   - **Absent lockfile entry** (a bundled artifact with a file on disk but *no* lockfile artifact at all — distinct from "entry present but no `blocks` map"): treat locked-version = none → in scope → route to the inconsistent-lock handler (§2.4), not a crash.

Keep all additions **zero-LLM** (except the Phase-2 conflict merge) and **idempotent**; `--dry-run`
must stay a pure preview. Re-running the whole flow after a successful run must be a no-op (all blocks
classify as unchanged, versions already advanced).

### 2.3a Conflict-block merge: what base the agent gets
The Lever-2 `conflict` case (user edited a block *and* the template changed it) needs a merge, but the
lockfile stores only a *hash* of the base — not its text — and the target project has no old template.
Two supported paths, in preference order:
1. **Preferred — invariant-guarded LLM merge (no base text needed).** The agent is shown the user's
   current block and the new-template block, and produces a merge. Determinism is *not* required for
   safety, because the Lever-3 out-of-block byte-identity invariant guarantees the merge cannot touch
   any project data (it all lives outside blocks), and the in-block result is presented as a diff for
   **explicit user confirmation** before commit. This is acceptable precisely because framework blocks
   are small (a handful of rule bullets).
2. **Optional hardening — store base block text.** If a true 3-way `merge3(base, user, new)` is wanted,
   extend the lockfile `blocks` values from a bare hash to `{hash, text}` (blocks are small). Deferred
   unless conflict merges prove unreliable in practice.

### 2.4 One-time marker migration (out-of-band, disposable — NOT in the steady-state flow)
Existing projects scaffolded **before** this change have `.memory/` files with **no** markers.
Injecting markers is a **one-time transition**; keep it out of `scaffold.py` / `/stratosphere-update`
so the permanent flow carries no dead migration code. (Every project scaffolded from this change
onward ships markers natively.)

- **Delivery — a maintainer script, not a shipped command:** `scripts/migrations/inject_markers.py`
  in the repo root, **not** copied into `dist/` (add it under `scripts/` at repo root, which `build.py`
  does not bundle — confirm it is outside `src/`). Not a lifecycle command; no `versions.json` entry.
- **Behavior:** for each marked template, locate the framework block in a target project's `.memory/`
  file by matching the known old-template block text (retrieved from git history of
  `src/memory-templates/` at the project's locked version — reachable because this is a maintainer
  script run from inside the StratOS repo, not the target-project scaffolder) and wrap it in
  `SOS:BLOCK` markers in place. **Guards a validation run flagged as missing:** (a) require **exactly
  one** match per block — 0 matches ⇒ report for manual wrap (user customized it); ≥2 matches or one
  block's content being a substring of another ⇒ abort that block and report (no `find()`-first-hit
  guessing); (b) **idempotency** — if the file already contains any `SOS:BLOCK` markers, skip it (never
  double-wrap). Exact single match ⇒ inject silently. **After wrapping, seed the lockfile `blocks` map**
  (§0.4, via the shared `block_hash` helper) with each block's baseline hash so the first subsequent
  `/stratosphere-update` has `H_base`. Preserve original bytes on write (don't re-encode em-dashes /
  newlines in the untouched project regions).
- Run manually **once** per pre-marker project (i.e. CleanTechHub); verify; commit; then it is
  irrelevant and may be archived/deleted.
- **Steady-state guard:** `/stratosphere-update` assumes markers exist. **The authoritative
  "unmarked" signal is scanning the file for `SOS:BLOCK` markers — NOT "lockfile has no `blocks` map"**
  (a validation run showed a fresh install or a partial prior write can leave a *marked* file whose
  lockfile lacks the map). If the file genuinely has no markers, emit one notice that **names the
  migration command** — e.g. *"Unmarked framework file `<path>` — run
  `python scripts/migrations/inject_markers.py` to enable in-place updates."* — and skip the file.
- **Inconsistent lock (markers present, `blocks` map missing/incomplete) — do NOT blindly re-seed
  `H_base := H_user`.** A gate run proved that re-seeding forces every block to look pristine, so a
  *customized* block is then classified pristine+changed and **silently overwritten** — the exact
  data-loss the design must prevent. Instead, for each block classify against **`H_new` directly**:
  `H_user == H_new` → already-at-target (no change); `H_user ≠ H_new` → treat as a **conflict** (agent
  merge + user-confirmed diff), never a blind replace. Only seed a block's `H_base` from `H_user` once
  it is confirmed at-target or the user has confirmed the merge. If `sha256_at_install` is present and
  matches the current whole-file bytes, the file is provably untouched since install and the blocks may
  be re-seeded as pristine safely.
- **Stop the nag:** skipping an unmarked file does not advance its baseline, so it stays in scope and
  would re-notify every run. To avoid training users to ignore output, record an
  `acknowledged_unmarked` marker (a per-file flag in the lockfile) so the notice degrades to a single
  end-of-run summary line ("1 file needs marker migration") on subsequent runs until resolved.

### 2.5 `/stratosphere-update` — the new sibling command
**Why a new command (not just docs):** today the only update path is "re-run `/stratosphere-setup`",
which is undocumented and misleading (the name reads first-run-only), and setup carries heavy audit
checkpoints (DB introspection, architecture mapping, design audit, label reconciliation, skill
selection) that an update must not re-run.

**Author it like the installer.** Study `build/build.py` step 3 (`inst = SRC/"commands"/"instantiate"/…`).
The installer is special-cased: shipped to Claude as `commands/stratosphere-setup.md` and to
Antigravity as `skills/stratosphere-setup/SKILL.md`. Mirror that for update:
1. Create `src/commands/update/Stratosphere-Update.md` with frontmatter
   `name: stratosphere-update`, `type: workflow`, `description:`, `version:`, **and `timestamp:`**.
   All four of `{name, description, version, timestamp}` are **required** — `build/validate.py` fails
   the build otherwise (it enforces that set on both commands/workflows and skills).
2. In `build/build.py`, add a step mirroring step 3: for Claude write
   `dist/claude-code/commands/stratosphere-update.md`; for Antigravity write
   `dist/antigravity/skills/stratosphere-update/SKILL.md`. (This gives it parity with setup and makes
   it available on Antigravity immediately after a plugin upgrade, before any re-scaffold.)
3. **Content:** the command orchestrates Phases 0–4 of §2.2 plus constitution `NEEDS-REVIEW` handling —
   and **nothing else** (no setup Checkpoints). Move the "Update & Drift check" block out of
   `src/commands/instantiate/Instantiate-StratosphereOS.md` into this command so the logic lives in
   exactly one place; setup's re-run path delegates to it (see the guard below).
4. `versions.json` entry appears automatically once the file has a `version:` and you re-run the build.

**Setup detection guard (existing-install handoff).** Add to
`src/commands/instantiate/Instantiate-StratosphereOS.md`: before any scaffold/file creation, detect an
existing install and hand off — do not silently re-scaffold.
- **Detection:** already-instantiated if `.agents/.stratosphere-lock.json` exists (primary), or, as a
  fallback for pre-lockfile installs, if both `AGENT.md` and a populated `.memory/` exist.
- **On detection: stop and flag.** Message e.g. *"This project already has StratosphereOS installed
  (lockfile plugin v&lt;X&gt;, N tracked artifacts). Setup bootstraps a new project; to upgrade, run
  `/stratosphere-update`."*
- **Require explicit confirmation** via the host tool (`AskUserQuestion` on Claude Code /
  `ask_question` on Antigravity), three options:
  1. **Run `/stratosphere-update` instead** (recommended).
  2. **Continue setup anyway** — only the create-only-if-missing scaffold; never overwrites preserved
     data or the constitution.
  3. **Cancel.**
- Default/recommended is (1). Setup never runs the update flow itself, never overwrites, and never
  proceeds past this guard without an answer.
- **Also reword the command's self-description in the same edit.** `Instantiate-StratosphereOS.md`
  currently says "Run once per project; safe to re-run" (frontmatter description, ~line 4) and
  "one-time setup (safe to re-run for upgrades)" (~line 13). Those now contradict the hard-stop guard —
  change them to describe first-run bootstrap with a pointer to `/stratosphere-update` for upgrades.
  Bump the command's `version:` (bump-guard).

### 2.6 Cross-host rule-loading parity (optional, orthogonal)
`.agents/rules/` is Antigravity's always-resident folder; Claude Code does **not** auto-load it and
instead relies on the constitution pointer model (`AGENT.md` §8, "Pointer Directory") to read rules on
demand. If you want the genuinely every-session invariants guaranteed-resident on Claude Code too, the
lever is the **`CLAUDE.md` template** (`src/constitution/CLAUDE.md`), not the scaffolder:
```markdown
@.agents/rules/output-mode.md
@.agents/rules/memory-protocol.md
```
- Claude Code inlines `@path` imports into every session. Keep imports **only in `CLAUDE.md`** (it is
  already Claude-only) so they never leak into `GEMINI.md`/`AGENT.md` (host-agnostic design).
- Be **selective** — only invariant, every-session rules; importing occasional/domain rules
  reintroduces the always-read cost.
- No scaffold change; this is a constitution-tier edit. Ship it as its **own PR** — it is independent
  of the update flow. (Bump `src/constitution/CLAUDE.md` `version:`.)

---

## 3. README changes (`README.md`)
1. Add an **Updating** subsection under "Getting Started (Installation)" documenting
   `/stratosphere-update`, with the guarantee: *"Your `.memory/` data and constitution are never
   overwritten; framework blocks are updated in place, and you confirm any conflict."*
2. Add a **Maintenance** row to the Lifecycle Commands Matrix for `/stratosphere-update`.
3. Reword the "Instantiate Project Memory" step so `/stratosphere-setup` reads as first-run bootstrap,
   pointing to `/stratosphere-update` for upgrades.

---

## 4. Testing

Two layers: a **design-validation gate using subagents** run *before* implementation (§4.2), and
automated tests once code exists (§4.1).

### 4.1 Automated harness (post-implementation) — extend `tests/install-harness/`
- **Fresh install** unaffected (regression).
- **Pristine update:** old-template `.memory/` file + bumped bundle ⇒ block swapped; frontmatter +
  lockfile advanced; a second `--update --dry-run` reports **no** pending update (proves the re-prompt
  fix).
- **Conflict update:** user-edited block ⇒ agent-merge path; invariant holds; data rows untouched.
- **Unchanged-but-bumped:** version bumped, block content identical ⇒ no content change, baseline
  still advances.
- **Migration (separate from the flow):** `inject_markers.py` on a marker-less fixture ⇒ markers
  injected; a subsequent update behaves as pristine. Also: update on a marker-less file *without*
  migrating emits the guard notice and skips.
- **Invariant trip — whole row:** drop a `BT-xxx` row mid-merge ⇒ Phase 4 aborts, no write.
- **Invariant trip — intra-row field (from the gate):** a conflict merge that also flips `BT-007`'s
  `status`/`ICE` while ID set + row count stay constant ⇒ the out-of-block byte-identity invariant
  aborts. (The old per-field invariant missed this.)
- **CRLF+BOM pristine (from the gate):** a pristine block in a CRLF+BOM file classifies as pristine (not
  conflict); confirms `normalize()` is applied in `block_hash`.
- **Atomicity / crash recovery (from the gate):** simulate a crash after staging but before commit ⇒
  no file mutated; a rerun still classifies pristine (not a spurious conflict).
- **Marker integrity (from the gate):** a file with a dropped END marker ⇒ aborts with an integrity
  error, never swallows the next block.
- **Path-key mapping:** a versions.json/lockfile pair is joined via `map_bundled_to_project()`, not
  basename; an unmappable key fails loudly.
- **Setup detection guard:** setup on an already-instantiated project ⇒ detects lockfile, flags,
  blocks on confirmation; recommended choice routes to update; no files change until answered.
- **Malformed markers:** missing END / duplicate id ⇒ file skipped + reported, never partial-written.
- **Migration guards (from the gate):** ≥2 matches for a block ⇒ reported not auto-wrapped; re-running
  `inject_markers.py` on an already-marked file is a no-op (idempotent).
- Run against both `dist/claude-code` and `dist/antigravity`.

### 4.2 Subagent mock-environment validation (pre-implementation gate)

**Purpose.** Before writing code, have independent subagents *execute the update algorithm by hand*
against a controlled mock repo (a tabletop simulation). It answers: "is the spec unambiguous and safe
enough to implement and then run against a live project?" Its currency is **spec gaps and data-loss
paths**, not pass/fail. Learnings feed back into this document (§4.3) before any implementation and
before the maintainer's manual test on CleanTechHub.

**Step A — build the mock env** in a throwaway scratch dir (never the real repo). Structure:
```
mock-stratos/
  ALGORITHM.md          # the self-contained spec below
  template_old/         # marked templates at the "locked" version (e.g. BACKLOG_MAP v1.1.3)
  template_new/         # bundled version (e.g. v1.1.4) with exactly ONE block's content changed
  versions_new.json     # { "plugin_version":"1.0.0", "artifacts": { "assets/templates/memory/BACKLOG_MAP.md": {"version":"1.1.4", ...} } }
  scenario_pristine/    # .memory/BACKLOG_MAP.md (block untouched) + lock with blocks{} hash == user's block hash
  scenario_conflict/    # user edited a rule bullet inside the block (so user block hash != lock baseline hash)
  scenario_unchanged/   # bundle bumped but template block content equals baseline (H_new == H_base)
  scenario_legacy/      # .memory file with NO markers
  scenario_migration/   # legacy file, target for inject_markers
```
Every scenario lockfile MUST include the new `blocks` map (§0.4) with baseline per-block hashes —
that is the interface pristine detection reads. Author `H_base` = `sha256(normalize(inter-marker
content of template_old's block))`; the pristine fixture's user block equals that content; the conflict
fixture's does not.
Each `.memory` fixture MUST contain realistic **project data to preserve verbatim**: ≥3 `BT-xxx`
rows, a reconciled `area:` set (e.g. `area:FE-dashboard`), and (for a DESIGN_RULES fixture) ≥1
`[[DR-xxx]]` Immortal Component. Author **one** fixture with **CRLF line endings + a UTF-8 BOM** to
exercise `normalize()`.

**Step B — write `ALGORITHM.md`** (paste this verbatim into the mock env so agents are self-contained):
> You are simulating `/stratosphere-update` by hand. Execute the phases literally, produce the
> resulting files, and report every ambiguity. Markers: `<!-- SOS:BLOCK id=X v=N -->` … `<!-- SOS:/BLOCK id=X -->`;
> content outside a block is project data and must NEVER change.
> **Phase 0:** if bundled `version` (versions_new.json) > locked `version` (lockfile), the file is in
> scope. **Phase 1 (per block, hash-based):** compute `H_user = sha256(normalize(user's inter-marker
> content))` (exclude marker lines; BOM/CRLF→LF). Read `H_base` from the lockfile `blocks` map and
> compute `H_new` from `template_new`'s block. Then: `H_user==H_base && H_new!=H_base` ⇒ **pristine** →
> replace the user's whole block (markers included) with `template_new`'s block; `H_user!=H_base &&
> H_new!=H_base` ⇒ **conflict** → Phase 2; otherwise no-op. If the file has NO markers ⇒ do NOT inject;
> emit the guard notice and skip. **Phase 2:** for each conflict, edit ONLY within that block to port
> the framework change while preserving the user's edit; show a diff. **Phase 3:** set the file's
> frontmatter `version` to bundled, and rewrite the lockfile entry incl. each block's new hash in
> `blocks`.
> **Phase 4:** the set of `BT-xxx` IDs and `## Backlog` data-row count MUST be identical before/after;
> if not, ABORT and report data loss.
> **Report:** (1) final file(s); (2) final lockfile; (3) per-phase notes; (4) ambiguities/spec gaps
> (specific); (5) invariant result (BT-id set + row count before/after); (6) data-loss risks.

**Step C — dispatch subagents in parallel.** Spawn six `general-purpose` subagents; give each
`ALGORITHM.md`, `template_old/`, `template_new/`, and its scenario dir. Roles:

| Agent | Scenario | Must demonstrate |
|:---|:---|:---|
| A | pristine | block swapped; `area:` + `BT` rows byte-identical; frontmatter + lockfile advanced; re-run shows no pending update |
| B | conflict | only the conflicted block edited; user customization preserved; diff shown; invariant holds |
| C | unchanged | no content change despite bump; baseline still advances |
| D | legacy | refuses to inject; emits guard notice; changes nothing |
| E | migration | inject_markers logic wraps the correct span; exact-match injects, mismatch reports |
| F (adversary) | all | actively hunt data-loss/reversion: can any step drop a `BT` row, revert `area:` labels, mis-place a marker, or mis-detect pristine due to the `v=` stamp or BOM/CRLF? |

**Step D — pass gate (all must hold before implementation):**
- A–E produce correct output with the invariant intact.
- F reports no *unmitigated* data-loss path.
- Every ambiguity is either resolved by an edit to this document or explicitly deferred with rationale
  (logged in §4.3).

**Step E — feedback loop.** Collect reports → extract distinct learnings → apply each as a concrete
edit to this document or the task list → log in §4.3. Re-run §4.2 if any change is structural. Only
once the gate is green does implementation begin; the maintainer's manual CleanTechHub test is the
final step of §5.

### 4.3 Validation findings log
Rows 1–11 are from static review (design drafting + an independent challenger). **Rows 12–20 are from
the executed §4.2 subagent gate** (6 agents: 5 scenarios + 1 adversary), which surfaced four
blocker-class defects that static review missed.

| # | Finding | Change applied | Status |
|:--|:--|:--|:--|
| 1 | Whole-block equality fails because the `v=` marker stamp differs across versions | Lever 1 comparison rule + §2.2 Phase 1 compare inter-marker content only | applied |
| 2 | Pristine detection unimplementable: scaffold runs in the target project, which has no old template; lockfile stores only a whole-file hash | Lever 2 rewritten to hash-based 3-way; added per-block `blocks` hash map to the lockfile (§0.4, §2.3, §2.4) | applied |
| 3 | Wrapping DESIGN_RULES §2 would revert user-set `Design Source`/`Design References` | §2.1 keeps those + Applicability/round-trip paragraphs outside the block; corrected the false "only prose is template-owned" claim | applied |
| 4 | Lever-3 invariant ignored the reconciled `area:` set — the highest-risk data | §1 Lever 3 + §2.3(5) now assert the `area:*` set (and DESIGN_RULES Design Source/References) unchanged | applied |
| 5 | Version-comparison ownership (scaffold vs command) undefined | §2.3 states the comparison moves into scaffold; the command-layer comparison is deleted | applied |
| 6 | Worked example didn't match the real 8-bullet Label Registry (missing Execution Mode; merged Scope/Milestone) | §2.1 example rewritten to the real 8 bullets with framework/data split | applied |
| 7 | Update command frontmatter missing `timestamp:` → build fails validate.py | §2.5 step 1 requires all four frontmatter keys | applied |
| 8 | `DR-007–016` implies DR-012/013 are reference rules; they aren't | §2.1 notes the exclusion | applied |
| 9 | `.gitignore` mis-described as a `place()`/preserved-tier file | §0.4 corrected (separate create-if-missing logic) | applied |
| 10 | In-place swap write-back line endings unspecified (Windows CRLF churn) | §2.3(2) specifies preserving the file's dominant newline | applied |
| 11 | Setup command still self-describes as "safe to re-run," contradicting the new guard | §2.5 reword instruction added | applied |
| 12 | **BLOCKER** — hashing input undefined (trailing-newline): seed vs read disagreed, manufacturing false conflicts on pristine blocks (agents A/B/C/E) | Lever 1 EXACT hashing rule pinned; single shared `block_hash` helper mandated (§2.3(5)) | applied |
| 13 | **BLOCKER** — Phase-4 invariant blind to intra-row/field & §3-body mutation; a conflict merge could corrupt `BT-007` status/ICE and pass (adversary) | Lever 3 rewritten to **out-of-block byte-identity** (protects all project data) + marker integrity | applied |
| 14 | **BLOCKER** — writes land before verify; a mid-run crash converts a pristine file into a false conflict on rerun (adversary) | §2.2 compute-in-memory → verify proposed bytes → **atomic commit** (§2.3(8)) | applied |
| 15 | **BLOCKER** — Phase 3 not stated as unconditional; a naive impl gating advance on "a block changed" leaves unchanged-but-bumped files re-prompting forever (agents C/D/F) | §2.2 Phase 3 + §2.3(3) made explicitly unconditional | applied |
| 16 | Marker integrity unchecked: a dropped END marker on one run makes the next run swallow/delete following blocks (adversary) | Added marker-integrity invariant (Lever 3 #2, §2.3(7)) | applied |
| 17 | "No `blocks` map" is necessary-but-not-sufficient for "legacy"; fresh install / partial write can leave a marked file without the map (agent D) | §2.4 makes **file marker-scan authoritative**; markers-but-no-map → "inconsistent lock state" diagnostic | applied |
| 18 | Legacy skip re-prompts forever and never names the migration command (agents D/F) | §2.4 names the command in the notice + `acknowledged_unmarked` flag degrades it to a summary line | applied |
| 19 | Migration `find()` has no match-uniqueness / tie-break / idempotency guard → could mis-wrap and orphan data (agents E/F) | §2.4 requires exactly-one-match, aborts on ≥2/substring, skips already-marked files | applied |
| 20 | Path-key mismatch (versions.json asset paths vs lockfile project paths) never joined; basename-match is unsafe (agents A/F) | §2.3(4) mandates `map_bundled_to_project()`, fail-loud on unmappable | applied |
| 21 | Minor: `sha256_at_install` recompute on advance, and marker `v=` left stale on unchanged blocks, were unspecified | §2.3(3) recomputes `sha256_at_install`; `v=` documented as informational (hashes are authoritative), unchanged blocks not re-stamped | applied |

**Round-1 gate verdict:** all 6 agents preserved project data in their scenarios; the adversary's two
"expected" attacks (`area:` revert, `Design Source` revert) were **defended** by the marker/scoping
model, but it found the four blockers above elsewhere. All folded in.

**Round 2 (re-run against the revised spec — 6 agents incl. 2 new probes: inconsistent-lock,
crash-recovery).** Confirmed rows 12/15/16 fixed (pinned hash removed all classification ambiguity;
unconditional Phase 3 kills the re-prompt; marker-integrity + CRLF/BOM in-block classification work).
Found 3 new blockers + 2 majors (rows 22–28), two of them self-inflicted by the round-1 fixes:

| # | Finding | Change applied | Status |
|:--|:--|:--|:--|
| 22 | **BLOCKER** — Phase 3 mutates the out-of-block frontmatter `version:` line, so the new out-of-block invariant aborts **every** run (found by 5 of 6 agents) | Lever 3 #1 exempts frontmatter `version:` + changed-block `v=` | applied |
| 23 | **BLOCKER** — no classification row for `H_user == H_new`; a crash-recovered/already-at-target block is misclassified as conflict → needless merge that can corrupt correct content | Lever 2 adds a dominating `H_user == H_new` "already-at-target" pre-check; conflict row now also requires `H_user ≠ H_new` | applied |
| 24 | **BLOCKER** — "commit all files AND the lockfile" is N+1 renames, not jointly atomic; a crash between them creates the crash-recovery state | §2.2 + §2.3(8): lockfile committed **last**; torn state self-heals via the row-23 pre-check; optional journal | applied |
| 25 | **MAJOR** — out-of-block invariant compared *after `normalize()`*, silently permitting CRLF→LF + BOM-strip of the user's untouched project data | Lever 3 #1 now compares out-of-block content **raw**; original EOL/BOM preserved on write | applied |
| 26 | **MAJOR** — inconsistent-lock re-seed (`H_base := H_user`) blesses user content as baseline → a customized block is then blind-replaced (silent overwrite) | §2.4: classify against `H_new` directly (at-target vs conflict), never blind-replace; gate re-seed on `sha256_at_install` match | applied |
| 27 | MINOR — Phase 0 undefined when a bundled artifact has a file on disk but no lockfile entry at all | §2.3(9): locked=none → in scope → route to inconsistent-lock handler | applied |
| 28 | MINOR — marker-integrity checked known ids only; a stray unknown-id marker from a bad merge passes | Lever 3 #2 now also rejects unknown-id markers | applied |
| 29 | MINOR — `sha256_at_install` normalization + version-compare type unspecified | §2.3(9): `sha256_at_install` over raw committed bytes; semver compare | applied |

**Round-2 verdict:** the marker/scoping architecture held under a second adversarial pass; every new
finding was an *implementation-spec* defect (invariant scope, a missing classification branch, commit
ordering), all now folded in. The design is converging — round 2 found no flaw in the core approach,
only in its precise statement. A third gate pass is optional; the residual risk is low enough that the
maintainer's CleanTechHub manual test (rollout step 9) is a reasonable next validation instead.

---

## 5. Rollout / task breakdown (execution order)

0. **Design gate:** run §4.2 subagent validation; fold learnings into this doc; log in §4.3. **Do not
   start code until the gate is green.**
1. **Templates:** add markers to the six marked files in `src/memory-templates/` (incl. the
   `BACKLOG_MAP.md` `area:` reorder); bump each file's frontmatter `version:`.
2. **`scaffold.py`:** implement §2.3 — the lockfile `blocks` hash map (schema change, §0.4),
   install-time per-block hashing, preserved-delta mode (hash-based classification), baseline advance,
   worklist JSON, invariant hook — **and delete the version-comparison block from the setup command**
   (re-homed here).
3. **Update command:** create `src/commands/update/Stratosphere-Update.md`; add the mirrored build step
   in `build/build.py`; move the "Update & Drift check" logic out of the installer; add the setup
   detection guard to the installer.
4. **README:** Updating subsection + Maintenance matrix row + reworded instantiate step.
5. **Build:** run `python build/build.py`; confirm `versions.json` regenerated with the new command and
   bumped templates; run `build/validate.py` (bump-guard).
6. **Automated tests:** implement §4.1 in `tests/install-harness/`.
7. **Migration tool (one-time):** author `scripts/migrations/inject_markers.py` (repo-root, not
   bundled); add the steady-state guard notice to the update command.
8. **Re-run §4.2** against the built `dist/`; confirm green.
9. **Manual test (maintainer, in IDE):** run `inject_markers.py` once against CleanTechHub, then run
   the full `/stratosphere-update` there; verify data preserved and the re-prompt gone.
   Archive/delete the migration script once all pre-marker projects are migrated.
10. **Parity (separate PR, optional):** the §2.6 `CLAUDE.md` `@import`s.

---

## 6. Risks & mitigations

| Risk | Mitigation |
|:---|:---|
| Marker injection mis-locates a block in a customized legacy file | Exact-match required for auto-injection; any mismatch is reported for manual wrap, never guessed. |
| Agent edits outside a block during a conflict merge | Lever-3 **out-of-block byte-identity** invariant aborts if *any* content outside the changed block differs — catches intra-row/field edits, not just row add/drop. |
| Mid-run crash corrupts state or fabricates a conflict on rerun | Compute-in-memory → verify → **atomic commit** (temp-write + rename); a run lands fully or not at all. |
| Marker drift (dropped/duplicated END) silently deletes a block next run | Marker-integrity invariant (one ordered START/END pair per id) checked before and after every run. |
| Hash seed vs read disagree → false conflicts on pristine blocks | Single pinned `block_hash` helper in `_versioning.py`, exact byte definition + worked-example test. |
| Frontmatter version bump changes the content hash and re-trips drift | `_versioning.body_hash` strips `version`/`timestamp` before hashing, so a bump is hash-neutral by design. |
| Forgetting to bump a template `version:` after adding markers | `build/validate.py` bump-guard fails the build. |
| `versions.json` hand-edited and drifts | Never hand-edit it — it is generated by `build.py` step 7. |
| Scope creep into a rules-relocation refactor | Markers only *wrap existing* content in place; nothing moves out of `.memory/`. |
| Import bloat from `@import` parity | Selective import of invariants only; separate PR. |

---

## 7. Out of scope
- Relocating framework rules out of `.memory/` into `.agents/`.
- A markdown-heading-aware scaffolder.
- A hand-maintained per-version migration narrative — the deterministic layer already computes "where,"
  and the marked-block design removes most of the "what to do." If ever needed, auto-generate it from
  template git diffs rather than hand-maintain.
