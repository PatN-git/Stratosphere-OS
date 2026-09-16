---
type: plan
title: L3 — Automated Lifecycle E2E Harness
description: Drive the full StratOS lifecycle (0a→1a→1b→2a→2b→3b→3d→4a→0b) end-to-end in a throwaway environment with no human interaction, asserting on artifacts rather than prose.
version: "4.0.0"
generated:
  by: Claude Opus 5
  at: 2026-09-15
verified:
  - by: independent-review
    at: 2026-09-16
---

# L3 — Automated Lifecycle E2E Harness

Execution plan. 10 slices (0–9).

## 1. Contract

One command runs the StratOS lifecycle against a throwaway project and exits non-zero on
any gate failure, with **no human interaction and no residue**:

```bash
python tests/lifecycle-harness/run-L3.py            # shimmed lane (CI, deterministic)
python tests/lifecycle-harness/run-L3.py --live-gh  # real throwaway GitHub repo
```

Coverage is `0a→1a→1b→2a→2b→3b→3d→4a(audit-only)→0b`. **`4a`'s `ship-only` phase is out of
scope** (fact 12) — L3 is not the whole lifecycle, and Slice 8 says so plainly.

**The run's product is a report, not an exit code.** Every run emits
`docs/audits/l3-<run-id>.md` — a classified, evidence-carrying list of what StratOS v4 needs
changed (Slice 9). The exit code says whether the lifecycle completed; the report says what
is wrong with it.

At exit: temp `HOME` removed, temp project removed, any created GitHub repo deleted, the
developer's real `~/.claude`, `~/.gemini`, `~/.config/devin` and working repo untouched.

## 2. Facts

Verified 2026-09-15, re-verified under independent review 2026-09-16. Each carries its
source. **Check the source before trusting a fact; do not assume it is still true.**

1. **L3 is the gap.** `tests/install-harness/README.md` documents L1 (install paths, no
   agent), L2 (agentic install via headless `claude -p`), L4 (manual). All three cover
   **onboarding**. Nothing drives the **lifecycle**.
2. **The driver pattern exists but is single-turn.** `run-L2.py:56` spawns `claude -p` with
   `--dangerously-skip-permissions`, a temp `HOME`, one prompt string and `stdin=DEVNULL`.
   Assertions key off a sentinel, on-disk artifacts, **and the tool-use stream**
   (`run-L2.py:296-305` inspects tool blobs). All three are sanctioned surfaces. The
   single-turn shape is the problem Slice 0 solves.
3. **A simulation precedent exists** — `tests/test_3z_orchestrator_simulation.py` models the
   `3z-afk-loop` state machine without invoking an agent. *Unverified in detail.*
4. **Lifecycle skills are deliberately not model-invocable**: `disable-model-invocation:
   true` + `triggers: ["user"]` + a Codex sidecar (the sidecar exists under `dist/`, emitted
   by `build.py`). A harness invoking `/0a-start-session` **is** the user, so this is not an
   obstacle — but nothing may rely on a *model* deciding to fire one.
5. **Five subagents sit inside the tested chain**, confirmed by
   `tests/test_subagent_spawning.py:20-32`: `1b` Skeptical Challenger, `2b` Stress Tester,
   `3b` Slice Draft Auditor, and `4a`'s two auditors. **`1a`'s refutation subagent is Phase 2
   only and does not run under Quick Search** (fact 9). `3a`/`4c` also spawn subagents but
   are not phases under test. Every one of these carries a *report-only, write-nothing*
   guardrail.
6. **GitHub is load-bearing mid-flow.** `3b` creates issues, `3c` creates milestones, `4a`
   opens the PR. `src/scripts/reconcile.py:109` enforces the `[MIRROR-OK]` terminal-sync
   gate using **`gh issue view --json`**, not graphql; graphql is used separately by
   `3b`/`4a` for `addSubIssue`/`addBlockedBy`. `reconcile.py:160-166`: when `gh auth status`
   fails it prints `[local-only — GitHub not checked]` and returns 0 — it never prints
   `[MIRROR-OK]`, so an assertion on that string fails on a mis-built shim.
