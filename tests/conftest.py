"""Shared pytest configuration for StratosphereOS test suite."""
import itertools
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"

# Prime sys.path so tests can import src modules without per-file boilerplate
# when run under pytest. Standalone scripts still keep their own sys.path setup.
for p in [str(REPO_ROOT), str(REPO_ROOT / "tests")]:
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


_GIT_ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}
_commit_seq = itertools.count()


def git(cwd, *args):
    """Run git in `cwd` (raises on failure) and return stripped stdout. Author identity is pinned via env."""
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True,
                          env=_GIT_ENV).stdout.strip()


def commit(repo, subject, files=None):
    """Write+commit `files` (default: one fresh file) with `subject`; return the new HEAD sha."""
    for rel in files or [f"f{next(_commit_seq)}.txt"]:
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(subject + os.urandom(4).hex(), encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", subject)
    return git(repo, "rev-parse", "HEAD")


def read_src(rel):
    """Text of `src/<rel>` (workflow/reference contract tests)."""
    return (SRC / rel).read_text(encoding="utf-8")


def read_repo(rel):
    """Text of `<rel>` relative to the repo root."""
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


_COMBINED_GATE = re.compile(r"python \.agents/scripts/reconcile\.py ([^`]*--with-edges dependents[^`]*)`")


def combined_gate_calls():
    """The `reconcile.py ... --with-edges dependents` argument strings 4a's text carries (one per call)."""
    return _COMBINED_GATE.findall(read_src("workflows/4a-verify-and-ship.md"))


def combined_gate_argv(slice_id, epic_id):
    """argv of 4a's github ship gate read out of the workflow text: optional groups kept, placeholders filled."""
    text = re.sub(r"\[([^\]]*)\]", r"\1", combined_gate_calls()[0])
    text = text.replace("BT-<slice>", slice_id).replace("BT-<epic flipped>", epic_id).replace("BT-<epic>", epic_id)
    return shlex.split(text)


def update_skill_text():
    """stratosphere-update SKILL.md + the `references/update-*.md` it routes to, in citation order.

    The host-specific update paths live in those references, not in SKILL.md; tests that pin their
    text (or that must see the whole update flow) read it through here.
    """
    skill = (REPO_ROOT / "src/commands/stratosphere-update/SKILL.md").read_text(encoding="utf-8")
    cited = dict.fromkeys(re.findall(r"(?<![\w/.])references/(update-[A-Za-z0-9_.-]+\.md)", skill))
    return skill + "".join("\n" + (REPO_ROOT / "src/references" / name).read_text(encoding="utf-8") for name in cited)


def pytest_collection_modifyitems(items):
    """tests/lifecycle guards tests/lifecycle-harness, which neither CI nor check.sh runs (last live L3 run
    2026-09-17); the `integration` marker keeps it out of the default run. `pytest -m integration tests/lifecycle`."""
    for item in items:
        if "tests/lifecycle/" in item.nodeid.replace("\\", "/"):
            item.add_marker(pytest.mark.integration)
