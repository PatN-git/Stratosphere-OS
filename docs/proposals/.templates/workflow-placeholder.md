---
name: xxx
description: "xxx. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
  stratos.version: "0.1.0"
---

# TBD

> Also emit `agents/openai.yaml` alongside `SKILL.md`:
> `policy: { allow_implicit_invocation: false }`