7. **`4a` exposes named gates** — `audit-only` (Phases 1–4) and `ship-only` (Phase 5) — so
   the harness can stop before any push.
8. **Workflows never merge** (AGENTS.md §4). A PR may be opened; merging is out of scope.
9. **`1a-research` runs live web searches.** `src/workflows/1a-research.md:33` — Quick
   Search is "single-iteration … **bypasses Phase 2 deep loop, work file, and refutation**";
   `:46` "Skip Phase 2 if running in Quick Search mode". The 24-query cap is a *Deep
   Research* budget (`1a:41-44`), not a Quick Search one. Content is never reproducible, so
   `1a` assertions are structural only.
10. **`2b-interface-design` branches three ways.** Path A (generator-assisted) needs Stitch
    or Claude Design MCP tools; Path B is native UI; **Path C (non-UI contract) is the only
    path fully exercisable headlessly.** The fixture topic must have no UI surface.
    *The absence of those MCP servers under `claude -p` is assumed, not tested.*
11. **Three skills commit and push to the default branch unprompted**, when `gh`/remote is
    connected: `2a-write-prd.md:88`, `2b-interface-design.md:100`,
    `3a-version-planning.md:69` (`3a` is outside the tested chain). The text says "push to
    the **default** branch"; no command is named, but no `gh` push exists, so it is
    `git push` — **the `gh` shim cannot intercept it.** This is the one place an automated
    run pushes without asking.
12. **`4a`'s `ship-only` is not exercisable here.** Phase 5.2 runs
    `design_theme.py --check <app-css-dir>/theme.tokens.css` and halts the ship on non-zero.
    A non-UI fixture has no CSS directory, so `ship-only` would fail for a reason unrelated
    to what L3 tests.
13. **`3d` depends on an externally-fetched skill.** `3d-implement-issue.md:38` runs
    `code-simplifier`, which is not in `src/skills/` — `src/external-skills.json:15-21`
    fetches it from GitHub. Setup therefore needs network even when `1a` is skipped.
14. **`run-L2.py:247` copies the repo with its `.git`**, carrying the real `origin` into the
    sandbox, and `:271` passes the full environment (including `GH_TOKEN`) to the child.
    Reusing it verbatim would hand a pushing agent a live remote — see E1, E7.

## 3. Invariants

- **E1. Containment is enforced, not merely checked.** `--dangerously-skip-permissions`
  means the agent can write anywhere, so a post-hoc diff is evidence, not a barrier. Scrub
  `GH_TOKEN`/`GITHUB_*` from the child environment in the shimmed lane; record a pre-run
  hash manifest of `~/.claude`, `~/.gemini`, `~/.config/devin` and the working repo's
  `git status`; diff at teardown. Never touch those paths (fact 14).
- **E2. Teardown is guaranteed**, including on failure and on SIGINT. A run that cannot
  guarantee teardown must refuse to start.
- **E3.** Assert on **artifacts, frontmatter, sentinels and the tool-use stream** — never on
  agent prose. Prose varies between runs and models; structure does not (fact 2).
- **E4.** The default lane shims **`gh`**. It is offline with respect to GitHub, not with
  respect to the web: `1a` searches live (fact 9) and setup fetches `code-simplifier`
  (fact 13). `--live-gh` is opt-in and never runs in the default CI job. `--skip-research`
  drops `1a` but does **not** make the lane egress-free.
- **E5.** The harness **never merges** and **never pushes to a real remote**. It does push
  to the *throwaway's* default branch, because `2a` and `2b` do so by design (fact 11).
  That is contained by E7, not prevented.
- **E6.** No gate may block. Gates are answered by a **scripted responder with a default
  answer policy** (Slice 0), not by pre-written text alone — most gates ask about content
  the agent invents at run time. An unmatched question fails the run by name.
