#!/usr/bin/env python3
"""Pre-commit test gate: refuse a commit whose staged code was not in a recorded passing test run.

  test_gate.py record -- <test command...>   run the tests; on a pass, record every changed file's content
  test_gate.py record --suite BT-<n> -- <whole-suite command...>
                                             the one full run per slice: refuses a dirty tree or a scoped command
                                             (exit 2), records like `record`, then writes .tmp/3d-suite-BT-<NNN>.json
                                             {head_sha, cmd, observed} only if the tree and HEAD are unchanged
                                             (else exit 3). Chain commands with `bash -c "a && b"`.
  test_gate.py check                         hook body: exit 1 if a staged code file differs from the record
  test_gate.py install                       write the pre-commit hook (never over a foreign hook or core.hooksPath)
  test_gate.py status                        exit 0 when the StratOS hook is installed, else 1

Content-addressed: the record maps each path to the blob hash it had when the tests passed, so partial
commits and incremental commits on a moving HEAD both work. It proves tests ran and passed on the staged
content, not that the tests are good. Stdlib only; runs from the repo root.
"""
import datetime
import fnmatch
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

RECORD = Path(".tmp") / "test-gate.json"
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
ZERO = "0" * 40
MARKER = "# stratos-test-gate"
CHECK_LINE = "python .agents/scripts/test_gate.py check"
FIX = "python .agents/scripts/test_gate.py record -- <related-tests command>"
SUITE_ID_RE = re.compile(r"^BT-(\d+|LOCAL-[a-z0-9-]+)$")
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
COUNT_RE = re.compile(r"\d+ (?:passed|failed)")
# Docs and framework/CI files the project's tests never cover need no test run.
# A pattern without "/" matches the file name at any depth.
UNGATED = ("*.md", "*.mdx", "*.txt", "*.rst", "docs/*", ".memory/*", ".agents/*", ".claude/*", ".github/*",
           "LICENSE*", ".gitignore", ".gitattributes", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.webp", "*.ico")
SKIP_MODES = ("120000", "160000")  # symlinks, submodules


def git(*args, input=None, check=True):
    out = subprocess.run(["git", *args], input=input, capture_output=True, text=True,
                         encoding="utf-8", errors="surrogateescape")
    if check and out.returncode != 0:
        sys.exit(f"test-gate: git {' '.join(args)} failed: {out.stderr.strip()}")
    return out


def ungated(path):
    return any(fnmatch.fnmatchcase(path if "/" in pat else path.rsplit("/", 1)[-1], pat)
               for pat in UNGATED)


def load_record():
    try:
        return json.loads(RECORD.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"files": {}}


def record(cmd, cwd):
    if not cmd:
        sys.exit("usage: test_gate.py record -- <test command...>")
    try:  # which() resolves npm.cmd & co. on Windows
        rc = subprocess.run([shutil.which(cmd[0]) or cmd[0], *cmd[1:]], cwd=cwd).returncode
    except OSError as e:
        print(f"test-gate: cannot run {cmd[0]}: {e}; nothing recorded", file=sys.stderr)
        return 127
    if rc != 0:
        print(f"test-gate: tests failed (exit {rc}); nothing recorded", file=sys.stderr)
        return rc
    return save_record(cmd)


def save_record(cmd):
    # Hash after the run, so files the suite generated are covered too.
    entries = git("status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames").stdout
    paths = [e[3:] for e in entries.split("\0") if len(e) > 3]
    present = [p for p in paths if os.path.isfile(p) and not os.path.islink(p)]
    blobs = git("hash-object", "--stdin-paths", input="\n".join(present) + "\n").stdout.split() if present else []
    data = load_record()
    files = data.get("files", {})
    files.update({p: None for p in paths if not os.path.lexists(p)})
    files.update(dict(zip(present, blobs)))
    RECORD.parent.mkdir(exist_ok=True)
    RECORD.write_text(json.dumps({"cmd": " ".join(cmd), "at": datetime.datetime.now().isoformat(timespec="seconds"),
                                  "files": files}, indent=1), encoding="utf-8")
    print(f"test-gate: recorded {len(files)} file(s) from a passing run")
    return 0


def tee(cmd, cwd):
    """Run `cmd`, copying its raw output to ours (no decode on the write side: a cp1252 pipe must not crash on
    a check mark); return (exit code, last 64 KB of output)."""
    tail = b""
    try:
        proc = subprocess.Popen([shutil.which(cmd[0]) or cmd[0], *cmd[1:]], cwd=cwd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, env={**os.environ, "PYTHONUNBUFFERED": "1"})
    except OSError as e:
        print(f"test-gate: cannot run {cmd[0]}: {e}; nothing recorded", file=sys.stderr)
        return 127, tail
    try:
        while chunk := os.read(proc.stdout.fileno(), 65536):
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
            tail = (tail + chunk)[-65536:]
    except KeyboardInterrupt:
        proc.kill()
        proc.wait()
        return 130, tail
    return proc.wait(), tail


def observed_line(tail):
    """The last four `N passed|failed` lines (so check.sh keeps pytest's count beside the harness's) plus the last line."""
    lines = [l for l in (ANSI_RE.sub("", s).strip() for s in tail.decode("utf-8", "replace").splitlines()) if l]
    counts = [l for l in lines if COUNT_RE.search(l)][-4:]
    return "; ".join([*counts, *(lines[-1:] if lines[-1:] != counts[-1:] else [])])[:300]


def record_suite(issue, cmd, cwd):
    try:
        import pr_body  # ships beside this script; reads the same record at reuse time
    except ImportError:
        print("test-gate: pr_body.py is missing beside test_gate.py; run /stratosphere-update", file=sys.stderr)
        return 2
    if not pr_body.tree_is_clean():
        print("test-gate: uncommitted changes outside .memory/, docs/, .tmp/: commit first, a suite record is only "
              "reusable at a clean HEAD", file=sys.stderr)
        return 2
    is_scoped = getattr(pr_body, "is_scoped", None)  # an older pr_body still enforces this at read time
    if is_scoped and is_scoped(cmd):
        print(f"test-gate: refusing a scoped command ({shlex.join(cmd)}): --suite records the whole suite",
              file=sys.stderr)
        return 2
    head = git("rev-parse", "HEAD").stdout.strip()
    rc, tail = tee(cmd, cwd)
    if rc != 0:
        print(f"test-gate: tests failed (exit {rc}); nothing recorded", file=sys.stderr)
        return rc
    save_record(cmd)
    if not pr_body.tree_is_clean() or git("rev-parse", "HEAD").stdout.strip() != head:
        print("test-gate: tests passed but no suite record was written: the tree or HEAD changed during the run",
              file=sys.stderr)
        return 3
    sid = SUITE_ID_RE.match(issue).group(1)
    name = f"{int(sid):03d}" if sid.isdigit() else sid
    path = Path(".tmp") / f"3d-suite-BT-{name}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"head_sha": head, "cmd": shlex.join(cmd), "observed": observed_line(tail)}, indent=1),
                    encoding="utf-8")
    print(f"test-gate: wrote {path}")
    return 0


