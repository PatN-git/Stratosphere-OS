---
name: x_jules-dispatch
type: workflow experimental
description: Optional, opt-in — offload bounded mode:AFK slices to Google Jules (async cloud agent). Dispatches and reports; hands off at "PR opened". Never merges, never orchestrates.
trigger: User-invoked only.
version: "0.1.0"
timestamp: 2026-07-15
---

# x_jules-dispatch (experimental)

Offload **bounded, well-specified** `mode:AFK` slices to Google Jules. Jules runs in
its own cloud VM and opens a PR on origin; this pack **reports** and stops. You verify
with the full `/4a_verify-and-ship` and merge yourself. It is **not** an orchestrator.

> Preserves Claude/Antigravity tokens: dispatch + status are deterministic scripts
> (~0 local tokens); the implementation compute runs on Google's side.

## Prereqs
- `JULES_API_KEY` in `.env.local` (sent as the `X-Goog-Api-Key` header).
- The Jules GitHub app installed on the target repo; env setup configured once in
  Jules's UI (Initial Setup → Run and Snapshot).
- A root `AGENTS.md` in the target repo (Jules auto-reads it for conventions).

## Usage
```bash
# one slice
python <pack>/dispatch.py --slice BT-0042 --source <jules-source> [--repo owner/name]

# a batch / sprint (sequential dispatch; Jules parallelizes execution)
python <pack>/dispatch.py --sprint --source <jules-source> --max-sessions 3

# later — poll & report (deterministic, zero-LLM; run when you choose)
python <pack>/status.py
```

## Flow
1. **Preflight** each slice (`gh issue view`): must be `mode:AFK`, not `tier:epic`, and
   state acceptance criteria. Fail closed otherwise.
2. **Dispatch:** create a Jules session (`automationMode=AUTO_CREATE_PR`,
   `requirePlanApproval=true`); record `{slice_id, session_id, …, state:DISPATCHED}` in
   `.memory/jules-ledger.jsonl` (single-writer, sole state store, idempotent).
3. **`--status`:** poll each `DISPATCHED` session; when a PR is ready, print its URL +
   `gh pr view` CI status and flip the row to `DONE`. **No merge, no auto-merge, no
   workflow invocation.**
4. **You** run `gh pr checkout <pr>` in a real clone → `/4a_verify-and-ship` → merge.

## Guardrails
- Never merges / never enables auto-merge (`automationMode` is `AUTO_CREATE_PR` only).
- Never invokes `4a`/`3z`/`3d` (not an orchestrator).
- Never checks out or pushes a Jules branch locally (operates via `gh`/API on origin).
- Key never logged (`config.safe_log`).
