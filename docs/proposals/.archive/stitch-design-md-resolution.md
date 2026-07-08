type: proposal

title: "DESIGN.md resolution — tool-agnostic OKLCH SSOT with gated, setup-selected design-source seams"

status: proposed

date: 2026-06-25

revised: 2026-06-25

decision\_owner: Patrick

related:

*   docs/research/DESIGN\_md/2nd-review stitch-design-conflict.md
*   docs/research/DESIGN\_md/stitch-design-schema-conflict.md
*   docs/research/DESIGN\_md/Stitch-Docs.md
*   docs/research/DESIGN\_md/DESIGN mockup.md
*   docs/research/DESIGN\_md/DESIGN mockup copied back from Stitch.md  
    supersedes\_recommendation\_in: "2nd-review §7 Path A (refined below)"

## Proposal: DESIGN.md resolution

&gt; **TL;DR** — Keep `.memory/DESIGN.md` **OKLCH-native** as the single source of truth. `DESIGN.md` is a  
&gt; **tool-agnostic SSOT** (StratOS itself is host-agnostic — Claude Code _and_ Antigravity); the design source  
&gt; (**Stitch / Claude Design / native GenAI**) is a **setup-time choice** — one source, never synced duplicates.  
&gt; **The verification gate is RESOLVED (§3): Stitch ingests OKLCH and the** `**@google/design.md**` **linter coerces it**  
**&gt; and runs contrast — so** `**design-export**` **(OKLCH→hex) is CUT.** Build **one** deterministic script now  
&gt; (`design-theme`: OKLCH → Tailwind v4 / shadcn); lint runs directly on the OKLCH source; `design-import` is an  
&gt; optional one-shot snap. Constrain typography to the **Google Fonts catalog** (no silent Inter fallback). Wire  
&gt; it into the setup + `2b` workflows so it is **agent-driven, never hand-run**.

This proposal updates the recommendation in the 2nd review (`docs/research/DESIGN_md/2nd-review stitch-design-conflict.md`, §7 "Path A"). It was pressure-tested by a neutral adversarial review and its two load-bearing assumptions were then **empirically verified** (§3).

## 1\. Locked decisions

| # | Decision | Choice | Rationale |
| --- | --- | --- | --- |
| D1 | **Color home format** | **OKLCH-native** in `DESIGN.md` | Preserves DR-002 + perceptual uniformity; matches Tailwind v4 / shadcn defaults. Verified: both Stitch and the official linter accept OKLCH, so **no hex conversion is needed** anywhere (§3). |
| D2 | **Install model for source toolchains** | **Gated eager install at setup** — keyed to the chosen source / project type | `stitch` (and any UI project wanting spec-lint) → `@google/design.md` (lint/diff/dtcg, runs on OKLCH directly); Node/UI → `design-theme` runtime; `native`/non-Node/offline → skip + record. Honors "in the install workflow, never manual" without taxing projects that won't use it. |
| D3 | `**DESIGN.md**` **token vocabulary** | **Portable** — 4 semantic tokens + spec-recommended `surface`, `on-surface`, `error`; map to shadcn names at **build time** in `design-theme` | Keeps the SSOT renderer-agnostic and interop-friendly (DTCG / Figma / Stitch / Claude Design). |
| D4 | **Script scope** | `**design-theme**` **now**; `**design-export**` **CUT** (gate resolved); `**design-import**` = optional one-shot, propose-only snap | `design-theme` is the only source-independent, daily-driver gap. Export is unnecessary (§3). Import is a convenience for pulling a generator's hex back, not a requirement. |
| D5 | **Typography source** | **Google Fonts catalog** for generator-assisted projects; non-GF brand fonts kept in the SSOT with a GF **stand-in for mockups only** | Generators treat `fontFamily` as a hard constraint and render any Google Font (no Inter fallback); the app self-hosts via `next/font/google` / `@fontsource`. Verified by the `SF Pro → Inter` swap in the round-trip (§3). |
| D6 | `**DESIGN.md**` **is a tool-agnostic SSOT** | One OKLCH source for **all** consumers; design source chosen at setup — `stitch` | `claude-design` |
| D7 | **Dark mode = hybrid** | `DESIGN.md` stays single-palette (standard); `design-theme` **derives** a role-aware, contrast-checked `.dark` from the light OKLCH, **overridable** per-token via an optional `colorsDark:` group | The ecosystem treats dark as a _downstream_ concern (shadcn `:root`+`.dark`); the open spec is single-palette; `colorsDark` is a **linter-safe additive extension** (verified — 0 errors, `colors` still validated). Keeps the SSOT standard by default; `design-theme` validates dark contrast since the linter ignores `colorsDark`. See §4.10. |

