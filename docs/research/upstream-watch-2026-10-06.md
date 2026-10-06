---
type: research
title: "Upstream watch 2026-10-06"
description: "Baseline upstream-watch run over 8 weeks (2026-08-11 to 2026-10-06), all defined hosts: 14 items, one silent BREAKING (Codex untrusted-project AGENTS.md), two obsolete workarounds."
status: stable
generated:
  by: upstream-watch
  at: "2026-10-06T16:10:00Z"
---

Baseline run, no previous last_run

Window extended on request from the last ~2 weeks to 8 weeks (2026-08-11 to 2026-10-06), and widened from Claude Code + Antigravity to every host in AGENTS.md §8. Part 1 below covers Claude Code, Antigravity, `@google/design.md` and Stitch (items 1-7); Part 2 covers Cursor, Codex, Copilot, Gemini CLI, Jules, Devin and OpenClaw (items O1-O7). Highest: Codex 0.150.0 silently stops loading `AGENTS.md` in untrusted projects (O1). Decisions on what to change: `docs/proposals/upstream-watch-2026-10-adjustments.md`.

# Part 1: Claude Code, Antigravity, design.md, Stitch

## Ranked items

### 1. Both hosts now read AGENTS.md natively: Claude Code 2.1.277 (2026-09-18, with 2.1.281 for Bedrock/Vertex/gateways); Antigravity rules docs list `AGENTS.md`/`GEMINI.md` as natively active, and app 2.11.0 (2026-08-26) added `@path` imports inside AGENTS.md and rule files
- **Affected:** `AGENTS.md:69` and `src/constitution/AGENTS.md:69` ("the two that don't [read AGENTS.md natively] get a two-line pointer — CLAUDE.md and GEMINI.md"), `CLAUDE.md`, `GEMINI.md`, `src/scripts/scaffold.py:1473` (copies the three constitution files).
- **Impact:** OBSOLETES A WORKAROUND (partial). The Claude fallback applies only when a project has no `CLAUDE.md` and is a `/config` toggle ("Project instructions"), so the pointers still matter for versions before 2.1.277 and for `CLAUDE.md`'s "Check .agents/skills" line.
- **Action (S):** correct the §8 sentence only; keep both pointer files.
- **Community research worthwhile? no.**

### 2. Antigravity native plugin install: app 2.18.1 (2026-09-28) Customizations tab + marketplace, plugin-named slash commands; CLI `agy plugin install | import | validate | link`; plugins can carry `skills/`, `agents/`, `rules/`, `hooks.json`, `mcp_config.json` (CLI 1.1.15 added a plugin `rules` key)
- **Affected:** `build/build.py:277` (`write_antigravity_manifest` emits a manifest-only `dist/antigravity/plugin.json`), README Track D, `scripts/install-antigravity-bridge.*`, the "Antigravity / copied-skills Install" branch of `src/commands/stratosphere-update/SKILL.md:71`, `src/scripts/check_suite.py:122`.
- **Impact:** OPPORTUNITY. Verified locally with `agy` 1.1.4: `agy plugin validate dist/antigravity` passes but reports `skills: skipped (not found)`. The same `plugin.json` next to a copy of `dist/skills` as `skills/` reports `skills: 27 processed`. So the current Antigravity manifest ships zero skills. [UNVERIFIED]: whether the app/CLI marketplace can add this GitHub repo as a source, and the marketplace manifest format.
- **Action (M):** emit a plugin-shaped `dist/antigravity/` (manifest + `skills/`), document `agy plugin install <path>` as an extra Track, and keep Track D until the marketplace route is proven.
- **Community research worthwhile? yes** — "agy plugin link marketplace GitHub repo", "agy plugin import claude marketplace.json compatibility", "Antigravity plugin marketplace submit".

