---
name: upstream-watch-2026-10-adjustments
description: What StratOS should and should not adjust after the 8-week upstream review of every defined host (2026-08-11 to 2026-10-06), with the reason for each call.
type: proposal
version: "4.4.0"
generated:
  by: Claude
  at: "2026-10-06"
---

# Proposal: StratOS adjustments after the Aug-Oct 2026 upstream review

**Status:** Open proposal, nothing implemented. Evidence and sources: `docs/research/upstream-watch-2026-10-06.md`. "R1-R7" are its Part 1 items (Claude Code, Antigravity, design.md, Stitch); "O1-O7" are its Part 2 items (Cursor, Codex, Copilot, Gemini CLI, Jules, Devin, OpenClaw). Issues are minted by the human via `/3b`.

**Bottom line:** eight adjustments (A-H), one of them urgent in effect (O1: Codex silently drops `AGENTS.md` in untrusted projects), and a list of things to deliberately not do. All ship in **one feature PR** because they come from the same upstream run; the PR is three slices committed in order (see "Order of work"). Most are documentation or dead-code removal; the plugin-shaped bundle (D) is the only build-output change.

## Adjust

### A. Correct the `AGENTS.md` §8 host table (R1, O2, O3) — do, effort S
- **What:** `src/constitution/AGENTS.md:69-71` is wrong in four places: (1) it says Claude Code and Antigravity don't read `AGENTS.md` (Claude Code >= 2.1.277 does when there is no `CLAUDE.md`; Antigravity's docs list it as active); (2) it says Gemini CLI reads `AGENTS.md` natively (default context file is `GEMINI.md` only); (3) it says Copilot reads `.github/copilot/skills/` and that `.github/skills/` is "a Devin path" (VS Code docs of 2026-09-30 list `.github/skills/`, `.claude/skills/`, `.agents/skills/`); (4) the user-only table has no Copilot row (VS Code honors `disable-model-invocation`) and no Gemini CLI row (no enforcement). Reword, and state the version floors: Claude Code >= 2.1.277 for the fallback, >= 2.1.288 for glob rules to load when a new file is written.
- **Why:** this is the always-loaded constitution and the reason `CLAUDE.md`/`GEMINI.md` exist; a wrong reason invites deleting them. The Gemini CLI fact matters most: `GEMINI.md` is its only loader, so it serves two hosts.
- **Why not more:** no code. One per-file OKF version bump, in the PR that carries it.

### B. Delete `src/skills/plan-html/hooks.json` (R6) — do, effort S
- **What:** the `Stop` shape matches no host (Antigravity wants arrays of `{type, command, timeout}` in `.agents/hooks.json` or a plugin-root `hooks.json`); it sits in a skill dir where nothing loads it; nothing references it.
- **Why:** it advertises a verification step that never runs and ships in the bundle.
- **Why not make it real:** an echo-only hook costs tokens per stop and gates nothing. A real gate should be a deterministic check.

### C. Settle the Antigravity CLI directory question (R3) — do first, effort S
- **What:** the docs say CLI global skills live in `~/.gemini/antigravity-cli/skills/` and CLI-installed plugins in `~/.gemini/antigravity-cli/plugins/`, while the app/IDE uses `~/.gemini/config/skills/` (our bridge target). Test with a marker skill in each directory and `agy -p` on `agy` >= 1.2.x (this machine has 1.1.4; latest is 1.2.14).
- **Outcomes:** CLI reads both: document it. CLI reads only its own dir: add a second bridge target and extend the path lists in `stratosphere-update/SKILL.md:30-32,68-72`, `stratosphere-setup/SKILL.md:90-92`, `check_suite.py:122,154`.
- **Why first:** if it reads only its own, Track D gives CLI-only users nothing.

### D. One plugin-shaped bundle for several hosts (R2, O4) — do after C, effort M
- **What:** `build/build.py:277` writes a manifest-only `dist/antigravity/plugin.json`; `agy plugin validate` confirms zero skills, while the same manifest plus `skills/` validates with 27 processed. Four other hosts report converging on that layout (Copilot GA 2026-08-12, Devin from 2026-09-30, Cursor, Codex, plus OpenClaw git installs). Make `dist/` itself the plugin root: `plugin.json` at `dist/plugin.json` beside the existing `dist/skills/`, with no second skills tree (a copy under `dist/antigravity` would trip five BT-118 guards and reverse that decision), then spike an install on Antigravity, Copilot and Devin and document each route that works.
- **Why:** a native install and update path per host, and the update flow stops needing a throwaway clone plus bridge for them.
- **Scope inside the single PR:** emit the bundle, get `agy plugin validate` green, document the Antigravity route. Copilot and Devin install routes go into the README only if their spike passes during the PR; otherwise they are listed as follow-ups, so the PR never waits on a host that cannot be tested here.
- **Why not replace Track D or the Claude marketplace yet:** the spec text and each host's install from this GitHub repo are [UNVERIFIED]; the bundle has 27 skills but a project can hold 36 (external skills arrive via `/sync-skills`); plugin updates and plugin-prefixed slash names are undocumented, and README promises `/<name>`. Keep Track D until an install-update-reinstall round trip passes per host.

