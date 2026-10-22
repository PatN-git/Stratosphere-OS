---
type: research
title: 4a Audit Test Corpus
description: "Labeled cases, auditor results and triage verdicts for testing ideas that change what the 4a Spec auditor reports; the data behind 4a-audit-eval-results.md."
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-20
version: "1.0.0"
---

# 4a audit test corpus

Dev-only data for [the test plan](../../plans/4a-audit-eval-strategy.md) and [its first results](../4a-audit-eval-results.md).

- `cases.json`: 13 real cases (7 StratOS, 6 CleanTechHub) and 4 clean controls: repo, slice, issue, the commit before the audit fixes (`pre`) and the audit-fix commits (`fix`). Paths in the manifest are machine-local.
- `labels/<case>.json`: the labeled spec gaps, derived by a labeler subagent from the audit-fix commits (not from the auditor's own words), each with a class, key terms for mechanical matching and a label confidence. 43 labels: 19 high, 18 medium, 6 low.
- `results/<case>__B__<k>.json`: one lean+watch Spec audit run (`B` arm, repeat `k`): every finding at confidence 60 or above. `results/tokens.csv`: subagent tokens per run.
- `triage/<case>.verdict.json`: a small-model verifier's verdict on each 60-79 finding of run `k=1`; `triage/tokens.csv`: its cost.

Rebuild snapshots and packets with `python scripts/dev/audit_eval_build.py --out DIR`; score with `python scripts/dev/audit_eval_score.py --eval-dir DIR` (`--lint` for the AC-literal lint). BT-186 is not in the corpus: its fix commits are Standards-only, so it has no labeled spec gap.
