# md-crosscheck: tracker-verbs.md and label-taxonomy.md vs issues.py (CLI and CANONICAL), the 2a/2b/3b writers and the LEARNINGS template
"""BT-196, BT-221: the single write surface (tracker verbs) and the label taxonomy.

`references/tracker-verbs.md` states each write kind once with a GitHub form and a local form; the local form is one
`issues.py` command over the `<repo>/issues` tracker branch. The spec-phase writers (2a, 2b, 3b) state a write once,
as a verb.
"""
import re
import shlex
import sys

import pytest

from conftest import SRC, read_src

sys.path.insert(0, str(SRC / "scripts"))
import issues

VERBS = ["create", "set_status", "set_labels", "ensure_label", "set_milestone", "ensure_milestone", "close_milestone",
         "set_parent", "add_blocker", "clear_blocker", "close", "reopen", "comment", "set_refs", "set_ice", "set_body", "claim",
         "apply_moves"]
LOCAL_COMMAND = {"create": "create", "set_status": "set", "set_labels": "set", "set_milestone": "set", "set_parent": "set",
                 "add_blocker": "set", "clear_blocker": "set", "set_body": "set", "ensure_label": "label", "close": "close",
                 "reopen": "reopen", "comment": "comment", "claim": "claim", "apply_moves": "apply-moves"}
MISFITS = ["tracker_switch"]
GONE_MISFITS = ["set_ice", "set_body", "claim", "set_refs", "close"]
WRITERS = ["workflows/2a-write-prd.md", "workflows/2b-interface-design.md", "workflows/3b-create-issue.md"]


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


@pytest.mark.parametrize("verb", sorted(LOCAL_COMMAND))
def test_each_local_write_is_one_issues_py_command(verb):
    local = _verb_rows()[verb][1]
    assert f"issues.py {LOCAL_COMMAND[verb]}" in local, f"{verb}: {local}"
    assert "BACKLOG" not in local and "cell" not in local.lower() and "row" not in local.lower(), local


def test_every_issues_py_invocation_in_the_verbs_reference_parses():
    """The reference spells commands the script accepts: placeholders become a value, `[…]` optional parts stay."""
    spans = re.findall(r"`(?:python \.agents/scripts/)?issues\.py ([^`]+)`", read_src("references/tracker-verbs.md"))
    assert len(spans) >= 10, spans
    for span in spans:
        argv = shlex.split(re.sub(r"<[^>]*>", "x", span).replace("[", "").replace("]", "").replace("…", ""))
        try:
            issues.parser().parse_args(argv)
        except SystemExit:
            pytest.fail(f"`issues.py {span}` is not accepted by issues.py")


def test_the_misfits_are_named_and_pull_requests_are_not_a_tracker_verb():
    misfits = _section(read_src("references/tracker-verbs.md"), "Misfits")
    for verb in MISFITS:
        assert f"`{verb}`" in misfits, f"misfit {verb} not named"
    for verb in GONE_MISFITS:
        assert f"`{verb}`" not in misfits, f"{verb} is no longer a misfit: the local issue file matches GitHub"
    assert re.search(r"pull request|PR operations", misfits, re.I) and "not a tracker verb" in misfits


def test_close_is_a_normal_verb_row_that_states_the_merge_closes_rule_on_both_backends():
    github, local = _verb_rows()["close"]
    for form in (github, local):
        assert "merge closes" in form and "unmerged epic" in form, form
    assert "Closes #<n>" in github and "merged --close" in local


def test_the_runtime_halt_rule_lives_in_the_verbs_reference():
    text = _section(read_src("references/tracker-verbs.md"), "Runtime rule")
    assert re.search(r"never write a local copy", text, re.I)
    assert "retried 3 times" in text and "halt" in text


def test_the_local_store_is_the_tracker_branch_written_only_by_issues_py():
    text = _section(read_src("references/tracker-verbs.md"), "Runtime rule")
    for needle in ("`<repo>/issues`", "`tracker_branch:`", "docs/issues/", "archive/", "issues.py", "BT-LOCAL-<slug>"):
        assert needle in text, needle
    assert re.search(r"never edit", text, re.I) and re.search(r"never check (it )?out", text, re.I)
    assert "BACKLOG" not in read_src("references/tracker-verbs.md")


