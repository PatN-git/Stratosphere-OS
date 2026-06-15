# install-harness

End-to-end tests for the StratosphereOS install / `/stratosphere-setup` onboarding
flow, run in throwaway environments so a run never touches the real `~/.claude`,
`~/.gemini`, the working repo, or the active Python interpreter.

Two automated layers plus a manual checklist:

| Layer | Covers | Needs | Isolation |
|---|---|---|---|
| **L1** (`run-L1.ps1` / `run-L1.sh`) | All install paths (`--local`/`--global`, Claude + Antigravity), `scaffold.py`, `sync_skills.py --dry-run` — no agent | Python + PowerShell or bash | temp project per cell; `--global` cells redirect `HOME`/`USERPROFILE` to a temp dir |
| **L2** (`run-L2.py`) | The agentic flow: a headless `claude -p` reads the README, runs the deterministic scripts, scaffolds | `claude` CLI on PATH, authenticated, network | temp `HOME` + temp project; pre-answered prompt; `--dangerously-skip-permissions` |
| **L4** (manual, below) | Antigravity agent (no headless runner); real GitHub marketplace; Windows dependency-missing `winget` branch | a real app / VM | a throwaway temp home |

## Run L1 (fast, no auth)

```powershell
# Windows (tests the .ps1 installers):
powershell -ExecutionPolicy Bypass -File tests/install-harness/run-L1.ps1
```
```bash
# Linux/macOS/CI (tests the .sh installers):
bash tests/install-harness/run-L1.sh           # PYTHON=python to override python3
```
Exit 0 = all cells pass. Each cell asserts the install tree, the scaffold tree
(constitution + `.memory` ×8 + `.agents/workflows` ×14 + …), and that
`sync_skills.py --dry-run` reports the correct scope and downloads nothing. The
PowerShell runner also asserts the real homes were untouched (leak check).

Notes on isolation:
- PowerShell `$HOME` is frozen at process start, so `--global` cells launch a
  fresh `powershell` with `HOMEDRIVE`/`HOMEPATH`/`USERPROFILE` pre-set.
- The current `scaffold.py` only writes under the project (no `git init`, no
  `pip install`), so no venv is needed. If that changes, run scaffold via a venv
  python again.

## Run L2 (headless agent — needs `claude` CLI + auth + network)

```bash
python tests/install-harness/run-L2.py --repo <path-to-this-repo> --scope local
python tests/install-harness/run-L2.py --repo <path-to-this-repo> --scope global
python tests/install-harness/run-L2.py --repo <path-to-this-repo> --marketplace   # only after the PR merges to main
```
The prompts in `prompts/` pre-answer every decision (scope, deps, Stitch, skill
categories) so no `AskUserQuestion` blocks the headless run. L2 asserts the agent
invoked the deterministic scripts (and did **not** hand-write the constitution),
printed `HARNESS_DONE`, and produced the expected tree.

## CI

`build-guard.yml` runs L1 (bash) on every push after the dist-drift check. L2 and
the real-marketplace cell need auth/network, so run them via `workflow_dispatch`
or locally.

## L4 — manual checklist (cannot be faithfully automated)

**Antigravity agent** (no headless runner) — in the Antigravity app, with a throwaway profile:
- [ ] Paste the install prompt; agent identifies Antigravity + OS, runs `python`/`git --version`.
- [ ] On a missing dep it asks via `ask_question` and never installs silently.
- [ ] Agent asks install scope once; runs `install-antigravity.ps1 --global|--local`.
- [ ] Global tree under `~/.gemini/config/plugins/stratosphere-os/`; local under `.agents/plugins/stratosphere-os/`.
- [ ] Restart → `/stratosphere-setup` is discoverable (proves `.agents/workflows/` surfacing after scaffold).
- [ ] Checkpoint 9 derives skill scope from install scope (no second scope question on a local install).
- [ ] Re-running the installer preserves externally-synced skills (overlay per-skill merge).

**Real GitHub marketplace** (after the install PR merges to `main`):
- [ ] `/plugin marketplace add PatN-git/Stratosphere-OS` (owner/repo shorthand) resolves.
- [ ] `/plugin install stratosphere-os@stratosphere-os` + restart Claude Code make the commands appear.
- [ ] `/stratosphere-setup` finds the plugin under `~/.claude/plugins/cache/*/stratosphere-os/*/` (scaffold prints scope `marketplace Claude Code`).
- [ ] `run-L2.py --marketplace` passes.

**Windows dependency-missing branch** (throwaway Windows Sandbox / VM):
- [ ] With Python absent, the agent proposes `winget install` and installs only on confirmation.