### 3. Antigravity CLI uses different global dirs than the app (docs): CLI skills `~/.gemini/antigravity-cli/skills/`, CLI-installed plugins `~/.gemini/antigravity-cli/plugins/<name>/`; app/IDE skills `~/.gemini/config/skills/`
- **Affected:** `scripts/install-antigravity-bridge.sh` (`TARGET="$HOME/.gemini/config/skills"`, and the `.ps1` twin), `src/commands/stratosphere-update/SKILL.md:30-32,68-72`, `src/commands/stratosphere-setup/SKILL.md:90-92`, `src/scripts/check_suite.py:122,154`.
- **Impact:** WATCH, verify first. If the CLI does not also read `~/.gemini/config/skills`, Track D installs are invisible to CLI-only users, and the update flow's path detection would miss a plugin installed via `agy plugin install`. Not proven: this machine's `agy` is 1.1.4 (latest 1.2.14), has StratOS skills only under `~/.gemini/config/skills`, no `~/.gemini/antigravity-cli`, and no skills-list subcommand.
- **Action (S):** marker-skill test per dir with `agy -p`; record the result in README Track D.
- **Community research worthwhile? yes** — "antigravity-cli skills directory ~/.gemini/antigravity-cli/skills", "agy global skills not discovered config/skills", "vercel-labs/skills antigravity-cli path".

### 4. Plugin validators on both hosts: Claude Code `plugin validate` (2.1.233 bare `.claude/skills` SKILL.md frontmatter parse, 2.1.259 `--json`, 2.1.281 MCP/hook/`${CLAUDE_PLUGIN_ROOT}` checks, 2.1.283 name checks); `agy plugin validate`
- **Affected:** `tests/framework/test_dist_bundle.py:142` (cites validator behavior but no test or CI step runs it; `.github/workflows/build-guard.yml` has no `plugin validate`), `.claude-plugin/marketplace.json`.
- **Impact:** OPPORTUNITY. A deterministic gate that checks what each host really loads. `claude` is not on PATH on this machine, so the Claude validator is [UNVERIFIED] against this repo.
- **Action (S):** one local run now; add to `build-guard.yml` only if installing the CLI in CI is cheap.
- **Community research worthwhile? no.**

### 5. Skill-library cost and menu levers: Claude Code `/skill-doctor` (2.1.261: unused skills and their context cost); Antigravity CLI 1.1.12 (2026-08-11) `disable-slash-command: true` frontmatter (hides a skill from `/` and `/name`, model can still invoke it)
- **Affected:** `.agents/skills/` (36 skills), `dist/skills/` (27), skill frontmatter emitted by `build/build.py`.
- **Impact:** OPPORTUNITY (token efficiency). `/skill-doctor` needs no repo change. `disable-slash-command` is cosmetic (no token saving).
- **Action (S):** run `/skill-doctor` once and prune by evidence; do not add the frontmatter flag.
- **Community research worthwhile? no.**