def test_local_reads_are_issues_py_commands_and_candidates_is_one_command():
    reads = _section(read_src("references/tracker-verbs.md"), "Reads")
    assert "the same-named `issues.py` command" in reads
    assert set(re.findall(r"^- `(\w+)`", reads, re.M)) >= {"get", "list", "wip", "children"}
    for argv in (["get", "x"], ["list"], ["wip"], ["children", "x"], ["blockers", "x"], ["ready"], ["check"]):
        issues.parser().parse_args(argv)  # the same-named commands exist
    assert "issues.py ready" in reads
    line = next(l for l in reads.splitlines() if l.startswith("- `candidates`"))
    assert "ice_read.py candidates" in line and re.search(r"both backends", line)
    assert "issues.py check" in reads and "scans the table" not in reads


@pytest.mark.parametrize("rel", WRITERS)
def test_writers_cite_the_verbs_reference(rel):
    text = read_src(rel)
    assert "references/tracker-verbs-github.md" in text
    assert "references/tracker-verbs-local.md" in text


def _project(master):
    sys.path.insert(0, str(SRC.parent / "build"))
    from build import generate_projected_verbs
    return generate_projected_verbs(master)


def test_projected_tracker_verbs_in_sync_with_master():
    """Build-time projection: the committed projections equal a fresh projection of the master, whole file."""
    exp_gh, exp_local = _project(read_src("references/tracker-verbs.md"))
    assert read_src("references/tracker-verbs-github.md") == exp_gh
    assert read_src("references/tracker-verbs-local.md") == exp_local


def test_every_master_line_reaches_the_projections_it_is_tagged_for():
    """The master is the only source of every section: a tagged line goes to its backend only, an untagged line to
    both, a `master` line to neither; table rows are projected as bullets; no tag survives."""
    master = read_src("references/tracker-verbs.md")
    gh, local = _project(master)
    assert "<!--" not in re.sub(r"<!-- stratos:resume -->", "", gh + local)
    in_verbs = False
    for line in master.splitlines():
        if line.startswith("## "):
            in_verbs = line == "## Verbs"
        if not line.strip() or line.startswith(("---", "description:", "version:", "timestamp:", "# ")) or (in_verbs and line.startswith("|")):
            continue
        m = re.search(r"\s*<!-- (github|local|master) -->\s*$", line)
        text = line[:m.start()] if m else line
        tag = m.group(1) if m else "both"
        assert (text in gh.splitlines()) == (tag in ("github", "both")), f"github projection: {line[:90]}"
        assert (text in local.splitlines()) == (tag in ("local", "both")), f"local projection: {line[:90]}"


@pytest.mark.parametrize("marker_in, heading", [("Reverse switch", "Misfits"), ("retried 3 times", "Runtime rule"),
                                                  ("Post-condition check", "Reads"), ("Per-task progress", "Resume note")])
def test_a_master_edit_to_any_section_reaches_the_projections(marker_in, heading):
    """The old projection hard-coded the Runtime rule, Misfits, Reads and front matter: a master edit never reached them."""
    master = read_src("references/tracker-verbs.md")
    assert marker_in in _section(master, heading)
    gh, local = _project(master.replace(marker_in, "EDITED-IN-MASTER"))
    assert "EDITED-IN-MASTER" in gh or "EDITED-IN-MASTER" in local, f"edit to `## {heading}` reached no projection"


def test_the_front_matter_description_comes_from_the_master():
    gh, local = _project(read_src("references/tracker-verbs.md").replace("description: The single", "description: Zzz single"))
    assert "description: Zzz single" in gh and "description: Zzz single" in local


def test_projected_local_commands_are_real_issues_py_subcommands_and_children_blockers_use_their_own():
    local = read_src("references/tracker-verbs-local.md")
    sub = next(a for a in issues.parser()._actions if a.__class__.__name__ == "_SubParsersAction")
    named = set(re.findall(r"issues\.py ([a-z][a-z-]*)", local))
    assert len(named) >= 10 and named <= set(sub.choices), f"not issues.py subcommands: {named - set(sub.choices)}"
    reads = _section(local, "Reads")
    for verb in ("children", "blockers"):
        line = next(l for l in reads.splitlines() if l.startswith(f"- `{verb}`:"))
        assert f"issues.py {verb} <id>" in line and "issues.py get" not in line, line
    gh_reads = _section(read_src("references/tracker-verbs-github.md"), "Reads")
    assert "- `board`" not in gh_reads and re.search(r"^- `board`:.*issues\.py board .*--md", reads, re.M)


