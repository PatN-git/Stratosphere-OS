---
type: plan
title: L3 — Automated Lifecycle E2E Harness
description: Drive the full StratOS lifecycle (0a→4a→0b) end-to-end in a throwaway environment with no human interaction, asserting on artifacts rather than prose.
version: "1.0.0"
generated:
  by: Claude Opus 5
  at: 2026-09-15
---

# L3 — Automated Lifecycle E2E Harness

Execution plan. 8 slices.

## 1. Contract

One command runs the entire StratOS lifecycle against a throwaway project and exits
non-zero on any gate failure, with **no human interaction and no residue**:

```bash
python tests/lifecycle-harness/run-L3.py            # shimmed lane (CI, deterministic)
python tests/lifecycle-harness/run-L3.py --live-gh  # real throwaway GitHub repo
```

At exit: temp `HOME` removed, temp project removed, any created GitHub repo deleted,
the developer's real `~/.claude`, `~/.gemini`, `~/.config/devin` and working repo untouched.

## 2. Facts

Verified in this repo on 2026-09-15. **Do not re-derive.**

1. **L3 is the gap.** `tests/install-harness/README.md` documents L1 (install paths, no
   agent), L2 (agentic install via headless `claude -p`), L4 (manual). All three cover
   **onboarding**. Nothing drives the **lifecycle** — 0a→1b→2a→3b→3d→4a→0b.
2. **The driver pattern already exists.** `run-L2.py` spawns `claude -p` with
   `--dangerously-skip-permissions`, a temp `HOME`, a pre-written prompt file, and a
   **sentinel string** the agent must print. Assertions key off the sentinel plus
   on-disk artifacts, never on prose. Reuse it; do not invent a second pattern.
3. **A simulation precedent exists** — `tests/test_3z_orchestrator_simulation.py` models
   the `3z-afk-loop` state machine without invoking an agent. It covers orchestration
   logic; it does not exercise real skills.
4. **Lifecycle skills are deliberately not model-invocable**: `disable-model-invocation:
   true` + `triggers: ["user"]` + a Codex sidecar. A harness invoking `/0a-start-session`
   **is** the user, so this is not an obstacle — but nothing may rely on a *model*
   deciding to fire one.
5. **Several skills spawn their own subagents**: `4a` (2 auditors), `3b` (Slice Draft
   Auditor), `1a`, `3a`, `4c` (3 in parallel). The harness must tolerate nesting and must
   not assume one agent process per phase.
6. **GitHub is load-bearing mid-flow.** `3b` creates issues, `3c` creates milestones,
   `4a` opens the PR, and `reconcile.py` enforces a `[MIRROR-OK]` terminal-sync gate
   against `gh api graphql`.
7. **`4a` exposes named gates** — `audit-only` (Phases 1–4) and `ship-only` (Phase 5) —
   so the harness can stop before any push.
8. **Workflows never merge** (AGENTS.md §4). A PR may be opened; merging is out of scope
   for any automated run.

## 3. Invariants

- **E1.** Never touch the real `~/.claude`, `~/.gemini`, `~/.config/devin`, or the working
  repo. Redirect `HOME`/`USERPROFILE` per run, as L1 and L2 already do.
- **E2.** **Teardown is guaranteed**, including on failure and on SIGINT. A run that
  cannot guarantee teardown must refuse to start.
- **E3.** Assert on **artifacts and structure**, never on agent prose. Agent wording
  varies between runs and models; file existence, frontmatter shape, and sentinels do not.
- **E4.** Default lane is **shimmed and offline**. `--live-gh` is opt-in and never runs in
  the default CI job.
- **E5.** The harness **never merges** and never pushes to `main` (fact 8).
- **E6.** No prompt may ever block. Every HITL gate gets a pre-written answer; a gate with
  no scripted answer is a harness bug, not a pass.

## 4. Why a shim is the default lane

A real repo per run costs API calls, needs a token with repo-delete scope, leaves residue
when a run is killed, and makes CI flaky on GitHub outages. A `gh` shim on `PATH` returning
canned JSON makes the default lane deterministic, offline, and free.

The shim is not a substitute for reality, so `--live-gh` exists and should run on a
schedule, not per PR. Keep the shim honest: it replays **recorded** `gh` responses
captured from a real run, refreshed whenever a skill changes its `gh` usage.

---

## Slice 1 — Harness skeleton and isolation

`tests/lifecycle-harness/run-L3.py`, mirroring `run-L2.py`'s structure.

- Temp `HOME`/`USERPROFILE`, temp project dir, temp `PATH` prefix for shims.
- `try/finally` teardown plus a `SIGINT`/`SIGTERM` handler; refuse to start if the temp
  root cannot be created under the OS temp dir (E2).
- `--keep` to retain the project on failure for debugging, printing its path. Never the
  default.

**DONE WHEN:** a no-op run creates and removes its environment, and `~/.claude`,
`~/.gemini` and the working repo are byte-identical before and after.

## Slice 2 — The `gh` shim

`tests/lifecycle-harness/shims/gh` (+ `.cmd`), first on `PATH`.

- Dispatch on argv: `issue create|edit|view|list`, `pr create|view`, `api graphql`,
  `release view`, `auth status`.
- Back it with a JSON fixture store; mint monotonic issue numbers so `BT-<padded>` IDs are
  stable across a run.
- **Record mode** (`--record`, used with `--live-gh`) captures real responses into the
  fixture store, so the shim is refreshed from reality rather than hand-written.
- Unknown subcommand → exit non-zero with a loud message. A silently-succeeding shim would
  make every downstream assertion meaningless.

