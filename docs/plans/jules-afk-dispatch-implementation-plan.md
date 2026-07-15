---
type: implementation-plan
title: Jules Dispatch — Phased Implementation Plan (v0.1, experimental)
description: Optional, on-demand skill pack that offloads bounded StratOS slices to Google Jules (async cloud agent), preserving Claude/Antigravity tokens on the expensive implement step. Dispatches and reports; hands off at "PR opened". Distributed via sync-skills, invisible to scaffold --update, never merges, never orchestrates.
status: finalized — ready to execute at P0
audience: implementing-agent
timestamp: 2026-07-15
version: "1.0.0"
revision: finalized — all decisions locked; awaiting maintainer go + token-limit reset
---

# Jules Dispatch — Implementation Plan (v0.1)

> **▶ RESUME POINT (when work restarts):** Plan is FINALIZED — no open design decisions. Begin at **P0**. P0–P6 (the full deterministic pack + tests + distribution) need **nothing from the maintainer** and can run start-to-finish solo. Only **P7 (live E2E)** needs the key already in `.env.local` and the Jules app on `cleantech_jobs` (both confirmed present). See "Inputs" for the tiny maintainer surface and the mandatory P7 teardown.

> **Authoring note (agent-first):** Executable work orders, not prose. Each phase has preconditions, deterministic steps, artifacts, and a **binary test gate**. Do not advance until the gate is GREEN. Follow StratOS TDD (`3d`/`micro-tdd`): failing gate first → implement to green → refactor. **Never merge — humans merge.**

---

## Decision that shapes this plan (please confirm)

The adversarial review's strongest recommendation was to make Jules an *implement-backend inside `3z_afk-loop`*, reusing its queue/preflight/ship machinery. That is the "correct" deep integration — **but it edits core StratOS and is exactly the "bake it in" you asked to avoid for now.**

**This plan therefore takes the light path you asked for:** a standalone, opt-in pack that **dispatches slices to Jules and stops at "PR opened."** It does not drive `4a`, does not orchestrate, does not touch `3z`. You verify/merge the resulting PR through your normal process.

- ✅ Matches "optional, invoked for specific slices, don't build StratOS around it."
- ✅ Dissolves the review's blockers (no fake `4a` entrypoint, no second orchestrator, honest token claim).
- ⏭️ The `3z`-integrated route is preserved as **v0.2 (Deferred)** — opt into it later if the experiment proves out.

---

## 0. Scope & invariants (enforce always)

**Goal.** Ship `jules-dispatch`: an optional pack that offloads one or more **bounded, well-specified** slices to Jules. Jules runs in its own cloud VM and opens a PR against **origin**. The pack records state and reports readiness. **A human reviews, verifies, and merges** — the pack's job ends at "PR opened."

**Why this saves tokens.** The expensive part StratOS spends Claude/Antigravity tokens on is the *implement* step (`3d` TDD loop / `3z` Step 2A subagents). Jules replaces *that* with Google-side compute. Dispatch + status-poll are deterministic scripts (~0 local tokens). Verification you'd pay for anyway, on your schedule — and Jules already self-tests in its VM, so its PRs arrive with a passing test run.

