#!/usr/bin/env python3
"""BT-165 guards: deterministic artifact links. The discovery brief is located by `linked-prd:` (briefs are slug-only), PRD frontmatter carries `discovery:`/`research:`, and spec paths for a slice are keyed to its parent. Later slices extend this file."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def test_no_workflow_locates_a_brief_by_bt_id():
    # Briefs are slug-only; a BT-<padded>-* filename pattern never matches one.
    for f in sorted((SRC / "workflows").glob("*.md")):
        assert "docs/discovery/BT-" not in f.read_text(encoding="utf-8"), f.name


LOCATOR = ("whose frontmatter has `linked-prd: BT-<padded>`; "
           "if none, 2a's slug fuzzy-match (2a Phase 1 step 5)")


def test_2c_and_2z_share_one_brief_locator():
    # One rule, worded identically, so the two readers cannot drift apart.
    for rel in ("workflows/2c-reconcile-specs.md", "workflows/2z-write-spec.md"):
        assert LOCATOR in _read(rel), rel


def test_2a_fills_the_prd_links():
    assert "`discovery:` / `research:`" in _read("workflows/2a-write-prd.md")


def test_prd_template_frontmatter_links_brief_and_research():
    fm = _read("references/PRD-template.md").split("## Artifact frontmatter")[1].split("## Artifact body")[0]
    assert "\ndiscovery:" in fm and "\nresearch:" in fm


def test_slice_workflows_key_spec_paths_to_the_parent():
    for rel in ("workflows/3d-implement-issue.md", "workflows/4a-verify-and-ship.md", "workflows/3z-afk-loop.md"):
        text = _read(rel)
        for stale in ("docs/prds/BT-<padded>", "docs/design/BT-<padded>"):
            assert stale not in text, (rel, stale)
        assert "BT-<parentPadded>" in text, rel
        assert "standalone slice has no" in text, rel
