#!/usr/bin/env python3
"""Tests for scripts/migrations/migrate_v3_to_v4.py (v3 layout -> v4 Agent Skills).

The gitignore cases are regression tests: a real v3 project carried BOTH
`.agents/skills/*` and `.agents/skills/`, and an exact-match filter removed only
the second — leaving every migrated skill in an ignored path, which is the exact
failure this migration exists to prevent.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "migrations" / "migrate_v3_to_v4.py"


def run(project: Path, *extra):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--project", str(project), *extra],
        capture_output=True, text=True,
    )


def _seed(project: Path, gitignore_lines, *, workflows=("0a_start-session.md",), foreign=()):
    (project / ".gitignore").write_text("\n".join(gitignore_lines) + "\n", encoding="utf-8")
    wf = project / ".agents" / "workflows"
    wf.mkdir(parents=True)
    lock = {"artifacts": {}}
    for name in workflows:
        (wf / name).write_text("# framework\n", encoding="utf-8")
        lock["artifacts"][f".agents/workflows/{name}"] = {"version": "3.3.0"}
    for name in foreign:
        (wf / name).write_text("# mine\n", encoding="utf-8")
    (project / ".agents" / ".stratosphere-lock.json").write_text(
        json.dumps(lock), encoding="utf-8")


def _gitignore(project: Path):
    return (project / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_every_skills_ignore_spelling_is_removed():
    """The `*` variant must go too, or all 26 migrated skills stay untracked."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        _seed(p, [".agents/skills/*", "!.agents/skills/.lock.json",
                  "/.agents/skills/**", ".agents/skills/", "node_modules/"])
        assert run(p, "--apply").returncode == 0
        left = _gitignore(p)
        assert not [l for l in left if ".agents/skills" in l], left
        assert "node_modules/" in left, "unrelated entries must survive"


def test_unrelated_ignores_and_nested_paths_survive():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        _seed(p, [".agents/rules/", ".agents/skills/foo.md", ".env"])
        assert run(p, "--apply").returncode == 0
        left = _gitignore(p)
        for entry in (".agents/rules/", ".agents/skills/foo.md", ".env"):
            assert entry in left, (entry, left)


def test_dry_run_writes_nothing():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        _seed(p, [".agents/skills/*"])
        before = (p / ".gitignore").read_text(encoding="utf-8")
        r = run(p)
        assert r.returncode == 0
        assert (p / ".gitignore").read_text(encoding="utf-8") == before
        assert (p / ".agents" / "workflows" / "0a_start-session.md").exists()


def test_user_authored_workflow_survives_but_framework_files_go():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        _seed(p, [".agents/skills/*"], foreign=("my-own-thing.md",))
        assert run(p, "--apply").returncode == 0
        wf = p / ".agents" / "workflows"
        assert (wf / "my-own-thing.md").exists(), "user-authored file must be kept"
        assert not (wf / "0a_start-session.md").exists(), "framework file must be removed"


def test_is_idempotent():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        _seed(p, [".agents/skills/*", ".agents/skills/"])
        assert run(p, "--apply").returncode == 0
        first = _gitignore(p)
        assert run(p, "--apply").returncode == 0
        assert _gitignore(p) == first
