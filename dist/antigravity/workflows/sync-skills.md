---
name: sync-skills
type: workflow
description: Fetch third-party skill packs on demand from external-skills.json into the project's .agents/skills/.
version: "1.0.1"
timestamp: 2026-06-17
---

# Sync Skills

Third-party skills are **not bundled** with the plugin. They are fetched on demand from their upstream GitHub repos, driven by the registry at the plugin's `external-skills.json` (the single source of truth). This command wraps the deterministic `sync_skills.py` fetcher.

## Usage

Run from the **project root**. `sync_skills.py` lives in the installed plugin (not the project) and reads the plugin's `external-skills.json` automatically; invoke it with the plugin path — `<plugin>` is `~/.claude/plugins/stratosphere-os/` on Claude Code, or the global staged plugin dir `~/.gemini/config/plugins/stratosphere-os/` on Antigravity.

```bash
# See what's available (asterisk = installed by default)
python <plugin>/scripts/sync_skills.py --list

# System skills (code-simplifier, skill-creator)
python <plugin>/scripts/sync_skills.py --default

# By category: database | web | mobile | design | system
python <plugin>/scripts/sync_skills.py --category database web

# By exact name
python <plugin>/scripts/sync_skills.py --only supabase impeccable

# Everything, or preview first
python <plugin>/scripts/sync_skills.py --all --dry-run
```

Each skill lands at its registry `targetPath` (e.g. `.agents/skills/supabase`).

## Behaviour

- **Read-only registry.** The script never edits `external-skills.json`; update sources there by hand.
- **Surgical extract.** Only the `subPath` inside each upstream repo zip is extracted.
- **Safe skips.** Entries whose `repoZipUrl` is empty/`TODO`/`PENDING`/`N/A` are reported and skipped. A `0 files matched` warning means the `subPath` is wrong.
- **Exit code.** Non-zero only on a hard download/extract failure, so the installer can detect problems.

## When the installer calls this

Checkpoint 8 maps the user's "yes" answers to categories and invokes this with `--default` plus the chosen `--category` flags.
