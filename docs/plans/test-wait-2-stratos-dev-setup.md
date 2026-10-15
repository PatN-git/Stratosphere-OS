---
type: plan
title: Test Wait Plan 2 - StratOS Dev Setup
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-15
version: "1.0.0"
---

# Plan 2 — StratOS: make the test suite fast and safe to run in parallel

Status: v2, 2026-10-15, revised after an Opus (high) review. Tracked as BT-182 under epic BT-181. Independent of plans 1 and 3.
Needs its own BT issue and branch (AGENTS.md §4); do NOT build on `feat/BT-179-skill-pack-lifecycle-hardening`.
Changes are to `tests/`, CI, `pytest.ini`, `scripts/` only: no bump and no `dist/` change expected (`bump_guard.py:31` watches only `src/scripts`, `src/github`, `src/external-skills.json`). If any `src/` file changes, bump once.

## Goal
Full `pytest` from ~290–420s (varies with load) to roughly 90s with the same 986 passing and no new flakes, CI meaning unchanged.

## Evidence (reviews, 2026-10-15)
- Serial: 288s (quiet), 358s (my run), 423s (under load). Trend: 158s at 525 tests, now ~330s.
- Heaviest files serial: pr_body 46–82s, bridge 63–72s, update_flow 37–61s, floor_guard 36s, dist_bundle 26s. All spawn git/Python/PowerShell/bash per test.
- xdist 3.8.0 with 6 workers: `--dist loadfile` 112–134s (the bridge file alone sets the floor near 90s); `--dist worksteal` 89s. 90s is not reachable with loadfile.
- After the races are fixed, no file shares state between its own tests (only the session-scoped `repo_root`), so per-test distribution is safe.
- No test writes into the repo or `dist/`, none uses the real HOME, no fixed temp names outside `.tmp/test_*`, no `chdir` (checked).

## Steps (each a separate commit)
1. **Baseline.** `python -m pytest -q --durations=25` once on a quiet machine; record wall time and count in `.tmp/` (not committed).
2. **Remove the in-repo build race.** `tests/lifecycle-harness/env.py:621` runs `build/build.py` in the real repo; `build.py:207` deletes the bundle (`force_rmtree(BUNDLE)`) before rebuilding, so other tests copying from `dist/` can fail or skip (`test_install_antigravity_bridge.py:54` skips if the bundle is absent). Build into a temp copy, reusing the pattern in `test_dist_bundle.py:78-87` (copies `build/` and `src/` to a temp dir and builds there). Same `_install_stratos` is used by `run-L3.py`.
   Verify: no test runs `build/build.py` in the repo root (grep `env.py`), and `dist/plugin.json` mtime is unchanged after a full run. (`git status dist/` proves nothing: the rebuild is byte-identical.)
3. **Give `test_update_flow` sandboxes unique dirs, without `tmp_path`.** `tests/runners/verify_scripts.py:194` runs the file as a plain script (`__main__` at ~`:2810` calls ~40 tests with no arguments), so a `tmp_path` fixture cannot be used. Add a helper `_sandbox(name)` returning `Path(tempfile.mkdtemp(prefix=name + '-'))`; drop the autouse deletion of `.tmp/test_*`; clean up per test in both modes (autouse fixture under pytest, the existing atexit hook under `__main__`).
   Verify: `python tests/runners/verify_scripts.py` still passes. MAX_PATH margin: LongPathsEnabled is 0 here; the longest bundle path is ~69 chars, so ~205 chars with the install prefix and an xdist `popen-gwN` level, under 260. Keep sandbox names short.
4. **Harden teardown.** `tests/lifecycle-harness/env.py:684` retries 5×0.2s and one of three parallel runs failed with "temp root survived teardown". Widen `_teardown` to ~10 attempts with exponential backoff capped near 5s.
5. **Prove parallel safety.** In a throwaway venv under `.tmp/` install `pytest-xdist` and run `python -m pytest -n 6 --dist worksteal` three times: all 986 pass each time. Fix any further race before continuing. Fall back to `--dist loadfile` only if a race exists inside a single file.
6. **Wire it.** `scripts/check.sh`: run `python -m pytest -n 6 --dist worksteal`; update its `Requires:` line (pytest-xdist). CI `build-guard.yml`: `pip install pytest pytest-xdist`, run `-n auto` (Linux runners have ~4 vCPUs). Install xdist into the interpreter `check.sh` actually uses (Store Python). `-n 0` remains the serial escape hatch; mention it in one line in `scripts/check.sh`.
7. **Re-measure.** Three full runs: 986 pass each, no flakes, wall time about 90s or less. Record before/after in `.tmp/`.

## Decision D1 (user): should `-n 6 --dist worksteal` go into `pytest.ini` addopts?
- For: a bare `python -m pytest` (what agents ran in the transcripts, including every full run) becomes fast with no skill changes.
- Against (measured): a one-file run costs 1.0s with `-n 0` vs 3–10s with `-n 6`, paid on every red/green loop; `-p no:xdist` then fails (only `-n 0` works as an escape hatch); `required_plugins` makes a bare `pytest` without xdist fail.
- Recommendation: start without addopts (step 6 only). Revisit after plan 3: if agents' full runs still call bare `pytest`, put `-n 6 --dist worksteal` in addopts and give the targeted-run loop `-n 0`. Do not add `required_plugins`.

## Optional dev-environment items (measure first; user decides; not repo changes)
- **Python build.** A Store/MSIX Python spawn costs ~305ms (6.1s for 20) vs ~110ms for git. No non-Store Python is installed; the gain is plausible but unverified. Cheapest to measure: install a non-Store Python 3.13 and time `tests/scripts/test_floor_guard.py` on both.
- **Antivirus.** Real-time protection is on; effect on the suite is unmeasured (reading exclusions needs admin). A Dev Drive with performance mode is a safer option than exclusions. This is a security setting: suggest, never change it from an agent.

## Non-goals
No `slow` marker that deselects from the default run (`floor_guard` does not see pytest `addopts`, so a deselect silently shrinks the "full" suite). No testmon. No rewriting heavy tests to avoid subprocesses unless the target is missed.

## Done when
- Three consecutive full runs: 986 passing each, ~90s or less; `python -m pytest -n 0` and `python tests/runners/verify_scripts.py` still green; `bash scripts/check.sh` green; CI green on the PR.
- Develop in `C:\Users\patri\Dev\Stratosphere-OS` only (the GDrive path is backup-only).

## Risks
- Parallel load makes the Store-Python `WinError 31` flake in floor_guard more frequent. If it survives, lower to `-n 4`. No automatic retries (they hide real failures).
