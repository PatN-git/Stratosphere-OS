#!/usr/bin/env python3
"""floor_guard.py: diff-scoped guard against changes that lower the quality bar. Read-only.

  floor_guard.py [--base REF]

Diff = merge base with the default branch -> working tree (committed, staged, unstaged, untracked). Flags only moves
that lower the bar: added skip/xfail/only markers in test files, added suppressions, a net drop in test assertions,
loosened coverage/lint thresholds, new rows in the exception record. Tightening is silent.
Exit 0 clean, 1 violation (block), 2 could not run (never a pass). Output is rule, location and matched token,
never the source line (a suppressed line is often a secret's own line).
Exceptions: rows `<rule> <glob> — <reason>` under `## Floor exceptions` in .memory/ARCHITECTURE.md, read from the
default-branch tip only. A row added anywhere else is itself a violation, so no agent can approve its own loosening.
`<rule>` is a floor rule (skip, suppress, ...) or a memory rule ID (`A-003`), the latter read by the 4a Standards auditor.
On a clean run the tip's rule-ID rows and rules bound to a check (`[[A-003]] [LAW] ... Check: <path>` in ARCHITECTURE.md
or DESIGN_RULES.md) are printed as `info:` lines for the auditor; a row or marker added on a branch counts only once merged.
Stdlib only; base and glob helpers come from pr_body.py (shipped beside it).
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import pr_body

DOC_EXT = (".md", ".mdx", ".txt", ".rst")
TEST_RX = re.compile(r"(^|/)(tests?|__tests__|specs?)/|(^|/)test_[^/]*$|_test\.\w+$|\.(test|spec)\.\w+$|Tests?\.java$")
SKIP_RX = re.compile("|".join((
    r"pytest\.mark\.(?:skip|skipif|xfail)\b", r"\bpytest\.(?:skip|xfail)\(", r"\bunittest\.(?:skip\w*|expectedFailure)\b",
    r"\.skipTest\(", r"\b(?:it|test|describe|context)\.(?:skip|only|todo)\b",
    r"(?<![.\w])(?:xit|xdescribe|xtest|fit|fdescribe)\(", r"^\s*(?:xit|xdescribe|xcontext)\s+[\"']",
    r"\bt\.Skip(?:Now|f)?\(", r"#\[ignore\b", r"@(?:Disabled|Ignore)\b")))
SUPPRESS_RX = re.compile("|".join((
    r"#\s*noqa\b", r"#\s*type:\s*ignore\b", r"#\s*pylint:\s*disable", r"#\s*pragma:\s*no cover",
    r"@ts-(?:ignore|nocheck|expect-error)\b", r"eslint-dis[a]ble", r"biome-ign[o]re\b", r"nosem[g]rep\b", r"gitleaks:al[l]ow\b",
    r"Stryker\s+dis[a]ble", r"(?:istanbul|c8|v8)\s+ignore\b", r"//\s*nolint\b", r"#\[allow\(", r"@Suppress[W]arnings\b",
    r"rubocop:dis[a]ble")))
CI_SOFT_RX = re.compile(r"continue-on-error:\s*true|\|\|\s*true")
WORKFLOW_RX = re.compile(r"^\.github/workflows/")
ASSERT_RX = re.compile(r"\bassert\w*|\bexpect\s*\(|\.should\b|\bt\.(?:Error|Fatal)f?\(|\brequire\.|\braises\(|\btoThrow\b")
NUM = r"[\"']?\s*[=:]\s*[\"']?(?P<v>\d+(?:\.\d+)?)"
CONFIG = r"(?:pytest\.ini|pyproject\.toml|setup\.cfg|tox\.ini|\.coveragerc|package\.json|\.github/workflows/.*)"
JS_CONFIG = r"(?:(?:jest|vitest)\.config\.\w+|package\.json)"
CODECOV = r"\.?codecov\.ya?ml"
# (key pattern, files it applies to, which direction loosens: "min" = lower is looser, "max" = higher is looser)
THRESHOLDS = (
    (re.compile(rf"\b(?P<k>fail_under){NUM}"), CONFIG, "min"),
    (re.compile(r"(?P<k>--cov-fail-under)[= ](?P<v>\d+(?:\.\d+)?)"), CONFIG, "min"),
    (re.compile(rf"\b(?P<k>lines|branches|functions|statements){NUM}"), JS_CONFIG, "min"),
    (re.compile(rf"\b(?P<k>target){NUM}"), CODECOV, "min"),
    (re.compile(rf"\b(?P<k>threshold){NUM}"), CODECOV, "max"),
    (re.compile(rf"(?P<k>--max-warnings|maxWarnings)[=\s\"':]+(?P<v>\d+)"), CONFIG, "max"),
)
EXC_RULES = ("skip", "suppress", "tests-removed", "threshold")
RULE_ID = r"(?!BT-)[A-Z]{1,3}-\d{3,}"
EXC_RE = re.compile(rf"^[-*\s]*`?({'|'.join(EXC_RULES)}|{RULE_ID})`?\s+`?(\S+?)`?\s+[—–-]{{1,2}}\s+\S")
BOUND_RE = re.compile(rf"^\s*[-*+]\s+\**\s*\[\[({RULE_ID})\]\][^\n]*\[LAW\][^\n]*?\bCheck:\s*`?([^\s`]+)", re.M)
ARCH = ".memory/ARCHITECTURE.md"
DESIGN_RULES = ".memory/DESIGN_RULES.md"
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)")


class CouldNotRun(Exception):
    pass


def run(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def parse_diff(text):
    """{path: ([(line_no, text)] added, [text] removed)}; hunk bodies are content even when they start `+++`/`---`."""
    files, path, in_hunk, old, new, n = {}, None, False, None, None, 0
    for raw in text.split("\n"):
        line = raw.rstrip("\r")
        if not in_hunk:
            if line.startswith("diff --git "):
                old = new = None
            elif line.startswith("--- "):
                old = line[4:].split("\t")[0]
            elif line.startswith("+++ "):
                new = line[4:].split("\t")[0]
            elif m := HUNK_RE.match(line):
                gone = new in (None, "/dev/null")
                path = (old if gone else new)[2:]
                files.setdefault(path, ([], []))
                in_hunk, n = True, int(m.group(1))
            continue
        if line.startswith("diff --git "):
            in_hunk, old, new = False, None, None
        elif m := HUNK_RE.match(line):
            n = int(m.group(1))
        elif line.startswith("+"):
            files[path][0].append((n, line[1:]))
            n += 1
        elif line.startswith("-"):
            files[path][1].append(line[1:])
    return files


def untracked(files):
    for rel in (run("ls-files", "--others", "--exclude-standard", "-z") or "").split("\0"):
        p = Path(rel)
        if not rel or p.is_symlink() or not p.is_file() or p.stat().st_size > 1_000_000:
            continue
        data = p.read_bytes()
        if b"\0" not in data:
            lines = data.decode("utf-8", errors="replace").split("\n")
            files[rel] = ([(i, l.rstrip("\r")) for i, l in enumerate(lines, 1)], [])


def exception_rows(text):
    section = re.split(r"^## Floor exceptions\s*$", text or "", maxsplit=1, flags=re.M)
    rows = (EXC_RE.match(l.strip()) for l in (section[1].split("\n## ")[0].splitlines() if len(section) > 1 else []))
    return {(m.group(1), m.group(2)) for m in rows if m}


def bound_rules(text):
    """{(rule ID, check path)} for active [LAW] entries that name their check (single-line entries)."""
    return {(m.group(1), m.group(2)) for m in BOUND_RE.finditer(text or "")}


def threshold_changes(files):
    seen = {}
    for path, (added, removed) in files.items():
        for rx, scope, loosens in THRESHOLDS:
            if not re.search(rf"(^|/){scope}$", path):
                continue
            for side, lines in (("add", [t for _, t in added]), ("rem", removed)):
                for m in (rx.search(t) for t in lines):
                    if m:
                        seen.setdefault((m["k"], loosens), {"add": [], "rem": []})[side].append((path, float(m["v"])))
    for (key, loosens), sides in seen.items():
        if not sides["rem"]:
            continue
        old = (min if loosens == "min" else max)(v for _, v in sides["rem"])
        new = (min if loosens == "min" else max)((v for _, v in sides["add"]), default=None)
        if new is None or (new < old if loosens == "min" else new > old):
            yield sides["rem"][0][0], f"{key} {old:g} -> {'removed' if new is None else format(new, 'g')}"


def find(files):
    """[(rule, path, line, token)] for every bar-lowering move in the change set."""
    out = []
    for path, (added, _) in files.items():
        checks = []  # (pattern, rule) that apply to this file
        if TEST_RX.search(path):
            checks.append((SKIP_RX, "skip"))
        if not path.endswith(DOC_EXT):
            checks.append((SUPPRESS_RX, "suppress"))
        if WORKFLOW_RX.match(path):
            checks.append((CI_SOFT_RX, "suppress"))
        for n, text in added:
            for rx, rule in checks:
                if m := rx.search(text):
                    out.append((rule, path, n, m.group(0).strip()))
    count = lambda lines: sum(1 for l in lines if ASSERT_RX.search(l))
    tests = {p: (count(t for _, t in a), count(r)) for p, (a, r) in files.items() if TEST_RX.search(p)}
    if sum(a - r for a, r in tests.values()) < 0:
        out += [("tests-removed", p, 0, f"{r - a} net assertion lines removed") for p, (a, r) in tests.items() if r > a]
    out += [("threshold", p, 0, token) for p, token in threshold_changes(files)]
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", help="diff base ref (default: merge base with the default branch)")
    args = ap.parse_args(argv)
    top = (run("rev-parse", "--show-toplevel") or "").strip()
    if not top:
        raise CouldNotRun("not a git repository")
    os.chdir(top)
    base = pr_body.resolve_base(args.base)
    if not base:
        raise CouldNotRun("no diff base (pass --base <ref>; default-branch merge base not found)")
    default = next((r for r in pr_body.default_refs() if pr_body.git("rev-parse", "--verify", "--quiet", f"{r}^{{commit}}")), None)
    diff = run("-c", "core.quotepath=off", "diff", "-U0", "-M", "--no-textconv", "--no-ext-diff", "--no-color",
               "--src-prefix=a/", "--dst-prefix=b/", base)
    if diff is None:
        raise CouldNotRun("git diff failed")
    files = parse_diff(diff)
    untracked(files)
    tip = exception_rows(run("show", f"{default}:{ARCH}") if default else "")
    allowed = [(rule, pr_body.glob_rx(g)) for rule, g in tip]
    now = exception_rows(Path(ARCH).read_text(encoding="utf-8", errors="replace") if Path(ARCH).is_file() else "")
    found = [f for f in find(files) if not any(f[0] == r and rx.match(f[1]) for r, rx in allowed)]
    found += [("exception-added", ARCH, 0, f"{r} {g}") for r, g in sorted(now - tip)]
    for rule, path, n, token in found:
        print(f"[{rule}] {path}{f':{n}' if n else ''} {token}")
    if found:
        print(f"FLOOR VIOLATION: {len(found)} finding(s). Fix the code, or route it through a tracked exception "
              f"(a `## Floor exceptions` row in {ARCH}, merged to {default}).")
        return 1
    print("floor-guard: clean")
    for rule, glob in sorted(r for r in tip if re.fullmatch(RULE_ID, r[0])):
        print(f"info: exception {rule} {glob}")
    memory = "\n".join((run("show", f"{default}:{p}") or "") if default else "" for p in (ARCH, DESIGN_RULES))
    for rule, path in sorted(bound_rules(memory)):
        print(f"info: bound {rule} {path}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except CouldNotRun as e:
        print(f"COULD-NOT-RUN: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:  # a crash must never read as a violation (1) or a pass (0)
        print(f"COULD-NOT-RUN: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
