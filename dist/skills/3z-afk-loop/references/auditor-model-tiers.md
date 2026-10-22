---
description: Host-neutral auditor_model tiers and how each host maps a tier to its subagent model setting; used by 4a Phase 2 and 3z Step 2B for the Standards auditor.
version: "1.0.0"
timestamp: 2026-10-20
---

# Auditor model tiers

Only the Standards auditor is tiered; the Spec auditor runs on the default model. A tier is a name, never a model ID (host-neutral). No host model setting, or no mapping below → default model, silently. Record the tier used as `std_tier` (`references/pr-body-and-ship.md` § Audit findings); none → omit.

| Host | `small` | default (no tier) |
|---|---|---|
| Claude Code | pass `model: haiku` on the subagent dispatch, or `model: haiku` in the subagent's frontmatter | `inherit` |
| Antigravity | a custom subagent whose frontmatter sets `model: flash` | `inherit` |
| Codex | a custom agent file (`.codex/agents/<name>.toml`) with `model = "gpt-6-luna"` and `model_reasoning_effort = "high"`; an account without that model keeps the default | omit `model` |

Provenance: each host's docs, read 2026-10-20; re-verify when a host changes. Codex: agent-file `model` beats the `[agents]` default beats the parent's; `gpt-6-luna` is the documented lower-cost option for lighter subagent work, start at `high` effort; model names depend on account and CLI version.
