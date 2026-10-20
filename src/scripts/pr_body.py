#!/usr/bin/env python3
"""pr_body.py — deterministic builder for the unit-PR body, the suite-reuse decision and the ship-unit resolver. Never calls `gh`.

Used by 4a Phase 5 (and 0b for suite reuse), 3d/4a for the ship unit; the prior PR body is passed as a file.

  build  --slice BT-n --summary "..." --verdict PASS|WAIVED|SKIP --audit-rounds N
         [--manual-qa] [--post-merge S]... [--deviation S]... [--ref ID]... [--notes TEXT]
         [--prior-body-file F] [--base REF] [--risk-paths F] [--suite-json F]
         [--parent BT-n] [--epic BT-n]... [--close BT-n]... [--close-parent] [--out F]
    Prints the PR body: `Closes #n.` lines, one ```stratos-pr block, optional `## Notes`.
    Slices = BT scope of every `<type>(BT-n):` commit in `git log --no-merges <base>..HEAD`. The shipped slice
    gets the fresh values; others keep summary/verdict/audit_rounds from the prior block; no prior entry ->
    PENDING (no Closes line). A prior row a human set to `DROPPED` (never a `--verdict`) is kept verbatim and
    gets no Closes line. Commits scoped to an epic (`tier:epic` row in .memory/BACKLOG_MAP.md, plus any
    `--epic BT-n`; none when the file is absent and no flag is given) are not slices, except the shipped one. post_merge/deviations/refs are unioned
    (order-preserving) with the prior block.
    risk = tags fired by ALL files in `<base>...HEAD` against merge-risk-paths.md (+ `## One-way paths` in
    .memory/ARCHITECTURE.md); [none] when no rule fires. Exit 2 [NO-SUITE] when no suite result is reusable.
    <base> = --base, else the remote default branch (origin/HEAD), else origin/main|master, main|master; none
    resolves -> exit 2 [PR-BODY-ERROR] (pass --base <default-branch>). --parent and every --close must be BT-<n>
    (else exit 2). The block's `features: [BT-n, ...]` lists every epic in the PR (prior block + --parent + the
    parent of each slice row; rows carry `parent: BT-n`); a legacy single `feature:` prior block upgrades on
    rebuild. `Closes #n.` follows the slice lines for each --close epic (--close-parent = close --parent).
  suite  [--dir .tmp]
    Prints the newest reusable `.tmp/3d-suite-BT-*.json` (cmd, observed, head_sha) or nothing + exit 1 with
    `[NO-SUITE] <none|head moved|dirty tree|scoped>` on stderr. Reusable = head_sha is HEAD, or an ancestor with only
    `release: prepare` commits since (a bump changes no tested behaviour), the tree is clean outside .memory/, docs/,
    .tmp/ (4a's clean-tree guard), and `cmd` is a whole-suite command (`is_scoped`: unknown shapes count as scoped).
    Write the record with `test_gate.py record --suite BT-n -- <cmd>`, never by hand.
  unit   --slice BT-n [--milestone M] [--parent BT-n] [--parent-milestone M] [--epic] [--type T] [--slug S] [--branch B]
    Prints one JSON object `{unit, kind, globs, branch?, branch_ok?}`: the ship unit of the slice (`--epic`: of an
    epic row). unit = release `vX.Y` (own milestone `vX.Y.Z`, else the parent epic's), else the parent epic
    `BT-<n:03d>`, else the standalone issue `BT-<n:03d>`; "same ship unit" = equal `unit`. `globs` = branch-name
    patterns of the unit (legacy own-epic glob first); `branch` = `<T>/<unit>-<slug>` (T default feat) with --slug;
    `branch_ok` = --branch matches a glob. M = `v<X>.<Y>.<Z>` or none (empty, `-`, `—`). Bad input -> exit 2
    [SHIP-UNIT-ERROR]. `resolve_unit` is the only implementation of this rule; import it, never restate it.
"""
import argparse
import fnmatch
import json
import re
import shlex
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
SLICE_RE = re.compile(rf"\{{id: (BT-\d+), (?:parent: (BT-\d+), )?summary: ({STR}|[^,}}]*), verdict: (\w+), audit_rounds: (\d+)\}}")
VERDICTS = ("PASS", "WAIVED", "SKIP")
PARENT_RE = re.compile(r"BT-\d+")
MILESTONE_RE = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
TYPE_RE = re.compile(r"[a-z]+")
NONE_TOKENS = ("", "-", "—")
NO_PARENT = "—"
DRIFT_OK = (".memory/", "docs/", ".tmp/")  # paths allowed to be dirty (same set as 4a's clean-tree guard)
FULL_SIMPLE = {("npm", "test"), ("yarn", "test"), ("pnpm", "test"), ("npm", "run", "test"),
               ("yarn", "run", "test"), ("pnpm", "run", "test"), ("make", "test")}
