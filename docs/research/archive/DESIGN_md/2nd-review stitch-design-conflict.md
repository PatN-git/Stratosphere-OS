# 2nd Review: Stitch DESIGN.md Schema Conflict — Deep Analysis

> **Date:** 2026-06-24  
> **Reviewer:** Antigravity (Claude Opus 4.6)  
> **Branch:** `review-stitch-design-conflict` (at `f2bd390`, up-to-date with `origin/main`)  
> **Prior art:** [`stitch-design-schema-conflict.md`](./stitch-design-schema-conflict.md)  
> **Mockup evidence:** [`DESIGN mockup copied back from Stitch.md`](./DESIGN%20mockup%20copied%20back%20from%20Stitch.md)  
> **Official spec source:** [`Stitch-Docs.md`](./Stitch-Docs.md) (copied from Stitch docs pages)

---

## 1. Executive Summary

The StratosphereOS `DESIGN.md` template and the Google Stitch / `DESIGN.md` open-source specification (repo: [`google-labs-code/design.md`](https://github.com/google-labs-code/design.md)) are **structurally compatible but semantically divergent**. The first review correctly identified the core tension but understated a critical nuance: **the official spec is format-agnostic on color encoding**. The real conflicts are narrower — and more actionable — than initially presented.

### Key finding changes from 1st review

| Area | 1st Review Assessment | 2nd Review (with official spec) |
|---|---|---|
| Color format | "Stitch expects hex" | ✅ **Confirmed: spec mandates `# + hex code (sRGB)`**. OKLCH is a spec violation. |
| Typography weights | "String-wrapped required" | Spec says `number` (e.g., 400, 700). _"In YAML, bare numbers and quoted strings are equivalent"_ — so both parse identically |
| Spacing units | "Stitch requires rem" | Spec type is `Dimension` = `number + unit (px, em, rem)`. Both `px` and `rem` are valid |
| Material 3 tokens | "Stitch requires 50+ M3 surface tokens" | Spec only requires `name` + `colors`; M3 palette is **Stitch's default expansion**, not a spec requirement. Spec's "Consumer behavior" explicitly says: _"Unknown color token name → Accept if value is valid"_ |
| Round-trip compatibility | "Incompatible" | **Partially compatible** — the spec tolerates unknown tokens but Stitch's _output_ overwrites/expands the schema |
| `version` / `description` | _(not addressed)_ | **Both are in the official schema** as optional fields. StratOS's `type: design` field is the only non-spec addition |

---

## 2. Official Specification Analysis

### 2.1 Source of Truth

- **Repository:** [google-labs-code/design.md](https://github.com/google-labs-code/design.md) (Apache-2.0)
- **CLI tool:** `@google/design.md` (npm package `npx @google/design.md [command]`)
- **Stitch integration docs:** [stitch.withgoogle.com/docs/design-md/](https://stitch.withgoogle.com/docs/design-md/) → copied locally as [`Stitch-Docs.md`](./Stitch-Docs.md)
- **Community reference:** [designmd.app](https://designmd.app) (454 documented DESIGN.md files)

> [!NOTE]
> The Stitch documentation pages are client-rendered SPAs and cannot be scraped. The official content was manually copied into [`Stitch-Docs.md`](./Stitch-Docs.md) and is the basis for the analysis below.

### 2.2 File Structure (Official Spec)

The spec prescribes a two-layer markdown file. Per the official specification:

> _"A DESIGN.md file has two layers. The YAML front matter contains machine-readable design tokens — the precise values agents use to enforce consistency. The markdown body provides human-readable design rationale organized into ## sections."_

```
---                          ← YAML frontmatter start
name: "Project Name"         ← REQUIRED
colors:                      ← Token group
  primary: "#hexcode"
  ...
typography:                  ← Token group
  headline:
    fontFamily: Geist
    fontSize: 2rem
    fontWeight: 600
    ...
spacing:                     ← Token group
  sm: 8px
  ...
rounded:                     ← Token group
  sm: 4px
  ...
components:                  ← Component token group
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral}"
    ...
---                          ← YAML frontmatter end

## Overview                  ← Canonical section 1
## Colors                    ← Canonical section 2
## Typography                ← Canonical section 3
## Layout                    ← Canonical section 4
## Elevation & Depth         ← Canonical section 5
## Shapes                    ← Canonical section 6
## Components                ← Canonical section 7
## Do's and Don'ts           ← Canonical section 8
```

### 2.3 Official Schema (Verbatim from Spec)

```yaml
version: <string>          # optional, current version: "alpha"
name: <string>             # REQUIRED
description: <string>      # optional
colors:
  <token-name>: <Color>    # Color = "# + hex code (sRGB)"
typography:
  <token-name>: <Typography>
rounded:
  <scale-level>: <Dimension>
spacing:
  <scale-level>: <Dimension | number>
components:
  <component-name>:
    <token-name>: <string | token reference>
```

**Official Token Types:**

| Type | Format | Example |
|---|---|---|
| Color | `# + hex code (sRGB)` | `"#1A1C1E"` |
| Dimension | `number + unit (px, em, rem)` | `48px`, `-0.02em` |
| Token Reference | `{path.to.token}` | `{colors.primary}` |
| Typography | composite object | See properties below |

**Typography properties:** `fontFamily` (string), `fontSize` (Dimension), `fontWeight` (number), `lineHeight` (Dimension \| number), `letterSpacing` (Dimension), `fontFeature` (string), `fontVariation` (string)

### 2.4 What the Spec Requires vs What It Accepts

| Aspect | Official Spec | StratOS Template | Stitch Output | Conflict? |
|---|---|---|---|---|
| `name` field | ✅ Required | ✅ Yes | ✅ Yes | ❌ No |
| `version` field | Optional (`"alpha"`) | ✅ `"1.0.1"` | ❌ Not present | ❌ No |
| `description` field | Optional | ✅ Present | ❌ Not present | ❌ No |
| `colors` section | At minimum `primary` | ✅ Yes (4 tokens) | ✅ Yes (50+ tokens) | ⚠️ See §3.1 |
| **Color format** | **`# + hex code (sRGB)`** | **`oklch(...)` ❌** | `#hex` ✅ | **🔴 See §3.2** |
| Typography schema | `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing` | ✅ Matches | ✅ Matches | ❌ No |
| `fontWeight` type | `number` (bare or quoted equivalent in YAML) | Numeric (`600`) ✅ | String (`'700'`) ✅ | ❌ No |
| Spacing/Radius units | `Dimension` (px, em, rem) | `px` ✅ | `rem` ✅ | ❌ No |
| `{ref}` syntax | ✅ Supported | ✅ Used in `components` | Not observed | ❌ No |
| Canonical sections | Ordered (may omit) | ✅ All 8 present | ✅ All 8 present | ❌ No |
| `type` field | **Not in official schema** | ✅ `type: design` | ❌ Not present | ⚠️ See §3.4 |
| Unknown tokens | _"Accept if value is valid"_ | N/A | Adds 50+ M3 tokens | ⚠️ See §3.1 |

### 2.5 CLI Linting Rules (All 8, from Official Docs)

The `npx @google/design.md lint` command runs exactly **8 rules**:

| # | Rule | Severity | What It Checks | StratOS Impact |
|---|---|---|---|---|
| 1 | `broken-ref` | **error** | Token references `{path.to.token}` that don't resolve; unknown component sub-token property names | ✅ StratOS template references are valid. Component properties use the recognized set. |
| 2 | `missing-primary` | warning | Colors defined but no `primary` exists | ✅ StratOS has `primary` |
| 3 | `contrast-ratio` | warning | Component `backgroundColor`/`textColor` below WCAG AA 4.5:1 | 🔴 **Linter resolves token refs to hex values for contrast calc. If OKLCH is used, the linter likely cannot compute contrast.** |
| 4 | `orphaned-tokens` | warning | Color tokens defined but never referenced by any component | ⚠️ `secondary`, `tertiary`, `neutral` may trigger if not referenced in components |
| 5 | `missing-typography` | warning | Colors defined but no typography tokens exist | ✅ StratOS has typography |
| 6 | `section-order` | warning | Markdown sections out of canonical order | ✅ StratOS follows correct order |
| 7 | `missing-sections` | info | Optional sections (`spacing`, `rounded`) absent | ✅ StratOS has both |
| 8 | `token-summary` | info | Count of tokens defined per section (informational) | ✅ No action needed |

**Recognized component sub-token properties:** `backgroundColor`, `textColor`, `typography`, `rounded`, `padding`, `size`, `height`, `width`

**Recommended token names (from spec, not required):**
- Colors: `primary`, `secondary`, `tertiary`, `neutral`, `surface`, `on-surface`, `error`
- Typography: `headline-display`, `headline-lg`, `headline-md`, `body-lg`, `body-md`, `body-sm`, `label-lg`, `label-md`, `label-sm`
- Rounded: `none`, `sm`, `md`, `lg`, `xl`, `full`

---

## 3. Conflict Analysis — Dimension by Dimension

### 3.1 Color Token Granularity

**The core conflict is not format but _granularity_.**

| StratOS Template | Stitch Output |
|---|---|
| 4 semantic tokens: `primary`, `secondary`, `tertiary`, `neutral` | 50+ Material 3 tokens: `surface`, `surface-dim`, `surface-bright`, `surface-container-lowest`, `surface-container-low`, `surface-container`, `surface-container-high`, `surface-container-highest`, `on-surface`, `on-surface-variant`, `inverse-surface`, `inverse-on-surface`, `outline`, `outline-variant`, `surface-tint`, `primary`, `on-primary`, `primary-container`, `on-primary-container`, `inverse-primary`, `secondary`, `on-secondary`, `secondary-container`, `on-secondary-container`, `tertiary`, `on-tertiary`, `tertiary-container`, `on-tertiary-container`, `error`, `on-error`, `error-container`, `on-error-container`, `primary-fixed`, `primary-fixed-dim`, `on-primary-fixed`, `on-primary-fixed-variant`, `secondary-fixed`, `secondary-fixed-dim`, `on-secondary-fixed`, `on-secondary-fixed-variant`, `tertiary-fixed`, `tertiary-fixed-dim`, `on-tertiary-fixed`, `on-tertiary-fixed-variant`, `background`, `on-background`, `surface-variant` |
| + project-custom tokens allowed | + domain-specific tokens added (e.g., `sun-alert`, `background-neutral`) |

**Impact:** When Stitch ingests a 4-token DESIGN.md and generates UI, it _expands_ the palette to the full M3 set. When you copy the result back, you get a completely different color architecture than what went in.

**This is the fundamental round-trip problem** — not format incompatibility, but _schema expansion_.

### 3.2 Color Encoding: OKLCH vs Hex

> [!CAUTION]
> **This is the hardest conflict.** The official spec explicitly defines the Color type as `# + hex code (sRGB)` (see Token Types table in spec). StratOS uses `oklch(...)`. This is a **spec violation**, not merely a tooling concern.

| Aspect | Analysis |
|---|---|
| **Spec position** | **Explicit:** Color = `"# + hex code (sRGB)"`, example `"#1A1C1E"`. No mention of `oklch()`, `hsl()`, `rgb()`, or any other CSS color format |
| **Consumer behavior** | Spec says unknown color token _names_ are accepted _"if value is valid"_. But the Color _type_ itself is defined as hex only |
| **Linter behavior** | **Tested and confirmed:** The `@google/design.md` linter does *not* throw a hard error on `oklch(...)` (it reports 0 errors). However, it **silently drops** the OKLCH values from its parsed Abstract Syntax Tree (AST). Because the colors become invisible to the linter, crucial rules like `contrast-ratio` and `orphaned-tokens` cannot run. |
| **Stitch behavior** | Stitch _always_ outputs hex. It does not output OKLCH regardless of input format |
| **StratOS rationale** | OKLCH was chosen for perceptual uniformity — equal Lightness values produce equal perceived brightness. Hex does not have this property |

> [!NOTE]
> Because of the linter's "ghosting" behavior with OKLCH, StratOS files will technically pass CI linting, but without providing the actual safety guarantees the linter is meant to offer.

### 3.3 Units: px vs rem

| Aspect | Analysis |
|---|---|
| **StratOS** | Uses `px` for spacing (`4px`, `8px`, `16px`, `32px`, `64px`) and radius (`4px`, `8px`, `12px`, `9999px`) |
| **Stitch output** | Uses `rem` for radius (`0.25rem`, `0.5rem`, `0.75rem`, `1rem`, `1.5rem`) except `full: 9999px`. Uses `px` for spacing |
| **Spec position** | Both are valid CSS units; spec is unit-agnostic |
| **Practical impact** | Mixed units cause developer friction but not parsing failures. Stitch's radius output is internally consistent; StratOS's px-only approach is simpler |

**Verdict:** Low-severity conflict. Token Snap (DR-009) can handle this mechanically.

### 3.4 StratOS-Specific Frontmatter Fields

The StratOS template includes three extra top-level fields. Per the official schema, **two are actually standard**:

```yaml
version: "1.0.1"    # ✅ IN SPEC (optional, current spec version: "alpha")
description: <...>  # ✅ IN SPEC (optional)
type: design        # ❌ NOT IN SPEC — OKF classification
```

**Risk assessment:**
- `version` and `description` are **officially supported** optional fields. StratOS using `"1.0.1"` instead of `"alpha"` is fine — the spec doesn't constrain the value
- `type: design` is the **only non-spec field**. Per the spec's consumer behavior rules: _"Unknown content → Preserve; do not error."_ This should be tolerated by compliant consumers
- Stitch **silently ignores** unknown YAML keys (confirmed by the mockup: the Stitch output doesn't include `type`, but the original StratOS section below it retained it)

### 3.5 Typography: String vs Numeric fontWeight

| StratOS | Stitch Output | Spec |
|---|---|---|
| `fontWeight: 600` (numeric) ✅ | `fontWeight: '700'` (string) | `number` — _"Numeric weight (e.g., 400, 700). In YAML, bare numbers and quoted strings are equivalent"_ |

**Impact:** Zero. The spec explicitly notes YAML equivalence between `700` and `'700'`. StratOS's numeric form is the canonical representation. Token Snap normalizes to numeric. This is a non-issue.

### 3.6 Typography Token Naming

| StratOS | Stitch |
|---|---|
| Semantic roles: `h1`, `body-md`, `label-caps` | Material 3 scale: `headline-lg`, `headline-lg-mobile`, `body-md`, `label-caps` |

**Impact:** Moderate. Stitch may rename tokens to match M3 naming conventions, but the StratOS template's semantic names are **equally valid** per the spec. The spec doesn't prescribe token naming conventions within the `typography` group.

The mockup shows Stitch introduced a `headline-lg-mobile` variant not in the original — another case of schema expansion.

---

## 4. The Mockup Evidence — Detailed Analysis

The file [`DESIGN mockup copied back from Stitch.md`](./DESIGN%20mockup%20copied%20back%20from%20Stitch.md) is the smoking gun. It reveals Stitch's actual behavior:

### 4.1 Dual Frontmatter Problem

The file has **two YAML frontmatter blocks** separated by a Stratosphere version comment:

```
---
[Stitch's expanded output: lines 1-92]
---

<!-- stratosphere: version=1.0.0 updated=2026-06-17 -->
---
[Original StratOS input: lines 96-139]
---
```

**This is invalid YAML/Markdown.** A DESIGN.md file should have exactly one frontmatter block. The dual-block structure means:
1. Standard YAML parsers will only read the **first** block (Stitch's output)
2. The original StratOS tokens become dead content in the markdown body
3. The linter would likely fail or produce unexpected results

### 4.2 Schema Expansion Summary

| Token Group | StratOS Input Count | Stitch Output Count | Delta |
|---|---|---|---|
| Colors | 4 | 52+ | **+48 tokens added** |
| Typography | 3 roles | 4 roles | +1 (`headline-lg-mobile`) |
| Rounded | 4 | 6 | +2 (`DEFAULT`, changed values) |
| Spacing | 5 | 7 | +2 (`gutter`, `margin`) |

### 4.3 Value Transformations

| Token | StratOS Input | Stitch Output |
|---|---|---|
| `colors.primary` | `oklch(0.68 0.15 240)` | `#005da7` (hex approximation) |
| `rounded.sm` | `4px` | `0.25rem` |
| `rounded.md` | `8px` | `0.75rem` (≠ 8px!) |
| `rounded.lg` | `16px` | `1rem` (≠ 16px!) |
| `typography.h1.fontFamily` | `'SF Pro Display', sans-serif` | `Inter` (completely changed!) |
| `typography.h1.fontWeight` | `700` (numeric) | `'700'` (string) |

> [!CAUTION]
> **Stitch changed the font family** from `SF Pro Display` to `Inter` without being asked. This is a design decision override, not a format conversion. This confirms DR-015's wisdom: "Stitch output ingested once and frozen."

---

## 5. Review of DESIGN_RULES.md Consistency

The subagent research surfaced a critical inconsistency in `DESIGN_RULES.md`:

### Contradiction

| Source | Statement |
|---|---|
| **DESIGN_RULES.md line 44** | _"`.memory/DESIGN.md` IS a Stitch-spec `DESIGN.md` (open-source format). It is the SSOT."_ |
| **DESIGN_RULES.md line 40** | _"Treat Stitch as the **mood board**, not the **source of truth**."_ |

Line 44 implies bi-directional round-trip compatibility. Line 40 correctly positions Stitch as upstream inspiration only. **These contradict each other.**

### Resolution

Line 40 is correct. Line 44's claim that `.memory/DESIGN.md` "IS a Stitch-spec DESIGN.md" is **aspirationally true** (the format structure matches) but **practically misleading** (the token schema differs). It should be amended to:

> `.memory/DESIGN.md` **follows the open-source DESIGN.md format** (YAML frontmatter + markdown prose). It is the SSOT. Stitch reads this format natively, but Stitch's output will expand the token set beyond what StratOS defines. The Token Snap process (DR-009) normalizes Stitch's expanded output back to StratOS's canonical token architecture.

---

## 6. Impact on Existing Workflows

### 6.1 Workflow `2b_interface-design.md` — Token Snap Flow

The Token Snap (DR-009) in Phase 4 is **correctly designed** to handle the schema mismatch:

```
Stitch Output (hex/rem/50+ tokens)
    → Token Snap (DR-009)
        → Map hex to closest OKLCH
        → Convert rem to px
        → Discard M3 tokens not in StratOS schema
        → Preserve domain-specific tokens (user decision)
    → .memory/DESIGN.md (OKLCH/px/4-token)
```

**Assessment:** The workflow architecture is sound. The first review's concern about incompatibility is addressed by Token Snap — but **only if Token Snap is actually implemented**. Currently it's a documented process, not an automated script.

### 6.2 Workflow `2b` Greenfield Bootstrap

Lines 91-94 correctly handle the greenfield case:
- Token direction inverts: **extract** from Stitch output
- **Propose** seeding DESIGN.md (don't auto-commit)

This is the right approach. In greenfield, Stitch's M3 expansion is _welcome_ because there's no existing schema to protect.

---

## 7. Revised Resolution Paths

The 1st review proposed two paths. With the empirical linter data, here are the three viable paths forward:

### Path A: Dual-Schema with Automated Token Snap ⭐ (Recommended)

- **DESIGN.md stays OKLCH/px/semantic** internally — this is StratOS's internal SSOT for agents
- **Export script** converts to spec-compliant format (hex/sRGB) on demand for Stitch ingestion AND linting
- **Import script** (Token Snap) converts Stitch output back to OKLCH/px
- **Linter runs against the exported hex version**, not the OKLCH source

**Pros:** Preserves StratOS design principles (OKLCH perceptual uniformity), unlocks full use of the official linter (including contrast checks), clear separation of concerns.  
**Cons:** Requires implementing two JS/TS conversion scripts; the OKLCH source file is technically not spec-compliant (but that's by design — StratOS owns its internal format).  
**Effort:** Medium (scripts require programmatic use of the `@google/design.md` package + color space conversion).

> [!IMPORTANT]
> Given the spec's explicit `# + hex code (sRGB)` requirement and the linter's silent dropping of OKLCH, Path A requires the export step for **any** meaningful interaction with the official ecosystem (linting, Stitch, exports to Tailwind/DTCG).

### Path B: Align Natively with Stitch

- Convert StratOS template to hex/rem and adopt M3 tokens
- Accept the full Material 3 surface token hierarchy

**Pros:** Zero friction with Stitch and official tooling. No conversion scripts to maintain.  
**Cons:** Abandons OKLCH perceptual uniformity; bloats the token set from 4 to 50+; creates a dependency on M3's token naming.  
**Effort:** Low (template change only).

### Path C: Maintain OKLCH Native, Accept "Ghost" Linting

- Keep current OKLCH/px format
- Acknowledge that the official linter will run "blind" (silently dropping colors from the AST, meaning no contrast ratio safety checks)
- Accept that Stitch ingestion requires manual copy-paste-and-edit

**Pros:** Zero implementation effort.  
**Cons:** Fragile; prone to the dual-frontmatter problem observed in the mockup; no automated guardrails; defeats the purpose of running the linter.  
**Effort:** None (status quo).

---

## 8. Actionable Items

### 8.1 Immediate (This Branch)

- [ ] **Fix DESIGN_RULES.md line 44:** Amend the round-trip claim to be accurate (see §5)
- [ ] **Remove dead code in `build.py` line 87:** The `version = None if srcfile.name == "DESIGN.md"` line is confirmed dead code

### 8.2 Short-Term (Next Sprint)

- [ ] **Decide resolution path** (A, B, or C) — requires your input
- [ ] **If Path A:** Implement `scripts/design-token-snap.py` for OKLCH→hex export and hex→OKLCH import
- [ ] **Add recommended token names:** Spec suggests `surface`, `on-surface`, `error` as recommended color names — consider adding these to the template
- [ ] **Verify `orphaned-tokens` rule:** StratOS defines `secondary`, `tertiary`, `neutral` but may not reference all in `components` — will trigger warnings

### 8.3 Long-Term

- [ ] **Monitor spec evolution:** The `google-labs-code/design.md` repo is actively developed. Watch for OKLCH support and any schema changes
- [ ] **Consider `npx @google/design.md export`:** The CLI can export to Tailwind theme config or W3C DTCG `tokens.json` — this could replace custom conversion scripts
- [ ] **Evaluate `designmd` alias:** On Windows, the `.md` suffix in the package name can cause command resolution issues. Use `designmd` alias in `package.json` scripts
- [ ] **Consider adding `fontFeature` / `fontVariation`:** The spec supports these typography properties — useful for variable fonts

---

## 9. Open Questions for You

> [!IMPORTANT]
> 1. **Path preference?** My recommendation is Path A (dual-schema with automated Token Snap). The spec's explicit `# + hex code (sRGB)` requirement makes this more than a preference — it's needed for any official tooling interop. But Path B (align natively with hex) is also viable if you're willing to trade OKLCH perceptual uniformity for zero-friction compliance.
>
> 2. **Orphaned tokens strategy:** The `orphaned-tokens` linting rule will warn about any color not referenced in `components`. Should StratOS add more component definitions to cover `secondary`, `tertiary`, `neutral`, or accept the warnings?

---

## Appendix A: StratOS Template Tokens vs Stitch Output Tokens (Full Comparison)

### Colors

<details>
<summary>Click to expand full color token comparison</summary>

| StratOS Token | StratOS Value | Stitch Token | Stitch Value |
|---|---|---|---|
| `primary` | `oklch(0.68 0.15 240)` | `primary` | `#005da7` |
| `secondary` | `oklch(0.85 0.08 240)` | `secondary` | `#486175` |
| `tertiary` | `oklch(0.75 0.18 65)` | `tertiary` | `#7f5300` |
| `neutral` | `oklch(0.98 0.01 240)` | _(no direct equivalent)_ | — |
| — | — | `surface` | `#f8f9ff` |
| — | — | `surface-dim` | `#d8dae1` |
| — | — | `surface-bright` | `#f8f9ff` |
| — | — | `surface-container-lowest` | `#ffffff` |
| — | — | `surface-container-low` | `#f2f3fb` |
| — | — | `surface-container` | `#ecedf5` |
| — | — | `surface-container-high` | `#e6e8ef` |
| — | — | `surface-container-highest` | `#e1e2e9` |
| — | — | `on-surface` | `#191c21` |
| — | — | `on-surface-variant` | `#414751` |
| — | — | `inverse-surface` | `#2e3036` |
| — | — | `inverse-on-surface` | `#eff0f8` |
| — | — | `outline` | `#717783` |
| — | — | `outline-variant` | `#c1c7d3` |
| — | — | `surface-tint` | `#0060ac` |
| — | — | `on-primary` | `#ffffff` |
| — | — | `primary-container` | `#2976c7` |
| — | — | `on-primary-container` | `#fdfcff` |
| — | — | `inverse-primary` | `#a4c9ff` |
| — | — | `on-secondary` | `#ffffff` |
| — | — | `secondary-container` | `#c9e3fa` |
| — | — | `on-secondary-container` | `#4d6579` |
| — | — | `on-tertiary` | `#ffffff` |
| — | — | `tertiary-container` | `#a06900` |
| — | — | `on-tertiary-container` | `#fffbff` |
| — | — | `error` | `#ba1a1a` |
| — | — | `on-error` | `#ffffff` |
| — | — | `error-container` | `#ffdad6` |
| — | — | `on-error-container` | `#93000a` |
| — | — | `primary-fixed` | `#d4e3ff` |
| — | — | `primary-fixed-dim` | `#a4c9ff` |
| — | — | `on-primary-fixed` | `#001c39` |
| — | — | `on-primary-fixed-variant` | `#004883` |
| — | — | `secondary-fixed` | `#cce6fd` |
| — | — | `secondary-fixed-dim` | `#b0cae0` |
| — | — | `on-secondary-fixed` | `#011e2f` |
| — | — | `on-secondary-fixed-variant` | `#31495c` |
| — | — | `tertiary-fixed` | `#ffddb4` |
| — | — | `tertiary-fixed-dim` | `#ffb953` |
| — | — | `on-tertiary-fixed` | `#291800` |
| — | — | `on-tertiary-fixed-variant` | `#633f00` |
| — | — | `background` | `#f8f9ff` |
| — | — | `on-background` | `#191c21` |
| — | — | `surface-variant` | `#e1e2e9` |
| — | — | `sun-alert` | `#E5A040` |
| — | — | `background-neutral` | `#F7F9FB` |

</details>

### Spacing

| StratOS Token | StratOS Value | Stitch Token | Stitch Value |
|---|---|---|---|
| `xs` | `4px` | `xs` | `4px` |
| `sm` | `8px` | `sm` | `8px` |
| `md` | `16px` | `md` | `16px` |
| `lg` | `32px` | `lg` | `24px` ⚠️ |
| `xl` | `64px` | `xl` | `48px` ⚠️ |
| — | — | `gutter` | `16px` |
| — | — | `margin` | `24px` |

> [!WARNING]
> Stitch changed `lg` from `32px` to `24px` and `xl` from `64px` to `48px` without being asked. These are silent value overrides, not just format changes.

### Rounded

| StratOS Token | StratOS Value | Stitch Token | Stitch Value |
|---|---|---|---|
| `sm` | `4px` | `sm` | `0.25rem` (= 4px ✅) |
| `md` | `8px` | `DEFAULT` | `0.5rem` (= 8px) |
| `lg` | `12px` | `md` | `0.75rem` (= 12px ✅) |
| — | — | `lg` | `1rem` (= 16px) |
| — | — | `xl` | `1.5rem` (= 24px) |
| `full` | `9999px` | `full` | `9999px` ✅ |

---

## Appendix B: Relevant StratOS Files Referenced

| File | Path | Role |
|---|---|---|
| Template | `src/memory-templates/DESIGN.md` | Source template (OKLCH/px) |
| Design Rules | `src/memory-templates/DESIGN_RULES.md` | Governance doc (contains Stitch rules) |
| Workflow | `src/workflows/2b_interface-design.md` | Token Snap workflow definition |
| Stitch Brief Guide | `src/references/stitch-brief-guide.md` | Stitch integration instructions |
| Build Script | `build/build.py` (line 87) | Dead code flagged for removal |
| 1st Conflict Review | `docs/research/DESIGN_md/stitch-design-schema-conflict.md` | Prior analysis |
| Mockup Evidence | `docs/research/DESIGN_md/DESIGN mockup copied back from Stitch.md` | Proof of schema expansion |
| **Official Stitch Docs** | `docs/research/DESIGN_md/Stitch-Docs.md` | **Official spec, CLI, and linting rules (copied from Stitch)** |
