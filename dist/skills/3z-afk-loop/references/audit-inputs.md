---
description: How the 4a Spec auditor is fed (lean packet) and how a re-audit after a gap fix is scoped (delta rule); shared by 4a Phase 2/4 and 3z Steps 2B/2C.
version: "1.1.0"
timestamp: 2026-10-28
---

# Audit inputs: lean packet and delta re-audit

Same guardrails, same confidence scale (`confidence-scale.md`), same ≥ 80 threshold. Only how the Spec auditor's inputs are delivered changes; the Standards auditor already takes a diff command.

## Lean packet (default)
The lead resolves the targets and passes them inline:
- The slice issue's `### Acceptance Criteria` (primary) within the whole issue body (Overview and Notes carry scope lines such as "Not building"), the PRD §6/§7/§8 and design doc where they exist (never dropped), and the 3d `## Deviations`.
- The scoped diff (`git diff <base>...HEAD -- <changed paths>`, run by the lead, passed as text) and the names of the test files and tests the slice adds or changes.
- Nothing else up front. The auditor reads a full file (implementation, a test body, `LEARNINGS.md`) only when a finding needs it, and never runs repo-wide discovery.

Report `input: lean` in the audit findings record. An audit that read full files instead (the diff is too large to pass inline, or the lead chose to) reports `input: full`.

## Delta re-audit (round 2 and later)
After a gap fix the re-audit is handed the round-1 gap list (the previous coverage map's gap rows, each with its stated bar: its suggested fix), the previous coverage map and the fix diff (`git diff <last audited head>..HEAD`). The gap list is frozen:
1. Re-check each open gap only against the bar its round-1 entry stated. Never widen it; a wider concern is a new finding (point 2).
2. A new ≥ 80 gap only on lines changed since the last audited head (in the fix diff). Anything else, including a first-seen concern on unchanged lines, is Watch (`confidence-scale.md`).
3. Carry every other row forward unchanged.
- No extra full pass: it would cost more than the two full audits it replaces.
- The final `[PASS]` still needs a row in the coverage map for every AC. The diff unavailable (history rewritten) → audit the whole lean packet again.
