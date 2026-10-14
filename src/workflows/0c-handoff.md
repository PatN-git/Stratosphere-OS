---
name: 0c-handoff
description: "Compact conversation into handoff document for next session. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.1.0"
timestamp: 2026-10-14
---

Save handoff to `.tmp/handoff_<date>_<name>.md`; one line per section, `none` if empty:
1. **Scope & decisions:** accepted scope; decisions made in this chat.
2. **Status & next:** issue ID (do not restate it); the first action on resume.
3. **Tree:** branch, files changed, committed or not.
4. **Verification:** exact commands run and their outcomes.
5. **Open:** questions, risks, approvals still needed; approvals given here do not carry over.
6. **On disk vs chat-only:** what exists only in this conversation.
7. **Suggested Skills/Workflows.**

Reference PRDs and issues by ID/URL; never duplicate them. Redact credentials, PII, and sensitive data. Tailor to any passed arguments.
