#!/usr/bin/env python3
"""Contract tests for Presentation & Question Contract (BT-271).

# md-crosscheck: output-mode contract vs lifecycle, command skills, and built dist/ bundle

Enforces:
1. src/rules/output-mode.md Section 5 defines the 4-part Presentation & Question Contract
   (Tool Execution Barrier, Visible Markdown Content, Synchronous Pairing, Fallback)
   plus native question tool names and multi-select flags.
2. Lifecycle workflows (3b, 0b, 0d, 3a, 3c, 4a) and command skills (stratosphere-setup,
   stratosphere-update) cite .agents/rules/output-mode.md §5, keep visible-evidence +
   same-turn cues inline, and do not duplicate the 3-bullet boilerplate.
3. Zero interactive decision gates permit empty content or running question tools alongside other tools.
"""
from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
RULES = SRC / "rules"
DIST_SKILLS = ROOT / "dist" / "skills"


def test_output_mode_section_5_contract():
    output_mode = (RULES / "output-mode.md").read_text(encoding="utf-8")
    assert "## 5. Presentation & Question Contract" in output_mode
    section_5 = output_mode.split("## 5. Presentation & Question Contract", 1)[1]

    # 1. Tool Execution Barrier
    assert "Tool Execution Barrier" in section_5
    assert re.search(r"background|finish|other tools", section_5, re.IGNORECASE)

    # 2. Visible Markdown Content
    assert re.search(r"(Mandatory )?Visible (Markdown )?Content", section_5)
    assert re.search(r"evidence|table|card|content", section_5, re.IGNORECASE)

    # 3. Synchronous Pairing
    assert "Synchronous Pairing" in section_5
    assert re.search(r"same turn|synchronous", section_5, re.IGNORECASE)

    # 4. Fallback
    assert "Fallback" in section_5
    assert "halt" in section_5.lower()

    # Native question tools + multi-select parameters centralized here
    assert "ask_question" in section_5 and "AskUserQuestion" in section_5
    assert "is_multi_select: true" in section_5 and "multiSelect: true" in section_5


GATED_SKILLS = [
    ("workflows/0b-stop-session.md", "0b-stop-session/SKILL.md", r"classification table"),
    ("workflows/0d-nightly-consolidation.md", "0d-nightly-consolidation/SKILL.md", r"recommendations summary"),
    ("workflows/3a-version-planning.md", "3a-version-planning/SKILL.md", r"roadmap presentation"),
    ("workflows/3b-create-issue.md", "3b-create-issue/SKILL.md", r"Slices Proposed for Minting"),
    ("workflows/3c-sprint-planning.md", "3c-sprint-planning/SKILL.md", r"Topological Sprint Sequence"),
    ("workflows/4a-verify-and-ship.md", "4a-verify-and-ship/SKILL.md", r"Unified Ship Verification Gate"),
    ("commands/stratosphere-setup/SKILL.md", "stratosphere-setup/SKILL.md", r"label mapping table"),
    ("commands/stratosphere-update/SKILL.md", "stratosphere-update/SKILL.md", r"detected legacy paths|consolidated summary"),
]


@pytest.mark.parametrize("src_rel,dist_rel,evidence_rx", GATED_SKILLS)
def test_gated_skills_cite_output_mode_section_5_without_boilerplate(src_rel, dist_rel, evidence_rx):
    text = (SRC / src_rel).read_text(encoding="utf-8")
    assert ".agents/rules/output-mode.md" in text and "§5" in text, (
        f"{src_rel} must cite .agents/rules/output-mode.md §5 at its interactive gate"
    )
    assert re.search(rf"visible[^\n]*{evidence_rx}", text, re.IGNORECASE), (
        f"{src_rel} must keep inline visible-evidence cue ({evidence_rx})"
    )
    assert "same-turn" in text.lower(), f"{src_rel} must keep inline same-turn pairing cue"
    for boilerplate in (
        "**Tool Execution Barrier:**",
        "**Mandatory Visible Markdown Content:**",
        "**Synchronous Pairing:**",
    ):
        assert boilerplate not in text, f"{src_rel} must not duplicate {boilerplate} from output-mode.md §5"

    dist_text = (DIST_SKILLS / dist_rel).read_text(encoding="utf-8")
    assert dist_text == text, f"dist drift: {dist_rel} != src/{src_rel}"


def test_zero_empty_content_or_unshielded_background_tools():
    output_mode = (RULES / "output-mode.md").read_text(encoding="utf-8")
    assert re.search(r"empty|`?Content:\s*None`?", output_mode, re.IGNORECASE)
    assert re.search(r"same turn", output_mode, re.IGNORECASE) and "never invoke a question tool" in output_mode.lower()
