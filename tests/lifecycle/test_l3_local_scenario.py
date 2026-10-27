"""BT-221: one local-tracker scenario, end to end, with no agent in the loop.

The deterministic spine runs for real against the installed bundle: a scaffold with `--tracker local`, the seeded epic,
then every local verb through `.agents/scripts/issues.py` (create, ready, claim, comment, close, get), a store write from
a feature branch read back on the default branch with no merge, `issues.py check`, and the `tracker_switch.py` dry run through the gh
shim. The issue files live on the tracker branch only: the project's working tree never shows one. What an agent says
between those steps is the live run (`run-L3.py --seed`), which spends model calls.
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent / "lifecycle-harness"
REPO = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


e = _load("l3_env_local_scenario", HARNESS / "env.py")
a = _load("l3_assertions_local_scenario", HARNESS / "assertions.py")

SLICE = "type:feature,tier:slice,mode:AFK,size:small"
BODY = ("### Overview\n{title}.\n\n### ICE Priorities\n- **Impact:** 1.0\n- **Confidence:** 80%\n\n"
        "### Acceptance Criteria (Verifiable)\n- [ ] {title} works\n")


def _script(env, name, *argv):
    r = subprocess.run([sys.executable, str(env.project / ".agents" / "scripts" / name), *argv],
                       cwd=str(env.project), env=env.child_env, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def _issues(env, *argv):
    code, out = _script(env, "issues.py", *argv)
    assert code == 0, f"issues.py {argv}: {out}"
    return out


def _git(env, *argv):
    return subprocess.run(["git", "-C", str(env.project), *argv], env=env.child_env, capture_output=True,
                          text=True, check=True).stdout


def _body(env, title):
    p = env.root / (re.sub(r"\W+", "-", title) + ".md")
    p.write_text(BODY.format(title=title), encoding="utf-8")
    return str(p)


def _ready_ids(env):
    return {ln.split(" |", 1)[0] for ln in _issues(env, "ready").splitlines() if ln and not ln.startswith("[")}


def test_the_local_scenario_runs_end_to_end_on_the_tracker_branch():
    with e.lifecycle_env(REPO, scaffold=True, seed=True, tracker="local") as env:
        arch = (env.project / ".memory" / "ARCHITECTURE.md").read_text(encoding="utf-8")
        assert re.search(r"^tracker: local$", arch, re.M)
        branch = re.search(r"^tracker_branch: (\S+)$", arch, re.M).group(1)
        assert branch == _issues(env, "branch") == "throwaway/issues"
        epic = e._seed.LOCAL_EPIC_ID
        assert json.loads(_issues(env, "get", epic))["status"] == "planned"

        # 3b: two slices under the seeded epic, the second blocked by the first
        one = _issues(env, "create", "--title", "Ruleset parsing", "--label", SLICE, "--milestone", "v1.0.0",
                      "--parent", epic, "--body-file", _body(env, "Ruleset parsing"))
        two = _issues(env, "create", "--title", "Flag evaluation", "--label", SLICE, "--milestone", "v1.0.0",
                      "--parent", epic, "--blocked-by", one, "--body-file", _body(env, "Flag evaluation"))
        assert one == "BT-LOCAL-ruleset-parsing" and two == "BT-LOCAL-flag-evaluation"
        assert _issues(env, "check").startswith("[CHECK-OK")

        # 3c/3z: only the unblocked slice is ready; 3d claims it, a second holder is refused
        assert _ready_ids(env) == {one}
        _issues(env, "claim", one, "--by", "feature/BT-LOCAL-ruleset-parsing")
        code, out = _script(env, "issues.py", "claim", one, "--by", "someone-else")
        assert code == 1 and f"[CLAIMED {one} by feature/BT-LOCAL-ruleset-parsing]" in out, out
        assert [i["id"] for i in json.loads(_issues(env, "wip"))] == [one]

        # 4a: the auditor reads the Acceptance Criteria from the store; the ship comments and closes
        got = json.loads(_issues(env, "get", one))
        assert "### Acceptance Criteria" in got["body"] and "- [ ] Ruleset parsing works" in got["body"]
        _issues(env, "comment", one, "--body", "Shipped on feature/BT-LOCAL-ruleset-parsing")
        _issues(env, "close", one)
        got = json.loads(_issues(env, "get", one))
        assert got["status"] == "done" and any("Shipped on" in c for c in got["comments"])
        assert _ready_ids(env) == {two}

        # one state on every branch: a write from a feature branch is read on main with no merge
        main = _git(env, "branch", "--show-current").strip()  # the seeded default branch
        _git(env, "checkout", "-q", "-b", "feature/BT-LOCAL-flag-evaluation")
        three = _issues(env, "create", "--title", "Follow-up from the branch", "--label", SLICE,
                        "--body-file", _body(env, "Follow-up from the branch"))
        assert _git(env, "rev-parse", "HEAD") == _git(env, "rev-parse", main), "the write committed to the branch"
        _git(env, "checkout", "-q", main)
        assert three in {i["id"] for i in json.loads(_issues(env, "list"))}

        # the store never reaches the working tree or a feature branch; it stays coherent
        assert _git(env, "status", "--porcelain") == ""
        assert not (env.project / "docs" / "issues").exists()
        assert "docs/issues" not in _git(env, "ls-tree", "-r", "--name-only", main)
        assert _issues(env, "check").startswith("[CHECK-OK")
        assert not list(a.backlog_maps(env.project))

        # tracker_switch dry run (gh shim): one create planned per BT-LOCAL issue, nothing written
        code, out = _script(env, "tracker_switch.py")
        assert code == 0, out
        planned = set(re.findall(r"^\[PLAN create (BT-LOCAL-\S+?):", out, re.M))
        assert planned == {epic, one, two, three}, out
        assert "dry run, 4 issue(s) to create" in out, out
        assert _git(env, "status", "--porcelain") == ""


def test_env_defaults_to_the_local_tracker_on_its_issues_branch():
    with e.lifecycle_env(REPO, scaffold=True) as env:
        arch = (env.project / ".memory" / "ARCHITECTURE.md").read_text(encoding="utf-8")
        assert re.search(r"^tracker: local$", arch, re.M)
        assert re.search(r"^tracker_branch: throwaway/issues$", arch, re.M)
        assert _git(env, "ls-tree", "-r", "--name-only", "throwaway/issues").splitlines() == ["docs/issues/README.md"]
        assert not list(a.backlog_maps(env.project))
