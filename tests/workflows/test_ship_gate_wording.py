#!/usr/bin/env python3
"""BT-128 guards: workflow wording must agree with what the gates and repo hygiene require.

1. 4a step 6's slice comment must satisfy reconcile.py's PR-link predicate (no second comment).
2. Workflow `--body-file` scratch files live under `.tmp/` and are removed once consumed.
"""
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "src" / "workflows"
spec = importlib.util.spec_from_file_location("reconcile", ROOT / "src" / "scripts" / "reconcile.py")
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)

SAMPLE_URL = "https://github.com/o/r/pull/9"
BODY_FILE = re.compile(r"--body-file\s+(\S+)")


def test_4a_step6_comment_satisfies_reconcile_pr_link():
    text = (WF / "4a-verify-and-ship.md").read_text(encoding="utf-8")
    m = re.search(r'gh issue comment <n> --body "([^"]+)"', text)
    assert m, "4a step 6 has no `gh issue comment <n> --body \"...\"` literal"
    body = m.group(1).replace("<pr-url>", SAMPLE_URL).replace("<pr>", "9")
    drift = rec.compare({}, {"comments": [{"body": body}]}, set(), True)
    assert drift == [], f"step 6 comment {body!r} fails the reconcile PR-link check: {drift}"


def test_4a_documents_pr_body_file_under_tmp():
    text = (WF / "4a-verify-and-ship.md").read_text(encoding="utf-8")
    assert BODY_FILE.search(text), "4a step 5 must pass the PR body via `--body-file`"


def test_body_files_live_in_tmp_and_are_removed():
    for name in ("4a-verify-and-ship.md", "3b-create-issue.md"):
        text = (WF / name).read_text(encoding="utf-8")
        for path in BODY_FILE.findall(text):
            path = path.strip("\"'`")
            assert path.startswith(".tmp/"), f"{name}: --body-file {path} is outside .tmp/"
            assert re.search(rf"rm -f [^\n]*{re.escape(path)}", text), \
                f"{name}: no `rm -f {path}` cleanup"


def test_3b_issue_drafts_scratch_is_removed():
    text = (WF / "3b-create-issue.md").read_text(encoding="utf-8")
    assert re.search(r"rm -f [^\n]*\.tmp/BT-<padded>-issue-drafts\.md", text), \
        "3b never deletes .tmp/BT-<padded>-issue-drafts.md after minting"
