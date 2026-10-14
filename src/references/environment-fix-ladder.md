---
description: Destination ladder for candidate lessons. Routes each lesson to the cheapest durable fix, with LEARNINGS last. Cited by 0b and 0d.
version: "1.1.0"
timestamp: 2026-10-13
---

# Environment-Fix Ladder

A lesson written to `LEARNINGS.md` does not change behaviour on its own. Route each candidate to the **first** rung that fits.

## Rungs

1. **Deterministic check:** lint, test, setup file, CI, hook, or `validate_memory.py`. Wire an existing check before inventing one. Host or tooling behaviour (shell quoting, missing browser, scheduler limits, tool misuse, re-reads) lands here as a local hook, setup check, or project rule.
2. **Reviewer standard:** a rule read by the 4a Standards Auditor (`CODING_STANDARDS.md` → `[[A-xxx]]` → `code-smell-baseline.md`), not loaded into implementers. Name the file bare, with no directory prefix.
3. **Existing law covers it, first miss only:** a `[LAW]` entry or core rule. Cite it and write nothing. A `[PATTERN]` or `[ASSUMED]` LEARNINGS id is not law.
4. **Framework feedback:** a defect in an installed StratOS skill (stale path, missing guard, wrong contract). Record it as skill (`.agents/skills/<name>`) · installed `version:` · defect · evidence · suggested fix, where the citing workflow records findings (0d `## Framework feedback`, 0b handoff note). Never file it, name a repo, or edit the installed skill.
5. **Issue / `STATUS.md`:** in-flight state (the durability gate in 0b step 4).
6. **`LEARNINGS.md`:** only if durable, non-mechanical, needed while implementing a *different* slice, and backed by evidence (it bit ≥2× or cost real time; cite the session moment or commit).

## Rules

- **Escalation:** a finding that matches any LEARNINGS id, or a law already cited on an earlier night (0d: `nights ≥ 2`), is a recurrence: rung 1 or 4, never rung 3 and never a new or duplicate entry.
- **Evidence rule:** every candidate cites a concrete session moment. Discard any that cannot.
- **Hypothesis rule:** state a root cause as a hypothesis until verified.
