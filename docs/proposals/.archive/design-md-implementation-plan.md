---
type: implementation-plan
title: "DESIGN.md tool-agnostic OKLCH SSOT + design-theme — implementation plan"
status: ready-to-implement
date: 2026-06-25
source_of_truth: docs/proposals/stitch-design-md-resolution.md
audience: "an implementing agent with NO prior context on this analysis"
---

# Implementation Plan — DESIGN.md OKLCH SSOT + `design-theme`

> **You are implementing a feature for StratosphereOS (StratOS).** You do **not** need the full analysis.
> This document is self-contained and verifiable. Rationale lives in the source proposal
> ([stitch-design-md-resolution.md](stitch-design-md-resolution.md)); read it only if a step is unclear.
> **Do not change scope or invent behavior** — implement exactly what is specified, and verify each phase.

---

## 0. Orientation (read once)

**What StratOS is.** A scaffolding "plugin" that an AI agent installs into a target project. It ships durable memory templates, workflows, and helper scripts. It is **host-agnostic**: it must work identically under **Claude Code (Anthropic)** and **Antigravity (Google/Gemini)**. Never assume one vendor.

**What you are building.** Make `DESIGN.md` a **tool-agnostic, OKLCH-native design source-of-truth
(SSOT), and add a deterministic generator (`design-theme`) that projects it into the app's Tailwind v4 / shadcn `globals.css`. A user picks their **design source** (`stitch` | `claude-design` |`native`) at setup; all sources feed the one SSOT. Color stays **OKLCH end-to-end** (Tailwind v4 + shadcn accept `oklch()` natively) — there is **no hex conversion anywhere**.

**Seven decisions you must honor (do not re-litigate):**
| ID | Decision |
|---|---|
| D1 | `DESIGN.md` colors are **OKLCH**. No hex conversion in the pipeline. |
| D2 | The `@google/design.md` lint toolchain is **installed at setup only when gated** (design source = `stitch`, or a UI/Node project that wants spec-lint). `claude-design` (OKLCH-preserving, Anthropic-native) and `native`/offline/non-Node → skip. |
| D3 | `DESIGN.md` token names are **portable/semantic** (`primary`, `secondary`, `tertiary`, `neutral`, `surface`, `on-surface`, `error`). shadcn variable names are produced by `design-theme` at build time — **not** authored in `DESIGN.md`. |
| D4 | Build **`design-theme`** now. **No `design-export`** (cut). `design-import` is **optional** (a later, separate task). |
| D5 | Typography `fontFamily` values come from the **Google Fonts catalog** (so generators render them and the app self-hosts them). |
| D6 | One SSOT, **vendor-neutral**; the design source is a setup-time choice; never two synced files. |
| D7 | **Dark mode = hybrid.** `DESIGN.md` stays single-palette (standard); `design-theme` **derives** a role-aware, contrast-checked `.dark` block from the light OKLCH, **overridable** per-token by an optional `colorsDark:` group (see §2.5b). |

**Critical ground rules:**
- **All product changes go in `src/`.** The build (`python build/build.py`) packages `src/` → `dist/`
  (two variants: `dist/antigravity/`, `dist/claude-code/`). **Never hand-edit `dist/`.** `build/` itself
  (`build.py`, `validate.py`) is **dev tooling, not product** — do not treat it as a product change.
- After any `src/` change you **must** run `python build/build.py` and confirm `dist/` is regenerated;
  CI `.github/workflows/build-guard.yml` enforces `dist == build(src)`.
- **Helper scripts live in `src/scripts/`** (all Python, stdlib-only). `scaffold.py` deploys selected scripts
  into a target project's `.agents/scripts/`. So `design-theme`'s **source** is `src/scripts/design/`; its
  **deploy target** in a generated project is `.agents/scripts/design/`.
- **Host-agnostic phrasing in workflows:** where a workflow asks the user something, it already uses
  "`AskUserQuestion` (Claude Code) / `ask_question` (Antigravity)" — preserve that dual phrasing.
- **`design-theme` is pure Python, no third-party deps.** OKLCH passes through verbatim; the only math is a
  `-foreground` lightness flip and `clamp()` arithmetic. No PyYAML requirement (see §2.3).
- **Windows (Antigravity) shell note:** PowerShell's ExecutionPolicy can block the `npm`/`npx` `.ps1` shims. If
  an `npm install` / `designmd` call fails with an ExecutionPolicy error, invoke via `cmd /c "npm …"` /
  `cmd /c "npx …"`, or run it through the Git-Bash shell. (Python / `scaffold.py` are unaffected.)