**Hard invariants (violation = halt):**
- **I1 — Never merge, never auto-merge.** No merge call anywhere; and the create-session payload must **not** request auto-merge via `automationMode`. Enforced by a grep tripwire *and* a payload assertion (`automationMode == AUTO_CREATE_PR`, not any auto-merge value).
- **I2 — Not an orchestrator.** The pack never autonomously invokes another workflow (`4a`, `3z`, `3d`). It dispatches, polls, and reports. This preserves `3z` as the sole sanctioned AFK orchestrator (AGENT.md §1).
- **I3 — Never bake in.** Source lives outside the build allowlist; fetched on demand via `sync-skills`; `scaffold.py --update` leaves it byte-identical. No edits to `3c/3d/3z/4a`.
- **I4 — Secret hygiene.** Read the key from env var **`JULES_API_KEY`** (canonical Jules env-var name), sourced from **`.env.local`** (gitignored via `.env.*`, `scaffold.py:324`); send its value as the **`X-Goog-Api-Key`** HTTP header. (`JULES_API_KEY` = env-var name; `X-Goog-Api-Key` = header name — same value.) Never in logs, `.memory/`, PR bodies, or commits. Enforced by a literal-key log-scan (do **not** rely on the existing `sk-…` scanner — Google keys won't match it).
- **I5 — gh/API only, no local git.** The pack must never `checkout`/`push` a Jules branch — that branch exists only on origin, and this working tree is not a clone of it ([[local-repo-disconnected]]). All PR interaction goes through the `gh` CLI / Jules API against origin.
- **I6 — Fail closed.** Missing key, ineligible slice, ambiguous state → stop with an actionable message. Never dispatch on a guess.
- **I7 — Idempotent, single-writer ledger.** All dispatch state in one `.memory/jules-ledger.jsonl`, written by a **single sequential writer** (no concurrent appends). Re-dispatch/re-poll never duplicates.

**Ground-truth conventions (verified against repo — do not re-derive):**
- `build/build.py` copies an **explicit allowlist** of dirs (`src/skills`, workflows, commands, rules, references, github, scripts — `build.py:156–203`); it is **not** a broad glob. Placing source at `src/experimental/jules-dispatch/` means it is simply never referenced by the build. There is no "glob to exclude"; the guard is a `build/validate.py` assertion that no `experimental/` path reaches `dist/`.
- `scaffold.py --update` iterates only `bundled_manifest.items()` (`scaffold.py:587–589`); no mapping targets `.agents/skills/`, and it never prunes non-bundled files. A pack at `.agents/skills/jules-dispatch` is invisible and survives byte-identical. `.agents/skills/` is gitignored (`scaffold.py:325`).
- Eligibility labels `mode:AFK`, `tier:slice` are canonical (`verify_scripts.py:44–46`) — reuse them; no new registry entry needed.
- Tests: plain-Python `test_*()` via `subprocess`, `.tmp/` scratch, no pytest, live-API tests **env-gated** (`verify_scripts.py`, `test_update_flow.py`). New tests must be wired into an explicit runner (see P1) — there is no auto-discovery.

**Jules API surface (v1alpha — pin, treat as unstable):** `POST /v1alpha/sessions` (`automationMode: AUTO_CREATE_PR`, `requirePlanApproval: true`), `GET /v1alpha/sessions/{id}`, `GET /v1alpha/sessions/{id}/activities?createTime=…`, `GET /v1alpha/sources`. Header `X-Goog-Api-Key`.

---

## Phase map

| Phase | Deliverable | Gate |
|---|---|---|
| P0 | Prereqs, live contract capture, source location | live `GET /sources` 200 + 3 captured cassettes + `CONTRACT.md` PR-path |
| P1 | `jules_api.py` (one HTTP module, injectable caller) + test runner | offline unit + cassette replay green |
| P2 | config, preflight, secret hygiene | fail-closed + literal-key log-scan = 0 hits |
| P3 | dispatch: single slice **and** sequential list/`--sprint` | payload assertion + ledger idempotency + dep-exclusion green |
| P4 | `--status` report (poll → readiness, **no orchestration**) | cassette status + no-merge/no-auto-merge gate green |
| P5 | distribution (`external-skills.json`) + update-safety | sync→update byte-identical integration gate green |
| P6 | docs, egress note, optional Antigravity launcher | docs lint + launcher capability verified |
| P7 | E2E acceptance on sandbox | dispatch→PR→report loop green; dispatch runner has 0 LLM calls |

---

## P0 — Prereqs & live contract capture

**Objective.** Lock a real ground truth for the alpha API; fix the source location.

**Preconditions (maintainer):** Jules key in `.env.local` (sent as `X-Goog-Api-Key`); sandbox repo with Jules GitHub app installed; **one-time Jules environment setup** for the sandbox via Jules's UI ("Configuration → Initial Setup" install/lint/test commands → "Run and Snapshot") — Jules takes env setup from its UI, **not** from the dispatch prompt; a root **`AGENTS.md`** in the sandbox for conventions (Jules auto-reads it — see "Jules context" note below). *(Real-PR reference for the GitHub-handoff side: maintainer's existing CleanTech Jules PR — see Inputs.)*

