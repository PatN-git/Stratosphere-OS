p='findings.md'
s=open(p,encoding='utf-8').read()
row=("| F41 | B1 | product (docs) | minor | glossary-entry-rules.md: `Avoid:` \"required whenever any were rejected (always in 1b and 1c), omitted otherwise\" contradicts itself when 1b promotes a term with no rejected synonym. 1b wrote G-001 Ruleset with no `Avoid:` (none was rejected); validate_memory is clean either way. | not fixed. Proposed: drop \"(always in 1b and 1c)\" or say \"1b/1c always ask for rejected synonyms\". |\n")
s=s.replace("## Learnings", row+"## Learnings",1)
s+="""
## Follow-up B1 — 1b relay, local tracker (2026-10-28)
- Fresh unseeded local sandbox `C:\\t\\l3-1o9xjlx2`. Haiku-1b + one persistent blind proxy (topic.md only), relayed through files `relay/1b-out-NN.md` / `user-NN.md` (verbatim, never paraphrased). Turns 1–3 proxy, turn 4 scripted "That's enough, write it up", turn 5 scripted confirmations. ~1.0M Haiku tokens, ~25 min.
- Grill quality: proxy stayed on the fixture, pushed back once (malformed ruleset → defaults, not rejection); 1b adopted the fixture vocabulary (Flag, Ruleset, Rule, Segment, Bucketing key, Evaluation; Avoid toggle/experiment/bare targeting/user ID); framing B (correctness) chosen; RAT run inline (self-review) — it picked "ruleset reproduces the if-ladder" rather than the fixture's eventual-consistency risk.
- **After turn 4 ("enough"): GLOSSARY.md hash unchanged (PASS)**; 1b treated "enough" as ending the grill, not as approval, wrote the draft brief (Phase 5, allowed before the gate) and presented it with the unanswered gates as blocking questions. Not-consent rule held.
- After turn 5: G-001 Ruleset and G-002 Bucketing key written in rule format, `Source:` = the brief, G-002 `Avoid: user ID`; G-001 has no `Avoid:` (F41); harness `check_1b` **[ok]**; validate_memory clean; work file deleted; no commit (1b has none).
- Plan deviation: turn-4 assert "docs/discovery unchanged" was too strict (1b Phase 5 writes the draft before the user gate); kept the GLOSSARY hash assert only.
- Haiku skill_defects triaged: plan-html has no skip path at Phase 7 step 4 (it is a mandatory render; the skip came from my brief — not a defect); Skeptical Challenger "subagent" vs inline (AGENTS §8 says every subagent step must also run inline — not a defect); `version: <plugin version>` source = F30 class; Phase 0 gate overlap and "enough" vs approval — wording nits.
"""
open(p,'w',encoding='utf-8').write(s)
