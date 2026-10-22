# md-crosscheck: stage 0-1 and planning readers (load-memory, 0a, 0b, 1b, 1c, 3a, 3c, 4b, 4c, concept-map-operations, post-merge-sync) vs tracker-verbs.md, ice_read.py and reconcile.py
"""BT-198: in `tracker: github` mode the stage 0-1 and planning readers ask GitHub only what they need; the map is
named only as the local backend, and the 3a/3c/0b gates pass `--expect-file` from their own work file.
"""
import re
import subprocess
import sys

import pytest

from conftest import SRC, read_src

READERS = ["skills/load-memory/SKILL.md", "workflows/0a-start-session.md", "workflows/0b-stop-session.md",
           "workflows/1b-concept-framing.md", "workflows/1c-concept-map.md", "workflows/3a-version-planning.md",
           "workflows/3c-sprint-planning.md", "workflows/4b-audit-architecture-drift.md",
           "workflows/4c-codebase-health-audit.md", "references/concept-map-operations.md",
           "references/post-merge-sync.md"]
NAME_THE_MAP = [r for r in READERS if r != "workflows/0b-stop-session.md"]  # 0b delegates to post-merge-sync
WIP_READERS = ["skills/load-memory/SKILL.md", "workflows/0a-start-session.md", "workflows/4b-audit-architecture-drift.md",
               "workflows/4c-codebase-health-audit.md"]
GATES = ["workflows/3a-version-planning.md", "workflows/3c-sprint-planning.md", "references/post-merge-sync.md"]
GH_WRITE = re.compile(r"gh issue (create|edit|close|comment|reopen)|gh api graphql|addBlockedBy|addSubIssue|removeBlockedBy"
                      r"|--add-label|--remove-label|--milestone|`(set_status|set_milestone|close|create)`")


def _reads_section():
    m = re.search(r"^## Reads\n(.*?)(?=^## |\Z)", read_src("references/tracker-verbs.md"), re.M | re.S)
    assert m, "tracker-verbs.md has no `## Reads` section"
    return m.group(1)


@pytest.mark.parametrize("rel", READERS)
def test_the_map_is_only_named_as_the_local_backend(rel):
    offenders = [l.strip()[:120] for l in read_src(rel).splitlines()
                 if re.search(r"BACKLOG|map row", l) and not re.search(r"local", l, re.I)]
    assert offenders == [], f"{rel} reads or writes the map outside a local clause: {offenders}"


@pytest.mark.parametrize("rel", READERS)
def test_no_sentence_writes_both_github_and_the_map(rel):
    offenders = []
    for line in read_src(rel).splitlines():
        for sentence in re.split(r"(?<=[.;:])\s+", line):
            if "BACKLOG" in sentence and GH_WRITE.search(sentence):
                offenders.append(sentence.strip()[:120])
    assert offenders == [], f"{rel} writes GitHub and the map in one sentence: {offenders}"


@pytest.mark.parametrize("rel", NAME_THE_MAP)
def test_every_reader_keeps_its_local_clause(rel):
    assert "BACKLOG_MAP" in read_src(rel), f"{rel} lost its local-backend clause"


def test_the_reads_reference_defines_the_wip_set_and_the_candidates_read():
    reads = _reads_section()
    assert re.search(r"^- `wip`:.*status:in progress", reads, re.M)
    assert re.search(r"^- `candidates`:.*ice_read\.py candidates", reads, re.M)


@pytest.mark.parametrize("rel", WIP_READERS)
def test_wip_readers_use_a_scoped_query(rel):
    text = read_src(rel)
    assert 'status:in progress' in text and ("gh issue list" in text or "tracker-verbs.md" in text), \
        f"{rel} has no scoped WIP read"


def test_3c_reads_its_candidates_and_ice_from_ice_read():
    text = read_src("workflows/3c-sprint-planning.md")
    assert "ice_read.py candidates" in text
    out = subprocess.run([sys.executable, str(SRC / "scripts" / "ice_read.py"), "--help"], capture_output=True, text=True).stdout
    assert "candidates" in out


@pytest.mark.parametrize("rel", GATES)
def test_gates_pass_expect_file_from_their_work_file(rel):
    text = read_src(rel)
    call = re.search(r"python \.agents/scripts/reconcile\.py ([^`]*--expect-file[^`]*)`", text)
    assert call, f"{rel}: no `reconcile.py ... --expect-file` call"
    assert re.search(r"\.tmp/\w+-expect\.txt", call.group(1)), f"{rel}: --expect-file is not a .tmp work file"
    out = subprocess.run([sys.executable, str(SRC / "scripts" / "reconcile.py"), "--help"], capture_output=True, text=True).stdout
    used = set(re.findall(r"--[a-z-]+", re.sub(r"<[^>]*>", "", call.group(1))))
    assert used <= set(re.findall(r"--[a-z-]+", out)), f"{rel}: {used} not all accepted by reconcile.py"


def test_post_merge_sync_in_github_mode_queries_dependents_by_id_not_all_open():
    text = read_src("references/post-merge-sync.md")
    assert re.search(r"reconcile\.py --ids <[^`]*--edges dependents", text), "no `--ids ... --edges dependents` form"
    assert "--edges dependents --all-open" in text, "the local `--all-open` form must stay"
