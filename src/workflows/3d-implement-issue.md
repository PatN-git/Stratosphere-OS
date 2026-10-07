---
name: 3d-implement-issue
description: "TDD implementation of vertical slices with token-efficient Fast-Tracks. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "2.3.0"
timestamp: 2026-10-07
---

# Implement issue

Apply strictly to backend logic, database operations, hooks, and state functions.

## Phase 0: Branch & Context Intake
**Hydrate first:** Run the `load-memory` skill to restore session context (read-only); the steps below own all side effects.
1. **Branch Isolation:** Resolve parent BT (via parent link/dependencies; if none, use slice ID). feature branch: `<type>/BT-<parentPadded>-<slug>` (using parent `type:`). Checkout/pull if exists, else create from default. If parent ambiguous, prompt (if AFK, default to slice branch). Never work on `main`. Update `.memory/STATUS.md` `Current Branch`/`Active issue`. Refresh `generated.at` (and `generated.by`) on any `.memory/` document this step mutates.
2. Read slice issue. Check if design reference in issue/BACKLOG_MAP Ref. **First-slice rule:** set the slice to `status:in progress` in `BACKLOG_MAP.md` and via `gh issue edit <n> --remove-label "status:planned" --remove-label "status:needs_spec" --remove-label "status:blocked" --remove-label "status:in review" --add-label "status:in progress"`. Promote the parent epic `planned → in progress` **only if the epic is not already at `in progress`, `in review`, or `done`** (never downgrade a further-along epic).
3. **Conditional Read:** If UX blueprint referenced, read: frozen blueprint `docs/design/BT-<padded>-interface.md`, brand tokens `.memory/DESIGN.md`, and design rules `.memory/DESIGN_RULES.md` §3. UI slices must implement design *only* from these files via Fast-Track B; never access/re-read the live generator. Re-express layout (reference only, not copy-source) in shadcn/ui [[DR-004]] + semantic HTML [[DR-006]], binding to `DESIGN.md` tokens [[DR-002]]/[[DR-003]] per `references/shadcn-build-guide.md`.
4. If no design reference, proceed to Phase 0.5.
5. **Regenerate Theme Tokens:** If design tokens/styling involved, run:
   ```bash
   python .agents/scripts/design/design_theme.py --design .memory/DESIGN.md --out <app-css-dir>/theme.tokens.css
   ```

**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**

## Phase 0.5: Plan
Plan every slice before coding; small slices get a short plan. **Skip only** a pure cosmetic slice (micro-tdd Fast-Track B scope; no plan file is written). Persist the plan to `.tmp/3d-plan-BT-<padded>.md` (scratch; 4a deletes it after ship).
- **HITL:** use the host's native planning mode where one exists (e.g. Antigravity `/plan`, Claude Code plan mode). Any approval prompt is the host's own; add no extra review halt.
- **AFK** (dispatched by 3z): no approval.
- **Required sections:** (1) files `[NEW]`/`[MODIFY]`, one-line intent each; (2) seams to test; (3) AC → planned test path; (4) existing tests at risk and how each stays green; (5) cross-cutting touchpoints (state/URL hydration, mocks/fixtures, env stubs needed for CI parity); (6) applicable memory IDs (`[[L/A/DR/G-xxx]]`); (7) open decisions.
- **Mechanical plan check (agent-run):** derive the repo's test-file naming pattern(s) from `git ls-files`; no test files yet (greenfield) → skip the pattern match and say so. Every AC needs a planned test path matching one, or an explicit `[UNCOVERED] <AC>: <reason>` plan row (one line: manual-only or design blocker; Phase 3 surfaces it), and every planned test path must match one. Any other miss → fix the plan before Phase 1.

## Phase 1: Execution via Micro-TDD Skill
Run `micro-tdd` for each change: its Route table picks Direct, Fast-Track A/B, or the bug loop; its Declare Seam takes the seams from the plan. Mark paths matching `references/merge-risk-paths.md` (plus the project's `## One-way paths`) as risky so they take its Risk route. For HITL slices, show RED/GREEN test results (override silent mode; Fast-Track A may run silent). 3d owns the full-suite runs; micro-tdd runs related tests per cycle.
- micro-tdd returns `stuck` → halt the slice; commit nothing half-done. Stash uncommitted edits so the tree stays clean: `git stash push -u -m "BT-<padded> stuck"`.
- Then HITL presents its two options; AFK returns it as `stuck` in the 3z JSON.
1. **CLI/Subprocess:** assert on stdout/stderr, not just exit code.
2. **Requirements:** link test to requirement bare IDs from BACKLOG_MAP.md/issue (not STATUS.md) (e.g., `BT-101`).
3. **Fallbacks:** prefer native libraries (e.g. sqlite3, argparse) over third-party in mock/simple utility environments.

## Phase 2: Refactoring & Architecture Checks
Adhere to:
1. **Simplify:** run the `code-simplifier` skill on the slice diff under green tests — simplify/refine without changing behavior; re-run related tests after and keep them green.
2. **Architecture Rules:** verify architectural structure matches `[[A-xxx]]` rules in `.memory/ARCHITECTURE.md`.
3. **Incremental Commits:** commit incrementally per TDD milestone: `<type>(BT-<slicePadded>): <summary>`; run related tests before each incremental commit.
4. **Canonical naming:** name identifiers after GLOSSARY terms; never introduce `Avoid:` synonyms.
5. **Avoid-drift check:** check changed identifiers against GLOSSARY `Avoid:` lists (whole-identifier only). Ignore third-party/library names, import paths, string literals, and comments. Propose renames (citing the canonical term + `[[G-xxx]]`) at REFACTOR/HITL gate; never auto-rename. Scope: slice diff only.

## Phase 3: Slice Completion Gate
Confirm slice against AC (inline self-check, not sub-agent). Ephemeral (no tracked writes; `.tmp/` scratch only).
1. Read slice AC.
2. Produce an **exhaustive coverage map**: for every AC, name the passing test that covers it or mark it `[UNCOVERED]` — list each by name, never summarize as "looks complete."
3. Resolve each `[UNCOVERED]`: testable → return to the micro-tdd loop and cover it; genuinely uncoverable (e.g. design blocker) → surface it explicitly, never silently ship.
4. Done only when every AC maps to a passing test, or an `[UNCOVERED]` item is explicitly surfaced, and step 6's full run is green.
5. Compare the coverage map with the plan's AC → test list (skipped when Phase 0.5 was skipped). Name every deviation and write them to a `## Deviations` section of `.tmp/3d-plan-BT-<padded>.md`; none → `none`.
6. Run the full suite once at HEAD (the only full run in 3d); red → return to the micro-tdd loop, do not hand off. Write `{"head_sha", "cmd", "observed"}` (the observed summary line) to `.tmp/3d-suite-BT-<padded>.json`.
7. Done also requires a clean tree after the full run, so files the suite generated are checked (`git status --porcelain` — all work committed per Phase 2.3) under the `/4a-verify-and-ship` Phase 1 step 0 guard; it halts `[UNCOMMITTED]` otherwise.

**Hand-off:** Run `/4a-verify-and-ship` to verify and open/update PR.