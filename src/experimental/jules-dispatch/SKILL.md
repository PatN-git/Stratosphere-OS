---
name: jules-dispatch
type: skill experimental
description: EXPERIMENTAL, opt-in — offload bounded mode:AFK slices to Google Jules (async cloud agent). Dispatch + report; hands off at "PR opened". Never merges, never orchestrates. Use when the user asks to send/offload a slice to Jules.
version: "0.1.0"
timestamp: 2026-07-15
---

# SKILL: jules-dispatch (experimental)

Offload **bounded, well-specified** `mode:AFK` slices to Google Jules so the
implementation runs on Google's side (preserving Claude/Antigravity tokens). This
skill **dispatches and reports** — it does not verify or merge. You (the human) run
`/4a_verify-and-ship` and merge.

**This is deterministic tooling, not an orchestrator.** It never invokes `4a`/`3z`/`3d`,
never merges or enables auto-merge, and never checks out/pushes a Jules branch locally.

## When to use
User asks to "send/offload/dispatch this slice to Jules", or to fan a sprint's AFK
slices out to Jules. Only for bounded slices with acceptance criteria — not
exploratory, tight-iteration, or architecture work (keep those local).

## Prerequisites
- `JULES_API_KEY` in `.env.local` (sent as the `X-Goog-Api-Key` header).
- Jules GitHub app installed on the target repo; env configured once in Jules's UI
  (Initial Setup → Run and Snapshot).
- A root `AGENTS.md` in the target repo (Jules auto-reads it for conventions).

## How to run (from the project root)
```bash
PACK=.agents/skills/jules-dispatch

# one slice
python $PACK/dispatch.py --slice BT-0042 --source <jules-source> [--repo owner/name]

# a batch / sprint (sequential dispatch; Jules parallelizes execution server-side)
python $PACK/dispatch.py --sprint --source <jules-source> --max-sessions 3

# later, when you choose — poll & report (deterministic, zero-LLM)
python $PACK/status.py
```
`status.py` prints, for each ready PR, its URL + CI status and the handoff:
`gh pr checkout <pr>` in a real clone → `/4a_verify-and-ship` → merge yourself.

State lives only in `.memory/jules-ledger.jsonl` (single-writer, idempotent).
See `CONTRACT.md` for the pinned API shapes and `x_jules-dispatch.md` for the full flow.
