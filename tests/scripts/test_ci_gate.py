"""BT-187: `ci_gate.py` runs the project's CI checks locally (`parity`), triages a red PR (`status`) and caps a CI fix (`cap`).

Seams: `select_steps` / `parse_yaml` (pure), `main(argv)` for the CLI contract (exit code + JSON) inside a throwaway
git repo, and `status` with `gh` and the clock injected. Steps that really run are tiny `bash scripts/*.sh` files so no
package manager is touched.
"""
import json
import sys
import textwrap

import pytest

from conftest import REPO_ROOT, commit, git

SCRIPTS = REPO_ROOT / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import ci_gate  # noqa: E402


def wf(steps, on="pull_request", job_extra=""):
    body = "".join(f"      - name: {n}\n        {k}: {v}\n" for n, r in steps
                   for k, v in [("uses", r[5:].strip()) if r.startswith("uses:") else ("run", r)])
    return f"name: ci\non: {on}\njobs:\n  t:\n    runs-on: ubuntu-latest\n{job_extra}    steps:\n{body}"


def reasons(skipped):
    return {s["name"]: s["reason"] for s in skipped}


# --- reader and selection -------------------------------------------------------------------------------------

@pytest.mark.parametrize("on", [
    "pull_request",
    "[push, pull_request]",
    "\n  push:\n    branches: [main]\n  pull_request:\n",
    "\n  pull_request:\n    branches: [main]\n",
])
def test_on_shapes_all_select_a_pull_request_job(on):
    selected, _ = ci_gate.select_steps(wf([("Test", "bash scripts/t.sh")], on=on), "ci.yml")
    assert [s["name"] for s in selected] == ["Test"]


@pytest.mark.parametrize("on", ["push", "[push, schedule]", "\n  schedule:\n    - cron: '0 0 * * *'\n"])
def test_jobs_not_on_pull_request_are_out(on):
    selected, skipped = ci_gate.select_steps(wf([("Test", "bash scripts/t.sh")], on=on), "ci.yml")
    assert selected == [] and skipped == []


def test_selection_keeps_repo_checks_and_reports_every_skip_with_a_reason():
    text = wf([
        ("Checkout", "uses: actions/checkout@v4"),
        ("Install", "npm ci"),
        ("Unit", "pytest -q"),
        ("Guard", "python scripts/guard.py"),
        ("Lint", "bash scripts/lint.sh"),
        ("Secret", "echo ${{ secrets.TOKEN }}"),
        ("Deploy", "bash scripts/deploy.sh"),
        ("Matrix", "python x.py ${{ matrix.v }}"),
        ("Pip", "pip install pytest"),
        ("Echo", "echo hello"),
    ])
    selected, skipped = ci_gate.select_steps(text, "ci.yml")
    assert [s["name"] for s in selected] == ["Install", "Unit", "Guard", "Lint"]
    r = reasons(skipped)
    assert "uses" in r["Checkout"]
    assert "expression" in r["Secret"] and "expression" in r["Matrix"]
    assert "deploy" in r["Deploy"]
    assert "install" in r["Pip"]
    assert "not a project check" in r["Echo"]


def test_skip_wins_over_allow():
    selected, skipped = ci_gate.select_steps(wf([("Pip", "python -m pip install pytest pytest-xdist")]), "ci.yml")
    assert selected == [] and "install" in reasons(skipped)["Pip"]


@pytest.mark.parametrize("extra,why", [
    ("    services:\n      db:\n        image: postgres\n", "services"),
    ("    defaults:\n      run:\n        working-directory: app\n", "defaults.run"),
    ("    if: github.event.pull_request.draft == false\n", "if:"),
])
def test_unsupported_job_constructs_skip_every_step_of_the_job(extra, why):
    selected, skipped = ci_gate.select_steps(wf([("Unit", "pytest -q")], job_extra=extra), "ci.yml")
    assert selected == [] and why in reasons(skipped)["Unit"]


