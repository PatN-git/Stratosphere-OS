#!/usr/bin/env python3
# md-crosscheck: Stage 4 workflow integration and cryptographic test gate verification (BT-228)
"""Tests for cryptographic test gate verification on committed trees and Stage 4 workflow hardening (BT-228 / Epic BT-223)."""
import os
import sys
import subprocess
from pathlib import Path
import pytest
from conftest import REPO_ROOT, SRC, read_src

sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
import _versioning

SCRIPT = REPO_ROOT / "src" / "scripts" / "test_gate.py"
PASS = [sys.executable, "-c", "import sys; sys.exit(0)"]
FAIL = [sys.executable, "-c", "import sys; sys.exit(1)"]
PYTEST_FULL = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
PYTEST_SCOPED = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_ok.py"]

_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Test Author",
    "GIT_AUTHOR_EMAIL": "author@example.com",
    "GIT_COMMITTER_NAME": "Test Committer",
    "GIT_COMMITTER_EMAIL": "committer@example.com",
}


def git(cwd, *args, check=True):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          env=_GIT_ENV, check=check)


def gate(cwd, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd,
                          capture_output=True, text=True, env=_GIT_ENV)


def write(cwd, rel, text):
    path = cwd / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    d = tmp_path / "repo"
    d.mkdir()
    git(d, "init", "-b", "main")
    write(d, ".git/info/exclude", ".tmp/\n__pycache__/\n.pytest_cache/\n")
    write(d, "README.md", "# Fixture\n")
    write(d, "app.py", "x = 1\n")
    write(d, "test_ok.py", "def test_ok():\n    pass\n")
    git(d, "add", "-A")
    git(d, "commit", "-m", "init")
    return d


def test_verify_clean_match_returns_zero(repo):
    write(repo, "app.py", "x = 2\n")
    res_rec = gate(repo, "record", "--", *PASS)
    assert res_rec.returncode == 0, res_rec.stderr
    git(repo, "add", "app.py")
    git(repo, "commit", "-m", "feat: update app")
    res = gate(repo, "verify", "--base", "HEAD~1")
    assert res.returncode == 0, res.stderr
    assert "verified 1 file(s) against recorded passing test run" in res.stdout


def test_verify_unrecorded_committed_file_returns_one(repo):
    write(repo, "feature.py", "def run(): pass\n")
    git(repo, "add", "feature.py")
    git(repo, "commit", "-m", "feat: unrecorded commit")
    res = gate(repo, "verify", "--base", "HEAD~1")
    assert res.returncode == 1
    assert "verification failed" in res.stderr
    assert "feature.py" in res.stderr


def test_verify_modified_committed_file_with_outdated_record_returns_one(repo):
    write(repo, "app.py", "x = 100\n")
    assert gate(repo, "record", "--", *PASS).returncode == 0
    # Edit after record
    write(repo, "app.py", "x = 200\n")
    git(repo, "add", "app.py")
    git(repo, "commit", "-m", "feat: modified after record")
    res = gate(repo, "verify", "--base", "HEAD~1")
    assert res.returncode == 1
    assert "verification failed" in res.stderr
    assert "app.py" in res.stderr


