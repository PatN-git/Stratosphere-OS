---
type: design-doc
title: Harmonize trigger semantics across rules & workflows (dual-host)
status: ready-to-implement (handoff)
---

# Harmonize `trigger` semantics — rules ↔ workflows, Claude ↔ Antigravity

> **Handoff note.** This is a complete, standalone implementation spec — every change
> is described in full below (§Implementation steps). A working-tree prototype of most
> steps may already exist uncommitted; treat it as optional reference, not as a
> dependency. Nothing is committed. If merging with another plan, the overlap-prone
> files are `src/scripts/scaffold.py`, `build/validate.py`, and both `AGENTS.md` copies.

## Problem

The `trigger:` frontmatter key meant two incompatible things:

- **Workflows**: free-text prose (`trigger: User. Do not run autonomously.`) — advisory, machine-inert in both hosts.
- **Rules**: Antigravity's machine enum (`glob` / `always_on`) + `globs:`.

Same key, two meanings — and the enum only does anything in the host whose native rules dir the file sits in.

## Confirmed host facts

| | Claude Code | Antigravity |
|---|---|---|
| Native rules dir | `.claude/rules/` | `.agents/rules/` (plural — user-confirmed) |
| Rule activation field | `paths:` (YAML list of globs) | `trigger:` + `globs:` (comma string, unquoted) |
| Rule trigger vocabulary | n/a (`paths`-scoped, else always) | `manual` / `always_on` / `model_decision` / `glob` |
| Model can auto-invoke a workflow? | **No** — slash commands are user-typed only (no SlashCommand tool) | No — workflows are manual (@-mention) |

Consequences:
- **Workflows are already HITL-safe in both hosts with no field needed.** `disable-model-invocation` is invalid on commands (Skills only) and unnecessary. `trigger: manual` is purely declarative.
- The only functional lever is on **rules**, via each host's native dir + field.
- **Claude never fully loses a rule even without `.claude/rules/`**: every rule also has an AGENTS.md §8 prose pointer, so worst case it loads on-demand instead of `paths`-auto. This makes host-conditional placement safe.

## Canonical vocabulary (single source of truth — OKF §2.1)

One `trigger` enum shared by rules and workflows:

| `trigger` | Meaning | Antigravity | Claude Code |
|---|---|---|---|
| `always_on` | always in context | `trigger: always_on` in `.agents/rules/` | AGENTS.md §8 pointer (on-demand; NOT `.claude/rules/`) |
| `glob` | active on matching files | `trigger: glob` + `globs: a,b` in `.agents/rules/` | `paths: ["a","b"]` in `.claude/rules/` |
| `model_decision` | model decides from `description` | `trigger: model_decision` | description-driven / §8 pointer |
| `manual` | user explicitly invokes | native workflow / @-mention | slash command (inherently user-only) |

Workflows are all `manual`. Rules use the other three. Each **`glob`** rule carries **superset frontmatter** — `trigger` + `globs` (Antigravity) **and** `paths` (Claude) — so one source file is valid in either host's dir (each ignores the other's unknown keys).

## Placement model — HOST-CONDITIONAL

- **`.agents/rules/` — always written (both hosts need it).** Antigravity reads all rules here natively; Claude reads the `always_on` rules here via §8 pointers. Host-independent.
- **`.claude/rules/` — written only on Claude Code installs, and only for `glob` rules.** Gives Claude native `paths`-scoped activation. Antigravity installs skip it.

**Why host-conditional:** a both-host user installs StratOS in both; each install writes its host's native rules, and since project files are committed, the shared repo ends up with both. The mild cost (a teammate opening the repo in Claude without having run the Claude install won't get `.claude/rules/`) is bounded — `okf-protocol` still loads via its §8 pointer, just on-demand rather than `paths`-auto.

## Net effect

Only **`okf-protocol`** is `glob`-triggered → the single rule that lands in `.claude/rules/` (Claude installs only). `memory-protocol` and `output-mode` are `always_on` → `.agents/rules/` only + §8 pointer on Claude.

## Decisions (resolved)