**Branch/commit hygiene:** work on the current branch in this worktree. Do **not** push or open a PR unless
explicitly asked. Commit per phase with clear messages.

---

## 1. Phases overview (suggested order)

| # | Phase | Files (all under `src/`) | Risk |
|---|---|---|---|
| A | Rule + template edits | `memory-templates/DESIGN_RULES.md`, `memory-templates/DESIGN.md` | Low |
| B | Build `design-theme` (+ tests) | `scripts/design/design_theme.py`, `scripts/design/test/…` | **Med (core)** |
| C | Lint-toolchain template + scaffold wiring | `scripts/design/package.json`, `scripts/scaffold.py` | Med |
| D | Setup workflow edits | `commands/instantiate/Instantiate-StratosphereOS.md` | Low |
| E | `2b` workflow edits (invoke + drift gate) | `workflows/2b_interface-design.md`, `workflows/3d_implement-issue.md`, `workflows/4a_verify-and-ship.md` | Med |
| F | Brief-guide edits | `references/stitch-brief-guide.md` | Low |
| G | Regenerate `dist/` + verify | (runs `build/build.py`) | Low |
| H | Dev-tooling cleanup (optional, **outside `src/`**) | `build/build.py:87` | Low |

Phases A–C are independent of D–F and can be done in parallel; G is last. Do **B** carefully — it is the core.

---

## 2. Phase B — `design-theme` (the core; spec in full)

> Build this first if you prefer; the rest is editing. It is a **deterministic, idempotent pure function**:
> `DESIGN.md` (OKLCH frontmatter) → a shadcn/Tailwind-v4 `globals.css` fragment.

### 2.1 Location & CLI
- **File:** `src/scripts/design/design_theme.py` (Python 3, stdlib only).
- **CLI:**
  ```
  python design_theme.py --design <path/to/DESIGN.md> --out <path/to/theme.tokens.css>
  python design_theme.py --design <path/to/DESIGN.md> --check <path/to/theme.tokens.css>   # drift gate
  python design_theme.py --design <path/to/DESIGN.md>                                       # print to stdout
  ```
  - `--out` is the path to a **dedicated generated stylesheet** that `design-theme` owns entirely (default
    name `theme.tokens.css`, see §2.4). It writes with **LF newlines** and a fixed key order. The script does
    **no** path discovery — the caller/workflow supplies the path.
  - `--check` regenerates in memory and compares to the file at the path; **exit 0 if identical, exit 1 if
    different** (prints a unified diff). This is the drift gate used by `4a`/CI.
- **Idempotent:** running twice on the same input yields byte-identical output.

### 2.2 Inputs it reads (the `DESIGN.md` frontmatter schema)
```yaml
colors:        { <name>: "oklch(L C H)" , ... }   # names per D3
colorsDark:    { <name>: "oklch(L C H)" , ... }   # OPTIONAL per-token dark overrides (D7/§2.5b); omitted tokens are derived
typography:    { <level>: { fontFamily, fontSize, fontWeight, lineHeight, letterSpacing? } , ... }
spacing:       { <level>: "<n>px" , ... }
rounded:       { <level>: "<n>px" | "9999px" , ... }
# `components`, `version`, `name`, `description` are present but NOT consumed by design-theme.
```

### 2.3 YAML parsing without dependencies (important)
There is **no guaranteed PyYAML** in a target project. Implement a **minimal stdlib parser** for this
*constrained, regular* schema (2-space indentation, one nesting level under `typography`/`components`,
scalar values, quoted strings). Acceptable shortcut: `try: import yaml` as a fast path, but the stdlib
fallback **must** work and is what tests exercise. First confirm whether `src/scripts/` already contains a
frontmatter helper you may reuse; if not, write a small local one. **The file's first line must be `---`**
(a leading comment breaks downstream tooling — see §3 of the source proposal); reject/΄warn if not.

