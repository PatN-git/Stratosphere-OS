---
description: stratosphere-update path for a Claude Marketplace Cache install - confirm once, drive the claude plugin CLI, re-read skill, and proceed to Phase 0.5.
version: "1.1.0"
timestamp: 2026-11-09
---

# Update path: Claude Marketplace Cache

- **Claude Marketplace Cache** (path starts with `~/.claude/plugins/cache/`):
  Do **NOT** touch the cache folder directly and do **NOT** attempt any git operations on it. The interactive `/plugin` dialog is unavailable in the Claude desktop app, so drive the non-interactive CLI instead:
  1. **Find the CLI:** `claude` on PATH, else the newest `claude-code/<ver>/claude.exe` under the desktop app package (`%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude\claude-code\`).
  2. **Confirm once** (single HITL gate): `Update the StratOS plugin to v<latest_version> via the Claude Code plugin CLI? [y/N]`. On decline → HALT.
  3. Run `claude plugin marketplace update stratosphere-os`, then `claude plugin update stratosphere-os`. Non-zero exit → HALT with its output; never claim success.
  4. Re-read `<plugin>/skills/stratosphere-update/SKILL.md` from disk into context, print `StratOS plugin update to v<latest_version> applied — proceeding to Phase 0.5.`, and proceed to **Phase 0.5**. (In Phase 7, emit `/reload-plugins` to refresh host cache without restarting Claude Code).
  If no CLI is found, print the following notification verbatim instead:
  `Newer StratOS v<latest_version> available (you have v<installed_version>). Update via:`
  `  /plugin marketplace update stratosphere-os`
  `then /reload-plugins (or enable auto-update for this marketplace), re-read <plugin>/skills/stratosphere-update/SKILL.md, and proceed to Phase 0.5.`
  Then **HALT** execution. (If the user explicitly instructs to proceed anyway, continue against the stale plugin with a loud warning to Phase 0.5).
