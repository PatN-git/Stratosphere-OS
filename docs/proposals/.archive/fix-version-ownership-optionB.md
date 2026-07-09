---
type: proposal
title: "Fix: Version Ownership (Option B) + DR-016 Back-Reference"
description: Make .memory frontmatter version project-owned; track template version via lockfile + block markers; make update-scope content-based. Self-contained, executable plan.
status: draft
timestamp: 2026-07-08
version: "1.0.0"
---

# Fix Plan — Version Ownership (Option B) + DR-016 Back-Reference

> Self-contained. An agent with no prior context should be able to execute this end-to-end from this
> file plus the code it names. It is a follow-up fix to `optimize-stratos-update-flow.md` (the
> marker-based `/stratosphere-update` design); read §0 there only if you need the marker/hash model.
> **Do not implement while reading — this is the plan; a separate step implements it.**

Repo root (worktree): `.../optimize-stratos-update-flow/`. Source of truth is `src/`; `python
build/build.py` compiles to `dist/`; `versions.json` is generated (never hand-edited). Key file:
`src/scripts/scaffold.py`.

---

## 1. WHY

### 1.1 The bug found during live implementation
`.memory/*.md` frontmatter carries a `version:` field. It is **conflated across two owners**:

| Owner | Where | Meaning |
|---|---|---|
| **StratOS bundle** | `src/` templates → `versions.json` (via `build.py`) | the framework/template revision |
| **The live project** | a scaffolded downstream repo (e.g. CleanTechHub) | the file's own evolution; project agents bump it as they add entries. It can legitimately exceed the template version (e.g. `1.3.0`). |

The update flow **stamps the bundle version onto the frontmatter** — `scaffold.py`
`update_frontmatter_version(proposed_text, b_version)` (called in the update commit path, ~L759). A
project file at `1.3.0` is silently regressed to `1.1.4`. The lockfile write then **reads that stamped
value back** (~L836-839, `v, ts = read_version(text)`), laundering the downgrade into the lockfile so
it is concealed permanently.

Verified facts (from `src/scripts/scaffold.py`):
- Scope/staleness is decided from the **lockfile** version, not the frontmatter (~L618-626), so scope
  itself is not the bug — the frontmatter stamp + read-back is.
- Per-block classification (`H_user`/`H_base`/`H_new`) already handles pristine / conflict /
  unchanged / already-at-target / inconsistent-lock correctly (~L684-730).
- Block markers already carry a per-block template version: `<!-- SOS:BLOCK id=… v=1.1.4 -->` (set on
  swap, ~L741; seeded by migration; shipped in templates).

### 1.2 The fix direction — Option B (chosen over Option A)
- **Option B (this plan):** frontmatter `version:` is **project-owned**; the update flow **never
  writes it**. The template version is tracked by the **lockfile** (per-artifact) plus the **per-block
  `v=` markers** (already in the file). No new frontmatter field, no migration.
- **Option A (rejected): add a second `sos_version:` field.** Rejected because (a) it is redundant with
  the per-block `v=` markers, which already record template provenance *in the file at the correct
  granularity*; (b) a single file-level template version cannot honestly represent a file whose blocks
  are at mixed versions (one swapped, one still-conflicted); (c) two adjacent version fields is
  permanent toolchain surface (`build.py`, `validate.py` bump-guard, `read_version`, `inject_markers`)
  and a "which do I bump?" rot hazard. The "self-describing file" benefit A chases is already provided
  by the block markers.

### 1.3 A second, related risk this plan closes
Once frontmatter is project-owned, a version number can *lie* about template state (e.g. after
`repair-lock`, or adopting a pre-lockfile project). If update-scope keyed only on a version comparison,
a wrong version would **suppress a genuinely needed update**. So this plan also makes **scope
content-based**: a file is stale if the template's block content differs from the recorded baseline —
independent of any version number.

### 1.4 DR-016 regression (unrelated, bundled here)
In `src/memory-templates/DESIGN_RULES.md`, the `design-reference-rules` block's `DR-016` entry lost its
trailing `([[DR-011]])` back-reference when markers were added (v1.0.4 → v1.0.5). `DR-011` references
`DR-016`; the reciprocal was dropped, and the memory validator flags the one-way reference. Restore it.

---

## 2. WHAT (the target end-state)

1. **The update flow never modifies frontmatter `version:`.** Frontmatter is project data.
2. **The lockfile is written from the applied bundle version directly** (from the worklist), not by
   reading the file's frontmatter back — **and each block's baseline hash records the bundled TEMPLATE
   content (`H_new`), not the user file's content**, so customized/merged blocks are not silently
   overwritten on a later update (see §3.2).