### 2.4 Output: shadcn / Tailwind v4 `globals.css` fragment
Emit `:root` (light) + `.dark` (dark, per §2.5b) + `@theme inline`, plus the `@custom-variant dark` line shadcn uses:
```css
:root {
  --radius: <rounded.md or 0.625rem>;
  --background: <oklch surface>;
  --foreground: <oklch on-surface>;
  --card: <oklch surface>;
  --card-foreground: <oklch on-surface>;
  --popover: <oklch surface>;
  --popover-foreground: <oklch on-surface>;
  --primary: <oklch primary>;
  --primary-foreground: <derived>;
  --secondary: <oklch secondary>;
  --secondary-foreground: <derived>;
  --muted: <oklch neutral>;
  --muted-foreground: <light: oklch(0.50 C H) from on-surface — deterministic, see note>;
  --accent: <oklch tertiary>;
  --accent-foreground: <derived>;
  --destructive: <oklch error>;
  --border: <oklch neutral>;
  --input: <oklch neutral>;
  --ring: <oklch primary>;
}
@custom-variant dark (&:is(.dark *));
.dark {
  /* same keys as :root; value = colorsDark.<token> if present, else derived per §2.5b */
  --background: <dark surface>;  --foreground: <dark on-surface>;
  /* …one entry per :root color token… */
}
@theme inline {
  --color-background: var(--background);
  /* …one --color-<token> per :root color token… */
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: var(--radius);
  --radius-lg: calc(var(--radius) + 4px);
}
```
> **Verify the exact block against a current `npx shadcn@latest init` `globals.css`** before finalizing (shadcn's
> structure evolves) and pin your golden test to it. Keep OKLCH values **verbatim** from `DESIGN.md`.

**Canonical StratOS → shadcn mapping (default; this is the spec):**
| StratOS token | shadcn var(s) |
|---|---|
| `surface` | `--background`, `--card`, `--popover` |
| `on-surface` | `--foreground`, `--card-foreground`, `--popover-foreground`, `--muted-foreground` |
| `primary` | `--primary`, `--ring` |
| `secondary` | `--secondary` |
| `tertiary` | `--accent` |
| `neutral` | `--muted`, `--border`, `--input` |
| `error` | `--destructive` |
| *(derived)* | `--primary-foreground`, `--secondary-foreground`, `--accent-foreground` |

If a source token is absent, fall back: `surface`→use `neutral`; `on-surface`→ a near-black neutral. Emit a
`/* design-theme: <token> missing, fell back to <x> */` comment so it's visible.

**Deterministic `--muted-foreground` (no "or derived" guessing):** light = `oklch(0.50 C H)` using the C/H of
`on-surface`; dark = `oklch(0.70 C H)` (§2.5b). It is **not** verbatim `on-surface` (that would equal
`--foreground`). The L constants are tunable — pin them in the golden test.

