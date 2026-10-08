---
name: micro-tdd
description: Routes each code change to its cheapest safe path (direct edit, visual check, or test-first RED→GREEN→REFACTOR) and localizes unclear bugs before fixing. Use for any code change or bug fix; 3d delegates its loop here.
metadata:
  stratos.layer: execution
version: "1.4.0"
timestamp: 2026-10-07
---

# SKILL: Micro-TDD Execution

## Purpose
Code changes bound to observed verification at lowest token cost. Runs standalone or as a lifecycle workflow's loop; a caller owning plan, full suite, and coverage keeps them.

## 1. Operating Context
- **Precedence:** Layer 3 Autonomous Skill, subordinate to Core Rules (`.agents/rules/`) and User Requests.
- **Silent Execution Mode:** no inner monologue, step narration, or line-by-line code explanations.

## 2. Route
Classify each change before editing; first matching row wins. Log the route in one line.

| Route | Signal | Path |
|---|---|---|
| **Risk** | Touches security/RLS, auth, billing/entitlements, core math/algorithms, data migrations, or a path the caller marks risky | Fast-Track A, even for a one-line edit |
| **Direct** | No runtime behavior change: docs, comments, copy/log text, formatting, tool-driven rename, dead-code removal, test-only edit, config value, dependency bump | Edit; run related tests + type-check/lint; output `[DONE] direct` |
| **Visual** | Pure CSS, static assets, presentation markup | Fast-Track B |
| **Bug** | Defect caught or reported | Anti-Regression Bug Loop (§4) |
| **Logic** | Any other behavior change | Fast-Track A |

Direct guard: if the edit changes code that decides a branch taken, a return value, or a computation, it is not Direct. Changing only a constant's or config value is Direct unless the Risk row applies. Unsure → Logic.

## 3. Execution Paths

### Fast-Track A: Silent Logic Cycle
Logic and Risk routes. No production code until a failing test exists.

0. **Declare Seam:**
   - Name the seam being asserted (function/module/contract under test). HITL: surface it for confirmation; AFK: log it in one line. Assert behavior at the seam, never below it (implementation detail).
1. **Isolate & Specify (RED):**
   - Name the break first: the production change this test would catch. Write exactly one minimal unit test per cycle asserting the change or new capability; each boundary (e.g. both sides of a threshold) gets its own cycle. Expected values come from an independent source (literal, spec, worked example), never recomputed the way the code computes them. Never write a test that only asserts a constant equals its new value: test the behavior that reads it; if no code reads it, there is nothing to test, so finish on the Direct path.
   - Run the target test file; type-check during the loop.
   - **Validate Red:** Confirm the test fails specifically due to the absence of functionality—not due to runtime compile errors or typos. **Record the observed RED** — the failing assertion + that it failed for absent functionality; the RED must be an observed result, never assumed. In silent/AFK mode, surface it to the caller as `red_confirmed` rather than narrating.
     - **Characterization Carve-out:** a characterization test pinning already-correct legacy behavior before modification may start green.
     - Otherwise a test passing immediately is invalid — rewrite it. On the Bug route it means the assumed cause is wrong — localize (Bug Loop step 2).
2. **Implement & Pass (GREEN):**
   - Write the simplest non-speculative production code that passes the test.
   - **Validate Green:** re-run the target test file; confirm it passes.
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
- **Trigger:** test setup or mocks exceed **50 lines of code**, mocking more than **3 system dependencies**, **3 failed GREEN attempts** on the same test (attempt = production edit + red run), or no red-capable command reachable on the Bug route.
- **Action:** Freeze; no further edits. Prepare exactly two architectural options to simplify the design or API surface. User present: elevate to Layer 2 for the constitutional **ASK** protocol with them. AFK: return `stuck: {reason, options}` to the caller and stop.

### The Anti-Regression Bug Loop
- **Trigger:** Bug route.
1. **Cause evident** (stack trace, failing test, or recent diff names it): before editing production files, write a regression test reproducing the failure, confirm **RED** on the current code, then fix via **Fast-Track A**.
2. **Cause unclear, or the repro passes:** localize before fixing.
   - Get one red-capable command showing the failure; no hypothesis before it has run.
   - List 2–5 falsifiable hypotheses naming a file, function, config, or input, each with the observation that rules it out.
   - Run the cheapest observation that best separates survivors; drop falsified ones; repeat until one has direct evidence. Among survivors that fit, prefer fewest unsupported assumptions.
   - Tag temporary instrumentation `[DEBUG-<id>]`; grep-remove every tag before GREEN.
   - Then step 1 with the localized cause.
3. **Regression proof:** after GREEN, revert the fix only with git (`git stash push -- <fix files>`), confirm the test fails, restore (`git stash pop`), confirm green. Never copy files outside the repo.
