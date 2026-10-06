#!/usr/bin/env python3
"""BT-148 host-hygiene contract: the always-loaded docs and shipped files must match what the
hosts actually do (upstream-watch 2026-10-06), and two dead artifacts must stay gone.

Pins the machine-checkable acceptance criteria only; prose wording beyond these needles is free.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
JULES = "src/experimental/jules-dispatch"
CONSTITUTIONS = ["src/constitution/AGENTS.md", "AGENTS.md"]  # product source + this repo's installed copy


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("rel", CONSTITUTIONS)
def test_constitution_host_activation_is_accurate(rel):
    text = read(rel)
    activation = text[text.index("- **Host activation.**"):text.index("- **Subagent nesting.**")]
    table = text[text.index("- **HITL enforcement"):]
    always_on = next(line for line in activation.splitlines() if "*Always-on rules:*" in line)

    native_clause = next(s for s in re.split(r"(?<=[.;])\s", always_on) if "natively" in s)
    assert "Claude Code" not in native_clause and "Gemini CLI" not in native_clause, \
        "Claude Code and Gemini CLI do not read AGENTS.md natively by default"
    assert "the two that don't" not in activation, "stale claim: Claude Code and Antigravity skip AGENTS.md"
    assert "context.fileName" in always_on and "GEMINI.md" in always_on, "must say Gemini CLI loads GEMINI.md"
    for floor in ("2.1.277", "2.1.288", "0.150.0", "0.59.0"):
        assert floor in activation, f"version floor {floor} missing from Host activation"

    assert ".github/skills/" in activation, "Copilot reads .github/skills/"
    assert "Devin path" not in activation and ".github/copilot/skills" not in activation, "stale Copilot skill path claim"
    assert re.search(r"\|\s*Copilot[^|]*\|\s*`disable-model-invocation`", table), "Copilot row missing from manual-only table"
    assert re.search(r"\|\s*Gemini CLI\s*\|\s*none", table), "Gemini CLI row missing from manual-only table"


@pytest.mark.parametrize("rel", ["README.md", "src/commands/stratosphere-setup/SKILL.md"])
def test_trust_prerequisite_documented(rel):
    text = read(rel)
    assert "0.150.0" in text, f"{rel} must name the Codex >= 0.150.0 project-trust prerequisite"
    assert "0.59.0" in text, f"{rel} must name the Gemini CLI >= 0.59.0 workspace-trust prerequisite"


def test_plan_html_hooks_json_removed():
    # Dead Stop hook in a shape no host loads (R6). Path parts, not one literal, so a grep for the dead path stays clean.
    for root in ("src", "dist"):
        dead = REPO_ROOT / root / "skills" / "plan-html" / "hooks.json"
        assert not dead.exists(), f"{dead.relative_to(REPO_ROOT).as_posix()} must stay deleted (rebuild dist after removing the source)"


def test_jules_contract_is_current():
    api = read(f"{JULES}/jules_api.py")
    contract = read(f"{JULES}/CONTRACT.md")
    assert 'query["createTime"]' not in api, "activities.list takes no createTime parameter (discovery doc 20261004)"
    assert "createTime=" not in contract, "poll row must not advertise a createTime parameter"
    assert "/activities?pageSize=" in contract, "poll row must list pageSize only"
    # ":archive" does not match ":unarchive" (unlike a bare "archive", which "archived" already satisfies)
    for needle in ("headRef", "baseRef", "workingBranch", "archived", ":archive", ":unarchive", "DELETE"):
        assert needle in contract, f"CONTRACT.md does not pin {needle!r}"
