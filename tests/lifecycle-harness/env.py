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
import tempfile
from dataclasses import dataclass
from pathlib import Path

SCRUB_PREFIXES = ("GH_", "GITHUB_")
SCRUB_EXACT = {"GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN"}


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


def manifest(paths, max_depth: int = 2) -> dict[str, str]:
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

    Names-only catches what actually matters: the harness installing into the real
    HOME instead of the temp one, which shows up as new entries (a plugin directory,
    a skills tree). It will NOT catch an in-place edit of an existing file. That is
    an accepted limit - containment is the redirected HOME, the scrubbed environment
    and the stripped remotes; this is the backstop, and `assert_no_install` names the
    one breach worth asserting outright.
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
def lifecycle_env(repo_root: Path, keep: bool = False, scaffold: bool = True):
    """Build an isolated project with StratOS installed, and tear it down."""
    repo_root = Path(repo_root).resolve()
    real_home = Path(os.path.expanduser("~"))
    watched = [real_home / ".claude", real_home / ".gemini", real_home / ".config" / "devin"]
    before = manifest(watched)
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

        _seed_credentials(real_home, home)
        if scaffold:
            _install_stratos(repo_root, home, project, child)

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
        assert_no_install(real_home, markers_before)
        drift = diff_manifest(before, manifest(watched))
        if drift:
            raise RuntimeError("the run added or removed entries under paths it must never touch (E1):\n  "
                               + "\n  ".join(drift))


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
    subprocess.run(["python", str(dist / "scripts" / "scaffold.py"), "--yes"],
                   cwd=str(project), env=child, capture_output=True)


def _teardown(root: Path, keep: bool) -> None:
    if keep:
        print(f"[kept] {root}")
        return
    shutil.rmtree(root, ignore_errors=True)
