---
name: 0c_handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
type: workflow HITL
trigger: User. Do not run autonomously.
version: "1.0.1"
updated: 2026-06-17
---

Write a handoff document summarizing the current conversation so it can continue in a fresh session. Save to `.tmp/` using the naming convention `handoff_<date>_<name>.md`.

Include a "suggested skills/workflow" section, which suggests skills should be used in new session.

Do not duplicate content already captured in other artifacts (e.g. PRDs, git issues). Reference by ID or URL instead.

Redact sensitive information (e.g. API keys, passwords, personally identifiable information).

If user passed arguments, treat them as description of what the next session will focus on and tailor doc accordingly.