---
name: 3d_implement-issue
description: TDD implementation of vertical slices with token-efficient Fast-Tracks.
type: workflow HITL
trigger: manual
version: "2.0.14"
timestamp: 2026-07-17
---

# Implement issue

Apply strictly to backend logic, database operations, hooks, and state functions. Run `.agents/skills/code-simplifier/SKILL.md` at end.

## Phase 0: Branch & Context Intake
1. **Branch Isolation:** Resolve parent BT (via parent link/dependencies; if none, use slice ID). feature branch: `<type>/BT-<parentPadded>-<slug>` (using parent `type:`). Checkout/pull if exists, else create from default. If parent ambiguous, prompt (if AFK, default to slice branch). Never work on `main`. Update `.memory/STATUS.md` `Current Branch`/`Active issue`.
2. Read slice issue. Check if design reference in issue/BACKLOG_MAP Ref. Set slice & parent epic to `status:in progress` in `BACKLOG_MAP.md` and via: `gh issue edit <n> --remove-label "status:planned" --remove-label "status:needs_spec" --remove-label "status:blocked" --add-label "status:in progress"`.
3. **Conditional Read:** If UX blueprint referenced, read: frozen blueprint `docs/design/BT-<padded>-interface.md`, brand tokens `.memory/DESIGN.md`, and design rules `.memory/DESIGN_RULES.md` §3. UI slices must implement design *only* from these files via Fast-Track B; never access/re-read the live generator. Re-express layout (reference only, not copy-source) in shadcn/ui [[DR-004]] + semantic HTML [[DR-006]], binding to `DESIGN.md` tokens [[DR-002]]/[[DR-003]] per `.agents/workflows/.reference/shadcn-build-guide.md`.
4. If no design reference, proceed to Phase 1.
5. **Regenerate Theme Tokens:** If design tokens/styling involved, run:
   ```bash
   python .agents/scripts/design/design_theme.py --design .memory/DESIGN.md --out <app-css-dir>/theme.tokens.css
   ```

**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**

## Phase 1: Execution via Micro-TDD Skill
Run `micro-tdd` for RED→GREEN→REFACTOR (Fast-Track A/B, stuck protocol, anti-regression). For HITL slices, show RED/GREEN test results (override silent mode; Fast-Track A may run silent).
1. **CLI/Subprocess:** assert on stdout/stderr, not just exit code.
2. **Requirements:** link test to requirement bare IDs from BACKLOG_MAP.md/issue (not STATUS.md) (e.g., `BT-101`).
3. **Fallbacks:** prefer native libraries (e.g. sqlite3, argparse) over third-party in mock/simple utility environments.

## Phase 2: Refactoring & Architecture Checks
Adhere to:
1. **Architecture Rules:** verify architectural structure matches `[[A-xxx]]` rules in `.memory/ARCHITECTURE.md`.
2. **Incremental Commits:** commit incrementally per TDD milestone: `<type>(BT-<slicePadded>): <summary>`.
3. **Canonical naming:** name identifiers after GLOSSARY terms; never introduce `Avoid:` synonyms.
4. **Avoid-drift check:** check changed identifiers against GLOSSARY `Avoid:` lists (whole-identifier only). Ignore third-party/library names, import paths, string literals, and comments. Propose renames (citing the canonical term + `[[G-xxx]]`) at REFACTOR/HITL gate; never auto-rename. Scope: slice diff only.

## Phase 3: Slice Completion Gate
Confirm slice against AC (inline self-check, not sub-agent). Ephemeral (no writes).
1. Read slice AC.
2. Produce an **exhaustive coverage map**: for every AC, name the passing test that covers it or mark it `[UNCOVERED]` — list each by name, never summarize as "looks complete."
3. Resolve each `[UNCOVERED]`: testable → return to the micro-tdd loop and cover it; genuinely uncoverable (e.g. design blocker) → surface it explicitly, never silently ship.
4. Done only when every AC maps to a passing test, or an `[UNCOVERED]` item is explicitly surfaced.

**Hand-off:** Run `/4a_verify-and-ship` to verify and open/update PR.