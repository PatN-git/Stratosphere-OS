# install-harness

End-to-end tests for the StratosphereOS install / `/stratosphere-setup` onboarding
flow, run in throwaway environments so a run never touches the real `~/.claude`,
`~/.gemini`, the working repo, or the active Python interpreter.

Two automated layers plus a manual checklist:

| Layer | Covers | Needs | Isolation |
|---|---|---|---|
| **L1** (`run-L1.ps1` / `run-L1.sh`) | Track B plain-copy install of `dist/skills` (`.claude/skills`, `.agents/skills` × local/global) + `scaffold.py` + `sync_skills.py --dry-run`; Track A `npx skills add ./dist/skills --copy -y` (same 2×2 matrix); Track D Antigravity bridge `--target` — no agent | Python + PowerShell or bash; Node/`npx` + network for Track A (SKIPs without) | temp project per cell; `--global` cells redirect `HOME`/`USERPROFILE` to a temp dir |
| **L2** (`run-L2.py`) | The agentic flow (Claude Code only): a headless `claude -p` reads the README, runs the deterministic scripts, scaffolds | `claude` CLI on PATH, authenticated, network | temp `HOME` + temp project; pre-answered prompt; `--dangerously-skip-permissions` |
| **L4** (manual, below) | Antigravity agent (no headless runner); real GitHub marketplace; Windows dependency-missing `winget` branch | a real app / VM | a throwaway temp home |

## Run L1 (fast, no auth)

```powershell
# Windows (PowerShell runner):
powershell -ExecutionPolicy Bypass -File tests/install-harness/run-L1.ps1
```
```bash
# Linux/macOS/CI (bash runner):
bash tests/install-harness/run-L1.sh           # PYTHON=python to override python3
```
Exit 0 = all cells pass. Each cell asserts the install tree, the scaffold tree
(constitution + `.memory` ×9 + `.agents/skills` ×26 + …), and that
`sync_skills.py --dry-run` reports the correct scope and downloads nothing. The
PowerShell runner also asserts the real homes were untouched (leak check).

Install tracks covered (each asserts the same bundle tree: 26 skills, 22 HITL
sidecars, `stratosphere-setup` scaffolder payload):
- **Track B** — plain copy (`cp -r` / `Copy-Item`), plus scaffold + sync.
- **Track A** — `npx skills add ./dist/skills --copy -y`; no `-a` flag → `.agents/skills`,
  `-a claude-code` → `.claude/skills`, `-g` → temp `HOME`. A local path source means the
  only network need is npx fetching the `skills` CLI. If `npx` is missing or the CLI
  can't be fetched, the cell prints `SKIP` (not a failure).
- **Track D** — `scripts/install-antigravity-bridge.{sh,ps1} --target <tmp>`, then a re-run
  proving foreign skills survive and stale files in shipped skills are dropped.

Notes on isolation:
- PowerShell `$HOME` is frozen at process start, so `--global` cells launch a
  fresh `powershell` with `HOMEDRIVE`/`HOMEPATH`/`USERPROFILE` pre-set.
- The current `scaffold.py` only writes under the project (no `git init`, no
  `pip install`), so no venv is needed. If that changes, run scaffold via a venv
  python again.

## Run L2 (headless agent — needs `claude` CLI + auth + network)

```bash
python tests/install-harness/run-L2.py --repo <path-to-this-repo> --scope local   # claude-code only
python tests/install-harness/run-L2.py --repo <path-to-this-repo> --marketplace   # only after the PR merges to main
```
The prompts in `prompts/` pre-answer every decision (scope, deps, Stitch, skill
categories) so no `AskUserQuestion` blocks the headless run. L2 asserts the agent
invoked the deterministic scripts (and did **not** hand-write the constitution),
printed `HARNESS_DONE`, and produced the expected tree.

## CI

`build-guard.yml` runs L1 (bash) on every push after the dist-drift check, with Node set
up so Track A runs rather than skips. L2 and
the real-marketplace cell need auth/network, so run them via `workflow_dispatch`
or locally.

## L4 — manual checklist (cannot be faithfully automated)

**Antigravity agent** (no headless runner — `run-L2.py` is Claude Code only; the bridge's file
placement is covered by L1 Track D) — in the Antigravity app, with a throwaway profile:
- [ ] Paste the install prompt; agent identifies Antigravity + OS, runs `python`/`git --version`.
- [ ] On a missing dep it asks via `ask_question` and never installs silently.
- [ ] Agent asks install scope once; runs `scripts/install-antigravity-bridge.ps1` (global) or copies `dist/skills` to `.agents/skills` (local).
- [ ] Global skills land under `~/.gemini/config/skills/`; local under `.agents/skills/`.
- [ ] Restart → `/stratosphere-setup` is discoverable (proves `.agents/workflows/` surfacing after scaffold).
- [ ] Checkpoint 9 derives skill scope from install scope (no second scope question on a local install).
- [ ] Re-running the bridge preserves externally-synced skills (overlay per-skill merge).

**Real GitHub marketplace** (after the install PR merges to `main`):
- [ ] `/plugin marketplace add PatN-git/Stratosphere-OS` (owner/repo shorthand) resolves.
- [ ] `/plugin install stratosphere-os@stratosphere-os` + restart Claude Code make the commands appear.
- [ ] `/stratosphere-setup` finds the plugin under `~/.claude/plugins/cache/*/stratosphere-os/*/` (scaffold prints scope `marketplace Claude Code`).
- [ ] `run-L2.py --marketplace` passes.

**Windows dependency-missing branch** (throwaway Windows Sandbox / VM):
- [ ] With Python absent, the agent proposes `winget install` and installs only on confirmation.
