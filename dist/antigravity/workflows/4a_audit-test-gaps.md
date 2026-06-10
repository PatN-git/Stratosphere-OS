---
name: 4a_audit-test-gaps
description: Validates that test suites match business requirements, acceptance criteria, and security boundaries.
type: workflow HITL
trigger: User. Do not run autonomously.
---

# PHASE 1: VALUE-ADD GATE
_INPUT:_ GitHub Issue/PRD. ACTION: Evaluate risk profile of target issue before spending execution tokens.
_ACTION:_ Evaluate whether target issue is high-risk enough to justify a focused test-alignment audit.
1. IF the task is a pure UI/cosmetic change, standard layout tweak, CSS/Tailwind adjustment, basic view rendering, copy change, or simple visual polish with no underlying data/logic invariants → HALT immediately.
    - OUTPUT: `[SKIP] Pure UI/cosmetic task with no logical or security invariants. Audit bypassed to save tokens.`
2. IF the task touches any of the following -> PROCEED to Phase 2:
  - Supabase RLS policies
  - User authentication or authorization
  - Billing, payments, credits, limits, or entitlements
  - Core business math, calculations, algorithms, or ranking logic
  - Security boundaries between users, tenants, teams, or roles
  - Explicit PRD acceptance criteria with meaningful edge cases
  - A `[size:large]` `[type:AFK]`

# PHASE 2: EXECUTION
_INPUT:_
- GitHub Issue/PRD + the frozen design doc (`docs/design/BT-<padded>-interface.md`)
- New/modified test files
- relevant implementation files when needed to understand what the tests verify 
- `.memory/LEARNINGS.md`.

_PERSONA:_ Strict Business Logic Auditor. Focus exclusively on requirements and security boundaries. Ignore syntax, formatting, and stylistic preferences.

## Confidence scale & reporting threshold
Confidence is not certainty alone. It is the combined score for:

1. **Evidence strength** — Is the gap directly visible in the PRD, GitHub Issue, tests, or `.memory/LEARNINGS.md`?
2. **Scope relevance** — Is it about stated requirements, acceptance criteria, business logic, security boundaries, Supabase RLS, auth, billing, or specified edge cases?
3. **Practical impact** — Would this likely allow a requirement gap, security bypass, incorrect business behavior, or false sense of test coverage in normal use?
4. **Actionability** — Can a developer reasonably add or change a test to close the gap?

- **Implementation-only Divergence Rule:** Any implementation-only divergence (where the code does something different from design/primitives but does NOT violate any stated PRD Acceptance Criteria or Design Contract) MUST cap at [Weak Signal] (confidence < 70) and is withheld from the final report.

Assign a confidence score from 0–100 using these anchors:
- **0–39: Discard**
  - Speculative, stylistic, pre-existing, unrelated to requirements/security, or unsupported by direct evidence.
  - Do not mention in output.
- **40–69: Weak Signal**
  - Possibly valid, but evidence is incomplete, impact is low, or it depends on assumptions not stated in the PRD / Issue / tests.
  - Do not report unless explicitly asked for exploratory findings.
- **70–79: Near Miss**
  - Likely valid and relevant, but missing direct evidence, clear impact, or immediate actionability.
  - Do not report in final output. Use internally only.
- **80–89: Report**
  - Strong evidence of a missing assertion, untested stated requirement, unhandled specified edge case, or likely security/business-logic test gap.
  - Include in final output.
- **90–100: Critical / Confirmed**
  - Directly proven mismatch between stated acceptance criteria/security boundary and test coverage.
  - Likely to cause repeated, serious, or production-impacting failure if left untested.
  - Include in final output.

## Clean Exit Rule
- IF no architectural issues meet the **confidence >= 80** threshold -> HALT execution.
- OUTPUT: `[PASS] No high-confidence logical or security anomalies identified. Slice is verified.` 
Do not generate additional output.

# PHASE 3: Output
IF issues **confidence >= 80** exist, output only compact, dense markdown table mapping PRD Acceptance Criteria (AC) directly to tests:

| AC / Requirement | Test Target | Status | Confidence | Gap / Security Risk |
|---|---|---:|---:|---|
| [1-line AC or requirement description] | [test_name] or [NONE] | FAIL | [80-100] | [Missing assertion, untested edge case, business logic gap, or security boundary risk] |

*(Optional Footnote)* If sub-threshold findings (40-79) were identified and withheld, append: *"Note: <N> sub-threshold findings were withheld from this report."*

# PHASE 4: HANDOFF
HALT execution. Await human instruction:
- Human commands agent back to standard TDD loop to implement missing test coverage, OR approves and proceeds to merge.