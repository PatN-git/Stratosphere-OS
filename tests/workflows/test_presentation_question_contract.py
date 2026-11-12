#!/usr/bin/env python3
"""Contract tests for Presentation & Question Contract (BT-271).

# md-crosscheck: output-mode contract vs lifecycle and command decision gates

Enforces:
1. src/rules/output-mode.md Section 5 defines the 4-part Presentation & Question Contract
   (Tool Execution Barrier, Mandatory Visible Markdown Content, Synchronous Pairing, Fallback Invariant).
2. Lifecycle workflows (3b, 0b, 0d, 3a, 3c, 4a) mandate tool execution barrier, visible markdown in content,
   and synchronous pairing with ask_question / AskUserQuestion.
3. Command skills (stratosphere-setup, stratosphere-update) mandate tool execution barrier, visible markdown
   in content, and synchronous pairing with question tools.
4. Zero interactive decision gates permit empty content or running question tools unshielded with background tools.
"""
from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
RULES = SRC / "rules"
WORKFLOWS = SRC / "workflows"
COMMANDS = SRC / "commands"


def test_output_mode_section_5_contract():
    output_mode = (RULES / "output-mode.md").read_text(encoding="utf-8")
    assert "## 5. Presentation & Question Contract" in output_mode, (
        "src/rules/output-mode.md must contain '## 5. Presentation & Question Contract'"
    )
    section_5 = output_mode.split("## 5. Presentation & Question Contract", 1)[1]
    
    # Tool Execution Barrier
    assert "Tool Execution Barrier" in section_5, "Section 5 must define 'Tool Execution Barrier'"
    assert re.search(r"background|barrier|completion", section_5, re.IGNORECASE), (
        "Section 5 must specify barrier/completion of background tools"
    )
    
    # Mandatory Visible Markdown Content
    assert re.search(r"Mandatory Visible (Markdown )?Content", section_5), (
        "Section 5 must define 'Mandatory Visible Content'"
    )
    assert re.search(r"content|table|card|evidence", section_5, re.IGNORECASE), (
        "Section 5 must mandate emission in visible message content"
    )
    
    # Synchronous Pairing
    assert "Synchronous Pairing" in section_5, "Section 5 must define 'Synchronous Pairing'"
    assert re.search(r"same turn|synchronous|pair", section_5, re.IGNORECASE), (
        "Section 5 must mandate synchronous pairing of visible markdown with question tools"
    )
    
    # Non-Interactive Fallback Contract / Fallback Invariant
    assert re.search(r"Fallback", section_5), "Section 5 must define Fallback contract"


