"""BT-144 follow-up: `pr_body.py` builds the feature-PR body (`build`) and decides suite reuse (`suite`).

Seam: the CLI (stdout + exit code) run inside a throwaway git repo. The script is a pure builder:
it never calls `gh`; the prior PR body arrives as a file.
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT, commit, git

SCRIPT = REPO_ROOT / "src" / "scripts" / "pr_body.py"
RISK_PATHS = REPO_ROOT / "src" / "references" / "merge-risk-paths.md"


def init_repo(path, default_branch):
    git(path, "init", "-b", default_branch)
    git(path, "config", "user.name", "t")
    git(path, "config", "user.email", "t@example.com")
    (path / ".git" / "info" / "exclude").write_text(".tmp/\n", encoding="utf-8")
    commit(path, "chore: init", ["README.md"])
    git(path, "checkout", "-b", "feat/BT-10-x")
    (path / ".tmp").mkdir()
    return path


@pytest.fixture
def repo(tmp_path):
    return init_repo(tmp_path, "main")


@pytest.fixture
def develop_repo(tmp_path):
    """Default branch is `develop`: none of the main/master candidates exist, and there is no remote."""
    return init_repo(tmp_path, "develop")


def run(repo, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], cwd=repo, capture_output=True, text=True)


def write_suite(repo, name="3d-suite-BT-1.json", sha=None, cmd="pytest -q", observed="5 passed"):
    sha = sha or git(repo, "rev-parse", "HEAD")
    p = repo / ".tmp" / name
    p.write_text(json.dumps({"head_sha": sha, "cmd": cmd, "observed": observed}), encoding="utf-8")
    return p


def build(repo, slice_id, *extra, prior=None, summary="did a thing", verdict="PASS", rounds=1, parent="BT-10"):
    suite = write_suite(repo, f"3d-suite-{slice_id}.json")
    args = ["build", "--slice", slice_id, "--summary", summary, "--verdict", verdict,
            "--audit-rounds", rounds, "--base", "main", "--risk-paths", RISK_PATHS,
            "--suite-json", suite, "--parent", parent, *extra]
    if prior:
        args += ["--prior-body-file", prior]
    r = run(repo, *args)
    assert r.returncode == 0, r.stderr
    return r.stdout


def block(body):
    return re.search(r"```stratos-pr\n(.*?)\n```", body, re.S).group(1)


def field(body, name):
    return re.search(rf"^{name}: (.*)$", block(body), re.M).group(1)


def slices(body):
    return re.findall(r"^  - \{id: (BT-\d+), summary: (\".*?\"), verdict: (\w+), audit_rounds: (\d+)\}$", block(body), re.M)


def test_body_shape_closing_lines_then_block_and_parent_only_on_flag(repo):
    commit(repo, "feat(BT-11): first")
    body = build(repo, "BT-11")
    assert body.startswith("Closes #11.\n\n```stratos-pr\n")
    assert "Closes #10." not in body
    assert field(body, "feature") == "BT-10"
    assert field(body, "head") == git(repo, "rev-parse", "HEAD")
    closed = build(repo, "BT-11", "--close-parent")
    assert closed.splitlines()[:2] == ["Closes #11.", "Closes #10."]


def test_slices_rebuilt_from_git_log_ignoring_unscoped_commits(repo):
    commit(repo, "feat(BT-11): first")
    commit(repo, "fix(BT-12): second")
    commit(repo, "release: prepare v1.2.3")
    body = build(repo, "BT-11")
    assert [s[0] for s in slices(body)] == ["BT-11", "BT-12"]


def test_other_slices_keep_prior_values_and_pending_gets_no_closes_line(repo, tmp_path):
    commit(repo, "feat(BT-11): first")
    prior = repo / ".tmp" / "prior.md"
    prior.write_text(build(repo, "BT-11", summary="slice one", verdict="WAIVED", rounds=3), encoding="utf-8")
    commit(repo, "feat(BT-12): second")
    commit(repo, "feat(BT-13): third, not yet shipped")
    body = build(repo, "BT-12", prior=prior, summary="slice two")
    by_id = {s[0]: s for s in slices(body)}
    assert by_id["BT-11"][1:] == ('"slice one"', "WAIVED", "3")
    assert by_id["BT-12"][1:] == ('"slice two"', "PASS", "1")
    assert by_id["BT-13"][2] == "PENDING"
    assert "Closes #11." in body and "Closes #12." in body and "Closes #13." not in body


def test_post_merge_deviations_refs_survive_across_three_slice_ships(repo):
    commit(repo, "feat(BT-11): one")
    p1 = repo / ".tmp" / "p1.md"
    p1.write_text(build(repo, "BT-11", "--post-merge", "run migration 0007", "--deviation", "used queue not cron",
                        "--ref", "L-12"), encoding="utf-8")
    commit(repo, "feat(BT-12): two")
    p2 = repo / ".tmp" / "p2.md"
    p2.write_text(build(repo, "BT-12", "--post-merge", "flip flag", "--ref", "D-3", prior=p1), encoding="utf-8")
    commit(repo, "feat(BT-13): three")
    body = build(repo, "BT-13", "--post-merge", "run migration 0007", "--manual-qa", "--ref", "L-12", prior=p2)
    assert json.loads(field(body, "post_merge")) == ["run migration 0007", "flip flag", "manual-QA: BT-13"]
    assert json.loads(field(body, "deviations")) == ["used queue not cron"]
    assert field(body, "refs") == "[L-12, D-3]"
    assert [s[0] for s in slices(body)] == ["BT-11", "BT-12", "BT-13"]


def test_rebuild_with_same_inputs_is_idempotent(repo):
    commit(repo, "feat(BT-11): one")
    first = repo / ".tmp" / "first.md"
    first.write_text(build(repo, "BT-11", "--post-merge", "a step", "--notes", "root cause: x"), encoding="utf-8")
    again = build(repo, "BT-11", "--post-merge", "a step", prior=first)
    assert again == first.read_text(encoding="utf-8")
    assert again.rstrip().endswith("## Notes\nroot cause: x")


def test_risk_fires_on_one_way_path_from_all_changed_files_else_none(repo):
    commit(repo, "feat(BT-11): clean")
    assert field(build(repo, "BT-11"), "risk") == "[none]"
    commit(repo, "feat(BT-11): migration", ["db/migrations/001_init.sql"])
    commit(repo, "feat(BT-12): later, clean", ["src/app.py"])
    body = build(repo, "BT-12")
    assert field(body, "risk") == "[db-migration]", "risk covers every file in <base>..HEAD, not just the shipped slice"
    commit(repo, "ci(BT-12): pipeline", [".github/workflows/ci.yml"])
    assert field(build(repo, "BT-12"), "risk") == "[ci, db-migration]"


def test_risk_reads_project_one_way_paths_from_architecture(repo):
    arch = repo / ".memory" / "ARCHITECTURE.md"
    arch.parent.mkdir()
    arch.write_text("# A\n\n## One-way paths\n- `scripts/deploy_*.py` → `live-write`\n\n## Other\n", encoding="utf-8")
    commit(repo, "feat(BT-11): deploy", ["scripts/deploy_prod.py"])
    assert field(build(repo, "BT-11"), "risk") == "[live-write]"


def test_test_block_comes_from_suite_json_and_head_is_current(repo):
    c = commit(repo, "feat(BT-11): one")
    suite = write_suite(repo, "s.json", sha=c, cmd="make test", observed="9 passed")
    commit(repo, "release: prepare v2.0.0")
    r = run(repo, "build", "--slice", "BT-11", "--summary", "s", "--verdict", "PASS", "--audit-rounds", "1",
            "--base", "main", "--risk-paths", RISK_PATHS, "--suite-json", suite)
    assert r.returncode == 0, r.stderr
    assert field(r.stdout, "test") == f'{{cmd: "make test", observed: "9 passed", at: {c}}}'
    assert field(r.stdout, "head") == git(repo, "rev-parse", "HEAD") != c


def test_build_without_reusable_suite_exits_2_and_names_the_fix(repo):
    commit(repo, "feat(BT-11): one")
    r = run(repo, "build", "--slice", "BT-11", "--summary", "s", "--verdict", "PASS", "--audit-rounds", "1",
            "--base", "main", "--risk-paths", RISK_PATHS)
    assert r.returncode == 2 and "[NO-SUITE]" in r.stderr and not r.stdout


def test_out_writes_the_body_to_a_file(repo):
    commit(repo, "feat(BT-11): one")
    out = repo / ".tmp" / "body.md"
    body = build(repo, "BT-11", "--out", out)
    assert body == "" and out.read_text(encoding="utf-8").startswith("Closes #11.")


def build_raw(repo, *extra, suite=None, **kw):
    args = ["build", "--slice", "BT-11", "--summary", "s", "--verdict", "PASS", "--audit-rounds", "1",
            "--base", "main", "--risk-paths", kw.get("risk", RISK_PATHS), *extra]
    if suite is not None:
        args += ["--suite-json", suite]
    return run(repo, *args)


def assert_clean_error(r):
    assert r.returncode == 2 and r.stderr.startswith("[PR-BODY-ERROR]") and "Traceback" not in r.stderr and not r.stdout, r.stderr


def test_build_bad_suite_json_or_prior_file_is_a_clean_exit_2(repo):
    commit(repo, "feat(BT-11): one")
    assert_clean_error(build_raw(repo, suite=repo / ".tmp" / "missing.json"))
    garbage = repo / ".tmp" / "garbage.json"
    garbage.write_text("{not json", encoding="utf-8")
    assert_clean_error(build_raw(repo, suite=garbage))
    good = write_suite(repo, "good.json")
    assert_clean_error(build_raw(repo, "--prior-body-file", repo / ".tmp" / "nope.md", suite=good))


def test_build_suite_record_missing_a_field_is_a_clean_exit_2(repo):
    commit(repo, "feat(BT-11): one")
    sha = git(repo, "rev-parse", "HEAD")
    for rec in ({"head_sha": sha, "observed": "ok"}, {"head_sha": sha, "cmd": "t"}, {"cmd": "t", "observed": "ok"}):
        bad = repo / ".tmp" / "bad.json"
        bad.write_text(json.dumps(rec), encoding="utf-8")
        assert_clean_error(build_raw(repo, suite=bad))


def test_unparsed_prior_slice_line_warns_instead_of_silently_going_pending(repo):
    commit(repo, "feat(BT-11): first")
    prior = repo / ".tmp" / "prior.md"
    drifted = '  - {id: BT-11, summary: "drifted", audit_rounds: 2, verdict: PASS}'  # fields reordered
    prior.write_text(f"```stratos-pr\nfeature: BT-10\nslices:\n{drifted}\n```\n", encoding="utf-8")
    commit(repo, "feat(BT-12): second")
    r = build_raw(repo, "--prior-body-file", prior, suite=write_suite(repo))
    assert r.returncode == 0, r.stderr
    assert "[PR-BODY-WARN] unparsed prior slice line:" in r.stderr and "BT-11" in r.stderr


def test_missing_risk_paths_file_warns_that_risk_none_is_unverified(repo):
    commit(repo, "feat(BT-11): one")
    r = build_raw(repo, suite=write_suite(repo), risk=repo / "absent.md")
    assert r.returncode == 0, r.stderr
    assert "[PR-BODY-WARN] risk rules not found at" in r.stderr and "unverified" in r.stderr


def test_commit_scoped_to_the_parent_is_not_a_slice_or_closes_line(repo):
    commit(repo, "feat(BT-11): first")
    commit(repo, "fix(BT-10): touches the parent itself")
    body = build(repo, "BT-11")
    assert [s[0] for s in slices(body)] == ["BT-11"]
    assert "Closes #10." not in body
    assert "Closes #10." in build(repo, "BT-11", "--close-parent")


def test_parent_conflicting_with_prior_feature_warns_and_overrides(repo):
    commit(repo, "feat(BT-11): first")
    prior = repo / ".tmp" / "prior.md"
    prior.write_text("```stratos-pr\nfeature: BT-77\nslices:\n```\n", encoding="utf-8")
    r = build_raw(repo, "--prior-body-file", prior, "--parent", "BT-10", suite=write_suite(repo))
    assert r.returncode == 0, r.stderr
    assert "[PR-BODY-WARN] --parent BT-10 overrides prior feature BT-77" in r.stderr
    assert field(r.stdout, "feature") == "BT-10"
    same = repo / ".tmp" / "same.md"
    same.write_text("```stratos-pr\nfeature: BT-10\nslices:\n```\n", encoding="utf-8")
    assert "[PR-BODY-WARN]" not in build_raw(repo, "--prior-body-file", same, "--parent", "BT-10",
                                              suite=write_suite(repo)).stderr


@pytest.mark.parametrize("bad", ["136", "BT-", "bt-10", "BT-10x", "BT-1 0", ""])
def test_parent_must_look_like_bt_n_else_clean_exit_2(repo, bad):
    commit(repo, "feat(BT-11): one")
    r = build_raw(repo, "--parent", bad, suite=write_suite(repo))
    assert_clean_error(r)
    assert "--parent" in r.stderr


def test_close_parent_when_the_slice_is_the_parent_emits_one_closes_line(repo):
    commit(repo, "feat(BT-10): the whole feature")
    body = build(repo, "BT-10", "--close-parent", parent="BT-10")
    assert body.count("Closes #10.") == 1
    assert body.startswith("Closes #10.\n\n```stratos-pr\n")


def test_close_parent_dedup_keeps_closes_order(repo):
    commit(repo, "feat(BT-8): first")
    prior = repo / ".tmp" / "prior.md"
    prior.write_text(build(repo, "BT-8", parent="BT-10"), encoding="utf-8")
    commit(repo, "feat(BT-10): the parent as its own slice")
    body = build(repo, "BT-10", "--close-parent", prior=prior, parent="BT-10")
    assert body.splitlines()[:3] == ["Closes #8.", "Closes #10.", ""]


# --- base resolution (B1) ---------------------------------------------------------------------

def build_no_base(repo, *extra):
    return run(repo, "build", "--slice", "BT-11", "--summary", "s", "--verdict", "PASS", "--audit-rounds", "1",
               "--risk-paths", RISK_PATHS, "--suite-json", write_suite(repo), *extra)


def set_remote_head(repo, branch, sha):
    git(repo, "update-ref", f"refs/remotes/origin/{branch}", sha)
    git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", f"refs/remotes/origin/{branch}")


def test_base_defaults_to_the_remote_default_branch_on_a_develop_repo(develop_repo):
    set_remote_head(develop_repo, "develop", "develop")
    commit(develop_repo, "feat(BT-11): migration", ["db/migrations/001_init.sql"])
    r = build_no_base(develop_repo)
    assert r.returncode == 0, r.stderr
    assert field(r.stdout, "risk") == "[db-migration]", "risk must not silently become [none] on a non-main default"


def test_explicit_base_wins_over_the_remote_default_and_remote_default_over_main(repo):
    c1 = commit(repo, "feat(BT-11): migration", ["db/migrations/001_init.sql"])
    commit(repo, "feat(BT-12): later, clean", ["src/app.py"])
    set_remote_head(repo, "develop", c1)
    by_remote = build_no_base(repo)  # merge-base with origin/develop is c1, so the migration is outside <base>..HEAD
    assert by_remote.returncode == 0, by_remote.stderr
    assert field(by_remote.stdout, "risk") == "[none]"
    explicit = build_no_base(repo, "--base", "main")
    assert explicit.returncode == 0, explicit.stderr
    assert field(explicit.stdout, "risk") == "[db-migration]"


@pytest.mark.parametrize("default", ["main", "master"])
def test_base_falls_back_to_main_or_master_without_a_remote(tmp_path, default):
    repo = init_repo(tmp_path, default)
    commit(repo, "feat(BT-11): migration", ["db/migrations/001_init.sql"])
    r = build_no_base(repo)
    assert r.returncode == 0, r.stderr
    assert field(r.stdout, "risk") == "[db-migration]"


def test_unresolvable_base_fails_closed_and_names_the_fix(develop_repo):
    commit(develop_repo, "feat(BT-11): migration", ["db/migrations/001_init.sql"])
    r = build_no_base(develop_repo)
    assert_clean_error(r)
    assert "--base" in r.stderr
    fixed = build_no_base(develop_repo, "--base", "develop")
    assert fixed.returncode == 0, fixed.stderr
    assert field(fixed.stdout, "risk") == "[db-migration]"


def test_explicit_base_that_is_not_a_commit_fails_closed(repo):
    """A typo'd --base used to diff against nothing and report `risk: [none]` for a migration PR."""
    commit(repo, "feat(BT-11): migration", ["db/migrations/001_init.sql"])
    r = build_no_base(repo, "--base", "no-such-branch")
    assert_clean_error(r)
    assert "no-such-branch" in r.stderr and "--base" in r.stderr