**Output is a self-owned file, not a splice.** `design-theme` writes a **complete, dedicated** stylesheet
(default `theme.tokens.css`) that the project's main CSS `@import`s **once**. Because the script owns the whole
file, `--check` can compare **byte-exact**. Do **not** splice generated tokens into a hand-maintained
`globals.css` — that makes `--check` impossible (the file would also contain `@import "tailwindcss";`,
`@custom-variant dark`, etc. the script doesn't emit). The project's `globals.css` keeps its imports/variants
and adds `@import "./theme.tokens.css";`. **Deterministic key order = the §2.4 mapping-table order**, then
typography, then spacing/radius.

### 2.5 The two bits of math (pure arithmetic on the OKLCH string)
- **`-foreground` derivation.** Parse `L` (first number) from a token's `oklch(L C H)`. Emit foreground =
  `oklch(0.985 0 0)` if `L < 0.5`, else `oklch(0.205 0 0)`. (High-contrast neutral text; the linter's
  `contrast-ratio` rule validates — if it warns, the implementer adjusts the source token, not the heuristic.)
  **Non-OKLCH input:** D1 expects OKLCH, but if a color value is not `oklch(...)`, pass it through to the CSS
  var verbatim (Tailwind accepts hex), **default** its foreground to `oklch(0.205 0 0)`, and emit a
  `/* design-theme: non-oklch <token>; foreground defaulted */` warning comment.
- **Fluid `clamp()` (DR-003).** Applies to `typography.*.fontSize` and `spacing.*` whose px value `≥ 16`.
  Given anchor `MAX` (px) → `MIN = max(round(MAX*0.66), 12)`; reference viewports 360px→1280px:
  ```
  clamp(MINpx, calc(MINpx + (MAX - MIN) * ((100vw - 360px) / (1280 - 360))), MAXpx)
  ```
  Values `< 16px` and `rounded.*` (radii) pass through unchanged; `9999px` passes through. Use `round()` for
  `MIN`. **Emit the canonical string exactly** (pin it in the golden test): a 48px anchor →
  `clamp(32px, calc(32px + 16 * ((100vw - 360px) / 920)), 48px)` — here `16 = MAX − MIN`, `920 = 1280 − 360`;
  the parenthetical resolves to a length, so the whole expression types as a length in CSS `calc`.

### 2.5b Dark-mode derivation (D7)
`design-theme` emits a `.dark` block. Each token's dark value is **`colorsDark.<token>` if present (verbatim), else derived** from the light `oklch(L C H)` by role (deterministic arithmetic on `L`/`C`, hue preserved):

| Role (shadcn var) | Dark value derived from light `oklch(L C H)` |
|---|---|
| backgrounds/surfaces (`--background`,`--card`,`--popover`) | `oklch(0.17 min(C,0.02) H)` |
| text (`--foreground` & `*-foreground`) | `oklch(0.96 min(C,0.02) H)` |
| `--muted` / `--muted-foreground` | `oklch(0.24 min(C,0.03) H)` / `oklch(0.70 C H)` |
| `--border`,`--input` | `oklch(0.27 min(C,0.03) H)` |
| brand accents (`--primary`,`--secondary`,`--accent`,`--ring`) | lighten + slightly desaturate: `oklch(min(L+0.06, 0.85) C*0.92 H)` |
| `--destructive` | `oklch(max(L, 0.55) C H)` |
| accent `-foreground` | the §2.5 L-flip rule applied to the **dark** accent value |

- **`colorsDark` is optional & additive** — if absent, the file stays a standard single-palette `DESIGN.md`
  (D6/portability). Overrides are per-token (tune only the few that need it).
- **`design-theme` MUST validate each `.dark` background/text pair for WCAG AA (≥4.5:1)** and emit a
  `/* design-theme: dark contrast <token> = X:1 below AA */` warning — the `@google/design.md` linter does
  **not** lint `colorsDark` or the derived `.dark` block (verified: it counts only `colors`), so this is on us.
- Exact L/C constants are **tunable** — pin them in the golden test (like the clamp ratios, §7).

### 2.6 Tests (mandatory — this is how a neutral agent proves quality)
Place under `src/scripts/design/test/` (the build **excludes `test/` from `dist/`**). Use stdlib `unittest`
(no pytest). Run: `python src/scripts/design/test/test_design_theme.py`.
1. **Golden file:** fixture `fixtures/skycast.DESIGN.md` (a real OKLCH file — copy the schema from
   `docs/research/DESIGN_md/DESIGN mockup.md` but **without** the leading HTML comment) → assert byte-exact
   match to `fixtures/skycast.globals.css` (commit the expected output you verified by hand).
2. **Idempotency:** generate twice → identical bytes.
3. **`--check` drift:** generate, mutate one byte of the output, run `--check` → exit 1 + diff printed.
4. **Missing-token fallback:** a `DESIGN.md` without `surface` → output contains the fallback comment, still valid CSS.
5. **Leading-comment rejection:** a file starting with `<!-- … -->` → script errors clearly (does not emit garbage).
6. **clamp math:** `fontSize: 48px` → `clamp(32px, calc(32px + 16 * ((100vw - 360px)/920)), 48px)` (or your
   exact rounding) — pin it in the golden file.
7. **Dark derive:** a `DESIGN.md` with **no** `colorsDark` → output has `@custom-variant dark` + a `.dark` block
   with role-derived values (§2.5b); pin it in the golden file.
8. **`colorsDark` override:** add `colorsDark.primary` → that token's `.dark` value is the override verbatim;
   underridden siblings still derive.
9. **Dark contrast warning:** a `colorsDark` (or derived) bg/text pair below AA → script emits the dark-contrast warning comment.

**Acceptance for Phase B:** all 6 tests pass; output OKLCH values are verbatim from the input; running the
official linter on the *input* fixture (see §6) reports colors parsed (not dropped).

---

## 3. Phase A — Rules + template

### 3.1 `src/memory-templates/DESIGN_RULES.md`
All entries are `[LAW]`-tier. These are **proposed** rule changes — when this plan is executed inside a real
project the agent proposes them for user confirmation; **here you are editing the StratOS template**, so apply them directly to the template text.

| Rule | Exact change |
|---|---|
| **DR-001** | Replace "no default Inter font" with **"no *unchosen* or *Inter* default font (Inter is seen as AI slop and often an inherited tool default)"** Keep the rest of DR-001 unchanged. |
| **DR-002** | Append: "OKLCH is accepted end-to-end by the tooling (Stitch ingests it; the `@google/design.md` linter coerces it); **no hex conversion is needed**. Hex appears only if a generator emits it." |
| **DR-003** | Append the px-anchor→clamp rule: "px values in `DESIGN.md` are **desktop anchors**; `design-theme` emits `clamp(min, fluid, max)` (min = max·0.66 floored at 12px; viewports 360→1280px)." |
| **DR-009** | Reword: "Token Snap = **script does mechanical conversion, human curates** which tokens to keep. Applies to **any external source (Stitch / Claude Design)**." |
| **DR-010 / DR-015** | Generalize every "Stitch" → "**any external design generator (Stitch / Claude Design)**." Add to DR-015: "Claude Design's two-way Claude Code sync is **frozen** (ingest → snap → reconcile into the one SSOT; never live)." |
| **DR-011** | Generalize "Stitch" → "the chosen generator"; add "name the exact **Google Fonts** family so it renders as a hard constraint (DR-016)." |
| **DR-016** *(new, append after DR-015)* | "**[[DR-016]] [LAW]** Typography source — Google Fonts. Author every `DESIGN.md` `fontFamily` from the Google Fonts catalog (renderable by generators as a hard constraint; self-hostable via `next/font/google` / `@fontsource`). Non-GF brand fonts: keep the real family in the SSOT and declare a Google Fonts **stand-in for mockups only**, applying the real font at implementation. Pair wide choice with restraint: one display/serif + one neutral/sans." |
| **§2 field** | In the §2 header block, rename **`Stitch Status: <yes\|no>`** → **`Design Source: <stitch \| claude-design \| native — set during /stratosphere-setup>`**. Keep `Design References` for the `native` case. Update §2 prose that says "Stitch Status = no" to "Design Source = native". |
| **Line ~44 ("DESIGN.md round-trip")** | Fix the wording: clarify "Stitch-spec `DESIGN.md`" means **conforms to the open DESIGN.md format** (not "Stitch is the SSOT"); replace "never hand-resync tokens" with "tokens are reconciled by the Token-Snap **script/agent**, not hand-synced." |

> **`Stitch Status` appears in THREE `src` files** — `memory-templates/DESIGN_RULES.md` (§2, ≈ lines 37/40),
> `commands/instantiate/Instantiate-StratosphereOS.md` (Checkpoint 8, ≈ line 241), and
> `workflows/2b_interface-design.md` (Phase 1 step 4, ≈ lines 23/26). **All three** must migrate to
> `Design Source` (Phases D and E cover the latter two). DR-012/DR-013 (example-purge rules) are unrelated and stay untouched.

**Acceptance:** `DESIGN_RULES.md` still parses as the project's OKF doc; DR-016 present; **no `Stitch Status`
string remains in any `src` file** (replaced by `Design Source`); DR-007/008/012/013/014 untouched.

### 3.2 `src/memory-templates/DESIGN.md`
- **Keep OKLCH.** Keep the existing 4 colors; **add** `surface`, `on-surface`, `error` (placeholder OKLCH
  values consistent with a neutral light theme).
- **Typography:** set `fontFamily` placeholders to a **Google Fonts** family with an inline comment, e.g.
  `fontFamily: <Google Fonts family, e.g. "Inter">  # DR-016: must be a Google Fonts family`.
- **File must start with `---`** (it already does — confirm no leading comment is ever added).
- Add a one-line comment in the body: `<!-- shadcn variable names are generated from these tokens by design-theme (see .agents/scripts/design) -->` (place it **after** the frontmatter, inside the markdown body, never before `---`).
- **Do NOT add a `colorsDark:` block by default** (D7 — single-palette is the standard; `design-theme` derives dark). In the body comment, show the optional override syntax so authors know it exists, e.g. `<!-- optional dark overrides: add a top-level colorsDark block; omitted tokens are derived. Example:\ncolorsDark:\n  primary: "oklch(0.4 0.1 120)"\n-->`.

**Acceptance:** `npx -p "@google/design.md@0.3.0" designmd lint src/memory-templates/DESIGN.md` (dev-time check; pin the version) parses successfully
(non-empty `designSystem`, `primary` present). Contrast warnings on placeholder values are acceptable (note them).

---

## 4. Phase C — Lint toolchain template + `scaffold.py`

### 4.1 `src/scripts/design/` (new product files)
- `design_theme.py` (Phase B).
- `package.json` — the **lint toolchain template** deployed into a project's `.agents/scripts/design/`:
  ```json
  {
    "name": "stratos-design-toolchain",
    "private": true,
    "version": "0.0.0",
    "dependencies": { "@google/design.md": "0.3.0" },
    "scripts": {
      "lint": "designmd lint",
      "diff": "designmd diff",
      "export-dtcg": "designmd export --format dtcg"
    }
  }
  ```
  > **Why this shape:** the bare `npx @google/design.md lint` no-ops on Windows and `@google/designmd` is a
  > 404. The working invocation is the package's **`designmd` bin** (used above via npm scripts, or
  > `npx -p "@google/design.md" designmd lint`). Pin `0.3.0`.
