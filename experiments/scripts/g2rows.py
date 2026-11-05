p='findings.md'
s=open(p,encoding='utf-8').read()
rows=("| F31 | G2 | product (pre-existing) | minor | 3c Phase 5 step 1 sets `priority:*` with no `ensure_label` step; Phase 3 \"Label Check: Verify labels exist in registry\" names no action for a missing label. On real GitHub, `gh issue edit --add-label priority:high` fails when the label does not exist (first sprint of a fresh repo). Haiku improvised `gh label create`. | not fixed. Proposed: Phase 5 step 1 `ensure_label` each `priority:*` band it sets (covered by the sprint halt's confirmation). |\n"
"| F32 | G2 | harness | minor | Fake gh accepts `--add-label` for labels absent from its registry (real gh errors), and the seed creates no labels, so F31-type gaps pass silently. Also nested `-q .a.b` is unsupported (known F4 class). | not fixed. |\n")
s=s.replace("## Learnings", rows+"## Learnings",1)
s+="""
## Follow-up G2 — 3c GitHub (2026-10-28)
- Haiku 1.9 min, 101k, 17 tool calls. ice_read candidates → reconcile `--edges blockers` once → v1.0.1 created → A1 (#2) and S (#5) moved to v1.0.1 with `priority:high`, sync comments, `[MIRROR-OK BT-002,BT-005]` first attempt. S sequenced as blocked-but-in-sprint; B1 (#4) `[BLOCKED]` (effective blocker from epic B's 3a `[NEW-DEP]` on BT-001), not budgeted. No commit or push.
- stage_checks G2: **all 16 PASS** (incl. no `--state all`, only ice_read reads bodies).
- Triage of Haiku's skill_defects: F31 (priority label never ensured) logged; B1's blocker "not its parent" is false (3c: effective blockers include the parent epic's); load-memory no-active-task in planning phases (also hit in 3a) and the missing `[BLOCKED]` template line are wording nits. Agent slip, not a skill defect: it said it "kept BT-004 in v1.0" although its parent is on v1.1.0; harmless here because B1 was blocked, but a non-blocked v1.1 slice could have been sequenced into v1.0.1 under my loosely worded pre-answer.
"""
open(p,'w',encoding='utf-8').write(s)
