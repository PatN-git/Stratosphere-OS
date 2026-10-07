#!/usr/bin/env python3
"""Pre-commit test gate: refuse a commit whose staged code was not in a recorded passing test run.

  test_gate.py record -- <test command...>   run the tests; on a pass, record every changed file's content
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
import shutil
import subprocess
import sys
from pathlib import Path

RECORD = Path(".tmp") / "test-gate.json"
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
ZERO = "0" * 40
MARKER = "# stratos-test-gate"
CHECK_LINE = "python .agents/scripts/test_gate.py check"
FIX = "python .agents/scripts/test_gate.py record -- <test command>"
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
    print(f"Run the tests, then commit again:\n  {FIX}\nAgents: never bypass with --no-verify.", file=sys.stderr)
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
        return record(rest[1:] if rest[:1] == ["--"] else rest, cwd)
    handlers = {"check": check, "install": install, "status": status}
    if cmd not in handlers or len(argv) != 1:
        sys.exit(__doc__)
    return handlers[cmd]()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
