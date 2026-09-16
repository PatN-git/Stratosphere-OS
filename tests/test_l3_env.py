"""L3 containment - the invariants that stop a run reaching the real world.

These need git but not the `claude` CLI, so the dangerous half of the harness is
verifiable here even though driving an agent is not.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).parent / "lifecycle-harness" / "env.py"
_spec = importlib.util.spec_from_file_location("l3_env", _SRC)
e = importlib.util.module_from_spec(_spec)
sys.modules["l3_env"] = e
_spec.loader.exec_module(e)

REPO = Path(__file__).resolve().parents[1]


def _repo(path, remote=None):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", str(path)], capture_output=True, check=True)
    if remote:
        subprocess.run(["git", "-C", str(path), "remote", "add", "origin", remote],
                       capture_output=True, check=True)
    return path


# --- E1: nothing that can authenticate to real GitHub reaches the child ------

def test_scrub_drops_tokens_and_keeps_everything_else():
    out = e.scrub({"GH_TOKEN": "x", "GITHUB_TOKEN": "y", "GITHUB_ACTIONS": "true",
                   "GH_ENTERPRISE_TOKEN": "z", "PATH": "/usr/bin", "HOME": "/h"})
    assert out == {"PATH": "/usr/bin", "HOME": "/h"}


def test_manifest_notices_a_new_file(tmp_path):
    watched = tmp_path / "w"
    watched.mkdir()
    (watched / "a.txt").write_text("a", encoding="utf-8")
    before = e.manifest([watched])
    (watched / "b.txt").write_text("b", encoding="utf-8")
    assert e.diff_manifest(before, e.manifest([watched]))


def test_manifest_is_stable_when_nothing_changes(tmp_path):
    watched = tmp_path / "w"
    watched.mkdir()
    (watched / "a.txt").write_text("a", encoding="utf-8")
    assert not e.diff_manifest(e.manifest([watched]), e.manifest([watched]))


def test_absent_path_is_recorded_not_crashed(tmp_path):
    assert e.manifest([tmp_path / "nope"])[str(tmp_path / "nope")] == "<absent>"


# --- E7: no repository under the temp root can push outside it ---------------

def test_preflight_rejects_a_remote_pointing_outside(tmp_path):
    _repo(tmp_path / "proj", remote="https://github.com/PatN-git/Stratosphere-OS.git")
    with pytest.raises(RuntimeError) as exc:
        e.preflight_remotes(tmp_path)
    assert "push outside" in str(exc.value)
    assert "github.com" in str(exc.value)


def test_preflight_accepts_a_remote_inside_the_root(tmp_path):
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(bare)], capture_output=True, check=True)
    _repo(tmp_path / "proj", remote=str(bare))
    e.preflight_remotes(tmp_path)          # must not raise


def test_preflight_walks_nested_repos_not_just_the_project(tmp_path):
    """run-L2.py copies the repo with its .git, so the hazard is a NESTED repo."""
    _repo(tmp_path / "proj")
    _repo(tmp_path / "proj" / "vendored",
          remote="git@github.com:PatN-git/Stratosphere-OS.git")
    with pytest.raises(RuntimeError) as exc:
        e.preflight_remotes(tmp_path)
    assert "vendored" in str(exc.value)


def test_strip_remotes_clears_every_nested_repo(tmp_path):
    _repo(tmp_path / "proj", remote="https://github.com/x/y.git")
    _repo(tmp_path / "proj" / "inner", remote="https://github.com/a/b.git")
    assert e.strip_remotes(tmp_path) == 2
    e.preflight_remotes(tmp_path)          # now clean


# --- E2: the environment is built, contained, and removed --------------------

def test_lifecycle_env_builds_and_tears_down():
    with e.lifecycle_env(REPO, scaffold=False) as env:
        root = env.root
        assert env.project.exists() and env.bare.exists()
        assert env.home.exists()
        # origin resolves into the temp root, never to GitHub
        remotes = e.git_remotes(env.project / ".git")
        assert remotes and all(str(root) in r for r in remotes)
        # tokens never reach the child
        assert not any(k.startswith(("GH_", "GITHUB_")) for k in env.child_env)
        assert env.child_env["HOME"] == str(env.home)
        assert str(root) in env.child_env["GIT_CONFIG_GLOBAL"]
    assert not root.exists(), "temp root survived teardown"


def test_teardown_runs_even_when_the_body_raises():
    root = None
    with pytest.raises(ValueError):
        with e.lifecycle_env(REPO, scaffold=False) as env:
            root = env.root
            raise ValueError("phase blew up")
    assert root is not None and not root.exists()


def test_git_config_redirects_github_urls_into_the_bare_repo():
    with e.lifecycle_env(REPO, scaffold=False) as env:
        cfg = Path(env.child_env["GIT_CONFIG_GLOBAL"]).read_text(encoding="utf-8")
        assert "insteadOf = https://github.com/" in cfg
        assert env.bare.as_uri() in cfg


# --- the guard must survive a live config directory ---------------------------

def test_concurrent_writes_to_existing_files_do_not_trip_the_guard(tmp_path):
    """Antigravity writes into ~/.gemini while the harness runs.

    A content-sensitive fingerprint fails on the developer's IDE rather than on a
    real breach - observed during Slice 0, and it passed on retry, which is worse.
    """
    watched = tmp_path / "gemini"
    (watched / "sessions").mkdir(parents=True)
    log = watched / "sessions" / "current.log"
    log.write_text("start", encoding="utf-8")

    before = e.manifest([watched])
    log.write_text("start" + "x" * 5000, encoding="utf-8")   # IDE appends
    assert not e.diff_manifest(before, e.manifest([watched]))


def test_a_new_entry_still_trips_the_guard(tmp_path):
    watched = tmp_path / "claude"
    (watched / "plugins").mkdir(parents=True)
    before = e.manifest([watched])
    (watched / "plugins" / "stratosphere-os").mkdir()         # an install appearing
    assert e.diff_manifest(before, e.manifest([watched]))


def test_assert_no_install_flags_only_what_appeared(tmp_path):
    home = tmp_path / "home"
    (home / ".claude" / "plugins").mkdir(parents=True)
    pre_existing = home / ".claude" / "plugins" / "stratosphere-os"
    pre_existing.mkdir()

    markers = e.install_markers_present(home)
    e.assert_no_install(home, markers)          # already there before: not a breach

    (home / ".claude" / "skills" / "0a-start-session").mkdir(parents=True)
    with pytest.raises(RuntimeError) as exc:
        e.assert_no_install(home, markers)
    assert "0a-start-session" in str(exc.value)
    assert "REAL home" in str(exc.value)