RUNNER_FLAG_RE = re.compile(r"^(?:-q|-v|-vv|-x|--run|--no-header|-n\d+|-n=\S+|--dist=\S+|--tb=\S+|--color=\S+|--reporter=\S+)$")
RUNNER_VALUE_FLAGS = ("-n", "--dist", "-p")
SEGMENT_BREAKS = {";", "&&", "||", "|", "&"}


def git(*args):
    """Stripped stdout, or None when git exits non-zero. Empty output on success is "" (not None)."""
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip() if r.returncode == 0 else None


def git_ok(*args):
    """True when git exits 0 (for yes/no commands such as `merge-base --is-ancestor`)."""
    return subprocess.run(["git", *args], capture_output=True).returncode == 0


def default_refs():
    """Candidate refs for the default branch, best first (remote default, origin/main|master, main|master)."""
    remote_head = git("symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    return (*([remote_head] if remote_head else []), "origin/main", "origin/master", "main", "master")


def resolve_base(given):
    if given:  # an explicit base must still be a commit, else the diff is empty and risk would read [none]
        return given if git("rev-parse", "--verify", "--quiet", f"{given}^{{commit}}") else None
    for cand in default_refs():
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
    """Return ([epic ids], {int id: (id, parent, summary_json, verdict, rounds)}, {list fields}, notes) from a prior body.

    Epics come from `features: [..]`, else a legacy single `feature:` (which is also the parent of rows without one).
    """
    m = re.search(r"```stratos-pr\n(.*?)\n```", text, re.S)
    blk = m.group(1) if m else ""
    legacy = re.search(r"^feature: (BT-\d+)", blk, re.M)
    feats = re.search(r"^features: \[(.*)\]$", blk, re.M)
    features = ([f for f in re.split(r"\s*,\s*", feats.group(1).strip()) if PARENT_RE.fullmatch(f)] if feats
                else [legacy.group(1)] if legacy else [])
    row_default = legacy.group(1) if legacy and not feats else NO_PARENT
    prior = {}
    for s in SLICE_RE.findall(blk):
        row_parent = s[1] or row_default
        prior[int(s[0][3:])] = (s[0], NO_PARENT if row_parent == NO_PARENT else canon(row_parent), *s[2:])
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
    return features, prior, lists, (notes.group(1).strip() if notes else "")


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


def tree_is_clean():
    """True when no tracked change or untracked file lies outside DRIFT_OK (a rename counts both of its paths)."""
    r = subprocess.run(["git", "status", "--porcelain", "-z"], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        return False
    fields = iter(r.stdout.split(chr(0)))
    for entry in fields:
        paths = [entry[3:]] + ([next(fields, "")] if "R" in entry[:2] or "C" in entry[:2] else [])
        if entry and not all(p.startswith(DRIFT_OK) for p in paths):
            return False
    return True


def _launcher(token):
    """Lower-cased basename of a command token without its Windows extension (`C:\\Py\\python.exe` -> python)."""
    return re.sub(r"\.(exe|cmd|bat)$", "", re.split(r"[\\/]", token)[-1].lower())


def _tokens(cmd):
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        return cmd.split()


def _segment_full(t):
    """True when one command segment (no `;`, `&&`, `||`) runs the project's whole suite."""
    if t and _launcher(t[0]) == "npx":
        t = t[1:]
    if len(t) >= 3 and _launcher(t[0]) in ("python", "python3", "py") and t[1] == "-m":
        t = t[2:]
    if not t:
        return False
    head = _launcher(t[0])
    if (head, *t[1:]) in FULL_SIMPLE:
        return True
    if head in ("bash", "sh"):
        if len(t) == 3 and t[1] == "-c":
            return _command_full(t[2])
        return len(t) == 2 and t[1].endswith(".sh")
    if head in ("pytest", "vitest", "jest"):
        rest = t[1:]
        if head == "vitest" and rest[:1] == ["run"]:
            rest = rest[1:]
        i = 0
        while i < len(rest):
            if rest[i] in RUNNER_VALUE_FLAGS:
                i += 2
                continue
            if not RUNNER_FLAG_RE.match(rest[i]):
                return False
            i += 1
        return True
    return False


def _command_full(cmd):
    tokens = _tokens(cmd)
    for i, tok in enumerate(tokens[:-1]):  # drop a leading `...test_gate.py record [--suite X] --` wrapper
        if _launcher(tok) == "test_gate.py" and tokens[i + 1] == "record":
            if "--" not in tokens[i:]:
                return False
            tokens = tokens[i + tokens[i:].index("--") + 1:]
            break
    segments, current = [], []
    for tok in tokens:
        if tok in SEGMENT_BREAKS:
            segments.append(current)
            current = []
        else:
            current.append(tok)
    segments.append(current)
    return any(_segment_full(s) for s in segments)


def is_scoped(cmd):
    """True unless `cmd` (a string, or an argv list) provably runs the whole suite.

    An allowlist on purpose: an unknown command shape counts as scoped, which costs one re-run and can
    never reuse a partial run as "the suite". A command is full when any of its `;`/`&&`/`||` segments is
    (so `bash scripts/check.sh && pytest tests/jules` is full). The recorder writes `shlex.join(argv)` so the
    same string gets the same verdict at record and read time.
    """
    return not _command_full(shlex.join(cmd) if isinstance(cmd, (list, tuple)) else cmd)


def suite_status(dirpath):
    """(record, reason): the newest reusable `<dirpath>/3d-suite-BT-*.json`, else (None, why not)."""
    if not tree_is_clean():
        return None, "dirty tree"
    head = git("rev-parse", "HEAD")
    files = sorted(Path(dirpath).glob("3d-suite-BT-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    scoped_hit = False
    for f in files:
        try:
            rec = check_suite(json.loads(f.read_text(encoding="utf-8-sig")))
        except (OSError, ValueError):
            continue
        sha = rec["head_sha"]
        if sha != head:
            if not git_ok("merge-base", "--is-ancestor", sha, "HEAD"):  # unknown sha or not an ancestor
                continue
            subjects = git("log", "--format=%s", f"{sha}..HEAD")
            if subjects is None or not all(RELEASE_RE.match(s) for s in subjects.splitlines()):
                continue
        if is_scoped(rec["cmd"]):
            scoped_hit = True
            continue
        return rec, ""
    return None, "scoped" if scoped_hit else ("head moved" if files else "none")


def reusable_suite(dirpath):
    """Newest reusable suite record from `<dirpath>/3d-suite-BT-*.json`, else None."""
    return suite_status(dirpath)[0]


def cmd_suite(args):
    rec, reason = suite_status(args.dir)
    if not rec:
        print(f"[NO-SUITE] {reason}", file=sys.stderr)
        return 1
    print(json.dumps({"cmd": rec["cmd"], "observed": rec["observed"], "head_sha": rec["head_sha"]}))
    return 0


def dumps(value):
    return json.dumps(value, ensure_ascii=False)


def canon(bt):
    """`BT-7` -> `BT-007`: the repo's padded spelling, one per epic so `features:` never lists an epic twice."""
    return f"BT-{int(bt[3:]):03d}"


def backlog_rows(path=".memory/BACKLOG_MAP.md"):
    """BACKLOG_MAP rows via `reconcile.parse_backlog`; {} when the map is absent or unreadable (fails open)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import reconcile
        return reconcile.parse_backlog(path)
    except (ImportError, OSError, ValueError):
        return {}


def epic_ids(path=".memory/BACKLOG_MAP.md"):
    """Int ids of the BACKLOG_MAP rows labelled exactly `tier:epic` (BT-007 -> 7; BT-LOCAL-1 ignored).

    Fails open to an empty set when the map is absent or unreadable: an epic commit then shows as PENDING.
    """
    ids = (re.fullmatch(r"BT-0*(\d+)", bt) for bt, r in backlog_rows(path).items() if "tier:epic" in r["labels"])
    return {int(m.group(1)) for m in ids if m}


def backlog_parents(path=".memory/BACKLOG_MAP.md"):
    """{int id: 'BT-<nnn>'} of each BACKLOG_MAP row that has a parent (padded `BT-051`); {} when the map is unreadable."""
    out = {}
    for bt, r in backlog_rows(path).items():
        row, parent = re.fullmatch(r"BT-0*(\d+)", bt), re.fullmatch(r"BT-0*(\d+)", r["parent"])
        if row and parent:
            out[int(row.group(1))] = f"BT-{int(parent.group(1)):03d}"
    return out


def slice_rows(args, prior, features, base):
    """(id, parent, summary_json, verdict, rounds) per slice: BT scopes of `<base>..HEAD` commits plus the shipped slice.
    Fresh values for the shipped slice, prior-block values for others, PENDING when new (parent from BACKLOG_MAP).
    None if --slice is malformed. Commits scoped to an epic in `features` or to any other epic are not slices
    (an epic closes only via --close / --close-parent)."""
    log = git("log", "--no-merges", "--format=%s", f"{base}..HEAD") or ""
    first_subject = {}  # int id -> (digits, summary of its oldest commit)
    for subject in reversed(log.splitlines()):
        m = SCOPE_RE.match(subject)
        if m:
            first_subject.setdefault(int(m.group(1)), (m.group(1), m.group(2)))
    ship = re.fullmatch(r"BT-(\d+)", args.slice)
    if not ship:
        return None
    ship_n = int(ship.group(1))
    first_subject.setdefault(ship_n, (ship.group(1), args.summary))
    for epic_n in (epic_ids() | {int(e[3:]) for e in args.epic} | {int(f[3:]) for f in features}) - {ship_n}:
        first_subject.pop(epic_n, None)

    parents = backlog_parents()
    rows = []
    for n in sorted(first_subject):
        digits, subject_summary = first_subject[n]
        if n == ship_n:
            row = (f"BT-{digits}", canon(args.parent) if args.parent else NO_PARENT, dumps(args.summary), args.verdict, str(args.audit_rounds))
        elif n in prior:
            row = prior[n]
        else:
            row = (f"BT-{digits}", parents.get(n, NO_PARENT), dumps(subject_summary), "PENDING", "0")
        rows.append(row)
    return rows


def changed_risk_tags(base, risk_paths):
    files = (git("diff", "--name-only", f"{base}...HEAD") or "").splitlines()
    rules = risk_rules(risk_paths)
    return sorted({tag for f in files for rx, tag in rules if rx.match(f.replace("\\", "/"))})


def render_body(rows, features, closing, rec, tags, lists, notes):
    closes = union([f"Closes #{int(r[0][3:])}." for r in rows if r[3] not in ("PENDING", "DROPPED")],
                   [f"Closes #{int(c[3:])}." for c in closing])
    out = [*closes, "", "```stratos-pr", f"features: [{', '.join(features)}]", f"head: {git('rev-parse', 'HEAD')}", "slices:"]
    for i, p, s, v, a in rows:
        parent = "" if p == NO_PARENT else f"parent: {p}, "
        out.append(f"  - {{id: {i}, {parent}summary: {s}, verdict: {v}, audit_rounds: {a}}}")
    out += [f'test: {{cmd: {dumps(rec["cmd"])}, observed: {dumps(rec["observed"])}, at: {rec["head_sha"]}}}',
            f"risk: [{', '.join(tags) if tags else 'none'}]",
            f"post_merge: {dumps(lists['post_merge'])}", f"deviations: {dumps(lists['deviations'])}",
            f"refs: [{', '.join(lists['refs'])}]", "```"]
    if notes:
        out += ["## Notes", notes]
    return "\n".join(out) + "\n"


def cmd_build(args):
    if args.parent is not None and not PARENT_RE.fullmatch(args.parent):
        print(f"[PR-BODY-ERROR] --parent must look like BT-<n>, got {args.parent!r}", file=sys.stderr)
        return 2
    for flag, values in (("--epic", args.epic), ("--close", args.close)):
        bad = next((v for v in values if not PARENT_RE.fullmatch(v)), None)
        if bad is not None:
            print(f"[PR-BODY-ERROR] {flag} must look like BT-<n>, got {bad!r}", file=sys.stderr)
            return 2
    try:
        prior_text = Path(args.prior_body_file).read_text(encoding="utf-8-sig") if args.prior_body_file else ""
    except (OSError, ValueError) as e:
        print(f"[PR-BODY-ERROR] cannot read --prior-body-file: {e}", file=sys.stderr)
        return 2
    prior_features, prior, prior_lists, prior_notes = parse_prior(prior_text)

    if args.suite_json:
        try:
            rec = check_suite(json.loads(Path(args.suite_json).read_text(encoding="utf-8-sig")))
            if is_scoped(rec["cmd"]):
                raise ValueError("cmd is a scoped run, not the whole suite; record it with test_gate.py record --suite")
        except (OSError, ValueError) as e:
            print(f"[PR-BODY-ERROR] bad --suite-json {args.suite_json}: {e}", file=sys.stderr)
            return 2
    else:
        rec, reason = suite_status(".tmp")
    if not rec:
        print(f"[NO-SUITE] {reason}: no reusable suite result. Run the suite once through "
              "`python .agents/scripts/test_gate.py record --suite BT-<padded> -- <cmd>` (it writes "
              ".tmp/3d-suite-BT-<padded>.json; HEAD must match and the tree be clean outside .memory/, docs/, "
              ".tmp/)", file=sys.stderr)
        return 2
    base = resolve_base(args.base)
    if not base:
        why = f"--base {args.base!r} is not a commit" if args.base else "no origin/HEAD, main or master"
        print(f"[PR-BODY-ERROR] cannot resolve the base branch ({why}): "
              "pass --base <default-branch>; risk would otherwise be unverified", file=sys.stderr)
        return 2

    features = union([canon(f) for f in prior_features], [canon(args.parent)] if args.parent else [])
    rows = slice_rows(args, prior, features, base)
    if rows is None:
        print(f"[PR-BODY-ERROR] --slice must look like BT-<n>, got {args.slice!r}", file=sys.stderr)
        return 2
    features = union(features, [canon(r[1]) for r in rows if r[1] != NO_PARENT]) or [canon(args.slice)]
    closing = union([canon(c) for c in args.close],
                    [canon(args.parent or (prior_features[0] if prior_features else args.slice))] if args.close_parent else [])

    qa = [f"manual-QA: {args.slice}"] if args.manual_qa else []
    lists = {"post_merge": union(prior_lists["post_merge"], args.post_merge, qa),
             "deviations": union(prior_lists["deviations"], args.deviation),
             "refs": union(prior_lists["refs"], args.ref)}
    notes = args.notes if args.notes is not None else prior_notes
    tags = changed_risk_tags(base, args.risk_paths)
    body = render_body(rows, features, closing, rec, tags, lists, notes)
    if args.out:
        Path(args.out).write_text(body, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(body)
    return 0


def _milestone(value, flag):
    """(X, Y) of a `vX.Y.Z` milestone, None for a none token (None, empty, `-`, `—`); ValueError otherwise."""
    if value is None or value.strip() in NONE_TOKENS:
        return None
    m = MILESTONE_RE.fullmatch(value.strip())
    if not m:
        raise ValueError(f"{flag} must look like v<X>.<Y>.<Z> or be none (empty, '-' or an em dash), got {value!r}")
    return int(m.group(1)), int(m.group(2))


def slugify(text):
    """Lower-case, non-[a-z0-9] runs -> `-`, at most 40 chars with no leading/trailing `-`."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40].strip("-")


def resolve_unit(id, milestone, parent, parent_milestone=None, epic=False):
    """Ship unit of a slice (or of an epic row with epic=True): {unit, kind, globs}. ValueError on bad input.

    The only implementation of D1: a release `vX.Y` (own milestone, else the parent epic's), else the parent epic,
    else the issue itself (a standalone issue never joins a release). Globs are fnmatch patterns for branch names;
    the legacy own-epic glob comes first so a mid-flight per-epic branch keeps its epic. Pure; no I/O.
    """
    if not PARENT_RE.fullmatch(id):
        raise ValueError(f"--slice must look like BT-<n>, got {id!r}")
    if parent is not None and parent.strip() not in NONE_TOKENS and not PARENT_RE.fullmatch(parent):
        raise ValueError(f"--parent must look like BT-<n> or be none, got {parent!r}")
    own, inherited = _milestone(milestone, "--milestone"), _milestone(parent_milestone, "--parent-milestone")
    has_parent = parent is not None and parent.strip() not in NONE_TOKENS
    own_glob = f"*/BT-{int(id[3:]):03d}-*"
    if epic and own:
        return {"unit": f"v{own[0]}.{own[1]}", "kind": "release", "globs": [own_glob, f"*/v{own[0]}.{own[1]}-*"]}
    if epic or not has_parent:
        return {"unit": f"BT-{int(id[3:]):03d}", "kind": "epic" if epic else "issue", "globs": [own_glob]}
    parent_glob = f"*/BT-{int(parent[3:]):03d}-*"
    release = own or inherited
    if release:
        return {"unit": f"v{release[0]}.{release[1]}", "kind": "release", "globs": [parent_glob, f"*/v{release[0]}.{release[1]}-*"]}
    return {"unit": f"BT-{int(parent[3:]):03d}", "kind": "epic", "globs": [parent_glob]}


def cmd_unit(args):
    try:
        out = resolve_unit(args.slice, args.milestone, args.parent, args.parent_milestone, args.epic)
        if args.type is not None and not TYPE_RE.fullmatch(args.type):
            raise ValueError(f"--type must be lower-case letters (the commit type, e.g. feat), got {args.type!r}")
        if args.slug is not None:
            slug = slugify(args.slug)
            if not slug:
                raise ValueError(f"--slug {args.slug!r} has no letters or digits to build a branch name from")
            out["branch"] = f"{args.type or 'feat'}/{out['unit']}-{slug}"
        if args.branch is not None:
            names = {args.branch, args.branch.removeprefix("origin/")}
            out["branch_ok"] = any(fnmatch.fnmatchcase(n, g) for n in names for g in out["globs"])
    except ValueError as e:
        print(f"[SHIP-UNIT-ERROR] {e}", file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False))
    return 0


def build_parser():
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
    b.add_argument("--base", help="base ref; default: merge-base with origin/HEAD's branch, then origin/main|master, "
                                  "main|master; none resolves -> exit 2")
    b.add_argument("--risk-paths", default=DEFAULT_RISK_PATHS)
    b.add_argument("--suite-json", help="suite record; default: the reusable one in .tmp")
    b.add_argument("--parent")
    b.add_argument("--epic", action="append", default=[],
                   help="BT-n of an epic whose commits are not slices (repeatable; adds to BACKLOG_MAP's tier:epic rows)")
    b.add_argument("--close", action="append", default=[],
                   help="BT-n of an epic this PR completes: adds `Closes #n.` after the slice lines (repeatable)")
    b.add_argument("--close-parent", action="store_true", help="alias: close --parent")
    b.add_argument("--out")
    s = sub.add_parser("suite")
    s.add_argument("--dir", default=".tmp")
    u = sub.add_parser("unit", help="resolve the ship unit (release vX.Y, parent epic or issue) of a slice")
    u.add_argument("--slice", required=True, help="BT-n of the slice (of the epic with --epic)")
    u.add_argument("--milestone", help="its milestone v<X>.<Y>.<Z>; empty, -, or — = none")
    u.add_argument("--parent", help="BT-n of its parent epic; empty, -, or — = standalone")
    u.add_argument("--parent-milestone", help="the parent epic's milestone, inherited when --milestone is none")
    u.add_argument("--epic", action="store_true", help="--slice is a tier:epic row")
    u.add_argument("--type", help="commit type for --slug (default feat)")
    u.add_argument("--slug", help="print `branch` = <type>/<unit>-<slugified text>")
    u.add_argument("--branch", help="print `branch_ok`: does this branch name belong to the unit")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    return {"suite": cmd_suite, "unit": cmd_unit}.get(args.cmd, cmd_build)(args)


if __name__ == "__main__":
    sys.exit(main())
