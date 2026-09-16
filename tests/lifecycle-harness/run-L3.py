#!/usr/bin/env python3
"""L3 Slice 1 - build a contained throwaway project, prove it, remove it.

This is the entry point every later slice runs inside. It drives no agent: Slice 3
writes the per-phase prompts and Slice 4 launches them. What it does is establish
and *assert* the environment those phases assume, because every invariant that is
only assumed is one an agent with `--dangerously-skip-permissions` can break
silently.

    python tests/lifecycle-harness/run-L3.py
    python tests/lifecycle-harness/run-L3.py --keep    # keep the project to inspect

Four things are proven before the run would hand control to a phase:

  E1  Nothing that could authenticate to a real GitHub reaches the child, and the
      developer's `~/.claude`, `~/.gemini`, `~/.config/devin` and working repo are
      the same after the run as before it.
  E7  Every repository under the temp root pushes into the temp root or nowhere.
      `2a`, `2b` and `3a` push their generated document unprompted and use plain
      `git push`, which no `gh` shim can intercept.
  E2  The environment is removed on success, on failure and on signal.
      A run that cannot guarantee that refuses to start.
  --  The project is scaffolded AND its `.memory/` passes `validate_memory.py`.
      The first full-depth Slice 0 run drove `1b` against a project with no
      `.agents/` at all, because a swallowed argparse failure looked like success.

Exit 0 = the environment was built, contained and removed.
Exit 1 = a check failed; the message names which.
Exit 2 = refused to start, so nothing was proven either way.

`code-simplifier` vendoring (fact 13) is deliberately NOT here. `3d` is the only
consumer and is not driven until Slice 4, and fetching it is the one step that
needs network - so it lands with the phase that needs it, not before.
"""
from __future__ import annotations

import argparse
import importlib.util
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


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="Build, prove and tear down the L3 lifecycle environment.")
    ap.add_argument("--repo", default=str(REPO),
                    help="repo root to build StratOS from (default: this checkout)")
    ap.add_argument("--keep", action="store_true",
                    help="keep the temp root on exit and print its path")
    return ap.parse_args(argv)


def preflight(repo_root: Path) -> None:
    """Refuse to start rather than half-start (E2).

    Teardown is a `shutil.rmtree` of a directory under the OS temp dir. If that
    directory cannot be created here, nothing later can guarantee its removal,
    and a harness that leaves residue is worse than one that does not run.
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
    """The two containment facts a phase would otherwise take on trust."""
    leaked = sorted(k for k in env.child_env
                    if k.startswith(("GH_", "GITHUB_")))
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


def main(argv=None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo).resolve()
    preflight(repo_root)

    dirt = env_mod.repo_status(repo_root)
    if dirt:
        # Not fatal: the manifest compares before against after, so pre-existing
        # dirt is a constant on both sides. It is worth saying out loud, because
        # a dirty tree is what turns "the agent wrote here" into "something
        # wrote here, probably".
        print(f"[warn] the working repo is dirty; drift is still detected, but "
              f"the starting point is not clean:\n{dirt[:400]}")

    try:
        with env_mod.lifecycle_env(repo_root, keep=args.keep) as env:
            print(f"[env]  root    {env.root}")
            print(f"[env]  home    {env.home}")
            print(f"[env]  project {env.project}")
            print(f"[env]  origin  {env.bare}")
            assert_contained(env)
            print("[ok]   no GitHub credentials in the child environment (E1)")
            print("[ok]   every remote under the temp root resolves inside it (E7)")
            print("[ok]   project scaffolded and .memory/ passes validate_memory.py")
            print("[note] no phases yet - Slice 3 writes the prompts, Slice 4 drives "
                  "them")
            root = env.root
    except RuntimeError as exc:
        print(f"[fail] {exc}")
        return 1

    if args.keep:
        print(f"[pass] environment built and contained; kept at {root}")
        return 0
    if root.exists():
        print(f"[fail] the temp root survived teardown: {root}")
        return 1
    print("[pass] environment built, contained and removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
