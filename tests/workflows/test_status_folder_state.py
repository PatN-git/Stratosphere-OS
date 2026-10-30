#!/usr/bin/env python3
# md-crosscheck: STATUS writers/readers (0a, 0b, 3d, 3z, load-memory, setup) vs the STATUS template and tracker-verbs.md
"""BT-218: STATUS.md holds folder state only. Per-task progress and the next step are a resume note on the issue
(`<!-- stratos:resume -->`, `comment` verb, read back with `resume_note`); STATUS keeps `Last Sync`, one session
line per task in the folder (`BT-n · branch · date`), repo notes and a blocker. 0a resolves the branch from the
chosen task, never from STATUS."""
import re

import pytest

from conftest import SRC, read_src

OLD_FIELDS = ["Current Branch", "Active Issue", "Current Focus", "Completed This Session",
              "Open/Active Task Brief", "Next Immediate Step"]
WRITERS = ["workflows/0a-start-session.md", "workflows/0b-stop-session.md", "workflows/3d-implement-issue.md",
           "workflows/3z-afk-loop.md", "skills/load-memory/SKILL.md", "commands/stratosphere-setup/SKILL.md"]


def _status_lines(rel):
    return [l for l in read_src(rel).splitlines() if "STATUS" in l]


def test_template_holds_folder_state_only():
    body = read_src("memory-templates/STATUS.md")
    for field in ("Last Sync", "Sessions", "Repo notes", "Blocker"):
        assert f"**{field}" in body, field
    assert "BT-n · branch · date" in body
    for old in OLD_FIELDS:
        assert old not in body, f"template still has `{old}`"


@pytest.mark.parametrize("rel", WRITERS)
def test_no_writer_names_a_retired_status_field(rel):
    offenders = [l.strip()[:140] for l in _status_lines(rel)
                 if any(f in l for f in OLD_FIELDS + ["Active issue"])]
    assert offenders == [], f"{rel}: {offenders}"


@pytest.mark.parametrize("rel", ["workflows/0a-start-session.md", "workflows/3d-implement-issue.md",
                                 "workflows/3z-afk-loop.md"])
def test_writers_upsert_their_own_session_line(rel):
    text = read_src(rel)
    assert "session line" in text, rel
    assert not re.search(r"Update `\.memory/STATUS\.md`", text), f"{rel} still rewrites STATUS fields"


def test_0a_resolves_the_branch_from_the_task_not_status():
    text = read_src("workflows/0a-start-session.md")
    assert "[DIRTY-TREE]" in text
    assert "--untracked-files=no" in text
    assert "pr_body.py unit" in text and "branch_ok" in text
    assert "STATUS `Current Branch`" not in text and "read STATUS" not in text


def test_0a_session_line_conflict_uses_the_wip_set_not_a_date():
    text = read_src("workflows/0a-start-session.md")
    assert "wip" in text.split("## Phase B", 1)[1], "branch-in-use check should use Phase A's wip set"


def test_3d_leaves_status_to_the_orchestrator_under_3z():
    line = next(l for l in read_src("workflows/3d-implement-issue.md").splitlines() if "session line" in l)
    assert "3z" in line


def test_3z_upserts_after_dispatch_from_the_returned_branch():
    text = read_src("workflows/3z-afk-loop.md")
    assert re.search(r"session line.*`branch`|`branch`.*session line", text), "3z must use the JSON branch"
    assert "subagent" in text.split("Step 2A.2", 1)[-1] or "not `.memory/STATUS.md`" in text


def test_0b_writes_the_resume_note_and_prunes_by_the_stale_rule():
    text = read_src("workflows/0b-stop-session.md")
    assert "stratos:resume" in text and "`comment`" in text
    assert "14 days" in text and "`wip`" in text
    assert "the resume note allows resuming" in text
    assert "STATUS.md` allows resuming" not in text


def test_load_memory_reads_the_resume_note():
    text = read_src("skills/load-memory/SKILL.md")
    assert "`resume_note`" in text and "stratos:resume" in text


def test_tracker_verbs_defines_the_resume_note_for_both_backends():
    text = read_src("references/tracker-verbs.md")
    assert "<!-- stratos:resume -->" in text
    reads = re.search(r"^## Reads\n(.*?)(?=^## |\Z)", text, re.M | re.S).group(1)
    line = next(l for l in reads.splitlines() if l.startswith("- `resume_note`"))
    assert "gh issue view" in line and "--json comments" in line and "startswith" in line
    assert ".memory/resume/" in line
    assert "gh api" not in line, "the REST form returns only the first 30 comments"
    comment = next(l for l in text.splitlines() if l.startswith("| `comment`"))
    assert ".memory/resume/" in comment and "--body-file" in comment


def test_no_template_or_reference_routes_task_status_to_status_md():
    assert "Current task status → `STATUS.md`" not in read_src("memory-templates/LEARNINGS.md")
    assert "Issue / `STATUS.md`" not in read_src("references/environment-fix-ladder.md")


def test_load_memory_carries_the_same_resume_note_query_as_tracker_verbs():
    """A skill cannot cite references (it ships alone), so the query is inline there and must not drift."""
    jq = re.compile(r"--jq '([^']+)'")
    verbs = next(l for l in read_src("references/tracker-verbs.md").splitlines() if l.startswith("- `resume_note`"))
    skill = next(l for l in read_src("skills/load-memory/SKILL.md").splitlines() if "`resume_note`" in l)
    assert jq.search(verbs).group(1) == jq.search(skill).group(1)