3. **Update-scope is content-based:** a marked preserved file is in scope iff the file is missing, OR
   the lockfile lacks a complete `blocks` map, OR any block's recorded baseline hash differs from the
   bundled template's block hash, OR (fast-path) `locked_version < bundle_version`. The version
   comparison becomes a hint, not the sole gate.
4. **`repair-lock` and the seed path never source the template version from the project frontmatter,
   and never falsely claim the bundle version for older content.** They trust current content as the
   baseline (seeding `blocks` from current hashes) and derive the file-level `version` from the block
   `v=` markers, with a documented "customizations present at repair time become the new baseline"
   caveat. The `blocks` map seeding must be preserved.
5. **`DESIGN_RULES.md` DR-016** carries `([[DR-011]])` again; file bumped `1.0.5 → 1.0.6`; block marker
   `v=1.0.6`.
6. **The parent proposal is corrected** so spec and code agree (§0.4, §2.2 Phase 3, §2.3): frontmatter
   `version:` is project-owned and never written by the update flow; scope is content-based.
7. **Tests** encode the corrected semantics (frontmatter unchanged, lockfile advanced) and cover the
   downgrade, content-based-scope, and repair cases.

Non-goals: no new frontmatter field; no change to how `build.py` reads `version:` from `src/` templates
(there it *is* the template version — correct); no change to the marker/hash classification logic.

---

## 3. HOW (concrete changes)

All line numbers are approximate anchors in `src/scripts/scaffold.py`; locate by the function/behavior,
not the number. Rebuild with `python build/build.py` and run `build/validate.py` after source edits.

### 3.1 Stop stamping frontmatter in the update path
- **Remove the `update_frontmatter_version(proposed_text, b_version)` call** in the update commit path
  (~L759). Do **not** guard it — remove it. Frontmatter is never written by `--update`.
- Keep `detect_and_apply_newline(...)` (~L760) — newline preservation is still required.
- Leave the `update_frontmatter_version` **function definition** in place only if another caller needs
  it; if nothing else calls it after this change, delete the function too (grep first).
- The block marker `v=` swap (~L741, `v={b_version}`) **stays** — that is the per-block template-version
  record.

### 3.2 Write the lockfile from the bundle version AND store the TEMPLATE block baseline
In the post-commit lockfile write (~L833-844), two changes:

**(a) version — stop reading the frontmatter back; use the bundle version from the worklist.**
```diff
 for proj_path, info in worklist["preserved_files"].items():
     p = project / proj_path
     if p.exists():
         text = p.read_bytes().decode("utf-8")
-        v, ts = _versioning.read_version(text, p)
         lock_entry = {
-            "version": v or info["new_version"],
+            "version": info["new_version"],   # applied template (bundle) version
             "sha256_at_install": _versioning.body_hash(text)
         }
```

**(b) `blocks` baseline — store the bundled TEMPLATE block hash (`H_new`), NOT the user file's block
hash.** This is a correctness fix, not a cosmetic one, and it reverses the current code:
```diff
-        blocks = get_blocks_map(text)          # BUG: hashes the USER file → baseline drifts
-        if blocks:
-            lock_entry["blocks"] = blocks
+        # Baseline must be the template content last reconciled against, so that next run
+        # H_user==H_base means "unchanged since last template" and H_user!=H_base means "customized".
+        lock_entry["blocks"] = { bid: block_hash(bundled_text_for(proj_path), bid)
+                                 for bid in template_block_ids_for(proj_path) }
```
**Why (from the verify pass):** `H_base` is defined as *the template baseline the user's content is a
customization of*. If it is seeded from the user's file, then after a **conflict merge** (user content
= merged, ≠ template) the next update computes `H_user == H_base` (both = merged) and `H_new != H_base`
→ classifies the block **pristine → swaps to pure template → destroys the merge**. Storing `H_new`
instead makes a later template change to a kept-custom/merged block correctly classify as **conflict**.
The rule is uniform: **after a committed update, every block's `H_base := bundled H_new`** — a no-op for
unchanged/left-as-is blocks (their `H_new == H_base` already), correct for pristine/already-at-target
(content == template), and correct for conflict-merged (baseline = the template they merged against).
Source `H_new` from the bundled template (recompute `block_hash(bundled_text, bid)`, or reuse
`info["blocks"][bid]["new_hash"]` which classification already recorded) — never from the user file.

