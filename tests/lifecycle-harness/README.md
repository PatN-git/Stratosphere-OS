# L3 — lifecycle harness

L1, L2 and L4 all test **onboarding**. L3 tests the **lifecycle**: driving the skills
themselves, end to end, against one subject, with no human present.

Plan: [`docs/plans/l3-lifecycle-e2e-harness-plan.md`](../../docs/plans/l3-lifecycle-e2e-harness-plan.md).

## Status

**Slice 0 built. The live spike is unproven** — the `claude` CLI is not installed on the
development machine, so `1b` has not actually been driven yet. Everything that does not
need the CLI is tested (29 tests, `test_l3_responder.py` and `test_l3_env.py`).

That split is deliberate. The parts where a bug would be silent — a gate answered
non-deterministically, the proxy handed the draft brief, a grill that never ends, a run
that reaches the real GitHub — are all verifiable without an agent, and are verified. What
remains unproven is whether a real `1b` conversation terminates under this policy, which is
the question Slice 0 exists to answer.

```bash
python tests/lifecycle-harness/spike_1b.py        # exit 2 = claude unavailable, nothing proven
python -m pytest tests/test_l3_responder.py tests/test_l3_env.py -q
```

## Pieces

| File | Role |
|:---|:---|
| `responder.py` | Answers as the user. Deterministic policy for structured gates, isolated proxy for the rest, hard ceiling on total replies. |
| `session.py` | Multi-turn `claude` driver (`--resume` per turn), plus `ClaudeProxy` and `ClaudeAuditor`, each a fresh session in an empty directory. |
| `env.py` | Containment: temp HOME, temp project, stripped remotes, scrubbed tokens, guaranteed teardown. |
| `fixture/topic.md` | The pinned subject. The proxy sees this and nothing else. |
| `gates.md` | Every HALT/ASK point and its answer, so "every gate is answered" is falsifiable. |
| `spike_1b.py` | Slice 0's spike: drive `1b` alone and see whether it terminates. |

## Two things worth knowing before extending this

**The proxy must stay blind.** It is given the fixture and the question — never the draft
brief. If it could read what the agent wrote, it would be approving its own work, which is
exactly what `1b:64` forbids. `test_responder_cannot_leak_a_brief_because_it_never_holds_one`
fails the moment `Responder` grows a field that would allow it.

**The E1 manifest compares names, not contents.** `~/.gemini` holds ~67k files and
Antigravity writes into it while the harness runs, so a content-sensitive fingerprint fails
on the developer's IDE rather than on a real breach — it did exactly that during Slice 0,
then passed on retry, which is worse than failing. Containment is the redirected HOME, the
scrubbed environment and the stripped remotes; the manifest is a backstop, and
`assert_no_install` names the one breach worth asserting outright.
