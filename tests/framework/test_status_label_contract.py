# md-crosscheck: label contract vs template registry and board sync
"""The status:* labels are an integration contract with the Projects board sync Action.

Renaming a label makes the Action skip the board update with only a log warning, so the
vocabulary is pinned in three places that must agree: references/label-taxonomy.md,
docs/status-label-contract.md, and (byte-for-byte) the workflow installed in this repo.
See docs/status-label-contract.md before changing any of them.
"""
import re

from conftest import REPO_ROOT

CONTRACT = REPO_ROOT / "docs" / "status-label-contract.md"
TAXONOMY = REPO_ROOT / "src" / "references" / "label-taxonomy.md"
ACTION_SRC = REPO_ROOT / "src" / "github" / "sync-labels-to-project.yml"
ACTION_DEV = REPO_ROOT / ".github" / "workflows" / "sync-labels-to-project.yml"

HINT = " -- status:* labels are a board integration contract; update docs/status-label-contract.md, the taxonomy and the board together"


def _statuses(path):
    line = next(l for l in path.read_text(encoding="utf-8").splitlines()
                if l.startswith("- **Status (`status:xxx`)**"))
    return re.findall(r"`status:([^`]+)`", line.split("(lifecycle order")[0].split("**:", 1)[1])


def _contract_statuses():
    return re.findall(r"^\| `status:([^`]+)` \| `([^`]+)` \|$", CONTRACT.read_text(encoding="utf-8"), re.M)


def test_contract_matches_the_label_taxonomy():
    rows = _contract_statuses()
    assert [s for s, _ in rows] == _statuses(TAXONOMY), "contract table vs references/label-taxonomy.md" + HINT


def test_board_option_is_the_label_value():
    for status, option in _contract_statuses():
        assert option == status, f"status:{status} must map to a board option of the same name" + HINT


def test_dev_workflow_is_the_shipped_template():
    assert ACTION_DEV.read_bytes() == ACTION_SRC.read_bytes(), (
        ".github/workflows/sync-labels-to-project.yml drifted from src/github/ -- copy the template, don't fork it")
