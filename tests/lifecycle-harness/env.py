#!/usr/bin/env python3
"""L3 containment - temp HOME, temp project, and a remote that cannot reach GitHub.

Pulled forward from Slice 1 because the Slice 0 spike needs an environment to run in.
Slice 1 generalises this into `run-L3.py`; the invariants live here.

Three things this exists to prevent, each one an observed hazard rather than a
hypothetical:

  E7  `2a`, `2b` and `3a` commit their generated document and push it to the default
      branch by design (AGENTS.md 4, documentation-artifact exception). They use
      `git push`, which no `gh` shim can intercept. `run-L2.py:247` copies the repo
      WITH its `.git`, so a naive reuse hands a pushing agent the real origin. Every
      `.git` under the temp root therefore has its remotes stripped and redirected to
      a local bare repo, and preflight refuses to start if any remote still points
      outside.

  E1  `run-L2.py:271` passes the whole environment to the child, `GH_TOKEN` included,
      and the agent runs with `--dangerously-skip-permissions`. Containment is by
      construction, not by hoping: tokens are scrubbed, and a manifest of the real
      `~/.claude`, `~/.gemini` and the working repo is compared before and after.

  E2  Teardown runs on success, failure and signal, or the run refuses to start.
"""
from __future__ import annotations

import contextlib
import hashlib
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# GH_*/GITHUB_*: anything that could authenticate to a real GitHub.
# CLAUDE*/ANTHROPIC_*/AI_AGENT: the PARENT agent's session identity. When the harness
# is itself launched from a Claude session, the child inherits CLAUDECODE,
# CLAUDE_CODE_CHILD_SESSION, CLAUDE_CODE_SESSION_ID and friends, and is no longer an
# independent run - it believes it is a continuation of the session driving it.
SCRUB_PREFIXES = ("GH_", "GITHUB_", "CLAUDE", "ANTHROPIC_")
SCRUB_EXACT = {"GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "AI_AGENT"}


@dataclass
class Env:
    root: Path
    home: Path
    project: Path
    bare: Path
    child_env: dict


def scrub(env: dict) -> dict:
    """Drop anything that could authenticate to a real GitHub."""
    return {k: v for k, v in env.items()
            if k not in SCRUB_EXACT and not k.startswith(SCRUB_PREFIXES)}


def git_remotes(git_dir: Path) -> list[str]:
    r = subprocess.run(["git", "--git-dir", str(git_dir), "remote", "-v"],
                       capture_output=True, text=True)
    return [ln.split()[1] for ln in r.stdout.splitlines() if len(ln.split()) > 1]


def strip_remotes(root: Path) -> int:
    """Remove every remote from every repository under `root`. Returns how many."""
    n = 0
    for git_dir in list(root.rglob(".git")):
        if git_dir.is_file():          # worktree pointer file
            continue
        names = subprocess.run(["git", "--git-dir", str(git_dir), "remote"],
                               capture_output=True, text=True).stdout.split()
        for name in names:
            subprocess.run(["git", "--git-dir", str(git_dir), "remote", "remove", name],
                           capture_output=True)
            n += 1
    return n


def preflight_remotes(root: Path) -> None:
    """Refuse to run if any repo under `root` can reach outside it (E7)."""
    offenders = []
    for git_dir in root.rglob(".git"):
        if git_dir.is_file():
            continue
        for url in git_remotes(git_dir):
            resolved = url
            with contextlib.suppress(OSError, ValueError):
                resolved = str(Path(url.replace("file://", "")).resolve())
            if not resolved.startswith(str(root.resolve())):
                offenders.append(f"{git_dir}: {url}")
    if offenders:
        raise RuntimeError(
            "refusing to start - a repository under the temp root can push outside it. "
            "2a/2b/3a push unprompted, so this would reach a real remote:\n  "
            + "\n  ".join(offenders))


def manifest(paths, max_depth: int = 1) -> dict[str, str]:
    """Depth-limited fingerprint of paths that must not change (E1).

    Records entry NAMES only, to depth 2. Two hard-won constraints shape this:

      * Not a full-tree hash. `~/.gemini` alone holds ~67k files; hashing it end to
        end took longer than the run it guards, and a backstop nobody can afford to
        run is not a backstop.
      * Not sizes or mtimes. These directories are LIVE - Antigravity writes into
        `~/.gemini` while the harness runs, so any content-sensitive fingerprint
        fails on the developer's own IDE rather than on a real breach. That is not a
        theoretical risk: it failed exactly that way during Slice 0, and passed on
        the retry, which is worse.

    Depth 1, not 2, for the same reason. At depth 2 a new `sessions/<id>` directory
    under `~/.gemini` - Antigravity creating one while the harness runs - reads as
    drift and fails the run. That happened on the first real spike, AFTER the
    names-only fix, so depth 2 was still too sensitive to live churn. The same is
    true of `~/.claude/projects/<project>`.

    What is left is deliberately coarse: a new or vanished TOP-LEVEL entry. It will
    not catch an in-place edit, nor a new entry nested inside an existing directory.
    That is an accepted limit - containment is the redirected HOME, the scrubbed
    environment and the stripped remotes. `assert_no_install` covers the deep paths
    that actually matter, by name.
    """
    out = {}
    for p in paths:
        p = Path(p)
        if not p.exists():
            out[str(p)] = "<absent>"
            continue
        h = hashlib.sha256()
        for rel in sorted(_walk(p, max_depth)):
            h.update(rel.encode())
        out[str(p)] = h.hexdigest()
    return out


def repo_status(repo_root: Path) -> str:
    """`git status --porcelain` of the developer's real working repo (E1).

    The three watched HOME directories are only half of E1. The harness builds
    inside the real repo and the agent runs with `--dangerously-skip-permissions`,
    so the repo's own dirt is the other half. `build/build.py` is idempotent -
    `dist/` is tracked and regenerates byte-identically - so a clean tree stays
    clean across a run and any change here is the run's own doing.

    Unlike `manifest`, this is exact rather than coarse: `git status` already
    ignores the live churn (`.tmp/`, `.agents/`) that forced the names-only
    fingerprint, so there is no reason to blunt it.
    """
    r = subprocess.run(["git", "-C", str(repo_root), "status", "--porcelain"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return f"<git status failed: exit {r.returncode}>"
    return r.stdout.strip()[:2000]


def watched_manifest(real_home: Path, repo_root: Path) -> dict[str, str]:
    """Everything E1 says must be the same after the run as before it."""
    out = manifest([real_home / ".claude", real_home / ".gemini",
                    real_home / ".config" / "devin"])
    out[f"{repo_root}: git status"] = repo_status(repo_root)
    return out


def _walk(root: Path, max_depth: int, depth: int = 1):
    """Relative entry names down to `max_depth`. Names only - see manifest()."""
    with contextlib.suppress(OSError):
        for entry in os.scandir(root):
            rel = str(Path(entry.path).relative_to(root))
            yield rel
            if entry.is_dir(follow_symlinks=False) and depth < max_depth:
                for nested in _walk(Path(entry.path), max_depth, depth + 1):
                    yield f"{rel}/{nested}"


# The one breach worth asserting outright: StratOS installed into the real HOME.
INSTALL_MARKERS = (
    Path(".claude") / "plugins" / "stratosphere-os",
    Path(".claude") / "skills" / "0a-start-session",
    Path(".gemini") / "config" / "plugins" / "stratosphere-os",
)


def install_markers_present(real_home: Path) -> set:
    return {str(m) for m in INSTALL_MARKERS if (real_home / m).exists()}


def assert_no_install(real_home: Path, before_present: set) -> None:
    """Fail if a StratOS install APPEARED in the developer's real HOME."""
    appeared = [str(m) for m in INSTALL_MARKERS
                if (real_home / m).exists() and str(m) not in before_present]
    if appeared:
        raise RuntimeError(
            "the run installed StratOS into the REAL home directory (E1): "
            + ", ".join(appeared))


def diff_manifest(before: dict, after: dict) -> list[str]:
    return [f"{k}: {before.get(k)} -> {after.get(k)}"
            for k in set(before) | set(after) if before.get(k) != after.get(k)]


@contextlib.contextmanager
def lifecycle_env(repo_root: Path, keep: bool = False, scaffold: bool = True,
                  vendor: bool = False):
    """Build an isolated project with StratOS installed, and tear it down."""
    repo_root = Path(repo_root).resolve()
    real_home = Path(os.path.expanduser("~"))
    before = watched_manifest(real_home, repo_root)
    markers_before = install_markers_present(real_home)

    root = Path(tempfile.mkdtemp(prefix="l3-"))
    env_obj = None
    original_handlers = {}

    def _bail(signum, frame):     # E2: teardown on signal, not just on return
        _teardown(root, keep)
        raise KeyboardInterrupt(f"signal {signum}")

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            with contextlib.suppress(ValueError, AttributeError, OSError):
                original_handlers[sig] = signal.signal(sig, _bail)

        home = root / "home"
        project = root / "project"
        bare = root / "origin.git"
        for d in (home, project):
            d.mkdir(parents=True)
        subprocess.run(["git", "init", "--bare", str(bare)], capture_output=True, check=True)
        subprocess.run(["git", "init", str(project)], capture_output=True, check=True)
        subprocess.run(["git", "-C", str(project), "remote", "add", "origin", str(bare)],
                       capture_output=True, check=True)

        child = scrub(dict(os.environ))
        child.update({
            "HOME": str(home), "USERPROFILE": str(home),
            # A global config inside the temp root: nothing the agent does with git
            # can read the developer's identity or credential helpers.
            "GIT_CONFIG_GLOBAL": str(_write_git_config(root, bare)),
            "GIT_TERMINAL_PROMPT": "0",
        })

        install_shims(root, child)
        assert_gh_is_shimmed(child)

        _seed_credentials(real_home, home)
        if scaffold:
            _install_stratos(repo_root, home, project, child)
        if vendor:
            vendor_skills(repo_root, project, child)

        strip_remotes(project)
        subprocess.run(["git", "-C", str(project), "remote", "add", "origin", str(bare)],
                       capture_output=True)
        preflight_remotes(root)

        env_obj = Env(root=root, home=home, project=project, bare=bare, child_env=child)
        yield env_obj
    finally:
        for sig, handler in original_handlers.items():
            with contextlib.suppress(ValueError, OSError):
                signal.signal(sig, handler)
        _teardown(root, keep)
        # Raising from `finally` REPLACES whatever the body was already raising, so
        # a containment warning would erase the real failure - the first spike's
        # "rounds exhausted with gaps still open" became an E1 traceback instead.
        # Only raise when nothing else is in flight; otherwise warn and let the
        # original outcome stand.
        failing = sys.exc_info()[0] is not None
        try:
            assert_no_install(real_home, markers_before)
        except RuntimeError:
            if not failing:
                raise
            print("[warn] E1: StratOS markers appeared in the real HOME", file=sys.stderr)
        drift = diff_manifest(before, watched_manifest(real_home, repo_root))
        if drift:
            msg = ("the run changed something it must never touch - a top-level "
                   "entry under HOME, or the working repo itself (E1):\n  " + "\n  ".join(drift))
            if failing:
                print(f"[warn] {msg}", file=sys.stderr)
            else:
                raise RuntimeError(msg)


# `3d:38` runs `code-simplifier`, which is NOT bundled - `external-skills.json`
# fetches it from GitHub (fact 13). `plan-html`, which `2b` invokes, IS bundled and
# arrives with the scaffold; do not fetch it.
VENDORED = ("code-simplifier",)


# `sync_skills.py:364-375` picks its destination by HOST, not from the registry's
# `targetPath`: `.claude/skills` when a `.claude-plugin` marker sits beside the
# script (Claude Code), `.agents/skills` otherwise. Checking only one of them made
# a successful vendor look like a silent miss.
SKILL_BASES = (".claude/skills", ".agents/skills")


def vendored_at(project: Path, name: str) -> Path | None:
    for base in SKILL_BASES:
        candidate = project / Path(base) / name
        if candidate.is_dir():
            return candidate
    return None


def vendor_skills(repo_root: Path, project: Path, child: dict,
                  names=VENDORED, script: Path | None = None) -> None:
    """Fetch the external skills a driven phase needs, and prove they landed.

    This is the one setup step that needs network, which is why it runs only when
    the phase that needs it is in the run. A silent miss here surfaces much later
    as `3d` behaving oddly for no visible reason, so both the exit code and the
    resulting directory are checked - the `--yes` lesson from Slice 0.
    """
    script = script or (repo_root / "dist" / "claude-code" / "scripts" /
                        "sync_skills.py")
    if not script.exists():
        raise RuntimeError(f"no sync_skills.py at {script} - build first")
    r = subprocess.run(["python", str(script), "--only", *names,
                        "--project-root", str(project)],
                       cwd=str(project), env=child, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            f"vendoring {', '.join(names)} failed (exit {r.returncode}): "
            f"{(r.stdout or '')[-500:]}{(r.stderr or '')[-500:]}")
    missing = [n for n in names if not vendored_at(project, n)]
    if missing:
        raise RuntimeError(
            f"sync_skills.py reported success but did not install: "
            f"{', '.join(missing)} (looked in {', '.join(SKILL_BASES)}). "
            f"3d invokes code-simplifier (3d:38, fact 13).")


SHIM_SRC = Path(__file__).parent / "shims"

# Asks the shim who it is, from inside a child that has the run's environment.
# It cannot be asked from here: on Windows the executable search uses the CALLING
# process's PATH, not the `env=` one, so a check run from the harness would resolve
# the developer's real gh and pass while the run under test was still shimmed - or,
# worse, the reverse.
_PROBE = ("import subprocess,sys;"
          "r=subprocess.run(['gh','version'],capture_output=True,text=True);"
          "sys.stdout.write(r.stdout)")


def install_shims(root: Path, child: dict) -> Path:
    """Put a `gh` the run controls in front of the real one (E4)."""
    shim_dir = root / "shims"
    shutil.copytree(SHIM_SRC, shim_dir, dirs_exist_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(shim_dir / "gh", 0o755)
    if os.name == "nt":
        _mint_windows_launcher(shim_dir)
    child["PATH"] = str(shim_dir) + os.pathsep + child.get("PATH", "")
    # The Windows launcher imports `gh_shim` rather than running it as a file.
    child["PYTHONPATH"] = os.pathsep.join(
        [str(shim_dir)] + ([child["PYTHONPATH"]] if child.get("PYTHONPATH") else []))
    child["L3_GH_STORE"] = str(root / "gh-store.json")
    return shim_dir


def _mint_windows_launcher(shim_dir: Path) -> None:
    """A `.cmd` shim cannot intercept a Python caller on Windows.

    `CreateProcess` appends only `.exe` when it searches PATH - PATHEXT is a shell
    feature, which is why `shutil.which('gh')` finds `gh.cmd` and
    `subprocess.run(['gh', ...])` does not. `reconcile.py:109,139` is exactly that
    kind of caller, so with only a `.cmd` on PATH the terminal-sync gate would reach
    the developer's real gh - authenticated through the OS keyring, which scrubbing
    `GH_TOKEN` does nothing about. Mint a real launcher instead.
    """
    try:
        from pip._vendor.distlib.scripts import ScriptMaker
    except ImportError as exc:      # no launcher, no containment - do not proceed
        raise RuntimeError(
            "cannot mint tests/lifecycle-harness/shims/gh.exe: pip's vendored "
            "distlib is unavailable, and on Windows a .cmd shim cannot intercept "
            f"reconcile.py's `gh` calls, which would then reach the real GitHub: {exc}")
    maker = ScriptMaker(None, str(shim_dir))
    maker.executable = sys.executable
    maker.variants = {""}
    maker.make("gh = gh_shim:main")


def assert_gh_is_shimmed(child: dict) -> None:
    """Prove the interception, from a child with the run's environment (E4)."""
    r = subprocess.run(["python", "-c", _PROBE], env=child,
                       capture_output=True, text=True)
    if "l3-shim" not in (r.stdout or ""):
        raise RuntimeError(
            "`gh` does not resolve to the L3 shim inside the run's environment, so "
            "a phase would reach the real GitHub (E4). Probe said: "
            f"{(r.stdout or r.stderr or '<nothing>').strip()[:300]!r}")


def _seed_credentials(real_home: Path, temp_home: Path) -> None:
    """Copy the local Claude credentials into the temp HOME.

    Redirecting HOME is what contains the run, but it also hides the CLI's own
    credentials, and the agent then dies mid-grill with "Not logged in" - an empty
    turn that looks like a driver bug. `run-L2.py:282-285` copies the same file for
    the same reason. It is a local copy into a directory removed at teardown; nothing
    is transmitted and nothing outlives the run.
    """
    src = real_home / ".claude" / ".credentials.json"
    if not src.exists():
        return
    dest = temp_home / ".claude"
    dest.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        shutil.copy2(src, dest / ".credentials.json")


def _write_git_config(root: Path, bare: Path) -> Path:
    cfg = root / "gitconfig"
    url = bare.as_uri()
    cfg.write_text(
        "[user]\n\tname = L3 Harness\n\temail = l3@harness.invalid\n"
        "[init]\n\tdefaultBranch = main\n"
        f'[url "{url}"]\n\tinsteadOf = https://github.com/\n'
        "[remote]\n\tpushDefault = origin\n",
        encoding="utf-8")
    return cfg


def _install_stratos(repo_root: Path, home: Path, project: Path, child: dict) -> None:
    """Build the bundle and scaffold it into the project (Slice 1's core)."""
    subprocess.run(["python", "build/build.py"], cwd=str(repo_root), check=True,
                   capture_output=True)
    dist = repo_root / "dist" / "claude-code"
    claude_dir = home / ".claude"
    (claude_dir / "plugins").mkdir(parents=True, exist_ok=True)
    shutil.copytree(dist, claude_dir / "plugins" / "stratosphere-os", dirs_exist_ok=True)
    if (dist / "skills").is_dir():
        shutil.copytree(dist / "skills", claude_dir / "skills", dirs_exist_ok=True)
    # No `--yes` flag exists - scaffold.py takes --dry-run/--repair-lock/--update/
    # --verify and nothing else. Passing it made argparse exit 2, and
    # capture_output with no check swallowed that completely: the first real
    # full-depth run drove 1b against a project with no .agents/ and no .memory/
    # at all, and nothing said so. Fail loudly instead.
    r = subprocess.run(["python", str(dist / "scripts" / "scaffold.py")],
                       cwd=str(project), env=child, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            f"scaffold.py failed (exit {r.returncode}):\n"
            f"{(r.stdout or '')[-800:]}\n{(r.stderr or '')[-800:]}")
    assert_scaffolded(project)
    assert_memory_valid(project, child)


SCAFFOLD_MARKERS = (
    Path(".agents") / "rules",
    Path(".agents") / "scripts" / "validate_memory.py",
    Path(".agents") / ".stratosphere-lock.json",
    Path(".memory"),
    Path("AGENTS.md"),
)


def assert_scaffolded(project: Path) -> None:
    """A silent scaffold failure invalidates every phase downstream of it."""
    missing = [str(m) for m in SCAFFOLD_MARKERS if not (project / m).exists()]
    if missing:
        raise RuntimeError(
            "the project was not scaffolded - these are absent: " + ", ".join(missing))


def assert_memory_valid(project: Path, child: dict) -> None:
    """The scaffolded `.memory/` must pass its own validator before phase 1.

    `assert_scaffolded` only proves the files arrived. This proves they are
    coherent - IDs unique, cross-references resolvable, no secrets - which is
    what every later phase reads and what `0b` re-runs at the end (Slice 4).
    A fresh scaffold exits 0 here; exit 2 is warnings and exit 1 is errors, and
    neither is an acceptable starting state for a run that will blame the
    lifecycle for whatever it finds later.
    """
    script = project / ".agents" / "scripts" / "validate_memory.py"
    if not script.exists():
        raise RuntimeError(
            f"the scaffold left no memory validator at {script} - "
            "there is nothing to validate the run's starting state against")
    r = subprocess.run(["python", str(script), "--path", ".memory"],
                       cwd=str(project), env=child, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            f"the scaffolded .memory/ does not pass validate_memory.py "
            f"(exit {r.returncode}):\n"
            f"{(r.stdout or '')[-800:]}\n{(r.stderr or '')[-400:]}")


def _teardown(root: Path, keep: bool) -> None:
    if keep:
        print(f"[kept] {root}")
        return
    shutil.rmtree(root, ignore_errors=True)