### 6. Hooks have a defined shape on both hosts; `src/skills/plan-html/hooks.json` matches neither
- **Source:** Antigravity hooks docs (workspace `.agents/hooks.json`, global `~/.gemini/config/hooks.json`, or a plugin's root `hooks.json`; events `PreToolUse|PostToolUse|PreInvocation|PostInvocation|Stop` as arrays of `{type:"command", command, timeout}`); Claude Code plugin hooks live in `hooks/hooks.json` (2.1.274 entry). Claude Mods and gating-hook validation (2.1.287 / 2.1.290) are Claude-only.
- **Affected:** `src/skills/plan-html/hooks.json` (`"Stop": {description, command}`, inside a skill dir). No code in `src/ build/ tests/ scripts/` references it. Local `agy plugin validate` reports hooks `skipped (not found)` for a plugin root without a root `hooks.json`.
- **Impact:** WATCH, cleanup. The file claims a Stop hook that no host loads.
- **Action (S):** delete it (or move to a proper plugin-root `hooks.json` if a real gate is wanted).
- **Community research worthwhile? no.**

### 7. Stitch (forum only; no official changelog; blog.google Labs page had no Stitch post) [COMMUNITY, UNVERIFIED]
- **Change:** user reports of API-key creation failing (2026-09-27, 2026-09-30), "Stitch Design Breaking in AI Studio when Exported" (2026-08-18), a themed-component-catalog feature request (2026-08-18); official "Stitch Prompt Guide" (2026-09-28).
- **Affected:** `src/workflows/2b-interface-design.md:56,68` (DESIGN.md as Stitch Design System; the MCP fallback that reads the Stitch API key).
- **Impact:** WATCH.
- **Action:** none, watch. Re-check the forum next run.
- **Community research worthwhile? yes** — "Stitch API key failed to create", "Stitch DESIGN.md import design system", "Stitch MCP get_screen".

## Checked, no StratOS hit (Part 1)
- Antigravity rules budget (app 2.17.0, CLI 1.2.7): 20K tokens for always-on rules, 24 KB per file, `.agents/rules/` direct `.md` children only. StratOS always-on rules are `memory-protocol` 6.6 KB + `output-mode` 2.7 KB (~2.3K tokens est.); `okf-protocol` is glob-scoped, 9.8 KB.
- CLI 1.2.10 scan change applies to `skills.json`/`plugins.json` `path` entries (direct children only, like `.agents/skills/`); StratOS's one-level `.agents/skills/<name>/` layout is unaffected.
- Claude Code 2.1.288 glob-rule fix (`.claude/rules` `paths:` now load on Write/Edit): benefits `okf-protocol.md`; no in-repo workaround existed.
- Custom-agent features (`omitClaudeMd` 2.1.271; Antigravity `inheritCustomizations`, `rules:`): StratOS ships no named agents. Claude Code 2.1.286 `claude purge`, 2.1.285 settings changes, `/workflows` (2.1.268): no repo hits.
- `@google/design.md` pin 0.4.0 equals latest; no commits on main since the 2026-07-27 release.

## Sources reviewed (Part 1)
- claude_code: 2.1.228 to 2.1.291 (2026-08-11 to 2026-10-06), complete. The web changelog truncates, so entries came from the official `anthropics/claude-code` `CHANGELOG.md` via `gh api`; dates from `npm view @anthropic-ai/claude-code time`.
- antigravity_app: 2.7.1 to 2.19.1 (2026-08-11 to 2026-09-30). antigravity_cli: 1.1.12 to 1.2.14 (2026-08-11 to 2026-09-30). The WebFetch result truncates at 2.12.0 / 1.2.3, so the same official page was fetched with `curl --compressed` and parsed locally (a deviation from "WebFetch only", first-party URL, no third-party source). Antigravity SDK 0.1.11 to 0.1.17 skimmed (no StratOS surface). CLI 1.0.0 to 1.0.3 are dated "January 1, 2026" on the page: [UNVERIFIED], outside the window.
- Antigravity docs pages read for plugins, skills, rules and hooks (official, same domain): current-state docs, not dated.
- design_md: 0.1.0 to 0.4.0, no release in the extended window (npm and `gh api` agree).
- stitch: forum topics 2026-08-16 to 2026-10-05; no Google announcements; `stitch.withgoogle.com/docs` returned no readable content; 1 of 2 corroboration lookups used.
- Local checks: `agy` 1.1.4 (`plugin validate` spike in `.tmp/`); `claude` CLI not on PATH.

# Part 2: Cursor, Codex, Copilot, Gemini CLI, Jules, Devin, OpenClaw

Window 2026-08-11 to 2026-10-06. Five read-only subagents read the official sources; I re-checked the findings that would change the repo. "✔" = I re-read it against an official source; "reported" = subagent only, not re-fetched.

## Ranked items

### O1. Codex 0.150.0 (2026-08-26): untrusted projects no longer supply project-level `AGENTS.md` (PR #39837, merged 2026-08-21). Gemini CLI v0.59.0 (2026-09-08): fail-closed workspace trust (#29099)
- **Evidence:** ✔ both statements are in the official release notes (`openai/codex` rust-v0.150.0; `google-gemini/gemini-cli` v0.59.0). Reported: on Gemini CLI, skills and just-in-time `GEMINI.md` also load only in a trusted workspace; on Codex, repo `.agents/skills` roots are not trust-gated (from source, untested). Codex 0.149.0 (2026-08-20) also makes `AGENTS.md` reads obey the filesystem sandbox (#39653 ✔).
- **Affected:** the constitution `AGENTS.md` as always-on rules on Codex and Gemini CLI. `README.md`, `src/commands/stratosphere-setup/SKILL.md` and `src/constitution/AGENTS.md` never mention project trust (grep: no hit).
- **Impact:** BREAKING (silent). An untrusted Codex project still gets the skills but not the constitution (precedence, security, git protocol), with no error.
- **Action (S):** state the "trust this folder" prerequisite for Codex and Gemini CLI in README requirements and the setup summary.
- **Community research worthwhile? yes** — "Codex untrusted project AGENTS.md not loaded", "Codex trust project config.toml", "Gemini CLI trusted folders workspace trust AGENTS.md".

### O2. GitHub Copilot reads `.github/skills/`, `.claude/skills/`, `.agents/skills/` (project) and `~/.copilot/skills`, `~/.claude/skills`, `~/.agents/skills` (personal); `.github/copilot/skills/` is in no official source
- **Evidence:** ✔ VS Code agent-skills page (stamped 9/30/2026) lists exactly those directories and does not mention `.github/copilot/skills/`; it lists `disable-model-invocation` and `user-invocable` as supported fields. Reported: the Copilot CLI and cloud-agent docs and every release note in the window agree, and the CLI honors `disable-model-invocation`.
- **Affected:** `src/scripts/scaffold.py:341-345,378,466,568` (copies the whole bundle to `.github/copilot/skills/`), `tests/framework/test_skill_conformance.py:145-146` (requires the twin, forbids `.github/skills`), `tests/framework/test_update_flow.py:1946-1977`, `tests/install-harness/run-L1.ps1:51-52`, `AGENTS.md:71` ("Copilot, not `.github/skills/`, a Devin path"). StratOS's own `docs/research/host-agnostic-skill-distribution.md:162` already says the opposite.
- **Impact:** OBSOLETES A WORKAROUND. The twin is never read and duplicates ~1 MB of skills per project (`dist/skills` is 1,085 KB); Copilot already reads `.agents/skills`.
- **Action (M):** stop writing the twin; make the update flow prune existing twins; fix the three tests and the §8 line. Add Copilot to the §8 user-only table (VS Code honors the field).
- **Community research worthwhile? no.**

### O3. Gemini CLI loads only `GEMINI.md` by default; `AGENTS.md` loads only when `context.fileName` lists it
- **Evidence:** ✔ geminicli.com GEMINI.md docs and `DEFAULT_CONTEXT_FILENAME = 'GEMINI.md'` in `google-gemini/gemini-cli`. Reported: docs list only `name` and `description` as skill frontmatter, so Gemini CLI has no user-only enforcement; `.agents/skills/` is read there (alias added Feb 2026, before the window). No change in the window.
- **Affected:** `AGENTS.md:69` and `src/constitution/AGENTS.md:69` list Gemini CLI among hosts that read `AGENTS.md` natively; `GEMINI.md` (313 B) is what Gemini CLI loads (and Antigravity). The §8 user-only table has no Gemini CLI or Copilot row.
- **Impact:** WATCH. A false line in the always-loaded constitution; no functional break because `GEMINI.md` points at `AGENTS.md`. It also means `GEMINI.md` serves two hosts, so Part 1 item 1's reasoning must not be read as "GEMINI.md is redundant".
- **Action (S):** fold into the §8 correction.
- **Community research worthwhile? no.**

### O4. Plugin formats converge on one layout: root `plugin.json` plus `skills/` (Agent Plugins 1.0)
- **Evidence:** reported: GA in VS Code 1.133 and Copilot CLI/SDK (2026-08-12 changelog; spec dated 2026-08-06); Devin CLI v3000.5.20 (2026-08-21) compatibility and, from 2026-09-30, `devin plugins install owner/repo` accepting skills-only repos; Cursor loads the format; Codex documents a root `plugin.json` and `.agents/plugins/marketplace.json`; OpenClaw `git:owner/repo@ref` and `skills-sh:` installs. ✔ My Antigravity spike (Part 1, item 2) shows `agy plugin validate` accepts exactly this layout.
- **Affected:** `build/build.py:277-283` (manifest-only `dist/antigravity/plugin.json`), `.claude-plugin/marketplace.json`.
- **Impact:** OPPORTUNITY. One plugin-shaped bundle could serve four or more hosts, not only Antigravity. [UNVERIFIED]: the spec text and whether each host installs this layout from the GitHub repo. Cursor needs a `.cursor-plugin/marketplace.json` for repo imports (reported).
- **Action (M):** widen Part 1 item 2's action into "one plugin-shaped root", then spike Copilot and Devin installs.
- **Community research worthwhile? yes** — "Agent Plugins 1.0 specification plugin.json", "devin plugins install skills-only repo", "copilot plugin install from GitHub repo skills".

### O5. Jules API v1alpha (discovery doc revision 20261004): `sessions.activities.list` takes `parent, pageToken, filter, pageSize`, no `createTime`; new `PullRequest.headRef/baseRef`, `SourceContext.workingBranch`, `Session.archived`, methods `archive|unarchive|delete`
- **Evidence:** ✔ read from the live official discovery endpoint. When each field landed is [UNVERIFIED] (no per-change dates); the docs still say alpha and the official changelog's newest entry is 2026-03-09 (reported). Nothing was called live; no key used.
- **Affected:** `src/experimental/jules-dispatch/jules_api.py:86-89` (sends `createTime`; ✔ no caller in the pack, so dormant), `CONTRACT.md` (pins only `url/title/description`, lists the poll as `?pageSize=&createTime=`).
- **Impact:** WATCH (latent defect in dead code) and OPPORTUNITY (`headRef/baseRef` could replace the "do not match on branch prefix" caveat; `sessions.delete` for E2E teardown). `outputs[].pullRequest.url`, the auth header, the `state` and `automationMode` enums are unchanged.
- **Action (S):** remove the unused `since` argument or switch to `filter=create_time > "<RFC3339>"`; add the new fields to `CONTRACT.md`.
- **Community research worthwhile? no.**

### O6. Instruction-size ceilings differ by host
- **Evidence:** reported: Devin injects only the first 16 KiB of each `AGENTS.md` (docs, undated); Codex `project_doc_max_bytes` is 32 KiB. ✔ Antigravity: 24 KB per rule file. ✔ Measured here: `AGENTS.md` is 9,865 B (~6 KB under Devin's cap); the 36 installed skill descriptions total 8,259 characters (~2.1K tokens). A reported Codex skills budget (`[skills].max_context_tokens`, 2% of context, at most 10K) is not in the 0.149.0 release notes I read: [UNVERIFIED].
- **Affected:** `AGENTS.md`, `src/constitution/AGENTS.md`, skill descriptions.
- **Impact:** WATCH. Headroom is fine today; the constitution cannot grow past ~16 KiB without being cut on Devin.
- **Action (S, optional):** a one-line test that `src/constitution/AGENTS.md` stays under 15 KiB.
- **Community research worthwhile? no.**

### O7. Cursor, Devin, OpenClaw: no breaking change to skills, frontmatter or `AGENTS.md` in the window
- **Evidence (all reported):** Cursor reads `.agents/skills/` and `.cursor/skills/`, honors `disable-model-invocation`, adds `paths` scoping, and since CLI v2026.08.11 skill scans skip hidden dot-directories below a root (`.agents/skills` itself is a documented root); Cursor does not copy global `~/.agents/skills` to cloud agents (project-level installs reach them). Devin: `triggers: ["user"]` is still the only user-only switch (no `disable-model-invocation`), six project skill directories incl. `.agents/skills`. OpenClaw: `disable-model-invocation` hides a skill from the model but `$skill-name` still invokes it; `.agents/skills` precedence unchanged; the Sep 8 breaking changes are runtime-only (Node version, workshop collections).
- **Affected:** `build/build.py:177-194` (Codex sidecar, `triggers`), skill frontmatter emission.
- **Impact:** WATCH. Confirms the current per-host mechanisms; no action.
- **Community research worthwhile? no.**

## Checked, no StratOS hit (Part 2)
- Codex: sidecar schema unchanged (`policy.allow_implicit_invocation`; reported that an unparseable `openai.yaml` fails open); matches `build/build.py:177-194`. `codex mcp-server` removal and the `untrusted` approval-policy retirement: no repo references.
- Copilot CLI removed `copilot plugins install --skill/--scope` and `/plugins` (v1.0.81 to v1.0.88, reported): no StratOS script calls them (grep).
- Hooks changed on every host (Cursor, Codex, Copilot, Devin); Cursor and Copilot also import Claude Code hooks, which risks double-firing. StratOS ships no live hooks, so no hit.
- Worktrees: Codex `--worktree` (default 0.156.0, detached HEAD), Copilot CLI `/worktree` and experimental `git.worktreeSymlinkFolders`, OpenClaw managed worktrees. The §8 note "worktrees lack untracked deps" stays true; Copilot's setting only partly eases it.
- Skill catalog size: 36 descriptions (~2.1K tokens) fit every reported host budget.

## Sources reviewed (Part 2)
- cursor: cursor.com/changelog (Aug 13 to Sep 23, 2026), docs release notes (IDE 3.19 to 3.23, CLI v2026.08.11 to v2026.09.28), skills/rules/hooks/subagents/plugins docs (undated). No live test.
- codex: changelog (redirects to learn.chatgpt.com; 2026-08-11 to 2026-10-05, read with curl because WebFetch truncated), 28 stable `openai/codex` releases (0.148.0 to 0.160.1), docs pages, `openai/skills` (deprecated 2026-06-22, no change in window). ✔ release notes 0.149.0 and 0.150.0 re-read by me.
- copilot: github.blog Copilot changelog (2026-08-11 to 2026-10-02), VS Code 1.132 to 1.140, Copilot CLI v1.0.79 to v1.0.92, `cli/cli` v2.94 to v2.102, VS Code and GitHub docs (mostly undated). ✔ VS Code skills page re-read by me.
- gemini_cli: stable v0.55.1 to v0.62.0 via `gh api`, geminicli.com docs ("last updated" stamps all predate the window). ✔ GEMINI.md docs page and v0.59.0 notes re-read by me.
- jules: jules.google changelog (newest entry 2026-03-09), API docs (REST reference last updated 2025-10-07; v1beta/v1 pages 404), live v1alpha discovery doc revision 20261004 ✔ re-read by me. Jules Tools CLI changelog not reviewed.
- devin: release notes (Aug 12 to Oct 5, 2026) and CLI changelog v3000.4.25 to v3000.11.3, read with curl (WebFetch dated an entry wrongly); docs pages undated. `cognition.ai/blog` not reviewed.
- openclaw: docs and 20 releases v2026.8.1-beta.2 to v2026.10.1-beta.1 via `gh api`; extended-stable backports are published out of version order, so version-to-date mapping for v2026.6.35, v2026.7.35 and v2026.8.33-35 is [UNVERIFIED].

## Plan (BREAKING and OBSOLETES items present; proposed only, the human mints issues via /3b)
One feature PR, three slices committed in this order; full wording and reasons in `docs/proposals/upstream-watch-2026-10-adjustments.md`.
1. Host hygiene. Acceptance: `AGENTS.md` §8 no longer claims Claude Code or Antigravity skip `AGENTS.md`, states that Gemini CLI loads `GEMINI.md`, lists Copilot's real skill paths and adds Copilot and Gemini CLI rows to the user-only table; README and the setup summary name the Codex (>= 0.150.0) and Gemini CLI (>= 0.59.0) project-trust step (O1); `src/skills/plan-html/hooks.json` is gone; `jules_api.py` sends no `createTime` and `CONTRACT.md` pins the new fields (O5); build and validate green.
2. Stop writing the Copilot `.github/copilot/skills/` twin (O2). Acceptance: `SKILL_TARGETS` is `[".agents/skills"]`, `get_twin_paths` has no skills branch, the three test sites updated, suite green, a scratch scaffold run creates no twin. Existing twins (cleantechhub, and this repo if present) are removed by a one-time manual `git rm -r`, not by migration code.
3. Plugin-shaped bundle and validators (Part 1 items 2-4, O4). Acceptance: the Antigravity CLI directory check is recorded in README Track D; `agy plugin validate` on the bundle reports `skills: <bundle count> processed`; the README documents each host route whose install spike passed; Track D retained; `RELEASING.md` lists both validator commands.
