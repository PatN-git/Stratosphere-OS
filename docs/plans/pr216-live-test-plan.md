---
type: plan
title: PR 216 live AFK test plan v3.0
description: Live in-app staged test plan for PR 216
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-28
version: "3.0.0"
---

# PR #216 live AFK test — plan v3.0 (in-app, staged, local first)

Target: PatN-git/Stratosphere-OS#216 (v5.0.0, head `9a1b511`). Agent under test: **Haiku 5.5, effort high**, run as subagents of this app session. No terminal step, no CLI login, no `claude.exe`.

## What changed from v2.0
- **Started from the app.** Haiku subagents of this session replace the CLI harness driver. That drops the expired `--login` credential and the missing CLI. The harness is still used to build the throwaway sandboxes and for its per-phase assertions.
- **Local first.** The local tracker is all new: `issues.py` and one file per issue on the `<repo>/issues` branch (BT-221, which took 4 audit rounds). GitHub mode did change too: there is no map, and the `--expect` gate is new. But StratOS itself has run in GitHub mode on this branch since BT-199. So GitHub gets a short regression stage.
- **Six stops.** You check, then continue or halt.

## Quota rule
Read with the app's usage tool at the start, and the numbers reported at every stop:

| Limit | At start (2026-10-28) |
|:--|:--|
| 5-hour window | 3% used, resets 17:30 UTC |
| Weekly | 38% used |
| Extra usage | **enabled, $300 cap** |

Because extra usage is on, going over the 5-hour window would spend money. So:
- **Hard stop at 60%** of the 5-hour window. I halt at the next stop and do not start a new stage.
- **No stage starts unless it fits.** I estimate a stage from the measured cost of the earlier stages; if it does not fit, I wait for the reset instead.
- **Opus is the main cost; the Haiku subagents are cheap.** I keep my own share small: subagents return short JSON, and I do not read their full transcripts.

## Containment, the same at every stage
- **Pinned code:** `C:\t\l3src`, a detached worktree at `9a1b511`.
- **Sandboxes are throwaway**, built by the harness's own `env.py` under `C:\t`:
  - a temp HOME;
  - a fake `gh` (no real GitHub);
  - `origin` set to a local bare repo;
  - GitHub tokens scrubbed.
- **Every command goes through `C:\t\l3live\sbx.py <root> -- <cmd>`.** It runs the command with the sandbox's environment, and refuses to run unless `gh` is the fake and the cwd is inside the sandbox. It also logs every call.
- **Subagents get explicit rules:** never run bare `gh`, and never read or write outside their sandbox.
- **Canary:** I snapshot `gh api users/PatN-git/events` and `git ls-remote origin` before and after. Any new event or ref is a failure.

## How a Haiku subagent runs a workflow (AFK)
The brief gives it:
- the sandbox path;
- "read the project's `AGENTS.md`, then follow `.agents/skills/<skill>/SKILL.md` to the end";
- a fixed answer for every gate it may hit (3b approval: mint all drafted slices, ICE 1.0/80%/small/AFK; confirms: yes). It reports every gate it hit;
- "where the skill dispatches a subagent, do that step inline" (AGENTS.md §8 allows this);
- a short JSON return.

After each phase **I run the harness's own checks** (`check_3b`, `check_3d`, `check_0b`, `check_0a_second`) against the sandbox, plus the new-feature checks listed in each stage. I do not trust the subagent's own verdict.

**Fidelity limits, stated in the report:**
- The skill is read from disk, not loaded by the host.
- Nested subagents run inline.
- The subagent's own file tools are bounded by its instructions, not by a temp HOME. The canary is the backstop.

## Stages and stops
| Stage | What | Who | Est. time | STOP |
|:--|:--|:--|:--|:--|
| 1 Setup | Pin the worktree; write `sbx.py` plus a sandbox builder (scratch); run `bash scripts/check.sh` (expect 1001 passed); build two seeded sandboxes (local, github); take the canary baseline | me | 15 min | **A:** baseline result + usage |
| 2 Local scripts | **`issues.py` across git topology:** a feature branch, a `git worktree` and a second clone all see one state; `sync`; a claim race from two worktrees gives exactly one `[CLAIMED]`.<br>**v4 → v5 upgrade:** a v4 install from `origin/main`, then `scaffold --update` (the tracker NOTE), then `issues.py migrate`.<br>**`validate_memory`:** STATUS over 3,000 chars and tracked-STATUS warnings, and the glossary field check | 1 Haiku; I replay every check | 20–30 min | **B** |
| 3 Local live, part 1 | **3b:** slices created with `issues.py`, no `BACKLOG_MAP`, `issues.py check` clean.<br>**3d:** `claim` sets `claimed_by` to the branch, a STATUS session line is written, the commit is on the unit branch | 2 Haiku, one after the other | 30–40 min | **C** |
| 4 Local live, part 2 | **0b:** a resume note in `.memory/resume/<id>.md`, the tracker branch **not** pushed, glossary writer rules followed if a term comes up.<br>**0a-second (from `main`):** follows 3d's branch and reads the resume note | 2 Haiku, one after the other | 20–30 min | **D** |
| 5 GitHub regression | **(a) scripts:** `reconcile.py --expect`, `--expect-file` and `--edges`; removed flags rejected; `ice_read.py candidates`; `pr_body.py unit` fails closed; `tracker_switch.py` moves Stage 4's finished local project to GitHub (dry run, apply, kill + resume, idempotent).<br>**(b) live:** 3b in the github sandbox, whose `--expect` gate passes | 2 Haiku in parallel | 20–30 min | **E:** findings report |
| 6 Teardown | Delete the sandboxes and the pin worktree; compare the canary again | me, after your OK | 5 min | — |

**Total: about 2–2.5 h of wall time**, inside the current 5-hour window if the stop rule holds. These are estimates; real cost is measured at stop A onward.

**At every stop I send:**
- the stage's pass/fail lines;
- any findings, classed as product, harness or env;
- 5-hour and weekly usage;
- whether the next stage fits.

You answer **Continue** or **Halt**. Sandboxes are kept between stops, so a halt can resume later, even after the window resets.

## Not tested (unit tests only, stated in the report)
- **Workflows:** 3a, 3c, 3z, 4a (ship and audit), post-merge sync, 1b/1c/2a/2b, 0d.
- **Real GitHub API behaviour:** the fake `gh` is not GitHub.

## Output
- **Report:** `.tmp/l3live/report.md` in the pinned worktree, also sent to you at stop E.
- **Proposed issues:** listed, not minted.
