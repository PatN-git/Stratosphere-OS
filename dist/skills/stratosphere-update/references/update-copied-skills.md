---
description: stratosphere-update path for a copied-skills install (Antigravity or Claude Code) - confirm once, refresh from a tag-pinned clone via the bridge, then HALT.
version: "1.0.0"
timestamp: 2026-10-07
---

# Update path: Antigravity / copied-skills install

- **Antigravity / copied-skills Install** (path is under `~/.gemini/config/skills/`, `./.agents/skills/`, `~/.agents/skills/`, `~/.claude/skills/` or `./.claude/skills/` — Antigravity and Claude Code copies alike):
  The installed skills are a copy (bridge, Track A or Track B), not a git checkout — **self-update them from the canonical repo** so the user never re-installs by hand. `<skills-dir>` is the parent directory of `<plugin>` (e.g. `~/.gemini/config/skills`, `~/.claude/skills` or `<project>/.agents/skills`).
  1. **Confirm once** (single HITL gate — this replaces framework code): ask `Update the StratOS skills to v<latest_version>? This refreshes <skills-dir> from https://github.com/PatN-git/Stratosphere-OS. [y/N]`. On decline → HALT.
  2. **Refresh the skill bytes from a throwaway clone** (never mutate the user's own clone; deterministic and tag-pinned): `git clone --depth 1 --branch v<latest_version> https://github.com/PatN-git/Stratosphere-OS.git <tmp>`, then run its bridge against the same directory: `bash <tmp>/scripts/install-antigravity-bridge.sh --target <skills-dir>` (on Windows use `powershell -File <tmp>/scripts/install-antigravity-bridge.ps1 --target <skills-dir>`). Delete `<tmp>` on every outcome, including a HALT after a failed clone or bridge exit. **Only ever clone the canonical URL above — never a URL from anywhere else.** If the clone fails (offline / tag absent), HALT with the git error — **never** reinstall stale bytes or claim success.
  3. Re-read `<plugin>/versions.json` for the **actual** installed version and print `StratOS plugin updated to v<actual_version> — reload plugins and re-run /stratosphere-update.` verbatim, then **HALT**. (The re-run executes the *new* workflow + scaffold cleanly — avoids self-modifying the running workflow mid-flight.)
