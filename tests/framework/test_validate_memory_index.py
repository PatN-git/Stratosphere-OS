#!/usr/bin/env python3
# md-crosscheck: validate_memory.py indexer AST extraction against memory markdown and workflows
"""Tests for deterministic AST memory hydration and consolidation (BT-224 / Epic BT-223)."""
import os
import sys
import time
import subprocess
from pathlib import Path
from unittest.mock import patch
import pytest
from conftest import REPO_ROOT, SRC, read_src

sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
import _versioning

SCRIPT = REPO_ROOT / "src" / "scripts" / "validate_memory.py"

ARCH_FIXTURE = """---
type: architecture
title: Architecture
description: Test fixture.
generated:
  by: test
  at: 2026-11-06
version: "1.0.0"
---
# ARCHITECTURE

## Structural Rules
- **[[A-001]] [LAW]** Keep page/app files focused on top-level state coordination.
- **[[A-003]] [LAW]** Do not mix unrelated concerns in large component files. If a file exceeds 400 lines, extract concerns. Never inline multi-line shell strings. Avoid: God-components. Check: tests/standards/size.test.js
"""

LEARNINGS_FIXTURE = """---
type: learnings
title: Learnings
description: Test fixture.
generated:
  by: test
  at: 2026-11-06
version: "1.0.0"
---
# LEARNINGS

## Active Entries
- **[[L-001]] [ASSUMED] [2026-10-05]** Baseline lesson. Source: BT-001.
- **[[L-003]] [PATTERN] [2026-10-05]** Detail drawer state must remain outside map marker components to avoid rerender loop. Avoid: inline closures in markers. Source: BT-002.
"""

GLOSSARY_FIXTURE = """---
type: glossary
title: Glossary
description: Test fixture.
generated:
  by: test
  at: 2026-11-06
version: "1.0.0"
---
# GLOSSARY

## Active Entries
- **[[G-001]] [ASSUMED] [2026-11-05]** App Shell: Frame container. Avoid: outer wrapper. Source: BT-010.
- **[[G-002]] [ASSUMED] [2026-11-05]** Drawer: slide-over panel. Avoid: modal, popup. Source: BT-100.
"""

DESIGN_RULES_FIXTURE = """---
type: design-rules
title: Design Rules
description: Test fixture.
generated:
  by: test
  at: 2026-11-06
version: "1.0.0"
---
# DESIGN RULES

## Active Rules
- **[[DR-001]] [LAW]** Avoid raw hex colors. Use design tokens exclusively. Check: tests/standards/design_tokens.test.js
"""


def _setup_mock_memory(tmp_path):
    mem = tmp_path / ".memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "ARCHITECTURE.md").write_text(ARCH_FIXTURE, encoding="utf-8")
    (mem / "LEARNINGS.md").write_text(LEARNINGS_FIXTURE, encoding="utf-8")
    (mem / "GLOSSARY.md").write_text(GLOSSARY_FIXTURE, encoding="utf-8")
    (mem / "DESIGN_RULES.md").write_text(DESIGN_RULES_FIXTURE, encoding="utf-8")
    return mem


def test_validate_memory_index_issue_body_file(tmp_path):
    mem = _setup_mock_memory(tmp_path)
    issue_file = tmp_path / "issue-test.md"
    issue_file.write_text("""# Task
Refs: [[A-003]], [[L-003]]
Also depends on [[G-002]] and [[DR-001]].
Placeholder [[L-XXX]] should be ignored.
""", encoding="utf-8")
    out_file = tmp_path / ".tmp" / "active-refs.txt"

    cmd = [
        sys.executable, str(SCRIPT),
        "--index",
        "--issue-body", str(issue_file),
        "--memory-dir", str(mem),
        "--out", str(out_file)
    ]
    r = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert out_file.exists()

    content = out_file.read_text(encoding="utf-8")
    assert "[[A-003]]" in content
    assert "[[L-003]]" in content
    assert "[[G-002]]" in content
    assert "[[DR-001]]" in content
    assert "[[L-XXX]]" not in content
    assert "[[A-001]]" not in content
    assert "[[G-001]]" not in content


def test_validate_memory_index_performance_under_5ms(tmp_path):
    mem = _setup_mock_memory(tmp_path)
    issue_file = tmp_path / "issue-perf.md"
    issue_file.write_text("""# Task Performance
Check [[A-001]], [[A-003]], [[L-003]], [[G-002]], [[DR-001]].
""", encoding="utf-8")
    out_file = tmp_path / ".tmp" / "perf-refs.txt"

    import validate_memory
    body = issue_file.read_text(encoding="utf-8")
    # Warm up disk/cache
    validate_memory.extract_active_refs(
        issue_body=body,
        memory_dir=mem,
        out_path=out_file
    )

    times = []
    for _ in range(10):
        start = time.perf_counter()
        res = validate_memory.extract_active_refs(
            issue_body=body,
            memory_dir=mem,
            out_path=out_file
        )
        times.append((time.perf_counter() - start) * 1000.0)
    elapsed_ms = min(times)

    assert res == 0
    assert out_file.exists()
    budget = 25.0 if os.environ.get("CI") else 5.0
    assert elapsed_ms < budget, f"AST indexer execution took {elapsed_ms:.3f}ms, exceeding {budget}ms budget"


