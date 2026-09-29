---
type: reference
title: Status Label Integration Contract
description: The status:* label vocabulary is an integration contract with the GitHub Projects board sync Action; renaming a label breaks the board.
generated:
  by: Patrick Nennewitz
  at: 2026-09-29
version: "1.0.0"
---

# Status Label Integration Contract

The `status:*` issue labels are **not** an internal convention. `.github/workflows/sync-labels-to-project.yml` reads them and moves the issue on the GitHub Projects board (`PatN-git` project #2). Renaming, adding or removing a status label changes board behaviour, so treat every change here as a breaking change.

## Direction of truth

**Labels are the source of truth; the board is a derived view.** The sync is one-way (label → board). `reconcile.py` deliberately does *not* mirror board position — it keeps its 5 fields (status, milestone, labels, parent, blocked-by) and compares `.memory/BACKLOG_MAP.md` against GitHub labels only. Never edit a card's Status on the board by hand; the next label event overwrites it.

## Vocabulary

The lifecycle workflows (`0a`, `3d`, `4a`, `3z` and others) write these labels. Each label maps to the board `Status` option of the same name. The Action matches on name after lower-casing and treating `_`, `-` and spaces as equal, and only logs a warning if an option is missing — a rename fails silently.

| Label | Board Status option |
|---|---|
| `status:needs_spec` | `needs_spec` |
| `status:planned` | `planned` |
| `status:in progress` | `in progress` |
| `status:in review` | `in review` |
| `status:blocked` | `blocked` |
| `status:done` | `done` |

Lifecycle order: `needs_spec → planned → in progress → in review → done`; `blocked` from any point.

## Action rules the vocabulary depends on

- An issue carries exactly one `status:*` label (Single Status Invariant, `BACKLOG_MAP.md`). The Action does not strip stale labels: with two, the last one in the payload wins.
- Closing an issue as completed sets `done` regardless of label; closing as *not planned* leaves the board untouched. Reopening restores the issue's `status:*` label, or `planned` if it has none. This is why `closed ≡ status:done`.
- Issues with any `concept:*` label are excluded from the board.
- Other `key:value` labels (`type`, `size`, `priority`, …) only sync if the board has a single-select field of that name. Board #2 has none today, so they are skipped.

## Changing the vocabulary

1. Update the vocabulary in `src/memory-templates/BACKLOG_MAP.md`, this table, and the board's `Status` options together.
2. `tests/framework/test_status_label_contract.py` fails until the template and this table agree.
3. Rebuild `dist/` and bump versions per the normal release rules.

## Setup (per repository)

The workflow reads `PROJECT_TOKEN` (secret: a classic personal access token with the `project` scope — the default `GITHUB_TOKEN` cannot write Projects v2) and the variables `PROJECT_OWNER`, `PROJECT_OWNER_TYPE` (`user` or `org`; the default is `org`), `PROJECT_NUMBER` and optionally `DRY_RUN=true`. The workflow file is a byte-identical copy of `src/github/sync-labels-to-project.yml`, which is what `stratosphere-setup` installs into consumer projects.