- **E7.** No `.git` under the temp root may have a remote outside the temp root. Strip every
  `origin`, set `GIT_CONFIG_GLOBAL` to a temp file redirecting pushes to a local bare repo,
  and walk **all** `.git` directories in preflight — not just the project's (fact 14).

## 4. Why a shim is the default lane

A real repo per run costs API calls, needs a token with repo-delete scope, leaves residue
when a run is killed, and makes CI flaky on GitHub outages. A `gh` shim on `PATH` returning
canned JSON makes the default lane deterministic and free.

The shim is not a substitute for reality, so `--live-gh` exists and runs on a schedule, not
per PR. The first fixture set is hand-written (Slice 2); `--record` refreshes it from a real
run once Slice 6 exists.

## 5. The fixture topic

Every phase carries one subject end to end, so the subject is a **fixture**: pinned here,
changed deliberately, never retyped per run.

**A feature-flag evaluation engine.** Local evaluation of a flag ruleset: percentage
rollouts by hashed key, segment targeting, prerequisite flags, default fallback. No network
at run time, no service, no UI.

| Requirement | Why this topic satisfies it |
|:---|:---|
| `1a` can fill its template | `1a` Phase 3.3 demands an Opportunity table, Gap Matrix, Served/Pain matrices and **`## Cost & Viability Signals`** (pricing, paid products, ad spend). LaunchDarkly, Flagsmith, Unleash and Split have published, comparable per-MAU tiers — a real landscape to analyse. |
| `2a` can fill §12 | `2a` Phase 4 requires a populated cost table and a **Cost Approval Gate**. A per-MAU pricing landscape makes that gate genuinely fire instead of collapsing to `[Unknown]`. |
| `1b` has material to grill | Local evaluation vs. remote decisioning is a real trade-off with real consequences (latency, staleness, audit). Enough substance for a 20–50 question grill (Slice 0). |
| `2b` reaches Path C | No UI surface. The seam is an evaluation function plus a ruleset schema — deterministic, no generator MCP (fact 10). |
| `3b` slices naturally | Ruleset parsing → boolean/segment targeting → percentage rollout by hash → prerequisite chains. Four sequentially dependent, independently testable slices. |
| `3d` can implement it | Pure Python, no dependencies, no network, no credentials at run time. |
| `4a` can verify it | Deterministic tests against a fixed hash seed. No flake surface. |

Calibration is per phase, not overall. A cron parser — the obvious candidate — passes
`2b`/`3b`/`3d`/`4a` and fails `1a`/`2a`: every cron library is free OSS, so the cost and
competitive sections produce the right file shape while exercising none of the analytical
machinery behind them. Too easy starves the early phases; anything needing auth or a live
service cannot run offline.

Pin it in `tests/lifecycle-harness/fixture/topic.md`, together with the positions the
responder defends (Slice 0), so the subject is versioned alongside the harness.

---

## Slice 0 — The scripted responder (spike first)

**Build and prove this before anything else.** Every other slice assumes gates can be
answered; this is the slice that decides whether they can.

`claude -p` is single-turn (fact 2), but the gates are not. `1b-concept-framing.md:68`
specifies "typically 20–50 questions … no fixed question budget", and `:64` says "The user —
never the agent — declares 'enough'", explicitly guarding against an AFK agent grilling
itself. The questions do not exist until the agent writes them.

- Drive a multi-turn session: `--output-format stream-json --input-format stream-json` with
  a responder process, or a `claude --resume <session-id>` turn loop.

**Two subagents, asymmetric and isolated.** One agent answering its own grill is the exact
failure `1b:64` forbids. Isolation is what makes this legitimate rather than a loophole:

- **User Proxy** — sees only `fixture/topic.md` and the current question. Never sees the
  draft brief, the `1a` research file, or the grilling agent's reasoning. It answers in
  character; it cannot rubber-stamp a brief it has never read.
