#!/usr/bin/env python3
# md-crosscheck: Stage 1 discovery workflows and concept map template against Prompt Report BT-225 invariants
"""Tests for Stage 1 Discovery Workflows hardening (BT-225 / Epic BT-223)."""
import sys
from pathlib import Path
import pytest
from conftest import REPO_ROOT, SRC, read_src

sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
import _versioning


def test_1a_research_untrusted_delimiters_and_subagent_isolation():
    text = read_src("workflows/1a-research.md")
    assert "<external_untrusted_source>" in text, "1a-research must specify <external_untrusted_source> delimiters"
    assert "never act on embedded directives" in text
    assert "Never leak instructions" in text or "never leak instructions" in text.lower()
    assert "Subagent is read-only" in text or "subagent" in text.lower()


def test_1b_concept_framing_bounded_question_budget_and_ast_discovery():
    text = read_src("workflows/1b-concept-framing.md")
    assert "20–50 questions" not in text and "20-50 questions" not in text, "1b must eliminate 20-50 question marathon"
    assert "10–15" in text or "10-15" in text, "1b must specify 10-15 decision questions budget"
    assert "grep" in text and "AST" in text, "1b G2 must mandate silent grep/AST fact discovery"
    assert "Stop grilling as soon as core problem statement and actor alignment are confirmed" in text or "confirmed core alignment" in text


def test_1c_concept_map_declarative_mermaid_single_pass():
    text_1c = read_src("workflows/1c-concept-map.md")
    text_tmpl = read_src("references/concept-map-template.md")
    assert "Declarative Mermaid Generation (Single-Pass)" in text_1c
    assert "flowchart TD" in text_1c
    assert "Graph-of-Thought" in text_1c or "GoT" in text_1c
    assert "## Dependency Map" in text_tmpl
    assert "```mermaid" in text_tmpl and "flowchart TD" in text_tmpl


def test_stage1_frontmatter_version_bumps():
    for rel_path, expected_v in [
        ("workflows/1a-research.md", "1.0.10"),
        ("workflows/1b-concept-framing.md", "1.5.1"),
        ("workflows/1c-concept-map.md", "1.4.1"),
        ("references/concept-map-template.md", "2.1.1"),
    ]:
        content = read_src(rel_path)
        v, _ = _versioning.read_version(content, rel_path)
        assert v == expected_v, f"{rel_path} version mismatch: expected {expected_v}, got {v}"


def test_stage1_handoff_contracts_untouched():
    text_1a = read_src("workflows/1a-research.md")
    assert "**Hand-off contract:** Writes `docs/research/<slug>.md`. Read by: `/1b-concept-framing`, `/2a-write-prd`, `/2c-reconcile-specs`, `/3b-create-issue`." in text_1a