# --- suite reuse (D3) -------------------------------------------------------------------------

def suite_out(repo):
    r = run(repo, "suite", "--dir", repo / ".tmp")
    return r.returncode, r.stdout


def test_suite_reused_on_exact_head_sha(repo):
    commit(repo, "feat(BT-11): one")
    write_suite(repo, cmd="pytest -q", observed="7 passed")
    rc, out = suite_out(repo)
    assert rc == 0
    assert json.loads(out) == {"cmd": "pytest -q", "observed": "7 passed", "head_sha": git(repo, "rev-parse", "HEAD")}


def test_suite_reused_across_release_only_commits(repo):
    c = commit(repo, "feat(BT-11): one")
    write_suite(repo, sha=c)
    commit(repo, "release: prepare v1.4.0")
    commit(repo, "release: prepare v1.4.1")
    rc, out = suite_out(repo)
    assert rc == 0 and json.loads(out)["head_sha"] == c


def test_suite_not_reused_when_any_other_commit_follows(repo):
    c = commit(repo, "feat(BT-11): one")
    write_suite(repo, sha=c)
    commit(repo, "release: prepare v1.4.0")
    commit(repo, "fix(BT-11): behaviour change")
    assert suite_out(repo) == (1, "")


def test_suite_not_reused_for_unknown_or_non_ancestor_sha(repo):
    commit(repo, "feat(BT-11): one")
    write_suite(repo, sha="deadbeef" * 5)
    assert suite_out(repo) == (1, "")
    git(repo, "checkout", "-q", "-b", "other", "main")
    other = commit(repo, "feat(BT-99): elsewhere")
    git(repo, "checkout", "-q", "feat/BT-10-x")
    commit(repo, "release: prepare v1.0.0")
    write_suite(repo, sha=other)
    assert suite_out(repo) == (1, "")


