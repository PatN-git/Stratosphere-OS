---
name: sync-skills
description: "Fetch third-party skill packs on demand from external-skills.json into the project's .agents/skills/. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.1.0"
timestamp: 2026-10-08
---

# Sync Skills

Third-party skills are **not bundled** with the skill suite. They are fetched on demand from their upstream GitHub repos, driven by the registry at the setup skill's `external-skills.json` (the single source of truth). This command wraps the deterministic `sync_skills.py` fetcher.

## Usage

Run from the **project root**. `sync_skills.py` lives in the installed `stratosphere-setup` skill (not the project) and reads that skill's `external-skills.json` automatically; invoke it with that skill's path — `<plugin>` is the first of these that contains `scripts/sync_skills.py`. Check the running host's own group first; only if none matches, try the other group:

- **Claude Code:** `./.claude/skills/stratosphere-setup/`, `~/.claude/skills/stratosphere-setup/`, marketplace cache `~/.claude/plugins/cache/*/stratosphere-os/*/dist/skills/stratosphere-setup/` (glob — newest version directory)
- **Antigravity and other hosts:** `./.agents/skills/stratosphere-setup/`, `~/.gemini/config/plugins/stratosphere-os/skills/stratosphere-setup/` (`agy plugin install dist`), `~/.gemini/config/skills/stratosphere-setup/`, `~/.agents/skills/stratosphere-setup/`

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
- **No `SKILL.md`, no overwrite.** A pack without `SKILL.md` is skipped with a warning (the existing copy is kept) unless its registry entry names a `skillFile` to generate it from.
- **Exit code.** Non-zero only on a hard download/extract failure, so the installer can detect problems.

## When the installer calls this

Checkpoint 8 maps the user's "yes" answers to categories and invokes this with `--default` plus the chosen `--category` flags.
