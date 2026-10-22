# md-crosscheck: tracker-verbs.md and label-taxonomy.md vs the 2a/2b/3b writers, the LEARNINGS template and the BACKLOG_MAP template
"""BT-196: the single write surface (tracker verbs) and the label taxonomy moved out of the map.

`references/tracker-verbs.md` states each write kind once with a GitHub form and a local form; the spec-phase
writers (2a, 2b, 3b) state a write once, as a verb, and mention the map only as the local backend.
"""
import re

import pytest

from conftest import read_src

VERBS = ["create", "set_status", "set_labels", "ensure_label", "set_milestone", "ensure_milestone", "close_milestone",
         "set_parent", "add_blocker", "clear_blocker", "close", "reopen", "comment", "set_refs", "set_ice", "set_body", "claim"]
MISFITS = ["set_ice", "set_refs", "set_body", "claim", "close"]
WRITERS = ["workflows/2a-write-prd.md", "workflows/2b-interface-design.md", "workflows/3b-create-issue.md"]
GH_WRITE = re.compile(r"gh issue (create|edit|close|comment|reopen)|gh api graphql|addBlockedBy|addSubIssue|removeBlockedBy"
                      r"|--add-label|--remove-label|--milestone")


def _section(text, heading):
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, f"no `## {heading}` section"
    return m.group(1)


def _verb_rows():
    rows = {}
    for line in _section(read_src("references/tracker-verbs.md"), "Verbs").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        m = re.fullmatch(r"`(\w+)`", cells[0]) if len(cells) == 3 else None
        if m:
            rows[m.group(1)] = cells[1:]
    return rows


def test_every_write_kind_has_a_github_form_and_a_local_form():
    rows = _verb_rows()
    assert [v for v in VERBS if v not in rows] == [], "verbs missing from the table"
    empty = [v for v, cells in rows.items() if not all(c and c != "—" for c in cells)]
    assert empty == [], f"verbs without both forms: {empty}"


def test_the_misfits_are_named_and_pull_requests_are_not_a_tracker_verb():
    misfits = _section(read_src("references/tracker-verbs.md"), "Misfits")
    for verb in MISFITS:
        assert f"`{verb}`" in misfits, f"misfit {verb} not named"
    assert re.search(r"pull request|PR operations", misfits, re.I) and "not a tracker verb" in misfits


def test_the_runtime_halt_rule_lives_in_the_verbs_reference():
    text = _section(read_src("references/tracker-verbs.md"), "Runtime rule")
    assert re.search(r"never write a local copy", text, re.I)
    assert "retried 3 times" in text and "halt" in text


@pytest.mark.parametrize("rel", WRITERS)
def test_no_sentence_writes_both_github_and_the_map(rel):
    offenders = []
    for line in read_src(rel).splitlines():
        for sentence in re.split(r"(?<=[.;:])\s+", line):
            if "BACKLOG" in sentence and GH_WRITE.search(sentence):
                offenders.append(sentence.strip()[:120])
    assert offenders == [], f"{rel} writes GitHub and the map in one sentence: {offenders}"


@pytest.mark.parametrize("rel", WRITERS)
def test_the_map_is_only_named_as_the_local_backend(rel):
    offenders = [l.strip()[:120] for l in read_src(rel).splitlines() if "BACKLOG" in l and not re.search(r"local", l, re.I)]
    assert offenders == [], f"{rel} mentions the map without saying it is the local backend: {offenders}"


@pytest.mark.parametrize("rel", WRITERS)
def test_writers_cite_the_verbs_reference(rel):
    assert "references/tracker-verbs.md" in read_src(rel)


def test_there_is_no_provisional_milestone_outside_the_local_backend():
    for rel in WRITERS[:2]:
        for line in read_src(rel).splitlines():
            if re.search(r"provisional|default `v1\.0\.0`|v1\.0\.0", line):
                assert re.search(r"local", line, re.I), f"{rel}: provisional milestone outside a local clause: {line.strip()[:120]}"


def test_refs_move_to_the_issue_body_in_github_mode():
    text = read_src("references/tracker-verbs.md")
    row = _verb_rows()["set_refs"]
    assert "Refs:" in row[0] and "Ref" in row[1]
    for rel in WRITERS:
        assert "set_refs" in read_src(rel)
    assert "Refs:" in text


def test_label_taxonomy_is_the_home_of_the_map_rules():
    text = read_src("references/label-taxonomy.md")
    for needle in ("Label Composition Rules", "lifecycle order", "Milestone", "Concept Exemptions", "`concept:map`",
                   "Label source of truth", "Single Status Invariant", "`status:needs_spec`", "`mode:AFK`"):
        assert needle in text, f"label-taxonomy.md lacks {needle}"


def test_the_learnings_todo_sink_points_to_the_tracker():
    line = next(l for l in read_src("memory-templates/LEARNINGS.md").splitlines() if l.startswith("- Temporary TODOs"))
    assert "BACKLOG_MAP" not in line and "tracker" in line


def test_the_relations_and_template_references_cite_the_new_references():
    assert "references/tracker-verbs.md" in read_src("references/github-issue-relations.md")
    assert "references/label-taxonomy.md" in read_src("references/issue-templates.md")
