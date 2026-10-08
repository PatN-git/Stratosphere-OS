---
description: stratosphere-update path for an Antigravity plugin install (agy) - confirm once, reinstall from the release tag, then HALT.
version: "1.0.0"
timestamp: 2026-10-07
---

# Update path: Antigravity plugin install

- **Antigravity plugin install** (path is `~/.gemini/config/plugins/stratosphere-os/skills/stratosphere-setup/`):
  `agy plugin install` copied `dist/` there and did not record its source, so update by reinstalling from the release tag.
  1. **Find the CLI:** `agy` on PATH. If absent, print `Newer StratOS v<latest_version> available (you have v<installed_version>). Run: agy plugin install <clone>/dist` and **HALT**.
  2. **Confirm once** (single HITL gate — this replaces framework code): ask `Update the StratOS plugin to v<latest_version>? This reinstalls it from https://github.com/PatN-git/Stratosphere-OS. [y/N]`. On decline → HALT.
  3. **Reinstall from a throwaway clone** (tag-pinned): `git clone --depth 1 --branch v<latest_version> https://github.com/PatN-git/Stratosphere-OS.git <tmp>`, then `agy plugin install <tmp>/dist` (overwrites the installed plugin in place). Delete `<tmp>` on every outcome, including a HALT after a failed clone or non-zero `agy` exit. **Only ever clone the canonical URL above — never a URL from anywhere else.** A failed clone or non-zero `agy` exit → HALT with its output; never claim success.
  4. Re-read `<plugin>/versions.json` for the **actual** version and print `StratOS plugin updated to v<actual_version> — restart Antigravity and re-run /stratosphere-update.` verbatim, then **HALT**.