def test_suite_with_no_files_exits_1_silently(repo):
    assert suite_out(repo) == (1, "")


# --- suite reuse needs a clean tree (B2) ------------------------------------------------------

def dirty_tracked_readme(repo):
    (repo / "README.md").write_text("edited", encoding="utf-8")


def stage_readme(repo):
    dirty_tracked_readme(repo)
    git(repo, "add", "README.md")


def untracked_src(repo):
    (repo / "generated.txt").write_text("x", encoding="utf-8")


@pytest.mark.parametrize("dirty", [dirty_tracked_readme, stage_readme, untracked_src],
                         ids=["modified", "staged", "untracked"])
def test_suite_not_reused_when_the_tree_is_dirty_outside_the_ignored_dirs(repo, dirty):
    c = commit(repo, "feat(BT-11): one")
    write_suite(repo, sha=c)
    dirty(repo)
    assert suite_out(repo) == (1, "")


def test_suite_not_reused_across_a_release_commit_when_the_tree_is_dirty(repo):
    c = commit(repo, "feat(BT-11): one")
    write_suite(repo, sha=c)
    commit(repo, "release: prepare v1.4.0")
    untracked_src(repo)
    assert suite_out(repo) == (1, "")


def test_suite_not_reused_when_a_rename_moves_a_file_out_of_the_ignored_dirs(repo):
    commit(repo, "feat(BT-11): one", ["docs/a.md"])
    write_suite(repo)
    git(repo, "mv", "docs/a.md", "moved.md")
    assert suite_out(repo) == (1, "")