**What this changes vs. the 2nd review's Path A:** Path A proposed two perpetually-maintained conversion scripts up front, scoped to Stitch only. After verification we (a) build only `design-theme`, (b) **cut** `**design-export**`, (c) gate install conditionally, and (d) generalize the SSOT to be tool-agnostic with a setup-time, vendor-neutral source choice.

## 2\. Why (condensed analysis)

The conflict is **not** structural. StratOS and the Google spec share the two-layer shape (YAML frontmatter +  
canonical `##` sections). The differences that mattered:

1.  **Color encoding** — StratOS `oklch(...)` vs Google spec `# + hex (sRGB)`. _Resolved:_ both Stitch and the  
    linter accept OKLCH (§3), so this is no longer a blocker — OKLCH stays the home format.
2.  **Token granularity** — StratOS ~4 semantic tokens vs Stitch's ~50 Material-3 tokens (a _different_  
    _vocabulary_ for M3 components StratOS doesn't use — it ships **shadcn**). Handled by Token-Snap + curation.
3.  **Value drift** — the round-trip shows Stitch re-derives: `lg 32px→24px`, `xl 64px→48px`, primary color  
    shifted, and `SF Pro Display → Inter` (because SF Pro isn't a Google Font — validates D5). Handled by  
    propose-only import + freeze + the Google Fonts policy.

`DESIGN.md` is **no longer Stitch-specific**: **Claude Design also ingests it** and preserves OKLCH faithfully (verified — §4.9/§9),  
and the project's coding agent — **Claude Code** _**or**_ **Antigravity** — reads `DESIGN.md` as context. Since StratOS  
is host-agnostic and ships to both, the SSOT must be vendor-neutral and the freeze/snap discipline must cover  
_any_ external generator. The existing governance already has the right instincts: a generator is a **mood**  
**board** (DR-007/DR-010), **ingested once and frozen** (DR-015), normalized via **Token Snap** (DR-009).

## 3\. Verification gate — RESOLVED ✅

**Status: COMPLETE (2026-06-25) — nothing in this section remains to be done; it records results, not tasks.**  
The two assumptions the prior analysis treated as facts were tested (user run in Antigravity + independent  
subagent run of `@google/design.md` v0.3.0). Both load-bearing claims are now settled.

### Assumption B — "the linter silently drops OKLCH": **REFUTED**

*   The linter **parses and coerces** `oklch(...)` to `{hex, r, g, b, luminance}` (explicit `case "oklch" → oklchToRgb`), and the `**contrast-ratio**` **rule runs** on it (fired `2.69:1` on `button-primary`).
*   The "ghosting" myth was a **conflation**: a leading `<!-- stratosphere: … -->` comment _before_ the `---`  
    makes the linter report _"No YAML content found"_ → **empty design system → 0 errors (silent false-pass)**.  
    → **A** `**DESIGN.md**` **MUST start with** `**---**`**.**
*   **Windows invocation (corrected):** `npx @google/design.md lint` silently no-ops; `@google/designmd` is a  
    **404**. Use `npx --yes -p "@google/design.md" designmd lint "<file>"` (bin alias) or the programmatic `lint()`.
*   The parsed JSON keeps **only coerced hex** (no raw `oklch` string) → `design-theme` must read the **raw YAML**.

### Assumption A — "does Stitch honor OKLCH on input": **answered by the existing round-trip**

`docs/research/DESIGN_md/DESIGN mockup.md` (OKLCH input) → `…copied back from Stitch.md` (hex M3 output).  
Stitch **ingests OKLCH without error** but **re-derives** an M3 palette (primary `oklch(0.68 0.15 240)` →  
`#005da7`, ≠ the faithful sRGB `#1aa2eb`; font `SF Pro → Inter`; spacing shifted). So feeding OKLCH works;  
fidelity is not guaranteed — Token-Snap + freeze + curation handle the re-derivation.

### Outcome

`**design-export**` **(OKLCH→hex) is CUT** — neither feeding nor linting needs it. Lint runs **directly on the**  
**OKLCH source**. Contrast is covered by the linter's own rule (it coerces OKLCH faithfully for in-gamut colors);  
a separate OKLCH contrast check is only an optional fallback for out-of-gamut values.

## 4\. Build plan

### 4.1 `design-theme` — the only must-build (D4)

The daily driver: OKLCH SSOT → what the app consumes. Fills a real gap (the official `export --format tailwind`  
emits hex, wrong for Tailwind v4).

*   **Input:** `.memory/DESIGN.md` — **read the raw YAML frontmatter directly** (the linter's JSON discards the  
    `oklch(...)` strings; §3).
*   **Output:** a Tailwind v4 `@theme` block / shadcn `globals.css` CSS-variable set (OKLCH preserved).
*   **Responsibilities:**
    *   Map StratOS semantic tokens → shadcn variable names (`--primary`, `--background`, `--muted`, `--accent`,  
        `--destructive`, `--border`, `--ring`, …). **D3's portability lives here** — SSOT stays semantic.
    *   Derive `-foreground` pairs + tints/shades (OKLCH lightness steps), not 25 hand-authored tokens.
    *   Emit spacing/radius as **fluid clamps** per DR-003 (§4.5), not raw px.
    *   Emit Google-Fonts wiring (`next/font` / `@fontsource`) for the families named in the SSOT (§4.6).
    *   Contrast is validated by the official linter on the OKLCH source; `design-theme` may add an out-of-gamut  
        fallback check, but it is not the primary guard.
*   **Runtime (DECIDED): pure Python, no third-party deps.** Authored in `src/scripts/design/` (the product);  
    `scaffold.py` deploys it to each project's `.agents/scripts/`. Python is the guaranteed runtime (setup runs  
    `python scaffold.py`), so it works for **all** UI projects incl. `native` (no Node). **No color conversion**  
    **needed** — OKLCH passes through verbatim into the Tailwind v4 / shadcn CSS vars (both accept `oklch()`); the  
    only math is `-foreground` derivation (OKLCH lightness flip) + `clamp()` arithmetic.
