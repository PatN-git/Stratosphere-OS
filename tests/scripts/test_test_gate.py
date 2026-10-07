"""BT-153: `test_gate.py` blocks a commit whose staged code was not in a recorded passing test run.

Seam: the CLI (exit code + output) run inside a throwaway git repo; the hook end to end via `git commit`.
"""
import shutil
import subprocess
import sys

import pytest

from conftest import REPO_ROOT, _GIT_ENV, commit, git

SCRIPT = REPO_ROOT / "src" / "scripts" / "test_gate.py"
PASS = [sys.executable, "-c", "pass"]
FAIL = [sys.executable, "-c", "raise SystemExit(3)"]


def gate(repo, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True,
                          text=True, env=_GIT_ENV)


def write(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-b", "main")
    (tmp_path / ".git" / "info" / "exclude").write_text(".tmp/\n", encoding="utf-8")
    commit(tmp_path, "chore: init", ["README.md", "app.py"])
    return tmp_path


def test_untested_staged_code_blocks_and_a_passing_record_unblocks(repo):
    write(repo, "app.py", "x = 1\n")
    git(repo, "add", "app.py")
    blocked = gate(repo, "check")
    assert blocked.returncode == 1
    assert "app.py" in blocked.stderr and "test_gate.py record --" in blocked.stderr
    assert gate(repo, "record", "--", *PASS).returncode == 0
    assert gate(repo, "check").returncode == 0


def test_an_edit_after_the_record_blocks(repo):
    write(repo, "app.py", "x = 1\n")
    gate(repo, "record", "--", *PASS)
    write(repo, "app.py", "x = 2\n")
    git(repo, "add", "app.py")
    assert gate(repo, "check").returncode == 1


def test_a_failing_run_propagates_its_exit_code_and_records_nothing(repo):
    write(repo, "app.py", "x = 1\n")
    assert gate(repo, "record", "--", *FAIL).returncode == 3
    git(repo, "add", "app.py")
    assert gate(repo, "check").returncode == 1


def test_docs_and_framework_commits_need_no_record(repo):
    write(repo, "README.md", "changed\n")
    write(repo, "docs/guide.txt", "new\n")
    write(repo, ".memory/LEARNINGS.md", "note\n")
    write(repo, ".agents/scripts/reconcile.py", "# refreshed by /stratosphere-update\n")
    write(repo, ".github/workflows/ci.yml", "on: push\n")
    git(repo, "add", "-A")
    assert gate(repo, "check").returncode == 0


def test_a_partial_commit_of_recorded_files_passes(repo):
    write(repo, "app.py", "x = 1\n")
    write(repo, "lib.py", "y = 1\n")
    gate(repo, "record", "--", *PASS)
    git(repo, "add", "app.py")
    assert gate(repo, "check").returncode == 0


def test_a_staged_deletion_passes_only_when_it_was_recorded(repo):
    git(repo, "rm", "-q", "app.py")
    assert gate(repo, "check").returncode == 1
    gate(repo, "record", "--", *PASS)
    assert gate(repo, "check").returncode == 0


def test_works_before_the_first_commit(tmp_path):
    git(tmp_path, "init", "-b", "main")
    (tmp_path / ".git" / "info" / "exclude").write_text(".tmp/\n", encoding="utf-8")
    write(tmp_path, "app.py", "x = 1\n")
    git(tmp_path, "add", "app.py")
    assert gate(tmp_path, "check").returncode == 1
    gate(tmp_path, "record", "--", *PASS)
    assert gate(tmp_path, "check").returncode == 0


def test_install_writes_a_marked_hook_and_status_reports_it(repo):
    assert gate(repo, "status").returncode == 1
    assert gate(repo, "install").returncode == 0
    hook = (repo / ".git" / "hooks" / "pre-commit").read_text(encoding="utf-8")
    assert "stratos-test-gate" in hook and ".agents/scripts/test_gate.py check" in hook
    assert gate(repo, "status").returncode == 0
    assert gate(repo, "install").returncode == 0, "re-install refreshes our own hook"


def test_install_never_touches_a_foreign_hook(repo):
    foreign = repo / ".git" / "hooks" / "pre-commit"
    foreign.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    out = gate(repo, "install")
    assert out.returncode == 1 and "test_gate.py check" in out.stdout + out.stderr
    assert foreign.read_text(encoding="utf-8") == "#!/bin/sh\nexit 0\n"


def test_install_refuses_a_custom_hooks_path(repo):
    git(repo, "config", "core.hooksPath", ".husky")
    out = gate(repo, "install")
    assert out.returncode == 1 and ".husky" in out.stdout + out.stderr
    assert not (repo / ".husky").exists()


def test_the_installed_hook_blocks_git_commit_until_tests_are_recorded(repo):
    scripts = repo / ".agents" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(SCRIPT, scripts / "test_gate.py")
    git(repo, "add", ".agents")
    git(repo, "commit", "-q", "-m", "chore: add gate", "--no-verify")
    assert gate(repo, "install").returncode == 0
    write(repo, "app.py", "x = 1\n")
    git(repo, "add", "app.py")
    refused = subprocess.run(["git", "commit", "-q", "-m", "feat: x"], cwd=repo, capture_output=True,
                             text=True, env=_GIT_ENV)
    assert refused.returncode != 0 and "app.py" in refused.stderr
    gate(repo, "record", "--", *PASS)
    git(repo, "commit", "-q", "-m", "feat: x")
