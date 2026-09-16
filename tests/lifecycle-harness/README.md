# L3 — lifecycle harness

L1, L2 and L4 all test **onboarding**. L3 tests the **lifecycle**: driving the skills
themselves, end to end, against one subject, with no human present.

Plan: [`docs/plans/l3-lifecycle-e2e-harness-plan.md`](../../docs/plans/l3-lifecycle-e2e-harness-plan.md).

## Status

**Slice 0 is PROVEN and calibrated.** A full-depth run drove `1b-concept-framing` to a
sufficient discovery brief with no human present, 2026-09-16:

```
[models] driver=opus proxy=haiku auditor=sonnet
[  1] policy:not-yet     'Not yet - we have not explored this enough. Keep asking...'
[  2] proxy              "This is progressive rollout and entitlement, not kill-switch..."
[  3] proxy              "I'll flag one lock over-read, then give you my reads..."
[  4] proxy              "No external doc - this briefing is our complete spec..."
[  5] policy:not-yet     'Not yet - we have not explored this enough...'
[  6] proxy              'Q41 is in and foundational - ruleset-level CI tests...'
[audit] sufficient=False gaps=[2]
[  7] proxy              '**Q54 - S3.** If rules belong in the declarative artifact...'
[audit] sufficient=True gaps=[]
[pass] local-feature-flag-evaluation.md written in 7 replies, 2 round(s)
```

**7 turns, 2 rounds, ~23 minutes.** The brief was 148 lines and the vocabulary *extended*
the fixture rather than parroting it - `1b` coined `Subject`, `Reason`, `bucket_by` and
deploy-time propagation, with an `Avoid:` list of its own. The round mechanism did real
work: the auditor failed round 1 on two gaps, one of which was sharp enough to be worth
quoting - *"has the user explicitly confirmed the F2 framing over F1/F3, rather than it
being the author's recommendation?"*

### What the numbers mean

- **10 turns per round is ample.** Seven were enough, including one round of remediation.
- **The budget counts TURNS, not questions.** `1b` batches: the proxy's answers refer to
  "Q41" and "Q54", so seven turns carried dozens of questions. `--max-questions` keeps the
  familiar name, but turns are what it bounds.
- **The number is model-specific.** Calibrated with `driver=opus`. A different driver asks
  differently and needs re-calibrating - see the plan, section 6.

### Two defects the run found, both in the harness

1. **The responder was ending the grill itself.** `policy:confirm` matched `1b`'s primary
   stop gate (`1b:64`), so the first attempt answered "Yes, proceed." and finished in three
   replies without ever calling the proxy or the auditor. While turns remain, a request to
   stop is now refused (`policy:not-yet`).
2. **The scaffold never ran.** `scaffold.py` was invoked with an invented `--yes` flag;
   argparse exited 2; `capture_output` without `check` swallowed it. `1b` was driven against
   a project with no `.agents/` and no `.memory/` - and still produced a valid brief, which
   is why nothing looked wrong. Now `check`ed and asserted against `SCAFFOLD_MARKERS`.

Both are the class of bug this harness exists to surface, found on its own first outing.

### Running it

The CLI is a **separate auth domain from the desktop app** - `claude auth status` can report
`loggedIn: false` while the app works perfectly, and copying `~/.claude/.credentials.json`
into the temp HOME (what `run-L2.py:282-285` does) does **not** authenticate it. If a run
fails with "Not logged in", sign the CLI in once, interactively, from your own terminal:

```powershell
$exe = Get-ChildItem "$env:LOCALAPPDATA\Packages\Claude_*\LocalCache\Roaming\Claude\claude-code\*\claude.exe" | Sort-Object LastWriteTime | Select-Object -Last 1
& $exe.FullName auth login
```

Auth lands in `~/.claude`, which every build shares, so one login covers all of them. The
command is written version-agnostically on purpose: hard-coding a version breaks on the next
app update.

### Why the CLI path looks so strange

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
