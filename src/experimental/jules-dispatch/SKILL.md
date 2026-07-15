---
name: jules-dispatch
type: skill experimental
description: EXPERIMENTAL, opt-in — offload bounded mode:AFK slices to Google Jules (async cloud agent). Dispatch + report; hands off at "PR opened". Never merges, never orchestrates. Use when the user asks to send/offload a slice (or a sprint) to Jules.
version: "0.1.1"
timestamp: 2026-07-15
---

# SKILL: jules-dispatch (experimental)

Offload bounded, well-specified `mode:AFK` slices to Google Jules; implementation runs on
Google's VM, preserving Claude/Antigravity tokens. This skill **dispatches and reports** —
it never verifies or merges. You run `/4a_verify-and-ship` and merge.

## Guardrails (invariant — never weaken)
- **Never merges, never enables auto-merge** — `automationMode` is `AUTO_CREATE_PR` only.
- **Not an orchestrator** — never invokes `4a`/`3z`/`3d`.
- **Never checks out or pushes a Jules branch locally** — operates via `gh`/API against origin (that branch exists only on origin).
- **Key never logged** — read from `JULES_API_KEY` in `.env.local` and sent only as the `X-Goog-Api-Key` header; never placed in a URL, printed, or written (`config.safe_log` is available to scrub it from any diagnostic output).

## When to use
User asks to send/offload/dispatch a slice, or fan a sprint's AFK slices, to Jules. Only
bounded slices with acceptance criteria — keep exploratory, tight-iteration, and
architecture work local.

## Prerequisites
- `JULES_API_KEY` in `.env.local`.
- Jules GitHub app installed on the target repo; its environment configured once in Jules's
  UI (Initial Setup → Run and Snapshot).
- A root `AGENTS.md` in the target repo (Jules auto-reads it for conventions).

## Run (from project root)
```bash
PACK=.agents/skills/jules-dispatch
python $PACK/dispatch.py --slice BT-0042 --source <jules-source> [--repo owner/name]   # one slice
python $PACK/dispatch.py --sprint --source <jules-source> --max-sessions 3             # batch (sequential; Jules parallelizes)
python $PACK/status.py                                                                  # poll & report, when you choose
```

## Flow
1. **Preflight** (`gh issue view`): slice must be `mode:AFK`, not `tier:epic`, and state acceptance criteria — else fail closed.
2. **Dispatch:** create a Jules session (`automationMode=AUTO_CREATE_PR`, `requirePlanApproval=true`); record `{slice_id, session_id, …, state:DISPATCHED}` in `.memory/jules-ledger.jsonl` (single-writer, sole state store, idempotent).
3. **`--status`:** poll each `DISPATCHED` session; on a ready PR, print its URL + `gh pr view` CI status and flip the row to `DONE`.
4. **You** verify: `gh pr checkout <pr>` in a real clone → `/4a_verify-and-ship` → merge.

See `CONTRACT.md` for the pinned v1alpha API shapes (PR URL at `session.outputs[].pullRequest.url`).
