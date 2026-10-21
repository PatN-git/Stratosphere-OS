---
description: How the 4a Spec auditor is fed (lean packet) and how a re-audit after a gap fix is scoped (delta rule); shared by 4a Phase 2/4 and 3z Steps 2B/2C.
version: "1.0.0"
timestamp: 2026-10-20
---

# Audit inputs: lean packet and delta re-audit

Same guardrails, same confidence scale (`confidence-scale.md`), same ≥ 80 threshold. Only how the Spec auditor's inputs are delivered changes; the Standards auditor already takes a diff command.

## Lean packet (default)
The lead resolves the targets and passes them inline:
- The slice issue's `### Acceptance Criteria` (primary), the PRD §6/§7/§8 and design doc where they exist (never dropped), and the 3d `## Deviations`.
- The scoped diff (`git diff <base>...HEAD -- <changed paths>`, run by the lead, passed as text) and the names of the test files and tests the slice adds or changes.
- Nothing else up front. The auditor reads a full file (implementation, a test body, `LEARNINGS.md`) only when a finding needs it, and never runs repo-wide discovery.

Report `input: lean` in the audit findings record. An audit that read full files instead (the diff is too large to pass inline, or the lead chose to) reports `input: full`.

## Delta re-audit (round 2 and later)
After a gap fix the re-audit is handed the previous coverage map and the fix commits' changed files (`git diff --name-only <last audited head>..HEAD`):
- Carry every earlier PASS row forward unchanged, unless its test or implementation file is in that changed-file list.
- Re-check the failed AC rows and every carried row whose files changed.
- No extra full pass: it would cost more than the two full audits it replaces.
- The final `[PASS]` still needs a row in the coverage map for every AC. The list unavailable (history rewritten) → audit the whole lean packet again.
