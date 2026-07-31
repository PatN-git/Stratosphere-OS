---
type: reference
name: concept-map-changes
description: Side-by-side comparison of 1c_concept-map and 1b_concept-framing before and after the wayfinder-parity + AFK-posture proposal.
version: "1.0.0"
timestamp: 2026-07-30
---

# What changed — `1c` and `1b`

Review aid for [`README.md`](README.md). Left column is what ships today in `src/`; right column is the proposed work copy in this folder.

Raw diffs:

```bash
git diff --no-index src/workflows/1c_concept-map.md   docs/proposals/concept-map/1c_concept-map.work.md
git diff --no-index src/workflows/1b_concept-framing.md docs/proposals/concept-map/1b_concept-framing.work.md
```

`1c`: **+85 / −42** (77 → 119 lines). `1b`: **+4 / −9** (154 → 148 lines).

---

## 1. `1c_concept-map` — structure at a glance

| | Today (v1.1.1) | Proposed (v1.3.0) |
|---|---|---|
| Header | Purpose, Hand-off contract | *+* Invocation line with `[<map>] [<ticket>] [--drain]`, *+* `gh` requirement, *+* `> [!NOTE]` routing gate |
| — | *(none)* | **`## Invariants`** — 5 rules that hold across every phase |
| Phase 0 | Resume & Route (4 steps) | Resume & Route (5 steps) — preflight replaces the mode fork |
| Phase 1 | Chart (5 steps) | Chart (5 steps) — same shape, much sharper ticket rules |
| — | *(none)* | **Phase 2A — AFK Drain (9 steps)** |
| Phase 2 | Work (7 steps) | Work (7 steps) — now explicitly the *human* frontier |
| Phase 3 | Converge (7 steps) | Converge (7 steps) — unchanged except Decision Trail + AFK boundary |
| Modes | GitHub **or** BT-LOCAL fallback, forked in every phase | **One** mode; halts without `gh` |

The two structural additions are the `Invariants` block and `Phase 2A`. Everything else is the same skeleton with tightened steps.

## 2. `1c` — change by change

### New invariants (there were none)

| Rule | Why it exists |
|---|---|
| **Plan, don't do** — a ticket resolves a decision, never a build slice; `1c` never edits code or creates a branch | Users kept reading decision tickets as implementation tickets. Also closes a route where `1c` edited code on an ungated branch. |
| **Index, not store** — a decision lives in exactly one place, its ticket | Stops the map growing into a second copy of every answer. |
| **Refer by name** — never a bare `#42` in user-facing output | `#42, #43, #44` is illegible; names read at a glance. |
| **Attention is the bound, not context** — one `mode:HITL` ticket per session; AFK drains in parallel | Wayfinder's one-per-session rule was about context economy in a human-attended session. Your constraint is human attention. |
| **AFK prepares a HITL ticket, never resolves one** | The load-bearing safety rule once anything runs unattended. Without it, an agent answering its own grilling question becomes the default path. |

### Phase 0

| | Today | Proposed |
|---|---|---|
| Tracker | Every phase forks *GitHub CLI* vs *BT-LOCAL Fallback*, and **nothing says how the fork is decided** | `gh auth status` preflight; fail → `[BLOCKED]`. No fallback, no fork. |
| Discovery | Always queries open maps | Skipped when `<map>` is passed |
| Routing | Fog-or-flat → `/1b` | Same, plus a header `[!NOTE]` that routes *before* the user picks `1c` at all |

### Phase 1 — Chart

| | Today | Proposed |
|---|---|---|
| Destination | "Define destination and scope" | Grill for it, **and** name a destination *type* (`discovery-brief` \| `locked-decision` \| `in-place-change`) that drives the Phase 3 hand-off |
| Ticket body | Body is an SOS block containing only `Blocked by:` — **the question lives nowhere** | `## Question`, sized to one agent session |
| Ticket labels | `concept:<type>` | *+* `mode:AFK` \| `mode:HITL`, set per ticket, never inferred from type |
| Fog vs ticket | No guidance | **Fog-or-ticket test:** can you state the question precisely *now* — not answer it? Sharp → ticket even if blocked. Never pre-slice fog. |
| Type choice | No guidance | Prefer `prototype` over `grilling` for "how should it look / behave" |
| Issue numbers | — | Capture what `gh issue create` returns; never predict one |
| Research | Deferred to Phase 2, one session each | Moved to Phase 2A and fired in parallel |

### Phase 2A — AFK Drain (entirely new)