def check():
    base = "HEAD" if git("rev-parse", "--verify", "-q", "HEAD", check=False).returncode == 0 else EMPTY_TREE
    raw = git("diff", "--cached", "--raw", "-z", "--no-renames", "--no-abbrev", base).stdout.split("\0")
    files = load_record().get("files", {})
    untested = []
    for header, path in zip(raw[0::2], raw[1::2]):
        _, new_mode, _, new_sha, status = header.lstrip(":").split()
        if ungated(path) or new_mode in SKIP_MODES:
            continue
        staged = None if status == "D" or new_sha == ZERO else new_sha
        if path not in files or files[path] != staged:
            untested.append(path)
    if not untested:
        return 0
    print("test-gate: commit blocked: staged code was not in a passing test run:", file=sys.stderr)
    for p in untested:
        print(f"  {p}", file=sys.stderr)
    print("Run the related tests (not the full suite: /3d Phase 3 owns the one full run), then commit again:\n"
          f"  {FIX}\nAgents: never bypass with --no-verify.", file=sys.stderr)
    return 1


def hook_file():
    custom = git("config", "--get", "core.hooksPath", check=False).stdout.strip()
    return custom, Path(custom or git("rev-parse", "--git-path", "hooks").stdout.strip()) / "pre-commit"


def hook_body():
    interpreters = " ".join(f'"{c}"' for c in (Path(sys.executable).as_posix(), "python3", "python", "py"))
    return f"""#!/bin/sh
{MARKER}: managed by .agents/scripts/test_gate.py install (re-run to refresh)
if [ ! -f .agents/scripts/test_gate.py ]; then
  echo "test-gate: .agents/scripts/test_gate.py missing; commit blocked (restore it via /stratosphere-update or delete this hook)" >&2
  exit 1
fi
for PY in {interpreters}; do
  if "$PY" -c "" >/dev/null 2>&1; then exec "$PY" .agents/scripts/test_gate.py check; fi
done
echo "test-gate: no working Python found; commit blocked" >&2
exit 1
"""


def install():
    custom, hook = hook_file()
    if custom:
        print(f"test-gate: core.hooksPath is set ({custom}); not installing. Add to that hook manager's "
              f"pre-commit:\n  {CHECK_LINE}", file=sys.stderr)
        return 1
    if hook.exists() and MARKER not in hook.read_text(encoding="utf-8", errors="replace"):
        print(f"test-gate: {hook} already exists and is not ours; not touching it. Add this line to it:\n"
              f"  {CHECK_LINE}", file=sys.stderr)
        return 1
    hook.parent.mkdir(parents=True, exist_ok=True)
    with open(hook, "w", encoding="utf-8", newline="\n") as f:
        f.write(hook_body())
    hook.chmod(0o755)
    print(f"test-gate: installed {hook}")
    return 0


def status():
    _, hook = hook_file()
    on = hook.is_file() and MARKER in hook.read_text(encoding="utf-8", errors="replace")
    print(f"test-gate: {'installed' if on else 'not installed'}")
    return 0 if on else 1


def main(argv):
    top = git("rev-parse", "--show-toplevel", check=False)
    if top.returncode != 0:
        sys.exit("test-gate: not inside a git repository")
    cwd = os.getcwd()  # the test command runs where the caller ran it
    os.chdir(top.stdout.strip())
    cmd = argv[0] if argv else ""
    if cmd == "record":
        rest = argv[1:]
        if rest[:1] == ["--suite"]:
            if len(rest) < 4 or not SUITE_ID_RE.match(rest[1]) or rest[2] != "--":
                sys.exit("usage: test_gate.py record --suite BT-<n> -- <whole-suite command...>")
            return record_suite(rest[1], rest[3:], cwd)
        return record(rest[1:] if rest[:1] == ["--"] else rest, cwd)
    handlers = {"check": check, "install": install, "status": status}
    if cmd not in handlers or len(argv) != 1:
        sys.exit(__doc__)
    return handlers[cmd]()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
