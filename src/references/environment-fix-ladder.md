---
description: Destination ladder for candidate lessons. Routes each lesson to the cheapest durable fix, with LEARNINGS last. Cited by 0b.
version: "1.0.0"
timestamp: 2026-10-05
---

# Environment-Fix Ladder

A lesson written to `LEARNINGS.md` does not change behaviour on its own. Route each candidate to the **first** rung that fits.

## Rungs

1. **Deterministic check:** lint, test, setup file, CI, hook, or `validate_memory.py`. Wire an existing check before inventing one.
2. **Reviewer standard:** a rule read by the 4a Standards Auditor (`CODING_STANDARDS.md` → `[[A-xxx]]` → `code-smell-baseline.md`), not loaded into implementers. Name the file bare, with no directory prefix.
3. **Existing law already covers it:** cite it and write nothing.
4. **Framework issue:** host or agent tooling behaviour (shell quoting, tool misuse, re-reads). File it against StratOS, not the project.
5. **Issue / `STATUS.md`:** in-flight state (the durability gate in 0b step 4).
6. **`LEARNINGS.md`:** only if durable, non-mechanical, needed while implementing a *different* slice, and backed by evidence (it bit ≥2× or cost real time; cite the session moment or commit).

## Rules

- **Escalation:** a recurrence of an existing LEARNINGS lesson goes to rung 1 or 4, never a new or duplicate entry.
- **Evidence rule:** every candidate cites a concrete session moment. Discard any that cannot.
- **Hypothesis rule:** state a root cause as a hypothesis until verified.