- Optionally a short `README.md` documenting the invocation + that it's installed only when gated (D2).
- **Runtime invocation uses the LOCAL pinned install — never `npx -p`** (which re-resolves/downloads and
  bypasses the `0.3.0` pin). Run from the toolchain dir: `npx --no-install designmd lint <abs-path>` (CWD =
  `.agents/scripts/design/`, so pass an **absolute** path to the `DESIGN.md`), or call
  `node_modules/.bin/designmd` directly. Reserve `npx -p "@google/design.md@0.3.0" …` only for one-off
  **dev-time** checks where no local install exists.

### 4.2 `src/scripts/scaffold.py`
- Add a deploy clause that copies `src/scripts/design/` (source: `PLUGIN_ROOT / "scripts" / "design"`) → the
  project's `.agents/scripts/design/`, deploying **each file with `tier="managed"`** — exactly how
  `validate_memory.py` is deployed (`scaffold.py:259`) — so `--update` byte-diff-refreshes it. **Skip any path
  containing a `test` segment** so `test/` is never copied into a project.
- **Do NOT mirror the `okf_viewer` copy block** — it is a *counter-example*, not a template: it uses the
  **default `tier="preserved"`** (never refreshed on `--update`) and copies via `rglob` with **no `test/`
  filter**. Following it would violate this plan's Definition of Done.
