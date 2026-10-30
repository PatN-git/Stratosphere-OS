---
description: The label vocabulary and the rules around it: label list, composition, status lifecycle, milestone scheme, concept exemptions. The registry is the live GitHub label set, or locally this list plus the project's `area:*` slugs.
version: "1.0.0"
timestamp: 2026-10-22
---

# Label taxonomy

The one place for label rules. With `tracker: github` the registry is the live label set (`gh label list`); with `tracker: local` it is this list plus the project's `area:*` slugs in `docs/issues/README.md` on the tracker branch (added with `issues.py label`, the local `ensure_label`); local never reads GitHub labels. Never invent a label; ask the user first.

## Labels
- **Area (`area:xxx`)**: project-defined slugs (`area:BE-api`, `area:FE-<page_name>`, ...). Setup and 2a/3b read the registry.
- **Primary Type (`type:<class>`)**: `type:bug`, `type:content`, `type:feature`, `type:improvement`, `type:maintenance`, `type:research`
- **Execution Mode (`mode:<mode>`)**: `mode:HITL` (Human-in-Loop required), `mode:AFK` (Autonomous execution)
- **Tier (`tier:<tier>`)**: `tier:epic` (PRD parent / epic), `tier:slice` (Leaf vertical slice)
- **Priority (`priority:xxx`)**: `priority:high` (Must have), `priority:medium` (Important), `priority:low` (Nice to have)
- **Size (`size:xxx`)**: `size:large` (Biggest effort vertical slice), `size:medium` (Medium effort vertical slice), `size:small` (Surgical effort / local fix)
- **Scope (`scope:xxx`)**: `scope:baseline` (MVP end-to-end), `scope:differentiator` (differentiator to win), `scope:deferred` (out of scope/temporal deferral)
- **Status (`status:xxx`)**: `status:needs_spec`, `status:planned`, `status:in progress`, `status:in review`, `status:blocked`, `status:done` (lifecycle order: `needs_spec → planned → in progress → in review → done`; Spikes: `needs_spec → done`; `blocked` from any point; child slices go `in progress → done`, closed at ship; `in review` = standalone issue or epic with its PR open)
- **Concept Discovery (`concept:xxx`)**: `concept:map`, `concept:research`, `concept:grilling`, `concept:prototype`, `concept:task`
- **Risk (`risk:xxx`)**: `risk:one-way` (PR contains a hard-to-reverse change per `merge-risk-paths.md`; a human must read it before merge)

## Rules
- **Label Composition Rules**: each leaf issue carries exactly one `type:` + one `mode:` + `tier:slice` + one `size:`. Each epic carries `tier:epic` + one `type:` (no `mode:`, no `size:`).
- **Single Status Invariant**: an issue has exactly one `status:*` label. A transition removes the prior `status:*` label first (the `set_status` verb owns this, `references/tracker-verbs.md`). Locally the status is the issue's bare `status:` field, never a label. The `status:*` names are an integration contract with the Projects board Action: see `docs/status-label-contract.md` before renaming one.
- **Milestone**: `vX.Y.Z` (`vMAJOR.MINOR.SPRINT`, e.g. `v1.2.3` = release 1.2, sprint 3). `MAJOR.MINOR` = the product release, owned by `/3a-version-planning`; `SPRINT` (Z) is owned by `/3c-sprint-planning`. `vX.Y.0` = release planned, not yet sprinted. No leading zeros. It is the project's product-release tracker, not a tool/library version. An epic has no milestone until 3a assigns one.
- **Concept Exemptions**: an issue carrying a `concept:*` label is exempt from `/3c-sprint-planning`, `[NEEDS_SPEC]` alerts and the Single Status Invariant.
- **`concept:map` issue**: the `concept:map` issue carries `concept:map` + `status:*` (`status:in progress` while active, `status:done` on convergence) and is milestone-exempt. Child decision tickets (`concept:research`, `concept:grilling`, ...) are sub-issues of their tracking issue (`parent` = the map issue).
- **Closed ≡ done**: a closed issue is `status:done`.

With `tracker: github` there is no registry copy: a missing label is created with `ensure_label` after user confirmation, then used.