def test_pr_true_if_is_kept_and_other_if_is_skipped():
    text = ("on: pull_request\njobs:\n  t:\n    steps:\n"
            "      - name: Bump\n        if: github.event_name == 'pull_request'\n        run: python build/bump_guard.py .\n"
            "      - name: Push only\n        if: github.event_name == 'push'\n        run: python build/other.py\n")
    selected, skipped = ci_gate.select_steps(text, "ci.yml")
    assert [s["name"] for s in selected] == ["Bump"]
    assert "if:" in reasons(skipped)["Push only"]


def test_block_scalar_runs_are_kept_whole():
    text = ("on: pull_request\njobs:\n  t:\n    steps:\n      - name: Drift\n        run: |\n"
            "          DRIFT=\"$(git status --porcelain dist/)\"\n          if [ -n \"$DRIFT\" ]; then\n            exit 1\n          fi\n"
            "          bash scripts/ok.sh\n")
    selected, _ = ci_gate.select_steps(text, "ci.yml")
    assert len(selected) == 1 and selected[0]["run"].count("\n") == 4 and "exit 1" in selected[0]["run"]


def test_this_repos_build_guard_workflow_is_understood():
    text = (REPO_ROOT / ".github" / "workflows" / "build-guard.yml").read_text(encoding="utf-8")
    selected, skipped = ci_gate.select_steps(text, "build-guard.yml")
    runs = [s["run"] for s in selected]
    assert "python build/build.py" in runs and "python build/validate.py ." in runs
    assert any(r.startswith("python -m pytest") for r in runs)
    assert "python build/bump_guard.py ." in runs, "the PR-only bump guard has a PR-true `if:`"
    assert "install" in reasons(skipped)["Install pytest"]
    assert any("uses" in r for r in reasons(skipped).values())


# --- the CLI: parity ------------------------------------------------------------------------------------------

def make_repo(tmp_path, workflow, scripts=None):
    git(tmp_path, "init", "-b", "main")
    files = {".github/workflows/ci.yml": workflow, "README.md": "x\n"}
    files.update({f"scripts/{n}": body for n, body in (scripts or {}).items()})
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-m", "chore: base")
    return git(tmp_path, "rev-parse", "HEAD")


