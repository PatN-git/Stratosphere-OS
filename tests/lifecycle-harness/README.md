# L3 — lifecycle harness

L1, L2 and L4 all test **onboarding**. L3 tests the **lifecycle**: driving the skills
themselves, end to end, against one subject, with no human present.

Plan: [`docs/plans/l3-lifecycle-e2e-harness-plan.md`](../../docs/plans/l3-lifecycle-e2e-harness-plan.md).

## Status

**Slices 0–3 are done; Slice 4 is built and awaiting its first live run.** A full-depth run drove `1b-concept-framing` to a
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

**Authenticate the harness's own credential store, once:**

```bash
python tests/lifecycle-harness/run-L3.py --login
```

This is not optional politeness. A run refreshes whatever credential it is given, and the
provider **rotates the refresh token** when it does — the rotated token is written into the
temp HOME and deleted at teardown, leaving the original superseded. On 2026-09-16 exactly
that happened: a smoke run refreshed, the next run got *"OAuth session expired and could not
be refreshed"*, and the CLI then blanked its copy. One run had silently invalidated the
developer's own CLI login. The harness now keeps its own credential at
`~/.l3-harness/.credentials.json`, writes each rotation back into it, and never writes to
`~/.claude`. A run with no usable credential refuses in seconds, naming `--login`, rather
than dying mid-phase.

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
python tests/lifecycle-harness/run-L3.py          # build/prove/remove the environment; no agent, no network
python tests/lifecycle-harness/spike_1b.py        # exit 2 = claude unavailable, nothing proven
python -m pytest tests/test_l3_responder.py tests/test_l3_env.py tests/test_l3_run.py -q
```

`--handoff` runs every phase at minimum depth: 3 turns per round, 1 round, a 600s budget
per phase, and `1b`'s auditor demoted to advisory. It answers whether each phase starts from
the last one's artifacts and leaves what the next one reads — the chain, not the depth. A
finding from a hand-off run is a finding about the hand-off; artifact quality needs a
full-depth run, and the run prints which mode it is in.

`run-L3.py --env-only` costs nothing to run: it drives no agent and reaches no network. It builds
the throwaway, asserts the four things every later phase takes on trust — no GitHub
credentials in the child environment, every remote resolving inside the temp root, the
project scaffolded, and its `.memory/` passing `validate_memory.py` — then removes it.
A dirty working repo warns rather than refusing, because the manifest compares before
against after and pre-existing dirt is a constant on both sides.

## Pieces

| File | Role |
|:---|:---|
| `responder.py` | Answers as the user. Deterministic policy for structured gates, isolated proxy for the rest, hard ceiling on total replies. |
| `session.py` | Multi-turn `claude` driver (`--resume` per turn), plus `ClaudeProxy` and `ClaudeAuditor`, each a fresh session in an empty directory. |
| `env.py` | Containment: temp HOME, temp project, stripped remotes, scrubbed tokens, guaranteed teardown. |
| `driver.py` | Slice 4: drives one phase from its prompt to its sentinel. A missing sentinel is a failure, never a skip. |
| `assertions.py` | Slice 4: a checker per phase. Claims the transcript makes (`[MIRROR-OK]`, tests green, lint clean) are re-run here rather than believed. |
| `shims/gh_shim.py` | Slice 2: a `gh` that answers from a JSON store. `auth status` must succeed or `reconcile.py` degrades to `[local-only]` and never emits `[MIRROR-OK]`. Unknown subcommands fail loudly. |
| `fixture/topic.md` | The pinned subject. The proxy sees this and nothing else. |
| `prompts/` + `prompts.py` | Slice 3: the opening turn of each phase and its `L3-<PHASE>-COMPLETE` sentinel. The responder handles everything after it. No prompt carries the fixture. |
| `gates.md` | Every HALT/ASK point and its answer, so "every gate is answered" is falsifiable. |
| `run-L3.py` | Slice 1: the CLI. Builds the contained environment, asserts E1/E7/E2 and the scaffold, tears it down. Drives no agent yet. |
| `spike_1b.py` | Slice 0's spike: drive `1b` alone and see whether it terminates. |

## Two things worth knowing before extending this

**The proxy must stay blind.** It is given the fixture and the question — never the draft
brief. If it could read what the agent wrote, it would be approving its own work, which is
exactly what `1b:64` forbids. `test_responder_cannot_leak_a_brief_because_it_never_holds_one`
fails the moment `Responder` grows a field that would allow it.

**A `.cmd` shim does not intercept a Python caller on Windows.** `CreateProcess` appends
only `.exe` when it searches `PATH`; `PATHEXT` is a shell feature. So `shutil.which('gh')`
finds `gh.cmd` and `subprocess.run(['gh', ...])` — which is what `reconcile.py` does —
walks past it to the real `gh`, authenticated from the OS keyring where scrubbing
`GH_TOKEN` cannot reach. `env.py` mints a real `gh.exe` launcher and `assert_gh_is_shimmed`
proves the interception from inside a child carrying the run's environment. It cannot be
proven from the harness process: on Windows the executable search uses the *calling*
process's `PATH`, not the one passed in `env=`.

**The E1 manifest compares names, not contents.** `~/.gemini` holds ~67k files and
Antigravity writes into it while the harness runs, so a content-sensitive fingerprint fails
on the developer's IDE rather than on a real breach — it did exactly that during Slice 0,
then passed on retry, which is worse than failing. Containment is the redirected HOME, the
scrubbed environment and the stripped remotes; the manifest is a backstop, and
`assert_no_install` names the one breach worth asserting outright.
