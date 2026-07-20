---
name: x_jules-dispatch
description: EXPERIMENTAL launcher — run the opt-in jules-dispatch skill (offload bounded mode:AFK slices to Google Jules async agent). Thin delegator; the skill holds all logic and guardrails.
type: workflow HITL
trigger: manual
version: "0.1.4"
timestamp: 2026-07-17
---

# /x_jules-dispatch (experimental launcher)

User-invoked entry point for the **jules-dispatch** skill. Holds no logic of its own —
the skill is the single source of truth; this only routes to it (so it also works as a
call target when a future workflow delegates here).

## Steps
1. **Ensure the pack is installed.** If `.agents/skills/jules-dispatch/SKILL.md` is absent,
   run `/sync-skills --only jules-dispatch` first — the pack is opt-in, not bundled.
2. **Delegate to the skill.** Follow `.agents/skills/jules-dispatch/SKILL.md`, passing the
   user's arguments through (`--slice <id>` / `--sprint`, `--source <jules-source>`).
3. **Hand off.** The skill dispatches and reports PR readiness only; verify each PR with
   `/4a_verify-and-ship` and merge yourself.

All guardrails live in the skill (never merge/auto-merge, not an orchestrator, no local
git checkout/push, key never logged). This launcher never restates or weakens them.