- **D1 — `always_on` rules on Claude: keep as pointers.** `.claude/rules/` reserved for `glob` rules only; `always_on` rules stay §8 pointers on Claude (token-efficient) and native on Antigravity.
- **D2 — `output-mode` → `always_on`.** Governs all responses; the glob-to-memory/docs scoping was a mis-scope. `globs:` removed.
- **D3 — existing projects: migrate on update.** `stratosphere-update` re-places managed files; a Claude install gains its `.claude/rules/` copy on next update.
- **D4 — placement is HOST-CONDITIONAL** (see §Placement).
- **D5 — `(custom path)` scope → treat as non-Claude** (skip `.claude/rules/`); `okf-protocol` still resolves via §8 pointer.

---

# Implementation steps (complete)

Apply in order. Bump rules: any edit to a distributed `.md` frontmatter/body requires a `version:` bump (patch unless otherwise noted) and `timestamp: 2026-07-17`, because `_versioning.body_hash` hashes everything except `version`/`timestamp`, so validate.py §5 and bump_guard.py require the bump.

## Step 1 — `src/rules/okf-protocol.md`

**1a. Frontmatter** — add a `paths:` list (superset alongside existing `trigger`/`globs`); bump version `1.0.2 → 1.0.3`, timestamp `2026-07-17`. Final frontmatter:
```yaml
---
trigger: glob
globs: .memory/**/*,docs/**/*
paths:
  - ".memory/**/*"
  - "docs/**/*"
type: rule
title: Open Knowledge Format (OKF) Protocol
description: Specifications and type registries for OKF v0.1 conformance.
version: "1.0.3"
timestamp: 2026-07-17
---
```

**1b. Insert a new §2.1** immediately after the "Other existing metadata keys …" line at the end of §2:
```markdown
### 2.1 Activation contract (`rule` and `workflow` types)

`rule` and `workflow` files declare **when they activate** via a single canonical `trigger` key drawn from one shared enum. This unifies what were previously two divergent uses of `trigger:` (rules carried an Antigravity enum; workflows carried free-text prose).

| `trigger` | Meaning | Applies to |
|:---|:---|:---|
| `always_on` | Always in context. | rules |
| `glob` | Active only for files matching `globs`. Requires `globs`. | rules |
| `model_decision` | The model decides from `description`. | rules |
| `manual` | Activated only by explicit user invocation (slash command / `@`-mention). | workflows (all) |

Rules that are **`glob`** also carry host-native activation fields as a **superset** so one file works in both hosts (each host ignores the other's keys):

- `globs` (Antigravity): comma-separated glob patterns, **unquoted**, e.g. `globs: .memory/**/*,docs/**/*`.
- `paths` (Claude Code): YAML list mirroring `globs`, e.g. `paths: [".memory/**/*", "docs/**/*"]`.

Host activation semantics (see also [AGENTS.md](/AGENTS.md) §8):

- **Antigravity** reads `trigger`/`globs` natively from `.agents/rules/`.
- **Claude Code** has no `trigger` concept. `glob` rules activate via `paths` when installed to `.claude/rules/`; `always_on`/`model_decision` rules are surfaced through the AGENTS.md §8 pointer directory (on-demand load) to preserve token efficiency, not duplicated into `.claude/rules/`.
- **Workflows** need no host field: they build to Claude slash commands (user-only by construction — the model cannot auto-invoke them) and to Antigravity workflows (manual `@`-mention). `trigger: manual` is therefore declarative in both. Autonomy that begins *after* user invocation (e.g. `3z`) is documented in the body, not the trigger.
```

