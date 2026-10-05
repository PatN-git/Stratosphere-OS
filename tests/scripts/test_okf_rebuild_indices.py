#!/usr/bin/env python3
"""BT-142: okf_view.py --rebuild-indices deterministically rebuilds directory index.md files."""
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "src" / "scripts" / "okf_view.py"
spec = importlib.util.spec_from_file_location("okf_view", SCRIPT)
okf_view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(okf_view)


def _doc(path: Path, title: str, description: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntype: proposal\ntitle: {title}\ndescription: {description}\n"
                    f"generated:\n  by: x\n  at: 2026-10-05\n---\n\nbody\n", encoding="utf-8")


def _tree(tmp: Path):
    (tmp / ".memory").mkdir()
    _doc(tmp / ".memory" / "LEARNINGS.md", "Learnings", "Episodic lessons.")
    _doc(tmp / "docs" / "nightly" / "nightly-2026-10-04.md", "Nightly 10-04", "Night one")
    _doc(tmp / "docs" / "nightly" / "nightly-2026-10-05.md", "Nightly 10-05", "Night two")
    (tmp / "docs" / "nightly" / ".last-run.json").write_text("{}", encoding="utf-8")
    (tmp / "docs" / "nightly" / "index.md").write_text("stale\n", encoding="utf-8")
    _doc(tmp / "docs" / "knowledge" / "acme" / "concept.md", "Foreign", "must not be listed")
    (tmp / "docs" / "knowledge" / "beta").mkdir()
    (tmp / "docs" / "prds").mkdir()  # exists but empty


def test_rebuild_indices_writes_listing_per_directory(tmp_path):
    _tree(tmp_path)
    assert okf_view.rebuild_indices(tmp_path) == 4  # .memory, nightly, knowledge, prds
    assert (tmp_path / ".memory" / "index.md").read_text(encoding="utf-8") == (
        "# .memory\n\n* [Learnings](/.memory/LEARNINGS.md) - Episodic lessons.\n")
    nightly = (tmp_path / "docs" / "nightly" / "index.md").read_text(encoding="utf-8")
    assert nightly == ("# nightly\n\n"
                       "* [Nightly 10-04](/docs/nightly/nightly-2026-10-04.md) - Night one\n"
                       "* [Nightly 10-05](/docs/nightly/nightly-2026-10-05.md) - Night two\n")


def test_knowledge_index_lists_one_entry_per_source_bundle(tmp_path):
    _tree(tmp_path)
    okf_view.rebuild_indices(tmp_path)
    text = (tmp_path / "docs" / "knowledge" / "index.md").read_text(encoding="utf-8")
    assert "[acme](/docs/knowledge/acme/index.md)" in text
    assert "[beta](/docs/knowledge/beta/index.md)" in text
    assert "Foreign" not in text and "concept.md" not in text


def test_rebuild_is_idempotent_and_skips_absent_dirs(tmp_path):
    _tree(tmp_path)
    okf_view.rebuild_indices(tmp_path)
    first = (tmp_path / "docs" / "nightly" / "index.md").read_text(encoding="utf-8")
    assert okf_view.rebuild_indices(tmp_path) == 4
    assert (tmp_path / "docs" / "nightly" / "index.md").read_text(encoding="utf-8") == first
    assert not (tmp_path / "docs" / "research").exists()


def test_file_without_frontmatter_falls_back_to_stem(tmp_path):
    (tmp_path / ".memory").mkdir()
    (tmp_path / ".memory" / "NOTES.md").write_text("no frontmatter\n", encoding="utf-8")
    okf_view.rebuild_indices(tmp_path)
    assert "* [NOTES](/.memory/NOTES.md)\n" in (tmp_path / ".memory" / "index.md").read_text(encoding="utf-8")


def test_cli_prints_count_and_skips_visualization(tmp_path):
    _tree(tmp_path)
    r = subprocess.run([sys.executable, str(SCRIPT), "--project-root", str(tmp_path), "--rebuild-indices"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "4 indices rebuilt" in r.stdout
    assert not (tmp_path / "docs" / "okf-view.html").exists()