- **Sufficiency Auditor** — once the budget is spent, reads the draft brief and returns
  `PASS`, or `FAIL` plus the specific gaps. This replaces the human's "enough" declaration
  with something checkable, so a bound truncates deliberately rather than arbitrarily.

**The budget belongs to the harness, not to `1b`.** `1b`'s grill is deliberately unbounded
and the *user* ends it (`1b:64,68`) — because agents stop too early, and an agent that
decides it has asked enough is an agent grading its own work. That design is correct and
stays. The harness is standing in for the user, so the bound is the harness's own stopping
policy, expressed through the responder. **No change to `1b` follows from this.**

**Question budget: 10 per round** (`--max-questions`), auditor gate, then at most one more
round seeded by its gaps. **Hard cap 2 rounds / 20 questions**, after which the run fails
naming the unmet gaps. Default 10 in the shimmed lane keeps CI fast; the nightly
`--live-gh` lane runs `--max-questions 30` so a realistic-depth grill is exercised at least
once a day. A short run yields a thin brief by design — the auditor, not the count, decides
whether thin is sufficient, and the cap guarantees termination.

- **Default answer policy**, checked in and versioned with the fixture:
  - Pick-among-generated (`1b` framings, `2b` Phase 2.5 directions) → **always option 1**.
  - Open questions → answer from the pinned positions in `fixture/topic.md`.
  - Numeric/ICE prompts (`3b` Phase 2.2) → fixed: Impact 1.0, Confidence 80%, `size:small`,
    `mode:AFK` for every slice.
  - After N rounds on one gate → "enough, write it up".
  - No match → **fail the run, naming the gate and quoting the question** (E6).
- Enumerate every HALT/ASK/confirm point per skill into a checked-in `gates.md`, so
  "every gate is answered" is falsifiable.

**DONE WHEN:** `1b` reaches a valid discovery brief from a cold start with zero human
input; `gates.md` covers every gate the run actually hit; and **no loop can run forever** —
every gate has a budget and a terminal failure, proven by a test that starves the auditor
and asserts the run ends.

**IF THIS FAILS:** the phase list shrinks — `1a`/`1b` move to L4-manual and L3 covers
`2a→4a`. Decide that here, not after eight slices are built on the assumption.

## Slice 1 — Harness skeleton, isolation and scaffold

`tests/lifecycle-harness/run-L3.py`, borrowing `run-L2.py`'s structure but **not** its
repo-copy (fact 14).

- Temp `HOME`/`USERPROFILE`, temp project dir, temp `PATH` prefix for shims.
- Copy the repo **excluding `.git`**, or `git remote remove origin` on every `.git` under
  the temp root. Set `GIT_CONFIG_GLOBAL` to a temp file with
  `url."file:///<tempbare>".insteadOf` and `remote.pushDefault`. Preflight walks **all**
  `.git` dirs and aborts on any remote outside the temp root (E7).
- Scrub `GH_TOKEN`/`GITHUB_*` from the child env; the shim refuses to run if a real token
  is visible (E1).
- **Install StratOS into the throwaway** — `python build/build.py`, copy
  `dist/claude-code/{skills,commands}` into the temp `.claude/`, run `scaffold.py` against
  the project, and vendor the external skills (`code-simplifier`, `plan-html`) that `3d` and
  `2b` invoke (fact 13). Assert the scaffold tree before phase 1; without this there is no
  `/0a-start-session`, no `.memory/`, no `references/`, no `validate_memory.py`.
- `try/finally` teardown plus a `SIGINT`/`SIGTERM` handler; refuse to start if the temp root
  cannot be created under the OS temp dir (E2).
- `--keep` to retain the project on failure, printing its path. Never the default.

**DONE WHEN:** a no-op run creates and removes its environment; the pre/post hash manifest
of `~/.claude`, `~/.gemini` and the working repo matches; a run with any remote outside the
temp root refuses to start; and the scaffolded project passes `validate_memory.py`.

## Slice 2 — The `gh` shim

