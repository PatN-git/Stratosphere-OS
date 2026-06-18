---
name: 3d_implement-issue
description: Rigorous Test-Driven Development (TDD) cycle execution with token-efficient Fast-Tracks
type: workflow HITL
trigger: User. Do not run autonomously.
version: "2.0.0"
updated: 2026-06-18
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

## Phase 1: RED (Test Specification)
1. Draft exactly one minimal test demonstrating the target behavior.
   - **CLI/Subprocess Tests:** If testing a CLI or subprocess, assert explicitly on success path details, `stdout`, or `stderr` contents, rather than merely verifying a non-zero exit code.
2. Link the test to relevant requirement IDs from `BACKLOG_MAP.md` and the GitHub issue (NOT `STATUS.md`) using the bare ID (e.g., `BT-101`).
3. **Execute Test:** Run the test suite natively (e.g., npm test, vitest).  
4. **Verify Red:** Confirm the test fails. Check that the failure is exactly due to missing functionality, not syntax errors or typos.
   - **Characterization Carve-out:** If wrapping existing/legacy code to preserve already-correct behavior before introducing modifications, a characterization/locking test may start green to pin the baseline.
   - If the test passes immediately and this is not a characterization carve-out: The test is invalid. Rewrite it.

## Phase 2: GREEN (Minimal Implementation)
1. Write the absolute simplest, non-speculative code required to pass the test.
2. **Execute Test:** Run the test suite again.
3. **Verify Green:** Confirm the test passes. Ensure all existing tests remain green. If code was written prior to writing the test: Delete it. Start over. No exceptions.

## Phase 3: REFACTOR (Syntactic & Structural Polish)
1. Clean up imports, remove duplication, and optimize variable naming.
2. Verify architectural structure matches the project's `[[A-xxx]]` architecture rules inside `.memory/ARCHITECTURE.md`.
3. Re-run tests. Keep code perfectly green.
4. Commit incrementally per TDD milestone with `<type>(BT-<slicePadded>): <summary>` (slice's type).

## Fast-Track Protocols
To prevent token-burn and protect execution speeds on repetitive or lightweight operations.

### Fast-Track A: Silent Execution
- Applicable for: Straightforward database migrations, utility logic, or minor bug fixes with pre-existing coverage.
- Workflow: 
    1. Skip writing any conversational plan or explanation in the chat. 
    2. Implement the test immediately (RED). 
    3. Write the minimal code (GREEN). 
    4. Output only the passing test output and a 1-line summary: [DONE] BT-xxx verified.

### Fast-Track B: Visual & Cosmetic Bypass
- Applicable for: Pure CSS/Tailwind changes, asset configuration, or interactive layout elements where automated assertions are fragile or costly.
- Workflow: 
    1. Bypass the automated test suite requirement. 
    2. Spin up the local dev server environment. 
    3. Visual Audit Checklist:
        - Validate colors use OKLCH tokens [[DR-002]] and spacing/type use fluid scales [[DR-003]].
        - Confirm shadcn/ui primitives are used over raw elements ([[DR-004]]); semantic landmarks present, no generator div-soup ([[DR-006]]).
        - Confirm viewport responsiveness under mobile/desktop sizes.
        - Check transition/interaction effects under click/tap inputs.
    4. Output a verified manual confirmation log detailing layout compliance.

## Guardrails

### The "Stuck" Protocol (Design Alert)
- **Trigger**: If the test setup exceeds 50 lines of code, requires mocking more than 3 system dependencies, or encounters infinite testing cycles.
- **Action**: Stop immediately. Freeze implementation. Trigger the constitution ASK protocol. Present exactly two options to simplify the API design to your human partner.

### The Bug-Fix Loop (Anti-Regression)
- **Trigger**: A bug is reported in active code.
- **Action**: Write an automated regression test reproducing the exact failure state before editing any source code. Follow the standard Red-Green-Refactor loop to execute the fix.

### Standard Library Fallbacks
- **Preference**: When writing logic or tests for mock environments, simple utilities, or CLI spikes, favor native platform/standard libraries (e.g. `sqlite3` and `argparse`/`sys.argv` in Python, or native built-ins in Node/Go) over third-party packages. This guarantees offline capability, faster test execution, and removes setup dependency friction.