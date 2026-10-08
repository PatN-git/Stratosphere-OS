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


@pytest.mark.parametrize("rel", CONSTITUTIONS)
def test_constitution_section_8_keeps_install_and_authoring_rules_out(rel):
    # /sync-skills install wiring is enforced by check_suite.py visibility; "workflows cite skills by name,
    # never by path" is an authoring rule (improve-workflows-skills playbook). Neither guides a running agent.
    text = read(rel)
    section = text[text.index("## 8."):]
    for needle in ("never paths", "/sync-skills"):
        assert needle not in section, f"{rel} section 8 is always loaded; {needle!r} is not a runtime rule"


def test_playbook_carries_the_moved_cite_skills_by_name_rule():
    text = read("src/dev-skills/improve-workflows-skills/references/playbook.md")
    assert "never by path" in text and "SKILL.md` on disk" in text, \
        "authoring rule moved out of AGENTS.md section 8: skills are cited by name, the constitution's disk rule resolves them"


def test_constitution_section_8_identical_across_copies():
    # Only the pre-existing trailing backtick line may differ between the product source and this repo's copy.
    def section8(rel: str) -> str:
        text = read(rel)
        return text[text.index("## 8."):].rstrip("\n`")

    assert section8(CONSTITUTIONS[0]) == section8(CONSTITUTIONS[1])


def test_okf_manual_only_pointer_does_not_send_readers_to_section_8():
    # Section 8 no longer carries the manual-only field table; only section 1 describes the skill layers.
    text = read(OKF_PROTOCOL)
    para = next(p for p in text.split("\n\n") if p.startswith("**Skill invocation is not governed here.**"))
    assert "AGENTS.md" in para and "§1" in para, "must still point at AGENTS.md section 1"
    assert "§8" not in para, "AGENTS.md section 8 has no field table; do not send readers there for one"


def test_host_matrix_is_accurate():
    assert (REPO_ROOT / HOST_MATRIX).is_file(), "per-host facts moved out of AGENTS.md live here (dev-only, never shipped)"
    text = read(HOST_MATRIX)
    natively_row = next(line for line in text.splitlines() if "| natively" in line)
    assert "Claude Code" not in natively_row and "Gemini CLI" not in natively_row, \
        "Claude Code and Gemini CLI do not read AGENTS.md natively by default"
    assert "Antigravity" not in natively_row, "Antigravity has its own row: its pointer file is GEMINI.md, not none"
    assert re.search(r"\|\s*Antigravity\s*\|\s*natively\s*\|[^|\n]*`GEMINI\.md`", text), \
        "Antigravity row must say it loads AGENTS.md natively and keeps the GEMINI.md pointer file"
    assert "context.fileName" in text and "GEMINI.md" in text, "must say Gemini CLI loads GEMINI.md"
    for floor in ("2.1.277", "2.1.288", "0.150.0", "0.59.0"):
        assert floor in text, f"version floor {floor} missing from the host matrix"
    assert ".github/skills/" in text, "Copilot reads .github/skills/"
    assert "never `.agents/skills/`" in text, "Claude Code does not read .agents/skills/ (the constitution no longer says so)"
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
