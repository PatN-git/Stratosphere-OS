#!/usr/bin/env python3
"""audit_eval_build.py: dev-only. Build the 4a audit test corpus from docs/research/4a-audit-eval/cases.json.

For each case: a snapshot of the slice before its audit fixes (`git archive`, so the auditor cannot read the fix from
history), the lean packet (whole issue body, tests, changed paths, per-file diff), and a fix file for the labeler
(the fix commits' messages and diffs; never handed to an auditor).

  audit_eval_build.py --out DIR [--manifest F] [--case ID]...
Writes DIR/<id>/{snapshot/, packet.md, issue.md, fix.md}. Machine-local: the manifest names each repo's checkout path.
"""
import argparse
import io
import json
import re
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "research" / "4a-audit-eval" / "cases.json"
SKIP = re.compile(r"^dist/|(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml)$|^\.memory/|\.snap$|\.html$")
TEST = re.compile(r"(^tests?/|\.test\.|\.spec\.)")
MAX_FILE_DIFF_LINES = 400


def git(repo, *args, binary=False):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def slice_commits(repo, slice_id, until):
    """Oldest-first non-merge commits scoped `(<slice>)`, up to and including `until` (a sha or 'last')."""
    shas = git(repo, "log", "--no-merges", "--format=%H", "--grep", f"({slice_id})", "--reverse").split()
    if until == "last":
        return shas
    full = git(repo, "rev-parse", until).strip()
    return shas[: shas.index(full) + 1] if full in shas else shas


def changed_paths(repo, commits):
    return sorted({p for c in commits for p in git(repo, "show", "--name-only", "--format=", c).split() if not SKIP.search(p)})


def file_diffs(repo, base, head, paths):
    """{path: diff text} with long diffs cut at MAX_FILE_DIFF_LINES and untextual changes marked, so no path is silently absent."""
    out = {}
    for p in paths:
        d = git(repo, "diff", base, head, "--", p)
        lines = d.splitlines()
        if not d.strip():
            out[p] = "(no textual diff: binary, mode-only or net-unchanged)"
        elif len(lines) > MAX_FILE_DIFF_LINES:
            out[p] = "\n".join(lines[:MAX_FILE_DIFF_LINES]) + f"\n[truncated: {len(lines) - MAX_FILE_DIFF_LINES} more diff lines]"
        else:
            out[p] = d
    return out


def build_packet(case, issue_body, paths, diffs, base, head):
    ac = re.search(r"### Acceptance Criteria.*?(?=\n### |\Z)", issue_body, re.S)
    tests = [p for p in paths if TEST.search(p)]
    parts = [f"# Lean packet for {case['slice']} (pre-fix state {head[:7]})", "",
             f"## Acceptance Criteria (issue #{case['issue']})", ac.group(0) if ac else "(no '### Acceptance Criteria' section; see the issue body below)", "",
             "## Tests added or changed", *([f"- {t}" for t in tests] or ["- (none in the slice commits)"]), "",
             "## Changed paths", *(f"- {p}" for p in paths), "",
             f"## Diff (`git diff {base[:7]} {head[:7]}`, per file)"]
    for p in paths:
        parts += [f"### {p}", "```diff", diffs[p], "```"]
    parts += ["", "## Slice issue body (full, with Overview and Notes)", issue_body]
    return "\n".join(parts)


def build_case(case, repos, out_dir):
    repo = repos[case["repo"]]["path"]
    commits = slice_commits(repo, case["slice"], case["pre"])
    head = git(repo, "rev-parse", case["pre"] if case["pre"] != "last" else commits[-1]).strip()
    base = git(repo, "rev-parse", f"{commits[0]}^").strip()
    paths = changed_paths(repo, commits)
    body = subprocess.run(["gh", "issue", "view", str(case["issue"]), "-R", repos[case["repo"]]["gh"], "--json", "body", "-q", ".body"],
                          capture_output=True, text=True, encoding="utf-8").stdout
    d = out_dir / case["id"]
    snap = d / "snapshot"
    if not snap.exists():
        snap.mkdir(parents=True)
        tarfile.open(fileobj=io.BytesIO(git(repo, "archive", head, binary=True))).extractall(snap, filter="data")
    (d / "issue.md").write_text(body, encoding="utf-8")
    (d / "packet.md").write_text(build_packet(case, body, paths, file_diffs(repo, base, head, paths), base, head), encoding="utf-8")
    fix = [f"# Fix commits for {case['slice']} (for the labeler only)"]
    for c in case["fix"]:
        fix += ["", f"## {git(repo, 'show', '-s', '--format=%h %s', c).strip()}", git(repo, "show", "--format=%b", "--stat", c), "```diff",
                git(repo, "show", "--format=", "-U3", c, "--", *[p for p in git(repo, "show", "--name-only", "--format=", c).split() if not SKIP.search(p)]), "```"]
    (d / "fix.md").write_text("\n".join(fix), encoding="utf-8")
    spec = sorted(str(p.relative_to(snap)).replace("\\", "/") for pat in ("docs/prds", "docs/design") if (snap / pat).exists()
                  for p in (snap / pat).glob(f"{case['parent']}-*.md"))
    info = {"id": case["id"], "head": head[:7], "paths": paths, "spec_docs": spec}
    (d / "case.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    return info


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", default=str(MANIFEST))
    ap.add_argument("--case", action="append", default=[])
    a = ap.parse_args(argv)
    manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    out = Path(a.out)
    for case in manifest["cases"]:
        if a.case and case["id"] not in a.case:
            continue
        info = build_case(case, manifest["repos"], out)
        print(json.dumps({k: info[k] if k != "paths" else len(info[k]) for k in info}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
