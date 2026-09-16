# L3 — lifecycle harness

L1, L2 and L4 all test **onboarding**. L3 tests the **lifecycle**: driving the skills
themselves, end to end, against one subject, with no human present.

Plan: [`docs/plans/l3-lifecycle-e2e-harness-plan.md`](../../docs/plans/l3-lifecycle-e2e-harness-plan.md).

## Status

**Slice 0 is PROVEN.** A live 3-question probe drove `1b-concept-framing` end to end with
no human present, on 2026-09-16:

```
[  1] policy:pick-first  '1'
[  2] proxy              "I meant (a): this is single-actor. There's no config-owner/SDK-consumer split ..."
[  3] policy:pick-first  '1'
[  4] policy:budget      'That is enough questioning - proceed with what you have'
[audit] sufficient=False gaps=[5 specific, well-formed gaps]
[fail] rounds exhausted with gaps still open
```

Every load-bearing assumption held: `1b` **asks** in headless `-p` mode rather than
self-answering, `--resume` carries the conversation, the policy recognises real option
menus, the isolated proxy answers in character from the fixture, the budget fires, and the
auditor returns a structured verdict. The run then failed **correctly** - three questions
cannot produce a sufficient brief, and the auditor said so with specific gaps.

The remaining question is calibration, not viability: how deep a grill produces a brief the
auditor passes. That needs a full-depth run (`--max-questions 10 --max-rounds 2`).

### The one thing still blocking the live spike

**The CLI is not logged in.** `claude auth status` reports `loggedIn: false,
authMethod: "none"` even though the desktop app works — the CLI is a **separate auth
domain**, and copying `~/.claude/.credentials.json` into the temp HOME (what
`run-L2.py:282-285` does) does not authenticate it. Run once, interactively, in your own
terminal:

```powershell
& "$env:LOCALAPPDATA\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code.1.271\claude.exe" auth login
```

Auth lands in `~/.claude`, which every build shares, so one login covers all of them.

### Why that path looks so strange

The desktop app is a **packaged (MSIX) app**, so `%APPDATA%\Claude` is virtualized into its
container. Shell tools spawned *by the app* resolve it; your own terminal and any other
packaged app — including Microsoft Store Python, the only Python installed here — do not,
and report "is not recognized" or `exists → False`. The un-virtualized copy under
`%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\...` is readable and executable from
everywhere, so `_cli_roots()` searches it first. `CLAUDE_CLI` overrides discovery.

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