- **There is no script manifest/versions to register.** `versions.json` stamps only `.md` files
  (`build.py`: `if not f.endswith(".md"): continue`), and `scaffold.py`'s `map_bundled_to_project` has no
  `scripts/` branch. `--update` refresh for a script comes **only** from `tier="managed"`. Do not invent a
  versions/lockfile entry.
- **Do NOT run `npm install` from `scaffold.py`** — scaffolding is a zero-token deterministic file copy. The
  npm install is the setup **workflow's** job (Phase D), gated per D2.

**Acceptance:** `python src/scripts/scaffold.py --dry-run` (run from a scratch project dir) lists the new
`.agents/scripts/design/design_theme.py` and `package.json` under "WOULD CREATE"; `test/` is not listed.

---

## 5. Phases D–F — Workflow & guide edits

### 5.0 Design-source specifics (one lifecycle, per-source guards)

Every source follows the **same lifecycle** (feed current system → scoped brief → MCP ingest → freeze →
reconcile into the OKLCH `DESIGN.md` SSOT → re-express in shadcn). Only these details differ:

| | `stitch` | `claude-design` | `native` |
|---|---|---|---|
| Feed current system (DR-011) | set `.memory/DESIGN.md` as the Stitch Design System | **`/design-sync`** the StratOS system (DESIGN.md + shadcn) into Claude Design | n/a — agent uses `DESIGN.md` as context |
| Ingest via MCP | **pull-only** (`build_site` / `get_screen_code` / `get_screen_image`) | **handoff/implement** (writes code) + two-way `/design-sync` | n/a |
| Color on ingest | re-derives → **hex** → mechanical snap **hex→OKLCH** | **OKLCH preserved** (verified) — no snap | authored OKLCH directly |
| Components (DR-004) | always re-express in shadcn | targets your shadcn **only if `/design-sync` first** — **never cold-implement** (cold ⇒ bespoke ⇒ DR-004 break) | shadcn by default |
| Emits a `DESIGN.md`? | No | No — one-way (`DESIGN.md` → generator → reconcile) | n/a |
| Google lint toolchain (D2) | install | **not required** | not required |
| DR-015 guard | freeze; MCP is ingest-only | freeze; **never persist `/design-sync`** in CI / `mcpServers` | n/a |

**Verified** (real Claude Design product output — the SkyCast zip): it ingests an OKLCH `DESIGN.md`, **preserves
the exact tokens** (labels them `(spec)`), honors the type/spacing scales, and applies the Google-Fonts +
anti-Inter substitution (D5/DR-001) on its own. **Confirmed (per decision owner):** the sync-first handoff targets your shadcn components and preserves OKLCH. Stitch and Claude Design are **interchangeable generators behind one rule-set**
(DR-007/009/010/011/015); the rows above are the only per-source deltas.

