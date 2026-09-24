---
name: 0c-handoff
description: "Compact conversation into handoff document for next session. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.0.3"
timestamp: 2026-07-17
---

Save handoff summarizing current session to `.tmp/handoff_<date>_<name>.md`.

Include "Suggested Skills/Workflows" section.

Do not duplicate content in other artifacts (PRDs, issues); reference by ID/URL.

Redact credentials, PII, and sensitive data.

Tailor handoff to any passed arguments.