def test_suite_still_reused_when_only_memory_docs_and_tmp_drift(repo):
    c = commit(repo, "feat(BT-11): one", ["docs/prd.md", ".memory/notes.md"])
    write_suite(repo, sha=c)
    (repo / "docs" / "prd.md").write_text("edited", encoding="utf-8")  # tracked, modified
    (repo / ".memory" / "new.md").write_text("x", encoding="utf-8")  # untracked
    (repo / "docs" / "nightly").mkdir()
    (repo / "docs" / "nightly" / "n.md").write_text("x", encoding="utf-8")  # untracked dir
    (repo / ".tmp" / "scratch.log").write_text("x", encoding="utf-8")
    rc, out = suite_out(repo)
    assert rc == 0 and json.loads(out)["head_sha"] == c


def test_build_default_suite_lookup_exits_no_suite_on_a_dirty_tree(repo):
    commit(repo, "feat(BT-11): one")
    write_suite(repo)
    assert build_raw(repo).returncode == 0
    untracked_src(repo)
    r = build_raw(repo)
    assert r.returncode == 2 and "[NO-SUITE]" in r.stderr and not r.stdout


# --- BT-183: a scoped run is never "the suite"; the reason a record is not reusable is named ---------------------

SCOPED_CMDS = [
    "npx vitest run tests/ingestion/BT235_IngestionOfflineFallback.test.js tests/ingestion/BT164_StuttgartShootoutIngest.test.js",
    "python .agents/scripts/test_gate.py record -- python -m pytest -q tests/workflows tests/jules",
    "pytest tests/x.py::test_y", "pytest -k foo", "pytest -kfoo", "pytest -m slow", "pytest --ignore=tests/a",
    "pytest --last-failed", "vitest run --changed", "npx vitest run ingestion", "npm run test:ingestion",
    "pytest tests", "npm test -- src/lib", "bash -c 'npx vitest run src/lib'",
]
FULL_CMDS = [
    "pytest", "pytest -q", "python -m pytest -n 6 --dist worksteal", "python -m pytest -n auto -q -p no:cacheprovider",
    "bash scripts/check.sh", "npm test", "make test", "npx vitest run", "py -m pytest -q",
    "python .agents/scripts/test_gate.py record -- python -m pytest -q",
    "python .agents/scripts/test_gate.py record --suite BT-5 -- bash scripts/check.sh",
    "bash scripts/check.sh && python -m pytest tests/jules -q",
    "npm test && python .agents/scripts/validate_memory.py --path .memory",
    'bash -c "python -m pytest -q; bash scripts/check.sh"',
]


