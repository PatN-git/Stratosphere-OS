"""BT-199: one GitHub-mode scenario, end to end, with no BACKLOG_MAP.md anywhere and no agent in the loop.

The deterministic spine of the lifecycle runs for real: a scaffold with `--tracker github`, the seeded upstream, issues
minted through the gh shim, the 3b assertions, the status moves 3d and 4a make, and 4a's documented combined
`reconcile.py` call read out of the workflow text. What an agent would say between those steps is not driven here: that
is the live run (`run-L3.py --tracker github --seed`), which spends model calls.
"""
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

from conftest import combined_gate_argv

HARNESS = Path(__file__).resolve().parent.parent / "lifecycle-harness"
REPO = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


e = _load("l3_env_scenario", HARNESS / "env.py")
a = _load("l3_assertions_scenario", HARNESS / "assertions.py")
gh = _load("l3_gh_scenario", HARNESS / "shims" / "gh_shim.py")

SLICE = "status:planned,type:feature,tier:slice,mode:AFK,size:small"


def _reconcile(env, argv):
    script = env.project / ".agents" / "scripts" / "reconcile.py"
    r = subprocess.run([sys.executable, str(script), *argv], cwd=str(env.project), env=env.child_env,
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def test_the_github_scenario_runs_end_to_end_with_no_map_file(monkeypatch):
    with e.lifecycle_env(REPO, scaffold=True, seed=True, tracker="github") as env:
        project, child = env.project, env.child_env
        monkeypatch.setenv("L3_GH_STORE", child["L3_GH_STORE"])

        # setup: no map, the backend recorded, the epic minted through the shim and nothing mirrored locally
        assert not (project / ".memory" / "BACKLOG_MAP.md").exists()
        assert re.search(r"^tracker: github$", (project / ".memory" / "ARCHITECTURE.md").read_text(encoding="utf-8"), re.M)
        before = a.snapshot(project, env.bare)
        assert before["backlog_md"] is None

        # 3b: two slices under the epic (BT-001), the second blocked by the first
        gh.main(["issue", "create", "--title", "Slice one", "--label", SLICE, "--milestone", "v1.0.0"])
        gh.main(["issue", "create", "--title", "Slice two", "--label", SLICE, "--milestone", "v1.0.0"])
        state = gh.load()
        epic, one, two = (state["issues"][n] for n in ("1", "2", "3"))
        for sl in (one, two):
            sl["parent"] = gh.brief(epic)
            epic["subIssues"].append(gh.brief(sl))
        two["blockedBy"] = [gh.brief(one)]
        gh.save(state)
        ctx = a.Context(project=project, child_env=child, store=Path(child["L3_GH_STORE"]), before=before,
                        tracker="github")
        problems, _ = a.check("3b", ctx)
        assert problems == [], problems

        # 3d: the slice goes in progress; 4a ships it
        gh.main(["issue", "edit", "2", "--remove-label", "status:planned", "--add-label", "status:in progress"])
        code, out = _reconcile(env, ["--ids", "BT-002", "--expect", "BT-002:status=in progress"])
        assert code == 0 and "[MIRROR-OK BT-002]" in out, out
        gh.main(["issue", "edit", "2", "--remove-label", "status:in progress", "--add-label", "status:done"])
        gh.main(["issue", "close", "2"])
        gh.main(["issue", "comment", "2", "--body", "Shipped in PR #9 — https://github.com/l3-harness/throwaway/pull/9"])
        gh.main(["issue", "edit", "1", "--remove-label", "status:planned", "--add-label", "status:in review"])

        # 4a: the documented combined call: gate + dependents from one fetch
        code, out = _reconcile(env, combined_gate_argv("BT-002", "BT-001"))
        assert code == 0, out
        assert "[MIRROR-OK BT-002,BT-001]" in out, out
        assert "[CLEAR BT-003 <- BT-002]" in out, out

        # ... the [CLEAR] edge is removed, then one re-check finds none left
        state = gh.load()
        state["issues"]["3"]["blockedBy"] = []
        gh.save(state)
        code, out = _reconcile(env, ["--edges", "dependents", "--ids", "BT-002,BT-001"])
        assert code == 0 and "[CLEAR" not in out, out

        assert not (project / ".memory" / "BACKLOG_MAP.md").exists(), "a phase recreated the map"


def test_env_only_github_has_no_map_file():
    with e.lifecycle_env(REPO, scaffold=True, tracker="github") as env:
        assert not (env.project / ".memory" / "BACKLOG_MAP.md").exists()
        assert (env.project / ".memory" / "ARCHITECTURE.md").exists()


def test_env_defaults_to_the_local_tracker_with_its_map():
    with e.lifecycle_env(REPO, scaffold=True) as env:
        assert (env.project / ".memory" / "BACKLOG_MAP.md").exists()
