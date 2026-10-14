#!/usr/bin/env python3
"""BT-169 wording pin: 0c writes a fixed-section handoff a cold agent can resume from."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SECTIONS = ("Scope & decisions", "Status & next", "Tree", "Verification", "Open",
            "On disk vs chat-only", "Suggested Skills/Workflows")


def test_0c_names_the_fixed_sections_in_order_and_never_carries_approval_over():
    text = (ROOT / "src" / "workflows" / "0c-handoff.md").read_text(encoding="utf-8")
    positions = [text.index(f"**{name}") for name in SECTIONS]
    assert positions == sorted(positions)
    assert "first action on resume" in text
    assert "do not carry over" in text