def suite_run(repo):
    return run(repo, "suite", "--dir", repo / ".tmp")


@pytest.mark.parametrize("cmd", SCOPED_CMDS)
def test_scoped_records_are_not_reusable(repo, cmd):
    c = commit(repo, "feat(BT-11): one")
    write_suite(repo, sha=c, cmd=cmd)
    r = suite_run(repo)
    assert (r.returncode, r.stdout) == (1, "")
    assert "[NO-SUITE] scoped" in r.stderr


@pytest.mark.parametrize("cmd", FULL_CMDS)
def test_full_suite_commands_stay_reusable(repo, cmd):
    c = commit(repo, "feat(BT-11): one")
    write_suite(repo, sha=c, cmd=cmd)
    r = suite_run(repo)
    assert r.returncode == 0 and json.loads(r.stdout)["cmd"] == cmd


def load_pr_body():
    spec = importlib.util.spec_from_file_location("pr_body_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_quoting_round_trip_gives_the_same_verdict_at_record_and_read_time():
    import shlex
    pb = load_pr_body()
    full = ["bash", "-c", "python -m pytest -q; bash scripts/check.sh"]
    scoped = ["bash", "-c", "npx vitest run src/lib"]
    assert pb.is_scoped(shlex.join(full)) is False
    assert pb.is_scoped(shlex.join(scoped)) is True


def test_no_suite_reasons_none_head_moved_dirty_tree_scoped(repo):
    assert "[NO-SUITE] none" in suite_run(repo).stderr
    c = commit(repo, "feat(BT-11): one")
    write_suite(repo, sha=c)
    commit(repo, "fix(BT-11): behaviour change")
    assert "[NO-SUITE] head moved" in suite_run(repo).stderr
    write_suite(repo)  # a record at the current HEAD
    untracked_src(repo)
    assert "[NO-SUITE] dirty tree" in suite_run(repo).stderr


def test_build_rejects_a_scoped_suite_json(repo):
    c = commit(repo, "feat(BT-11): one")
    scoped = write_suite(repo, "scoped.json", sha=c, cmd="pytest tests/x.py")
    r = build_raw(repo, suite=scoped)
    assert_clean_error(r)
    assert "scoped" in r.stderr


def test_build_no_suite_message_names_the_recorder(repo):
    commit(repo, "feat(BT-11): one")
    r = build_raw(repo)
    assert r.returncode == 2 and "[NO-SUITE]" in r.stderr
    assert "test_gate.py record --suite" in r.stderr and "none" in r.stderr


def test_suite_not_reused_across_a_docs_only_commit(repo):
    """Reuse is deliberately not widened: tests read docs/ and .memory/, so any new commit moves HEAD."""
    c = commit(repo, "feat(BT-11): one")
    write_suite(repo, sha=c)
    commit(repo, "docs(BT-11): notes", ["docs/notes.md"])
    assert suite_out(repo) == (1, "")


def test_pr_body_is_registered_like_contract_check():
    spec = importlib.util.spec_from_file_location("scaffold", REPO_ROOT / "src" / "scripts" / "scaffold.py")
    scaffold = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scaffold)
    placed = {rel for _, _, rel in scaffold.get_bundled_project_scripts(Path("proj"))}
    assert ".agents/scripts/pr_body.py" in placed, "scaffold must ship pr_body.py to .agents/scripts/"
    verify = (REPO_ROOT / "tests" / "runners" / "verify_scripts.py").read_text(encoding="utf-8")
    assert 'rel_str == "scripts/pr_body.py"' in verify and ".agents/scripts/pr_body.py" in verify


