#!/usr/bin/env python3
"""BT-214: `Check: <path>` bindings on [LAW] entries are validated against `git ls-files` (error), never against the disk.

Seam: validate_memory.py CLI in a throwaway repo. Exit 0 clean, 1 error, 2 warning only.
"""
import subprocess
import sys

from conftest import REPO_ROOT, git

SCRIPT = REPO_ROOT / "src" / "scripts" / "validate_memory.py"
CHECK = "tests/standards/size.test.js"

HEAD = """---
type: architecture
title: Architecture
description: Test fixture.
generated:
  by: test
  at: 2026-10-22
version: "1.0.0"
---
# ARCHITECTURE

## Structural Rules
"""


def _arch(*lines, superseded=""):
    return HEAD + "".join(f"- {l}\n" for l in lines) + "\n## Superseded\n" + superseded


def _rule(n, tail=""):
    return f"**[[A-{n:03d}]] [LAW]** Keep files under 400 lines.{tail}"


def _run(tmp_path, arch, tracked=(CHECK,), with_git=True):
    if with_git:
        git(tmp_path, "init", "-b", "main")
    (tmp_path / ".memory").mkdir()
    (tmp_path / ".memory" / "ARCHITECTURE.md").write_text(arch, encoding="utf-8")
    for rel in tracked:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("// check\n", encoding="utf-8")
    if with_git:
        git(tmp_path, "add", "-A")
        git(tmp_path, "commit", "-m", "chore: base")
    r = subprocess.run([sys.executable, str(SCRIPT), "--path", ".memory"], cwd=tmp_path, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def test_a_tracked_check_path_passes(tmp_path):
    code, out = _run(tmp_path, _arch(_rule(1, f" Check: {CHECK} (tolerance 10%)")))
    assert code == 0, out


def test_an_untracked_or_missing_check_path_is_an_error(tmp_path):
    code, out = _run(tmp_path, _arch(_rule(1, " Check: tests/standards/gone.test.js")))
    assert code == 1, out
    assert "Check binding" in out and "A-001" in out and "tests/standards/gone.test.js" in out


def test_a_file_on_disk_but_not_tracked_is_an_error(tmp_path):
    code, out = _run(tmp_path, _arch(_rule(1, " Check: tests/standards/new.test.js")))
    (tmp_path / "tests/standards/new.test.js").write_text("// untracked\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), "--path", ".memory"], cwd=tmp_path, capture_output=True)
    assert r.returncode == 1, r.stdout.decode("utf-8", "replace")


def test_a_directory_prefix_matches_any_tracked_file_below_it(tmp_path):
    code, out = _run(tmp_path, _arch(_rule(1, " Check: tests/standards/")))
    assert code == 0, out


def test_backslashes_and_a_leading_dot_slash_are_normalised(tmp_path):
    code, out = _run(tmp_path, _arch(_rule(1, " Check: .\\tests\\standards\\size.test.js")))
    assert code == 0, out


def test_a_path_that_leaves_the_repo_is_an_error(tmp_path):
    code, out = _run(tmp_path, _arch(_rule(1, " Check: ../outside.test.js")))
    assert code == 1 and "Check binding" in out, out


def test_an_entry_without_check_is_untouched(tmp_path):
    code, out = _run(tmp_path, _arch(_rule(1), _rule(2)))
    assert code == 0, out


def test_a_superseded_entry_is_not_checked(tmp_path):
    old = "- **[[A-002]] [SUPERSEDED BY [[A-001]]] [2026-10-22]** Old. Check: tests/standards/gone.test.js\n"
    code, out = _run(tmp_path, _arch(_rule(1), superseded=old))
    assert "Check binding" not in out, out


def test_without_git_a_binding_only_warns_and_no_binding_stays_silent(tmp_path):
    code, out = _run(tmp_path, _arch(_rule(1, f" Check: {CHECK}")), with_git=False)
    assert code == 2 and "could not verify Check bindings" in out and "[ERROR]" not in out, out
    plain = tmp_path / "plain"
    plain.mkdir()
    code, out = _run(plain, _arch(_rule(1)), with_git=False)
    assert code == 0 and "could not verify" not in out, out
