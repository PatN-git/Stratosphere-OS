---
name: 0c_handoff
description: Compact conversation into handoff document for next session.
type: workflow HITL
trigger: manual
version: "1.0.4"
timestamp: 2026-07-17
---

## Phase 0: Context Hydration (self-gated, read-only)
Run `.agents/skills/load-memory/SKILL.md` to restore session context. Self-gated (no-op if already loaded this session). Read-only: never transitions issue state or touches branches.

Save handoff summarizing current session to `.tmp/handoff_<date>_<name>.md`.

Include "Suggested Skills/Workflows" section.

Do not duplicate content in other artifacts (PRDs, issues); reference by ID/URL.

Redact credentials, PII, and sensitive data.

Tailor handoff to any passed arguments.