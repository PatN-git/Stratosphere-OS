"""L3 Slice 1 - the run wrapper and the two checks it added to containment.

No agent and no network: every test here builds its own stub project or stub
validator, so the wrapper's failure paths are exercised without spending a run.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parent.parent / "lifecycle-harness"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


e = _load("l3_env_run", HARNESS / "env.py")
# The filename is not an identifier, so it can only be loaded by path.
r = _load("l3_run", HARNESS / "run-L3.py")

REPO = Path(__file__).resolve().parents[2]

# Enough environment to find the interpreter, and nothing else: the real
# caller passes a fully scrubbed environ, and an empty dict would fail on
# Windows for a reason that has nothing to do with what is under test.
CHILD = {"PATH": os.environ.get("PATH", ""),
         "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}


def _stub_project(tmp_path, exit_code, message="stub validator"):
    """A project shaped like a scaffold, with a validator that exits as told."""
    proj = tmp_path / "proj"
    scripts = proj / ".agents" / "scripts"
    scripts.mkdir(parents=True)
    (proj / ".memory").mkdir()
    (scripts / "validate_memory.py").write_text(
        f"import sys\nprint({message!r})\nsys.exit({exit_code})\n", encoding="utf-8")
    return proj


# --- E1: the working repo is part of the manifest, not just the HOME paths ----

def test_repo_status_is_empty_for_a_clean_repo(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
    assert e.repo_status(tmp_path) == ""


def test_repo_status_notices_an_untracked_file(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
    (tmp_path / "stray.md").write_text("written by the run", encoding="utf-8")
    assert "stray.md" in e.repo_status(tmp_path)


def test_watched_manifest_covers_the_working_repo_too(tmp_path):
    """E1 names four things; three of them live under HOME and one does not."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)

    before = e.watched_manifest(home, repo)
    assert any(str(repo) in k for k in before)

    (repo / "left-behind.txt").write_text("x", encoding="utf-8")
    drift = e.diff_manifest(before, e.watched_manifest(home, repo))
    assert drift and "left-behind.txt" in drift[0]


def test_a_repo_that_is_not_a_repo_does_not_crash_the_manifest(tmp_path):
    assert "git status failed" in e.repo_status(tmp_path / "nowhere")


# --- the scaffolded memory layer must validate before phase 1 -----------------

def test_memory_gate_passes_a_clean_project(tmp_path):
    e.assert_memory_valid(_stub_project(tmp_path, 0), CHILD)


def test_memory_gate_fails_on_errors_and_quotes_the_validator(tmp_path):
    proj = _stub_project(tmp_path, 1, message="ID collision: [[D-001]] twice")
    with pytest.raises(RuntimeError) as exc:
        e.assert_memory_valid(proj, CHILD)
    assert "exit 1" in str(exc.value)
    assert "ID collision" in str(exc.value)


def test_memory_gate_fails_on_warnings_too(tmp_path):
    """Exit 2 is warnings. A run that starts from a warning state will blame the
    lifecycle for something the scaffold brought with it."""
    proj = _stub_project(tmp_path, 2, message="one-way reference")
    with pytest.raises(RuntimeError) as exc:
        e.assert_memory_valid(proj, CHILD)
    assert "exit 2" in str(exc.value)


def test_memory_gate_names_a_missing_validator(tmp_path):
    proj = tmp_path / "empty"
    proj.mkdir()
    with pytest.raises(RuntimeError) as exc:
        e.assert_memory_valid(proj, CHILD)
    assert "validate_memory.py" in str(exc.value)


# --- the wrapper -------------------------------------------------------------

def test_keep_is_never_the_default():
    assert r.parse_args([]).keep is False
    assert r.parse_args(["--keep"]).keep is True


def test_repo_defaults_to_this_checkout():
    assert Path(r.parse_args([]).repo).resolve() == REPO


def test_preflight_refuses_a_directory_that_is_not_a_checkout(tmp_path):
    with pytest.raises(SystemExit) as exc:
        r.preflight(tmp_path)
    assert "not a StratOS checkout" in str(exc.value)


def test_preflight_accepts_this_checkout():
    r.preflight(REPO)          # must not raise