**Steps:**
1. Create `src/experimental/jules-dispatch/` (source home; build never references it).
2. `scripts/dev/capture_jules_contract.py` captures **real** responses into `tests/fixtures/jules/` (redacted): `sources.json`, `session_created.json`, `activities_pr_ready.json`, `activities_running.json`.
3. Record the exact JSON path where the PR URL appears in `src/experimental/jules-dispatch/CONTRACT.md`.

**🚦 Gate P0:** live `GET /sources` returns 200 with ≥1 source (env-gated); 4 fixtures present and schema-valid; `CONTRACT.md` states the literal PR-URL path. *(If maintainer supplies cassettes instead of a key, the gate is fixture presence + schema validation.)*

---

## P1 — `jules_api.py` (one module, testable offline)

**Objective.** All Jules HTTP in a single module. One seam only — an injectable `call(method, path, body)` — so tests run offline. No vendor-abstraction layer, no multi-class taxonomy.

**Steps:**
1. `jules_api.py`: `create_session`, `get_session`, `list_activities(since=None)`, `find_pr_url(session_id)`, `list_sources`. Default caller reads `X-Goog-Api-Key`; tests inject a `ReplayCaller` over `tests/fixtures/jules/`.
2. One `JulesError(status, message)` for failures (401/429/unexpected shape) — actionable message, never a bare `KeyError`. **Surface** `Retry-After` on 429 (attached to the exception for the caller; the client does not auto-retry).
3. `find_pr_url` uses the `CONTRACT.md` path; returns `None` when absent.
4. **Test runner:** create `tests/test_jules.py` with an explicit `__main__` calling each `test_*()` (mirroring `verify_scripts.py:364`); add a line to the repo's test entry so the suite actually runs them.

**🚦 Gate P1** (`python tests/test_jules.py`): each method parses its cassette; `find_pr_url` returns the PR from `activities_pr_ready.json`, `None` from `activities_running.json`; injected 401→`JulesError(401,…)`, 429 surfaces `Retry-After` (carried on the exception); `list_activities(since=T)` forwards `createTime=T`.

> Note (m1): these prove parsing + determinism, **not** live correctness. Live correctness is proven only by P0 capture and P7 E2E. Treat snapshots as regression guards, not proof.

---

## P2 — config, preflight, secret hygiene (I4, I6)

**Steps:**
1. `config.py`: read env var **`JULES_API_KEY`** (from `.env.local`); send as `X-Goog-Api-Key`. Absence → `JulesError` with actionable `JULES_API_KEY not configured in .env.local`; **no** dispatch.
2. `preflight(slice_id)`: via `gh issue view` assert issue exists, has acceptance criteria, carries `mode:AFK`, is not `tier:epic`. Return structured result.
3. `safe_log()` scrubs the key literal before any print/write.

**🚦 Gate P2:** key unset → non-zero exit, `create_session` call-count == 0; ineligible slice → fail closed with reason; **log-scan:** run every path with a fake key literal, grep all stdout/stderr/written files → **0 matches** (this greps the literal key, not the `sk-` pattern).

---

## P3 — dispatch: single + sequential batch (Options A & B)

**Objective.** Offload one slice, or several. **Batch = sequential dispatch loop, not concurrent** (avoids the single-ledger write race) — yet each created session runs **in parallel on Jules's side**, so you still get parallel throughput while walking away.

**Steps:**
1. `dispatch.py` (with argparse CLI) documented in the pack's `SKILL.md` (single self-contained skill doc; the pack ships as a skill, so no separate workflow doc — see the improve-workflows-skills §1/§2 pass).
2. Single: `preflight` → build prompt from **issue title/body/acceptance-criteria only** (conventions come from the repo's `AGENTS.md`, which Jules auto-reads; environment from Jules's UI snapshot — the prompt carries neither) → `create_session(auto_pr=True, require_plan_approval=True)` → append ledger row `{slice_id, session_id, source, created_at, state:DISPATCHED}`.
3. Batch: explicit list or `--sprint` (leaves with `mode:AFK`+`tier:slice` from the sprint milestone / `BACKLOG_MAP.md`); **exclude** slices with unmet `--blocked-by` deps; dispatch **sequentially**, one row per slice; a single failure records `FAILED` and continues.
4. `--max-sessions N` cap (default small) to bound alpha quota/cost (m6).
5. Ledger is single-writer and the **sole** state store; re-dispatch of a `DISPATCHED`/`DONE` slice is a no-op notice (I7). **No new GitHub labels invented** — eligibility reuses canonical `mode:AFK`+`tier:slice`; per-PR state lives only in the ledger (avoids coupling to the `BACKLOG_MAP` label registry). GitHub-side state labels can be added in a later version if a registry entry is created.