`tests/lifecycle-harness/shims/gh` (+ `.cmd`), first on `PATH`.

- Dispatch on argv. The real surface, from
  `grep -rhoE '\bgh [a-z-]+( [a-z-]+)?' src/workflows/ src/references/ src/scripts/`:
  `issue create|edit|view|list|comment|close`, `pr create|view|ready`, `api graphql`,
  `api repos`, `auth status`, `version`, plus `repo create|delete|list` for Slice 6.
  (`release view` does not appear anywhere — do not implement it.)
- Back it with a JSON fixture store; mint monotonic issue numbers so `BT-<padded>` IDs are
  stable across a run. The store is the **authoritative source `3b` writes `BACKLOG_MAP.md`
  from**, or `reconcile.py` will diverge from it (fact 6).
- `gh auth status` must **succeed**, or `reconcile.py` prints `[local-only]` and never emits
  `[MIRROR-OK]` (fact 6).
- Unknown subcommand → exit non-zero, logging the full argv, so the gap is self-diagnosing.
  A silently-succeeding shim makes every downstream assertion meaningless.
- **Record mode** (`--record`, with `--live-gh`) refreshes fixtures from reality. It depends
  on Slice 6, so the first fixture set is hand-written.

**DONE WHEN:** `3b` completes against the shim, `reconcile.py` reaches `[MIRROR-OK]`, and
the fixture store contains every `gh` invocation the run made.

## Slice 3 — Per-phase prompts

`tests/lifecycle-harness/prompts/<phase>.txt` — the *opening* turn only; the responder from
Slice 0 handles everything after it.

Each carries the invocation (`/0a-start-session`), the fixture reference, and a unique
sentinel to print on success.

**DONE WHEN:** every phase starts from its prompt and completes under the responder, with
`gates.md` updated for any gate the run discovers.

## Slice 4 — Phase driver and artifact assertions

For each phase: launch the phase, wait for its sentinel, then assert on disk.

| Phase | Asserted artifacts |
|:---|:---|
| `0a` (first, greenfield) | `Session Status: no-active-task`; **STATUS.md unchanged and no branch touched** — `0a:23` halts before any side effect, and `0a:24` says "**NEVER create a branch**" |
| `1a-research` | `docs/research/<slug>.md`; `type: research`; `sources:` non-empty, every entry carries `resource`; `## Cost & Viability Signals` populated, not `[Unknown]`; **no assertion on findings** (fact 9) |
| `1b-concept-framing` | `docs/discovery/<slug>.md`; `type: discovery-brief`; `status` in the routing vocab; cites the `1a` file; a `[[G-001]]` glossary term with its `Avoid:` list (scripted via the responder) |
| `2a-write-prd` | `docs/prds/BT-*.md`; `type: prd`; `status: stable`; §12 cost table populated; **`linked-prd` written back into the `1b` brief** — the one true cross-phase hand-off assertion |
| `2b-interface-design` | `docs/design/BT-*-interface.md`; `type: interface-design`; **Path C taken** — `## Interface Contract` present, no generator MCP in the tool-use stream; `docs/design/BT-*-directions.html`; `## Direction Alternatives (Considered)`; design path appended to the issue body; push landed on the throwaway bare repo (E7) |
| `0a` (second, post-backlog) | STATUS.md updated; existing branch checked out |
| `3b-create-issue` | issues minted in the fixture store; `BACKLOG_MAP.md` row per slice; `[MIRROR-OK]` reached; `generated.at` refreshed |
| `3d-implement-issue` | a feature branch exists; a commit per slice; tests green in the fixture project |
| `4a-verify-and-ship` | `audit-only` produces a coverage verdict and **no** branch/PR mutation |
| `0b-stop-session` | `.memory/STATUS.md` fields written (step 2); `validate_memory.py` exit 0 (step 9); `okf_view.py` ran (step 10). **Not** LEARNINGS/GLOSSARY entries (conditional) and **not** `verified` — promotion needs ≥2 occurrences across tasks and belongs to `0d`, so a single run never appends it |

