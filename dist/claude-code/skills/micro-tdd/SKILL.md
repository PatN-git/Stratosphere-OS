---
name: Micro-TDD Execution
type: skill
description: Autonomous, token-optimized Test-Driven Development for minor fixes, isolated functions, and sub-tasks.
version: "1.0.1"
timestamp: 2026-06-17
---

# SKILL: Micro-TDD Execution

## Purpose
Execute autonomous, deterministic code modifications during hands-free (AFK) operation when macro-workflow is not explicitly active. This skill guarantees project hygiene, prevents principle drift, and strictly binds execution to automated verification while remaining extremely token-efficient.

## 1. Operating Context & Routing
- **Trigger:** Routed autonomously by Layer 2 Orchestration whenever a code change is needed for backend logic, database tables, custom hooks, utilities, or state managers.
- **Precedence:** Acts as a Layer 3 Autonomous Skill. It is strictly subordinate to Core Rules (`.agents/rules/`) and explicit User Requests, but enhances default high-level operational guidelines in `AGENT.md`.
- **Communication Protocol:** Enforces **Silent Execution Mode**. Natively suppress inner monologue, execution step narration, and line-by-line code explanations.

---

## 2. Execution Paths

### Fast-Track A: Silent Logic Cycle (Default)
Apply strictly to all pure logic, state updates, API mutations, hooks, and backend functions. Do not write production code until a failing test exists.

1. **Isolate & Specify (RED):**
   - Write exactly one minimal, target-focused unit test asserting the exact change or new capability.   
   - Run the test suite natively (`npm test`, `vitest`, `pytest`, etc.).
   - **Validate Red:** Confirm the test fails specifically due to the absence of functionality—not due to runtime compile errors or typos.
2. **Implement & Pass (GREEN):**
   - Write the absolute simplest, non-speculative production code required to satisfy the failing test.
   - Re-run the test suite.
   - **Validate Green:** Confirm the new test passes and no regression errors exist across the remaining suite.
3. **Clean Diffs (REFACTOR):**
   - Clean up code formatting using your active code simplifier protocols.
   - Output only the passing test suite results and a 1-line summary: `[DONE] [[ID]] verified.`

### Fast-Track B: Visual & Layout Bypass
Apply strictly to pure CSS/Tailwind, static asset placements, or presentation markup adjustments where automated logic assertions are fragile.

1. **Structural Shield Audit:** Verify the target component is not listed under `IMMORTAL_COMPONENTS` inside `DESIGN.md`. If shielded, halt execution immediately and notify Layer 2.
2. **Environment Execution:** Boot the local development or preview server environment.
3. **Visual Verification Matrix:** Complete a strict manual verification checklist:
   - Validate design token alignment (e.g., oklch, padding spacing scales) against layout rules.
   - Confirm cross-viewport scaling (mobile/desktop responsive breakpoints).
4. **Log Output:** Emit a concise layout compliance log specifying the layout changes verified.

---

## 3. Mandatory Safety Guardrails

### The "Stuck" Protocol (Design Alert)
- **Trigger:** If the unit test setup or mock requirement exceeds **50 lines of code**, demands mocking more than **3 system dependencies**, or generates circular failing loops.
- **Action:** Freeze execution immediately. Exit Layer 3 execution. Elevate control back to the Layer 2 Orchestrator to execute the constitutional **ASK** protocol. Present exactly two architectural options to simplify the application design or API surface area to the user.

### The Anti-Regression Bug Loop
- **Trigger:** A defect, bug, or incorrect execution behavior is caught or reported.
- **Action:** Before editing any production or application files, write a targeted regression test that explicitly reproduces the reported failure state. Verify the test is **RED** on the current codebase, then route back through **Fast-Track A** to eliminate the bug.