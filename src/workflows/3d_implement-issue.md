---
name: 3d_implement-issue
description: Rigorous Test-Driven Development (TDD) cycle execution with token-efficient Fast-Tracks
type: workflow HITL
trigger: User. Do not run autonomously.
version: "2.0.3"
timestamp: 2026-06-23
---

# Implement issue

**Purpose:** Implement deterministic vertical slices following a strict Test-Driven Development (TDD) cycle, prioritizing token efficiency and architectural integrity.

Apply strictly to all backend logic, database operations, hooks, and state functions. Use `.agents/skills/code-simplifier/SKILL.md` at the end.

## Phase 0: Branch & Context Intake
1. **Branch Isolation (per AGENT.md §4):** Resolve the slice's PARENT feature BT (from the slice issue's parent link or BACKLOG Dependencies).
   - Feature branch format: `<type>/BT-<parentPadded>-<slug>` (use `type:` from the PARENT feature). If it exists → check it out and pull; else → create it from up-to-date default.
   - If the slice has no resolvable parent → use its own ID; if genuinely ambiguous → INTERACTIVE prompt to clarify (if AFK, default to the slice's own branch).
   - Never work on `main`.
   - Update `.memory/STATUS.md` `Current Branch`.
2. Read the current slice issue description. Check if a design reference is linked in the GitHub Issue body or in the `Ref` column of `.memory/BACKLOG_MAP.md`.
3. **Conditional Read:** If a UX design blueprint is referenced (e.g., `docs/design/BT-<padded>-interface.md`), you MUST load and read:
   - The frozen blueprint: `docs/design/BT-<padded>-interface.md` (search for the section relevant to the current slice).
   - The brand design tokens: `.memory/DESIGN.md`.
   - The design rules: `.memory/DESIGN_RULES.md` (specifically §3 Immortal Components).
   - **UI Slices Read Rule:** UI slices must implement design based *only* on these frozen repository artifacts using Fast-Track B (visual audit). Never access or re-read live Stitch.
   - **Translation Rule:** the blueprint's layout hierarchy (and any Stitch HTML) is a layout REFERENCE, not copy-source. Re-express it in shadcn/ui ([[DR-004]]) + semantic HTML ([[DR-006]]), binding values to `DESIGN.md` tokens ([[DR-002]]/[[DR-003]]). See `.agents/workflows/.reference/shadcn-build-guide.md`.
4. If no design reference exists (such as for pure backend logic, migrations, or utility functions), proceed immediately to Phase 1 without blocking or waiting for user input.

**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**

## Phase 1: Execution via Micro-TDD Skill

Run the `micro-tdd` skill to execute the RED→GREEN→REFACTOR loop, its Fast-Track A/B paths, the "Stuck" Protocol, and the Anti-Regression loop. **For HITL slices, surface each cycle's RED and GREEN test results** (override `micro-tdd`'s Silent Execution Mode); Fast-Track A may run silent.

Apply the following slice-specific guidance when designing and writing tests/implementation:
1. **CLI/Subprocess Tests:** If testing a CLI or subprocess, assert explicitly on success path details, `stdout`, or `stderr` contents, rather than merely verifying a non-zero exit code.
2. **Requirement-ID Linking:** Link the test to relevant requirement IDs from `BACKLOG_MAP.md` and the GitHub issue (NOT `STATUS.md`) using the bare ID (e.g., `BT-101`).
3. **Standard Library Fallbacks:** When writing logic or tests for mock environments, simple utilities, or CLI spikes, favor native platform/standard libraries (e.g. `sqlite3` and `argparse`/`sys.argv` in Python, or native built-ins in Node/Go) over third-party packages. This guarantees offline capability, faster test execution, and removes setup dependency friction.

## Phase 2: Refactoring & Architecture Checks

When refactoring in the loop, adhere to:
1. **Architecture Rules:** Verify architectural structure matches the project's `[[A-xxx]]` architecture rules inside `.memory/ARCHITECTURE.md`.
2. **Incremental Commits:** Commit incrementally per TDD milestone with the format `<type>(BT-<slicePadded>): <summary>` (where `<type>` is the slice's type label).
3. **Canonical naming (leading word):** name new/changed identifiers after the applicable GLOSSARY term; never introduce a listed `Avoid:` synonym.
4. **Avoid-drift check (propose-only):** check the identifiers THIS SLICE introduced or modified against GLOSSARY `Avoid:` lists (only terms that have one). Use judgment — flag a match only when the banned word is used as the domain concept the glossary canonicalized; ignore third-party/library names, import paths, string literals, and comments; match on whole-identifier boundaries. Propose any renames (citing the canonical term + `[[G-xxx]]`) at the REFACTOR/HITL gate; never auto-rename. Scope is this slice's diff only — never the whole repo.

**Hand-off:** Slice implemented and committed. Run `/4a_verify-and-ship` to verify against acceptance criteria and open/update the feature PR.