Artifacts are additionally validated by `validate_memory.py` and by `src/scripts/okf_view.py`
against the OKF type registry (`src/rules/okf-protocol.md`). **Not** by
`tests/test_skill_conformance.py` — that validates the emitted skill tree under `dist/` and
knows nothing about `docs/`.

**DONE WHEN:** each phase asserts at least one artifact and one frontmatter invariant; no
assertion inspects agent prose (E3); `2b` completes Path C with no generator MCP.

## Slice 5 — Subagent tolerance

Five subagents sit in the chain (fact 5). Phases are not single-process.

- Per-phase timeouts scaled to subagent count; a timeout names **which phase**.
- Cap `reconcile.py` heal retries (`--max-heal-attempts`); `3b` Phase 3.5 and `4a` Phase 5.8
  say "re-run until `[MIRROR-OK]`", which is an unbounded loop with no scripted answer
  (fact 6). Fail by name instead of spinning.
- Capture nested output to `<temp>/logs/<phase>.log`; print the tail on failure.
- Assert the guardrails held: every one of the five is *report-only, write-nothing*, and
  after `4a audit-only` there is no commit, no push, no PR.

**DONE WHEN:** `1b`'s Skeptical Challenger, `2b`'s Stress Tester, `3b`'s Slice Draft Auditor
and `4a`'s two auditors all complete, and a deliberately broken guardrail (a subagent that
writes a file) fails the run.

## Slice 6 — The `--live-gh` lane

- Create `stratos-l3-<run-id>` via `gh repo create --private`, delete in teardown.
- Preflight: refuse to start unless `gh auth status` shows `delete_repo` scope, so a run can
  never leave an orphan.
- Registered atexit **and** signal handler; on teardown failure, print the exact
  `gh repo delete` command rather than failing silently.
- Stops at `audit-only` (facts 7, 12). Never merges (E5, fact 8).

**DONE WHEN:** a live run creates, exercises and deletes its repo; a killed run leaves no
repo behind; `gh repo list` is unchanged before and after.

## Slice 7 — CI wiring

- Default lane in `build-guard.yml`, behind the existing `pytest` step, gated on `claude`
  being available — skip with a clear message when it is not, never a silent pass.
- `--live-gh` nightly, not per PR (E4).
- Publish `<temp>/logs/` as an artifact on failure.

**DONE WHEN:** a PR runs the shimmed lane; the nightly runs the live lane; a failure uploads
logs.

## Slice 8 — Document L3

Extend `tests/install-harness/README.md`'s layer table with L3. State plainly what L3 does
**not** cover:

- **Non-Claude hosts.** No headless runner exists for Antigravity, Cursor, Codex, Devin or
  Copilot. L3 green implies nothing about them.
- **`4a ship-only`** — branch-safety check, push, `gh pr create --draft`, `status:in review`,
  `gh pr ready`, `reconcile --pr-id`. Untested here (fact 12); stays L4-manual.
- **Merge.** Never automated (fact 8).

**DONE WHEN:** the layer table names L1–L4 with owner, isolation and coverage, and L3's
limits are explicit. *(Doc-only; not verified by the harness itself.)*

## Slice 9 — Emit the v4 findings report

A pass/fail exit code says the lifecycle ran. It does not say what is wrong with StratOS.
This run is the only place every skill is exercised back-to-back against one subject, so it
is the only place the friction between them is visible — and that friction is the point.

Emit `<temp>/L3-report.md`, copied out to `docs/audits/l3-<run-id>.md` with OKF
`type: audit-report`. **Emit it on failure too**: a run that dies at `2b` has already
learned everything up to `2b`, and discarding that is the expensive mistake.

Classify every finding, because the three classes demand different action:

