"""Shared pytest configuration for StratosphereOS test suite."""
from pathlib import Path
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
