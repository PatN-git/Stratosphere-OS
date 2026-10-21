---
description: Host-neutral auditor_model tiers and how each host maps a tier to its subagent model setting; used by 4a Phase 2 and 3z Step 2B for the Standards auditor.
version: "1.0.0"
timestamp: 2026-10-20
---

# Auditor model tiers

Only the Standards auditor is tiered; the Spec auditor always runs on the default model. A tier is a name, never a model ID, so workflows stay host-neutral. A host with no model setting, or a tier with no mapping below, runs the auditor on the default model, silently. Record the tier used as `std_tier` in the audit findings (`references/pr-body-and-ship.md` § Audit findings); none set → omit it.

| Host | `small` | default (no tier) |
|---|---|---|
| Claude Code | pass `model: haiku` on the subagent dispatch, or `model: haiku` in the subagent's frontmatter | `inherit` |
| Antigravity | a custom subagent whose frontmatter sets `model: flash` (tiers `inherit`, `flash`, `pro`) | `inherit` |
| Codex | a custom agent file (`.codex/agents/<name>.toml`) whose `model` is the project's small model; Codex has no portable alias, so the default applies until the project defines one | omit `model` |

Provenance (read from each host's docs on 2026-10-20; re-verify when a host changes): Claude Code subagents (`model`: `sonnet`, `opus`, `haiku`, a full model ID or `inherit`); Antigravity custom subagents (`model`: `inherit`, `flash` or `pro`); Codex subagents (agent-file `model` takes precedence, else the `[agents]` default, else the parent's).