def test_validate_memory_index_preserves_negative_constraints(tmp_path):
    mem = _setup_mock_memory(tmp_path)
    issue_file = tmp_path / "issue-negative.md"
    issue_file.write_text("Needs [[A-003]] and [[G-002]].", encoding="utf-8")
    out_file = tmp_path / ".tmp" / "negative-refs.txt"

    subprocess.run([
        sys.executable, str(SCRIPT),
        "--index",
        "--issue-body", str(issue_file),
        "--memory-dir", str(mem),
        "--out", str(out_file)
    ], cwd=tmp_path, check=True)

    text = out_file.read_text(encoding="utf-8")
    assert "Avoid: God-components" in text
    assert "Do not mix unrelated concerns" in text
    assert "Never inline multi-line shell strings" in text
    assert "Avoid: modal, popup" in text
    assert "[LAW]" in text


def test_validate_memory_index_missing_and_placeholder_handling(tmp_path):
    mem = _setup_mock_memory(tmp_path)
    issue_file = tmp_path / "issue-missing.md"
    issue_file.write_text("Mentions [[L-999]] and placeholder [[A-XXX]].", encoding="utf-8")
    out_file = tmp_path / ".tmp" / "missing-refs.txt"

    r = subprocess.run([
        sys.executable, str(SCRIPT),
        "--index",
        "--issue-body", str(issue_file),
        "--memory-dir", str(mem),
        "--out", str(out_file)
    ], cwd=tmp_path, capture_output=True, text=True)

    assert r.returncode == 0
    text = out_file.read_text(encoding="utf-8")
    assert "[[A-XXX]]" not in text
    assert "L-999" in text
    assert "Unresolved References" in text or "not found" in text.lower()


def test_validate_memory_index_query_issue_mock(tmp_path):
    mem = _setup_mock_memory(tmp_path)
    out_file = tmp_path / ".tmp" / "query-refs.txt"

    import validate_memory

    # Test query_issue with mock runner returning JSON body
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"body": "Task context referencing [[A-001]] and [[L-003]]."}'
        res = validate_memory.extract_active_refs(
            query_issue="BT-223",
            memory_dir=mem,
            out_path=out_file
        )
        assert res == 0
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "[[A-001]]" in content
        assert "[[L-003]]" in content
        # Ensure '223' was queried without crash
        called_cmd = mock_run.call_args[0][0]
        assert "223" in called_cmd


def test_0a_start_session_and_load_memory_consume_active_refs():
    text_0a = read_src("workflows/0a-start-session.md")
    text_load = read_src("skills/load-memory/SKILL.md")

    # 0a assertions
    assert "validate_memory.py --index" in text_0a
    assert "Zero Test/Build Invariant" in text_0a
    assert "S2A" in text_0a or "System 2 Attention" in text_0a
    assert "k-NN" in text_0a or "vector" in text_0a

    # load-memory assertions
    assert "validate_memory.py --index" in text_load
    assert ".tmp/active-memory-refs.txt" in text_load
    assert "negative constraints" in text_load.lower()


def test_0b_and_0d_streamlined_templates_and_diff_verification():
    text_0b = read_src("workflows/0b-stop-session.md")
    text_0d = read_src("workflows/0d-nightly-consolidation.md")

    # 0b assertions
    assert "git diff" in text_0b
    assert "negative constraints" in text_0b.lower()
    assert "validate_memory.py" in text_0b

    # 0d assertions
    assert "| Slug | Nights | Ladder Rung |" in text_0d
    assert "Diff-Based Consolidation Verification" in text_0d
    assert "git log --since=" in text_0d


def test_0e_plain_english_standardized_prompt_structure():
    text_0e = read_src("workflows/0e-plain-english.md")
    assert "≤ 250 words" in text_0e or "<= 250 words" in text_0e
    assert "Verdict:" in text_0e
    assert "Picture:" in text_0e
    assert "Needs from you:" in text_0e
    assert "Recommendation:" in text_0e
    assert "Heads-up:" in text_0e
    assert "Left out:" in text_0e
    assert 'Say "more" for details' in text_0e


def test_0b_session_tmp_files_review_and_triage_proposal():
    text_0b = read_src("workflows/0b-stop-session.md")
    # Procedure step assertions: inspect .tmp/ and present 3-way HITL triage proposal
    assert ".tmp/" in text_0b
    assert "triage" in text_0b.lower()
    assert "delete" in text_0b.lower()
    assert "relocate" in text_0b.lower()
    assert "keep" in text_0b.lower()
    assert "docs/" in text_0b
    assert "OKF frontmatter" in text_0b
    assert "confirmation" in text_0b.lower()
    # Explicit exemptions for active framework state files
    assert ".tmp/3d-suite-*.json" in text_0b
    assert ".tmp/3z-loop.work.md" in text_0b
    assert ".tmp/3d-plan-*.md" in text_0b
    assert ".tmp/4a-audit-*.json" in text_0b
    # Handoff Note Format assertion
    assert "- Tmp files triaged (deleted / relocated / kept):" in text_0b


def test_stage0_frontmatter_version_bumps():
    for rel_path, expected_v in [
        ("skills/load-memory/SKILL.md", "1.3.0"),
        ("workflows/0a-start-session.md", "1.4.0"),
        ("workflows/0b-stop-session.md", "1.10.0"),
        ("workflows/0d-nightly-consolidation.md", "1.8.0"),
        ("workflows/0e-plain-english.md", "1.2.0"),
    ]:
        content = read_src(rel_path)
        v, _ = _versioning.read_version(content, rel_path)
        assert v == expected_v, f"{rel_path} version mismatch: expected {expected_v}, got {v}"
