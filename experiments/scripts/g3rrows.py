p='findings.md'
s=open(p,encoding='utf-8').read()
rows=("| F37 | G3R | product | minor | A re-queued `status:blocked` slice restarts at attempt 1 with no gap report: 3z Step 2A's dispatch says \"If prior gap report is attached, target it\", but no step fetches the blocking `[UNCOVERED]` comment on re-queue (Haiku-3z wrote \"No prior gap report is attached\"). The 3d implementer found it anyway by reading the issue comments. | not fixed. Proposed: Step 1B Retry — attach the slice's last `[UNCOVERED]`/`[STUCK]` comment as the gap report. |\n"
"| F38 | G3R | harness | minor | Fake gh `issue edit --add-assignee @me` appends a duplicate (`['@me','@me']`); real GitHub assignees are a set. Haiku reported it as a 3d claim defect (false against real GitHub). | not fixed; dedupe in gh_shim. |\n"
"| F39 | G3R | rig | note | My 3z relay brief listed \"the Feature Acceptance Audit\" among 3z's dispatches, so Haiku-3z cut the ship-only pass before 4a step 8 to dispatch it itself. Corrected at the relay: ship-only ran all of Phase 5 and relayed its own FAA (09a). 3z's own text is fine (the FAA belongs to 4a); its claimed 3z defect is a rig artefact. | brief template fixed for later stages. |\n")
s=s.replace("## Learnings", rows+"## Learnings",1)
s+="""
## Follow-up G3 re-run — 3z, ship path (2026-10-28)
- User instruction: ship even if the audit is imperfect (process test), and leave a note for later agents. Brief carried a TEST-ENV OPERATOR OVERRIDE (UNCOVERED → VERIFIED, recorded in log, issue comment and PR deviations). **Not triggered**: the re-run's audit was a genuine `[PASS]`.
- Fresh Haiku-3z + 7 relayed runs (3d, 4a audit-only, Spec, Standards, 4a ship-only, FAA): BT-002 re-queued from blocked, 3d closed G-AC4 (+1 test, RED by mutation, 7ba488a), audit PASS round 1 (spec 0, std 0, watch 3), ship-only: push, draft PR #6, A1 done+closed, Epic Check R, FAA CLEAN, CI gate green, body rebuilt with `Closes #1`/`#2`, ready flip, epic A `in review`, terminal sync MIRROR-OK; S `[SKIP-DEP]`, edge KEEP.
- **stage_checks G3: all 21 PASS.** Agent slip: ci_gate called with `--expect-checks` though the repo has no workflows (ci-gate.md:17 says only then); harmless with the shim's green rollup.
- Findings: F37, F38 (harness), F39 (rig). 3z "Step 3A should mention the FAA" is F39, not a skill defect.
"""
open(p,'w',encoding='utf-8').write(s)
p2='followup-plan.md'
t=open(p2,encoding='utf-8').read()
if '## Notes for following agents' not in t:
    t+="""
## Notes for following agents (live state, 2026-10-28)
- Sandbox in use: `C:\t\l3-4brkfd5x` (github, seeded). `C:\t\l3-e28jbsvr` is superseded (first G1 run).
- **Ship history of PR #6 (BT-002):** the first 3z run blocked BT-002 after 3 `[UNCOVERED]` rounds (F35); issue #2 still carries that `[UNCOVERED]` comment. A second 3z run re-queued it and shipped on a genuine round-1 `[PASS]`. The user allowed shipping imperfect work in this test environment ("we care about the process, not the outcome"); the override clause was in the brief but never fired. Do not treat PR #6's quality as evidence either way.
- Watch items open on BT-002 (non-blocking): KeyError for an unknown flag key vs design "raises nothing"; default-on middle flag semantics; no throughput test.
- Relay protocol: subagent hand-backs are summarized, so dispatches/results go through files `.tmp/relay/dispatch-NN-<role>.md` / `result-NN-<role>.md`; a 4a pass relays its own auditors (incl. the FAA) as sub-dispatches.
- G4 next: `merge_sim.py <root> 6`, then 0b (bucket key brief). `stage_checks mark G4` first.
"""
    open(p2,'w',encoding='utf-8').write(t)
