import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_SCRIPTS = REPO_ROOT / "src" / "scripts"
SCAFFOLD_SCRIPT = SRC_SCRIPTS / "scaffold.py"

sys.path.insert(0, str(SRC_SCRIPTS))
import scaffold


def run_src_scaffold(cwd: Path, *args: str, stdin_input: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCAFFOLD_SCRIPT), *args],
        cwd=str(cwd),
        input=stdin_input,
        capture_output=True,
        text=True,
    )


def test_vault_obsidian_scaffolds_configs_and_gitignore_idempotently(tmp_path: Path):
    r1 = run_src_scaffold(tmp_path, "--vault", "obsidian")
    assert r1.returncode == 0, r1.stdout + r1.stderr

    obs = tmp_path / ".obsidian"
    assert (obs / "app.json").is_file()
    assert (obs / "graph.json").is_file()
    assert (obs / "core-plugins.json").is_file()

    app_cfg = json.loads((obs / "app.json").read_text(encoding="utf-8"))
    assert app_cfg["useMarkdownLinks"] is False
    assert app_cfg["newLinkFormat"] == "shortest"
    assert app_cfg["showLineNumber"] is True
    assert isinstance(app_cfg["userIgnoreFilters"], list)

    graph_cfg = json.loads((obs / "graph.json").read_text(encoding="utf-8"))
    assert graph_cfg["search"] == "path:docs OR path:.memory"
    assert len(graph_cfg["colorGroups"]) >= 7

    plugins_cfg = json.loads((obs / "core-plugins.json").read_text(encoding="utf-8"))
    assert "graph" in plugins_cfg
    assert "backlink" in plugins_cfg

    gi_lines_1 = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    for entry in (".obsidian/workspace*.json", ".obsidian/cache/", ".obsidian/graph-cache.json"):
        assert gi_lines_1.count(entry) == 1

    # Idempotent re-run must not duplicate .gitignore lines
    r2 = run_src_scaffold(tmp_path, "--vault", "obsidian")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    gi_lines_2 = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    for entry in (".obsidian/workspace*.json", ".obsidian/cache/", ".obsidian/graph-cache.json"):
        assert gi_lines_2.count(entry) == 1

    lock_data = json.loads((tmp_path / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_data.get("vault") == "obsidian"


def test_vault_none_opt_out_purity(tmp_path: Path):
    # Pre-populate .gitignore with baseline StratOS entries so we can verify byte-for-byte untouched
    baseline_gi = "\n".join(scaffold.GITIGNORE_ENTRIES) + "\n# custom rule\n"
    (tmp_path / ".gitignore").write_text(baseline_gi, encoding="utf-8")

    r = run_src_scaffold(tmp_path, "--vault", "none")
    assert r.returncode == 0, r.stdout + r.stderr

    assert not (tmp_path / ".obsidian").exists()
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == baseline_gi

    lock_data = json.loads((tmp_path / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_data.get("vault") == "none"


def test_vault_okf_html_records_choice_without_obsidian(tmp_path: Path):
    r = run_src_scaffold(tmp_path, "--vault", "okf-html")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (tmp_path / ".obsidian").exists()
    gi_text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".obsidian/" not in gi_text
    lock_data = json.loads((tmp_path / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_data.get("vault") == "okf-html"


def test_vault_update_preserves_user_configs_and_lockfile(tmp_path: Path):
    r1 = run_src_scaffold(tmp_path, "--vault", "obsidian")
    assert r1.returncode == 0, r1.stdout + r1.stderr

    app_path = tmp_path / ".obsidian" / "app.json"
    graph_path = tmp_path / ".obsidian" / "graph.json"
    custom_app = json.dumps({"useMarkdownLinks": False, "customUserKey": "keep-me"}, indent=2) + "\n"
    custom_graph = json.dumps({"search": "path:docs", "customGraph": True}, indent=2) + "\n"
    app_path.write_text(custom_app, encoding="utf-8")
    graph_path.write_text(custom_graph, encoding="utf-8")

    # Run --update without --vault: must preserve existing .obsidian edits and lockfile vault choice
    r2 = run_src_scaffold(tmp_path, "--update")
    assert r2.returncode == 0, r2.stdout + r2.stderr

    assert app_path.read_text(encoding="utf-8") == custom_app
    assert graph_path.read_text(encoding="utf-8") == custom_graph
    lock_data = json.loads((tmp_path / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_data.get("vault") == "obsidian"


def test_vault_graph_json_schema_and_dynamic_ignore_filters(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / ".memory").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "custom_app").mkdir()
    (tmp_path / "archive").mkdir()

    filters = scaffold.get_dynamic_ignore_filters(tmp_path)
    assert "^src/" in filters
    assert "^custom_app/" in filters
    assert "^archive/" in filters
    assert "^docs/" not in filters
    assert "^\\.memory/" not in filters
    assert "^\\.obsidian/" not in filters

    r = run_src_scaffold(tmp_path, "--vault", "obsidian")
    assert r.returncode == 0, r.stdout + r.stderr
    app_cfg = json.loads((tmp_path / ".obsidian" / "app.json").read_text(encoding="utf-8"))
    assert "^custom_app/" in app_cfg["userIgnoreFilters"]
    assert "^archive/" in app_cfg["userIgnoreFilters"]
    assert "^docs/archive/" in app_cfg["userIgnoreFilters"]

    graph_cfg = json.loads((tmp_path / ".obsidian" / "graph.json").read_text(encoding="utf-8"))
    assert graph_cfg["search"] == "path:docs OR path:.memory"
    queries = {g["query"] for g in graph_cfg["colorGroups"]}
    assert "file:.memory" in queries
    assert "path:docs/prds" in queries
    assert "file:index.md" in queries


def test_vault_headless_non_tty_defaults_without_blocking(tmp_path: Path):
    # Explicit closed/empty stdin (isatty() == False) must not hang or prompt and must default to none
    r = run_src_scaffold(tmp_path, stdin_input="")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (tmp_path / ".obsidian").exists()
    lock_data = json.loads((tmp_path / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_data.get("vault") == "none"


def test_vault_tty_interactive_prompt_selects_obsidian(tmp_path: Path, monkeypatch):
    class FakeTTY(io.StringIO):
        def isatty(self) -> bool:
            return True

    # Two prompts in fresh TTY mode: delivery mode ("1") then vault mode ("2" = obsidian)
    answers = iter(["1", "2"])
    monkeypatch.setattr(sys, "stdin", FakeTTY())
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [str(SCAFFOLD_SCRIPT)])

    scaffold.main()
    assert (tmp_path / ".obsidian" / "app.json").is_file()
    assert (tmp_path / ".obsidian" / "graph.json").is_file()
    assert (tmp_path / ".obsidian" / "core-plugins.json").is_file()
    lock_data = json.loads((tmp_path / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_data.get("vault") == "obsidian"


def test_vault_obsidian_dry_run_stages_without_writing(tmp_path: Path):
    r = run_src_scaffold(tmp_path, "--vault", "obsidian", "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (tmp_path / ".obsidian").exists()
    assert not (tmp_path / ".gitignore").exists()
    staged_gi = (tmp_path / ".gitignore.stratosphere-new").read_text(encoding="utf-8")
    assert ".obsidian/workspace*.json" in staged_gi
    assert ".obsidian/cache/" in staged_gi
    assert ".obsidian/graph-cache.json" in staged_gi
    assert ".tmp/" in staged_gi


def test_dist_bundle_scaffolds_obsidian_vault(tmp_path: Path):
    dist_scaffold = REPO_ROOT / "dist" / "skills" / "stratosphere-setup" / "scripts" / "scaffold.py"
    r = subprocess.run(
        [sys.executable, str(dist_scaffold), "--vault", "obsidian"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / ".obsidian" / "app.json").is_file()
    assert (tmp_path / ".obsidian" / "graph.json").is_file()
    assert (tmp_path / ".obsidian" / "core-plugins.json").is_file()
    assert not (REPO_ROOT / "dist" / "assets" / "templates").exists()


def test_get_bundled_project_scripts_skips_pycache_and_pyc(tmp_path: Path, monkeypatch):
    fake_plugin = tmp_path / "plugin"
    (fake_plugin / "scripts" / "okf_viewer" / "__pycache__").mkdir(parents=True)
    (fake_plugin / "scripts" / "okf_viewer" / "__init__.py").write_text("", encoding="utf-8")
    (fake_plugin / "scripts" / "okf_viewer" / "__pycache__" / "__init__.cpython-313.pyc").write_bytes(
        b"\xf3\x0d\x0d\x0a\x00"
    )
    (fake_plugin / "scripts" / "design" / "__pycache__").mkdir(parents=True)
    (fake_plugin / "scripts" / "design" / "design_theme.py").write_text("# ok\n", encoding="utf-8")
    (fake_plugin / "scripts" / "design" / "__pycache__" / "design_theme.cpython-313.pyc").write_bytes(
        b"\xf3\x0d\x0d\x0a\x00"
    )

    monkeypatch.setattr(scaffold, "PLUGIN_ROOT", fake_plugin)
    bundled = scaffold.get_bundled_project_scripts(tmp_path / "proj")
    rels = [rel for _, _, rel in bundled]
    assert ".agents/scripts/okf_viewer/__init__.py" in rels
    assert ".agents/scripts/design/design_theme.py" in rels
    assert not any("__pycache__" in rel or rel.endswith(".pyc") for rel in rels), rels
