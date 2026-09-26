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
    assert [s["number"] for s in json.loads(kids)["subIssues"]] == [2]


def test_blocked_by_can_be_added_and_removed(store, capsys):
    run(["issue", "create", "--title", "first"], capsys)
    run(["issue", "create", "--title", "second"], capsys)
    run(_mutation("addBlockedBy", gh.node_id(2), gh.node_id(1)), capsys)
    _, out, _ = run(["issue", "view", "2", "--json", "blockedBy"], capsys)
    assert [b["number"] for b in json.loads(out)["blockedBy"]] == [1]

    run(_mutation("removeBlockedBy", gh.node_id(2), gh.node_id(1)), capsys)
    _, out, _ = run(["issue", "view", "2", "--json", "blockedBy"], capsys)
    assert json.loads(out)["blockedBy"] == []


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
    """Slice 2's real DONE WHEN. `--require-gh` is what the terminal gates pass,
    and it exits 3 with [MIRROR-UNVERIFIED] the moment `gh auth status` fails - so
    reaching [MIRROR-OK] proves the shim was both found and believed."""
    _shimmed_env(tmp_path, monkeypatch)
    _seed_two_slices(capsys)

    project = tmp_path / "project" / ".memory"
    project.mkdir(parents=True)
    (project / "BACKLOG_MAP.md").write_text(BACKLOG, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, str(REPO / "src" / "scripts" / "reconcile.py"),
         "--require-gh", "--ids", "BT-001,BT-002"],
        cwd=str(tmp_path / "project"), capture_output=True, text=True)
    assert "[MIRROR-OK BT-001,BT-002]" in r.stdout, r.stdout + r.stderr
    assert r.returncode == 0


def test_reconcile_still_sees_drift_through_the_shim(tmp_path, monkeypatch, capsys):
    """A shim that made everything pass would be worse than none at all."""
    _shimmed_env(tmp_path, monkeypatch)
    _seed_two_slices(capsys)
    run(["issue", "edit", "2", "--remove-label", "status:planned",
         "--add-label", "status:done"], capsys)

    project = tmp_path / "project" / ".memory"
    project.mkdir(parents=True)
    (project / "BACKLOG_MAP.md").write_text(BACKLOG, encoding="utf-8")

    r = subprocess.run(
        [sys.executable, str(REPO / "src" / "scripts" / "reconcile.py"),
         "--require-gh", "--ids", "BT-002"],
        cwd=str(tmp_path / "project"), capture_output=True, text=True)
    assert "[MIRROR-DRIFT BT-002" in r.stdout
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