### 5.1 `src/commands/instantiate/Instantiate-StratosphereOS.md` (Phase D)
- **Sweep stale Stitch wording (required — beyond Checkpoint 8).** The file still references Stitch elsewhere:
  line ~16 ("Stitch harmonization"), Checkpoint 4.2 (~line 166, "§2 Stitch Harmonization"), and Checkpoint 9
  step 5 (~line 273, "Google Stitch is OPTIONAL"). **Grep the file for `Stitch` / `Google Stitch` and
  neutralize every non-historical hit** to host-neutral **Design Source** wording (e.g. "design-source
  harmonization", "the chosen design source is OPTIONAL"). The plan says implement-exactly — so this sweep is
  explicit, not inferred.
- **Checkpoint 8:** change the question from "Does this project use Google Stitch? [yes/no]" to a
  **Design Source** choice: `stitch | claude-design | native` (use `AskUserQuestion` on Claude Code /
  `ask_question` on Antigravity). Write the answer to `DESIGN_RULES.md` §2 `Design Source`. For `native`,
  optionally collect Design References (as today).
- **Gated toolchain install (new step, after the source is known):** if Design Source = `stitch` **or** the
  project is a Node/UI project that wants spec-lint, run `npm install` inside `.agents/scripts/design/`
  (the agent runs it — never the user). For `claude-design`, `native`, non-Node, or offline: **skip and record**
  in `STATUS.md` that the Google lint seam is not provisioned (`claude-design` is OKLCH-preserving and needs no
  Google toolchain).
- **Checkpoint 4.1 step 6:** replace the "validate optionally with `npx @google/design.md lint`" line with a
  **working, agent-run, version-pinned** lint on the OKLCH source (file must start with `---`). Mind the
  ordering: Checkpoint 4.1 runs **before** the gated install (Checkpoint 8), so:
  - **If the gated toolchain is already installed** (§4.1) → use the local pin:
    `npx --no-install designmd lint "<abs path to .memory/DESIGN.md>"` from `.agents/scripts/design/`.
  - **Otherwise** (toolchain not yet provisioned at this point in setup) → use the pinned download form:
    `npx -p "@google/design.md@0.3.0" designmd lint .memory/DESIGN.md`.
  - **Never** the unpinned `npx @google/design.md` (no-ops on Windows) or unpinned `npx -p "@google/design.md"`
    (drifts off `0.3.0`).

### 5.2 `src/workflows/2b_interface-design.md` (Phase E-1)
- Generalize **Path A** label from "Stitch-assisted" to "**generator-assisted** (Stitch *or* Claude Design)".
- **Migrate the source-branching (required — easy to miss).** `2b` Phase 1 step 4 currently reads
  `Stitch Status` from `DESIGN_RULES.md` §2 and branches `yes`→Path A / `no`→Path B (≈ line 23), with the
  placeholder `<yes | no — …>` (≈ line 26). Change it to read **`Design Source`** and map
  `stitch`/`claude-design` → Path A (generator-assisted), `native` → Path B; update the placeholder to
  `<stitch | claude-design | native — set during /stratosphere-setup>`.
- **Per-source feed/ingest — follow §5.0:** Stitch = set `DESIGN.md` as Design System + MCP **pull** + snap
  hex→OKLCH; Claude Design = **`/design-sync` first** (never cold-implement → DR-004) + handoff; `native` =
  agent composition. All paths **freeze + reconcile** into the OKLCH SSOT (DR-015/DR-009) and re-express in shadcn.
- **Phase 4 (Harmonize & Freeze):** after the design system is snapped/frozen, the agent **runs
  `design-theme`** (`python .agents/scripts/design/design_theme.py --design .memory/DESIGN.md --out
  <app-css-dir>/theme.tokens.css`) to (re)generate the self-owned token file (§2.4). The **workflow** detects
  the CSS directory (Next.js `app/`, Vite `src/`) and ensures the main stylesheet `@import`s
  `theme.tokens.css` once; the **script** does no path discovery.
- Token-Snap wording → the §4.4 split (script mechanical, human curates).
- If/when `design-import` exists, make it **propose-only** with two guards: reject a file with a **leading
  comment before `---`** or **two `---` blocks**; flag a returned `fontFamily ≠ declared` (substitution).
- The Stitch brief step: **name the exact Google Fonts family** (DR-011/DR-016); fold in the operating
  practices from `stitch-brief-guide.md`.

### 5.3 `src/workflows/3d_implement-issue.md` (Phase E-2)
- Before building UI (shadcn step), regenerate the token file: run `design-theme --design .memory/DESIGN.md
  --out <app-css-dir>/theme.tokens.css`. Components bind to the generated CSS vars (per
  `references/shadcn-build-guide.md`).

### 5.4 `src/workflows/4a_verify-and-ship.md` (Phase E-3)
- Add a **drift gate**: run `design-theme --design .memory/DESIGN.md --check <app-css-dir>/theme.tokens.css`;
  **fail the ship** if it exits non-zero (the committed token file is out of sync with the SSOT, or was
  hand-edited). Because the script owns the whole file, the comparison is byte-exact.

### 5.5 `src/references/stitch-brief-guide.md` (Phase F)
- Add: feed `DESIGN.md` as the generator's Design System (no inlined token values); **name the exact Google
  Fonts family** (DR-016); fold in operating practices: pick model/mode by phase; *generate broad, edit
  surgical* (Direct Edits in context, one change at a time); web layouts need richer prompts; generator
  output is a translation base (re-express in shadcn, never paste markup).

**Acceptance (D–F):** no remaining "Stitch Status" string in workflows; `2b`/`3d`/`4a` reference
`design-theme` with the correct invocation; setup gates the npm install per source.

---

## 6. Phase G — Regenerate `dist/` and verify everything

1. `python build/build.py` → regenerates `dist/antigravity/` and `dist/claude-code/`. Confirm the changed
   templates/scripts/workflows appear in both variants (e.g. `dist/*/scripts/design/design_theme.py`,
   updated `DESIGN_RULES.md`, `DESIGN.md`).
2. Run the repo's build guard locally if present (`python build/validate.py`); ensure no errors.
3. **Full verification matrix:**

| Check | Command / action | Expected |
|---|---|---|
| design-theme unit tests | `python src/scripts/design/test/test_design_theme.py` | all pass |
| Template lints | `npx -p "@google/design.md@0.3.0" designmd lint src/memory-templates/DESIGN.md` (dev-time; pin version) | parses; `primary` present; OKLCH coerced (not dropped) |
| Leading-comment guard | lint a copy with a leading `<!-- -->` | reproduces "No YAML content found" (proves why the template must start with `---`) |
| scaffold dry-run | `python src/scripts/scaffold.py --dry-run` in a scratch dir | lists `.agents/scripts/design/{design_theme.py,package.json}`; no `test/` |
| design-theme e2e | run on `src/memory-templates/DESIGN.md` → temp css | valid shadcn `:root` + `@theme inline`; OKLCH verbatim; clamp() on ≥16px tokens |
| drift gate | `design_theme.py --check` on an edited css | exit 1 + diff |
| dist sync | `python build/build.py` then check `git status` | only intended files changed; build-guard would pass |

---

## 7. Phase H — Dev-tooling cleanup (optional, **outside `src/`**)

`build/build.py` line ~87 contains dead code: `version = None if srcfile.name == "DESIGN.md" else VERSION`.
It is unreachable (`memory-templates/` is copied via `copytree`, not `copy_md_with_frontmatter`). Remove it.
This is a **dev-tooling** change, not part of the product; keep it in a separate commit. Also confirm the build
never prepends a comment before a `DESIGN.md` `---` (would break the linter).

---

## 8. Out of scope (do NOT build now)
- **`design-export` (OKLCH→hex):** cut — verified unnecessary (Stitch ingests OKLCH; linter coerces it).
- **`design-import`:** optional; spec is in the source proposal §4.3. If asked later, build it one-shot,
  propose-only, with the two guards. Not part of this plan's acceptance.
- **Dark mode:** now **in scope** (D7 / §2.5b) — `design-theme` derives a `.dark` block + honors an optional
  `colorsDark` override. *Out:* a separately hand-*designed* dark theme beyond the derived baseline + per-token overrides.
- **Claude Design is an IN-scope Design Source** (see §5.0). What stays out: **adopting its bespoke component
  bundle** (DR-004 → re-express in shadcn) and any **persistent `/design-sync` dependency** (DR-015).

---

## 9. Definition of done
- [ ] Phase A–F edits applied **in `src/`**; no `dist/` hand-edits.
- [ ] `design-theme` built (pure Python, no deps) with all §2.6 tests passing.
- [ ] `design-theme` emits `@custom-variant dark` + a derived `.dark` block, honors `colorsDark` overrides, and validates dark contrast (D7 / §2.5b).
- [ ] `DESIGN.md` template lints clean (parses, OKLCH coerced); starts with `---`.
- [ ] `scaffold.py` deploys `design/` (excluding `test/`); `--update` tracks it.
- [ ] Setup gates the npm install per Design Source; lint uses the working `designmd` invocation.
- [ ] `2b` regenerates the theme on freeze; `4a` drift-gate added; `3d` regenerates before build.
- [ ] `2b` encodes the §5.0 per-source guards (Stitch pull+snap; Claude Design **sync-first, never cold-implement**; never persist `/design-sync`).
- [ ] `python build/build.py` run; `dist/` regenerated; build-guard would pass.
- [ ] (Optional) `build/build.py:87` dead code removed in a separate commit.

---

*Source of truth for rationale: [stitch-design-md-resolution.md](stitch-design-md-resolution.md). If this plan
and that proposal disagree, the proposal's decisions (D1–D7) win; fix this plan.*