**DONE WHEN:** `3b` completes against the shim and the fixture store contains every
`gh` invocation it made.

## Slice 3 — Scripted gate answers

`tests/lifecycle-harness/prompts/<phase>.txt`, one per lifecycle gate, following L2's
pre-answered-prompt convention.

Each carries: the invocation (`/0a-start-session`), the scripted answers for that skill's
HALT/ASK points, and a unique sentinel to print on success.

**DONE WHEN:** every gate in the phases under test has a scripted answer; an unanswered
gate fails the run with the gate's name (E6).

## Slice 4 — Phase driver and artifact assertions

For each phase: launch `claude -p` with the phase prompt, wait for its sentinel, then
assert on disk.

| Phase | Asserted artifacts |
|:---|:---|
| `0a-start-session` | `.memory/STATUS.md` updated; branch restored or created |
| `1b-concept-framing` | `docs/discovery/<slug>.md` exists; `type: discovery-brief`; `generated.by` = the skill; `status` in the routing vocab |
| `2a-write-prd` | `docs/prds/BT-*.md`; `type: prd`; `status: stable`; no duplicate `type:` key |
| `3b-create-issue` | issues minted in the fixture store; `BACKLOG_MAP.md` row per slice; `generated.at` refreshed |
| `3d-implement-issue` | a feature branch exists; a commit per slice; tests green in the fixture project |
| `4a-verify-and-ship` | `audit-only` produces a coverage verdict and **no** branch/PR mutation |
| `0b-stop-session` | `LEARNINGS.md`/`GLOSSARY.md` entries; `verified` appended on promotion; memory lint clean |

Every artifact is additionally validated by the existing gates: `validate_memory.py` and
the spec checks in `tests/test_skill_conformance.py`.

**DONE WHEN:** each phase asserts at least one artifact and one frontmatter invariant, and
no assertion inspects agent prose (E3).

## Slice 5 — Subagent tolerance

Phases that spawn subagents (fact 5) must not be assumed single-process.

- Per-phase timeouts scaled to subagent count; a timeout reports **which phase**, not a
  bare expiry.
- Capture nested output to `<temp>/logs/<phase>.log` and print the tail on failure.
- Assert the nested guardrails actually held: after `4a audit-only`, no commit, no push,
  no PR — the subagent contract is that it reports only.

**DONE WHEN:** `4a`'s two auditors and `3b`'s Slice Draft Auditor complete, and a
deliberately broken guardrail (a subagent that writes a file) fails the run.

## Slice 6 — The `--live-gh` lane

- Create `stratos-l3-<run-id>` via `gh repo create --private`, delete in teardown.
- Preflight: refuse to start unless `gh auth status` shows `delete_repo` scope, so a run
  can never leave an orphan.
- Registered atexit **and** signal handler; on teardown failure, print the exact
  `gh repo delete` command rather than failing silently.
- Stops at `audit-only`. Never runs `ship-only`, never merges (E5, fact 8).

**DONE WHEN:** a live run creates, exercises and deletes its repo; a killed run leaves no
repo behind; `gh repo list` is unchanged before and after.

## Slice 7 — CI wiring

- Default lane in `build-guard.yml`, behind the existing `pytest` step, gated on `claude`
  being available — skip with a clear message when it is not, never a silent pass.
- `--live-gh` on a nightly schedule, not per PR (E4).
- Publish `<temp>/logs/` as an artifact on failure.

**DONE WHEN:** a PR runs the shimmed lane; the nightly runs the live lane; a failure
uploads logs.

## Slice 8 — Document L3

Extend `tests/install-harness/README.md`'s layer table with L3, or split the harness docs
if the directory separation makes that clearer. State plainly what L3 does **not** cover:
non-Claude hosts (no headless runner exists for Antigravity, Cursor, Codex, Devin or
Copilot), and merge.

**DONE WHEN:** the layer table names L1–L4 with owner, isolation and coverage, and L3's
limits are explicit.

---

## 5. Order

```
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8
```

2 blocks 4 (phases need the shim). 5 hardens 4. 6 is independent of 7.

## 6. Verification

| Check | Slice |
|:---|:---|
| `~/.claude`, `~/.gemini`, working repo byte-identical before/after | 1 |
| Temp environment removed on success, failure and SIGINT | 1 |
| Every `gh` call served by the shim; unknown subcommand fails loudly | 2 |
| No gate blocks; an unanswered gate fails by name | 3 |
| Each phase asserts an artifact + a frontmatter invariant | 4 |
| No assertion reads agent prose | 4 |
| Subagent guardrails verified, not assumed | 5 |
| Live lane leaves no repo, even when killed | 6 |
| Shimmed lane runs per PR; live lane nightly | 7 |

## 7. Risks

| Risk | Mitigation |
|:---|:---|
| Agent non-determinism makes assertions flaky | Assert artifacts and sentinels only (E3) |
| Shim drifts from real `gh` behaviour, so the lane passes while reality breaks | Fixtures are **recorded** from `--live-gh`, refreshed when a skill's `gh` usage changes (Slice 2) |
| A killed live run orphans a GitHub repo | Scope preflight + atexit + signal handler; print the delete command on failure (Slice 6) |
| Cost and wall-clock of full-lifecycle agent runs | Shimmed lane is the default; live lane nightly |
| Only Claude Code is exercisable headlessly | Stated as an explicit limit, not papered over (Slice 8) |
| Harness passes because a gate silently never ran | Per-phase sentinels; a missing sentinel is a failure, never a skip |