*   **Determinism:** values must trace to tokens (DR-005); a script beats LLM-typed CSS.

### 4.2 Gated eager install of the lint toolchain (D2)

*   **Home (source → target):** the lint toolchain template is authored in `src/scripts/design/` (the product)  
    and `scaffold.py` deploys it to each project's `.agents/scripts/design/` — an **isolated** Node package with  
    its own `package.json` (separate from the app's, which StratOS doesn't manage). Pin `**@google/design.md@0.3.0**`.  
    Record the targeted spec version (`alpha`).
*   **Justification narrowed:** the linter is for **lint / diff / dtcg-export**, not hex conversion. Because it  
    now validates the **OKLCH source directly** (structural rules + contrast), it's useful for **any UI project**,  
    most of all `stitch`.
*   **Gate:** `stitch` or UI/Node project wanting spec-lint → install; `native` / non-Node / offline → skip + record.
*   **Windows:** wire the working invocation `npx -p "@google/design.md" designmd lint` (NOT the bare `.md` form,  
    NOT `@google/designmd`) into the npm script. See \[\[design-md-linter-gotchas\]\].
*   **Spec drift:** on `scaffold.py --update`, re-validate against the pinned version; upstream changes are  
    NEEDS-REVIEW, never silent upgrades.

### 4.3 `design-import` — optional, one-shot snap (D4; `design-export` cut)

`design-export` is **cut** (§3). `design-import` is **optional**: a convenience for pulling a generator's hex  
output back into OKLCH. If built, it is a **one-shot, propose-only snap** inside the `2b` HITL flow — **no diff**  
**engine, no selective re-import** (that would contradict DR-015 freeze / DR-009). Mandatory guards:

*   **Frontmatter sanity** — reject files with a **leading comment before** `**---**` or **two** `**---**` **blocks** (the  
    mockup exhibits both; the leading comment also silently breaks the linter, §3).