### 3.3 Make update-scope content-based
Today (~L618-626) scope is purely `semver(b_version) > semver(locked_version)`. Augment it so template
content changes are detected even when the version number would not flag them. This can be decided from
the **lockfile `blocks` map vs the bundled template's block hashes** — no need to read the user file at
scope time:
```
locked_version = lock_entry.get("version")
locked_blocks  = lock_entry.get("blocks", {})            # H_base per block
bundled_block_hashes = { id: block_hash(bundled_text, id) for id in template_block_ids }  # H_new

is_stale = (
    (not p.exists())
    or (not locked_version)
    or (semver_key(b_version) > semver_key(locked_version))     # fast-path hint
    or (set(locked_blocks) != set(bundled_block_hashes))        # blocks added/removed or map incomplete
    or any(locked_blocks.get(bid) != h for bid, h in bundled_block_hashes.items())  # content drift
)
```
Notes:
- Parse the bundled template once per file to get `template_block_ids` + `bundled_block_hashes`. The
  bundled bytes are already read before the scope decision (~L587), so this needs no new I/O ordering;
  memoize so scope and classification (~L671-691) share the parse.
- This makes a wrong/stale version number unable to suppress a real update, and makes a bundle that
  bumps *only* a block (without a file version bump) still update. Keep the version comparison as the
  cheap first check.
- **Remove the stray `print(f"DEBUG version check ...")`** (~L628) that sits in this block while you are
  here.

### 3.4 Fix `repair-lock` and the seed path (generate_lockfile)
Both currently read the frontmatter `version:` (`repair` ~L480-494; seed ~L497-510). Under Option B the
frontmatter is project-owned, so neither may use it as the template version.

- **Do not read the frontmatter `version:` for the lockfile entry.** Derive the file-level `version`
  from the block `v=` markers instead: `version = min(marker_versions, key=semver_key)` (most
  conservative; with content-based scope the exact value is non-critical). Use `semver_key` — plain
  `min()` over version *strings* compares lexicographically (`"1.9.0" > "1.10.0"`, wrong);
  `semver_key` already exists in `scaffold.py` (~L42) and is the comparator scope uses. If a file has no
  parseable markers, fall back to the bundled `b_meta["version"]` for a freshly-scaffolded file, else
  record `"unknown"`.
- **Do not blindly record the bundle version** for a file whose block content may be older — that would
  (via any residual version fast-path) claim "current." Content-based scope (§3.3) is the real
  protection, but the recorded version must still not overstate.
- **Preserve `blocks` seeding** (the `get_blocks_map` lines at ~L490-492 and ~L506-508). An earlier
  draft diff dropped these — do **not** drop them. Note the deliberate asymmetry vs §3.2: the mainline
  *commit* stores the **template** hash (`H_new`) as the baseline, but repair/seed **trust the current
  workspace content** (`get_blocks_map(user file)`) as the baseline — that is the intended semantics of
  a recovery/adoption tool ("this is now your baseline"), with the caveat below.
- **Repair semantics / caveat (document in the command help and a code comment):** `repair-lock` trusts
  the current workspace content as the new baseline (`H_base := current`). Consequence: any block a user
  had *customized* becomes the baseline, so a later template change to that block will be offered as a
  *pristine swap* (i.e. may overwrite the customization). This is acceptable for a rare recovery tool
  but must be stated. If stronger safety is wanted later, gate repaired-then-changed blocks through the
  inconsistent-lock/conflict path — out of scope here.

### 3.5 DR-016 template fix (`src/memory-templates/DESIGN_RULES.md`)
1. In the `design-reference-rules` block, restore the trailing back-reference on the DR-016 line:
   `…one display/serif + one neutral/sans.` → `…one display/serif + one neutral/sans ([[DR-011]]).`
2. Bump frontmatter `version: "1.0.5"` → `"1.0.6"`; update `timestamp`.
3. Bump the `design-reference-rules` block marker `v=1.0.5` → `v=1.0.6`.
4. Confirm `DR-011` still references `DR-016` so the link becomes bidirectional (grep for `[[DR-016]]`).
5. `python build/build.py`; confirm `dist/*/versions.json` shows `DESIGN_RULES.md` at `1.0.6` and the
   dist copy contains `([[DR-011]])`; `build/validate.py` passes (bump-guard satisfied by the bump).