def test_lifecycle_workflows_presentation_contract():
    # 3b-create-issue
    wf_3b = (WORKFLOWS / "3b-create-issue.md").read_text(encoding="utf-8")
    assert re.search(r"Tool [Ee]xecution [Bb]arrier", wf_3b), (
        "3b-create-issue must specify Tool Execution Barrier for minting gate"
    )
    assert re.search(r"Visible (Markdown )?Content|visible message `?content`?", wf_3b, re.IGNORECASE), (
        "3b-create-issue must specify visible markdown content in message content"
    )
    assert re.search(r"Synchronous Pairing|same turn", wf_3b, re.IGNORECASE), (
        "3b-create-issue must specify synchronous pairing with question tool"
    )

    # 0b-stop-session
    wf_0b = (WORKFLOWS / "0b-stop-session.md").read_text(encoding="utf-8")
    assert re.search(r"Tool [Ee]xecution [Bb]arrier", wf_0b), (
        "0b-stop-session must specify Tool Execution Barrier for tmp triage gate"
    )
    assert re.search(r"visible|content|table", wf_0b, re.IGNORECASE), (
        "0b-stop-session must mandate visible markdown content for candidate files"
    )
    assert re.search(r"Synchronous Pairing|same turn", wf_0b, re.IGNORECASE), (
        "0b-stop-session must specify synchronous pairing with question tool"
    )

    # 0d-nightly-consolidation
    wf_0d = (WORKFLOWS / "0d-nightly-consolidation.md").read_text(encoding="utf-8")
    assert re.search(r"Tool [Ee]xecution [Bb]arrier", wf_0d), (
        "0d-nightly-consolidation must specify Tool Execution Barrier for decision halt"
    )
    assert re.search(r"visible|content|summary", wf_0d, re.IGNORECASE), (
        "0d-nightly-consolidation must mandate visible markdown content"
    )
    assert re.search(r"Synchronous Pairing|same turn", wf_0d, re.IGNORECASE), (
        "0d-nightly-consolidation must specify synchronous pairing with question tool"
    )

    # 3a-version-planning
    wf_3a = (WORKFLOWS / "3a-version-planning.md").read_text(encoding="utf-8")
    assert re.search(r"Tool [Ee]xecution [Bb]arrier", wf_3a), (
        "3a-version-planning must specify Tool Execution Barrier for roadmap authorization gate"
    )
    assert re.search(r"visible|content", wf_3a, re.IGNORECASE), (
        "3a-version-planning must mandate visible markdown content"
    )
    assert re.search(r"Synchronous Pairing|same turn", wf_3a, re.IGNORECASE), (
        "3a-version-planning must specify synchronous pairing with question tool"
    )

    # 3c-sprint-planning
    wf_3c = (WORKFLOWS / "3c-sprint-planning.md").read_text(encoding="utf-8")
    assert re.search(r"Tool [Ee]xecution [Bb]arrier", wf_3c), (
        "3c-sprint-planning must specify Tool Execution Barrier for sprint authorization gate"
    )
    assert re.search(r"visible|content", wf_3c, re.IGNORECASE), (
        "3c-sprint-planning must mandate visible markdown content"
    )
    assert re.search(r"Synchronous Pairing|same turn", wf_3c, re.IGNORECASE), (
        "3c-sprint-planning must specify synchronous pairing with question tool"
    )

    # 4a-verify-and-ship
    wf_4a = (WORKFLOWS / "4a-verify-and-ship.md").read_text(encoding="utf-8")
    assert re.search(r"Tool [Ee]xecution [Bb]arrier", wf_4a), (
        "4a-verify-and-ship must specify Tool Execution Barrier for unified ship gate"
    )
    assert re.search(r"visible|content", wf_4a, re.IGNORECASE), (
        "4a-verify-and-ship must mandate visible markdown content"
    )
    assert re.search(r"Synchronous Pairing|same turn", wf_4a, re.IGNORECASE), (
        "4a-verify-and-ship must specify synchronous pairing with question tool"
    )


def test_command_skills_presentation_contract():
    # stratosphere-setup
    setup_skill = (COMMANDS / "stratosphere-setup" / "SKILL.md").read_text(encoding="utf-8")
    assert re.search(r"Tool [Ee]xecution [Bb]arrier", setup_skill), (
        "stratosphere-setup must specify Tool Execution Barrier for label mapping presentation"
    )
    assert re.search(r"visible|content|table", setup_skill, re.IGNORECASE), (
        "stratosphere-setup must mandate visible markdown emission of label mapping table"
    )
    assert re.search(r"Synchronous Pairing|same turn", setup_skill, re.IGNORECASE), (
        "stratosphere-setup must specify synchronous pairing with question tool"
    )

    # stratosphere-update
    update_skill = (COMMANDS / "stratosphere-update" / "SKILL.md").read_text(encoding="utf-8")
    assert re.search(r"Tool [Ee]xecution [Bb]arrier", update_skill), (
        "stratosphere-update must specify Tool Execution Barrier"
    )
    assert re.search(r"visible|content", update_skill, re.IGNORECASE), (
        "stratosphere-update must mandate visible markdown emission"
    )
    assert re.search(r"Synchronous Pairing|same turn", update_skill, re.IGNORECASE), (
        "stratosphere-update must specify synchronous pairing with question tool"
    )


def test_zero_empty_content_or_unshielded_background_tools():
    # Check that output-mode explicitly forbids empty content and unshielded background operations
    output_mode = (RULES / "output-mode.md").read_text(encoding="utf-8")
    assert re.search(r"empty (message )?content|`?Content:\s*None`?", output_mode, re.IGNORECASE), (
        "output-mode must explicitly forbid question tools with empty content / Content: None"
    )
    assert re.search(r"same turn|unshielded|barrier", output_mode, re.IGNORECASE), (
        "output-mode must explicitly forbid question tools directly following background tools in same turn"
    )