*   **Substitution guard (DR-001/DR-016)** — flag when the returned `fontFamily` ≠ declared (Inter = common  
    symptom; rare under the Google Fonts policy, §4.6).
*   **Propose-only** — never auto-commit generator values; surface silent overrides for human accept/revert.

### 4.4 Curation stays human (labor split)

*   **Script:** mechanical conversion (hex↔OKLCH if importing, rem→px), structural emit.
*   **Human/agent (HITL):** which generator tokens collapse into the StratOS set, which domain tokens to keep  
    (`sun-alert`), accept/revert silent changes. An auto-mapper would launder the drift DR-001/DR-010 prevent.

### 4.5 px-anchor → fluid-clamp (resolve the DR-003 fiction)

Make it explicit: **px in** `**DESIGN.md**` **is the desktop anchor;** `**design-theme**` **emits** `**clamp(min, fluid, max)**`  
where `max` = the px anchor, `min ≈ round(anchor × 0.66)` (with a floor), `fluid` interpolates between reference  
viewports (e.g. 360px→1280px). Document the formula in DR-003 so px values are enforceable. (Exact ratios → §7.)

### 4.6 Typography source policy — Google Fonts (D5)

Generators treat `fontFamily` as a **hard constraint** and render the full **Google Fonts catalog (~1,800**  
**families)**. The mockup's `SF Pro Display → Inter` swap (§3) happened because SF Pro is not a Google Font.

*   **Policy:** author every `DESIGN.md` `fontFamily` from **Google Fonts**; self-host in the app via  
    `next/font/google` / `@fontsource/*` (optimized, no layout shift, no CDN/GDPR concern).
*   **Why this seam:** Google Fonts is the intersection where generators _and_ the Tailwind/shadcn/Next stack both  
    have first-class support — prevention beats the import guard.
*   **Escape hatch:** non-GF brand fonts stay in the SSOT; declare a GF **stand-in for mockups only**; apply the  
    real font at implementation in `design-theme`/`globals.css`.
*   **Restraint:** pair wide choice with _one display/serif + one neutral/sans_ (DR-001). **Bonus:** variable  
    fonts map to the spec's `fontVariation` / `fontFeature`.

