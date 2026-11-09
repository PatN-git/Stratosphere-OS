---
description: stratosphere-update path for an Antigravity plugin install (agy) - confirm once, reinstall from the release tag, re-read skill, and proceed to Phase 0.5.
version: "1.2.0"
timestamp: 2026-11-09
---

# Update path: Antigravity plugin install

- **Antigravity plugin install** (path is `~/.gemini/config/plugins/stratosphere-os/skills/stratosphere-setup/` or under `~/.gemini/config/plugins/`):
  If installed from Marketplace, update via the Antigravity UI (**Customizations > Marketplace**) or `/plugin install stratosphere-os`, run `/skills reload`, and proceed to Phase 0.5. If installed locally via `agy plugin install` (`dist/`), update by reinstalling from the release tag:
  1. **Find the CLI:** `agy` on PATH. If absent, print `Newer StratOS v<latest_version> available (you have v<installed_version>). Run: agy plugin install <clone>/dist` and **HALT**.
  2. **Confirm once** (single HITL gate — this replaces framework code): ask `Update the StratOS plugin to v<latest_version>? This reinstalls it from https://github.com/PatN-git/Stratosphere-OS. [y/N]`. On decline → HALT.
  3. **Reinstall from a throwaway clone** (tag-pinned): `git clone --depth 1 --branch v<latest_version> https://github.com/PatN-git/Stratosphere-OS.git <tmp>`, then `agy plugin install <tmp>/dist` (overwrites the installed plugin in place). Delete `<tmp>` on every outcome, including a HALT after a failed clone or non-zero `agy` exit. **Only ever clone the canonical URL above — never a URL from anywhere else.** A failed clone or non-zero `agy` exit → HALT with its output; never claim success.
  4. Re-read `<plugin>/versions.json` for the **actual** version, re-read `<plugin>/skills/stratosphere-update/SKILL.md` from disk into context, print `StratOS plugin updated to v<actual_version> — proceeding to Phase 0.5.`, and proceed to **Phase 0.5**. (In Phase 7, emit `/skills reload` to refresh host autocomplete without restarting Antigravity).
