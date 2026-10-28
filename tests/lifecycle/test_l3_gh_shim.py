"""L3 Slice 2 - the `gh` shim, and the gate it exists to let run.

The shim's whole purpose is that `reconcile.py` can reach `[MIRROR-OK]` without a
real repository, so the last test here drives the real `src/scripts/reconcile.py`
against it. No agent and no network.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parent.parent / "lifecycle-harness"
REPO = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gh = _load("l3_gh_shim", HARNESS / "shims" / "gh_shim.py")
e = _load("l3_env_shim", HARNESS / "env.py")


@pytest.fixture
def store(tmp_path, monkeypatch):
    path = tmp_path / "gh-store.json"
    monkeypatch.setenv("L3_GH_STORE", str(path))
    for var in gh.TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)  # a PR call asks git about origin: never the developer's checkout
    return path


def run(argv, capsys):
    code = gh.main(argv)
    out = capsys.readouterr()
    return code, out.out.strip(), out.err.strip()


def state(store):
    return json.loads(store.read_text(encoding="utf-8"))


# --- the three rules the shim exists to keep ---------------------------------

def test_auth_status_succeeds(store, capsys):
    """reconcile.py:139 keys off the exit code alone. A shim that fails here turns
    the terminal-sync gate into a no-op that still reports success."""
    code, _, err = run(["auth", "status"], capsys)
    assert code == 0
    assert "Logged in" in err


def test_an_unknown_subcommand_fails_loudly_and_records_the_argv(store, capsys):
    code, _, err = run(["issue", "transfer", "7"], capsys)
    assert code != 0
    assert "gh issue transfer" in err
    assert ["issue", "transfer", "7"] in state(store)["unknown"]


def test_a_command_from_outside_the_tested_chain_is_not_quietly_served(store, capsys):
    """`gh release view` exists in stratosphere-update, which L3 never drives.
    If a phase reaches for it, that is a finding, not something to fake."""
    code, _, err = run(["release", "view", "--json", "tagName"], capsys)
    assert code != 0
    assert "unknown command" in err


def test_every_invocation_is_recorded(store, capsys):
    run(["auth", "status"], capsys)
    run(["issue", "create", "--title", "one"], capsys)
    run(["version"], capsys)
    assert [i[0] for i in state(store)["invocations"]] == ["auth", "issue", "version"]


def test_a_real_token_stops_the_shim_dead(store, capsys, monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "ghp_a_real_one")
    code, _, err = run(["issue", "create", "--title", "x"], capsys)
    assert code == gh.EXIT_REAL_TOKEN
    assert "GH_TOKEN" in err


def test_no_store_is_refused_rather_than_invented(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("L3_GH_STORE", raising=False)
    for var in gh.TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)
    code, _, err = run(["issue", "list"], capsys)
    assert code == gh.EXIT_NO_STORE
    assert "L3_GH_STORE" in err


# --- issues ------------------------------------------------------------------

def test_issue_numbers_are_monotonic_and_shared_with_prs(store, capsys):
    """GitHub shares numbering across issues and PRs, which is why 2a:32 and 3b:66
    forbid predicting the next one. The shim shares it too."""
    _, first, _ = run(["issue", "create", "--title", "a"], capsys)
    _, second, _ = run(["issue", "create", "--title", "b"], capsys)
    _, pr, _ = run(["pr", "create", "--title", "c", "--draft"], capsys)
    assert first.endswith("/issues/1")
    assert second.endswith("/issues/2")
    assert pr.endswith("/pull/3")


def test_labels_arrive_repeated_or_comma_separated(store, capsys):
    run(["issue", "create", "--title", "a", "--label", "type:feature,size:small",
         "--label", "mode:AFK"], capsys)
    _, out, _ = run(["issue", "view", "1", "--json", "labels"], capsys)
    assert {l["name"] for l in json.loads(out)["labels"]} == {
        "type:feature", "size:small", "mode:AFK"}


def test_issue_edit_swaps_a_status_label(store, capsys):
    run(["issue", "create", "--title", "a", "--label", "status:planned"], capsys)
    run(["issue", "edit", "1", "--remove-label", "status:planned",
         "--add-label", "status:in progress"], capsys)
    _, out, _ = run(["issue", "view", "1", "--json", "labels"], capsys)
    assert [l["name"] for l in json.loads(out)["labels"]] == ["status:in progress"]


def test_view_returns_only_the_fields_asked_for(store, capsys):
    """reconcile.py:130 asks for `blockedBy` alone and skips a field the response
    omits, so returning extras would mask a field real gh does not expose."""
    run(["issue", "create", "--title", "a"], capsys)
    _, out, _ = run(["issue", "view", "1", "--json", "number,labels"], capsys)
    assert set(json.loads(out)) == {"number", "labels"}


def test_an_unknown_json_field_fails(store, capsys):
    run(["issue", "create", "--title", "a"], capsys)
    code, _, err = run(["issue", "view", "1", "--json", "reactionGroups"], capsys)
    assert code != 0
    assert "reactionGroups" in err


def test_jq_selects_the_node_id(store, capsys):
    """github-issue-relations.md:9 nests `--json id -q .id` inside every mutation."""
    run(["issue", "create", "--title", "a"], capsys)
    _, out, _ = run(["issue", "view", "1", "--json", "id", "-q", ".id"], capsys)
    assert out == gh.node_id(1)


def test_an_unsupported_jq_expression_fails_rather_than_guessing(store, capsys):
    run(["issue", "create", "--title", "a"], capsys)
    code, _, err = run(["issue", "view", "1", "--json", "id", "-q",
                        ".labels[] | .name"], capsys)
    assert code != 0
    assert "only `-q .<field>`" in err


def test_issue_list_filters_by_state_and_label(store, capsys):
    run(["issue", "create", "--title", "a", "--label", "type:feature"], capsys)
    run(["issue", "create", "--title", "b"], capsys)
    run(["issue", "close", "1"], capsys)
    _, out, _ = run(["issue", "list", "--state", "open", "--json", "number"], capsys)
    assert [r["number"] for r in json.loads(out)] == [2]


def test_a_pr_link_comment_is_readable_back(store, capsys):
    """4a:75 comments the PR link on the issue; reconcile.py:101 then looks for
    `/pull/` in the comment bodies."""
    run(["issue", "create", "--title", "a"], capsys)
    run(["issue", "comment", "1", "--body",
         "Shipped in https://github.com/l3-harness/throwaway/pull/9"], capsys)
    _, out, _ = run(["issue", "view", "1", "--json", "comments"], capsys)
    assert "/pull/" in json.loads(out)["comments"][0]["body"]


def test_body_file_is_read_from_disk(store, capsys, tmp_path):
    """3b:66 passes the approved draft verbatim, which is a file, never a flag."""
    draft = tmp_path / "draft.md"
    draft.write_text("## Acceptance Criteria\nit works", encoding="utf-8")
    run(["issue", "create", "--title", "a", "--body-file", str(draft)], capsys)
    _, out, _ = run(["issue", "view", "1", "--json", "body"], capsys)
    assert "Acceptance Criteria" in json.loads(out)["body"]


# --- the surface the live runs found missing ---------------------------------

def test_milestones_list_with_paginate_and_query_create_and_include_issue_milestones(store, capsys):
    """`ensure_milestone` (tracker-verbs.md) lists with --paginate, a query string and --jq, then creates with -f."""
    run(["issue", "create", "--title", "seeded", "--milestone", "v0.9.0"], capsys)
    list_argv = ["api", "--paginate", "repos/{owner}/{repo}/milestones?state=open", "--jq", ".[].title"]
    assert run(list_argv, capsys) == (0, "v0.9.0", "")
    assert run(["api", "repos/{owner}/{repo}/milestones", "-f", "title=v1.0.0"], capsys)[0] == 0
    assert run(["api", "repos/{owner}/{repo}/milestones", "-f", "title=v1.0.0"], capsys)[0] == 0  # not duplicated
    assert run(list_argv, capsys)[1].splitlines() == ["v1.0.0", "v0.9.0"]
    assert run(["issue", "create", "--title", "x", "--milestone", "v1.0.0"], capsys)[0] == 0


def test_label_create_then_list_in_text_json_and_jq(store, capsys):
    assert run(["label", "create", "area:fe", "--description", "front end"], capsys)[0] == 0
    run(["issue", "create", "--title", "a", "--label", "type:bug"], capsys)
    assert run(["label", "create", "area:fe"], capsys)[0] == 0  # idempotent
    _, out, _ = run(["label", "list", "--json", "name"], capsys)
    assert json.loads(out) == [{"name": "area:fe"}, {"name": "type:bug"}]
    assert run(["label", "list", "--json", "name", "--jq", ".[].name"], capsys)[1].splitlines() == ["area:fe", "type:bug"]
    assert "area:fe\tfront end" in run(["label", "list"], capsys)[1]
    assert run(["label", "list", "--json", "nope"], capsys)[0] != 0
    assert run(["label", "delete", "area:fe"], capsys)[0] != 0


def _prs(capsys):
    run(["pr", "create", "--title", "Unit one", "--head", "feat/a", "--body", "Closes #7."], capsys)
    run(["pr", "create", "--title", "Unit two", "--head", "feat/b"], capsys)
    run(["pr", "create", "--title", "Unit three", "--head", "feat/c"], capsys)
    run(["issue", "create", "--title", "an issue, not a PR"], capsys)


def test_pr_list_filters_by_state_head_and_search_and_projects_json(store, capsys):
    _prs(capsys)
    raw = state(store)
    raw["issues"]["2"]["state"] = "MERGED"
    raw["issues"]["2"]["mergedAt"] = "2026-10-28T00:00:00Z"
    raw["issues"]["3"]["state"] = "CLOSED"
    store.write_text(json.dumps(raw), encoding="utf-8")

    def numbers(*argv):
        code, out, _ = run(["pr", "list", *argv, "--json", "number"], capsys)
        assert code == 0
        return [r["number"] for r in json.loads(out)]

    assert numbers() == [1]                                          # open by default; the issue is not a PR
    assert numbers("--state", "all") == [1, 2, 3]
    assert numbers("--state", "closed") == [2, 3]                      # closed includes merged, as the search does
    assert numbers("--state", "merged") == [2]
    assert numbers("--state", "all", "--head", "feat/c") == [3]
    assert numbers("--state", "closed", "--search", "closed:>=2026-10-01") == [2, 3]  # dates are ignored
    assert numbers("--state", "all", "--search", "two") == [2]
    _, out, _ = run(["pr", "list", "--state", "all", "--json", "number,mergedAt,closingIssuesReferences,headRefName"], capsys)
    rows = json.loads(out)
    assert rows[0] == {"number": 1, "mergedAt": None, "closingIssuesReferences": [{"number": 7}], "headRefName": "feat/a"}
    assert rows[1]["mergedAt"] == "2026-10-28T00:00:00Z"
    assert run(["pr", "list", "--search", "label:x"], capsys)[0] != 0     # an unimplemented qualifier fails loudly


def test_pr_edit_changes_body_title_and_labels(store, capsys, tmp_path):
    _prs(capsys)
    body = tmp_path / "b.md"
    body.write_text("new body", encoding="utf-8")
    assert run(["pr", "edit", "1", "--title", "Renamed", "--body-file", str(body),
                "--add-label", "risk:one-way"], capsys)[0] == 0
    assert run(["pr", "edit", "1", "--add-label", "x", "--remove-label", "risk:one-way"], capsys)[0] == 0
    _, out, _ = run(["pr", "view", "1", "--json", "title,body,labels"], capsys)
    got = json.loads(out)
    assert (got["title"], got["body"], got["labels"]) == ("Renamed", "new body", [{"name": "x"}])


def test_pr_ready_undo_converts_back_to_draft(store, capsys):
    run(["pr", "create", "--title", "p", "--draft"], capsys)
    run(["pr", "ready", "1"], capsys)
    assert json.loads(run(["pr", "view", "1", "--json", "isDraft"], capsys)[1]) == {"isDraft": False}
    run(["pr", "ready", "1", "--undo"], capsys)
    assert json.loads(run(["pr", "view", "1", "--json", "isDraft"], capsys)[1]) == {"isDraft": True}


def test_adding_an_assignee_twice_keeps_one_like_real_github(store, capsys):
    run(["issue", "create", "--title", "a"], capsys)
    run(["issue", "edit", "1", "--add-assignee", "@me"], capsys)
    run(["issue", "edit", "1", "--add-assignee", "@me"], capsys)
    assert json.loads(run(["issue", "view", "1", "--json", "assignees"], capsys)[1]) == {"assignees": ["@me"]}


def test_issue_reopen_sets_the_state_back_to_open(store, capsys):
    run(["issue", "create", "--title", "a"], capsys)
    run(["issue", "close", "1"], capsys)
    assert run(["issue", "reopen", "1"], capsys)[0] == 0
    assert json.loads(run(["issue", "view", "1", "--json", "state"], capsys)[1]) == {"state": "OPEN"}


# --- relations ---------------------------------------------------------------

def _mutation(kind, a, b):
    query = f"mutation($x:ID!,$y:ID!){{{kind}(input:{{...}}){{issue{{number}}}}}}"
    keys = {"addSubIssue": ("p", "c")}.get(kind, ("i", "b"))
    return ["api", "graphql", "-f", f"query={query}",
            "-f", f"{keys[0]}={a}", "-f", f"{keys[1]}={b}"]


def test_add_sub_issue_sets_both_ends(store, capsys):
    run(["issue", "create", "--title", "epic"], capsys)
    run(["issue", "create", "--title", "slice"], capsys)
    code, _, _ = run(_mutation("addSubIssue", gh.node_id(1), gh.node_id(2)), capsys)
    assert code == 0
    _, parent, _ = run(["issue", "view", "2", "--json", "parent"], capsys)
    _, kids, _ = run(["issue", "view", "1", "--json", "subIssues"], capsys)
    assert json.loads(parent)["parent"]["number"] == 1
    assert [s["number"] for s in json.loads(kids)["subIssues"]["nodes"]] == [2]


def test_blocked_by_can_be_added_and_removed(store, capsys):
    run(["issue", "create", "--title", "first"], capsys)
    run(["issue", "create", "--title", "second"], capsys)
    run(_mutation("addBlockedBy", gh.node_id(2), gh.node_id(1)), capsys)
    _, out, _ = run(["issue", "view", "2", "--json", "blockedBy"], capsys)
    assert [b["number"] for b in json.loads(out)["blockedBy"]["nodes"]] == [1]

    run(_mutation("removeBlockedBy", gh.node_id(2), gh.node_id(1)), capsys)
    _, out, _ = run(["issue", "view", "2", "--json", "blockedBy"], capsys)
    assert json.loads(out)["blockedBy"] == {"nodes": [], "totalCount": 0}


def test_an_unknown_mutation_fails_by_name(store, capsys):
    code, _, err = run(["api", "graphql", "-f",
                        "query=mutation{closeIssue(input:{}){issue{number}}}"], capsys)
    assert code != 0
    assert "addSubIssue" in err


def test_a_node_id_the_store_never_minted_fails(store, capsys):
    run(["issue", "create", "--title", "a"], capsys)
    code, _, err = run(_mutation("addSubIssue", "I_notmine", gh.node_id(1)), capsys)
    assert code != 0
    assert "node id" in err


# --- the gate this all exists for --------------------------------------------

BACKLOG = """\
| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| BT-001 | Ruleset parsing | planned | type:feature, size:small | v1.0.0 | — | — | 1.0 | — |
| BT-002 | Percentage rollout | planned | type:feature, size:small | v1.0.0 | BT-001 | BT-001 | 1.0 | — |
"""


def _shimmed_env(tmp_path, monkeypatch):
    """The run's environment, applied to THIS process.

    `monkeypatch.setenv` rather than `env=` on purpose: on Windows the executable
    search uses the calling process's PATH, so passing `env=` would resolve the
    developer's real gh and the test would prove nothing.
    """
    child = {"PATH": os.environ.get("PATH", "")}
    e.install_shims(tmp_path, child)
    for key in ("PATH", "PYTHONPATH", "L3_GH_STORE"):
        monkeypatch.setenv(key, child[key])
    for var in gh.TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)
    return child


def _seed_two_slices(capsys):
    run(["issue", "create", "--title", "Ruleset parsing", "--label",
         "status:planned,type:feature,size:small", "--milestone", "v1.0.0"], capsys)
    run(["issue", "create", "--title", "Percentage rollout", "--label",
         "status:planned,type:feature,size:small", "--milestone", "v1.0.0"], capsys)
    run(_mutation("addSubIssue", gh.node_id(1), gh.node_id(2)), capsys)
    run(_mutation("addBlockedBy", gh.node_id(2), gh.node_id(1)), capsys)


def test_reconcile_reaches_mirror_ok_against_the_shim(tmp_path, monkeypatch, capsys):
    """Slice 2's real DONE WHEN. The GitHub-mode gate exits 3 with [GH-UNAVAILABLE] the moment `gh auth
    status` fails - so reaching [MIRROR-OK] proves the shim was both found and believed."""
    _shimmed_env(tmp_path, monkeypatch)
    _seed_two_slices(capsys)

    r = _reconcile(_github_project(tmp_path), "--ids", "BT-001,BT-002",
                   "--expect", "BT-1:status=planned;BT-2:status=planned")
    assert "[MIRROR-OK BT-001,BT-002]" in r.stdout, r.stdout + r.stderr
    assert r.returncode == 0


def test_reconcile_still_sees_drift_through_the_shim(tmp_path, monkeypatch, capsys):
    """A shim that made everything pass would be worse than none at all."""
    _shimmed_env(tmp_path, monkeypatch)
    _seed_two_slices(capsys)
    run(["issue", "edit", "2", "--remove-label", "status:planned",
         "--add-label", "status:done"], capsys)

    r = _reconcile(_github_project(tmp_path), "--ids", "BT-002", "--expect", "BT-2:status=planned")
    assert "[MIRROR-DRIFT BT-002" in r.stdout, r.stdout + r.stderr
    assert r.returncode == 1


def test_a_cmd_shim_alone_would_not_intercept_a_python_caller(tmp_path, monkeypatch):
    """The reason `gh.exe` is minted at all.

    On Windows `CreateProcess` appends only `.exe` when it searches PATH - PATHEXT
    is a shell feature - so `shutil.which` finds a `gh.cmd` and
    `subprocess.run(['gh'])` does not. `reconcile.py:109,139` is the second kind of
    caller, and with only a `.cmd` on PATH it would reach the developer's real gh,
    authenticated through the OS keyring. If this test ever starts failing, the
    platform changed and the minted launcher can go.
    """
    if os.name != "nt":
        pytest.skip("POSIX searches the passed env's PATH and runs `gh` directly")

    cmd_only = tmp_path / "cmd-only"
    cmd_only.mkdir()
    (cmd_only / "gh.cmd").write_text(
        "@echo off\necho CMD-SHIM-SPEAKING\n", encoding="utf-8")
    monkeypatch.setenv("PATH", str(cmd_only) + os.pathsep + os.environ["PATH"])

    import shutil
    assert shutil.which("gh") == str(cmd_only / "gh.CMD"), "PATH is not as expected"
    probe = subprocess.run([sys.executable, "-c", e._PROBE],
                           capture_output=True, text=True)
    assert "CMD-SHIM-SPEAKING" not in probe.stdout, (
        "a .cmd shim now DOES intercept a Python caller - the minted gh.exe is "
        "no longer needed")


def test_the_minted_launcher_does_intercept(tmp_path):
    child = {"PATH": os.environ.get("PATH", "")}
    shim_dir = e.install_shims(tmp_path, child)
    if os.name == "nt":
        assert (shim_dir / "gh.exe").exists(), "no launcher was minted"
    e.assert_gh_is_shimmed(child)


# --- GitHub mode: the batched read the gate makes (BT-195) -------------------

rec = _load("l3_reconcile_gh_mode", REPO / "src" / "scripts" / "reconcile.py")
ARCH_GITHUB = '---\ntype: architecture\ntracker: github\nversion: "1.0.0"\n---\n# A\n'


def _graphql_read(nums, capsys, **kw):
    code, out, err = run(["api", "graphql", "-F", "owner={owner}", "-F", "name={repo}",
                          "-f", "query=" + rec.build_query(nums, **kw)], capsys)
    return code, out, err


def _seed_chain(capsys):
    """#1 epic, #2 and #3 its slices, #3 blocked by #2."""
    run(["issue", "create", "--title", "epic", "--label", "tier:epic,status:in progress"], capsys)
    run(["issue", "create", "--title", "first", "--label", "tier:slice,status:in review", "--milestone", "v1.2.0"], capsys)
    run(["issue", "create", "--title", "second", "--label", "tier:slice,status:planned", "--milestone", "v1.2.0"], capsys)
    run(_mutation("addSubIssue", gh.node_id(1), gh.node_id(2)), capsys)
    run(_mutation("addSubIssue", gh.node_id(1), gh.node_id(3)), capsys)
    run(_mutation("addBlockedBy", gh.node_id(3), gh.node_id(2)), capsys)
    run(["issue", "comment", "2", "--body", "Shipped in https://github.com/l3-harness/throwaway/pull/9"], capsys)


def test_a_batched_alias_query_answers_with_graphql_connections(store, capsys):
    _seed_chain(capsys)
    code, out, _ = _graphql_read([2, 3], capsys, comments=True, edges=True)
    repo = json.loads(out)["data"]["repository"]
    assert code == 0 and set(repo) == {"i_2", "i_3"}
    two, three = repo["i_2"], repo["i_3"]
    assert two["state"] == "OPEN" and two["milestone"] == {"title": "v1.2.0"}
    assert {l["name"] for l in two["labels"]["nodes"]} == {"tier:slice", "status:in review"}
    assert two["parent"]["number"] == 1 and "tier:epic" in {l["name"] for l in two["parent"]["labels"]["nodes"]}
    assert [n["number"] for n in two["blocking"]["nodes"]] == [3]
    assert [n["number"] for n in three["blockedBy"]["nodes"]] == [2]
    assert "/pull/" in two["comments"]["nodes"][0]["body"]


def test_a_missing_issue_is_a_null_alias_with_a_not_found_error_and_exit_1(store, capsys):
    """Real gh prints the partial data and exits 1 when any alias errors."""
    _seed_chain(capsys)
    code, out, _ = _graphql_read([2, 99], capsys)
    body = json.loads(out)
    assert code == 1 and body["data"]["repository"]["i_99"] is None and body["data"]["repository"]["i_2"]["number"] == 2
    assert [e["type"] for e in body["errors"]] == ["NOT_FOUND"]
    assert [] == state(store)["unknown"], "a missing issue is not an unknown command"


def test_json_parent_and_blocked_by_view_and_body_edit_round_trip(store, capsys, tmp_path):
    _seed_chain(capsys)
    _, out, _ = run(["issue", "view", "3", "--json", "parent,blockedBy"], capsys)
    data = json.loads(out)
    assert data["parent"]["number"] == 1 and [n["number"] for n in data["blockedBy"]["nodes"]] == [2]
    body = tmp_path / "body.md"
    body.write_text("Refs: [[L-001]]", encoding="utf-8")
    run(["issue", "edit", "3", "--body-file", str(body)], capsys)
    _, out, _ = run(["issue", "view", "3", "--json", "body"], capsys)
    assert json.loads(out)["body"] == "Refs: [[L-001]]"


def _github_project(tmp_path):
    project = tmp_path / "project"
    (project / ".memory").mkdir(parents=True)
    (project / ".memory" / "ARCHITECTURE.md").write_text(ARCH_GITHUB, encoding="utf-8")
    return project


def _reconcile(project, *argv):
    return subprocess.run([sys.executable, str(REPO / "src" / "scripts" / "reconcile.py"), *argv],
                          cwd=str(project), capture_output=True, text=True)


def test_github_mode_gate_runs_with_no_map_in_one_gh_call_for_four_ids(tmp_path, monkeypatch, capsys):
    """BT-195 AC: tracker github + no map; a missing status label, a missing PR-link comment and an open-but-done
    issue are all found, with at most 2 gh calls for 4 ids."""
    _shimmed_env(tmp_path, monkeypatch)
    for title, labels in (("a", "status:in review"), ("b", "status:planned"), ("c", "status:done"), ("d", "type:improvement")):
        run(["issue", "create", "--title", title, "--label", labels], capsys)
    project = _github_project(tmp_path)
    before = len(state(os.environ and Path(os.environ["L3_GH_STORE"]))["invocations"])
    r = _reconcile(project, "--ids", "BT-001,BT-002,BT-003,BT-004", "--pr-id", "BT-001",
                   "--expect", "BT-1:status=in review;BT-2:status=planned;BT-3:status=done;BT-4:status=planned")
    calls = len(state(Path(os.environ["L3_GH_STORE"]))["invocations"]) - before
    assert r.returncode == 1, r.stdout + r.stderr
    assert "[MIRROR-DRIFT BT-001: pr-link absent from issue comments]" in r.stdout
    assert "[MIRROR-DRIFT BT-003: open on GitHub, expect=done]" in r.stdout
    assert "[MIRROR-DRIFT BT-004: status expect=planned gh=None]" in r.stdout
    assert "BT-002" not in r.stdout
    assert calls <= 2, calls
    assert not (project / ".memory" / "BACKLOG_MAP.md").exists()


def test_github_mode_paginates_past_100_issues(tmp_path, monkeypatch, capsys):
    _shimmed_env(tmp_path, monkeypatch)
    for i in range(1, 102):
        run(["issue", "create", "--title", f"s{i}", "--label", "status:planned"], capsys)
    project = _github_project(tmp_path)
    ids = ",".join(f"BT-{i:03d}" for i in range(1, 102))
    before = len(state(Path(os.environ["L3_GH_STORE"]))["invocations"])
    r = _reconcile(project, "--ids", ids, "--expect", "BT-101:status=done")
    calls = len(state(Path(os.environ["L3_GH_STORE"]))["invocations"]) - before
    assert r.returncode == 1 and "[MIRROR-DRIFT BT-101: open on GitHub, expect=done]" in r.stdout, r.stdout + r.stderr
    assert "not found" not in r.stdout and calls == 3


def test_combined_mode_returns_gate_and_edges_in_one_invocation(tmp_path, monkeypatch, capsys):
    _shimmed_env(tmp_path, monkeypatch)
    _seed_chain(capsys)
    project = _github_project(tmp_path)
    before = len(state(Path(os.environ["L3_GH_STORE"]))["invocations"])
    r = _reconcile(project, "--ids", "BT-002", "--pr-id", "BT-002", "--with-edges", "dependents",
                   "--expect", "BT-2:status=in review")
    calls = len(state(Path(os.environ["L3_GH_STORE"]))["invocations"]) - before
    assert r.returncode == 0, r.stdout + r.stderr
    assert "[MIRROR-OK BT-002]" in r.stdout and "[CLEAR BT-003 <- BT-002] same-unit" in r.stdout
    assert calls == 1


def test_a_gh_failure_halts_without_a_local_copy(tmp_path, monkeypatch, capsys):
    """No store is set, so the shim refuses every call: exit 3, a clear line, nothing written."""
    _shimmed_env(tmp_path, monkeypatch)
    monkeypatch.delenv("L3_GH_STORE", raising=False)
    project = _github_project(tmp_path)
    r = subprocess.run([sys.executable, "-c",
                        "import sys; sys.argv=['reconcile.py']+sys.argv[1:]; "
                        f"sys.path.insert(0, {str(REPO / 'src' / 'scripts')!r}); import reconcile; "
                        "reconcile.RETRY_DELAYS=(0,0,0); sys.exit(reconcile.main())",
                        "--ids", "BT-001", "--expect", "BT-1:status=done"],
                       cwd=str(project), capture_output=True, text=True, env={**os.environ})
    assert r.returncode == 3 and "[GH-UNAVAILABLE" in r.stdout, r.stdout + r.stderr
    assert sorted(p.name for p in (project / ".memory").iterdir()) == ["ARCHITECTURE.md"]


# --- the surface the follow-up live test needs: real branches, live relations, a CI rollup -------------------

def _git(cwd, *args):
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t.invalid", "-c", "commit.gpgsign=false",
                        *args], cwd=str(cwd), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.fixture
def clone(tmp_path, store, monkeypatch):
    """A working clone whose `origin` is a local bare repo with `master` pushed: what the sandbox gives the shim."""
    bare, work = tmp_path / "origin.git", tmp_path / "work"
    work.mkdir()
    _git(tmp_path, "init", "--bare", "-b", "master", str(bare))
    _git(work, "init", "-b", "master")
    _git(work, "remote", "add", "origin", bare.as_posix())
    (work / "a.txt").write_text("a", encoding="utf-8")
    _git(work, "add", "-A")
    _git(work, "commit", "-m", "init")
    _git(work, "push", "-q", "origin", "master")
    monkeypatch.chdir(work)
    return work


def _push_branch(work, name, content="b"):
    _git(work, "checkout", "-q", "-b", name)
    (work / f"{name.replace('/', '_')}.txt").write_text(content, encoding="utf-8")
    _git(work, "add", "-A")
    _git(work, "commit", "-m", f"work on {name}")
    _git(work, "push", "-q", "origin", name)
    return _git(work, "rev-parse", "HEAD")


def _view(capsys, *argv):
    code, out, err = run(["pr", "view", *argv], capsys)
    assert code == 0, err
    return json.loads(out)


def test_pr_create_defaults_head_to_the_current_branch_and_base_to_the_remote_head(clone, store, capsys):
    sha = _push_branch(clone, "feat/x")
    assert run(["pr", "create", "--title", "t", "--draft"], capsys)[0] == 0
    got = _view(capsys, "1", "--json", "headRefName,baseRefName,headRefOid,baseRefOid")
    assert (got["headRefName"], got["baseRefName"], got["headRefOid"]) == ("feat/x", "master", sha)
    assert got["baseRefOid"] == _git(clone, "rev-parse", "origin/master")


def test_head_ref_oid_follows_the_remote_not_the_pr_creation(clone, store, capsys):
    """ci_gate waits until `headRefOid` equals the pushed sha, so a later push must show."""
    _push_branch(clone, "feat/x")
    run(["pr", "create", "--title", "t"], capsys)
    (clone / "more.txt").write_text("m", encoding="utf-8")
    _git(clone, "add", "-A")
    _git(clone, "commit", "-m", "more")
    _git(clone, "push", "-q", "origin", "feat/x")
    assert _view(capsys, "1", "--json", "headRefOid")["headRefOid"] == _git(clone, "rev-parse", "HEAD")


def test_explicit_head_and_base_win_over_the_defaults(clone, store, capsys):
    _push_branch(clone, "feat/x")
    run(["pr", "create", "--title", "t", "--head", "feat/y", "--base", "release"], capsys)
    assert _view(capsys, "1", "--json", "headRefName,baseRefName,headRefOid") == {
        "headRefName": "feat/y", "baseRefName": "release", "headRefOid": None}


def test_a_remote_that_is_not_local_is_never_contacted(clone, store, capsys):
    """The shim must not reach a network: an https origin falls back to `main` and no oid."""
    _git(clone, "remote", "set-url", "origin", "https://example.invalid/x/y.git")
    run(["pr", "create", "--title", "t", "--head", "feat/x"], capsys)
    assert _view(capsys, "1", "--json", "baseRefName,headRefOid") == {"baseRefName": "main", "headRefOid": None}


def test_pr_view_with_no_argument_or_a_branch_name_finds_the_pr(clone, store, capsys):
    _push_branch(clone, "feat/x")
    run(["pr", "create", "--title", "one"], capsys)
    run(["pr", "create", "--title", "other", "--head", "feat/other"], capsys)
    assert _view(capsys, "--json", "number") == {"number": 1}                      # the current branch
    assert _view(capsys, "feat/other", "--json", "number") == {"number": 2}
    assert _view(capsys, "https://github.com/l3-harness/throwaway/pull/2", "--json", "number") == {"number": 2}
    code, _, err = run(["pr", "view", "feat/none", "--json", "number"], capsys)
    assert code != 0 and "feat/none" in err


def test_pr_view_by_branch_prefers_the_open_pr(clone, store, capsys):
    _push_branch(clone, "feat/x")
    def set_states(*states):
        raw = state(store)
        for number, st in enumerate(states, 1):
            raw["issues"][str(number)]["state"] = st
        store.write_text(json.dumps(raw), encoding="utf-8")

    run(["pr", "create", "--title", "old"], capsys)
    set_states("CLOSED")
    run(["pr", "create", "--title", "new"], capsys)
    set_states("OPEN", "CLOSED")
    assert _view(capsys, "--json", "number") == {"number": 1}   # the open one, though a newer PR exists
    set_states("CLOSED", "MERGED")
    assert _view(capsys, "--json", "number") == {"number": 2}   # none open: the newest


def test_a_second_open_pr_for_the_same_head_and_base_is_refused(clone, store, capsys):
    _push_branch(clone, "feat/x")
    assert run(["pr", "create", "--title", "one"], capsys)[0] == 0
    code, _, err = run(["pr", "create", "--title", "two"], capsys)
    assert code != 0 and "already exists" in err


def test_pr_view_of_an_issue_number_fails(store, capsys):
    run(["issue", "create", "--title", "an issue"], capsys)
    assert run(["pr", "view", "1", "--json", "number"], capsys)[0] != 0


def test_a_pr_carries_one_green_check_run_by_default_and_a_stored_rollup_overrides_it(clone, store, capsys):
    _push_branch(clone, "feat/x")
    run(["pr", "create", "--title", "t"], capsys)
    rollup = _view(capsys, "1", "--json", "statusCheckRollup")["statusCheckRollup"]
    assert [(c["__typename"], c["status"], c["conclusion"]) for c in rollup] == [("CheckRun", "COMPLETED", "SUCCESS")]
    raw = state(store)
    raw["issues"]["1"]["statusCheckRollup"] = []
    store.write_text(json.dumps(raw), encoding="utf-8")
    assert _view(capsys, "1", "--json", "statusCheckRollup") == {"statusCheckRollup": []}


def test_ci_gate_reads_green_from_the_shim(clone, store, tmp_path, monkeypatch, capsys):
    """4a's CI gate: `pr view N --json headRefOid,baseRefOid,mergeStateStatus,statusCheckRollup` against the pushed sha."""
    _shimmed_env(tmp_path, monkeypatch)
    sha = _push_branch(clone, "feat/x")
    run(["pr", "create", "--title", "t", "--draft"], capsys)
    r = subprocess.run([sys.executable, str(REPO / "src" / "scripts" / "ci_gate.py"), "status", "--pr", "1",
                        "--sha", sha, "--wait", "5"], cwd=str(clone), capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads(r.stdout)["verdict"] == "green"
    assert state(Path(os.environ["L3_GH_STORE"]))["unknown"] == []


def test_sub_issues_and_blocked_by_render_live_from_the_store(store, capsys):
    """A relation recorded while the issue was open must show it CLOSED after a later close."""
    _seed_chain(capsys)
    run(["issue", "close", "2"], capsys)
    kids = json.loads(run(["issue", "view", "1", "--json", "subIssues"], capsys)[1])["subIssues"]
    assert {n["number"]: n["state"] for n in kids["nodes"]} == {2: "CLOSED", 3: "OPEN"} and kids["totalCount"] == 2
    blockers = json.loads(run(["issue", "view", "3", "--json", "blockedBy"], capsys)[1])["blockedBy"]
    assert [(n["number"], n["state"]) for n in blockers["nodes"]] == [(2, "CLOSED")]
    assert json.loads(run(["issue", "view", "3", "--json", "parent"], capsys)[1])["parent"]["number"] == 1
    listed = json.loads(run(["issue", "list", "--json", "number,blockedBy", "--state", "all"], capsys)[1])
    assert [[n["state"] for n in r["blockedBy"]["nodes"]] for r in listed if r["number"] == 3] == [["CLOSED"]]


def test_issue_list_filters_by_milestone(store, capsys):
    run(["issue", "create", "--title", "a", "--milestone", "v1.0.1"], capsys)
    run(["issue", "create", "--title", "b", "--milestone", "v1.1.0"], capsys)
    run(["issue", "create", "--title", "c"], capsys)
    _, out, _ = run(["issue", "list", "--state", "open", "--milestone", "v1.0.1", "--json", "number,milestone"], capsys)
    assert json.loads(out) == [{"number": 1, "milestone": {"title": "v1.0.1"}}]
    assert run(["issue", "list", "-m", "v9.9.9", "--json", "number"], capsys)[1] == "[]"


def test_issue_edit_remove_milestone_unsets_it(store, capsys):
    run(["issue", "create", "--title", "a", "--milestone", "v1.0.0"], capsys)
    assert run(["issue", "edit", "1", "--remove-milestone"], capsys)[0] == 0
    assert json.loads(run(["issue", "view", "1", "--json", "milestone"], capsys)[1]) == {"milestone": None}
