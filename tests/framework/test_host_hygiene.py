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
HOST_MATRIX = "src/dev-skills/improve-workflows-skills/references/host-matrix.md"
HOST_NAMES = ("Claude Code", "Gemini CLI", "Antigravity", "Codex", "Cursor", "Devin", "Copilot", "Jules", "OpenClaw")
HOST_SECTION_BUDGET = 1000  # chars, ~250 tokens: AGENTS.md is always loaded, so per-host facts live in HOST_MATRIX


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def host_section(text: str) -> str:
    """The §8 bullets that used to carry per-host facts: Host activation and HITL enforcement."""
    return text[text.index("- **Host activation.**"):text.index("- **Subagent nesting.**")] + text[text.index("- **HITL enforcement"):]


@pytest.mark.parametrize("rel", CONSTITUTIONS)
def test_constitution_host_section_names_no_host_and_stays_small(rel):
    section = host_section(read(rel))
    named = [host for host in HOST_NAMES if host in section]
    assert not named, f"AGENTS.md is always loaded; per-host facts ({named}) belong in {HOST_MATRIX}"
    assert not re.search(r"\d+\.\d+\.\d+", section), "version floors belong in the host matrix"
    assert "CLAUDE.md" in section and "GEMINI.md" in section, "the two pointer files stay named"
    assert len(section) <= HOST_SECTION_BUDGET, f"host section is {len(section)} chars (budget {HOST_SECTION_BUDGET})"


def test_host_matrix_is_accurate():
    assert (REPO_ROOT / HOST_MATRIX).is_file(), "per-host facts moved out of AGENTS.md live here (dev-only, never shipped)"
    text = read(HOST_MATRIX)
    natively_row = next(line for line in text.splitlines() if "| natively" in line)
    assert "Claude Code" not in natively_row and "Gemini CLI" not in natively_row, \
        "Claude Code and Gemini CLI do not read AGENTS.md natively by default"
    assert "context.fileName" in text and "GEMINI.md" in text, "must say Gemini CLI loads GEMINI.md"
    for floor in ("2.1.277", "2.1.288", "0.150.0", "0.59.0"):
        assert floor in text, f"version floor {floor} missing from the host matrix"
    assert ".github/skills/" in text, "Copilot reads .github/skills/"
    assert "Devin path" not in text and ".github/copilot/skills" not in text, "stale Copilot skill path claim"
    assert re.search(r"\|\s*Copilot[^|]*\|[^\n]*`disable-model-invocation`", text), "Copilot row missing"
    assert re.search(r"\|\s*Gemini CLI\s*\|[^\n]*none", text), "Gemini CLI row missing"


def test_dev_skill_points_at_the_host_matrix():
    assert "references/host-matrix.md" in read("src/dev-skills/improve-workflows-skills/SKILL.md")


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
