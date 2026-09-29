"""build/bump_guard.py must require a version bump for ANY shipped-file change.

It used to watch only src/scripts/scaffold.py, so a change to reconcile.py or
validate_memory.py shipped without a bump, and on Windows it reported a change that
did not exist (git output decoded as cp1252, files read as utf-8, so any non-ASCII
byte in a watched file differed from its own release-tag blob).
"""
import json
import os
import subprocess
import sys

import pytest

from conftest import REPO_ROOT

GUARD = REPO_ROOT / "build" / "bump_guard.py"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t"}


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=ENV)


def write(root, rel, text, encoding="utf-8"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode(encoding))


def set_version(root, v):
    write(root, "build/build.py", f'VERSION = "{v}"\n')


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    write(tmp_path, "dist/antigravity/versions.json", json.dumps({"artifacts": {}}))
    write(tmp_path, "src/scripts/reconcile.py", "# plain\n")
    write(tmp_path, "src/scripts/scaffold.py", "# em dash — non-ascii\n")
    write(tmp_path, "src/scripts/design/test/skip.py", "# tests do not ship\n")
    set_version(tmp_path, "1.0.0")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "release")
    git(tmp_path, "tag", "v1.0.0")
    return tmp_path


def guard(root):
    r = subprocess.run([sys.executable, str(GUARD), str(root)], capture_output=True)
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", errors="replace")


def test_no_change_passes_even_with_non_ascii_files(repo):
    rc, out = guard(repo)
    assert rc == 0 and "no shipped-content change" in out, out


def test_any_shipped_script_change_without_bump_fails(repo):
    write(repo, "src/scripts/reconcile.py", "# changed\n")
    rc, out = guard(repo)
    assert rc == 1 and "src/scripts/reconcile.py" in out, out


def test_change_with_bump_passes(repo):
    write(repo, "src/scripts/reconcile.py", "# changed\n")
    set_version(repo, "1.0.1")
    rc, out = guard(repo)
    assert rc == 0, out


def test_new_untracked_shipped_script_fails(repo):
    write(repo, "src/scripts/new_tool.py", "# new\n")
    rc, out = guard(repo)
    assert rc == 1 and "new_tool.py" in out, out


def test_test_dirs_do_not_ship(repo):
    write(repo, "src/scripts/design/test/skip.py", "# edited test\n")
    rc, out = guard(repo)
    assert rc == 0, out
