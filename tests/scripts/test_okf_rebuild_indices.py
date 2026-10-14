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



def test_nested_yaml_keys_do_not_overwrite_top_level_fields(tmp_path):
    (tmp_path / ".memory").mkdir()
    (tmp_path / ".memory" / "NESTED.md").write_text(
        "---\ntype: proposal\ntitle: Top title\ndescription: Top description\n"
        "generated:\n  by: skill\n  at: 2026-10-13T10:00:00\n"
        "related:\n  title: Nested title\n  description: Nested description\n"
        "tags:\n  - alpha\n  - beta\n---\n\nbody\n", encoding="utf-8")
    fm = okf_view.OKFDocument.parse((tmp_path / ".memory" / "NESTED.md").read_text(encoding="utf-8")).frontmatter
    assert fm["title"] == "Top title" and fm["description"] == "Top description"
    assert "by" not in fm and "at" not in fm
    assert fm["generated"] is None and fm["related"] is None
    assert fm["tags"] == ["alpha", "beta"]
    okf_view.rebuild_indices(tmp_path)
    assert "* [Top title](/.memory/NESTED.md) - Top description\n" in (
        tmp_path / ".memory" / "index.md").read_text(encoding="utf-8")


def test_nested_key_resets_list_state():
    fm = okf_view.OKFDocument.parse(
        "---\ntype: x\nparent:\n  child: value\n  - stray\nafter: ok\n---\n").frontmatter
    assert fm["parent"] is None and fm["after"] == "ok"


# --- BT-168: a blank description falls back to the first body paragraph ------

def _index_line(tmp: Path, name: str, text: str) -> str:
    (tmp / ".memory").mkdir(exist_ok=True)
    (tmp / ".memory" / name).write_text(text, encoding="utf-8")
    okf_view.rebuild_indices(tmp)
    lines = (tmp / ".memory" / "index.md").read_text(encoding="utf-8").splitlines()
    return next(l for l in lines if f"/.memory/{name})" in l)


def test_explicit_description_wins_over_body_paragraph(tmp_path):
    line = _index_line(tmp_path, "A.md",
                       "---\ntype: plan\ntitle: A\ndescription: Declared.\n---\n\nBody paragraph.\n")
    assert line == "* [A](/.memory/A.md) - Declared."


def test_blank_description_falls_back_to_first_paragraph(tmp_path):
    for fm in ("description:\n", ""):  # blank value, and key absent
        line = _index_line(tmp_path, "B.md",
                           f"---\ntype: plan\ntitle: B\n{fm}---\n\nFirst line\nsecond   line.\n\nLater paragraph.\n")
        assert line == "* [B](/.memory/B.md) - First line second line."


def test_fallback_skips_headings_quotes_comments_and_tables_and_is_cut(tmp_path):
    long_para = " ".join(["word"] * 60)
    line = _index_line(tmp_path, "C.md",
                       "---\ntype: plan\ntitle: C\ndescription:\n---\n\n# Heading\n\n> note\n\n"
                       "<!-- multi\nline comment -->\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
                       f"## Sub\n{long_para}\n")
    desc = line.split(" - ", 1)[1]
    assert desc.startswith("word word") and desc.endswith("…")
    assert len(desc) <= 161 and "Heading" not in desc and "note" not in desc and "|" not in desc


def test_body_with_only_skipped_constructs_leaves_no_description(tmp_path):
    line = _index_line(tmp_path, "D.md", "---\ntype: plan\ntitle: D\n---\n\n# Only heading\n\n> quote\n")
    assert line == "* [D](/.memory/D.md)"


def test_fallback_skips_code_fences(tmp_path):
    line = _index_line(tmp_path, "E.md",
                       "---\ntype: plan\ntitle: E\n---\n\n```bash\nrm -rf nothing\n\nstill code\n```\n\n"
                       "~~~\ntilde code\n~~~\n\nReal text.\n")
    assert line == "* [E](/.memory/E.md) - Real text."


def test_fallback_skips_rules_raw_html_and_unterminated_comment(tmp_path):
    line = _index_line(tmp_path, "F.md",
                       "---\ntype: plan\ntitle: F\n---\n\n---\n\n* * *\n\n<div class=\"x\">\n\n_ _ _\n\nProse here.\n")
    assert line == "* [F](/.memory/F.md) - Prose here."
    line = _index_line(tmp_path, "G.md", "---\ntype: plan\ntitle: G\n---\n\n<!-- never closed\n\nHidden.\n")
    assert line == "* [G](/.memory/G.md)"
