"""Shared pytest configuration for StratosphereOS test suite."""
import itertools
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

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


def update_skill_text():
    """stratosphere-update SKILL.md + the `references/update-*.md` it routes to, in citation order.

    The host-specific update paths live in those references, not in SKILL.md; tests that pin their
    text (or that must see the whole update flow) read it through here.
    """
    skill = (REPO_ROOT / "src/commands/stratosphere-update/SKILL.md").read_text(encoding="utf-8")
    cited = dict.fromkeys(re.findall(r"(?<![\w/.])references/(update-[A-Za-z0-9_.-]+\.md)", skill))
    return skill + "".join("\n" + (REPO_ROOT / "src/references" / name).read_text(encoding="utf-8") for name in cited)
