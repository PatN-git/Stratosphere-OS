---
type: plan
title: BT-247 (Slice S5 of BT-242) Phase 5A Handover & Phase 5B Integration Guide
generated:
  by: antigravity session (BT-247 Phase 5A HITL)
  at: 2026-11-09
version: "1.0.0"
---

# BT-247 (Slice S5 of BT-242) Phase 5A Handover & Phase 5B Integration Guide

## 1. Executive Summary

This document serves as the formal handover for **BT-247 (Unified Python CLI Façade for tracker operations)** upon the successful completion and verification of **Phase 5A**. 

In accordance with [bt242_v5_1_execution_plan.md](file:///C:/Users/patri/.gemini/antigravity/brain/89eae076-d827-4781-814f-91fd1cb2daad/bt242_v5_1_execution_plan.md) §1 D3 and §4, Phase 5A was developed in parallel HITL isolation with **zero file overlap** with Waves 1–3 on `improvement/BT-242-v5-1-follow-ups`.

- **Current Branch:** `unified_python_cli_facade` (branched from `main` @ `3eff7ba`)
- **Phase 5A Artifacts:**
  1. `src/scripts/tracker.py` (390 lines, $\le 400$ lines limit per `[[A-003]]`, stdlib only)
  2. `tests/scripts/test_tracker_equivalence.py` (740 lines, 7/7 tests passed green)
- **Status:** Phase 5A is 100% verified green. Paused for Main Orchestrator integration in **Wave 4A**.

---

## 2. Phase 5A Verification Results

### 2.1 Equivalence Test Suite (`tests/scripts/test_tracker_equivalence.py`)
Run command: `python -m pytest -n 0 tests/scripts/test_tracker_equivalence.py`
Status: **7 passed in 110.29s**

| Layer | Test Name | Invariant / Parity Verified |
|:---|:---|:---|
| **Layer 1** | `test_layer1_github_equivalence` | 1-to-1 parity between legacy raw `gh` commands and `tracker.py` across all 16 verbs and 7 reads against `gh_shim.py` JSON store. Identical store JSON state, exit codes, and stdout. |
| **Layer 1** | `test_layer1_local_equivalence` | 1-to-1 parity between legacy `issues.py` commands and `tracker.py` across all 16 verbs and 7 reads against git `refs/heads/<repo>/issues` branch. Identical commit tree and diffs. |
| **Layer 2** | `test_layer2_single_status_invariant_github` | Mutually exclusive status labels on GitHub: transitions remove previous `status:*` before adding the new one. |
| **Layer 2** | `test_layer2_single_status_invariant_local` | Mutually exclusive `status:` field in markdown frontmatter on local issue store. |
| **Layer 2** | `test_layer2_a005_retry_halt_contract` | Under `GH_SHIM_FAIL=1`, `tracker.py` retries 3 times with exponential backoff, exits non-zero, and creates 0 fallback files. |
| **Layer 3** | `test_layer3_downstream_gate_compatibility_github` | Downstream verification passes identically on state produced by `tracker.py`: `reconcile.py --ids ... --expect ... --with-edges ...` and `ice_read.py candidates`. |
| **Layer 3** | `test_layer3_downstream_gate_compatibility_local` | Downstream verification passes identically on local store produced by `tracker.py`: `reconcile.py` and `ice_read.py candidates`. |

### 2.2 Regression Suites
Run command: `python -m pytest -n 0 tests/framework/test_tracker_verbs.py tests/scripts/test_tracker_switch.py`
Status: **59 passed in 168.38s** (0 regressions).

---

## 3. CLI Façade Specification (`src/scripts/tracker.py`)

`tracker.py` dynamically resolves the active backend (`tracker: github` or `tracker: local`) from `.memory/ARCHITECTURE.md` using `reconcile.read_tracker`. It accepts both kebab-case (`set-status`) and snake_case (`set_status`) command names.

### Verbs (Mutations)
```bash
# Issue Lifecycle
python src/scripts/tracker.py create --title "<t>" [--body "<b>"] [--label <l>]... [--milestone <m>] [--parent <p>]
python src/scripts/tracker.py close <id> [--reason <completed|not_planned>]
python src/scripts/tracker.py reopen <id>
python src/scripts/tracker.py claim <id> [--assignee <a>]

# Status & Labels
python src/scripts/tracker.py set-status <id> <status>
python src/scripts/tracker.py set-labels <id> [--add <l>]... [--remove <l>]...
python src/scripts/tracker.py ensure-label <name> [--color <c>] [--description <d>]
python src/scripts/tracker.py set-milestone <id> <milestone>
python src/scripts/tracker.py ensure-milestone <title>
python src/scripts/tracker.py close-milestone <title>

# Relationships & Content
python src/scripts/tracker.py set-parent <id> <parent_id>
python src/scripts/tracker.py add-blocker <id> <blocker_id>
python src/scripts/tracker.py clear-blocker <id> <blocker_id>
python src/scripts/tracker.py comment <id> "<body>"
python src/scripts/tracker.py set-refs <id> <ref>...
python src/scripts/tracker.py set-body <id> "<body>"
```

### Reads (Queries)
```bash
python src/scripts/tracker.py get <id> [--json]
python src/scripts/tracker.py list [--state <open|closed|all>] [--label <l>] [--milestone <m>] [--json]
python src/scripts/tracker.py wip [--json]
python src/scripts/tracker.py resume-note <id>
python src/scripts/tracker.py candidates [--milestone <m>] [--json]
python src/scripts/tracker.py children <id> [--json]
python src/scripts/tracker.py blockers <id> [--json]
```

---

## 4. Phase 5B Execution Plan (Wave 4A Integration)

Once Waves 1–3 (`BT-257`, `BT-251`, `BT-245`, `BT-243`, `BT-244`, `BT-252`) are completed and Gate 3 is committed on `improvement/BT-242-v5-1-follow-ups`, execute Wave 4A in the main session as follows:

### Step 1: Merge Phase 5A
```bash
git checkout improvement/BT-242-v5-1-follow-ups
git merge unified_python_cli_facade --no-edit
```

### Step 2: Wire `tracker.py` into Project Scaffolding & Verification
1. **`src/scripts/scaffold.py:634`**:
   Add `"tracker.py"` to `get_bundled_project_scripts`:
   ```python
   def get_bundled_project_scripts() -> tuple[str, ...]:
       return (
           ...,
           "tracker.py",
       )
   ```
2. **`tests/runners/verify_scripts.py:211`**:
   Add mapping for `scripts/tracker.py`:
   ```python
   elif rel_str == "scripts/tracker.py":
       proj_rel_path = ".agents/scripts/tracker.py"
   ```
3. **`tests/lifecycle/test_l3_seed.py` & `test_l3_assertions.py`**:
   Add `"tracker.py"` to the `SCRIPTS` tuple.

### Step 3: Workflow Cutover
Replace raw backend calls in citing workflows/commands (`src/workflows/*.md` and `src/commands/stratosphere-update/SKILL.md`) with `python src/scripts/tracker.py <verb> ...` (or `.agents/scripts/tracker.py <verb> ...` for consumer projects).

### Step 4: Update `build/build.py`
In `build/build.py`:
- Stop copying `tracker-verbs-github.md`, `tracker-verbs-local.md`, and `github-issue-relations.md` into the 14 skills.
- Consumer updates via `scaffold.py:1153-1205` will automatically detect these 42 pruned paths as orphans and clean them up during `/stratosphere-update`.

### Step 5: Test Alignment & Floor Guard (`MF-6`)
Update assertions in `tests/framework/test_tracker_verbs.py`, `tests/framework/test_contract_s6.py`, and `tests/framework/test_scoped_readers.py` in-place to assert `.agents/scripts/tracker.py` while ensuring net assertion count $\ge 0$ (protecting `floor_guard.py:161` `[tests-removed]`).

### Step 6: Build & Verification Gate
```bash
python build/build.py
python src/scripts/floor_guard.py
python .agents/scripts/test_gate.py record -- python -m pytest tests/scripts/test_tracker_equivalence.py tests/framework/test_tracker_verbs.py tests/scripts/test_tracker_switch.py
git commit -m "improvement(BT-247): unified python cli facade (tracker.py cutover)"
```

Proceed immediately to **Wave 4B** (`4a ship-only` sequential loop across all 7 slices).
