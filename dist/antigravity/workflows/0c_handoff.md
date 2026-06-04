---
name: 0c_handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
type: workflow HITL
trigger: user
---

Write handoff document summarising the current conversation so it can be continued in fresh session. Save to `.tmp` name like this handoff_date_name.

Include a "suggested skills/workflow" section, which suggests skills should be used in new session.

Do not duplicate content already captured in other artifacts (e.g. PRDs, git issues). Reference by ID or URL instead.

Redact sensitive information (e.g. API keys, passwords, personally identifiable information).

If user passed arguments, treat them as description of what the next session will focus on and tailor doc accordingly.