---
name: 0c_handoff
description: Compact conversation into handoff document for next session.
type: workflow HITL
trigger: manual
version: "1.0.5"
timestamp: 2026-07-17
---

Save handoff summarizing current session to `.tmp/handoff_<date>_<name>.md`.

Include "Suggested Skills/Workflows" section.

Do not duplicate content in other artifacts (PRDs, issues); reference by ID/URL.

Redact credentials, PII, and sensitive data.

Tailor handoff to any passed arguments.