def parity(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    code = ci_gate.main(["parity"])
    out = capsys.readouterr().out
    return code, json.loads(out)


def need_bash():
    if ci_gate.find_bash() is None:
        pytest.skip("no usable bash on this host")


def test_parity_pass_runs_selected_steps_in_order(tmp_path, monkeypatch, capsys):
    need_bash()
    make_repo(tmp_path, wf([("One", "bash scripts/one.sh"), ("Two", "bash scripts/two.sh")]),
              {"one.sh": "echo 1 >> order.log\n", "two.sh": "echo 2 >> order.log\n"})
    code, out = parity(tmp_path, monkeypatch, capsys)
    assert code == 0 and out["verdict"] == "pass"
    assert [s["status"] for s in out["steps"]] == ["pass", "pass"]
    assert (tmp_path / "order.log").read_text().split() == ["1", "2"]


def test_parity_stops_at_the_first_failing_step_exit_1(tmp_path, monkeypatch, capsys):
    need_bash()
    make_repo(tmp_path, wf([("Bad", "bash scripts/bad.sh"), ("After", "bash scripts/after.sh")]),
              {"bad.sh": "exit 3\n", "after.sh": "echo ran > after.log\n"})
    code, out = parity(tmp_path, monkeypatch, capsys)
    assert code == 1 and out["verdict"] == "fail"
    assert [s["name"] for s in out["steps"]] == ["Bad"] and out["steps"][0]["status"] == "fail"
    assert not (tmp_path / "after.log").exists()


def test_parity_pipefail_fails_a_block_like_actions_does(tmp_path, monkeypatch, capsys):
    need_bash()
    make_repo(tmp_path, wf([("Blk", "|\n          bash scripts/bad.sh\n          bash scripts/ok.sh")]),
              {"bad.sh": "exit 1\n", "ok.sh": "exit 0\n"})
    code, out = parity(tmp_path, monkeypatch, capsys)
    assert code == 1 and out["verdict"] == "fail", "bash -e: a failing first line must fail the block"


def test_parity_no_workflow_is_none_and_runs_nothing(tmp_path, monkeypatch, capsys):
    git(tmp_path, "init", "-b", "main")
    commit(tmp_path, "chore: base")
    code, out = parity(tmp_path, monkeypatch, capsys)
    assert code == 0 and out["verdict"] == "none" and out["steps"] == []


def test_parity_nothing_selectable_is_none(tmp_path, monkeypatch, capsys):
    make_repo(tmp_path, wf([("Co", "uses: actions/checkout@v4")]))
    code, out = parity(tmp_path, monkeypatch, capsys)
    assert code == 0 and out["verdict"] == "none" and out["skipped"]


def test_parity_cannot_run_when_no_bash_exit_2(tmp_path, monkeypatch, capsys):
    make_repo(tmp_path, wf([("One", "bash scripts/one.sh")]), {"one.sh": "exit 0\n"})
    monkeypatch.setattr(ci_gate, "find_bash", lambda: None)
    code, out = parity(tmp_path, monkeypatch, capsys)
    assert code == 2 and out["verdict"] == "cannot_run" and "bash" in out["reason"]


def test_parity_a_step_that_changes_a_tracked_file_halts_as_tree_changed(tmp_path, monkeypatch, capsys):
    need_bash()
    make_repo(tmp_path, wf([("Regen", "bash scripts/regen.sh")]), {"regen.sh": "echo changed > README.md\n"})
    code, out = parity(tmp_path, monkeypatch, capsys)
    assert code == 1 and out["verdict"] == "fail" and out["reason"] == "tree changed" and out["changed"] == ["README.md"]


def test_parity_reuses_a_full_suite_record_for_the_same_head_and_runner(tmp_path, monkeypatch, capsys):
    need_bash()
    head = make_repo(tmp_path, wf([("Suite", "bash scripts/check.sh")]), {"check.sh": "exit 1\n"})
    code, out = parity(tmp_path, monkeypatch, capsys)
    assert code == 1, "without a record the failing suite step runs and fails"
    rec = {"cmd": "bash scripts/check.sh", "observed": "1 passed", "head_sha": head}
    (tmp_path / ".tmp").mkdir()
    (tmp_path / ".tmp" / "3d-suite-BT-1.json").write_text(json.dumps(rec), encoding="utf-8")
    code, out = parity(tmp_path, monkeypatch, capsys)
    assert code == 0 and [s["status"] for s in out["steps"]] == ["covered"]


def test_a_recorded_pytest_run_never_covers_a_jest_step(tmp_path, monkeypatch, capsys):
    need_bash()
    head = make_repo(tmp_path, wf([("Suite", "jest")]), {})
    rec = {"cmd": "python -m pytest -q", "observed": "1 passed", "head_sha": head}
    (tmp_path / ".tmp").mkdir()
    (tmp_path / ".tmp" / "3d-suite-BT-1.json").write_text(json.dumps(rec), encoding="utf-8")
    assert ci_gate.covered_by_suite("jest", rec) is False
    assert ci_gate.covered_by_suite("python -m pytest -n auto --dist worksteal", rec) is True


@pytest.mark.parametrize("which,git_bash,expected", [
    (r"C:\Windows\System32\bash.exe", None, None),
    (r"C:\Windows\System32\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"),
    ("/usr/bin/bash", None, "/usr/bin/bash"),
    (None, None, None),
])
def test_pick_bash_prefers_git_bash_and_rejects_the_wsl_launcher(which, git_bash, expected):
    assert ci_gate.pick_bash(which, git_bash) == expected
