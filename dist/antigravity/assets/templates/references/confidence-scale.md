---
description: Generic confidence scale and scoring dimensions for StratOS audits and findings.
version: "1.0.0"
timestamp: 2026-06-22
---

# Confidence Scale

## Scoring Dimensions
Score findings from 0–100 based on the following dimensions:
1. **Evidence strength** — Is the issue directly visible in the files or documented guidance?
2. **Scope relevance** — Is it structural architectural drift, a domain boundary violation, scalability risk, or repeated violation of documented rules?
3. **Practical impact** — Would this materially affect maintainability, scalability, domain separation, implementation safety, or future feature delivery?
4. **Actionability** — Can the issue be converted into a clear action with a specific component, root cause, and remediation direction?

## Banding Anchors
- **0–39: Discard**
  - Speculative, stylistic, linter-level, pre-existing without current impact, already tracked in backlog, or outside the target directory/scope.
  - Do not mention in output.
- **40–69: Weak Signal**
  - Possibly valid, but isolated, low-impact, or lacking connection to documented architectural rules.
  - Do not report unless explicitly asked for exploratory findings.
- **70–79: Near Miss**
  - Likely architectural concern, but missing repeated evidence, explicit rule violation, clear scalability impact, or actionable remediation.
  - Do not report in final output. Use internally only.
- **80–89: Report**
  - Strong evidence of structural drift, domain boundary violation, repeated anti-pattern, ignored documented rule, or unmanaged debt likely to block maintainability/scalability.
- **90–100: Critical / Confirmed**
  - Directly proven violation of documented architecture rules or repeated historical failure pattern with clear downstream impact.
  - The issue materially increases implementation risk, feature delivery cost, or system coupling.

## Threshold Rule
- **Only report findings with confidence ≥ 80.**
- When in doubt, lower the score and discard.
