---
type: plan
title: Future-Proofing StratOS — v4.0.0 Execution Plan
description: Migrate StratOS workflows to spec-conformant Agent Skills across six hosts, adopt OKF v0.2, before Antigravity retires workflow indexing on 2026-11-01.
version: "6.0.0"
timestamp: 2026-09-15
---

# v4.0.0 — Spec Conformance, Host Expansion, OKF v0.2

Execution plan. 15 slices, one feature branch, one PR. Read §1–§3 before any slice; §4–§8 (order, spike, verification, abort, risks) follow the slices.

Work list for Slice 9: [workflow-migration-audit.md](workflow-migration-audit.md).

> Planned in worktree `feat/spec-conformance-v4` off `origin/main` (`c5b9ff9`). All counts re-derived against main on 2026-09-15.
>
> **Sources:** [Agent Skills spec](https://agentskills.io/specification) · [Antigravity workflows→skills](https://antigravity.google/docs/migration/workflows-to-skills/) · [OKF SPEC.md](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md)

## 1. Contract

At completion, on a clean scaffolded project:

- All **22** skills resolve as `/<name>` on Claude Code, Antigravity, Cursor, Codex, Devin, OpenClaw — 19 lifecycle plus the 3 drivers (`stratosphere-setup`, `stratosphere-update`, `sync-skills`).
- `.agents/workflows/` is not written.
- No skill body exists twice in `dist/`.
- No file outside `.memory/` + `docs/` carries an OKF `type:`.
- A v3 project upgrades without losing data or retaining stale artifacts.

**Deadline: 2026-11-01.** After it, Antigravity stops indexing `.agents/workflows/`.

## 2. Facts

Verified against live specs and `origin/main` on 2026-09-15. **Do not re-derive.**

1. Agent Skills spec recognizes `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. **Unknown fields are ignored by spec guarantee.**
2. `name` matches `^[a-z0-9]+(-[a-z0-9]+)*$` **and equals the parent directory name**. `description` ≤ 1024 chars. `metadata` is a string→string map.
3. All 19 files in `src/workflows/` have invalid names. 3 drivers in `src/commands/`; only `sync-skills` conforms.
4. Rename blast radius: **196 occurrences / 37 files**. `docs/plans/` is **sweep-exempt** (planning records, incl. this file — 104 further occurrences). Archives excluded. Three separate roots — a single `src docs build .github` sweep misses two of them:
   - `--exclude-dir=archive --exclude-dir=.archive --exclude-dir=plans src docs build .github` → **144 / 30**
   - same pattern over `tests` → **34 / 6**
   - **repo-root `*.md`** → **18 / 1** — all in `README.md`, lines 62–69: the public lifecycle table naming every slash command. `RELEASING.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` carry none.
5. Host read paths:
   - `.agents/skills/` — Cursor, Codex, Antigravity, Devin, OpenClaw
   - `.claude/skills/` — Claude Code (also read by Devin)
   - `.github/copilot/skills/` — VS Code Copilot (≠ `.github/skills/`, a Devin path)
6. Claude Code **merged commands into skills**: `.claude/commands/x.md` and `.claude/skills/x/SKILL.md` both create `/x`.
7. Manual-only field by host: `disable-model-invocation: true` (Claude Code, Cursor, OpenClaw); `triggers: ["user"]` (Devin); sidecar `<skill>/agents/openai.yaml` → `policy.allow_implicit_invocation: false` (Codex, **fixed convention** — no parser resolves frontmatter pointers); **nothing** (Antigravity — reads only `description`).
8. `diff -rq dist/antigravity/skills dist/claude-code/skills` → **no differing files, only differing membership**: `stratosphere-setup` and `stratosphere-update` are Antigravity **skills** and Claude-Code **commands**. Slice 7.6 collapses that asymmetry. `versions.json` differs across ~150 lines (`workflows/*` vs `commands/*` keys); `plugin.json` exists only under `dist/antigravity/`.
9. `.agents/skills/` is gitignored by `scaffold.py:323` (`GITIGNORE_ENTRIES`).
10. `reconcile_gitignore()` is **add-only** (`scaffold.py:~356`). It never removes a stale entry.
11. **37 `.reference/` citations** across 14 workflows, 1 command, 1 reference body. 5 shared references → 18 copies: `github-issue-relations` ×5, `confidence-scale` ×5, `terminal-sync-invariant` ×4, `issue-templates` ×2, `design-brief-guide` ×2.
12. `.reference/` is also cited from Python: `reconcile.py:14`, `scaffold.py:338`, `scaffold.py:1068`.
13. **17 path-based skill delegations**; 13 are `load-memory`, which appears **nowhere in `scaffold.py`** — already broken in consumer projects.
14. **4 `status:` vocabularies** across 6 templates. `concept-map-template.md:6` carries `status: "status:in progress"` — a GitHub label in doc frontmatter, **already illegal** per `okf-protocol.md:34`.
15. `timestamp:` has a **reader**: `1b:77`, the 90-day research staleness gate.
16. **88** files carry `timestamp:`: **21** in `docs/` (OKF scope; includes 2 untracked plan docs — **19** against main), **64** in `src/` (build field — `build.py:248`, `validate.py:60,68`; `build/` itself contributes 0), **3** at repo root (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) which lose `type: constitution` in Slice 3 but **keep `timestamp:` as a build field**. **`.memory/` does not exist in this repo** — project-local and gitignored; Slice 10 migrates it in consumer projects.
17. `brainstorm-techniques.md` has zero citations — superseded by the `concept-brainstorm` skill. Only genuine orphan.
18. `improve-workflows-skills` has no `src/` counterpart; hand-maintained in `.agents/skills/` and `.claude/skills/`.
19. `docs/okf-spec-essentials.md` cites a dead repo path. OKF moved to `GoogleCloudPlatform/open-knowledge-format`.

## 3. Invariants

- **I1.** Rename to spec form (`_` → `-`). One canonical name set across all hosts.
- **I2.** Ships as **v4.0.0**. **No alias shims.**
- **I3.** One canonical skill set. Per-host folders carry packaging only. Bodies byte-identical. A new host is a placement-map entry, never a content fork.
- **I4.** **Never run Antigravity's `/migrate-workflows`.** It rewrites `.agents/`, which is build output.
- **I5.** Edit `src/` only. Never hand-edit `dist/` or `.agents/`. Rebuild via `python build/build.py`.
- **I6.** Per-file `version` bumps **once per PR** against the fork-point baseline.
- **I7.** Migrations are one-off throwaway scripts. Never agent passes, never workflow steps.
- **I8.** Shared references **fan out from `src/references/` at build time**. Emitted copies are generated, never hand-edited.
- **I9.** Slices 1–3 land before 4–15. `okf-protocol.md` is a `glob` rule matching `docs/**` and `.memory/**` — it auto-loads into agent context during this migration. `improve-workflows-skills` fires on any edit to `src/skills/` or `src/workflows/`, so Slice 6's `git mv` of 19 files loads its stale §1 mid-sweep. **Both** currently instruct the opposite of this plan (`improve-workflows-skills/README.md` §1: *"This repo does not use `disable-model-invocation`. … Don't add the field."*).
- **I10.** Push nothing until Slice 15. `main` stays untouched.

---

## Slice 1 — Constitution

Edit `src/constitution/AGENTS.md`.

- §1 Layer 1: path `.agents/workflows` → `.agents/skills/`. Mark "triggered only by the user" **host-dependent**.
- §1 Layer 3: same directory as Layer 1. Layers distinguished by **frontmatter, not location**.
- §2 Precedence: re-key to `metadata.stratos.layer`: `lifecycle` | `execution`. Mode plays no part in precedence.
- §8 Host activation: rewrite for the six hosts in fact 5. State the Antigravity HITL gap explicitly.

Split the discriminator. Source: `type: workflow HITL` / `workflow AFK` in each `src/workflows/` file (registry row `okf-protocol.md:66`).
- `metadata.stratos.layer: lifecycle | execution` — the §2 precedence key
- `metadata.stratos.mode: HITL | AFK` — execution style after invocation

Every `src/workflows/` file carries a qualifier and maps cleanly. **The 3 `src/commands/` drivers carry bare `type: workflow` and no `trigger:`** — classify them explicitly as `layer: lifecycle`, `mode: HITL`, or precedence has nothing to key off.

**DONE WHEN:** an agent reading only `AGENTS.md` classifies any artifact in `.agents/skills/` into Layer 1 or Layer 3 without inspecting its path, **and every one of the 22 has a qualifier to be classified by**.

## Slice 2 — Governance docs

Rewrite before any code moves (I9).

| File | Change |
|:---|:---|
| `src/rules/okf-protocol.md` | Drop own `type: rule`; keep `trigger`/`globs`/`paths`. **Split §2.1** — rule activation stays; skill activation moves to Slice 8's frontmatter contract. **Delete §3 rows 64–66** (`constitution`, `rule`, `workflow`). §2 contract: `timestamp` → `generated.at` for in-scope files. §4: `okf_version` → `"0.2"`. Delete §2's "OKF stays value-agnostic" claim about `status` — false in v0.2. Keep the `discovery-brief` carve-out. |
| `src/rules/memory-protocol.md` | Drop `type: rule`. Note `verified:` arriving in Slice 14. |
| `src/rules/output-mode.md` | Drop `type: rule`. |
| `docs/improve-workflows-skills/README.md` | §1 table wrong in 4 rows: install split; "`disable-model-invocation` not used in this repo" (**reverse**); "`trigger:` is inert"; `.agents/workflows/.reference/` convention. Add I8 so authors read emitted duplication as intended. |
| `docs/improve-workflows-skills/glossary.md` | Redefine at minimum: **workflow**, **command**, **skill**, **trigger**. Target state: "workflow" survives only as `metadata.stratos.layer: lifecycle`; "command" is retired (fact 6). |
| `improve-workflows-skills` | **Create `src/skills/improve-workflows-skills/SKILL.md` FIRST, then rebuild** — do not hand-edit the two copies (I5). The `.claude/skills/` copy is tracked; the `.agents/skills/` copy is untracked (caught by `GITIGNORE_ENTRIES`). Apply the same 4 corrections as the README row. |
| `docs/okf-spec-essentials.md` | Re-capture against v0.2. Fix the dead URL (fact 19). |
| `docs/VERSIONING.md`, `/RELEASING.md` (repo root) | New layout; v4.0.0 breaking-change note; document `scripts/migrations/migrate_v3_to_v4.py` (Slice 10). Neither carries a stale workflow name — content only. |
| `/README.md` (repo root) | Lifecycle table at lines 62–69 renames in Slice 6. Version badge bumps in Slice 15. Update any prose describing `.agents/workflows/` or the command-vs-skill split. |
| `docs/proposals/.templates/skill-placeholder.md`, `workflow-placeholder.md` | New frontmatter shape (Slice 8). |

**DONE WHEN:** no governance file instructs anything this plan contradicts.

## Slice 3 — OKF scope and type registry

**Scope stays `.memory/` + `docs/` as written.** OKF governs knowledge; `metadata.stratos.*` governs artifacts.

**Remove** (files outside bundle scope; they stop carrying `type:`): `constitution`, `rule`, `workflow`.
**Never add:** `skill`, `reference`.
**Add:** `roadmap` (`docs/ROADMAP.md`), `audit-report` (`docs/audits/*.md`), `concept-map` (`docs/discovery/*.map.md`), `plan` (`docs/plans/*.md`, absorbs `implementation-plan`), `proposal` (`docs/proposals/*.md`).

Carve `docs/discovery/*.map.md` out of `discovery-brief`'s `docs/discovery/*.md` glob or it shadows `concept-map`.

**Final registry — 18 types:**
- `.memory/`: `status`, `backlog`, `learnings`, `glossary`, `architecture`, `database-schema`, `design-rules`, `design`
- `docs/`: `prd`, `discovery-brief`, `research`, `interface-design`, `design-doc`, `roadmap`, `audit-report`, `concept-map`, `plan`, `proposal`

**Template exception (discovered in execution).** A template that *mints* an in-scope document carries the **emitted document's** `type:` — `src/memory-templates/*` and `src/references/*template*`. That is the artifact's type, not the template's, and it stays. Only framework artifacts lose `type:`: constitution, rules, skills, the 3 drivers, and the 3 non-template references.

`src/workflows/*` keep `type: workflow HITL|AFK` until **Slice 8** converts them to `metadata.stratos.layer`+`.mode`; Slice 1 names that field as the conversion source.

**Also:** this repo's **root** `AGENTS.md` is its own constitution (real Vision), not a copy of `src/constitution/AGENTS.md` (placeholder Vision). Slice 1's edits must be applied to **both**, or the constitution governing this repo stays stale while the shipped one moves.

**DONE WHEN:** no framework artifact outside `.memory/`+`docs/` carries `type:` (templates and `src/workflows/` excepted as above); every `type:` value in use is one of the 18; `implementation-plan` is gone from live docs.

## Slice 4 — OKF v0.2 shape

Migrate the **21 in-scope files only** (fact 16). `src/`/`build/` keep `version:` + `timestamp:` as build fields.

1. `timestamp` → `generated: {by, at}`. **A mechanical key rename produces invalid YAML** — `generated` is a nested mapping, not a scalar. **`by` names the invoking workflow** (its frontmatter `name`), never a subagent — `4c` consolidates three subagents and forces this rule. Backfill: git author of last commit; unresolvable → `by: unknown`. Never guess.
2. `status` → `draft | stable | deprecated`:

| Vocabulary | Templates | Map |
|:---|:---|:---|
| `draft \| approved \| superseded` | `PRD-template`, `design-doc-template` | `approved`→`stable`, `superseded`→`deprecated` |
| `active \| stale \| superseded` | `research-competitive-template`, `research-problem-template` | `active`→`stable`, `stale`/`superseded`→`deprecated` |
| `ready-for-prd \| exit-bug \| exit-spike \| dropped` | `discovery_brief_template` | **exempt** |
| `"status:in progress"` | `concept-map-template:6` | `draft` (open) / `stable` (converged, `1c:75`) |

Also instructed **inline in bodies** — edit these too: `2a:83`, `2b:76`, `2b:78`, `2b:83`.
3. `okf_version` → `"0.2"` at `scaffold.py:1117` and the root `index.md` template. Legal **only** in the bundle-root `index.md`.
4. Teach `build/validate.py` and `build/bump_guard.py` the new key.
5. Fix body-prose writers: `2c:58`, `2b:32`.
6. **Sweep readers.** `1b:77` is the 90-day research staleness gate. Repoint to `generated.at` or it **fails open** and silently reuses stale research.

One-off throwaway script (I7). Single PR (I6).

**DONE WHEN:** `grep -rn "^timestamp:" docs --exclude-dir=plans` = 0 (`.memory/` is absent from this repo — Slice 10 covers it); no body prose writes *or reads* `timestamp`; every `status:` is a v0.2 member or documented exemption.

## Slice 5 — Artifact-minting conformance

Templates carry the frontmatter that lands in artifacts. Fix the machinery, not just existing files.

| Target | Defect | Fix |
|:---|:---|:---|
| `ROADMAP-template.md:1-7` | Leaks `name: ROADMAP-template`, `version: "1.0.1"`, **`timestamp: 2026-07-10` — a hardcoded literal date** | Drop `name`; add `title: Product Roadmap`; `version` → runtime plugin version (OKF §5); `timestamp` → `generated: {by, at}` |
| `concept-map-template.md:5-6` | **Hardcoded `timestamp: 2026-07-09`** + illegal `status: "status:in progress"` | Placeholder date → `generated: {by, at}`; status per Slice 4 |
| `health-audit-report-template.md:31-35` | Mints `timestamp: <YYYY-MM-DD>` — a **date, not ISO 8601 datetime** | `generated: {by, at}`, datetime precision (the file's own `.last-run.json` schema already uses `<ISO-8601>`) |
| `research-*-template.md` | `status: active \| stale \| superseded`; body `## Sources` (`research-competitive-template.md:82`, `research-problem-template.md:38`) | Slice 4 map. **`## Sources` → frontmatter `sources:` is deferred to Slice 14** — leave the body section in place here |
| `3a:61` | *"Prepend OKF `type: roadmap`"* — template already has it → **duplicate YAML key** | Delete the prepend instruction |

**Untyped artifacts inside bundle scope:**
- `docs/nightly/nightly-<YYYY-MM-DD>.md` (`0d:20`) — "tracked", no frontmatter, no template, no type. Use `proposal`. `0d:36-37` rebuilds `index.md` from `title`/`description` these files never have.
- `.work.md` inside `docs/` — `1a:49`, `1b:43`, and `3a` at **`:37` (write), `:49` (auditor read), `:67` (cleanup)** → `.tmp/3a-roadmap.work.md`. **Relocate all three to `.tmp/`** (AGENTS.md §3 already mandates it; `3z:36` and `3b:48` already follow it). Do not add frontmatter. Gitignored via `scaffold.py:326` (`*.work.md`) but **`validate_memory.py:387` walks `docs/**/*.md` regardless**, so the OKF lint sees them.

**Rule the non-`.md` durables.** `docs/ROADMAP.html`, `docs/audits/.last-run.json`, `.memory/jules-ledger.jsonl` are durable, inside bundle scope, and **cannot carry frontmatter**. Add an explicit exclusion to `src/rules/okf-protocol.md` **§4 Reserved Files** (line 81), which today names only `index.md` and `log.md`.

**Split `concept-map-template.md`** — `concept-map-operations.md:23` pipes it to `gh issue create --body-file`, posting its YAML verbatim into the issue body.

**Add a re-stamp step to every workflow that mutates an in-scope doc.** `3b:66`, `3c:63-65`, `3d:16-17`, `4a:68-69` change `BACKLOG_MAP.md`/`STATUS.md` with no change-date bump; `generated.at` would go permanently stale. Follow `2c:58`, the only site that does it correctly.

**DONE WHEN:** every template's minted block is v0.2-shaped; `generated.by` convention stated; no in-scope durable file lacks frontmatter or a documented exemption; no `.work.md` inside `docs/`.

## Slice 6 — Rename

**Decided (no gate).** `x_jules-dispatch` → **`3x-jules-dispatch`**; map stays **19 entries**. *(Resolved.)* `3x-jules-dispatch.md` matches `LIFECYCLE_RE`, so **`EXTRA_WORKFLOWS` shrinks to `{"sync-skills.md"}`**.

1. Create and freeze `docs/plans/rename-map.json`. Every target matches `^[a-z0-9]+(-[a-z0-9]+)*$`.
2. `git mv` all 19 in `src/workflows/`. Rename `src/commands/instantiate/` → `stratosphere-setup/`, `update/` → `stratosphere-update/`, `SKILL_sync-skills.md` → `SKILL.md` (fact 2: `name` == directory).
3. Rewrite **196 / 37 files**, **longest-key-first**: 144/30 under `src docs build .github`, 34/6 under `tests/`, **18 in root `README.md` (lines 62–69)**. Archives and `docs/plans/` out of scope. `README.md` is the project's public face — every stale entry prints a command a user types that silently does not resolve (I2).
4. `src/scripts/scaffold.py` — **Slice 6 renames strings only; Slice 7 owns every retarget.** Rename inside `EXTRA_WORKFLOWS` (321) so the intermediate build stays green; Slice 7.3 then retires the constant. **Leave `map_bundled_to_project()` (330) pointing at `.agents/workflows/`** — its targets at **338** (references) and **341** (workflows) belong to Slice 7.2/7.4. The dir list at **400–401** holds no old names: pure Slice 7 deletion, listed here only so Slice 6 does not touch it. Same for `WF_SRC` (318), `GITIGNORE_ENTRIES` (323), placement blocks (1068, 1074), `okf_version` (1117). Fix the stale `# 0a..4b` comment at 320. `LIFECYCLE_RE` (320) and `place()` (413) need **no change**.
5. `src/experimental/jules-dispatch/status.py`.

**Sweep hazards — do NOT touch:** bare short ids (`0a`, `3d`, `4a`); `.github/workflows/` (GitHub Actions — `scaffold.py:339`); `discovery_brief_template.md` (underscore in a *reference* filename, cited `1b:112`); `4a:64` "If command exits non-zero" (shell).
**Forms a naive sweep misses:** unbackticked prose (`1b:73`); escaped-JSON payloads (`3z:44`); multiple targets per line (`1a:15`, `3z:14`).

**DONE WHEN:** `grep -rE '[0-4][a-z]_|x_jules-dispatch' --exclude-dir=archive --exclude-dir=.archive --exclude-dir=plans src docs build .github tests *.md` = 0 — the trailing `*.md` covers repo root and is **required** (fact 4). `--exclude-dir=plans` is **required** — planning docs cite old names as records (fact 4). The `x_jules-dispatch` alternation is **required** — `[0-4][a-z]_` does not match it.

## Slice 7 — Canonical emitter

1. **Unblock the gitignore first** (fact 9). `GITIGNORE_ENTRIES` (`scaffold.py:323`) writes `.agents/skills/` into every project's `.gitignore`. Ignore only on-demand pack directories, or negate the bundled names.
2. Emit each workflow to `.agents/skills/<name>/SKILL.md` via `map_bundled_to_project()`.
3. Retires the `.agents/workflows/.reference/` indirection and the `EXTRA_WORKFLOWS` workaround documented at `scaffold.py:21`.
4. **Fan out references (I8).** 18 copies from 5 shared sources (fact 11). Rewrite citations **inside reference bodies** (`concept-map-operations.md` holds 3 of the 37) **and inside Python** (fact 12 — sweep `--include=*.py`). Drop `brainstorm-techniques.md` (fact 17) after confirming it is dead.
5. **Dedupe `dist/`** (fact 8): build one canonical tree at **`dist/skills/`**; reduce `dist/<host>/` to manifest plus packaging that references it. Slices 11 and 12 resolve against `dist/skills/`.
6. **Retire `dist/claude-code/commands/`** (fact 6). Claude Code HITL moves to `disable-model-invocation`, which also **prevents subagent preloading** — the property mitigating Slice 9 §F.

| Path | Hosts |
|:---|:---|
| `.agents/skills/` | Cursor, Codex, Antigravity, Devin, OpenClaw |
| `.claude/skills/` | Claude Code (also Devin) |

**DONE WHEN:** a scaffolded project surfaces all 22 as `/<name>` on Antigravity; `.agents/workflows/` not written; `git status` shows skill directories **tracked**; no skill body twice in `dist/`.

## Slice 8 — Cross-host HITL

```yaml
name: 3d-implement-issue          # == parent dir name
description: ...                   # <= 1024 chars; MUST state user-only (Antigravity reads only this)
disable-model-invocation: true     # Claude Code, Cursor, OpenClaw
triggers: ["user"]                 # Devin
metadata:
  stratos.layer: "lifecycle"       # §2 precedence key
  stratos.mode: "HITL"
  stratos.version: "2.1.0"
```

Plus `<skill>/agents/openai.yaml` → `policy: { allow_implicit_invocation: false }`. **Never reference the sidecar from frontmatter** (fact 7).

- **Handle the three drivers explicitly.** `stratosphere-setup`, `stratosphere-update`, `sync-skills` carry **no `trigger:`**. A transform keyed on `trigger: manual` skips them, leaving `/stratosphere-setup` model-invocable.
- **`3x-jules-dispatch` and `3z-afk-loop` keep the HITL keys** despite `mode: AFK`. AFK describes what happens after invocation, not who invokes.
- Keep the `stratos.` prefix: the spec recommends unique keys; `type`/`version` are what another tool claims in a shared map; the field is build-generated.
- Consider `allowed-tools` (spec-standard, honored by Devin) on read-only skills. `4c:48-50` shells out to `git log` — strongest candidate.

**DONE WHEN:** every emitted skill — including the three drivers — carries `disable-model-invocation`, `triggers`, `metadata.stratos.layer`, `metadata.stratos.mode`, `agents/openai.yaml`, and a user-only `description`. No skill carries an OKF `type:`.

## Slice 9 — In-body remediation

Work list: **[workflow-migration-audit.md](workflow-migration-audit.md)**.

| § | Work |
|:---|:---|
| A | Repoint 37 `.reference/` citations to per-skill `references/` |
| B | **5 subagent-boundary sites** — `4a:30`, `4a:31`, `4b:33`, `4c:69`, `4c:74` — use absolute `.agents/skills/<name>/references/<file>.md`. A relative path resolves against repo-root cwd and fails **silently**. `4c:74` is worst: no scan matrix → every subagent reports zero findings → `4c` prints `[HEALTHY]` and persists a false all-clear to `.last-run.json` |
| C | Convert 17 path delegations to name-based; 13 are `load-memory` (fact 13) |
| E | Three drivers missing `trigger:`; `name` ≠ dir |
| F | Restate user-only in every `description`. Strengthen `0d` Phase 3.6 — it emits `/<sibling>` into agent context guarded only by prose |
| G | Generalize 5 two-host subagent enumerations. **`4c:63` requires 3 *parallel* subagents** — unverified on Cursor, Codex, Devin, OpenClaw. Specify sequential degradation: auditors share no state, so sequential is equivalent, but all six passes must run or Phase 5's `6/6` is false |
| H | Convert `3z`'s phase-number coupling to `4a` into **named gates** (`audit-only`/`ship-only`). If `4a` renumbers, `3z` silently ships unverified work |
| K | Rewrite `Instantiate-StratosphereOS.md:37` (every clause falsified) and its `.gitignore` enumeration. Add a **reserved-name guard** to `sync_skills.py` — an `external-skills.json` `targetPath` can clobber a lifecycle skill |
| E2 | **`4c:15` claims `Read-only.` while `4c:115` deletes files.** Fix when rewriting its `description`. Same section carries `4c`'s parallel-subagent and argument-channel findings |

**DONE WHEN:** every audit item resolved or explicitly deferred with a reason.

## Slice 10 — v3 → v4 upgrade

`stratosphere-update` **cannot** perform this migration:
- `reconcile_gitignore()` is add-only (fact 10) → upgraded projects keep `.agents/skills/` ignored and silently lose every lifecycle skill.
- No removal phase → 19 stale `.agents/workflows/*.md` + 19 orphaned `.reference/` files remain. On Antigravity both trees resolve until 2026-11-01, so `/0a_start-session` **and** `/0a-start-session` both work.
- Worklist schema (`preserved_files`, `needs_review_constitution`, `unmarked`) has no **moved** category.

**Precedent:** `place_project_scripts()` (`scaffold.py:446`) already pushes new/changed scripts on update. The gap is *removal* and *moves*, not addition.

Ship **`scripts/migrations/migrate_v3_to_v4.py`** — standalone, manual, documented in `/RELEASING.md`. **Defaults to `--dry-run`** with a full diff.

**Follow the existing precedent, do not invent one.** `scripts/migrations/` already holds `migrate_agent_to_agents.py` — structurally the same problem (a rename with consumer-project impact), with the same contract in its docstring: *"intentionally NOT wired into scaffold.py's install/update lifecycle — run it once, by hand, from the target project root."* Mirror its shape, and its test (`tests/test_migrate_agent_to_agents.py`) for Slice 11. Note `scaffold.py:710` already points users at `scripts/migrations/inject_markers.py`, so the directory is wired into the update flow's guidance.

1. Rewrite the stale `.gitignore` entry.
2. Detect the pre-v4 `.agents/workflows/` tree; list framework-owned files; **spare user-authored ones**; confirm; remove; report what was left.
3. Migrate the project's **own** `.memory/` + `docs/` frontmatter (`preserved` tier — the scaffolder never touches it).
4. Idempotent; safe to re-run.

Add a detection phase to `src/commands/stratosphere-update/` directing the user to the script.

**DONE WHEN:** a v3 fixture upgrades cleanly — no stale workflow files, no stale `.gitignore` entry, project docs on v0.2 shape, user content untouched, dry-run matches the write run.

## Slice 11 — Test suite

**34 occurrences / 6 files**, plus assertions that fail rather than error.

| File | Breakage |
|:---|:---|
| `tests/install-harness/run-L2.py:202,210` | Hardcodes `== 14` workflows (already stale — `dist/antigravity/workflows/` holds 20) and probes `.../"workflows"`. Written `... if (...).exists() else False`, so a retired directory returns **False and fails as "wrong count"**, not "directory gone". Rewrite against `.agents/skills/<name>/SKILL.md`; derive the count from `rename-map.json` |
| `tests/test_3z_orchestrator_simulation.py:52,221` | Asserts the literal `"run /3d_implement-issue + /4a_verify-and-ship manually"` |
| `tests/test_jules_status.py:42,116` | Asserts `/4a_verify-and-ship` in output and in `status.py` source |
| `tests/test_plan_html_delegation.py:25,29,33` | Dict keyed on `src/workflows/<old-name>.md` |
| `test_subagent_spawning.py`, `test_terminal_sync.py`, `test_update_flow.py` | Name-bearing assertions |

**Add coverage nothing currently has:** emitted tree is spec-conformant (name regex, `name` == dir); every shared reference present in each consuming skill; `.agents/skills/` **not** gitignored in a scaffolded project.

**DONE WHEN:** `grep -rE '[0-4][a-z]_|x_jules-dispatch' tests/` = 0; no hardcoded count; suite green in CI.

## Slice 12 — Validation & CI

`validate.py` drives off `for plat, inv in [("dist/claude-code","commands"), ("dist/antigravity","workflows")]` (lines 54, 302) and `(root/plat/"skills").glob("*/SKILL.md")` (63). After Slice 7 `dist/antigravity/workflows/` is gone — and **`Path.glob` on a missing directory yields nothing without erroring**, so these iterate zero files and CI goes green on an empty set.

1. Retarget the loops at 54 and 302 to `dist/skills/` (Slice 7.5).
2. **Assert a non-zero file count** so an empty walk fails loudly.
3. Update **both** `required` sets — lines 60 **and** 68.
4. Spec-name check: regex + `name` == parent dir.
5. **Link integrity resolved from the skill directory**, not repo root, or it passes paths broken at runtime (Slice 9 §B).
6. `skills-ref validate` ([agentskills/agentskills](https://github.com/agentskills/agentskills/tree/main/skills-ref)). Confirm install method before wiring in.
7. Reserved-name guard in `sync_skills.py`.

**DONE WHEN:** CI green on a clean checkout with a **non-zero** validated file count; install-harness green.

## Slice 13 — VS Code Copilot *(deadline-optional)*

Add `.github/copilot/skills/` to the placement map. ≠ `.github/skills/` (a Devin path).

## Slice 14 — OKF v0.2 trust signals *(deadline-optional)*

Additive; changes no existing field.

| Feature | Mapping |
|:---|:---|
| `verified: [{by, at}]` | Memory-protocol trust tags — records who promoted `[ASSUMED]` → `[PATTERN]`/`[CONFIRMED]` and when |
| `sources` | `1a-research` output; per-source `author`/`last_modified` |
| `stale_after` | `.memory/STATUS.md` and sprint docs only |
| Attestation (`runtime`/`executor`/`attester`) | **Not adopted.** No StratOS use case. Recorded so it is not re-litigated |

## Slice 15 — Ship

Rebuild. **Bump `build/build.py` VERSION 3.3.0 → 4.0.0 and the `README.md` version badge to match** — `validate.py:261-274` fails the build on a mismatch. Verify (§6). **Regenerate `dist/` in a single final commit** — 186 tracked files; mixed into hand-written slices the human diff disappears. Open the feature PR. A human merges.

---

## 4. Order

```
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → [13 | 14] → 15
```

- 1–3 precede all implementation (I9).
- 6 blocks 7: the skill directory name must equal `name`.
- 7 step 1 (gitignore) blocks the rest of 7.
- 10 depends on 7 (must know the final layout).
- 13, 14 independent and droppable.

## 5. Spike before the sweep

**Unverified assumption: a numbered-prefix skill name resolves as `/0a-start-session` in each host's slash menu.** The spec permits the name; no host has been tested.

Migrate **one** workflow end-to-end through Slices 6–9 and invoke it on all six hosts before renaming the other 18. Doubles as the self-hosting canary — this repo drives its own work with `/3d`, `/4a`, `/0b`, and those break the moment Slice 7 stops emitting `.agents/workflows/`.

## 6. Verification

**Fresh scaffold:**

| Check | Slice |
|:---|:---|
| All **22** (19 lifecycle + 3 drivers) resolve as `/<name>` on Claude Code and Antigravity | 7 |
| The spike skill resolves on Cursor, Codex, Devin, OpenClaw | 7, §5 |
| Skill dirs resolve under `.agents/skills/` and `.claude/skills/` | 7 |
| `.agents/workflows/` absent | 7 |
| `git status` shows skill directories tracked | 7.1 |
| No skill body duplicated across `dist/` | 7.5 |
| Every shared reference present in each consuming skill | 7.4 |
| `grep -rE '[0-4][a-z]_\|x_jules-dispatch' --exclude-dir=archive --exclude-dir=.archive --exclude-dir=plans src docs build .github tests *.md` = 0 | 6 |
| `grep -rn "^timestamp:" docs --exclude-dir=plans` = 0 | 4 |
| Every skill carries `disable-model-invocation`, `triggers`, `metadata.stratos.layer`+`.mode`, `agents/openai.yaml`, user-only `description` | 8 |
| No file outside `.memory/`+`docs/` carries `type:`; every in-scope `type:` registered | 3 |
| Link integrity green, **resolved from each skill's directory** | 12.5 |
| `skills-ref validate` passes on every skill directory | 12.6 |
| `validate.py` reports a **non-zero** validated count | 12.2 |
| Suite green; no hardcoded counts | 11 |
| Every one of the 22 has a `layer`+`mode` qualifier; `AGENTS.md` alone classifies them | 1 |
| Every template's minted block is v0.2-shaped; no `.work.md` inside `docs/`; `generated.by` convention stated | 5 |
| Every audit item resolved or explicitly deferred with a reason | 9 |
| `implementation-plan` appears nowhere | 3 |
| No governance file contradicts the shipped shape | 1–2 |

**Upgrade path** (a v3 fixture — nothing above exercises it):

| Check | Slice |
|:---|:---|
| No stale `.agents/workflows/` files | 10.2 |
| `.gitignore` no longer ignores lifecycle skills | 10.1 |
| Project `.memory/`+`docs/` on v0.2 shape | 10.3 |
| User-authored workflows preserved | 10.2 |
| `--dry-run` matches the real run | 10 |
| Re-running is a no-op | 10.4 |

Green **in CI**, not locally — `verify_scripts` fails on Google Drive via `st_mtime`. CI is the arbiter.

## 7. Abort

Nothing is pushed until Slice 15 (I10). Rollback is always "reset the branch".

**Independently revertable:** 1, 2, 3, 4, 5, 11, 13, 14.
**One-way door: Slice 6.** Once 178 occurrences are rewritten, every later slice speaks the new names. Reverting 6 means reverting 7–15.
**Coupled chain:** `6 → 7 → 8 → 9`; `10` depends on `7`. No partial state inside it is coherent — renamed sources with the old emitter produce skills resolving under neither name.

**Abort points, cheapest last:** after 3 (governance + registry stand alone as a decision record) · after 5 (frontmatter conformance ships as an unrelated PR) · before 6.

**Minimum viable deadline path.** The deadline requires only that workflows survive as skills. Ship **6 → 7 → 8 → 11 → 12**; defer the rest. Accept deliberately: deferring Slice 2 means agents implement against contradicting guidance (I9), so a human drives those slices, not an AFK loop; deferring Slice 10 leaves v3 projects without an upgrade path — tolerable only because the deadline binds new Antigravity *indexing*, not installed projects.

## 8. Risks

| Risk | Mitigation |
|:---|:---|
| `.agents/skills/` gitignored — skills vanish from consumer projects | 7.1 (fresh) + 10.1 (upgrade), both gated by verification |
| Upgraded projects run two resolvable copies of every workflow until Nov 1 | 10.2 removal phase |
| `validate.py` iterates zero files and CI goes green | Non-zero count assertion, 12.2 |
| Relative reference path fails silently inside a subagent | Absolute paths at the 5 sites + skill-dir-relative link check (9.B, 12.5) |
| `timestamp` reader fails open, reusing stale research | Reader sweep, 4.6 |
| Agents implement against stale guidance | Governance-first (I9) |
| `3z` ships unverified work if `4a` renumbers | Named gates, 9.H |
| Numbered-prefix names may not resolve in some host's slash menu | Spike (§5) before the sweep |
| Antigravity cannot enforce HITL | **Accepted degradation.** Documented in `AGENTS.md` §8 (Slice 1); every `description` restates user-only (Slice 8). No host-side enforcement exists |
| Antigravity ships further changes before Nov 1 | Re-verify its docs at ship time |