### 3.6 Reconcile the parent proposal
Edit `docs/proposals/optimize-stratos-update-flow.md`:
- §0.4: stop describing the lockfile `version` as "the framework version a project file was installed
  at" in a way that implies frontmatter == template version. State: frontmatter `version:` is
  project-owned; template version = lockfile + block `v=` markers.
- §2.2 Phase 3: change "set its frontmatter `version:` to the bundled version **and** write the lockfile
  entry" to "advance **only the lockfile** (version + block hashes); never write frontmatter `version:`."
- §2.2 Phase 0 / §2.3: state scope is content-based per §3.3 here.
- Add a one-paragraph "Version ownership (Option A vs B)" note recording why B was chosen (§1.2), so it
  is not re-litigated.

---

## 4. TESTS

Location: `tests/test_update_flow.py` (extend) + a build check. All deterministic (pytest-style /
the project's existing harness). Subagents are **not** needed for the assertions below — but §4.3 adds
one optional adversarial subagent pass for semantics, which is where a subagent earns its keep.

### 4.1 New / changed deterministic tests
1. **`test_project_version_preserved` (the core regression).** Fixture: `.memory/BACKLOG_MAP.md`
   frontmatter `version: "1.3.0"`, block markers `v=1.1.3`; lockfile `version: "1.1.3"` + `blocks` at
   the 1.1.3 hashes; bundle `1.1.4` with a changed `backlog-rules` block. Run `--update`. Assert:
   frontmatter still `"1.3.0"` (NOT downgraded); lockfile `version == "1.1.4"`; `backlog-rules` content
   updated; its marker now `v=1.1.4`; other blocks + backlog rows + `area:` line byte-identical.
2. **`test_frontmatter_never_written_even_when_bundle_higher`.** Fixture frontmatter `version: "1.1.3"`
   (equal to old template), bundle `1.1.4`. Assert frontmatter stays `"1.1.3"` after update (proves the
   stamp is gone, not just guarded), lockfile advances to `1.1.4`.
3. **`test_content_based_scope_catches_stale_block_at_equal_version`.** Fixture: lockfile
   `version == bundle` (`1.1.4`) but lockfile `blocks[backlog-rules]` = an OLD hash ≠ bundled block
   hash. Assert the file is still put in scope and the block updated (proves §3.3 — a version number
   cannot hide a stale block).
4. **`test_repair_lock_does_not_inflate_or_read_frontmatter`.** Fixture: frontmatter `version: "1.3.0"`,
   markers `v=1.1.3`, no lockfile. Run `repair-lock`. Assert lockfile `version` is derived from markers
   (`"1.1.3"`), NOT `1.3.0` and NOT the bundle; `blocks` map is seeded (non-empty). Then set bundle to
   `1.1.5` and run `--update`: assert the file is in scope and updates (repaired lock did not block it).
5. **`test_repair_then_update_pristine`.** After `repair-lock` on a pristine (uncustomized) file, a
   subsequent `--update` classifies its blocks as pristine and swaps cleanly (no spurious conflict).
6. **`test_customization_survives_second_update` (the §3.2 regression guard — REQUIRED).** This is the
   case the verify pass proved the earlier design silently broke, and which no other test catches.
   Fixture: a file with **block A** the template will change and **block B** the user has customized
   (template for B unchanged). Run `--update`: assert A swapped, B untouched, lockfile
   `blocks` now hold **template `H_new`** for every block. Run `--update` **again with the same bundle**:
   assert the file is **out of scope** (no re-classification), B is **byte-identical**, and A is not
   re-swapped. Then add a **merge variant**: after a conflict-merge commit of block A, a second
   `--update` with an *unchanged* bundle leaves the merged content byte-identical (does NOT reclassify
   it pristine and overwrite). If the baseline were stored as the user's content, both variants would
   re-swap and fail — that is the assertion that matters.
7. **Update existing regression tests.** Change assertions that expect the **frontmatter** version to
   advance — under Option B they must assert **frontmatter unchanged** and **lockfile advanced**:
   - Needs change (hard-asserts frontmatter `1.1.4`): `test_pristine_update` (~L167, L177),
     `test_atomicity_crash_recovery` (~L728), `test_unchanged_but_bumped` (~L618).
   - **Verify, likely no change:** `test_conflict_update` (~L310) asserts `version: "1.1.4"` but that
     value is hardcoded in the `.stratosphere-new` merge fixture it writes, so removing the stamp does
     not affect it — confirm by trace, don't blindly edit. `test_crlf_bom_preservation` has no version
     assertion — leave it.
7. **`test_dr016_backref_restored`** (build/template): after `build.py`, assert `versions.json` has
   `DESIGN_RULES.md == 1.0.6`, the dist template's DR-016 line contains `([[DR-011]])`, and running the
   memory validator on a project using it produces no one-way-reference warning for DR-011/DR-016.

### 4.2 Idempotency & no-op checks
8. **`test_update_idempotent`.** Run `--update` twice on scenario (1). Second run: file out of scope
   (blocks match, version now equal), zero writes.
9. **`test_dry_run_no_writes`.** `--update --dry-run` writes only `*.stratosphere-new` staging files and
   the worklist; the real files and lockfile are untouched.

### 4.3 Optional adversarial semantics pass (independent subagent)
After the deterministic tests pass, run **one `general-purpose` subagent** as an independent verifier of
the *version-ownership semantics* (the part unit tests under-cover because it is about intent, not a
single assertion). Give it: this plan, the patched `scaffold.py`, and a scratch mock project. Task it to
hunt specifically for: (a) any code path that still writes frontmatter `version:` on `--update`; (b) any
path where a project-owned version can leak into the lockfile as the template version; (c) any path
where a stale block can be skipped because a version number claims "current"; (d) whether `repair-lock`
can bake a customization in and later silently overwrite it, and whether that is documented. Fold its
findings back before shipping. (Deterministic tests verify behavior; the subagent verifies the *space of
paths* a fixed test set misses.)

### 4.4 Manual verification
- `python build/build.py` succeeds; `versions.json` shows DESIGN_RULES `1.0.6`.
- Existing L1 install harness still passes.
- Dry-run `--update` against a copy of a real project (CleanTechHub) with a hand-bumped
  `.memory/BACKLOG_MAP.md` `version:` → confirm frontmatter is preserved and the lockfile advances.

---

## 5. Rollout order
1. §3.5 DR-016 template fix + build (independent, low-risk; land first).
2. §3.1 remove frontmatter stamp; §3.2 lockfile-from-bundle. (Core downgrade fix.)
3. §3.3 content-based scope. (Depends on shared bundled-block-hash parse.)
4. §3.4 repair-lock / seed path + caveat docs.
5. §4 tests (write §4.1(6) test updates alongside the code they cover, not after).
6. §3.6 reconcile the parent proposal.
7. §4.3 optional subagent semantics pass; §4.4 manual verification.

## 6. Risks
| Risk | Mitigation |
|---|---|
| Removing the stamp but missing §3.2 → lockfile records the project's `1.3.0` → future updates blocked | §3.2 and §3.1 land together; test (4) asserts lockfile == bundle, not frontmatter. |
| **Storing the user's block content as `H_base` → content-based scope reclassifies customized/merged blocks as pristine and overwrites them next run** (found in verify pass) | §3.2(b): mainline commit stores the **template** `H_new` as baseline; test (6) proves customization/merge survives a second `--update`. |
| Content-based scope regresses performance (parses every bundled template) | Templates are small and few; memoize the bundled parse shared with classification. |
| repair-lock adopts a customization as baseline → later overwrite | Deliberate trust-current semantics for a recovery tool; documented caveat (§3.4); stronger gating deferred. |
| DR-016 bump collides with in-flight fixtures pinned to 1.0.5 | Re-point any 1.0.5 DESIGN_RULES fixtures to 1.0.6 (grep tests). |

## 7. Verify-pass findings (folded in)
An independent verifier subagent checked this plan against the actual `scaffold.py`/`_versioning.py`/
`DESIGN_RULES.md`. It confirmed all line anchors, that no other reader depends on `.memory` frontmatter
being the template version, that content-based scope is implementable where stated, and that the DR-016
facts hold. It found and this revision fixed:
| # | Severity | Finding | Fix |
|---|---|---|---|
| 1 | BLOCKER | Post-commit baseline seeded from the **user file** (`get_blocks_map`), so content-based scope would reclassify merged/customized blocks as pristine and overwrite them | §3.2(b): store template `H_new` as baseline |
| 2 | BLOCKER | No test exercised the two-cycle customization-survival path → the regression would ship green | §4.1(6) added |
| 3 | MAJOR | `min(marker v)` compares version strings lexicographically | §3.4: `min(..., key=semver_key)` |
| 4 | MINOR | Stray `DEBUG` print in the scope block being rewritten | §3.3: remove it |
| 5 | MINOR | Test-update list mis-stated `test_conflict_update` as needing a change | §4.1(7) corrected |
