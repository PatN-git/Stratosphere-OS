---
type: research
title: "Research: Targeted Test Verification Discipline & Subagent Model Dispatch Scoping"
description: "Analysis of agent test runner hangs (bare pytest vs targeted execution), verification scoping across StratOS and downstream product repos (cleantechhub, trading), and Antigravity invoke_subagent model enum constraints."
version: "1.0.0"
generated:
  by: 3b-create-issue
  at: "2026-11-06"
---

# Targeted Test Verification Discipline & Subagent Model Dispatch Scoping

## 1. Executive Summary

During agent-driven development sessions, two recurring friction points were identified:
1. **Agent Full-Suite Test Stalls:** Agents reflexively execute bare `pytest` across the entire repository to establish a verification baseline or satisfy completion criteria, causing multi-minute hangs and timeout-driven background task escalations.
2. **Subagent Model Dispatch Mismatch:** Prompting an agent in Antigravity to dispatch a subagent using model naming variants (e.g., "4 Argon High") fails silently or is ignored because Antigravity's `invoke_subagent` tool schema enforces a strict 4-value enum: `["inherit", "flash_lite", "flash", "pro"]`.

This document records the empirical findings, architectural causes, cross-repository impact evaluation, and concrete implementation recommendations.

---

## 2. Test Execution & Verification Analysis

### 2.1 Why Did Long-Running `pytest` Sessions Occur?

Three structural factors combined to cause runaway test execution:
1. **LLM Verification Reflex:** System prompts and general model conditioning strongly instruct agents to verify changes before completing tasks. In Python repositories, models reflexively invoke `pytest` or `python -m pytest` with no file or test arguments.
2. **Single-Threaded Windows Execution:** StratOS's pre-flight test gate (`scripts/check.sh`) specifies parallel execution:
   ```bash
   python -m pytest -n 6 --dist worksteal
   ```
   When an agent runs bare `pytest`, it defaults to single-process serial execution (`-n 0`).
3. **High Volume of Filesystem/Subprocess Tests:** Even with `pytest.ini` excluding `-m integration` tests, the default suite selects **1,170 tests**. Many of these tests dynamically create temporary git repositories on disk and run nested `subprocess.run(["git", ...])` commands. On Windows, running over a thousand git subprocesses sequentially takes 5–8 minutes, triggering Antigravity's async command threshold and backgrounding the task.

### 2.2 StratOS Test Suite Design Purpose

The suite located in `tests/` is not a collection of lightweight unit helpers; it is the **formal CI and contract regression engine** for the StratOS framework:
* `tests/framework/`: Asserts architectural contracts, frontmatter schemas, migration invariants, and model ID hygiene (`test_no_vendor_model_ids.py`).
* `tests/scripts/`: Validates CLI toolchain behavior (`reconcile.py`, `floor_guard.py`, `ci_gate.py`, `pr_body.py`, `test_gate.py`, `issues.py`).
* `tests/workflows/`: Cross-checks markdown workflow procedures against Python script signatures and handoff contracts.
* `tests/lifecycle/`: Validates end-to-end multi-agent orchestration harness simulations.

**Conclusion:** The full test suite is designed for **CI (`build-guard.yml`)**, **release gates (`scripts/check.sh`)**, and **ship verification (`/4a` via `test_gate.py record --suite`)**. It is explicitly not designed for turn-by-turn interactive checks.

---

## 3. Cross-Repository Compatibility Analysis

Evaluating the proposed remedies across both StratOS itself and downstream consumer product repositories (e.g., `cleantechhub`, `trading`):

| Recommendation | StratOS Repo | Product Repos (`cleantechhub`, `trading`) | Verdict & Rationale |
|---|---|---|---|
| **Rec 1: Clarify Targeted Verification in `AGENTS.md` §5** | ✅ Highly Suitable | ✅ Highly Suitable | **Universal Win.** Mandates that in-session verification during development/research must be targeted to the modified file or test case. Full suite runs belong only to ship gates. Protects all repos from token and time waste. |
| **Rec 2: Set `addopts = -n auto` in `pytest.ini`** | ✅ Highly Suitable | ❌ Unsuitable / Risky | **StratOS-Specific Only.** Product repos may use other test runners (`vitest`, `jest`), may lack `pytest-xdist` (causing `pytest` to exit with unrecognized argument errors), or may have database/state race conditions under multi-process parallelism (e.g., SQLite file locks or transaction collisions in trading/cleantechhub). |
| **Rec 3: Reinforce Scoped Execution in `micro-tdd` & Workflows** | ✅ Highly Suitable | ✅ Highly Suitable | **Universal Win.** `micro-tdd` is runner-agnostic and explicitly emphasizes testing only the target seam during the RED-GREEN loop. Reinforcing that callers must run only the touched file prevents accidental full-suite execution across all stacks. |

---

## 4. Subagent Model Dispatch Constraints in Antigravity

### 4.1 Schema Definition

In Google Antigravity, the `invoke_subagent` tool schema specifies:
```json
"Model": {
  "type": "STRING",
  "enum": [
    "inherit",
    "flash_lite",
    "flash",
    "pro"
  ],
  "description": "'inherit' (default) uses your model. 'flash_lite' and 'flash' are lighter, faster models for simple tasks. 'pro' is a larger model for complex work."
}
```

### 4.2 Key Findings
* **No Arbitrary Model Strings:** The host rejects or drops arbitrary model identifiers (e.g., "gemini-3.8-flash", "4 Argon High", "claude-sonnet-4-6").
* **Tier Mapping:** Host-neutral tier names (such as `small` vs. default/parent) must map cleanly to the supported host enum:
  * In Claude Code: `model: haiku` or `inherit`.
  * In Antigravity: `Model: flash` (or `flash_lite`) for `small`, and `inherit` for default.
  * In Codex: TOML configuration overrides.
* **Frontmatter vs. Parameter:** In Antigravity, subagents dispatched dynamically receive their model via the `Model` argument of `invoke_subagent`.

---

## 5. Actionable Implementation Plan

1. **Update `src/constitution/AGENTS.md` (§5 Operating Principles):**
   * Add an explicit clause under **Verification**:
     > *Targeted verification only:* In-session verification during development or research must be scoped to the touched file, function, or seam (e.g., `pytest path/to/test.py::test_fn` or `npm test -- path/to/test.ts`). Never run bare `pytest` or the full test suite across the whole repository during active work; full suite runs belong strictly to the final ship gate (`4a` / `test_gate.py record --suite`) or explicit user request.
2. **Optimize StratOS `pytest.ini`:**
   * In StratOS's local `pytest.ini`, add `-n auto` to `addopts` to ensure any accidental bare `pytest` run executes concurrently across CPU cores instead of locking single-threaded on Windows.
3. **Clarify Subagent Model Tiers:**
   * Maintain `src/references/auditor-model-tiers.md` with explicit host tool parameter mapping (`invoke_subagent` `Model: flash` for `small`, `inherit` for default).