**1c. §3 Type Registry** — replace the `rule` and `workflow` rows with:
```markdown
| `rule` | `.agents/rules/*.md` (glob rules also `.claude/rules/*.md`) | `trigger` (required): `always_on` \| `glob` \| `model_decision` (see §2.1); if `glob`, also `globs` (Antigravity) **and** `paths` (Claude) |
| `workflow` | `.agents/workflows/*.md` | `trigger` (required): `manual` (see §2.1); `type` keeps its `HITL`/`AFK` qualifier, e.g. `workflow HITL` |
```

## Step 2 — `src/rules/output-mode.md`

Change `trigger: glob` → `trigger: always_on` and **remove** the `globs:` line (D2). Bump version `1.0.3 → 1.0.4`, timestamp `2026-07-17`. Final frontmatter:
```yaml
---
trigger: always_on
type: rule
title: Output Mode Protocol
description: Guidelines to maximize information density and minimize token waste in agent responses.
timestamp: 2026-07-17
version: "1.0.4"
---
```

## Step 3 — `src/rules/memory-protocol.md`

Ensure `trigger: always_on` is present (add as first frontmatter line if missing). Bump version `1.0.5 → 1.0.6`, timestamp `2026-07-17`. (Body unchanged; the frontmatter change alone requires the bump.)

## Step 4 — `src/workflows/*.md` (all 17)

For each file, set `trigger: manual` (replace the prose value; for `4b_audit-architecture-drift.md`, which has none, insert `trigger: manual` right after the `type:` line). Patch-bump each file's existing `version:` and set `timestamp: 2026-07-17`. `3z_afk-loop.md` stays `trigger: manual` — its post-invocation autonomy remains described in the `description`/body, not the trigger.

Files: `0a_start-session, 0b_stop-session, 0c_handoff, 0d_nightly-consolidation, 1a_research, 1b_concept-framing, 1c_concept-map, 2a_write-prd, 2b_interface-design, 3a_version-planning, 3b_create-issue, 3c_sprint-planning, 3d_implement-issue, 3z_afk-loop, 4a_verify-and-ship, 4b_audit-architecture-drift, x_jules-dispatch`.

Do this deterministically with a throwaway script (per [[stratos-no-token-bloat-migrations]] — do not commit it). Reference implementation in Appendix A.

## Step 5 — `build.py`

**No change.** Superset frontmatter is authored directly in `src/rules/*.md` and byte-copied to `assets/templates/rules/`; no per-host translation pass is needed. `VERSION` is already `2.2.0` (> last release `v2.1.0`), satisfying the plugin-level bump-guard.

## Step 6 — `src/scripts/scaffold.py` (host-conditional placement)

Replace the rule-placement block (currently `# 4. Rules -> .agents/rules/`, ~line 1025 inside `main()`). The `scope` local is computed ~line 454 in the same function; `re` is imported; `place()` creates parent dirs.
```python
    # 4. Rules -> .agents/rules/ (both hosts: Antigravity-native + Claude §8 pointers).
    #    Claude installs ONLY: glob rules ALSO -> .claude/rules/ for native paths:
    #    activation. Antigravity/custom installs skip .claude/rules/ (D4/D5).
    is_claude = "Claude Code" in scope
    for src in sorted((ASSETS / "rules").glob("*.md")):
        place(src, project / ".agents" / "rules" / src.name, res, dry, update=update, tier="managed")
        if is_claude and re.search(r'^trigger:\s*glob\b', src.read_text(encoding="utf-8"), re.M):
            place(src, project / ".claude" / "rules" / src.name, res, dry, update=update, tier="managed")
```

## Step 7 — `build/validate.py` (enum enforcement)

Insert this block **before** the `# Also check python script files in dist for BOM` block. Uses the existing `fm_dict()` helper.
```python
# 2.6 Trigger-enum contract (OKF §2.1): rules and workflows share one `trigger` vocabulary.
RULE_TRIGGERS = {"always_on", "glob", "model_decision"}
for plat in ["dist/claude-code", "dist/antigravity"]:
    rules_dir = root / plat / "assets/templates/rules"
    if rules_dir.exists():
        for rp in rules_dir.glob("*.md"):
            if rp.name == "index.md":
                continue
            d = fm_dict(rp.read_text(encoding="utf-8"))
            trig = d.get("trigger")
            if trig not in RULE_TRIGGERS:
                errs.append(f"{plat}/assets/templates/rules/{rp.name} trigger={trig!r}; must be one of {sorted(RULE_TRIGGERS)}")
            elif trig == "glob":
                if not d.get("globs"):
                    errs.append(f"{plat}/assets/templates/rules/{rp.name} trigger=glob but missing `globs` (Antigravity)")
                if "paths" not in d:
                    errs.append(f"{plat}/assets/templates/rules/{rp.name} trigger=glob but missing `paths` (Claude Code)")
    inv = "commands" if plat.endswith("claude-code") else "workflows"
    for md in (root / plat / inv).glob("*.md"):
        d = fm_dict(md.read_text(encoding="utf-8"))
        if "trigger" in d and d.get("trigger") != "manual":
            errs.append(f"{plat}/{inv}/{md.name} trigger={d.get('trigger')!r}; workflows must be `manual`")
```
Note: `fm_dict()` records list-valued keys like `paths:` with an empty string value (the `- "…"` items are skipped as they lack a colon), so `"paths" in d` is a valid presence check.

## Step 8 — `AGENTS.md` §8 (BOTH `src/constitution/AGENTS.md` and repo-root `AGENTS.md`)

Add this bullet to the §8 Pointer Directory, immediately after the OKF pointer line (before the closing ```` `` ````):
```markdown
- **Host activation:** Antigravity loads these rules from `.agents/rules/` via their `trigger`/`globs` frontmatter. Claude Code loads `glob` rules (e.g. `okf-protocol`) natively from `.claude/rules/` via `paths:` when matching files are touched; `always_on` rules (`output-mode`, `memory-protocol`) load via the pointers above. Contract: `okf-protocol.md` §2.1.
```
Bump versions + timestamps: `src/constitution/AGENTS.md` `2.0.0 → 2.0.1`; repo-root `AGENTS.md` `1.0.3 → 1.0.4`; both `timestamp: 2026-07-17`.

## Step 9 — Rebuild

`python build/build.py` (regenerates both `dist/` trees + `versions.json` + marketplace).

---

# Verification

- `python build/build.py` clean; `python build/validate.py` → `VALIDATION OK` (incl. §2.6 checks).
- `python build/bump_guard.py` passes (VERSION 2.2.0 > v2.1.0).
- Inspect `dist/{claude-code,antigravity}/assets/templates/rules/okf-protocol.md`: both carry `globs` + `paths` (byte-identical across dists); `output-mode.md`/`memory-protocol.md` are `always_on`.
- Inspect a built command, e.g. `dist/claude-code/commands/4a_verify-and-ship.md`: `trigger: manual`.
- **Host-conditional dry-runs** (run the dist copy of `scaffold.py` with `--dry-run` from a temp cwd):
  - Claude install → `okf-protocol` appears under **both** `.agents/rules/` and `.claude/rules/`; `always_on` rules under `.agents/rules/` only.
  - Antigravity install → **no** `.claude/rules/`; all rules under `.agents/rules/`.
  - Scope derives from the invoking plugin-root path; to force a host, invoke from a matching plugin location or temporarily stub `scope`.
- Spot-check in a real Antigravity workspace that a `glob` rule fires on a matching file; in Claude, confirm `/context` shows the path-scoped rule loading when a matching file is read. *(Unverified at authoring — no live Antigravity session.)*

---

# Appendix A — workflow trigger migration (throwaway; do not commit)

```python
#!/usr/bin/env python3
"""One-off: normalize workflow `trigger:` to `manual`, bump patch version + timestamp."""
import re
from pathlib import Path

WF = Path("src/workflows")   # run from repo root
TODAY = "2026-07-17"

def split_fm(text):
    m = re.match(r"^(---\r?\n)(.*?)(\r?\n---\r?\n?)(.*)$", text, re.S)
    return m.groups() if m else None

def bump_patch(v):
    a, b, c = v.split("."); return f"{a}.{b}.{int(c)+1}"

for f in sorted(WF.glob("*.md")):
    parts = split_fm(f.read_text(encoding="utf-8"))
    if not parts:
        continue
    open_, fm, close_, body = parts
    lines = fm.split("\n")
    had = False
    for i, ln in enumerate(lines):
        if re.match(r"^trigger:", ln):
            lines[i] = "trigger: manual"; had = True; break
    if not had:
        for i, ln in enumerate(lines):
            if re.match(r"^type:", ln):
                lines.insert(i + 1, "trigger: manual"); break
    for i, ln in enumerate(lines):
        m = re.match(r'^version:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?', ln)
        if m:
            lines[i] = f'version: "{bump_patch(m.group(1))}"'; break
    had_ts = False
    for i, ln in enumerate(lines):
        if re.match(r"^timestamp:", ln):
            lines[i] = f"timestamp: {TODAY}"; had_ts = True; break
    if not had_ts:
        lines.append(f"timestamp: {TODAY}")
    f.write_text(open_ + "\n".join(lines) + close_ + body, encoding="utf-8", newline="\n")
```