### E. Run the plugin validators in the release checklist, not CI (R4) — do, effort S
- **What:** add `claude plugin validate .` and `agy plugin validate <bundle>` to `RELEASING.md` as a manual pre-release step.
- **Why:** both check what the host really loads, which `tests/framework/test_dist_bundle.py` only approximates.
- **Why not CI now:** `claude` is not on this machine's PATH, so CI needs an install step of unmeasured cost. Revisit once D exists and a checklist run has caught something.

### F. Document the project-trust prerequisite for Codex and Gemini CLI (O1) — do, effort S
- **What:** add one requirements line (README) and one setup-summary line: trust the folder in Codex (>= 0.150.0) and Gemini CLI (>= 0.59.0), otherwise `AGENTS.md` is not loaded.
- **Why:** it fails silently. The skills still appear, so users believe StratOS is active while precedence, security and git rules are absent. Verified in the official release notes of both hosts.
- **Why not enforce it:** a skill cannot read the host's trust state. A first-turn self-check in `/0a-start-session` ("can you see the constitution?") would add tokens to every session; documentation is the smallest reversible step.

### G. Stop writing the Copilot `.github/copilot/skills/` twin (O2) — do, effort S
- **What:** set `SKILL_TARGETS` to `[".agents/skills"]` (`scaffold.py:345`), drop the skills branch of `get_twin_paths` (`scaffold.py:457-466`), and update `test_skill_conformance.py:145-146`, the twin assertions in `test_update_flow.py:1946-1977` and `tests/install-harness/run-L1.ps1:51-52`.
- **Existing twins: one-time manual clean, no migration code.** Per the owner the twin exists in only two projects (cleantechhub and this one); in this checkout `.github/copilot/skills/` is absent and untracked (checked), so confirm where it lives first. Delete it in each with `git rm -r .github/copilot/skills` after updating. That is cheaper than prune logic, which the update flow only runs for orphaned canonical skills (`scaffold.py:1130-1160`) and which would never fire for a removed target. This also fits the rule that one-off migrations stay out of the framework.
- **Why:** no official source reads that directory; Copilot reads `.agents/skills` natively, so nothing is lost. It removes ~1 MB of duplicate skills per project and a test that asserts something false. StratOS's own 2026-09-25 research already reached this conclusion.
- **Why not skip it:** the cost of leaving it is small (disk, noise), so this is cleanup, not a defect. With two affected projects it is cheap enough to finish in the same PR as A so docs and code agree.

### H. Jules pack: remove the dead poll marker, pin the new fields (O5) — do, effort S
- **What:** `jules_api.py:86-89` sends `createTime`, which the live discovery doc (revision 20261004) no longer lists; nothing calls it. Remove the unused `since` argument (or use `filter=create_time > "<RFC3339>"`) and add `headRef`, `baseRef`, `workingBranch`, `archive/delete` to `CONTRACT.md`.
- **Why:** the contract file is the pinned source of truth for the pack, and `headRef/baseRef` could later replace the "never match the branch prefix" workaround.
- **Why not more:** the pack is experimental and untested live in this review (no key used). Do not adopt `sessions.delete` teardown or `headRef` matching until a live E2E run confirms them.

## Do, no repo change
- Run `/skill-doctor` (Claude Code 2.1.261) once over the installed skills and prune on the evidence. Measured here: 36 skills carry ~2.1K tokens of descriptions, within every reported host budget, so expect small wins.

## Do not adjust

| Upstream change | Decision | Why not |
|---|---|---|
| Delete `CLAUDE.md` or `GEMINI.md` (R1, O3) | No | The Claude fallback applies only with no `CLAUDE.md` and is a user setting; older hosts need the pointer; `GEMINI.md` is Gemini CLI's only loader and Antigravity's pointer; the saving is under 100 tokens; scaffold treats these as never-overwritten constitution files. |
| Switch `GEMINI.md` to an `@AGENTS.md` import (Antigravity 2.11.0, Gemini CLI `@file`) | No | The prose pointer already works on both; import depth and failure behavior are undocumented; no token gain. |
| Add `.github/skills/` as a second Copilot/Devin target | No | Every host reads `.agents/skills`; a second copy adds ~1 MB per project and double-listing risk (Copilot CLI: first name wins). |
| `disable-slash-command: true` on Layer 3 skills (Antigravity CLI 1.1.12) or Cursor `paths` scoping | No | Menu hygiene only, no token saving; some execution skills are typed by users; host-only top-level fields in a repo that keeps host-neutral metadata under `metadata.stratos.*`. |
| Claude Mods, gating hooks, or hook-based audits on Cursor/Codex/Copilot/Devin (R6) | No | Hook surfaces diverge per host, and Cursor and Copilot also import Claude Code hooks, so one config can fire twice. Revisit when one deterministic gate needs host-enforced timing. |
| `omitClaudeMd` (2.1.271) or Antigravity `inheritCustomizations` | No | StratOS defines no named agents, and the safety rules in `AGENTS.md` (subagents never commit) must reach every subagent. |
| Rules-budget lint (Antigravity 20K tokens) | No | Always-on rules are ~2.3K tokens plus `AGENTS.md` ~2.5K: roughly 4x to 8x headroom (whether `AGENTS.md` counts is undocumented). Re-check if always-on rules pass ~40 KB. |
| Move OpenClaw to a root `skills/` dir, or adopt Devin/Codex-specific plugin dirs | No | `.agents/skills` is a documented root on all of them; a root `skills/` would make OpenClaw read build output as project skills. |
| Size guard for `src/constitution/AGENTS.md` (Devin injects only the first 16 KiB, reported) | Not now | The file is 9.7 KB (~6 KB headroom) and the figure comes from undated docs. Add a one-line test if the constitution nears 14 KiB. |
| Stitch reports (R7), Cursor Projects/cloud agents (O7) | Watch | Forum-only or beta and cloud-only; `2b-interface-design.md:68` already has a fallback path. |