class _FakeEnv:
    def __init__(self, tmp_path, child_env=None, remote=None):
        self.root = tmp_path
        self.home = tmp_path / "home"
        self.project = tmp_path / "project"
        self.bare = tmp_path / "origin.git"
        self.child_env = child_env if child_env is not None else {"HOME": str(self.home)}
        subprocess.run(["git", "init", str(self.project)], capture_output=True, check=True)
        if remote:
            subprocess.run(["git", "-C", str(self.project), "remote", "add",
                            "origin", remote], capture_output=True, check=True)


def test_contained_run_passes(tmp_path):
    env = _FakeEnv(tmp_path, remote=str(tmp_path / "origin.git"))
    r.assert_contained(env)    # must not raise


def test_a_leaked_token_fails_the_run(tmp_path):
    env = _FakeEnv(tmp_path, remote=str(tmp_path / "origin.git"))
    env.child_env["GH_TOKEN"] = "ghp_real"
    with pytest.raises(RuntimeError) as exc:
        r.assert_contained(env)
    assert "GH_TOKEN" in str(exc.value)


def test_a_remote_outside_the_root_fails_the_run(tmp_path):
    env = _FakeEnv(tmp_path, remote="https://github.com/PatN-git/Stratosphere-OS.git")
    with pytest.raises(RuntimeError) as exc:
        r.assert_contained(env)
    assert "temp root" in str(exc.value)


def test_no_remote_at_all_fails_the_run(tmp_path):
    """`2a`/`2b` push by design. A project with no origin pushes wherever
    GIT_CONFIG_GLOBAL's pushDefault sends it, which is not something to assume."""
    env = _FakeEnv(tmp_path)
    with pytest.raises(RuntimeError) as exc:
        r.assert_contained(env)
    assert "no remote at all" in str(exc.value)


def test_a_failed_environment_exits_one_and_says_why(tmp_path, monkeypatch, capsys):
    import contextlib

    @contextlib.contextmanager
    def boom(*a, **kw):
        raise RuntimeError("refusing to start - a repository can push outside it")
        yield

    monkeypatch.setattr(r.env_mod, "lifecycle_env", boom)
    # --env-only so the failure under test is the environment, not a probe
    # for the CLI - and so no test can ever spend a model call.
    assert r.main(["--repo", str(REPO), "--env-only"]) == 1
    assert "push outside" in capsys.readouterr().out


# --- Slice 4: phase selection, and the cost that comes with it ----------------

def test_env_only_drives_nothing():
    """The free form. Everything else spends the driver plus, in five phases, the
    subagents the skills spawn, which inherit the driver's model."""
    assert r.parse_args(["--env-only"]).env_only is True
    assert r.parse_args([]).env_only is False


def test_phases_default_to_the_whole_chain():
    assert r.chosen_phases(r.parse_args([])) == list(r.prompts_mod.PHASES)


def test_a_subset_can_be_named():
    assert r.chosen_phases(r.parse_args(["--phases", "0a,1b"])) == ["0a", "1b"]


def test_an_unknown_phase_is_refused_before_anything_is_built():
    with pytest.raises(SystemExit) as exc:
        r.chosen_phases(r.parse_args(["--phases", "0a,9z"]))
    assert "9z" in str(exc.value)


def test_skip_research_drops_only_1a():
    """E4: dropping 1a does NOT make the lane egress-free."""
    phases = r.chosen_phases(r.parse_args(["--skip-research"]))
    assert "1a" not in phases and "1b" in phases


def test_the_models_are_pinned_per_role_not_inherited():
    args = r.parse_args([])
    assert args.model == r.session_mod.DRIVER_MODEL
    assert args.proxy_model == r.session_mod.PROXY_MODEL
    assert args.auditor_model == r.session_mod.AUDITOR_MODEL
    assert args.proxy_model != args.model


def test_the_budget_counts_turns_and_says_so():
    """1b batches: seven turns carried dozens of numbered questions."""
    assert r.parse_args([]).max_questions == 10
    assert r.parse_args([]).max_rounds == 2


# --- vendoring the one skill that is not bundled (fact 13) -------------------

