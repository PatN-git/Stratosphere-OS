#!/usr/bin/env python3
"""Tests for BT-270: Obsidian wikilink migration CLI (scripts/migrations/migrate_obsidian_links.py)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT, git

SCRIPT = REPO_ROOT / "scripts" / "migrations" / "migrate_obsidian_links.py"
VALIDATE_SCRIPT = REPO_ROOT / "src" / "scripts" / "validate_memory.py"

ARCH_CONTENT = """---
type: architecture
title: Architecture
description: System architecture.
generated:
  by: test
  at: 2026-11-17
version: "1.0.0"
---
# ARCHITECTURE

## Structural Rules
- [[A-001]] [LAW] Rule one.
"""

LEARN_CONTENT = """---
type: learnings
title: Learnings
description: System learnings.
generated:
  by: test
  at: 2026-11-17
version: "1.0.0"
---
# LEARNINGS

## Active Entries
- [[L-001]] [ASSUMED] [2026-11-17] Learning one.
"""


def _write(root: Path, rel: str, text: str, newline: str = "\n") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline=newline)
    return p


def _init_repo(tmp_path: Path, files: dict[str, str], untracked: dict[str, str] | None = None) -> Path:
    git(tmp_path, "init", "-b", "main")
    for rel, content in files.items():
        _write(tmp_path, rel, content)
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-m", "base")
    for rel, content in (untracked or {}).items():
        _write(tmp_path, rel, content)
    return tmp_path


def run_migration(project: Path, *extra_args: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SCRIPT), "--project", str(project), *extra_args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def run_validator(cwd: Path) -> tuple[int, str, dict]:
    r = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT)],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    out = r.stdout
    machine_idx = out.rfind("# MACHINE\n")
    payload = json.loads(out[machine_idx + len("# MACHINE\n"):].strip()) if machine_idx != -1 else {}
    return r.returncode, out, payload


def test_dry_run_reports_and_modifies_no_files(tmp_path):
    """AC 1: --dry-run reports candidate link rewrites and MOCs without modifying files."""
    files = {
        "docs/prds/BT-001.md": "---\ntype: prd\ntitle: Doc One\ndescription: First PRD.\n---\n# Doc One\n",
        "docs/plans/plan.md": "---\ntype: proposal\ntitle: Plan\ndescription: A plan.\n---\n[Doc One](../prds/BT-001.md)\n",
    }
    repo = _init_repo(tmp_path, files)
    before_content = (repo / "docs/plans/plan.md").read_text(encoding="utf-8")

    r = run_migration(repo, "--dry-run")
    assert r.returncode == 0, f"Expected 0, got {r.returncode}: {r.stderr}"
    assert "Candidate Link Rewrites" in r.stdout or "docs/plans/plan.md" in r.stdout
    assert "[[BT-001|Doc One]]" in r.stdout

    # File on disk must NOT be modified
    assert (repo / "docs/plans/plan.md").read_text(encoding="utf-8") == before_content
    # index.md must NOT exist
    assert not (repo / "docs/prds/index.md").exists()
    assert not (repo / "docs/plans/index.md").exists()


def test_atomic_in_place_migration_rewrites_links_and_mocs(tmp_path):
    """AC 2: --write on clean tree rewrites links and regenerates MOC index.md files."""
    files = {
        "docs/prds/BT-001.md": "---\ntype: prd\ntitle: Doc One\ndescription: First PRD.\n---\n# Doc One\n",
        "docs/plans/plan.md": (
            "---\ntype: proposal\ntitle: Plan\ndescription: A plan.\n---\n"
            "Review [Doc One](../prds/BT-001.md) and [Section](#sec) here.\n"
        ),
    }
    repo = _init_repo(tmp_path, files)

    r = run_migration(repo, "--write")
    assert r.returncode == 0, f"Expected 0, got {r.returncode}: {r.stderr}"

    plan_text = (repo / "docs/plans/plan.md").read_text(encoding="utf-8")
    assert "[[BT-001|Doc One]]" in plan_text
    assert "[Section](#sec)" in plan_text

    prds_index = repo / "docs/prds/index.md"
    assert prds_index.exists()
    prds_text = prds_index.read_text(encoding="utf-8")
    assert "# prds" in prds_text
    assert "* [[BT-001|Doc One]] - First PRD." in prds_text


def test_validation_pass_after_migration_clean(tmp_path):
    """AC 3: validate_memory.py passes 100% clean after migration."""
    files = {
        ".memory/ARCHITECTURE.md": ARCH_CONTENT,
        ".memory/LEARNINGS.md": LEARN_CONTENT,
        "docs/prds/BT-001.md": (
            "---\ntype: prd\ntitle: Doc One\ndescription: First PRD.\ngenerated:\n  by: test\n  at: 2026-11-17\n---\n"
            "# Doc One\nGoverned by [[A-001]].\n"
        ),
        "docs/plans/plan.md": (
            "---\ntype: proposal\ntitle: Plan\ndescription: A plan.\ngenerated:\n  by: test\n  at: 2026-11-17\n---\n"
            "# Plan\nSee [Doc One](../prds/BT-001.md).\n"
        ),
    }
    repo = _init_repo(tmp_path, files)

    r = run_migration(repo, "--write")
    assert r.returncode == 0

    # Add the newly generated/modified files to git so validate_memory can resolve them via tracked_files
    git(repo, "add", "-A")

    code, out, payload = run_validator(repo)
    assert code == 0, f"Validator failed (exit {code}):\n{out}"
    assert payload.get("clean") is True, f"Validator not clean: {payload}"
    assert payload.get("errors") == []
    assert payload.get("warnings") == []


def test_dirty_working_tree_aborts_without_modifications(tmp_path):
    """AC 4: --write on dirty working tree aborts with error without modifying files."""
    files = {
        "docs/prds/BT-001.md": "---\ntype: prd\ntitle: Doc One\ndescription: First PRD.\n---\n# Doc One\n",
        "docs/plans/plan.md": "---\ntype: proposal\ntitle: Plan\ndescription: A plan.\n---\n[Doc One](../prds/BT-001.md)\n",
    }
    repo = _init_repo(tmp_path, files)

    # Make working tree dirty
    (repo / "docs/plans/plan.md").write_text(
        "---\ntype: proposal\ntitle: Plan\ndescription: A plan.\n---\n[Doc One](../prds/BT-001.md)\n<!-- dirty edit -->\n",
        encoding="utf-8",
    )

    before_content = (repo / "docs/plans/plan.md").read_text(encoding="utf-8")

    r = run_migration(repo, "--write")
    assert r.returncode == 1
    assert "Error: Working tree is dirty. Commit or stash changes before running --write" in r.stderr
    assert (repo / "docs/plans/plan.md").read_text(encoding="utf-8") == before_content
    assert not (repo / "docs/prds/index.md").exists()

    # --force should bypass the dirty check
    r_force = run_migration(repo, "--write", "--force")
    assert r_force.returncode == 0
    assert "[[BT-001|Doc One]]" in (repo / "docs/plans/plan.md").read_text(encoding="utf-8")


def test_line_ending_preservation_lf_and_crlf(tmp_path):
    """AC 5: Preserves LF line endings on Windows without CRLF churn per [[L-004]]."""
    files = {
        "docs/prds/BT-001.md": "---\ntype: prd\ntitle: Doc One\ndescription: First PRD.\n---\n# Doc One\n",
    }
    repo = _init_repo(tmp_path, files)

    # Write one file with LF and one with CRLF
    lf_file = repo / "docs/plans/lf_plan.md"
    lf_file.parent.mkdir(parents=True, exist_ok=True)
    lf_file.write_bytes(b"---\ntype: proposal\ntitle: LF\ndescription: LF.\n---\n[Doc One](../prds/BT-001.md)\n")

    crlf_file = repo / "docs/plans/crlf_plan.md"
    crlf_file.write_bytes(b"---\r\ntype: proposal\r\ntitle: CRLF\r\ndescription: CRLF.\r\n---\r\n[Doc One](../prds/BT-001.md)\r\n")

    r = run_migration(repo, "--write", "--force")
    assert r.returncode == 0

    lf_bytes = lf_file.read_bytes()
    assert b"\r\n" not in lf_bytes, "LF file must not contain CRLF"
    assert b"[[BT-001|Doc One]]" in lf_bytes

    crlf_bytes = crlf_file.read_bytes()
    assert b"\r\n" in crlf_bytes, "CRLF file must preserve CRLF"
    assert b"[[BT-001|Doc One]]" in crlf_bytes


def test_stem_collision_uses_minimum_path_prefix(tmp_path):
    """Disambiguates duplicate active stems with minimum path prefix."""
    files = {
        "docs/discovery/target.md": "---\ntype: discovery\ntitle: Discovery Target\ndescription: Discovery.\n---\n# Target\n",
        "docs/research/target.md": "---\ntype: research\ntitle: Research Target\ndescription: Research.\n---\n# Target\n",
        "docs/plans/plan.md": "---\ntype: proposal\ntitle: Plan\ndescription: Plan.\n---\n[Research](../research/target.md)\n",
    }
    repo = _init_repo(tmp_path, files)

    r = run_migration(repo, "--write")
    assert r.returncode == 0

    plan_text = (repo / "docs/plans/plan.md").read_text(encoding="utf-8")
    assert "[[docs/research/target|Research]]" in plan_text


def test_reserved_stems_index_and_readme_path_qualified(tmp_path):
    """Links to index.md or README.md must be path-qualified."""
    files = {
        "docs/research/sub/README.md": "# Readme\n",
        "docs/plans/plan.md": "---\ntype: proposal\ntitle: Plan\ndescription: Plan.\n---\n[Corpus](../research/sub/README.md)\n",
    }
    repo = _init_repo(tmp_path, files)

    r = run_migration(repo, "--write")
    assert r.returncode == 0

    plan_text = (repo / "docs/plans/plan.md").read_text(encoding="utf-8")
    assert "[[docs/research/sub/README|Corpus]]" in plan_text


def test_code_blocks_and_comments_preserved(tmp_path):
    """Links inside code blocks, backticks, and comments are not rewritten."""
    content = (
        "---\ntype: proposal\ntitle: Plan\ndescription: Plan.\n---\n"
        "[Real Link](../prds/BT-001.md)\n\n"
        "```python\n[Code Link](../prds/BT-001.md)\n```\n\n"
        "`[Inline Link](../prds/BT-001.md)`\n\n"
        "<!-- [Comment Link](../prds/BT-001.md) -->\n\n"
        "[`BT-001.md`](../prds/BT-001.md)\n"
    )
    files = {
        "docs/prds/BT-001.md": "---\ntype: prd\ntitle: Doc One\ndescription: First PRD.\n---\n# Doc One\n",
        "docs/plans/plan.md": content,
    }
    repo = _init_repo(tmp_path, files)

    r = run_migration(repo, "--write")
    assert r.returncode == 0

    plan_text = (repo / "docs/plans/plan.md").read_text(encoding="utf-8")
    assert "[[BT-001|Real Link]]" in plan_text
    assert "```python\n[Code Link](../prds/BT-001.md)\n```" in plan_text
    assert "`[Inline Link](../prds/BT-001.md)`" in plan_text
    assert "<!-- [Comment Link](../prds/BT-001.md) -->" in plan_text
    assert "[[BT-001|`BT-001.md`]]" in plan_text


def test_external_urls_and_images_untouched(tmp_path):
    """External URLs, anchors, mailto, and images are untouched."""
    content = (
        "---\ntype: proposal\ntitle: Plan\ndescription: Plan.\n---\n"
        "[Google](https://google.com)\n"
        "[Anchor](#local-section)\n"
        "[Email](mailto:user@example.com)\n"
        "![Logo](assets/logo.png)\n"
    )
    files = {
        "docs/plans/plan.md": content,
    }
    repo = _init_repo(tmp_path, files)

    r = run_migration(repo, "--write")
    assert r.returncode == 0
    assert (repo / "docs/plans/plan.md").read_text(encoding="utf-8") == content


def test_unresolvable_dangling_link_aborts_in_write_mode(tmp_path):
    """Two-phase commit: an unresolvable link aborts exit 1 without writing to disk."""
    files = {
        "docs/plans/plan.md": "---\ntype: proposal\ntitle: Plan\ndescription: Plan.\n---\n[Missing](non-existent-doc.md)\n",
    }
    repo = _init_repo(tmp_path, files)
    before_content = (repo / "docs/plans/plan.md").read_text(encoding="utf-8")

    r = run_migration(repo, "--write")
    assert r.returncode == 1
    assert "non-existent-doc.md" in r.stderr or "non-existent-doc" in r.stderr
    assert (repo / "docs/plans/plan.md").read_text(encoding="utf-8") == before_content
