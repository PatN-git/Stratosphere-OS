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
HOST_SECTION_BUDGET = 700  # chars, ~175 tokens: AGENTS.md is always loaded, so per-host facts live in HOST_MATRIX
OKF_PROTOCOL = "src/rules/okf-protocol.md"


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


@pytest.mark.parametrize("rel", CONSTITUTIONS)
def test_constitution_section_8_names_no_host(rel):
    # Whole section, not only the host bullets: the Subagent nesting bullet once said "Claude Code".
    text = read(rel)
    section = text[text.index("## 8."):]
    named = [host for host in HOST_NAMES if host in section]
    assert not named, f"{rel} section 8 is always loaded and must stay host-free; {named} belong in {HOST_MATRIX}"






CONSTITUTION_BUDGET = 9200  # chars: AGENTS.md is always loaded; the cap keeps additions deliberate


@pytest.mark.parametrize("rel", CONSTITUTIONS)
def test_constitution_stays_within_its_char_budget(rel):
    n = len(read(rel))
    assert n <= CONSTITUTION_BUDGET, \
        f"{rel} is {n} chars (budget {CONSTITUTION_BUDGET}); move per-case rules to a reference"


def test_constitution_intermediates_names_scratch_scripts_and_no_inline_code_identically():
    def bullet(rel: str) -> str:
        return next(l for l in read(rel).splitlines() if l.startswith("- **Intermediates:**"))

    assert bullet(CONSTITUTIONS[0]) == bullet(CONSTITUTIONS[1])
    text = bullet(CONSTITUTIONS[0])
    assert "scratch scripts" in text and "`.tmp/`" in text
    assert "`python -c`" in text and "heredocs" in text and "file content" in text
    assert "write it with the file-write tool, code to `.tmp/`" in text


def test_constitution_section_8_identical_across_copies():
    # Only the pre-existing trailing backtick line may differ between the product source and this repo's copy.
    def section8(rel: str) -> str:
        text = read(rel)
        return text[text.index("## 8."):].rstrip("\n`")

    assert section8(CONSTITUTIONS[0]) == section8(CONSTITUTIONS[1])


@pytest.mark.parametrize("rel", CONSTITUTIONS)
def test_constitution_has_no_stray_backtick_line(rel):
    # BT-154 F5: a backtick-only last line shipped to consumers.
    text = read(rel)
    assert not re.search(r"^\s*`+\s*$", text, re.M), f"{rel} has a backtick-only line"
    assert text.endswith("\n"), f"{rel} must end with a newline"










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
