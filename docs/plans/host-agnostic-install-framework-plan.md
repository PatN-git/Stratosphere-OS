# Plan — Host-Agnostic Install Framework

**Status:** Proposed — follow-on to PR #107 (v4.0.0). Not scoped into that PR.
**Objective:** Stop hand-maintaining per-host installers. Install StratOS the way the agent-skills ecosystem now does it, so adding a seventh host costs nothing.

---

## 1. Why

v4 expanded StratOS to six *consumption* hosts, but distribution stayed at two *installers*:

| Host | How it gets StratOS today |
|---|---|
| Claude Code | `/plugin marketplace add` → `dist/claude-code` |
| Antigravity | `scripts/install-antigravity.{sh,ps1}` → `cp -rf` into `~/.gemini/` |
| Cursor, Codex, Devin, OpenClaw, Copilot | nothing — they read `.agents/skills/` that `scaffold.py` wrote |

Three problems:
1. **Per-host bash + PowerShell is ours to maintain forever.** ~350 lines across four scripts, doubled for Windows, one pair per host. A seventh host means a fifth and sixth script.
2. **`install-claude-code.{sh,ps1}` is already near-redundant** — the marketplace entry does the same job — and still copies `dist/claude-code/commands/`, a directory v4 retired. The `if [ -d ]` guard makes it silently dead rather than loudly broken.
3. **Two directories named per-host (`dist/antigravity`, `dist/claude-code`) whose `skills/` trees are byte-identical**, which reads like "one per supported host" and is really "one per installer". It misled a reviewer on our own PR.

## 2. What the ecosystem settled on

The convention is a **dual path**: a managed plugin for hosts that have a marketplace, and one generic installer for everyone else.

- `mattpocock/skills`: `claude plugins install mattpocock-skills` (managed, read-only, auto-updating) **or** `npx skills@latest add mattpocock/skills` (editable, copied into your repo, re-syncable via `npx skills update`).
- That second command is [vercel-labs/skills](https://github.com/vercel-labs/skills) (`skills.sh`) — a host-agnostic installer that already places skills for **antigravity, claude-code, codex, cursor, github-copilot, gemini-cli, opencode, windsurf, amp, droid, goose, kilo, kiro, roo, trae** and more, and lets the user pick which skills and which agents.

Nobody is hand-writing per-host copy scripts anymore. Per-host placement is the installer's job, not the skill package's.

## 3. The split this forces (and why it's an improvement)

`scaffold.py` is ~1,198 lines and skill placement is only part of it. The rest is project bootstrap: constitution (`AGENTS.md`/`CLAUDE.md`/`GEMINI.md`), `.memory/` templates, `.agents/rules/`, `docs/`, `.gitignore`/`.gitattributes`, bundled scripts.

| Concern | Owner after this work |
|---|---|
| Get 26 skills onto the machine / into the repo | `skills.sh` package (+ Claude Code marketplace, kept) |
| Bootstrap a project (constitution, memory, rules, docs) | `stratosphere-setup` skill / `scaffold.py` |

Today both do placement. Separating them is the real win; dropping the installers is the visible one.

## 4. Scope sketch

- **S1 — `skills.sh` package manifest.** Make the repo installable via `npx skills add PatN-git/Stratosphere-OS`. Verify how it handles per-skill `references/`, our leading-digit names (`0a-start-session`), and `disable-model-invocation` / `triggers` / `agents/openai.yaml` sidecars. **Unknown until spiked — this is the gate on the whole plan.**
- **S2 — Retire the Claude Code installers.** Marketplace is the documented path; delete `install-claude-code.{sh,ps1}` and the dead `commands/` copy. Update README + `tests/install-harness`.
- **S3 — Retire the Antigravity installers** once S1 proves `skills.sh` places Antigravity correctly. Until then they stay: Antigravity has no marketplace and this is its only route.
- **S4 — `dist/` naming.** Either collapse to one bundle + a placement manifest, or rename to `dist/installers/<name>/` and document the two axes. Touches `check.sh` drift check, both install scripts, the harness.
- **S5 — Docs + upgrade path.** `stratosphere-update` must keep working for projects installed the old way; state the migration.

## 5. Risks / open questions

- **S1 may fail.** If `skills.sh` cannot carry the HITL sidecars or the per-skill `references/` layout, the whole plan reduces to S2 + S4 and we keep the Antigravity script. Spike before committing to the rest.
- **Third-party dependency.** `skills.sh` becomes a link in our install chain. The Claude Code marketplace path stays as the non-`npx` fallback, so it is never the only route.
- **`sync_skills.py` overlap.** We already fetch third-party skills from `external-skills.json`. If `skills.sh` does that better, that is a second thing to retire — out of scope here, worth noting.

## 6. Not in scope
- Changing what any skill *says*. This is distribution only.
- The Copilot path (`.github/copilot/skills/`), which stays a scaffold concern.
