# Plan — Lifecycle-Run Defects (StratOS 3.3.0 field report)

**Status:** Implemented on `feat/spec-conformance-v4` (PR #107), shipping in 4.0.0. See §4 for deviations from the draft.
**Origin:** Full lifecycle run (`1b → 2a → 2b → 2c → 3b → 0b`) on CleanTechHub, 2026-09-22.
**Delivery:** one commit per item, folded into the v4 PR. First built on `main` (3.3.0), then replayed onto v4; the 3.4.0 release commit was dropped. Paths below use v3 names; on v4 the workflows are `src/workflows/<nn>-<name>.md` and setup is `src/commands/stratosphere-setup/SKILL.md`.
**Release impact:** none separately; ships inside v4.0.0.

---

## 0. Verification of the report (done before planning)

| Item | Verdict | Evidence |
|---|---|---|
| P0-A storage/bootstrap | **Confirmed, but 7 templates, not 9** | `src/skills/plan-html/assets/templates/` has 7 templates, all with unguarded `localStorage` + `DOMContentLoaded`-only boot. `base-template.html` is also `DOMContentLoaded`-only (no storage). The 8 `test/output/` fixtures copy the same bootstrap. |
| "9 templates" | **Root cause elsewhere** | `annotated-flowchart` and `implementation-plan` were deleted in `9406151`. They survive in `~/.claude/plugins/stratosphere-os/` because `scripts/install-claude-code.{sh,ps1}` merge-copy (`cp -rf dist/claude-code/* …`) and never remove anything. The Antigravity installer already does per-item remove-then-copy. |
| Why CI missed P0-A | Harness gap | `tests/verify_plan_html.mjs` calls `renderBody()` directly and never runs the bootstrap; its mock `localStorage` never throws. |
| P1-A 0b consent | **Confirmed + worse** | 0b step 4 writes `LEARNINGS.md` directly. That contradicts `memory-protocol.md` (line 80: never write LEARNINGS without proposing and confirming). It is a Core Rule violation, not just an inconsistency. |
| P1-B stale companions | Confirmed | Rendered by `1b` step 4 (discovery), `2a` step 6 (PRD), `3a` steps 5–6 (ROADMAP, committed). No re-render anywhere; `2c` Phase 4 edits the sources. |
| P1-C placeholders | Confirmed | `3b` Phase 3.3 mints the draft verbatim with no placeholder check. |
| P2 2a order | Confirmed | Commit is step 3, render is step 6. **Becomes moot under P1-B.** |
| P2 2b gate | Confirmed | `2b` Phase 5.5 routes on "≥ 2 unassigned `tier:epic`". |
| P2 3b ODI fallback | Confirmed | `3b` Phase 2.2 "Prompt user" with no HALT. |
| P2 okf §5 vs 2c | **Confirmed; §5 is the dead rule** | §5 says generated docs get the plugin version. In practice every CleanTechHub PRD/discovery doc starts at `1.0.0` and gets revision bumps (`1.5.1`, `1.2.1`, …). `2c` 4.3 matches practice. |
| P2 `area:` registry | **Template is fine; setup drops it** | `src/memory-templates/BACKLOG_MAP.md:36` seeds `area:`. Setup Checkpoint 6 overwrites the registry with the "final resolved label set" and treats `area:` as the only project-defined dimension. A brownfield repo with no `area:*` labels at install ends up with no line. |

---

## 1. Commits

### C1 — `fix(plan-html): storage-safe, render-first bootstrap` (P0-A)
**Files:** the 7 `assets/templates/*.html`, `assets/base-template.html`, the 8 `test/output/*.html` fixtures, `SKILL.md`.
- Apply the report's fix: guard `localStorage` get/set with try/catch, add `bootPlan()` that calls `renderBody` **before** `initTheme`, and boot on `document.readyState`, not only `DOMContentLoaded`.
- `board.html` / `triage-board.html`: keep the `originalColumns` seeding inside `bootPlan()`, before render.
- `base-template.html`: readyState boot only (it has no theme code).
- `SKILL.md`: one constraint line, so hand-composed pages follow it too: *"Storage and theme code must never gate rendering: wrap storage in try/catch; render before theming; boot via readyState check."*

**Test (goes in with C1, and must fail before the fix):** add a boot-path suite to `tests/verify_plan_html.mjs`:
- For every template (with the matching fixture's `plan-data` injected: board→`triage-board`, trade-off-matrix→`db-options-matrix`, plan-document→`complex-plan-document`, others same name) and every fixture: build the vm context with a `localStorage` getter that throws `SecurityError`, set `document.readyState = 'complete'`, and never dispatch `DOMContentLoaded`.
- Assert the content container is non-empty, and `.spy-section` count > 0 for plan-document.
- Run it against the current tree first to confirm it fails on all 7 templates.

**Manual check:** open one generated page as a `data:` URL in the built-in browser and confirm `document.querySelectorAll('.spy-section').length > 0`.

### C2 — `fix(0b): confirm learnings, durability gate, supersession prompt` (P1-A)
**File:** `src/workflows/0b_stop-session.md`.
- Step 4: *"Propose the entry text (ID, tag, `Source:`); write only on confirmation."* Same gate as step 6.
- Step 4 durability gate, applied before proposing: *"Would this still be true after the work that prompted it ships? If no → record it in the issue or `STATUS.md`, not `LEARNINGS.md`."*
- Step 6, after confirmation: *"If a step-4 learning is now codified by the new `[[A-xxx]]`, propose superseding it (`L-xxx → A-xxx`, per supersession protocol)."*
- Handoff format: `New learnings (ID, tag, one-line text)`, so bare IDs no longer appear.

### C3 — `feat(plan-html)!: HTML companions are ephemeral renders` (P1-B, closes P2 "2a order")
Rule: a companion of a committed `.md` is rendered to `.tmp/render/<source path>.html` (already gitignored and ephemeral per AGENTS.md §3). It is never committed and never reused: it is regenerated from the current `.md` every time it is presented.
- `1b` step 4: path → `.tmp/render/docs/discovery/<slug>.html`.
- `2a` step 6: path → `.tmp/render/docs/prds/…html`. Nothing to commit, so the commit-before-render ordering defect disappears.
- `3a` steps 5–6: render ROADMAP to `.tmp/render/docs/ROADMAP.html`; the commit becomes `git add docs/ROADMAP.md` only.
- `plan-html/SKILL.md` output rule: companion renders go under `.tmp/render/`; always regenerate, never serve an existing render.
- **Out of scope, stays committed:** `2b` `docs/design/BT-<n>-directions.html` and prototypes. They are standalone option records for a decision, not mirrors of an `.md`.
- **Consumer migration:** release-note one-liner (`git rm --cached docs/prds/*.html docs/discovery/*.html docs/ROADMAP.html`). No migration step in any workflow (no-token-bloat-migrations).

### C4 — `fix(3b): pre-mint placeholder guard and mint order` (P1-C)
**File:** `src/workflows/3b_create-issue.md`.
- Phase 2.3 draft rule: cite only memory IDs that exist in `.memory/`. A not-yet-written ADR is written as plain text (`ADR pending: <title>`), never `[[A-xxx]]`.
- Phase 3.3 pre-mint guard: `grep -nE 'BT-<[^>]+>|\[\[[A-Z]+-[xX]+\]\]'` on the drafts file. Any hit → HALT and list the hits. The report's regexes are widened: `DR-` has two letters, and slice placeholders can contain digits.
- Mint order: when slices reference siblings, state a topological mint order (blockers first; a cycle → HALT, since Blocked-by must be a DAG). After each mint, substitute the real `BT-<padded>` into dependents' drafts in `.tmp`. This is a mechanical substitution and is allowed; regeneration is not. Phase 3.4 reads the same draft, so `BACKLOG_MAP` Ref is covered by the same guard.

### C5 — `fix(2b): route to /3a only when MAJOR.MINOR is undecided` (P2)
`2b` Phase 5.5: replace the "≥ 2 unassigned `tier:epic`" clause with *"parent epic has no GitHub milestone (`gh issue view <n> --json milestone` → null; 3a is the only milestone assigner)"*. Keep the "≥ 2 features contend for the current release" clause. Add: a sprint-digit change is `/3c`'s job, after `/3b`.

### C6 — `fix(3b): ODI fallback is an explicit HALT` (P2)
`3b` Phase 2.2 fallback: *"HALT: ask the user for Impact and Confidence; never infer them (inferred values move priority buckets)."* Same shape as the other HALTs in 3b.

### C7 — `fix(okf): define version handling for docs edited after generation` (P2)
v4 deliberately kept plugin-version stamping for generated docs (its templates carry `version: <plugin version>   # stamped at generation`). Decision (user, 2026-09-22): keep that. §5 gains an **Edited Docs** rule: an editing run re-stamps `version` to the installed plugin version and refreshes `generated.at`/`generated.by` once per run; `version` is never a document revision. `2c` Phase 4.3 now follows it instead of applying patch/minor increments.

### C8 — `fix(setup): always preserve the area: registry line` (P2)
`src/commands/instantiate/Instantiate-StratosphereOS.md` Checkpoint 6 (Greenfield step 3, Brownfield step 6): the written registry **must keep** an `Area (area:xxx)` line. When GitHub has no `area:*` labels, write it as *"project-defined — add slugs as introduced"*. Add `area:` to the `BACKLOG_MAP.md` PRESERVATION RULE line. 3b's "propose adding to registry" flow then works for new slugs unchanged.

### C9 — `fix(install): claude-code installer replaces shipped items` (orphan root cause)
`scripts/install-claude-code.sh` and `.ps1`: port the Antigravity overlay.
- `plugins/stratosphere-os/`: per top-level item remove-then-copy; `skills/` merged per skill.
- `commands/` and `skills/` under `~/.claude` are shared user dirs: remove-then-copy **only each shipped entry**, never wipe the dir.
- Test: `tests/test_install_overlay.py` (skip if no bash). Run `install-claude-code.sh --local --target <tmp>` after planting (a) an orphan file in `skills/plan-html/assets/templates/` and (b) a foreign skill dir. Assert (a) is gone and (b) survives.
- **Known limit:** an entire skill or command removed upstream still orphans; detecting that needs an install manifest. Not addressed here.

### C10 — `chore: version stamps + release notes`
Per-file OKF bumps for touched `src/` files (validate.py fork-point baseline), `dist/` rebuild, release notes incl. the C3 consumer migration line and the note that `/stratosphere-update` + reinstall clears the orphan templates.

---

## 2. Verification gate (before 4a/PR)
- `node tests/verify_plan_html.mjs`: new boot-path suite red on `main`, green on branch.
- `pytest` (includes 3b phrase-expectation tests in `test_subagent_spawning.py`; update expected phrases if C4/C6 change them).
- `python build/build.py && python build/validate.py`; `scripts/check.sh`.
- Manual `data:` URL check (C1).
- Re-read each edited workflow once for internal consistency (step numbers, handoff text).

## 3. Open risks
- C3 changes a visible habit: reviewers lose the rendered PRD in PR diffs. Accepted trade-off, chosen explicitly.
- CleanTechHub still holds 9 committed companions until someone runs the migration line.

## 4. Implementation notes (deviations from the draft)
- **C1:** the readyState dispatch is the script's **last line**, not the report's in-place block: a synchronous `bootPlan()` mid-script would hit board's later `const originalColumns` in its TDZ. The boot suite simulates blocked storage by omitting the global (vm ignores sandbox accessors); the real-browser check used a `DOMException('SecurityError')` getter over HTTP (main: 0 sections, `{{title}}`; fixed: 6 sections).
- **C2:** also applied propose-then-confirm to step 5 (GLOSSARY.md), under the same memory-protocol rule.
- **C3:** also corrected okf-protocol's example of excluded `docs/**/*.html`, which named `docs/ROADMAP.html`.
- **C7:** reversed from the draft (see C7). v4 had already fixed the template-version leak by splitting template and artifact frontmatter.
- **Versions:** files v4 had already bumped above v3.3.0 keep v4's number (plan-html 1.2.0, okf 2.0.0, BACKLOG_MAP 1.3.0, setup 1.1.0, 2c 1.1.0). Otherwise minor, since each change alters behavior: 0b 1.2.0, 1b 1.2.0, 2a 1.4.0, 2b 1.4.0, 3a 1.2.0, 3b 2.4.0.
- **Review follow-ups (independent judge):** (1) 3b's guard as drafted halted on the sibling placeholders the mint order exists to resolve. Sibling refs now use a defined `BT-<slice:N>` form: a whole-file check tolerates only that form, and a strict per-slice check runs before each mint. (2) 2b routes to `/3a` only when 3a's scale-gate would also act (no milestone **and** ≥ 1 other unassigned epic, or contention); a lone feature goes straight to `/3b`. Also: the sh installer now includes dot-dirs (`.claude-plugin/`), matching the ps1.
- **Gate inventory:** new HALT/confirm points are registered in `tests/lifecycle-harness/gates.md`.
- **Consumer migration** (goes in PR #107's body): `git rm --cached docs/prds/*.html docs/discovery/*.html docs/ROADMAP.html`.