| Class | Meaning | Routes to |
|:---|:---|:---|
| `stratos` | a skill, reference or script behaved wrongly, or contradicted the constitution | `/2c-reconcile-specs` |
| `harness` | the assertion, shim or responder is wrong | this plan's backlog |
| `environment` | no network, no `claude`, absent MCP server | neither — recorded so it is not re-diagnosed next run |

Each finding carries: phase, class, **evidence** (file path, log line, or the exact command
and its output), what was expected, and a proposed change. No finding ships without
evidence — an unevidenced observation is prose, and E3 keeps prose out of this harness.

The signals already exist; Slice 9 is about capturing rather than discarding them:

| Signal | What it means |
|:---|:---|
| A gate the responder could not match (Slice 0) | a skill asks something unanswerable without a human |
| A phase that halted without its sentinel | a broken hand-off contract |
| An artifact that failed `okf_view.py` | a template/registry mismatch |
| A `gh` subcommand the shim did not know (Slice 2) | undocumented GitHub surface |
| A heal loop that hit `--max-heal-attempts` (Slice 5) | an unbounded gate |
| A subagent that wrote a file | a violated guardrail |
| A phase whose wall-clock or token cost is an outlier | a skill that will not survive AFK use |

**DONE WHEN:** a full run emits a classified, evidence-carrying report; a deliberately
broken skill appears in it as `stratos` with file and line; and a run failed at `2b` still
reports the findings from `0a`–`2a`.

---

## 6. Order

```
0 → 1 → 2 → 3 → 4 → 5 → 9 → 6 → 7 → 8
              │             └── 2's --record mode lands after 6
              └── 9 accumulates findings from here on
```

**0 gates everything** — if the responder cannot drive `1b`, the phase list changes before
any other slice is built. 2 blocks 4. 5 hardens 4. **9 lands after 5**, once every signal it
records exists, but the collection hooks go in as each slice is built rather than being
retrofitted. 6 is independent of 7; 7 publishes 9's report as a CI artifact.

## 7. Verification

| Check | Slice |
|:---|:---|
| `1b` completes from a cold start with zero human input | 0 |
| Every gate hit appears in `gates.md`; an unmatched question fails by name | 0 |
| No loop can run forever: every gate has a budget and a terminal failure | 0 |
| User Proxy never sees the draft brief; Sufficiency Auditor gates the budget | 0 |
| Pre/post hash manifest of `~/.claude`, `~/.gemini`, working repo matches | 1 |
| No `.git` under the temp root has a remote outside it; a run that would push out refuses to start | 1 |
| `GH_TOKEN`/`GITHUB_*` absent from the child env in the shimmed lane | 1 |
| The throwaway is scaffolded and passes `validate_memory.py` before phase 1 | 1 |
| Temp environment removed on success, failure and SIGINT | 1 |
| Every `gh` call served; unknown subcommand fails loudly; `[MIRROR-OK]` reached | 2 |
| Each phase asserts an artifact + a frontmatter invariant | 4 |
| No assertion reads agent prose | 4 |
| `2b` completes Path C headlessly, with no generator MCP | 4 |
| `linked-prd` written back into the `1b` brief by `2a` | 4 |
| All five subagent guardrails verified, not assumed | 5 |
| Heal loops bounded; no unbounded `[MIRROR-DRIFT]` retry | 5 |
| Live lane leaves no repo, even when killed | 6 |
| A failing run still reports findings from the phases that completed | 9 |
| Every finding carries evidence and a class; a broken skill lands as `stratos` | 9 |
| Shimmed lane runs per PR; live lane nightly | 7 |

## 8. Risks