def _stub_sync(tmp_path, exit_code, creates=None):
    """A stand-in for sync_skills.py: no network, and it does exactly as told."""
    make = (f"from pathlib import Path; Path({str(creates)!r})"
            ".mkdir(parents=True, exist_ok=True)") if creates else ""
    script = tmp_path / "sync_skills.py"
    script.write_text(f"""import sys
{make}
sys.exit({exit_code})
""", encoding="utf-8")
    return script


@pytest.mark.parametrize("base", e.SKILL_BASES)
def test_vendoring_accepts_either_host_destination(tmp_path, base):
    """sync_skills.py:364-375 picks the base by HOST, not from the registry's
    targetPath: `.claude/skills` under Claude Code, `.agents/skills` elsewhere.
    Checking only one made a successful vendor look like a silent miss."""
    proj = tmp_path / "proj"
    proj.mkdir()
    target = proj / Path(base) / "code-simplifier"
    e.vendor_skills(tmp_path, proj, CHILD,
                    script=_stub_sync(tmp_path, 0, creates=str(target)))
    assert e.vendored_at(proj, "code-simplifier") == target


def test_vendoring_fails_loudly_when_sync_skills_does(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    with pytest.raises(RuntimeError) as exc:
        e.vendor_skills(tmp_path, proj, CHILD, script=_stub_sync(tmp_path, 2))
    assert "exit 2" in str(exc.value)


def test_vendoring_fails_when_it_reports_success_but_installs_nothing(tmp_path):
    """The Slice 0 lesson: a swallowed failure looks exactly like success until a
    phase behaves oddly for no visible reason."""
    proj = tmp_path / "proj"
    proj.mkdir()
    with pytest.raises(RuntimeError) as exc:
        e.vendor_skills(tmp_path, proj, CHILD, script=_stub_sync(tmp_path, 0))
    assert "code-simplifier" in str(exc.value)
    assert "3d:38" in str(exc.value)


def test_a_missing_sync_skills_says_to_build_first(tmp_path):
    with pytest.raises(RuntimeError) as exc:
        e.vendor_skills(tmp_path, tmp_path, CHILD, script=tmp_path / "nope.py")
    assert "build first" in str(exc.value)


# --- teardown must actually remove things, not report that it did -------------

def test_teardown_removes_read_only_files(tmp_path):
    """git writes its object and pack files read-only, so a plain rmtree is
    refused on Windows - and `ignore_errors=True` reports success anyway."""
    root = tmp_path / "root"
    (root / "objects").mkdir(parents=True)
    obj = root / "objects" / "pack.idx"
    obj.write_text("x", encoding="utf-8")
    os.chmod(obj, 0o444)

    e._teardown(root, keep=False)
    assert not root.exists()


def test_keep_leaves_it_and_says_where(tmp_path, capsys):
    root = tmp_path / "root"
    root.mkdir()
    e._teardown(root, keep=True)
    assert root.exists()
    assert str(root) in capsys.readouterr().out


# --- the transcript, which is evidence rather than an assertion ---------------

class _Turn:
    def __init__(self, text, tools=()):
        self.text = text
        self.tool_uses = [{"name": t} for t in tools]


class _Chat:
    def __init__(self, turns):
        self.turns = turns


class _Env:
    def __init__(self, root):
        self.root = root


def test_a_transcript_is_written_for_every_phase(tmp_path):
    """`4a produced none of the verdict tokens` is not diagnosable without the turn
    that was supposed to carry one."""
    env = _Env(tmp_path)
    path = r.write_transcript(env, "4a", _Chat([
        _Turn("Auditing the slice.", tools=["Read", "Bash"]),
        _Turn("Coverage map complete. L3-4A-COMPLETE")]))
    text = path.read_text(encoding="utf-8")
    assert path == tmp_path / "logs" / "4a.log"
    assert "turn 1" in text and "turn 2" in text
    assert "Bash, Read" in text
    assert "L3-4A-COMPLETE" in text


def test_a_phase_with_no_turns_writes_nothing(tmp_path):
    assert r.write_transcript(_Env(tmp_path), "0a", _Chat([])) is None


def test_the_tail_is_what_gets_printed_on_failure(tmp_path):
    log = tmp_path / "x.log"
    log.write_text("\n".join(f"line {i}" for i in range(50)), encoding="utf-8")
    shown = r.tail(log, lines=3)
    assert shown.count("\n") == 2
    assert "line 49" in shown and "line 46" not in shown
