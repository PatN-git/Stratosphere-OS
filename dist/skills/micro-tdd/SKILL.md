---
name: micro-tdd
description: Routes each code change to its cheapest safe path (direct edit, visual check, or test-first RED→GREEN→REFACTOR); localizes unclear bugs before fixing. Use for any code change or bug fix; 3d delegates its loop here.
metadata:
  stratos.layer: execution
version: "1.4.0"
timestamp: 2026-10-08
---

# SKILL: Micro-TDD Execution

## Purpose
Code changes bound to observed verification at lowest token cost. Standalone, or a lifecycle workflow's loop; a caller owning plan, full suite and coverage keeps them.

## 1. Operating Context
- **Precedence:** Layer 3 Autonomous Skill; subordinate to Core Rules (`.agents/rules/`) and User Requests.
- **Silent Execution Mode:** no monologue, step narration, or line-by-line explanation.

## 2. Route
Classify each change before editing; first matching row wins; log route in one line.

| Route | Signal | Path |
|---|---|---|
| **Risk** | Touches security/RLS, auth, billing/entitlements, core math/algorithms, data migrations, or a caller-marked risky path | Fast-Track A, even one-line edits |
| **Direct** | No runtime behavior change: docs, comments, copy/log text, formatting, tool-driven rename, dead-code removal, test-only edit, config value, dependency bump | Edit → related tests + type-check/lint → `[DONE] direct` |
| **Visual** | Pure CSS, static assets, presentation markup | Fast-Track B |
| **Bug** | Defect caught or reported | Anti-Regression Bug Loop (§4) |
| **Logic** | Any other behavior change | Fast-Track A |

Direct guard: edit changes code deciding a branch, return value or computation → it is not Direct. Changing only a constant's or config value is Direct unless the Risk row applies. Unsure → Logic.

## 3. Execution Paths

### Fast-Track A: Silent Logic Cycle
Logic and Risk routes. No production code before a failing test.

0. **Declare Seam:**
   - Name the seam asserted (function/module/contract under test); HITL: surface for confirmation; AFK: log in one line. Assert behavior at the seam, never below (implementation detail).
1. **Isolate & Specify (RED):**
   - Name the break first: the production change this test catches. Write one minimal unit test per cycle asserting the change or new capability; each boundary (e.g. both sides of a threshold) gets its own cycle. Expected values from an independent source (literal, spec, worked example), never recomputed the way the code computes them. Never write a test that only asserts a constant equals its new value: test behavior that reads it; nothing reads it → nothing to test, finish on Direct.
   - Run target test file; type-check during the loop.
   - **Validate Red:** Confirm the test fails specifically due to the absence of functionality—not due to runtime compile errors or typos. **Record the observed RED** — the failing assertion + that it failed for absent functionality; the RED must be an observed result, never assumed. In silent/AFK mode, surface it to the caller as `red_confirmed` rather than narrating.
     - **Characterization Carve-out:** test pinning already-correct legacy behavior before modification may start green.
     - Otherwise a test passing immediately is invalid → rewrite. Bug route: assumed cause is wrong → localize (Bug Loop step 2).
2. **Implement & Pass (GREEN):**
   - Simplest non-speculative production code that passes the test.
   - **Validate Green:** re-run target test file; confirm pass.
3. **Clean Diffs & Verify (REFACTOR):**
   - Simplify and format the diff.
   - Run the tests **related to the changed files** using the runner's related/changed mode (e.g. `vitest related <files> --run`, `jest --findRelatedTests <files>`, `pytest` with `testmon`). With no such mode, run the touched test files. When the caller owns the full suite, stop here; otherwise (standalone use) run the full suite **once** at the end of the task.
   - Output only the passing test suite results and a 1-line summary: `[DONE] [[ID]] verified.`

### Fast-Track B: Visual & Layout Bypass
Visual route, where automated logic assertions are fragile.

1. **Structural Shield Audit:** Verify the target component is not listed under `IMMORTAL_COMPONENTS` inside `DESIGN.md`. If shielded, halt execution immediately and notify Layer 2.
2. **Environment Execution:** Boot the local development or preview server environment.
3. **Visual Verification Matrix:** Complete a strict manual verification checklist:
   - Validate design token alignment (e.g., oklch, padding spacing scales) against layout rules.
   - Confirm cross-viewport scaling (mobile/desktop responsive breakpoints).
4. **Log Output:** Emit a concise layout compliance log specifying the layout changes verified.

---

## 4. Mandatory Safety Guardrails

### The "Stuck" Protocol (Design Alert)
- **Trigger:** test setup or mocks > **50 lines of code**, > **3 mocked system dependencies**, **3 failed GREEN attempts** on one test (attempt = production edit + red run), or no red-capable command reachable on the Bug route.
- **Action:** Freeze; no further edits. Prepare exactly two architectural options simplifying design or API surface. User present → Layer 2 constitutional **ASK** protocol with them. AFK → return `stuck: {reason, options}` to caller; stop.

### The Anti-Regression Bug Loop
- **Trigger:** Bug route.
1. **Cause evident** (stack trace, failing test or recent diff names it): before editing production files, write a regression test reproducing the failure, confirm **RED** on current code, fix via **Fast-Track A**.
2. **Cause unclear, or the repro passes:** localize before fixing.
   - One red-capable command showing the failure; no hypothesis before it has run.
   - 2–5 falsifiable hypotheses naming a file, function, config or input, each with the observation that rules it out.
   - Run the cheapest observation separating survivors; drop falsified; repeat until one has direct evidence. Among fitting survivors, prefer fewest unsupported assumptions.
   - Tag temporary instrumentation `[DEBUG-<id>]`; grep-remove every tag before GREEN.
   - Then step 1 with the localized cause.
3. **Regression proof:** after GREEN, revert the fix only via git (`git stash push -- <fix files>`) → test fails; restore (`git stash pop`) → green. Never copy files outside the repo.