| Risk | Mitigation |
|:---|:---|
| Gates cannot be answered without a human, so L3 is unbuildable as scoped | Slice 0 is a spike with an explicit fallback: shrink to `2a→4a`, move `1a`/`1b` to L4 |
| `--dangerously-skip-permissions` means containment is by convention, not sandbox | Env scrub + token-visibility refusal + hash manifest (E1); never run against a dirty working repo |
| The real `origin` rides into the sandbox and `2a`/`2b` push to it | Copy without `.git`; strip every remote; `GIT_CONFIG_GLOBAL` redirect; preflight walks all `.git` dirs (E7, fact 14) |
| Agent non-determinism makes assertions flaky | Assert artifacts, frontmatter, sentinels and tool-use stream only (E3) |
| Shim drifts from real `gh`, so the lane passes while reality breaks | Hand-written first, then `--record` from `--live-gh`; refreshed when a skill's `gh` usage changes |
| `reconcile.py` drift loops forever with no scripted answer | `--max-heal-attempts`; shim store is authoritative for `BACKLOG_MAP` (Slice 5, fact 6) |
| `1a`'s live searches make the lane slow or non-reproducible | Structural assertions only; `--skip-research` where there is no egress (E4) |
| A killed live run orphans a GitHub repo | Scope preflight + atexit + signal handler; print the delete command on failure (Slice 6) |
| Only Claude Code is exercisable headlessly, and `ship-only` is untested | Stated as explicit limits, not papered over (Slice 8) |
| Harness passes because a gate silently never ran | Per-phase sentinels; a missing sentinel is a failure, never a skip |
| The report becomes a dumping ground nobody acts on | Every finding is classified and routed; `stratos` findings go to `/2c-reconcile-specs` as real work, not a list |
| A bounded grill produces a brief too thin to be a real test | The Sufficiency Auditor, not the question count, decides; a `FAIL` with unmet gaps fails the run (Slice 0) |

## 9. Lifecycle defects this planning found — and their resolution

Each was verified against the source while planning the harness, then triaged with the
maintainer. **Two of the five were not defects at all**, which is itself the lesson: a
static read cannot distinguish a bug from a deliberate design without asking. All resolved
changes are in this PR.

| # | Finding | Verdict | Resolution |
|:--|:---|:---|:---|
| D1 | Three skills commit and push to the **default branch** automatically (`2a:88`, `2b:100`, `3a:69`), which AGENTS.md §4 clause (3) forbids | **Not a defect — deliberate.** The artifact must be reachable by every tool and agent that later picks up the work, not stranded in one working copy. | The constitution was silent on an intentional behaviour. §4 gains a narrow **documentation-artifact exception**: one generated document per run, never code, never swept drift, nothing else may push to the default branch. |
| D2 | `reconcile.py` **fails open** offline — `[local-only]`, `return 0` — so a gate that says "non-zero → heal" silently verifies nothing | **Defect.** | `--require-gh` added. Terminal gates pass it and get exit `3` + `[MIRROR-UNVERIFIED]` when GitHub is unreachable. Default behaviour unchanged, so ordinary offline dev runs still work. |
| D3 | Four gates are **unbounded loops** — "re-run until `[MIRROR-OK]`" with no cap | **Defect**, and it compounds with D2: offline the gate could never emit `[MIRROR-OK]` while also exiting 0, so the instruction was unsatisfiable exactly when it failed open. | Bounded to **3 attempts**, then halt and surface the drift. `[MIRROR-UNVERIFIED]` halts immediately. A human notices an infinite loop; `3z-afk-loop` does not. |
| D4 | `4a` Phase 5.2 runs `design_theme.py --check` **unconditionally**, so a backend-only project can never ship | **Defect.** | The check is now scoped to UI surfaces — skipped, with the skip stated, when there is no `theme.tokens.css` and no UI block in the `2b` doc (Path C). |
| D5 | `1b`'s grill has **no question budget** | **Not a defect — deliberate.** Agents stop too early; the user ends the line of questioning precisely so nothing is left unexplored. | Withdrawn. `1b` is unchanged. The harness bounds its *own* stopping policy in the responder (Slice 0), which is the harness acting as the user, not a change to the skill. |

**What remains for L3 to find:** D1–D5 were reachable by reading. The defects worth building
a harness for are the ones only a full run surfaces — hand-offs that break under real
artifacts, gates that deadlock in combination, skills whose cost makes them unusable AFK.
That is Slice 9's job.
