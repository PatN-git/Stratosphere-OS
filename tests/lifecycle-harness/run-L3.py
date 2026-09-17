#!/usr/bin/env python3
"""L3 - build a contained throwaway, drive the lifecycle through it, remove it.

    python tests/lifecycle-harness/run-L3.py --env-only     # no agent, no cost
    python tests/lifecycle-harness/run-L3.py                # drive every phase
    python tests/lifecycle-harness/run-L3.py --phases 0a,1b # drive a subset
    python tests/lifecycle-harness/run-L3.py --keep         # keep it to inspect

**`--env-only` is free and drives nothing.** Every other form spends real model
calls: the driver plus, in five of the phases, the subagents the skills spawn, which
inherit the driver's model and are not pinnable (plan, section 6).

Four things are proven before the first phase starts:

  E1  Nothing that could authenticate to a real GitHub reaches the child, and the
      developer's `~/.claude`, `~/.gemini`, `~/.config/devin` and working repo are
      the same after the run as before it.
  E4  `gh` resolves to the shim, checked from inside a child carrying the run's
      environment - not from here, where the answer would be different.
  E7  Every repository under the temp root pushes into the temp root or nowhere.
      `2a`, `2b` and `3a` push their generated document unprompted, using plain
      `git push`, which no `gh` shim can intercept.
  E2  The environment is removed on success, on failure and on signal. A run that
      cannot guarantee that refuses to start.

And the project is scaffolded AND its `.memory/` passes `validate_memory.py`: the
first full-depth Slice 0 run drove `1b` against a project with no `.agents/` at all,
because a swallowed argparse failure looked like success.

Exit 0 = every driven phase reached its sentinel and its assertions passed.
Exit 1 = a phase or an assertion failed; the message names which.
Exit 2 = refused to start, or `claude` is unavailable, so nothing was proven.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(f"l3_{name}", HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"l3_{name}"] = mod
    spec.loader.exec_module(mod)
    return mod


env_mod = _load("env")
prompts_mod = _load("prompts")
assertions_mod = _load("assertions")
driver_mod = _load("driver")
responder_mod = _load("responder")
session_mod = _load("session")


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="Drive the StratOS lifecycle through a contained throwaway.")
    ap.add_argument("--repo", default=str(REPO),
                    help="repo root to build StratOS from (default: this checkout)")
    ap.add_argument("--keep", action="store_true",
                    help="keep the temp root on exit and print its path")
    ap.add_argument("--env-only", action="store_true",
                    help="build and prove the environment, drive no phase (free)")
    ap.add_argument("--login", action="store_true",
                    help="authenticate the harness's OWN credential store "
                         "interactively, so runs never consume your CLI session")
    ap.add_argument("--phases", default=",".join(prompts_mod.PHASES),
                    help="comma-separated subset of "
                         f"{','.join(prompts_mod.PHASES)}")
    ap.add_argument("--skip-research", action="store_true",
                    help="drop 1a; the lane is still not egress-free (E4)")
    ap.add_argument("--handoff", action="store_true",
                    help="test the CHAIN, not the depth of each phase: fewer turns, "
                         "one round, a per-phase wall-clock budget, and 1b's "
                         "sufficiency auditor demoted to advisory")
    ap.add_argument("--max-questions", type=int, default=None,
                    help="agent TURNS per round, not questions - 1b batches "
                         "(default 10, or 3 with --handoff)")
    ap.add_argument("--max-rounds", type=int, default=None,
                    help="default 2, or 1 with --handoff")
    ap.add_argument("--phase-budget", type=float, default=None,
                    help="seconds per phase before it fails by name "
                         "(default none, or 600 with --handoff)")
    ap.add_argument("--model", default=session_mod.DRIVER_MODEL,
                    help="the agent under test; calibration is model-specific")
    ap.add_argument("--proxy-model", default=session_mod.PROXY_MODEL)
    ap.add_argument("--auditor-model", default=session_mod.AUDITOR_MODEL)
    args = ap.parse_args(argv)
    # Hand-off defaults, applied only where nothing was asked for explicitly, so
    # `--handoff --max-questions 6` means what it says.
    if args.max_questions is None:
        args.max_questions = 3 if args.handoff else 10
    if args.max_rounds is None:
        args.max_rounds = 1 if args.handoff else 2
    if args.phase_budget is None and args.handoff:
        args.phase_budget = 600.0
    return args


def chosen_phases(args) -> list[str]:
    wanted = [p.strip() for p in args.phases.split(",") if p.strip()]
    unknown = [p for p in wanted if p not in prompts_mod.PHASES]
    if unknown:
        raise SystemExit(f"[refused] no such phase(s): {', '.join(unknown)}")
    if args.skip_research:
        wanted = [p for p in wanted if p != "1a"]
    return wanted


def preflight(repo_root: Path) -> None:
    """Refuse to start rather than half-start (E2).

    Teardown is an `rmtree` of a directory under the OS temp dir. If that directory
    cannot be created here, nothing later can guarantee its removal, and a harness
    that leaves residue is worse than one that does not run.
    """
    if not (repo_root / "build" / "build.py").is_file():
        raise SystemExit(f"[refused] {repo_root} is not a StratOS checkout "
                         "(no build/build.py)")
    try:
        probe = Path(tempfile.mkdtemp(prefix="l3-preflight-"))
    except OSError as exc:
        raise SystemExit(f"[refused] cannot create a temp root under "
                         f"{tempfile.gettempdir()}: {exc}")
    probe.rmdir()


def assert_contained(env) -> None:
    """The containment facts a phase would otherwise take on trust."""
    leaked = sorted(k for k in env.child_env if k.startswith(("GH_", "GITHUB_")))
    if leaked:
        raise RuntimeError(
            "GitHub credentials survived the scrub and would reach the agent "
            "(E1): " + ", ".join(leaked))
    if env.child_env.get("HOME") != str(env.home):
        raise RuntimeError(
            f"the child's HOME is {env.child_env.get('HOME')}, not the temp home "
            f"{env.home} (E1)")
    remotes = env_mod.git_remotes(env.project / ".git")
    outside = [r for r in remotes if str(env.root) not in r]
    if not remotes or outside:
        raise RuntimeError(
            f"the project's origin does not resolve into the temp root (E7): "
            f"{remotes or '<no remote at all>'}")


def run_phase(phase: str, env, args, proxy, auditor) -> list[str]:
    """Drive one phase and assert what it left. Returns its problems."""
    before = assertions_mod.snapshot(env.project, env.bare)
    responder = responder_mod.Responder(
        fixture=(HERE / "fixture" / "topic.md").read_text(encoding="utf-8"),
        proxy=proxy, max_questions=args.max_questions, max_rounds=args.max_rounds)
    chat = session_mod.ClaudeSession(cwd=env.project, env=env.child_env,
                                     model=args.model)

    # Only `1b` hands in a `settle`: its sentinel is necessary but not sufficient,
    # because the first full-depth run printed it in three replies with a brief
    # nobody had audited. Elsewhere the sentinel plus the assertions are the gate.
    #
    # In hand-off mode the auditor is advisory. A three-turn grill SHOULD produce a
    # thin brief, and failing the run for that would be testing depth - the one
    # thing this mode deliberately does not test. The verdict is still taken and
    # still printed; it just does not reopen the phase or fail it.
    settle = (_brief_settle(env, auditor, advisory=args.handoff)
              if phase == "1b" else None)

    print(f"\n=== {phase} " + "=" * (60 - len(phase)))
    run = driver_mod.drive(phase, prompts_mod.load(phase, handoff=args.handoff),
                           prompts_mod.sentinel(phase), chat, responder, settle,
                           budget=args.phase_budget)

    tool_uses = [t for turn in run.turns for t in turn.tool_uses]
    ctx = assertions_mod.Context(
        project=env.project, child_env=env.child_env,
        store=Path(env.child_env["L3_GH_STORE"]), bare=env.bare,
        tool_uses=tool_uses, before=before, handoff=args.handoff,
        final_text=run.last.text if run.last else "")
    problems, notes = assertions_mod.check(phase, ctx)
    for note in notes:
        print(f"[note] {phase}: {note}")
    for problem in problems:
        print(f"[FAIL] {phase}: {problem}")
    if not problems:
        print(f"[ok]   {phase}: {run.replies} replies, {run.rounds} round(s), "
              f"assertions passed")
    return problems


def _brief_settle(env, auditor, advisory: bool = False):
    def settle():
        brief = assertions_mod.only(env.project, "docs/discovery/*.md")
        if brief is None:
            return None
        ok, gaps = auditor.judge(brief.read_text(encoding="utf-8"))
        if advisory and not ok:
            for gap in gaps:
                print(f"[note] 1b: the auditor would have reopened this: {gap}")
            return True, []
        return ok, gaps
    return settle


def login() -> int:
    """Authenticate the harness's own credential store, interactively.

    The harness never handles the credentials: this hands the CLI a HOME of its
    own and gets out of the way, so the sign-in happens between the developer and
    the CLI exactly as it normally would. What it buys is separation - after this,
    a run refreshes the HARNESS's token rather than consuming the developer's.
    """
    store = env_mod.HARNESS_STORE
    home = env_mod.HARNESS_HOME
    home.mkdir(parents=True, exist_ok=True)
    child = dict(os.environ)
    child.update({"HOME": str(home), "USERPROFILE": str(home)})
    cmd = session_mod._base_cmd() + ["auth", "login"]
    print(f"[login] authenticating the harness store at {store}")
    print(f"[login] {' '.join(cmd)}")
    completed = subprocess.run(cmd, env=child)
    if completed.returncode != 0 or not env_mod._usable(store):
        print("[login] the CLI did not leave a usable credential in the store")
        return 1
    print("[login] done - runs will now refresh this store, not your own session")
    return 0


def preflight_credentials(phases) -> int | None:
    """Fail in seconds with the fix, rather than after building everything."""
    if not phases:
        return None
    if env_mod.credentials_source(Path(os.path.expanduser("~"))) is not None:
        return None
    print("[refused] no usable Claude credential to give the run.\n"
          "  The temp HOME hides the CLI's own credentials, so a run with none dies\n"
          "  mid-phase looking like a driver bug. Authenticate the harness's own\n"
          "  store once:\n\n"
          "      python tests/lifecycle-harness/run-L3.py --login\n\n"
          "  A run refreshes whatever credential it is given, and the provider\n"
          "  ROTATES the refresh token when it does. That is why the harness keeps\n"
          "  its own: a run that borrowed yours would invalidate your CLI session\n"
          "  the moment a refresh fell due.")
    return 2


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.login:
        return login()
    repo_root = Path(args.repo).resolve()
    preflight(repo_root)
    phases = [] if args.env_only else chosen_phases(args)

    refused = preflight_credentials(phases)
    if refused is not None:
        return refused

    if phases:
        try:
            session_mod.probe()
        except session_mod.ClaudeUnavailable as exc:
            print(f"[skip] {exc}")
            print("[skip] nothing was proven - install the claude CLI and re-run.")
            return 2

    dirt = env_mod.repo_status(repo_root)
    if dirt:
        # Not fatal: the manifest compares before against after, so pre-existing
        # dirt is a constant on both sides. Worth saying out loud, because a dirty
        # tree turns "the agent wrote here" into "something wrote here, probably".
        print(f"[warn] the working repo is dirty; drift is still detected, but the "
              f"starting point is not clean:\n{dirt[:400]}")

    failures: dict[str, list[str]] = {}
    try:
        # Vendoring needs network and only `3d` needs the skill (fact 13), so
        # it runs when that phase is in the run and not otherwise.
        with env_mod.lifecycle_env(repo_root, keep=args.keep,
                                   vendor="3d" in phases) as env:
            print(f"[env]  root    {env.root}")
            print(f"[env]  project {env.project}")
            print(f"[env]  origin  {env.bare}")
            assert_contained(env)
            print("[ok]   no GitHub credentials in the child environment (E1)")
            print("[ok]   every remote under the temp root resolves inside it (E7)")
            print(f"[ok]   gh resolves to the shim, not the real one (E4); store at "
                  f"{env.child_env['L3_GH_STORE']}")
            print("[ok]   project scaffolded and .memory/ passes validate_memory.py")
            root = env.root

            if not phases:
                print("[note] --env-only: no phase was driven")
            else:
                print(f"[models] driver={args.model} proxy={args.proxy_model} "
                      f"auditor={args.auditor_model}")
                if args.handoff:
                    print(f"[mode]   hand-off: {args.max_questions} turns/round, "
                          f"{args.max_rounds} round(s), {args.phase_budget:.0f}s per "
                          f"phase, 1b's auditor advisory. Findings from this run are "
                          f"about the CHAIN, not about artifact quality.")
                proxy = session_mod.ClaudeProxy(env=env.child_env,
                                                model=args.proxy_model)
                auditor = session_mod.ClaudeAuditor(env=env.child_env,
                                                    model=args.auditor_model)
                for phase in phases:
                    try:
                        problems = run_phase(phase, env, args, proxy, auditor)
                    except (driver_mod.PhaseFailure,
                            responder_mod.ResponderFailure) as exc:
                        print(f"[FAIL] {exc}")
                        failures[phase] = [str(exc)]
                        # Stop at the first failed phase: every later phase reads
                        # this one's artifacts, so continuing measures nothing.
                        break
                    if problems:
                        failures[phase] = problems
                        break
    except RuntimeError as exc:
        print(f"[fail] {exc}")
        return 1

    if not args.keep and root.exists():
        print(f"[fail] the temp root survived teardown: {root}")
        return 1

    if failures:
        print(f"\n[fail] {len(failures)} phase(s) failed: {', '.join(failures)}")
        return 1
    if phases:
        print(f"\n[pass] {len(phases)} phase(s) drove and asserted clean: "
              f"{', '.join(phases)}")
    else:
        print("\n[pass] environment built, contained and removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
