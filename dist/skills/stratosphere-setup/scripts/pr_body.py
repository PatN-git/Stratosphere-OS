#!/usr/bin/env python3
"""pr_body.py — deterministic builder for the feature-PR body and the suite-reuse decision. Never calls `gh`.

Used by 4a Phase 5 (and 0b for suite reuse); the prior PR body is passed as a file.

  build  --slice BT-n --summary "..." --verdict PASS|WAIVED|SKIP --audit-rounds N
         [--manual-qa] [--post-merge S]... [--deviation S]... [--ref ID]... [--notes TEXT]
         [--prior-body-file F] [--base REF] [--risk-paths F] [--suite-json F]
         [--parent BT-n] [--close-parent] [--out F]
    Prints the PR body: `Closes #n.` lines, one ```stratos-pr block, optional `## Notes`.
    Slices = BT scope of every `<type>(BT-n):` commit in `git log --no-merges <base>..HEAD`. The shipped slice
    gets the fresh values; others keep summary/verdict/audit_rounds from the prior block; no prior entry ->
    PENDING (no Closes line). post_merge/deviations/refs are unioned (order-preserving) with the prior block.
    risk = tags fired by ALL files in `<base>...HEAD` against merge-risk-paths.md (+ `## One-way paths` in
    .memory/ARCHITECTURE.md); [none] when no rule fires. Exit 2 [NO-SUITE] when no suite result is reusable.
  suite  [--dir .tmp]
    Prints the newest reusable `.tmp/3d-suite-BT-*.json` (cmd, observed, head_sha) or nothing + exit 1. Reusable =
    head_sha is HEAD, or an ancestor with only `release: prepare` commits since (a bump changes no tested behaviour).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCOPE_RE = re.compile(r"^[a-z]+\(BT-(\d+)\):\s*(.*)")
RELEASE_RE = re.compile(r"^release: prepare")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
DEFAULT_RISK_PATHS = ".agents/skills/4a-verify-and-ship/references/merge-risk-paths.md"
TABLE_RULE_RE = re.compile(r"^\|\s*(`[^|]+`)\s*\|\s*`([a-z-]+)`\s*\|", re.M)
EXT_RULE_RE = re.compile(r"^[-*\s]*`?([^`\s→]+)`?\s*(?:→|->)\s*`?([\w-]+)`?\s*$")
STR = r'"(?:[^"\\]|\\.)*"'
SLICE_RE = re.compile(rf"\{{id: (BT-\d+), summary: ({STR}|[^,}}]*), verdict: (\w+), audit_rounds: (\d+)\}}")
VERDICTS = ("PASS", "WAIVED", "SKIP")


def git(*args):
    """Stripped stdout, or None when git exits non-zero. Empty output on success is "" (not None)."""
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip() if r.returncode == 0 else None


def git_ok(*args):
    """True when git exits 0 (for yes/no commands such as `merge-base --is-ancestor`)."""
    return subprocess.run(["git", *args], capture_output=True).returncode == 0


def resolve_base(given):
    if given:
        return given
    for cand in ("origin/main", "origin/master", "main", "master"):
        base = git("merge-base", "HEAD", cand)
        if base:
            return base
    return None


def union(*lists):
    out = []
    for item in (i for lst in lists for i in lst):
        if item not in out:
            out.append(item)
    return out


def glob_rx(glob):
    rx = re.escape(glob).replace(r"\*\*/", "(?:.*/)?").replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
    return re.compile(rf"^{rx}$")


def risk_rules(risk_paths):
    rules = []
    p = Path(risk_paths)
    if not p.is_file():
        print(f"[PR-BODY-WARN] risk rules not found at {risk_paths}; risk: [none] is unverified", file=sys.stderr)
    else:
        for cell, tag in TABLE_RULE_RE.findall(p.read_text(encoding="utf-8-sig")):
            rules += [(glob_rx(g), tag) for g in re.findall(r"`([^`]+)`", cell)]
    arch = Path(".memory/ARCHITECTURE.md")
    if arch.is_file():
        section = re.split(r"^## One-way paths\s*$", arch.read_text(encoding="utf-8-sig"), maxsplit=1, flags=re.M)
        for line in (section[1].split("\n## ")[0].splitlines() if len(section) > 1 else []):
            m = EXT_RULE_RE.match(line.strip())
            if m:
                rules.append((glob_rx(m.group(1)), m.group(2)))
    return rules


def parse_prior(text):
    """Return (feature, {int id: (id, summary_json, verdict, rounds)}, {list fields}, notes) from a prior body."""
    m = re.search(r"```stratos-pr\n(.*?)\n```", text, re.S)
    blk = m.group(1) if m else ""
    feature = re.search(r"^feature: (BT-\d+)", blk, re.M)
    prior = {int(s[0][3:]): s for s in SLICE_RE.findall(blk)}
    for line in blk.splitlines():
        if line.startswith("  - {id:") and not SLICE_RE.search(line):
            print(f"[PR-BODY-WARN] unparsed prior slice line: {line.strip()}", file=sys.stderr)
    lists = {}
    for name in ("post_merge", "deviations"):
        f = re.search(rf"^{name}: (\[.*\])$", blk, re.M)
        try:
            lists[name] = json.loads(f.group(1)) if f else []
        except json.JSONDecodeError:
            lists[name] = []
    refs = re.search(r"^refs: \[(.*)\]$", blk, re.M)
    lists["refs"] = [r.strip() for r in refs.group(1).split(",") if r.strip()] if refs else []
    notes = re.search(r"^## Notes\n(.*)$", text, re.M | re.S)
    return (feature.group(1) if feature else None), prior, lists, (notes.group(1).strip() if notes else "")


def check_suite(rec):
    """Return a suite record with str `cmd`/`observed` and a hex `head_sha`, else raise ValueError."""
    if not isinstance(rec, dict):
        raise ValueError("suite record must be a JSON object")
    for key in ("cmd", "observed", "head_sha"):
        if key not in rec:
            raise ValueError(f"suite record lacks {key!r}")
    if not isinstance(rec["head_sha"], str) or not SHA_RE.match(rec["head_sha"]):
        raise ValueError("suite record head_sha is not a git sha")
    return rec


def reusable_suite(dirpath):
    """Newest reusable suite record from `<dirpath>/3d-suite-BT-*.json`, else None."""
    head = git("rev-parse", "HEAD")
    for f in sorted(Path(dirpath).glob("3d-suite-BT-*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            rec = check_suite(json.loads(f.read_text(encoding="utf-8-sig")))
        except (OSError, ValueError):
            continue
        sha = rec["head_sha"]
        if sha == head:
            return rec
        if not git_ok("merge-base", "--is-ancestor", sha, "HEAD"):  # unknown sha or not an ancestor
            continue
        subjects = git("log", "--format=%s", f"{sha}..HEAD")
        if subjects is not None and all(RELEASE_RE.match(s) for s in subjects.splitlines()):
            return rec
    return None


def cmd_suite(args):
    rec = reusable_suite(args.dir)
    if not rec:
        return 1
    print(json.dumps({"cmd": rec["cmd"], "observed": rec["observed"], "head_sha": rec["head_sha"]}))
    return 0


def cmd_build(args):
    try:
        prior_text = Path(args.prior_body_file).read_text(encoding="utf-8-sig") if args.prior_body_file else ""
    except (OSError, ValueError) as e:
        print(f"[PR-BODY-ERROR] cannot read --prior-body-file: {e}", file=sys.stderr)
        return 2
    prior_feature, prior, prior_lists, prior_notes = parse_prior(prior_text)

    if args.suite_json:
        try:
            rec = check_suite(json.loads(Path(args.suite_json).read_text(encoding="utf-8-sig")))
        except (OSError, ValueError) as e:
            print(f"[PR-BODY-ERROR] bad --suite-json {args.suite_json}: {e}", file=sys.stderr)
            return 2
    else:
        rec = reusable_suite(".tmp")
    if not rec:
        print("[NO-SUITE] no reusable suite result: run the suite once and write {head_sha, cmd, observed} "
              "to .tmp/3d-suite-BT-<padded>.json", file=sys.stderr)
        return 2

    base = resolve_base(args.base)
    log = (git("log", "--no-merges", "--format=%s", f"{base}..HEAD") or "") if base else ""
    first_subject = {}  # int id -> (digits, summary of its oldest commit)
    for subject in reversed(log.splitlines()):
        m = SCOPE_RE.match(subject)
        if m:
            first_subject.setdefault(int(m.group(1)), (m.group(1), m.group(2)))
    ship = re.fullmatch(r"BT-(\d+)", args.slice)
    if not ship:
        print(f"[PR-BODY-ERROR] --slice must look like BT-<n>, got {args.slice!r}", file=sys.stderr)
        return 2
    ship_n = int(ship.group(1))
    first_subject.setdefault(ship_n, (ship.group(1), args.summary))

    rows = []
    for n in sorted(first_subject):
        digits, subject_summary = first_subject[n]
        if n == ship_n:
            row = (f"BT-{digits}", json.dumps(args.summary, ensure_ascii=False), args.verdict, str(args.audit_rounds))
        elif n in prior:
            row = prior[n]
        else:
            row = (f"BT-{digits}", json.dumps(subject_summary, ensure_ascii=False), "PENDING", "0")
        rows.append(row)

    files = (git("diff", "--name-only", f"{base}...HEAD") or "").splitlines() if base else []
    rules = risk_rules(args.risk_paths)
    tags = sorted({tag for f in files for rx, tag in rules if rx.match(f.replace("\\", "/"))})

    qa = [f"manual-QA: {args.slice}"] if args.manual_qa else []
    post_merge = union(prior_lists["post_merge"], args.post_merge, qa)
    deviations = union(prior_lists["deviations"], args.deviation)
    refs = union(prior_lists["refs"], args.ref)
    parent = args.parent or prior_feature or args.slice
    notes = args.notes if args.notes is not None else prior_notes

    closes = [f"Closes #{int(r[0][3:])}." for r in rows if r[2] != "PENDING"]
    if args.close_parent:
        closes.append(f"Closes #{int(parent[3:])}.")
    jd = lambda items: json.dumps(items, ensure_ascii=False)
    out = [*closes, "", "```stratos-pr", f"feature: {parent}", f"head: {git('rev-parse', 'HEAD')}", "slices:"]
    out += [f"  - {{id: {i}, summary: {s}, verdict: {v}, audit_rounds: {a}}}" for i, s, v, a in rows]
    out += [f'test: {{cmd: {json.dumps(rec["cmd"], ensure_ascii=False)}, '
            f'observed: {json.dumps(rec["observed"], ensure_ascii=False)}, at: {rec["head_sha"]}}}',
            f"risk: [{', '.join(tags) if tags else 'none'}]",
            f"post_merge: {jd(post_merge)}", f"deviations: {jd(deviations)}", f"refs: [{', '.join(refs)}]", "```"]
    if notes:
        out += ["## Notes", notes]
    body = "\n".join(out) + "\n"
    if args.out:
        Path(args.out).write_text(body, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(body)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Feature-PR body builder + suite-reuse check (never calls gh).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--slice", required=True)
    b.add_argument("--summary", required=True)
    b.add_argument("--verdict", required=True, choices=VERDICTS)
    b.add_argument("--audit-rounds", required=True, type=int)
    b.add_argument("--manual-qa", action="store_true")
    b.add_argument("--post-merge", action="append", default=[])
    b.add_argument("--deviation", action="append", default=[])
    b.add_argument("--ref", action="append", default=[])
    b.add_argument("--notes")
    b.add_argument("--prior-body-file")
    b.add_argument("--base", help="base ref; default: merge-base with origin/main|master, then main|master")
    b.add_argument("--risk-paths", default=DEFAULT_RISK_PATHS)
    b.add_argument("--suite-json", help="suite record; default: the reusable one in .tmp")
    b.add_argument("--parent")
    b.add_argument("--close-parent", action="store_true")
    b.add_argument("--out")
    s = sub.add_parser("suite")
    s.add_argument("--dir", default=".tmp")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    return cmd_suite(args) if args.cmd == "suite" else cmd_build(args)


if __name__ == "__main__":
    sys.exit(main())
