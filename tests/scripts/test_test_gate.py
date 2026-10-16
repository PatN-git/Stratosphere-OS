"""BT-153: `test_gate.py` blocks a commit whose staged code was not in a recorded passing test run.

Seam: the CLI (exit code + output) run inside a throwaway git repo; the hook end to end via `git commit`.
"""
import json
import os
import shutil
import subprocess
import sys
import textwrap

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


# --- BT-183: the hook hint and `record --suite` (the one deterministic writer of the suite record) -------------

PYTEST_FULL = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]


def suite_repo(repo, hook="pass"):
    """A committed, clean repo whose whole-suite command is real pytest; `hook` runs in pytest_terminal_summary."""
    write(repo, "test_ok.py", "def test_ok():\n    pass\n")
    write(repo, "conftest.py", "import os\nimport subprocess\n\n\ndef pytest_terminal_summary(terminalreporter):\n"
          + textwrap.indent(textwrap.dedent(hook).strip(), "    ") + "\n")
    (repo / ".git" / "info" / "exclude").write_text(".tmp/\n__pycache__/\n.pytest_cache/\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "chore: tests")


MARK_RAN = 'os.makedirs(".tmp", exist_ok=True)\nopen(os.path.join(".tmp", "ran"), "w").close()'


def suite_record(repo, issue="BT-182"):
    return repo / ".tmp" / f"3d-suite-{issue}.json"


def test_the_block_message_names_the_related_tests_path(repo):
    write(repo, "app.py", "x = 1\n")
    git(repo, "add", "app.py")
    blocked = gate(repo, "check")
    assert blocked.returncode == 1
    assert "related tests" in blocked.stderr and "full suite" in blocked.stderr
    assert "test_gate.py record --" in blocked.stderr


def test_record_suite_writes_three_keys_only_on_a_pass_and_a_clean_tree(repo):
    suite_repo(repo)
    r = gate(repo, "record", "--suite", "BT-182", "--", *PYTEST_FULL)
    assert r.returncode == 0, r.stdout + r.stderr
    rec = json.loads(suite_record(repo).read_text(encoding="utf-8"))
    assert set(rec) == {"head_sha", "cmd", "observed"}
    assert rec["head_sha"] == git(repo, "rev-parse", "HEAD")
    assert "pytest" in rec["cmd"] and "1 passed" in rec["observed"]
    assert (repo / ".tmp" / "test-gate.json").is_file()


def test_record_suite_with_a_failing_run_writes_nothing(repo):
    suite_repo(repo)
    write(repo, "test_ok.py", "def test_ok():\n    assert False\n")
    git(repo, "commit", "-q", "-am", "chore: red")
    r = gate(repo, "record", "--suite", "BT-182", "--", *PYTEST_FULL)
    assert r.returncode == 1 and not suite_record(repo).exists()


def test_record_suite_refuses_a_dirty_tree_before_running(repo):
    suite_repo(repo, MARK_RAN)
    write(repo, "generated.txt", "x")
    r = gate(repo, "record", "--suite", "BT-182", "--", *PYTEST_FULL)
    assert r.returncode == 2 and "commit" in r.stderr.lower()
    assert not (repo / ".tmp" / "ran").exists() and not suite_record(repo).exists()


def test_record_suite_refuses_a_scoped_command_without_running_it(repo):
    suite_repo(repo, MARK_RAN)
    r = gate(repo, "record", "--suite", "BT-182", "--", sys.executable, "-m", "pytest", "test_ok.py")
    assert r.returncode == 2 and "scoped" in r.stderr
    assert not (repo / ".tmp" / "ran").exists() and not suite_record(repo).exists()


def test_record_suite_writes_nothing_when_head_moves_during_the_run(repo):
    suite_repo(repo, 'subprocess.run(["git", "commit", "--allow-empty", "-q", "-m", "moved"], check=True)')
    r = gate(repo, "record", "--suite", "BT-182", "--", *PYTEST_FULL)
    assert r.returncode == 3 and not suite_record(repo).exists()
    assert (repo / ".tmp" / "test-gate.json").is_file()  # the tests did pass, so the commit gate still has its record


def test_record_suite_writes_nothing_when_the_run_leaves_the_tree_dirty(repo):
    suite_repo(repo, 'open("generated.txt", "w").write("x")')
    r = gate(repo, "record", "--suite", "BT-182", "--", *PYTEST_FULL)
    assert r.returncode == 3 and not suite_record(repo).exists()


def test_record_suite_observed_keeps_every_count_and_drops_colour_codes(repo):
    suite_repo(repo, r'os.write(1, "\x1b[32m5 passed\x1b[0m in 0.1s\ninstall-harness L1: 155 passed, 0 failed\nALL CHECKS PASSED\n".encode())')
    assert gate(repo, "record", "--suite", "BT-182", "--", *PYTEST_FULL).returncode == 0
    observed = json.loads(suite_record(repo).read_text(encoding="utf-8"))["observed"]
    assert "5 passed" in observed and "155 passed" in observed and "\x1b" not in observed and len(observed) <= 400


def test_record_suite_survives_a_cp1252_piped_stdout(repo):
    suite_repo(repo, r'os.write(1, "\u2713 vitest checkmark\n".encode("utf-8"))')
    env = {**_GIT_ENV, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    r = subprocess.run([sys.executable, str(SCRIPT), "record", "--suite", "BT-182", "--", *PYTEST_FULL],
                       cwd=repo, capture_output=True, env=env)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    assert "✓".encode("utf-8") in r.stdout and b"UnicodeEncodeError" not in r.stderr
    assert suite_record(repo).is_file()


def test_record_suite_pads_the_issue_number_to_three_digits(repo):
    suite_repo(repo)
    assert gate(repo, "record", "--suite", "BT-7", "--", *PYTEST_FULL).returncode == 0
    assert suite_record(repo, "BT-007").is_file()


def test_record_suite_needs_an_issue_id(repo):
    suite_repo(repo)
    assert gate(repo, "record", "--suite", "oops", "--", *PYTEST_FULL).returncode != 0