def test_apply_moves_and_the_web_board_reach_only_the_local_projection():
    """The board page's payload is `apply_moves` input: the local file names both, the GitHub file no local command."""
    gh = read_src("references/tracker-verbs-github.md")
    local = read_src("references/tracker-verbs-local.md")
    assert "- `apply_moves`: n/a" in gh and "issues.py" not in next(l for l in gh.splitlines() if l.startswith("- `apply_moves`"))
    assert "board --web" not in gh and "apply-moves" not in gh
    line = next(l for l in local.splitlines() if l.startswith("- `apply_moves`"))
    assert "issues.py apply-moves" in line and "--dry-run" in line and "board --web" in line
    assert "blocker" in line and "--force" in line
    board = next(l for l in local.splitlines() if l.startswith("- `board`"))
    assert "issues.py board --web" in board and "--md" in board and "apply_moves" in board


def test_projected_verbs_contain_all_canonical_verbs():
    gh_text = read_src("references/tracker-verbs-github.md")
    local_text = read_src("references/tracker-verbs-local.md")
    for verb in VERBS:
        assert f"- `{verb}`:" in gh_text, f"verb `{verb}` missing from tracker-verbs-github.md"
        assert f"- `{verb}`:" in local_text, f"verb `{verb}` missing from tracker-verbs-local.md"


def test_projected_local_verbs_commands_match():
    local_text = read_src("references/tracker-verbs-local.md")
    for verb, cmd in LOCAL_COMMAND.items():
        assert f"issues.py {cmd}" in local_text, f"{verb}: command issues.py {cmd} missing in local verbs"


def test_there_is_no_provisional_milestone_outside_the_local_backend():
    for rel in WRITERS[:2]:
        for line in read_src(rel).splitlines():
            if re.search(r"provisional|default `v1\.0\.0`|v1\.0\.0", line):
                assert re.search(r"local", line, re.I), f"{rel}: provisional milestone outside a local clause: {line.strip()[:120]}"


def test_refs_are_the_body_line_on_both_backends():
    text = read_src("references/tracker-verbs.md")
    github, local = _verb_rows()["set_refs"]
    assert "Refs:" in github and "Refs:" in local and "issues.py set" in local and "--body-file" in local
    for rel in WRITERS:
        assert "set_refs" in read_src(rel)
    assert "Refs:" in text


def test_label_taxonomy_is_the_home_of_the_label_rules():
    text = read_src("references/label-taxonomy.md")
    for needle in ("Label Composition Rules", "lifecycle order", "Milestone", "Concept Exemptions", "`concept:map`",
                   "Single Status Invariant", "`status:needs_spec`", "`mode:AFK`", "docs/issues/README.md", "issues.py label"):
        assert needle in text, f"label-taxonomy.md lacks {needle}"
    assert "BACKLOG" not in text and "Label source of truth" not in text  # local never syncs with GitHub


def _taxonomy_labels():
    labels = _section(read_src("references/label-taxonomy.md"), "Labels")
    return set(re.findall(r"`(\w+):([\w-]+)`", labels)) - {(p, "xxx") for p in issues.CANONICAL}  # `size:xxx` headers


def test_the_taxonomy_label_set_equals_issues_canonical():
    """issues.py `check` validates against CANONICAL; the taxonomy is the documented list: they must be one set."""
    found = {(p, v) for p, v in _taxonomy_labels() if p not in ("area", "status")}
    canonical = {(p, v) for p, values in issues.CANONICAL.items() for v in values}
    assert found == canonical, f"taxonomy only: {sorted(found - canonical)}; CANONICAL only: {sorted(canonical - found)}"


def test_the_taxonomy_statuses_equal_issues_statuses():
    statuses = re.findall(r"`status:([^`]+)`", next(l for l in _section(read_src("references/label-taxonomy.md"), "Labels")
                                                     .splitlines() if l.startswith("- **Status")))
    assert [s for s in dict.fromkeys(statuses) if s != "xxx"] == list(issues.STATUSES)


def test_the_learnings_todo_sink_points_to_the_tracker():
    line = next(l for l in read_src("memory-templates/LEARNINGS.md").splitlines() if l.startswith("- Temporary TODOs"))
    assert "BACKLOG_MAP" not in line and "tracker" in line


def test_the_relations_and_template_references_cite_the_new_references():
    assert "references/tracker-verbs-github.md" in read_src("references/github-issue-relations.md")
    assert "references/label-taxonomy.md" in read_src("references/issue-templates.md")
