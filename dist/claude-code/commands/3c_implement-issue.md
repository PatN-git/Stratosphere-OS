---
name: 3c_implement-issue
type: workflow
description: Rigorous Test-Driven Development (TDD) cycle execution with token-efficient Fast-Tracks
---

# Implement Issues

**Purpose:** Implement deterministic vertical slices following a strict Test-Driven Development (TDD) cycle, prioritizing token efficiency and architectural integrity.

## 1. The Core TDD Protocol

Apply strictly to all backend logic, database operations, hooks, and state functions. Use `.agents\skills\code-simplifier\SKILL.md` at the end.

**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**

### Phase 1: RED (Test Specification)
1. Draft exactly one minimal test demonstrating the target behavior.
2. Link the test to relevant requirement IDs from STATUS.md or BACKLOG_MAP.md using Foam double-brackets (e.g., [[BT-101]]).
3. **Execute Test:** Run the test suite natively (e.g., npm test, vitest).  
4. **Verify Red:** Confirm the test fails. Check that the failure is exactly due to missing functionality, not syntax errors or typos. If the test passes immediately: The test is invalid. Rewrite it.

### Phase 2: GREEN (Minimal Implementation)
1. Write the absolute simplest, non-speculative code required to pass the test.
2. **Execute Test:** Run the test suite again.
3. **Verify Green:** Confirm the test passes. Ensure all existing tests remain green. If code was written prior to writing the test: Delete it. Start over. No exceptions.

### Phase 3: REFACTOR (Syntactic & Structural Polish)
1. Clean up imports, remove duplication, and optimize variable naming.
2. Verify architectural structure matches [[A-001]] and [[A-002]] inside .memory/ARCHITECTURE.md.
3. Re-run tests. Keep code perfectly green.

## 2. The Fast-Track Protocols
To prevent token-burn and protect execution speeds on repetitive or lightweight operations.

### Fast-Track A: Silent Execution
- Applicable for: Straightforward database migrations, utility logic, or minor bug fixes with pre-existing coverage.
- Workflow: 
    1. Skip writing any conversational plan or explanation in the chat. 
    2. Implement the test immediately (RED). 
    3. Write the minimal code (GREEN). 
    4. Output only the passing test output and a 1-line summary: [DONE] [[BT-xxx]] verified.

### Fast-Track B: Visual & Cosmetic Bypass
- Applicable for: Pure CSS/Tailwind changes, asset configuration, or interactive layout elements where automated assertions are fragile or costly.
- Workflow: 
    1. Bypass the automated test suite requirement. 
    2. Spin up the local dev server environment. 
    3. Visual Audit Checklist:
        - Validate colors use OKLCH tokens [[DR-002]] and spacing/type use fluid scales [[DR-003]].
        - Confirm viewport responsiveness under mobile/desktop sizes.
        - Check transition/interaction effects under click/tap inputs.
    4. Output a verified manual confirmation log detailing layout compliance.

## 3. Operational Protocols & Guardrails

### The "Stuck" Protocol (Design Alert)
- **Trigger**: If the test setup exceeds 50 lines of code, requires mocking more than 3 system dependencies, or encounters infinite testing cycles.
- **Action**: Stop immediately. Freeze implementation. Trigger the constitution ASK protocol. Present exactly two options to simplify the API design to your human partner.

### The Bug-Fix Loop (Anti-Regression)
- **Trigger**: A bug is reported in active code.
- **Action**: Write an automated regression test reproducing the exact failure state before editing any source code. Follow the standard Red-Green-Refactor loop to execute the fix.