## Order of work and packaging
**One feature PR** (AGENTS.md §4: one branch, one PR per feature; slices are commits on it). One release bump, one OKF version bump per touched file, merge commit by a human. Parent: epic BT-012.

Commit order (a preference; no slice blocks another):
1. **Slice 1, host hygiene (A, B, F, H):** all text or dead-code edits in different files. F leads the commit message; it is the only user-visible safety fix.
2. **Slice 2, Copilot twin (G):** code plus the tests that assert the twin; slice 1 rewrites the §8 text about it, with no code dependency.
3. **Slice 3, plugin-shaped bundle (C, D, E):** C is the first step, not a separate issue. If C shows the CLI ignores `~/.gemini/config/skills`, its path fixes land in this slice. D changes `dist/` output, so it comes last and is the only slice that could be dropped from the PR without breaking the others.

After merge, outside the PR: the one-time clean of the twin in each affected project (G), then re-run this watch. The watermark `docs/research/.upstream-watch.json` stays at Claude Code 2.1.291, Antigravity app 2.19.1 / CLI 1.2.14; the other hosts have no watermark yet and are covered once by this baseline.

## Proposed issues (human mints via /3b)
Minted on 2026-10-06 as BT-148, BT-149 and BT-150, sub-issues of epic BT-012 ("General - 0 Constitution"), which has no `type:` label and no BACKLOG row yet, so the branch type for `3d` is still to be chosen:

| Slice | Acceptance check |
|---|---|
| BT-148 Host hygiene: AGENTS.md §8 table, trust note, hooks.json, Jules contract | No claim that Claude Code or Antigravity skip `AGENTS.md`; Gemini CLI stated to load `GEMINI.md`; Copilot real skill paths and a Copilot and a Gemini CLI row in the user-only table; version floors stated; `CLAUDE.md`/`GEMINI.md` unchanged. README requirements and setup summary name the Codex (>= 0.150.0) and Gemini CLI (>= 0.59.0) project-trust step. `src/skills/plan-html/hooks.json` absent from `src/` and `dist/`, no references. No `createTime` query param in `jules_api.py`; `CONTRACT.md` lists `headRef`, `baseRef`, `workingBranch`, archive and delete; pack tests pass. Build and validate green. |
| BT-149 Stop writing the Copilot skills twin | `SKILL_TARGETS` is `[".agents/skills"]`; `get_twin_paths` has no skills branch; `test_skill_conformance.py`, `test_update_flow.py` and `run-L1.ps1` updated; full suite green; a scaffold run into a scratch project produces no `.github/copilot/skills/`. |
| BT-150 Plugin-shaped bundle and validators | Marker-skill result per directory recorded in README Track D (C); `agy plugin validate` on the bundle shows `skills: <bundle count> processed`; README documents the Antigravity route and any other host whose spike passed; Track D retained; `RELEASING.md` lists `claude plugin validate .` and `agy plugin validate <bundle>` with one recorded dry run. |

Manual follow-up, no issue: delete `.github/copilot/skills/` in each project that has it (`git rm -r`, commit there).

## Open questions
- Does Antigravity's marketplace accept a GitHub repo or `.claude-plugin/marketplace.json`? (`agy plugin import` lists "claude" as a source; behavior unread.)
- Does a plugin install change slash command names from `/<name>`? README line 58 and every workflow hand-off text assume `/<name>`.
- Does the Copilot cloud agent honor `disable-model-invocation`, and do the CLI and cloud agent tolerate StratOS's extra frontmatter keys (`triggers`, `version`, `timestamp`)? Reported as unverified; VS Code only hints on unknown keys.
- Does a pinned Cursor "Custom Mode" bypass `disable-model-invocation`? The docs do not say.