_Corroboration: Stitch typography as hard constraints (_[_MindStudio_](https://www.mindstudio.ai/blog/what-is-google-stitch-design-md-file)_); catalog =_ [_Google Fonts_](https://fonts.google.com/)_._

### 4.7 Generator operating practices (craft, web-research corroborated)

Craft, not `[LAW]` — lands in `stitch-brief-guide.md` and `2b`.

*   **Mode / model by phase.** **Since Google I/O 2026, Stitch runs on Gemini 3** (3.5 on roadmap). Tiering  
    persists: fast/standard (text-only, Figma export) vs Pro/Thinking (higher fidelity), plus image-input (sketches/  
    screenshots, **no Figma export**). Use Pro/Thinking for the final direction; image-input only when feeding an  
    image. StratOS ingests via MCP/code (DR-015), so the Figma-export trade-off doesn't bite.
*   **Generate broad, edit surgical.** Bulk-generate the chosen direction's screens in one prompt, then refine with  
    **Direct Edits, one change at a time, in context** (click into the component) — more reliable, saves credits.
*   **Prompt hygiene.** Concise/numbered, UI/UX keywords, precise element references; never bundle features or mix  
    layout + component changes; keep under ~5,000 chars; don't assume the generator remembers prior designs.
*   **Web needs more than mobile.** Web layouts need richer prompts + a Direct-Edit pass ("zoom-out, zoom-in").
*   **Output is a translation base, not copy-source.** Static HTML + Tailwind, mock data — re-express in shadcn,  
    never paste markup (corroborates DR-007 + `shadcn-build-guide.md`).
*   **Treat generators as disposable.** Stitch and Claude Design are both Labs products (no SLA, may sunset) — why  
    DR-015 freezes output and forbids a live runtime dependency.

_Sources:_ [_Stitch prompt guide_](https://discuss.ai.google.dev/t/stitch-prompt-guide/83844)_;_ [_modes/limits_](https://uxpilot.ai/blogs/google-stitch-ai)_;_ [_edit-in-context/web/static_](https://medium.com/@0xmega/google-stitch-tutorial-2026-the-tool-that-made-figmas-stock-drop-10-in-a-day-7a051b77a591)_;_ [_Stitch on Gemini 3 — I/O 2026_](https://www.macrumors.com/2026/05/19/google-io-2026-roundup/)_;_ [_Labs/no-SLA_](https://moda.app/blog/google-stitch-review)_._

### 4.8 Ingest paths & where the operating practices apply

**Normal flow: design manually in the generator, then** _**pull**_ **the result** — no copy/paste.

*   **Stitch MCP pull (DR-015 ingest accelerator).** `davideast/stitch-mcp` is **pull-only**: `build_site`,  
    `get_screen_code`, `get_screen_image` (OAuth / `STITCH_API_KEY`). Upstream Stitch MCP also has generate tools;  
    not needed for the manual flow.
*   **Antigravity native export (I/O 2026)** — Stitch → Antigravity directly (cf. Google Codelab "Design-to-Code  
    with Antigravity and Stitch MCP").
*   **Claude Design → Claude Code handoff** (`claude-design` source) — native two-way sync, **frozen** per DR-015.
*   **Copy/paste /** `**.zip**` — always-available fallback.

The §4.7 practices apply to **the manual design session** (you prompt/edit) and to **what gets pulled** (freeze,  
guards) — the pull mechanism changes only retrieval, not the craft. In the manual flow the agent's job narrows to  
_ensure the Design System is set → pull → Token-Snap (§4.4) → freeze (DR-015)_.

_Sources:_ [_stitch-mcp (pull-only)_](https://github.com/davideast/stitch-mcp)_;_ [_Antigravity + Stitch MCP Codelab_](https://codelabs.developers.google.com/design-to-code-with-antigravity-stitch)_._

### 4.9 Design source is a setup-time choice (tool-agnostic SSOT) (D6)

`DESIGN.md` is a cross-tool standard. **Claude Design** (Anthropic Labs, Apr 2026; update Jun 2026) centers on the  
same `DESIGN.md` concept; the project's agent (Claude Code _or_ Antigravity) reads it as context. **StratOS targets**  
**both hosts, so the SSOT and the source choice are vendor-neutral** — no generator is the default. The source is a  
**setup-time choice** (generalizing today's "Stitch Status = yes/no"):

| Design source (set at setup) | What it means | Seam handling |
| --- | --- | --- |
| `stitch` | Google Stitch (external generator) | Ingests OKLCH (re-derives M3); pull via MCP/Antigravity export; Token-Snap + freeze. Optional lint via `@google/design.md`. |
| `claude-design` | Anthropic Claude Design (external generator) | **Verified OKLCH-native** — ingests your `DESIGN.md`, preserves tokens (§9). Feed via `**/design-sync**` **first**, then handoff/implement → targets **your shadcn** _only if synced first_ (never cold-implement → DR-004). Emits **no** `DESIGN.md` (one-way). Freeze; **never persist** `**/design-sync**` (DR-015). No Google toolchain needed. |
| `native` | GenAI-only (no external tool) | Path B reference-driven native composition (already in `2b`). No external toolchain. |

**One source, many consumers — never synced duplicates.** Stitch, Claude Design, the native agent, and the app are  
adapters off the single OKLCH SSOT. `design-theme` emits the app theme regardless of source; only the _ingest seam_  
differs. Maintaining two hand-synced `DESIGN.md` files is the dual-frontmatter anti-pattern the mockup exhibited.

**Claude Design output note (verified):** it does **not** emit a `DESIGN.md` or `tokens.json` — it emits OKLCH  
`tokens/*.css` + bespoke React primitives + a UI kit + a Claude Agent-Skill (ZIP), or implemented code (MCP).  
Reconciled by Token-Snap + curation (§4.4), re-expressed in shadcn — not adopted wholesale, never a second SSOT.

_Sources:_ [_Claude Design — Anthropic Labs_](https://www.anthropic.com/news/claude-design-anthropic-labs)_;_ [_DESIGN.md sections_](https://github.com/VoltAgent/awesome-claude-design)_;_ [_frontend-design plugin_](https://claude.com/plugins/frontend-design)_._

### 4.10 Dark mode — hybrid derive + `colorsDark` override (D7)

The ecosystem handles dark **downstream**: shadcn/Tailwind v4 ship `:root` + `.dark` in `globals.css`; the open  
`design.md` spec is **single-palette** (no dark field); DTCG uses separate token _sets_. So StratOS keeps  
`DESIGN.md` single-palette (standard, portable) and makes dark a **generation** concern:

*   `design-theme` emits a `.dark` block, deriving each token from the light OKLCH **by role** (backgrounds → low  
    L, text → high L, accents → lighten + slightly desaturate), contrast-checked. (Algorithm + tests: impl-plan §2.5b.)
*   An **optional additive** `**colorsDark:**` group overrides any token verbatim (hand-tuning). Verified  
    **linter-safe**: `@google/design.md` v0.3.0 parses a file with `colorsDark` at **0 errors** and still validates  
    `colors` — it simply ignores `colorsDark`. **So** `**design-theme**` **must validate dark contrast itself.**
*   Generators don't hand over a clean dark palette (Claude Design is single-palette; Stitch's dark export is  
    unconfirmed), so `colorsDark` is **user-authored or derived**, not Token-Snapped.

_Sources:_ [_shadcn theming_](https://ui.shadcn.com/docs/theming)_;_ [_shadcn Tailwind v4_](https://ui.shadcn.com/docs/tailwind-v4)_;_ [_design.md spec_](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md)_;_ [_DTCG Resolver (draft)_](https://www.designtokens.org/tr/drafts/resolver/)_._

## 5\. Workflow & file edits (the "agent-driven, not manual" requirement)

| File | Change |
| --- | --- |
| `src/commands/instantiate/Instantiate-StratosphereOS.md` | Generalize **Checkpoint 8** "Stitch yes/no" → **Design Source** (`stitch` |
| `src/workflows/2b_interface-design.md` | Generalize Path A "Stitch-assisted" → "**generator-assisted** (Stitch or Claude Design)". Agent **invokes** `design-theme` (and `design-import` if built). Import is **propose-only** with the frontmatter-sanity + font-substitution guards (§4.3). Reword Token Snap to the §4.4 split. Brief **names the exact Google Fonts family** (DR-011/DR-016). Apply §4.7 practices. |
| `src/memory-templates/DESIGN_RULES.md` | **See §5.1** — DR-001/002/003/009/010/015/011, new DR-016, §2 **Design Source** field, line-44 fix. |
| `src/memory-templates/DESIGN.md` | Keep OKLCH; add `surface`/`on-surface`/`error` (D3); author `fontFamily` from **Google Fonts** (D5). Ensure the file **starts with** `**---**` (no leading comment) so the linter parses it (§3). Comment that shadcn names are generated by `design-theme`. |
| `src/references/stitch-brief-guide.md` | Provisioned toolchain; feed DESIGN.md as the Design System (no inlined tokens); **name the exact Google Fonts family** (DR-016); fold in §4.7 practices. |
| `src/scripts/scaffold.py` | Ship `design-theme` into `.agents/scripts/` + the `.agents/scripts/design/package.json`; add to the managed manifest so `--update` tracks them. |
| `build/build.py` | **Remove dead line 87**. Verified dead: `memory-templates/` is copied via `copytree` (line 175); `copy_md_with_frontmatter` (the only caller) never runs on a file named `DESIGN.md`. Also ensure nothing prepends a comment to `DESIGN.md` (would break the linter, §3). |

### 5.1 Rule-file changes — `src/memory-templates/DESIGN_RULES.md`

The **one rule file** that changes (ships to `.memory/DESIGN_RULES.md`). All entries are `[LAW]`\-tier; per  
`memory-protocol.md` a new/amended `[LAW]` is **proposed**, applied on confirmation.

| Rule | Change | Type |
| --- | --- | --- |
| **DR-001** | Reframe the font clause: _no **unchosen** default font_ (deliberate Inter is fine; an inherited tool default is not). Keep the rest. | Amend |
| **DR-002** | Note OKLCH is the SSOT and is accepted by the official tooling end-to-end (no hex conversion needed); hex only appears if a generator emits it. | Amend |
| **DR-003** | Add the explicit **px-anchor → fluid-clamp formula** (§4.5). | Amend |
| **DR-009** | Token Snap = **script (mechanical) + human (curation)** (§4.4); generalize to **any external source (Stitch / Claude Design)**. | Amend |
| **DR-010 / DR-015** | Generalize "Stitch" → **any external generator**; DR-015 freeze explicitly covers Claude Design's two-way sync (ingest→snap→reconcile, never live). | Amend |
| **DR-011** | Name the exact **Google Fonts** family when feeding the chosen generator (ties to DR-016). | Amend |
| **DR-016** _(new)_ | **Typography source — Google Fonts catalog** (renderable hard constraint + self-hostable); non-GF brand fonts → SSOT + GF stand-in for mockups only; _one display/serif + one neutral/sans_. | Add |
| **§2 field** | Rename **Stitch Status** → **Design Source** (`stitch` | `claude-design` |
| **Line 44** | Fix round-trip wording: _"Stitch-spec"_ = conforms to the open format (not "Stitch is SSOT"); reconcile _"never hand-resync"_ with DR-009 (the **script** resyncs). | Fix |

&gt; **Other rule files unaffected:** `memory-protocol.md`, `output-mode.md`, and the constitution are untouched.

## 6\. Risks (post-verification)

| Risk | Severity | Handling |
| --- | --- | --- |
| `~design-export~` ~built on an unverified premise~ | **Resolved** | Export **cut** — Stitch ingests OKLCH; linter coerces it (§3). |
| ~"Linter drops OKLCH" unverified~ | **Resolved** | Refuted (§3): OKLCH parsed/coerced, contrast runs. |
| **Linter false-pass on a leading comment** | Med | `DESIGN.md` must start with `---`; frontmatter-sanity guard on import; build never prepends a comment (§3, §4.3, §5). |
| Node toolchain scope creep (offline / non-Node / `native`) | Med | Gated install per source (D2); skip + record when gate misses. |
| Claude Design **cold-implement** → bespoke components (DR-004) | Med | Always `**/design-sync**` **first**; never cold-implement (§4.9, §9). |
| Claude Design `/design-sync` persisted as a live dependency | Med | Keep it manual/one-time; never in CI / `mcpServers` (DR-015). |
| Claude Design output treated as the SSOT | Med | Reconcile **into** `DESIGN.md`; reject its self-SSOT framing (§9). |
| shadcn coupling in SSOT | Med | Avoided via D3 (portable names; map at build). |
| DR-003 px fiction | Med | Documented formula (§4.5). |
| Generator font substitution (Inter fallback) | Low | Prevented by the Google Fonts policy (DR-016/§4.6); residual caught by the substitution guard. |
| Unattended agent snaps silent overrides | Med | Propose-only import; human accept/revert (§4.3). |
| Alpha/preview tools drift or sunset | Med | Pin `@google/design.md@0.3.0` + `--update` re-validation; disposable-generator stance (§4.7). |

## 7\. Open implementation decisions (non-blocking)

1.  `**design-theme**` **runtime:** ✅ DECIDED — **pure Python, no deps** (OKLCH passes through; no color-space conversion needed).
2.  `**orphaned-tokens**` **policy:** reference `secondary`/`tertiary`/`neutral`/new tokens in `components`, or accept the warnings by policy.
3.  **Exact fluid-clamp ratios** (§4.5).

## 8\. Actionable checklist

**Path-independent (safe now):**

*   Remove dead `build/build.py:87`; ensure the build never prepends a comment to `DESIGN.md`.
*   `DESIGN_RULES.md` edits per §5.1 (DR-001/002/003/009/010/015/011, new DR-016, §2 Design Source, line 44). Propose `[LAW]` → confirm.
*   `src/memory-templates/DESIGN.md`: OKLCH + `surface`/`on-surface`/`error` (D3); Google-Fonts `fontFamily` (D5); **starts with** `**---**`.
*   Generalize setup **Checkpoint 8 → Design Source**; gate the toolchain install; wire the **correct lint invocation** (`npx -p "@google/design.md" designmd lint`) on the OKLCH source.
*   Add the Google-Fonts note + §4.7 practices to `stitch-brief-guide.md`; document the DR-003 clamp formula.

**Verification gate — DONE (§3):**

*   Test 2 — linter coerces OKLCH, contrast runs (user + independent subagent). `design-export` for linting not needed.
*   Test 1 — Stitch ingests OKLCH (re-derives M3) per the existing round-trip. `design-export` for feeding not needed.
*   `**design-export**` **cut.**

**Build:**

*   `design-theme` (OKLCH → Tailwind v4 / shadcn; reads raw YAML; Google-Fonts wiring), shipped via `scaffold.py`.
*   Gated lint-toolchain install wired into setup (D2) + `2b` invokes scripts agent-side.
*   `design-import` (optional) — one-shot, propose-only, with frontmatter-sanity + substitution guards.

**Claude Design evaluation (additional workstream — §9):**

*   Run §9 as far as needed; confirm specifics against an actual exported artifact before any adoption.

## 9\. Claude Design — findings & integration (verified)

Claude Design is a **first-class, vendor-neutral** design source (co-equal with `stitch`; StratOS is host-agnostic  
— neither is the default). The earlier "unconfirmed" framing is resolved: a **real product export** (the SkyCast  
zip) plus an MCP-path investigation settled the load-bearing questions.

**Verified findings:**

*   **OKLCH-native & spec-preserving.** Given an OKLCH `DESIGN.md`, the product ingests it and **preserves the exact**  
    **tokens** (labels them `(spec)`), honors the type/spacing scales, and emits OKLCH CSS tokens — _no hex seam_  
    (unlike Stitch, which re-derives to hex). It applies the **Google-Fonts + anti-Inter** substitution (D5/DR-001)  
    on its own and flags it.
*   **It consumes** `**DESIGN.md**`**; it does not emit one.** Output is a design-system package (OKLCH `tokens/*.css` +  
    bespoke React primitives + a UI kit + a Claude Agent-Skill), or — via the MCP — an implemented-code handoff.  
    So the flow is **one-way** (`DESIGN.md` → Claude Design → reconcile); there is **no second** `**DESIGN.md**` **to sync**.
*   **Two ingest paths:** (a) **ZIP** design-system export (bespoke components); (b) **MCP** "import + implement"  
    handoff that writes code — and **targets your shadcn only if you** `**/design-sync**` **your system first** (cold runs  
    produce bespoke components → a DR-004 break).

**Integration (same lifecycle as Stitch — see §4.8 + impl-plan §5.0):** `/design-sync` the StratOS system first  
(the DR-011 analog) → design with a **scoped brief** → handoff/implement → **freeze + reconcile** into the OKLCH  
`DESIGN.md` SSOT (DR-009/DR-015) → **re-express in shadcn** (DR-004 — do not adopt the bespoke bundle).

**Guards:** never **cold-implement** (always `/design-sync` first, or DR-004 breaks); never **persist** `**/design-sync**`  
in CI / `mcpServers` (or DR-015 breaks); the agent reconciles **into** `DESIGN.md`, never letting Claude Design's  
self-declared "this repo is the SSOT" output become the master.

**Status: Confirmed (per decision owner).** The sync-first handoff targets your shadcn components and preserves  
OKLCH — treated as confirmed; no seat check required. (A throwaway-branch `git diff --stat` + a  
`@/components/ui` / `oklch(` grep remains available to re-verify against a future Claude Design version.)

\*Authored 2026-06-25. Revised 2026-06-25: (a) Google Fonts policy (D5, §4.6); (b) per-rule changes (§5.1);  
(c) Gemini 3 / MCP-pull corrections (§4.7–§4.8); (d) tool-agnostic SSOT + setup-time source choice (D6, §4.9) +  
Claude Design workstream (§9); (e) **verification gate resolved —** `**design-export**` **cut, linter handles OKLCH,**  
**Windows invocation + leading-comment findings (§3)**; (f) host-agnostic correction (StratOS targets Claude Code

*   Antigravity; sources are vendor-neutral); **(g) Claude Design verified first-class via the SkyCast zip + MCP**  
    **investigation — §9 rewritten as findings,** `**claude-design**` **un-demoted, sync-first / DR-004 guards added.**
*   _(h) dark mode = hybrid derive +_ `_colorsDark_` _override (D7, §4.10).\*\* Decisions D1–D7 confirmed by the decision owner._