def test_verify_ungated_files_ignored(repo):
    write(repo, "docs/guide.md", "# Guide\n")
    write(repo, "README.md", "# Updated Readme\n")
    write(repo, ".memory/ARCHITECTURE.md", "# Architecture\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "docs: update ungated files")
    res = gate(repo, "verify", "--base", "HEAD~1")
    assert res.returncode == 0, res.stderr
    assert "verified 0 file(s) against recorded passing test run" in res.stdout


def test_verify_deleted_file_handling(repo):
    write(repo, "lib.py", "y = 1\n")
    assert gate(repo, "record", "--", *PASS).returncode == 0
    git(repo, "add", "lib.py")
    git(repo, "commit", "-m", "feat: add lib")

    os.remove(repo / "lib.py")
    assert gate(repo, "record", "--", *PASS).returncode == 0
    git(repo, "add", "lib.py")
    git(repo, "commit", "-m", "feat: remove lib")
    res = gate(repo, "verify", "--base", "HEAD~1")
    assert res.returncode == 0, res.stderr
    assert "verified 1 file(s) against recorded passing test run" in res.stdout


def test_verify_empty_repo_returns_zero(tmp_path):
    empty_repo = tmp_path / "empty_repo"
    empty_repo.mkdir()
    subprocess.run(["git", "init"], cwd=empty_repo, capture_output=True, check=True)
    res = subprocess.run([sys.executable, str(SCRIPT), "verify"], cwd=empty_repo, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert "verified 0 file(s) against recorded passing test run" in res.stdout


def test_verify_default_base_resolution(repo):
    write(repo, "app.py", "x = 42\n")
    assert gate(repo, "record", "--", *PASS).returncode == 0
    git(repo, "add", "app.py")
    git(repo, "commit", "-m", "feat: default base test")
    res = gate(repo, "verify")
    assert res.returncode == 0, res.stderr
    assert "verified 1 file(s) against recorded passing test run" in res.stdout


def test_record_suite_records_committed_files_for_verify(repo):
    import json

    git(repo, "checkout", "-b", "parent")
    write(repo, "parent.py", "p = 1\n")
    write(repo, "docs/note.md", "# ignored\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "feat: parent commit")

    git(repo, "checkout", "-b", "child")
    write(repo, "child.py", "c = 2\n")
    git(repo, "add", "child.py")
    git(repo, "commit", "-m", "feat: child commit")

    # Fresh worktree / prior session: no .tmp/test-gate.json yet
    rec_path = repo / ".tmp" / "test-gate.json"
    assert not rec_path.exists()

    res_suite = gate(repo, "record", "--suite", "BT-286", "--", *PYTEST_FULL)
    assert res_suite.returncode == 0, res_suite.stdout + res_suite.stderr

    data = json.loads(rec_path.read_text(encoding="utf-8"))
    assert "parent.py" in data["files"]
    assert "child.py" in data["files"]
    assert "docs/note.md" not in data["files"]

    for args in (("verify",), ("verify", "--base", "main"), ("verify", "--base", "parent")):
        res = gate(repo, *args)
        assert res.returncode == 0, f"{args}: {res.stderr}"


def test_record_suite_with_explicit_base_and_deleted_files(repo):
    import json

    write(repo, "doomed.py", "d = 1\n")
    git(repo, "add", "doomed.py")
    git(repo, "commit", "-m", "feat: add doomed")

    git(repo, "checkout", "-b", "feature")
    git(repo, "rm", "-q", "doomed.py")
    git(repo, "commit", "-m", "feat: delete doomed")

    res_suite = gate(repo, "record", "--suite", "BT-286", "--base", "main", "--", *PYTEST_FULL)
    assert res_suite.returncode == 0, res_suite.stdout + res_suite.stderr

    data = json.loads((repo / ".tmp" / "test-gate.json").read_text(encoding="utf-8"))
    assert data["files"]["doomed.py"] is None

    res = gate(repo, "verify", "--base", "main")
    assert res.returncode == 0, res.stderr
    assert "verified 1 file(s)" in res.stdout


def test_record_suite_subsequent_unrecorded_commit_fails_verify(repo):
    git(repo, "checkout", "-b", "feature")
    write(repo, "app.py", "x = 10\n")
    git(repo, "add", "app.py")
    git(repo, "commit", "-m", "feat: first commit")

    assert gate(repo, "record", "--suite", "BT-286", "--", *PYTEST_FULL).returncode == 0
    assert gate(repo, "verify").returncode == 0

    write(repo, "app.py", "x = 20\n")
    write(repo, "new_file.py", "n = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "feat: unrecorded follow-up")

    res = gate(repo, "verify")
    assert res.returncode == 1
    assert "app.py" in res.stderr
    assert "new_file.py" in res.stderr


def test_record_slice_does_not_backfill_prior_commits(repo):
    git(repo, "checkout", "-b", "feature")
    write(repo, "prior.py", "p = 1\n")
    git(repo, "add", "prior.py")
    git(repo, "commit", "-m", "feat: prior unrecorded commit")

    write(repo, "slice_file.py", "s = 1\n")
    assert gate(repo, "record", "--", *PASS).returncode == 0
    git(repo, "add", "slice_file.py")
    git(repo, "commit", "-m", "feat: slice commit")

    res_slice = gate(repo, "record", "--slice", "BT-286", "--", *PYTEST_SCOPED)
    assert res_slice.returncode == 0, res_slice.stdout + res_slice.stderr

    res = gate(repo, "verify")
    assert res.returncode == 1
    assert "prior.py" in res.stderr
    assert "<unrecorded>" in res.stderr


def test_4a_workflow_semantic_ac_mapping_and_verify_gate():
    text = read_src("workflows/4a-verify-and-ship.md")
    assert "test_gate.py verify --base <base>" in text
    assert "Map each Acceptance Criterion semantically to its test function name/identifier" in text
    assert "never cite fragile source line numbers or hallucinate line references" in text
    assert "Anti-Hallucination Invariant" in text
    assert "Reject line number hallucination" in text


def test_4a_workflow_stacked_pr_base_resolution():
    text = read_src("workflows/4a-verify-and-ship.md")
    phase2 = text.split("## Phase 2:", 1)[1].split("## Phase 3:", 1)[0]
    assert "baseRefName" in phase2 and "stacked" in phase2.lower()
    assert phase2.index("baseRefName") < phase2.index("merge-base HEAD origin/<default>")
    phase5 = text.split("## Phase 5:", 1)[1]
    assert "test_gate.py verify --base <base>" in phase5
    assert "[--base <base>]" in phase5 and "pr_body.py build" in phase5


def test_4b_workflow_negative_invariants_anchoring():
    text = read_src("workflows/4b-audit-architecture-drift.md")
    assert ".memory/ARCHITECTURE.md" in text
    assert "Never:" in text
    assert "[LAW]" in text
    assert "Avoid:" in text


def test_4c_workflow_decomposed_audit_passes():
    text = read_src("workflows/4c-codebase-health-audit.md")
    assert "Security Auditor" in text
    assert "Reliability Auditor" in text
    assert "Maintainability Auditor" in text
    assert "Architecture Auditor" in text
    assert "zero-bleed" in text.lower() or "context bleed" in text.lower()


def test_stage4_frontmatter_version_bumps():
    for rel_path, expected_v in [
        ("workflows/4a-verify-and-ship.md", "1.14.0"),
        ("workflows/4b-audit-architecture-drift.md", "1.5.1"),
        ("workflows/4c-codebase-health-audit.md", "1.6.1"),
    ]:
        content = read_src(rel_path)
        v, _ = _versioning.read_version(content, rel_path)
        assert v == expected_v, f"{rel_path} version mismatch: expected {expected_v}, got {v}"


if __name__ == "__main__":
    pytest.main([__file__])
