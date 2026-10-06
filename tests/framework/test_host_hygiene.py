#!/usr/bin/env python3
"""BT-148 host-hygiene contract: the always-loaded docs and shipped files must match what the
hosts actually do (upstream-watch 2026-10-06), and two dead artifacts must stay gone.

Pins the machine-checkable acceptance criteria only; prose wording beyond these needles is free.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
JULES = REPO_ROOT / "src" / "experimental" / "jules-dispatch"


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_plan_html_hooks_json_removed():
    # Dead Stop hook in a shape no host loads (R6). Path parts, not one literal, so a grep for the dead path stays clean.
    for root in ("src", "dist"):
        dead = REPO_ROOT / root / "skills" / "plan-html" / "hooks.json"
        assert not dead.exists(), f"{dead.relative_to(REPO_ROOT).as_posix()} must stay deleted (rebuild dist after removing the source)"


def test_jules_contract_is_current():
    api = (JULES / "jules_api.py").read_text(encoding="utf-8")
    contract = (JULES / "CONTRACT.md").read_text(encoding="utf-8")
    assert 'query["createTime"]' not in api, "activities.list takes no createTime parameter (discovery doc 20261004)"
    assert "createTime=" not in contract, "poll row must not advertise a createTime parameter"
    assert "/activities?pageSize=" in contract
    for needle in ("headRef", "baseRef", "workingBranch", "archived", "archive", "unarchive", "delete"):
        assert needle in contract, f"CONTRACT.md does not pin {needle!r}"