| Step | What it does |
|---|---|
| 1 | Partition the frontier by mode label → drainable vs human |
| 2 | Skip anything already prepped (idempotent per frontier state, so a scheduled drain doesn't re-post) |
| 3 | **One** authorization gate — skipped on standing authorization or `--drain` |
| 4 | Drain in parallel: `research` fully; `task` fully; `prototype` **build half**; `grilling` **prep half** (facts + a recommendation labelled as a proposal) |
| 5 | Exhaustive terminal states: `resolved` \| `prepped` \| `blocked-needs-human` \| `out-of-scope` |
| 6 | Max 3 attempts, then **demote** to `mode:HITL` — never retry forever, never silently drop |
| 7 | One map write after the whole batch |
| 8 | Recompute and repeat until the frontier is human-only |
| 9 | Report per ticket |

Steps 5–6 also fix a latent bug in the HITL-only version: it had **no failure handling at all** for a research subagent returning garbage.

### Phase 2 — Work

| | Today | Proposed |
|---|---|---|
| Opening move | Straight to a frontier query — the map body, Destination and Notes are never read | Load the map low-res once, orient to Destination, invoke the skills `Notes` names, **zoom on demand** |
| Ticket pick | "The user selects (or the agent picks) one" | Deterministic precedence: passed `<ticket>` → user's pick → lowest open issue number |
| Grilling rules | G1–G3 and V1–V3 pasted inline (~9 lines, duplicated from `1b`) | One pointer to `grilling-protocol.md` |
| Prep | — | Opens with Phase 2A's prep comment, treated as a proposal to react to |
| Concurrency | Claim-locking only | *+* re-read the map body immediately before writing; *+* release the claim on an unresolved halt |
| Fog graduation | "graduate sharp fog" | *+* **clear the graduated patch** from `Not yet specified`; *+* handle resolutions that invalidate other tickets |
| Out of scope | "mark mis-scoped tickets as out-of-scope" — no procedure | Close the ticket, one line in `Out of scope` with why, and keep it **out of** `Decisions so far` |
| Batching | "cheap frontier tickets may be batched if they fit the context limit" | Removed — one HITL ticket, full stop |
| Halt | Stop | *+* emit a paste-ready next-session invocation; *+* offer `/0c_handoff` |
| Credentials | "credentials location" recorded in the resolution | The credential's **env-var name** only — never its value or file path |

### Phase 3 — Converge

Deliberately the least-changed phase: the RAT guardrail is byte-identical, and the hard HITL gate and glossary-confirmation rule are preserved verbatim (both landed via the earlier `F2`/`F3` fixes).

| | Today | Proposed |
|---|---|---|
| Brief | Compile resolutions | *+* populate `## Decision Trail` — map link plus every resolved ticket, so a reader can reach the primary source |
| RAT dispatch | "Invoke a subagent" + guardrail | *+* dual-host phrasing, explicit Input and Output — brought to the repo standard |
| Gate | 7-item checklist | *+* Decision Trail check; *+* an explicit AFK boundary: a drain may draft the brief and run the RAT, never pass the gate |
| Archive | Close map, Status `done` | *+* abandon ramp (close with reason, Status `done`, `abandoned:` note) |
| Hand-off | `/2a` or exit ramps | Routed by destination type |

## 3. `1b_concept-framing` — one change only

Nothing about `1b`'s behaviour changes. G1–G3 and V1–V3 were **byte-identical duplicates** shared with `1c`; they move to a shared reference and both workflows point at it.

| | Today (v1.1.0) | Proposed (v1.2.0) |
|---|---|---|
| Phase 2 grilling rules | G1, G2, G3 stated in full (3 long bullets) | `**G1–G3 grilling guidelines: apply per .agents/workflows/.reference/grilling-protocol.md.**` |
| Phase 2 Vocabulary focus area | V1, V2, V3 stated as 3 sub-bullets | One line pointing at the same reference |
| Everything else | — | Untouched |

Two things worth noting on the extraction:

- `1c`'s copy of **G3 was weaker** than `1b`'s ("Resolve dependency chains sequentially" vs the full dependency-tree walk). The shared reference takes `1b`'s superset, so `1c` gains behaviour rather than `1b` losing it.
- V3's pointer was **strengthened** from `GLOSSARY.md` to `.memory/GLOSSARY.md`.

## 4. Supporting files

| File | Change |
|---|---|
| `concept-map-operations.md` | Preflight section; ticket body + mode label in §2; claim release in §3; §4a mode partition; §6 now covers fog patches as well as tickets; new §7 graduate-fog. All BT-LOCAL branches removed (190 → 133 lines). |
| `concept-map-template.md` | *+* destination type, *+* `AFK drain` field (user-set only); fog-or-ticket test and out-of-scope rules inline; `Decisions so far` moved above the fog sections; `Tracker mode` and the BT-LOCAL exception removed |
| `discovery_brief_template.md` | *+* `## Decision Trail` section |
| `grilling-protocol.md` | **New** — G1–G3 + V1–V3, single source of truth |
| `AGENTS.md` | **Constitution:** §1 sanctions a bounded AFK surface behind five conditions; §6 adds artifact-scoped standing authorization, user-set only |

## 5. Not yet done

- `2a_write-prd.md:43` still calls the brief "the source of truth", so the Decision Trail is written but never read — plan item #4 is half-landed.
- The map template's OKF frontmatter still leaks into the issue body via `--body-file`.
- `build/validate.py` has never seen these files; plugin `VERSION` unbumped; `1c` not registered in `tests/test_subagent_spawning.py`.
- Phase 2A and the constitution amendment have had **no independent review**.
