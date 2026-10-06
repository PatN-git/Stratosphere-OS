---
type: reference
title: Host Matrix
description: Per-host facts StratOS depends on (AGENTS.md loading, skill directories, manual-only fields, trust, version floors) and why the pointer files stay. Dev-only; never shipped; kept out of the always-loaded constitution.
version: "1.0.0"
generated:
  by: Claude
  at: "2026-10-06"
---

# Host Matrix

As of 2026-10-06. Evidence and sources: `docs/research/upstream-watch-2026-10-06.md` (re-check when the watermarks in `docs/research/.upstream-watch.json` move). "reported" = from release notes or docs not re-verified here.

`AGENTS.md` §8 stays host-name-free on purpose: it is loaded in every session of every project, so each host fact there costs tokens everywhere. Every per-host fact lives here, read only when authoring or auditing skills.

## AGENTS.md loading and pointer files
| Host | Loads `AGENTS.md` | Pointer file | Trust |
|---|---|---|---|
| Cursor, Devin, Copilot, Jules, Antigravity | natively | none | — |
| Codex | natively | none | >= 0.150.0 loads project `AGENTS.md` only once the project is trusted |
| Claude Code | only when the project has no `CLAUDE.md` (>= 2.1.277; a user setting) | `CLAUDE.md` (`@AGENTS.md`) | — |
| Gemini CLI | no: loads `GEMINI.md` unless `context.fileName` lists `AGENTS.md` | `GEMINI.md` | >= 0.59.0 fails closed on untrusted workspaces (reported: skills and `GEMINI.md` too) |

- **Keep both pointer files.** The Claude fallback applies only without a `CLAUDE.md` and is a setting; older hosts need the pointer; `GEMINI.md` serves two hosts (Gemini CLI and Antigravity); the saving is under 100 tokens; scaffold treats them as never-overwritten constitution files.
- **Trust cannot be stated in `AGENTS.md`**: an untrusted project never loads it, so the note could not reach the agent. It lives in the README install section and the setup skill (Checkpoint 1); a skill cannot read host trust state, so it is documented, not checked.

## Skills
| Host | Project skill dirs | Manual-only field |
|---|---|---|
| Claude Code | `.claude/skills/`, `~/.claude/skills/` (never `.agents/skills/`) | `disable-model-invocation` |
| Cursor, OpenClaw | `.agents/skills/` | `disable-model-invocation` |
| Copilot (VS Code) | `.agents/skills/`, `.github/skills/`, `.claude/skills/` | `disable-model-invocation` |
| Devin | `.agents/skills/` | `triggers: ["user"]` |
| Codex | `.agents/skills/` | `agents/openai.yaml` sidecar |
| Antigravity | `.agents/skills/`; app global `~/.gemini/config/skills/` | none: `description` only |
| Gemini CLI | `.agents/skills/` (reported) | none: `description` only |

- **Observed (`agy` 1.3.0, one run each):** the Antigravity CLI read a skill in `~/.gemini/config/skills/` and not one in `~/.gemini/antigravity-cli/skills/`, whatever its docs say.
- **Copilot** reads `.agents/skills/` natively, so StratOS writes no second copy (`SKILL_TARGETS` is `[".agents/skills"]`); `.github/skills/` would double-list.
- **Claude Code** skills arrive by marketplace, `npx skills add -a claude-code`, or a plain copy; the marketplace plugin also registers the bundled suite.
- **Antigravity** honours none of the manual-only fields, so every lifecycle `description` restates its user-only status (a prompt-level signal, not enforcement).

## Glob-scoped rules
`.agents/rules/` (Antigravity `trigger`/`globs`) and `.claude/rules/` (Claude Code `paths:`; >= 2.1.288 loads them when a file is written). Contract: `okf-protocol.md` §2.1.

## Adding or changing a host
1. Does it load `AGENTS.md` natively? If not, add a pointer file, never a copy of the rules.
2. Which skill directories does it read? Add it to `SKILL_TARGETS` only if `.agents/skills/` is not among them.
3. Which field makes a skill manual-only? Add the row above; if none, the `description` must say so.
4. Does it gate project instructions on trust? Update the README install note and setup Checkpoint 1.
5. Record version floors here, move the watermark, and keep `AGENTS.md` §8 free of host names (`tests/framework/test_host_hygiene.py` enforces it).
