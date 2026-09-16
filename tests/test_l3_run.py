"""L3 Slice 1 - the run wrapper and the two checks it added to containment.

No agent and no network: every test here builds its own stub project or stub
validator, so the wrapper's failure paths are exercised without spending a run.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).parent / "lifecycle-harness"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


e = _load("l3_env_run", HARNESS / "env.py")
# The filename is not an identifier, so it can only be loaded by path.
r = _load("l3_run", HARNESS / "run-L3.py")

REPO = Path(__file__).resolve().parents[1]

# Enough environment to find the interpreter, and nothing else: the real
# caller passes a fully scrubbed environ, and an empty dict would fail on
# Windows for a reason that has nothing to do with what is under test.
CHILD = {"PATH": os.environ.get("PATH", ""),
         "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}


def _stub_project(tmp_path, exit_code, message="stub validator"):
    """A project shaped like a scaffold, with a validator that exits as told."""
    proj = tmp_path / "proj"
    scripts = proj / ".agents" / "scripts"
    scripts.mkdir(parents=True)
    (proj / ".memory").mkdir()
    (scripts / "validate_memory.py").write_text(
        f"import sys\nprint({message!r})\nsys.exit({exit_code})\n", encoding="utf-8")
    return proj


# --- E1: the working repo is part of the manifest, not just the HOME paths ----

def test_repo_status_is_empty_for_a_clean_repo(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
    assert e.repo_status(tmp_path) == ""


def test_repo_status_notices_an_untracked_file(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
    (tmp_path / "stray.md").write_text("written by the run", encoding="utf-8")
    assert "stray.md" in e.repo_status(tmp_path)


def test_watched_manifest_covers_the_working_repo_too(tmp_path):
    """E1 names four things; three of them live under HOME and one does not."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)

    before = e.watched_manifest(home, repo)
    assert any(str(repo) in k for k in before)

    (repo / "left-behind.txt").write_text("x", encoding="utf-8")
    drift = e.diff_manifest(before, e.watched_manifest(home, repo))
    assert drift and "left-behind.txt" in drift[0]


def test_a_repo_that_is_not_a_repo_does_not_crash_the_manifest(tmp_path):
    assert "git status failed" in e.repo_status(tmp_path / "nowhere")


# --- the scaffolded memory layer must validate before phase 1 -----------------

def test_memory_gate_passes_a_clean_project(tmp_path):
    e.assert_memory_valid(_stub_project(tmp_path, 0), CHILD)


def test_memory_gate_fails_on_errors_and_quotes_the_validator(tmp_path):
    proj = _stub_project(tmp_path, 1, message="ID collision: [[D-001]] twice")
    with pytest.raises(RuntimeError) as exc:
        e.assert_memory_valid(proj, CHILD)
    assert "exit 1" in str(exc.value)
    assert "ID collision" in str(exc.value)


def test_memory_gate_fails_on_warnings_too(tmp_path):
    """Exit 2 is warnings. A run that starts from a warning state will blame the
    lifecycle for something the scaffold brought with it."""
    proj = _stub_project(tmp_path, 2, message="one-way reference")
    with pytest.raises(RuntimeError) as exc:
        e.assert_memory_valid(proj, CHILD)
    assert "exit 2" in str(exc.value)


def test_memory_gate_names_a_missing_validator(tmp_path):
    proj = tmp_path / "empty"
    proj.mkdir()
    with pytest.raises(RuntimeError) as exc:
        e.assert_memory_valid(proj, CHILD)
    assert "validate_memory.py" in str(exc.value)


# --- the wrapper -------------------------------------------------------------

def test_keep_is_never_the_default():
    assert r.parse_args([]).keep is False
    assert r.parse_args(["--keep"]).keep is True


def test_repo_defaults_to_this_checkout():
    assert Path(r.parse_args([]).repo).resolve() == REPO


def test_preflight_refuses_a_directory_that_is_not_a_checkout(tmp_path):
    with pytest.raises(SystemExit) as exc:
        r.preflight(tmp_path)
    assert "not a StratOS checkout" in str(exc.value)


def test_preflight_accepts_this_checkout():
    r.preflight(REPO)          # must not raise


class _FakeEnv:
    def __init__(self, tmp_path, child_env=None, remote=None):
        self.root = tmp_path
        self.home = tmp_path / "home"
        self.project = tmp_path / "project"
        self.bare = tmp_path / "origin.git"
        self.child_env = child_env if child_env is not None else {"HOME": str(self.home)}
        subprocess.run(["git", "init", str(self.project)], capture_output=True, check=True)
        if remote:
            subprocess.run(["git", "-C", str(self.project), "remote", "add",
                            "origin", remote], capture_output=True, check=True)


def test_contained_run_passes(tmp_path):
    env = _FakeEnv(tmp_path, remote=str(tmp_path / "origin.git"))
    r.assert_contained(env)    # must not raise


def test_a_leaked_token_fails_the_run(tmp_path):
    env = _FakeEnv(tmp_path, remote=str(tmp_path / "origin.git"))
    env.child_env["GH_TOKEN"] = "ghp_real"
    with pytest.raises(RuntimeError) as exc:
        r.assert_contained(env)
    assert "GH_TOKEN" in str(exc.value)


def test_a_remote_outside_the_root_fails_the_run(tmp_path):
    env = _FakeEnv(tmp_path, remote="https://github.com/PatN-git/Stratosphere-OS.git")
    with pytest.raises(RuntimeError) as exc:
        r.assert_contained(env)
    assert "temp root" in str(exc.value)


def test_no_remote_at_all_fails_the_run(tmp_path):
    """`2a`/`2b` push by design. A project with no origin pushes wherever
    GIT_CONFIG_GLOBAL's pushDefault sends it, which is not something to assume."""
    env = _FakeEnv(tmp_path)
    with pytest.raises(RuntimeError) as exc:
        r.assert_contained(env)
    assert "no remote at all" in str(exc.value)


def test_a_failed_environment_exits_one_and_says_why(tmp_path, monkeypatch, capsys):
    import contextlib

    @contextlib.contextmanager
    def boom(*a, **kw):
        raise RuntimeError("refusing to start - a repository can push outside it")
        yield

    monkeypatch.setattr(r.env_mod, "lifecycle_env", boom)
    assert r.main(["--repo", str(REPO)]) == 1
    assert "push outside" in capsys.readouterr().out