**🚦 Gate P3:** create-session payload asserted field-wise (`automationMode == AUTO_CREATE_PR`, `requirePlanApproval == true`) — not just a self-authored snapshot; second invocation for same slice → 0 new sessions; dependency-blocked slice excluded; injected failure on slice k → others still dispatched, row k `FAILED`, `--max-sessions` respected.

---

## P4 — `--status` report (poll & report; no orchestration) (I1, I2, I5)

**Objective.** Fire-and-forget catch-up that **reports**, and stops.

**Steps:**
1. `status.py`: read ledger → for each `DISPATCHED`, `get_session` + `find_pr_url`. PR ready → print `PR ready: <url>` + `gh pr view` CI status, set ledger row `DONE`. Still running → leave. Jules errored → `FAILED` + reason. **Jules-PR fingerprint (from CleanTech PR #77):** branch prefixed `jules-<digits>-<hash>`, commits authored by `google-labs-jules[bot]`, body with `## Summary` / `## Changes` — a corroborating detection signal alongside the session's own PR URL.
2. **Hand-off, not orchestration (decided — always-4a, human-triggered):** `--status` is a **deterministic, human-invoked** poll (no LLM, ~0 tokens). There is **no background or scheduled *agent* reconcile** — Jules sessions are intentionally slow, so an auto-checking agent loop would burn tokens for nothing. When a PR is ready, `--status` prints the PR URL + `gh pr view` CI status and instructs the human to run the **full `/4a_verify-and-ship` manually** in a real clone (`gh pr checkout <pr> && /4a…`). Verification is **always full `4a`**, always human-initiated. The pack never invokes `4a`/`3z` itself (I2) and never checks out/pushes locally (I5). *(Optional later: a deterministic cron that only refreshes the ledger — still zero-LLM — but never an LLM agent poll.)*
3. No merge, no auto-merge anywhere.

**🚦 Gate P4:** cassette PR-ready session → `--status` prints the PR URL + CI status and flips row to `DONE`; already-`DONE` rows skipped; **no-merge grep** (`grep -rEi "pr merge|/merge|automerge|merge_method|MERGE" src/experimental/jules-dispatch/` → 0) wired as an assertion; **no-auto-merge assertion** on the P3 payload; assert `status.py` makes **no** call to any workflow entrypoint.

---

## P5 — distribution & update-safety (I3)

**Steps:**
1. `build/validate.py`: assert no `experimental/` path appears in `dist/` (there is no build glob to edit — this guard is the whole job).
2. `external-skills.json` entry: `name: jules-dispatch`, `category: experimental`, `default: false`, **`repoZipUrl` = the StratOS repo archive** (decided: the pack ships as part of StratOS, marked experimental/test), `subPath: <repo>-<ref>/src/experimental/jules-dispatch/`, `targetPath: .agents/skills/jules-dispatch`, pinned `ref`.
3. Do not touch `scaffold.py`.

**🚦 Gate P5** (integration, temp project): `sync_skills.py --only jules-dispatch` lands the pack at `.agents/skills/jules-dispatch`; snapshot pack hashes → `scaffold.py --update` → re-hash **identical**, nothing pruned (the maintainer's core question, falsifiably tested); `dist/` has no `experimental/` path.

---

## P6 — docs, egress note, optional Antigravity launcher

**Steps:**
1. **README entry (decided):** document `jules-dispatch` in `README.md` as an **experimental, opt-in** pack — what it does, that it's fetched via `sync-skills` (not bundled), the `.env.local`/`X-Goog-Api-Key` requirement, and the "dispatch → walk away → `--status` → verify/merge yourself" flow. Mark clearly as experimental/test.
2. Data-egress note in `AGENT.md`/`README.md`: Jules clones into a Google-managed VM; PR reconciled on origin; key hygiene per I4; least-privilege GitHub-app scope.
3. **Antigravity launcher — DEFERRED (capability verified absent).** `sync_skills.py` always extracts to `skills_base / <entry name>` = `.agents/skills/<name>` (`fetch()` line ~243); the `targetPath` field is cosmetic and a `.agents/workflows/` target is impossible via sync-skills. So the pack ships as a **skill** (`SKILL.md`, invocable by name on Claude Code and available to Antigravity as a skill); a slash-command launcher on Antigravity would need a sync-skills enhancement or a manual copy. Documented, not built, for v0.1.

**🚦 Gate P6:** README experimental section + data-egress note present; `build/validate.py` guard asserts no `experimental/` path in `dist/`; `python build/validate.py` = OK. Antigravity slash-launcher explicitly deferred (see step 3).

---

## P7 — E2E acceptance (sandbox)

**Preconditions (maintainer-only):** a repo with the **Jules GitHub app installed** (throwaway sandbox, or reuse `cleantech_jobs`) + `JULES_API_KEY` in `.env.local`. The throwaway well-specified issues are **agent-generated** via `gh`, not hand-written.

**Steps:**
0. ⚠️ `cleantech_jobs` is a **real repo**, not a sandbox. All E2E artifacts must be trivial, clearly tagged, never merged, and fully removed in teardown. **Confirm the specific throwaway issues with the maintainer before any live dispatch.**
1. Agent creates 1–2 trivial, harmless throwaway issues via `gh` (e.g. add a code comment / touch a doc line), titled `TEST(jules-e2e): …`, labeled `mode:AFK` + `tier:slice`.
2. `dispatch.py --slice <id> --source <src>` → session created, ledger row `DISPATCHED`.
3. (out-of-band wait — Jules is deliberately slow) `status.py` → PR discovered (branch `jules-…`, author `google-labs-jules[bot]`), CI reported, row `DONE`, PR left **open** (never merged).
4. `--sprint` variant on 2 independent throwaway slices → 2 parallel sessions, both PRs reported.

**🚦 Gate P7 (acceptance):** full dispatch→PR→report loop green; PRs opened by Jules, **not merged**; **dispatch/status runner path makes 0 LLM calls** (deterministic — the honest, scoped form of the token claim).

**🧹 Teardown gate (mandatory — `cleantech_jobs` must end exactly as it started):** close every `jules-…` test PR (do **not** merge); delete their remote branches; close the throwaway `TEST(jules-e2e)` issues; remove any files/commits the test introduced; clear the local ledger. Verify via `gh pr list` / `gh issue list` / `git branch -r` that **zero** `jules-e2e` / `jules-*` test artifacts remain, and enumerate every closed/deleted item to the maintainer.

---

## Inputs required from maintainer

**✅ Decided:**
- **Eligibility signal** = canonical `mode:AFK` + `tier:slice` (no Jules-specific label in v0.1; no new registry entry).
- **Distribution** = ships inside the StratOS repo, marked experimental; fetched via `sync-skills`; documented in README (P5/P6).
- **Key** = stored in `.env.local`, sent as `X-Goog-Api-Key` (maintainer provisions; agent never handles the value, per I4 + platform safety).
- **`3z` integration** = deferred to v0.2.
- **Verification** = **always full `4a`, human-triggered**; `--status` is a deterministic zero-LLM poll with no background agent reconcile (P4).
- **`AGENTS.md` standard** = ADOPTED (done on branch `refactor/adopt-agents-md-standard`, v2.0.0) — target repos carry a root `AGENTS.md` Jules auto-reads; no generator needed.
- **GitHub-handoff reference** = ✅ received (CleanTech PR #77): Jules branch prefix `jules-<digits>-<hash>`, commit author `google-labs-jules[bot]`, `## Summary`/`## Changes` body.
- **Test issues** = agent-generated via `gh` (deterministic tests use in-code fixtures; live E2E creates throwaway issues) — maintainer need not hand-write any.
- **Key** = present in `.env.local` as **`JULES_API_KEY`** (canonical env var; the duplicate `X-Goog-Api-Key=` line is redundant and may be deleted).
- **Live E2E repo** = **`cleantech_jobs`** (real repo, Jules app already installed) — mandatory full teardown per P7.
- **Host order** = **Claude Code first**; Antigravity slash-command launcher is the optional P6 add-on.
- **CI policy** = **mock/cassette-only in CI** (no CI secret); live tests run locally against `.env.local`.
- **Runner** = Python; fire-and-forget + manual `--status`; `require_plan_approval=True`; sequential batch dispatch; `--max-sessions` default 3.

**⏳ Remaining (agent-side, no maintainer action):**
1. **Jules API contract** *(P0–P1)* — pin from the `google-labs-code/jules-sdk` source (TS types → REST fields; PR URL surfaces at the session result's `pullRequest.url`), draft `find_pr_url` against it, **confirm the exact REST path on the first live run** (guarded by `JulesContractError`).

**→ All design decisions are locked. Nothing blocks starting at P0.**

---

## Deferred to later versions (kept out of v0.1 on purpose)
- **v0.2 — `3z` integration (the review's "correct" path):** make Jules an alternate implement-backend inside `3z` Step 2A (dispatch to Jules instead of a local `3d` subagent), reusing `3z`'s queue/preflight/ship/conflict machinery. Requires editing core `3z` and accepting `3z` as the driver — opt in only if the standalone experiment proves out.
- **Concurrent fan-out** (multi-writer ledger / parallel HTTP) — v0.1 is sequential to avoid ledger races; Jules already parallelizes execution server-side, so the throughput win is largely already captured.
- **`AGENTS.md` generator** (`gen_agents_md.py`, Option D) — only relevant if StratOS keeps the nonstandard `AGENT.md` and needs to *derive* a Jules-readable `AGENTS.md` from it. If StratOS adopts the `AGENTS.md` standard (recommended companion chore), this generator is unnecessary — Jules reads `AGENTS.md` directly. Environment (install/lint/test) is configured in Jules's UI (Initial Setup + snapshot), so it never belongs in a generated file or the prompt.

**Jules context (resolved):** conventions ← repo root `AGENTS.md` (auto-read) + `readme.md`; environment ← Jules UI "Initial Setup" script + "Run and Snapshot" (one-time per repo); per-task detail ← the dispatch prompt (issue + acceptance criteria). The pack injects nothing beyond the task.
- **Vendor-neutral provider abstraction** — v0.1 is Jules-only in one module; generalize only when a second provider is real.

---

## What the review changed (changelog)
- **Removed the fake `4a` programmatic entrypoint.** `4a` is HITL-only (`4a:5,52`); the pack now hands off at "PR opened" and the human drives verification. *(B1)*
- **Fixed the token claim.** `4a` uses LLM auditors; "≈0 tokens" now scoped to the deterministic dispatch/status runner, which is what's actually true. *(B2)*
- **Stopped reinventing / conflicting with `3z`.** The pack is explicitly not an orchestrator (I2); `3z` integration moved to v0.2 Deferred. *(B3)*
- **Honored the disconnected-repo constraint.** New I5: `gh`/API only, no local checkout/push of Jules branches. *(B4)*
- **Dropped the fictional "exclude from build glob" step** — build is an allowlist, not a glob; kept only the `validate.py` guard. *(M1)*
- **Made batch sequential** (single-writer ledger) to kill the write race; throughput preserved via Jules-side parallelism. *(M2)*
- **Cut v0.1 scope** — one HTTP module + single `JulesError`, deferred vendor seam, fan-out concurrency, and `AGENTS.md` generator. *(M3)*
- **Hardened gates** — payload field assertions + no-auto-merge check (not just self-authored snapshots), literal-key log-scan (not the `sk-` scanner), explicit test-runner wiring, verified sync-target capability. *(m1–m4, m6)*
- **Maintainer decisions (round 2):** eligibility = `mode:AFK`+`tier:slice` (no new label); key in `.env.local` as `X-Goog-Api-Key`; pack ships in StratOS repo (experimental) + README entry; verification = **always full `4a`, human-triggered** (no background agent poll — Jules is intentionally slow); dropped invented `jules:*` labels (ledger is sole state).
- **Jules context resolved:** conventions via root `AGENTS.md` (auto-read) + readme; environment via Jules UI setup+snapshot (one-time); prompt carries only the task. Research found `AGENT.md` singular is nonstandard → `AGENTS.md`-adoption flagged as a separate companion chore.