def write_backlog(repo, *rows):
    """Throwaway .memory/BACKLOG_MAP.md; each row is (id, labels)."""
    (repo / ".memory").mkdir(exist_ok=True)
    lines = ["| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | PR |", "|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {i} | t | open | {labels} | — | — | — | — | — |" for i, labels in rows]
    (repo / ".memory" / "BACKLOG_MAP.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_dropped_prior_row_is_kept_without_a_closes_line(repo):
    commit(repo, "feat(BT-11): first")
    commit(repo, "feat(BT-12): deferred then dropped")
    prior = repo / ".tmp" / "prior.md"
    prior.write_text("```stratos-pr\nfeature: BT-10\nslices:\n"
                     '  - {id: BT-12, summary: "closed not planned", verdict: DROPPED, audit_rounds: 2}\n```\n',
                     encoding="utf-8")
    commit(repo, "feat(BT-13): third")
    body = build(repo, "BT-13", prior=prior)
    by_id = {s[0]: s for s in slices(body)}
    assert by_id["BT-12"][2] == "DROPPED"
    assert "Closes #13." in body and "Closes #12." not in body


@pytest.mark.parametrize("map_id", ["BT-007", "BT-7"])
def test_epic_scoped_commit_adds_no_slice_row(repo, map_id):
    commit(repo, "feat(BT-11): first")
    commit(repo, "docs(BT-7): plan doc for the epic")
    write_backlog(repo, (map_id, "type:feature, tier:epic"), ("BT-11", "tier:slice"))
    body = build(repo, "BT-11")
    assert [s[0] for s in slices(body)] == ["BT-11"]
    assert "Closes #7." not in body


def test_epic_label_must_be_an_exact_token(repo):
    commit(repo, "feat(BT-11): first")
    commit(repo, "docs(BT-7): not an epic")
    write_backlog(repo, ("BT-7", "tier:epic-ish, xtier:epic, tier:slice"))
    assert [s[0] for s in slices(build(repo, "BT-11"))] == ["BT-7", "BT-11"]


def test_without_a_backlog_map_epic_commits_stay_pending(repo):
    commit(repo, "feat(BT-11): first")
    commit(repo, "docs(BT-7): plan doc")
    by_id = {s[0]: s for s in slices(build(repo, "BT-11"))}
    assert by_id["BT-7"][2] == "PENDING"


def test_shipped_slice_is_never_filtered_as_an_epic(repo):
    commit(repo, "feat(BT-11): first")
    write_backlog(repo, ("BT-11", "tier:epic"), ("BT-LOCAL-1", "tier:epic"))
    body = build(repo, "BT-11")
    assert [s[0] for s in slices(body)] == ["BT-11"] and "Closes #11." in body


def test_non_numeric_epic_ids_are_ignored_and_unreadable_map_fails_open(repo):
    commit(repo, "feat(BT-11): first")
    commit(repo, "docs(BT-7): plan doc")
    write_backlog(repo, ("BT-LOCAL-1", "tier:epic"))
    assert [s[0] for s in slices(build(repo, "BT-11"))] == ["BT-7", "BT-11"]
    (repo / ".memory" / "BACKLOG_MAP.md").write_bytes(b"\xff\xfe\x00bad")
    assert [s[0] for s in slices(build(repo, "BT-11"))] == ["BT-7", "BT-11"]


# --- --epic: name the epics explicitly, for a clone or CI without .memory/BACKLOG_MAP.md -----------------------

def test_epic_flag_drops_epic_commits_without_a_backlog_map(repo):
    commit(repo, "feat(BT-11): first")
    commit(repo, "docs(BT-7): plan doc for the epic")
    body = build(repo, "BT-11", "--epic", "BT-7")
    assert [s[0] for s in slices(body)] == ["BT-11"] and "Closes #7." not in body


def test_epic_flag_repeats_and_accepts_padded_ids(repo):
    commit(repo, "feat(BT-11): first")
    commit(repo, "docs(BT-7): plan doc")
    commit(repo, "docs(BT-8): other epic doc")
    body = build(repo, "BT-11", "--epic", "BT-007", "--epic", "BT-8")
    assert [s[0] for s in slices(body)] == ["BT-11"]


def test_epic_flag_adds_to_the_backlog_epics(repo):
    commit(repo, "feat(BT-11): first")
    commit(repo, "docs(BT-7): plan doc")
    commit(repo, "docs(BT-8): other epic doc")
    write_backlog(repo, ("BT-7", "tier:epic"))
    assert [s[0] for s in slices(build(repo, "BT-11", "--epic", "BT-8"))] == ["BT-11"]


def test_epic_flag_never_filters_the_shipped_slice(repo):
    commit(repo, "feat(BT-11): first")
    body = build(repo, "BT-11", "--epic", "BT-11")
    assert [s[0] for s in slices(body)] == ["BT-11"] and "Closes #11." in body


def test_epic_flag_rejects_a_malformed_id_cleanly(repo):
    commit(repo, "feat(BT-11): one")
    suite = write_suite(repo, "s.json")
    r = build_raw(repo, "--epic", "oops", suite=suite)
    assert_clean_error(r)
    assert "--epic" in r.stderr
