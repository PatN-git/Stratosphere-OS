#!/usr/bin/env python3
"""L3 `3b` assertions for `tracker: github`: no map, the store and the gate are the only record.

Split out of `assertions.py` (one concern per file, A-003). `assertions.check_3b_github` loads this by path and passes
its own `mirror_ok`, so the real gate is still run by one definition.
"""
from __future__ import annotations

REQUIRED_SLICE_LABELS = ("type:", "tier:slice", "mode:", "size:")


def label_names(issue: dict) -> set:
    return {l["name"] for l in issue["labels"]}


def check(ctx, issues: list, mirror_ok) -> list:
    """GitHub mode: no map may exist; every slice carries the required labels and a parent; the gate (run here) reaches
    `[MIRROR-OK]` against the state the phase must have left (slices `planned`, under the epic)."""
    problems = []
    if (ctx.project / ".memory" / "BACKLOG_MAP.md").exists():
        problems.append("BACKLOG_MAP.md exists, but `tracker: github` keeps no map")
    epics = [i for i in issues if "tier:epic" in label_names(i)]
    slices = [i for i in issues if "tier:epic" not in label_names(i)]
    expect = []
    for i in slices:
        bt, names = f"BT-{i['number']:03d}", label_names(i)
        missing = [p for p in REQUIRED_SLICE_LABELS if not any(n.startswith(p) for n in names)]
        if missing:
            problems.append(f"{bt} lacks required label(s) {missing}")
        if epics and not i.get("parent"):
            problems.append(f"{bt} has no parent: 3b must link every slice under its epic")
        expect.append(f"{bt}:status=planned")
        if epics and i.get("parent"):
            expect.append(f"{bt}:parent=BT-{i['parent']['number']:03d}")
    ids = ",".join(f"BT-{i['number']:03d}" for i in issues)
    ok, out = mirror_ok(ctx, ids, expect)
    if not ok:
        problems.append(f"the terminal sync gate did not reach [MIRROR-OK]: {out.strip()[:300]}")
    return problems
