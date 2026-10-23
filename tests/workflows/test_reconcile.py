#!/usr/bin/env python3
"""Unit tests for src/scripts/reconcile.py — the Terminal Sync Invariant gate.

Pure logic (parse_backlog, compare) with fixtures + mocked gh JSON, plus main()
exit-code paths with gh monkeypatched — fully offline and deterministic.
"""
import contextlib
import importlib.util
import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("reconcile", ROOT / "src" / "scripts" / "reconcile.py")
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)
# The map-mode checks below pass no --arch: pin the default to an absent file so the repo's own (gitignored)
# .memory/ARCHITECTURE.md, which says `tracker: github` once StratOS dogfoods it, never changes the backend under test.
rec.ARCH_DEFAULT = str(ROOT / "tests" / "workflows" / "_absent-architecture.md")

ALL = set(rec.ALL_FIELDS)
FAILS = []


def check(name, cond):
    print(("PASS" if cond else "FAIL") + f": {name}")
    if not cond:
        FAILS.append(name)


BACKLOG = """\
# BACKLOG
| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |
|----|-------|--------|--------|-----------|--------|------------|-----|-----|
| BT-XXX | placeholder | planned | area:x | v1.0.0 | — | — | ICE | — |
| BT-007 | Real slice | in review | area:api, type:feature, tier:slice, size:small | v1.2.0 | BT-005 | BT-006 | ICE: 1.0 | [[L-1]] |
| BT-009 | Standalone | planned | type:feature, tier:epic | — | — | — | ICE: 0.5 | — |
"""


def gh_issue(status="in review", milestone="v1.2.0", extra_labels=None, blocked=("6",),
             parent_num="5", comments=None, with_blockedby=True, with_parent=True,
             blocked_shape="nodes"):
    labels = [{"name": f"status:{status}"}] if status else []
    labels += [{"name": n} for n in (extra_labels if extra_labels is not None
                                      else ["area:api", "type:feature", "tier:slice", "size:small"])]
    d = {"number": 7, "labels": labels,
         "milestone": {"title": milestone} if milestone else None}
    if with_blockedby:
        # Real `gh issue view --json blockedBy` is a connection, not a list.
        nodes = [{"id": f"I_{n}", "number": int(n), "state": "OPEN", "title": f"t{n}",
                  "url": f"https://github.com/o/r/issues/{n}"} for n in blocked]
        d["blockedBy"] = ({"nodes": nodes, "totalCount": len(nodes)} if blocked_shape == "nodes"
                          else nodes if blocked_shape == "list" else None)
    if with_parent:
        d["parent"] = {"number": int(parent_num)} if parent_num else None
    if comments is not None:
        d["comments"] = comments
    return d


def write_backlog(td):
    p = Path(td) / "BACKLOG_MAP.md"
    p.write_text(BACKLOG, encoding="utf-8")
    return str(p)


ALLOPEN = """\
| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |
|----|-------|--------|--------|-----------|--------|------------|-----|-----|
| BT-001 | Shipped | done | type:feature | v1.0.0 | BT-100 | — | ICE | — |
| BT-002 | In review | in review | type:feature | v1.0.0 | BT-100 | — | ICE | — |
| BT-003 | Waits on 2 | planned | type:feature | v1.0.0 | BT-100 | BT-002 | ICE | — |
| BT-004 | Waits on 1 | planned | type:feature | v1.0.0 | BT-100 | BT-001 | ICE | — |
| BT-005 | Waits on 9 | planned | type:feature | v1.0.0 | BT-100 | BT-009 | ICE | — |
| BT-009 | In progress | in progress | type:feature | v1.0.0 | BT-100 | — | ICE | — |
"""


def _run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = rec.main(argv)
    return code, buf.getvalue()


def _arg_error(argv):
    """True when argparse rejects argv (SystemExit 2)."""
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            rec.main(argv)
    except SystemExit as e:
        return e.code == 2
    return False


def all_open_checks():
    """BT-142: --all-open advisory sweep. In-band --ids gates keep their exact semantics."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "BACKLOG_MAP.md"
        p.write_text(ALLOPEN, encoding="utf-8")
        path = str(p)
        rows = rec.parse_backlog(path)

        check("open_ids excludes done rows", rec.open_ids(rows) == ["BT-002", "BT-003", "BT-004", "BT-005", "BT-009"])
        stale = rec.stale_blockers(rows)
        check("stale blocker: blocker in review flagged", "BT-003: stale blocker BT-002 should be cleared" in stale)
        check("stale blocker: blocker done flagged", "BT-004: stale blocker BT-001 should be cleared" in stale)
        check("stale blocker: blocker in progress not flagged", not any(x.startswith("BT-005") for x in stale))
        check("stale blocker: blocker absent from map not flagged",
              rec.stale_blockers({"BT-5": {"status": "planned", "blocked_by": {"BT-404"}}}) == [])

        check("closed_on_github: CLOSED + row not done -> drift",
              rec.closed_on_github({"status": "in review"}, {"state": "CLOSED"}) == "closed on GitHub, map=in review")
        check("closed_on_github: CLOSED + row done -> ok",
              rec.closed_on_github({"status": "done"}, {"state": "CLOSED"}) is None)
        check("closed_on_github: OPEN -> ok", rec.closed_on_github({"status": "in review"}, {"state": "OPEN"}) is None)
        check("closed_on_github: state absent -> not checked", rec.closed_on_github({"status": "in review"}, {}) is None)

        check("--ids and --all-open are mutually exclusive", _arg_error(["--ids", "BT-007", "--all-open"]))
        check("one of --ids / --all-open is required", _arg_error([]))

        orig_avail, orig_fetch = rec.gh_available, rec.fetch_issue
        try:
            rec.gh_available = lambda: False
            code, out = _run(["--all-open", "--backlog", path])
            check("--all-open offline: local-only tag + stale blocker, exit 1",
                  code == 1 and "[local-only" in out
                  and "[MIRROR-DRIFT BT-003: stale blocker BT-002 should be cleared]" in out)
            check("--all-open offline + --require-gh -> exit 3",
                  rec.main(["--all-open", "--backlog", path, "--require-gh"]) == 3)
            check("--ids offline ignores the stale-blocker check",
                  rec.main(["--ids", "BT-003", "--backlog", path]) == 0)

            rec.gh_available = lambda: True
            calls = []

            def fetch(num, want_comments, want_state=False):
                calls.append((num, want_state))
                status = {"2": "in review", "3": "planned", "4": "planned", "5": "planned", "9": "in progress"}[num]
                return {"number": int(num), "labels": [{"name": f"status:{status}"}, {"name": "type:feature"}],
                        "milestone": {"title": "v1.0.0"}, "state": "CLOSED" if num == "2" else "OPEN"}
            rec.fetch_issue = fetch
            code, out = _run(["--all-open", "--backlog", path, "--fields", "status,milestone,labels"])
            check("--all-open online: closed-on-GitHub flagged",
                  "[MIRROR-DRIFT BT-002: closed on GitHub, map=in review]" in out)
            check("--all-open online: stale blocker flagged",
                  "[MIRROR-DRIFT BT-003: stale blocker BT-002 should be cleared]" in out)
            check("--all-open online: drift -> exit 1", code == 1)
            check("--all-open online: done row not fetched, open rows fetched with state",
                  sorted(c[0] for c in calls) == ["2", "3", "4", "5", "9"] and all(c[1] for c in calls))
        finally:
            rec.gh_available, rec.fetch_issue = orig_avail, orig_fetch


def summary_checks():
    """BT-163 R1: --all-open --summary groups by kind, keeps new items verbatim, ages carried ones."""
    import json
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "BACKLOG_MAP.md"
        p.write_text(ALLOPEN, encoding="utf-8")
        path, out, keys, state = str(p), Path(td) / "raw.txt", Path(td) / "keys.txt", Path(td) / "state.json"

        check("drift_kind maps every compare/closed/stale text",
              [rec.drift_kind(t) for t in ("status map=a gh=b", "milestone map=a gh=b", "labels map_only=[]",
                                           "blocked_by map=[] gh=[]", "parent map=a gh=b", "closed on GitHub, map=x",
                                           "pr-link absent", "huh")]
              == ["status", "milestone", "labels", "blocked_by", "parent", "closed", "pr_link", "other"])

        orig_avail, orig_fetch = rec.gh_available, rec.fetch_issue
        try:
            rec.gh_available = lambda: True

            def fetch(num, want_comments, want_state=False):
                status = {"2": "in review", "3": "planned", "4": "in progress", "5": "planned", "9": "in progress"}[num]
                labels = [{"name": f"status:{status}"}, {"name": "type:feature"}]
                if num == "3":
                    labels.append({"name": "area:extra"})
                return {"number": int(num), "labels": labels, "milestone": {"title": "v1.0.0"},
                        "state": "CLOSED" if num == "2" else "OPEN"}
            rec.fetch_issue = fetch
            base = ["--all-open", "--backlog", path, "--fields", "status,milestone,labels", "--state", str(state)]

            code, raw = _run(base)
            check("non-summary output unchanged: every raw line, exit 1",
                  code == 1 and raw.splitlines()[0] == "[MIRROR-DRIFT BT-003: stale blocker BT-002 should be cleared]"
                  and "[MIRROR-DRIFT BT-004: status map=planned gh=in progress]" in raw and "DRIFT-SUMMARY" not in raw)

            code, first = _run(base + ["--summary", "--out", str(out), "--keys-out", str(keys), "--date", "2026-10-13"])
            check("summary: exit code unchanged (1)", code == 1)
            check("summary: header counts and per-kind counts",
                  "[DRIFT-SUMMARY 5 items: 5 new, 0 carried]" in first
                  and "kinds: closed 1 · labels 1 · stale_blocker 2 · status 1" in first)
            check("summary: no state -> all new, listed verbatim, none carried",
                  "new:" in first and "[MIRROR-DRIFT BT-003: stale blocker BT-002 should be cleared]" in first
                  and "carried" not in first.replace("0 carried", ""))
            check("--out holds every raw line, one per line",
                  out.read_text(encoding="utf-8").splitlines() == [l for l in raw.splitlines()])
            check("--keys-out holds deduped BT-x|kind keys",
                  keys.read_text(encoding="utf-8").splitlines()
                  == ["BT-002|closed", "BT-003|labels", "BT-003|stale_blocker", "BT-004|stale_blocker", "BT-004|status"])

            state.write_text(json.dumps({"last_run": "x", "drift": {
                "BT-003|labels": {"first": "2026-10-05", "last": "2026-10-09", "nights": 2},
                "BT-004|status": {"first": "2026-10-09", "last": "2026-10-09", "nights": 1},
                "BT-003|stale_blocker": {"first": "2026-10-13", "last": "2026-10-13", "nights": 1}}}), encoding="utf-8")
            code, aged = _run(base + ["--summary", "--date", "2026-10-13"])
            check("summary: carried totals", "[DRIFT-SUMMARY 5 items: 3 new, 2 carried]" in aged)
            check("summary: chronic carried item flagged with its night", "carried labels 1: night 3: BT-003 [CHRONIC 3]" in aged)
            check("summary: young carried item aged by group", "carried status 1: night 2: BT-004" in aged)
            check("summary: carried items are not repeated verbatim",
                  "BT-004: status map" not in aged and "BT-003: labels" not in aged)
            check("summary: a key first recorded tonight (nightly_state already ran) is still new",
                  "[MIRROR-DRIFT BT-003: stale blocker BT-002 should be cleared]" in aged)
            state.write_text(json.dumps({"drift": {
                "BT-003|labels": {"first": "2026-10-05", "last": "2026-10-13", "nights": 3}}}), encoding="utf-8")
            check("summary: re-run after nightly_state recorded tonight keeps the same age",
                  "carried labels 1: night 3: BT-003 [CHRONIC 3]" in _run(base + ["--summary", "--date", "2026-10-13"])[1])
            check("summary: the next night ages it again",
                  "night 4: BT-003 [CHRONIC 4]" in _run(base + ["--summary", "--date", "2026-10-14"])[1])

            state.write_text(json.dumps({"drift": {"BT-003|labels": {"first": "2026-10-05", "nights": 2}}}), encoding="utf-8")
            check("summary: a history entry without `last` still ages (not dropped)",
                  "night 3: BT-003 [CHRONIC 3]" in _run(base + ["--summary", "--date", "2026-10-13"])[1])
            state.write_text(json.dumps({"drift": {"BT-003|labels": {"first": "2026-10-05", "last": "2026-10-09",
                                                                      "nights": 2}, "BT-099|labels": {"first": "2026-10-05",
                                                                      "last": "2026-10-09", "nights": 4}}}), encoding="utf-8")
            multi = _run(base + ["--summary", "--date", "2026-10-13"])[1]
            check("summary: carried line lists ids grouped by age", "carried labels 1: night 3: BT-003 [CHRONIC 3]" in multi)
            state.write_text("not json", encoding="utf-8")
            check("summary: malformed state reads as no history",
                  "[DRIFT-SUMMARY 5 items: 5 new, 0 carried]" in _run(base + ["--summary"])[1])
            state.unlink()
            check("summary: missing state reads as no history",
                  "[DRIFT-SUMMARY 5 items: 5 new, 0 carried]" in _run(base + ["--summary"])[1])

            rec.fetch_issue = lambda num, want_comments, want_state=False: {
                "number": int(num), "labels": [{"name": "status:planned"}, {"name": "type:feature"}],
                "milestone": {"title": "v1.0.0"}, "state": "OPEN"}
            clean = ALLOPEN.replace("| BT-003 | Waits on 2 | planned | type:feature | v1.0.0 | BT-100 | BT-002 |",
                                    "| BT-003 | Waits on 2 | planned | type:feature | v1.0.0 | BT-100 | — |").replace(
                "| BT-004 | Waits on 1 | planned | type:feature | v1.0.0 | BT-100 | BT-001 |",
                "| BT-004 | Waits on 1 | planned | type:feature | v1.0.0 | BT-100 | — |")
            clean = clean.replace("| in review |", "| planned |").replace("| in progress |", "| planned |")
            p.write_text(clean, encoding="utf-8")
            code, ok = _run(["--all-open", "--backlog", path, "--summary", "--state", str(state),
                             "--out", str(out), "--keys-out", str(keys)])
            check("summary: no drift -> MIRROR-OK, exit 0, empty out/keys",
                  code == 0 and "[MIRROR-OK 5 open rows]" in ok and out.read_text(encoding="utf-8") == ""
                  and keys.read_text(encoding="utf-8") == "")

            p.write_text(ALLOPEN, encoding="utf-8")
            rec.fetch_issue = lambda num, want_comments, want_state=False: None  # transient gh failure
            keys.write_text("BT-9|labels\n", encoding="utf-8")
            code, flaky = _run(["--all-open", "--backlog", path, "--summary", "--state", str(state),
                                "--keys-out", str(keys)])
            check("summary: every row not_found -> treated as gh unavailable, no false drift",
                  "[local-only" in flaky and "not found" not in flaky and "stale_blocker 2" in flaky and code == 1
                  and not keys.exists())
            _, flaky_plain = _run(["--all-open", "--backlog", path])
            check("non-summary keeps not-found drift lines", "gh issue #2 not found" in flaky_plain)
            rec.fetch_issue = lambda num, want_comments, want_state=False: None if num == "2" else {
                "number": int(num), "labels": [{"name": "status:planned"}, {"name": "type:feature"}],
                "milestone": {"title": "v1.0.0"}, "state": "OPEN"}
            _, partial = _run(["--all-open", "--backlog", path, "--summary", "--state", str(state)])
            check("summary: a single not_found among fetched rows is real drift",
                  "[MIRROR-DRIFT BT-002: gh issue #2 not found]" in partial and "[local-only" not in partial)

            rec.gh_available = lambda: False
            keys.write_text("BT-9|labels\n", encoding="utf-8")
            code, off = _run(["--all-open", "--backlog", path, "--summary", "--state", str(state),
                              "--keys-out", str(keys)])
            check("summary offline: local-only tag, stale items only, exit 1",
                  code == 1 and "[local-only" in off and "stale_blocker 2" in off)
            check("summary offline: partial keys never left for nightly_state", not keys.exists())
        finally:
            rec.gh_available, rec.fetch_issue = orig_avail, orig_fetch

        check("--date must be YYYY-MM-DD", _arg_error(["--all-open", "--summary", "--date", "13-10-2026"]))
        check("--summary needs --all-open", _arg_error(["--ids", "BT-007", "--summary"]))
        check("--out needs --summary", _arg_error(["--all-open", "--out", "x.txt"]))
        check("--keys-out needs --summary", _arg_error(["--all-open", "--keys-out", "x.txt"]))


HEALMAP = """\
# BACKLOG
| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |
|----|-------|--------|--------|-----------|--------|------------|-----|-----|
| BT-010 | Drifted | planned | type:feature, area:old | v1.0.0 | BT-005 | BT-006 | ICE: 1.0 | [[L-1]] |
| BT-011 | In sync | planned | type:feature | v1.0.0 | — | — | ICE: 0.5 | — |
| BT-012 | Map status token | planned | type:feature, status:planned | v1.0.0 | — | — | ICE: 0.5 | — |
"""


def _healgh(num):
    """GitHub says: BT-010 differs on every kind; BT-011 agrees with the map; BT-012 has only a new label."""
    n = int(num)
    if n == 10:
        return {"number": 10, "labels": [{"name": "status:in progress"}, {"name": "type:feature"}, {"name": "area:new"}],
                "milestone": {"title": "v1.1.0"}, "state": "OPEN", "parent": {"number": 9},
                "blockedBy": {"nodes": [{"number": 8}, {"number": 7}], "totalCount": 2}}
    labels = [{"name": "status:planned"}, {"name": "type:feature"}] + ([{"name": "area:added"}] if n == 12 else [])
    return {"number": n, "labels": labels, "milestone": {"title": "v1.0.0"}, "state": "OPEN",
            "parent": None, "blockedBy": {"nodes": [], "totalCount": 0}}


def heal_checks():
    """BT-163 R2: --heal upserts ONE kind's map cells from GitHub (never appends, never writes GitHub);
    --source map prints the gh/GraphQL commands instead."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "BACKLOG_MAP.md"
        path = str(p)
        orig_avail, orig_fetch = rec.gh_available, rec.fetch_issue
        fetched = []
        try:
            rec.gh_available = lambda: True

            def fetch(num, want_comments, want_state=False):
                fetched.append(num)
                return None if num == "99" else _healgh(num)
            rec.fetch_issue = fetch

            def row(n):
                return next(l for l in p.read_text(encoding="utf-8").splitlines() if l.startswith(f"| BT-{n} "))

            def cells(n):
                return [c.strip() for c in row(n).split("|")[1:-1]]

            expect = {  # kind -> (cell index, healed cell text)
                "status": (2, "in progress"), "labels": (3, "area:new, type:feature"), "milestone": (4, "v1.1.0"),
                "parent": (5, "BT-009"), "blocked_by": (6, "BT-007, BT-008")}
            before = ["BT-010", "Drifted", "planned", "type:feature, area:old", "v1.0.0", "BT-005", "BT-006", "ICE: 1.0", "[[L-1]]"]
            for kind, (idx, text) in expect.items():
                p.write_text(HEALMAP, encoding="utf-8")
                code, out = _run(["--heal", "--kind", kind, "--source", "gh", "--ids", "BT-010", "--backlog", path])
                want = list(before)
                want[idx] = text
                check(f"heal {kind}: only that cell of that row is upserted from GitHub", code == 0 and cells("010") == want)
                check(f"heal {kind}: prints [HEALED] and [HEAL-DONE ... GitHub untouched]",
                      f"[HEALED {kind} BT-010]" in out and "1 healed" in out and "GitHub untouched" in out)
                check(f"heal {kind}: re-run is a no-op (in sync)",
                      "0 healed, 1 in sync" in _run(["--heal", "--kind", kind, "--source", "gh", "--ids", "BT-010",
                                                     "--backlog", path])[1])
            check("heal: rows are never appended and other rows are untouched",
                  len([l for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("| BT-")]) == 3
                  and row("011") == [l for l in HEALMAP.splitlines() if l.startswith("| BT-011 ")][0])
            check("heal: no .tmp left behind", not (Path(td) / "BACKLOG_MAP.md.tmp").exists())

            p.write_text(HEALMAP, encoding="utf-8")
            _run(["--heal", "--kind", "labels", "--source", "gh", "--ids", "BT-012", "--backlog", path])
            check("heal labels keeps the map's own status:* token", cells("012")[3] == "area:added, status:planned, type:feature")

            p.write_text(HEALMAP, encoding="utf-8")
            n0 = len(fetched)
            code, out = _run(["--heal", "--kind", "milestone", "--source", "gh", "--all-open", "--backlog", path])
            check("heal --all-open covers every open row",
                  sorted(fetched[n0:]) == ["10", "11", "12"] and "1 healed, 2 in sync" in out)

            p.write_bytes(HEALMAP.replace("\n", "\r\n").encode("utf-8"))
            _run(["--heal", "--kind", "milestone", "--source", "gh", "--ids", "BT-010", "--backlog", path])
            raw = p.read_bytes()
            check("heal preserves CRLF line endings and writes no BOM",
                  raw.count(b"\r\n") == HEALMAP.count("\n") and b"\n" not in raw.replace(b"\r\n", b"")
                  and not raw.startswith(b"\xef\xbb\xbf"))

            p.write_text(HEALMAP, encoding="utf-8")
            code, out = _run(["--heal", "--kind", "labels", "--source", "gh", "--ids", "BT-404,BT-LOCAL-x,BT-010",
                              "--backlog", path])
            check("heal: an id absent from the map is skipped, never appended; others still heal; exit 1",
                  code == 1 and "[HEAL-SKIP BT-404: absent from BACKLOG_MAP; rows are never appended]" in out
                  and "[HEALED labels BT-010]" in out and "BT-404" not in p.read_text(encoding="utf-8"))
            p.write_text(HEALMAP.replace("| BT-011 |", "| BT-099 |"), encoding="utf-8")
            code, out = _run(["--heal", "--kind", "labels", "--source", "gh", "--ids", "BT-099", "--backlog", path])
            check("heal: a gh issue that cannot be read is skipped with exit 1", code == 1 and "gh issue #99 not found" in out)

            # status with no status:* label on GitHub cannot be healed from GitHub
            p.write_text(HEALMAP, encoding="utf-8")
            rec.fetch_issue = lambda num, want_comments, want_state=False: dict(_healgh(num), labels=[{"name": "type:feature"}])
            code, out = _run(["--heal", "--kind", "status", "--source", "gh", "--ids", "BT-010", "--backlog", path])
            check("heal status: GitHub without a status:* label is skipped, map unchanged",
                  code == 1 and "GitHub has no status:* label" in out and p.read_text(encoding="utf-8") == HEALMAP)
            rec.fetch_issue = fetch

            # --source map: nothing written, exact commands printed
            p.write_text(HEALMAP, encoding="utf-8")
            node = lambda n: f'"$(gh issue view {n} --json id -q .id)"'
            for kind, needles in {
                "status": ['gh issue edit 10 --remove-label "status:in progress" --add-label "status:planned"'],
                "milestone": ['gh issue edit 10 --milestone "v1.0.0"'],
                "labels": ['gh issue edit 10 --add-label "area:old" --remove-label "area:new"'],
                "parent": ["removeSubIssue(input:{issueId:$i,subIssueId:$j})", f"-f i={node(9)} -f j={node(10)}",
                           "addSubIssue(input:{issueId:$i,subIssueId:$j})", f"-f i={node(5)} -f j={node(10)}"],
                "blocked_by": ["addBlockedBy(input:{issueId:$i,blockingIssueId:$j})", f"-f i={node(10)} -f j={node(6)}",
                               "removeBlockedBy(input:{issueId:$i,blockingIssueId:$j})"],
            }.items():
                code, out = _run(["--heal", "--kind", kind, "--source", "map", "--ids", "BT-010,BT-011", "--backlog", path])
                check(f"heal {kind} --source map: prints the exact gh commands, runs/writes nothing",
                      code == 0 and all(n in out for n in needles) and "# BT-010" in out and "# BT-011" not in out
                      and "1 issues need GitHub edits, 1 in sync" in out and "nothing run or written" in out
                      and p.read_text(encoding="utf-8") == HEALMAP)
            check("heal blocked_by --source map: removes the two GitHub-only edges, adds the map-only one",
                  out.count("removeBlockedBy(") == 2 and out.count("addBlockedBy(") == 1)
            p.write_text(HEALMAP.replace("| v1.0.0 | BT-005 |", "| — | BT-005 |"), encoding="utf-8")
            _, out = _run(["--heal", "--kind", "milestone", "--source", "map", "--ids", "BT-010", "--backlog", path])
            check("heal milestone --source map: a cleared map milestone is removed on GitHub",
                  "gh issue edit 10 --remove-milestone" in out)

            # BT-LOCAL rows: not applicable (own count), never a skip, never `gh issue view None`
            local_map = HEALMAP + "| BT-LOCAL-x | Local only | planned | type:feature | — | — | — | ICE: 0.1 | — |\n"
            p.write_text(local_map, encoding="utf-8")
            code, out = _run(["--heal", "--kind", "labels", "--source", "gh", "--all-open", "--backlog", path])
            check("heal --all-open: an open BT-LOCAL row is counted local, not skipped (exit 0)",
                  code == 0 and "1 local, 0 skipped" in out and "HEAL-SKIP" not in out)
            code, out = _run(["--heal", "--kind", "labels", "--source", "map", "--all-open", "--backlog", path])
            check("heal --source map: local rows are counted local too", code == 0 and "1 local" in out)
            code, out = _run(["--heal", "--kind", "labels", "--source", "gh", "--ids", "BT-404", "--backlog", path])
            check("heal: an id absent from the map alone still exits 1", code == 1 and "HEAL-SKIP BT-404" in out)
            lrow = {"status": "planned", "labels": set(), "milestone": "—", "parent": "BT-LOCAL-p",
                    "blocked_by": {"BT-LOCAL-b", "BT-006"}}
            lgh = {"labels": [], "milestone": None, "parent": None, "blockedBy": {"nodes": [], "totalCount": 0}}
            cmds = rec.gh_fix_commands("parent", "10", lrow, lgh) + rec.gh_fix_commands("blocked_by", "10", lrow, lgh)
            check("relation commands skip a BT-LOCAL id with a comment, never `None`",
                  "# skip BT-LOCAL-p: no GitHub issue" in cmds and "# skip BT-LOCAL-b: no GitHub issue" in cmds
                  and sum("addBlockedBy" in c for c in cmds) == 1 and not any("None" in c for c in cmds))
            rm = rec.gh_fix_commands("parent", "10", dict(lrow, parent="—"), dict(lgh, parent={"number": 9}))
            check("removeSubIssue is printed when the map has no parent", len(rm) == 1 and "removeSubIssue" in rm[0])

            # BT-162 F5: a blocker the map already cleared (its row is in review/done) is never written back
            stale_map = HEALMAP.replace("| BT-010 | Drifted | planned | type:feature, area:old | v1.0.0 | BT-005 | BT-006 |",
                                        "| BT-010 | Drifted | planned | type:feature, area:old | v1.0.0 | BT-005 | — |") + (
                "| BT-007 | Blocker in review | in review | type:feature | v1.0.0 | BT-005 | — | ICE: 0.5 | — |\n"
                "| BT-008 | Blocker planned | planned | type:feature | v1.0.0 | BT-005 | — | ICE: 0.5 | — |\n")
            p.write_text(stale_map, encoding="utf-8")
            code, out = _run(["--heal", "--kind", "blocked_by", "--source", "gh", "--ids", "BT-010", "--backlog", path])
            check("heal blocked_by: a stale blocker (in review/done) is skipped with exit 1, the rest is healed",
                  code == 1 and "[HEAL-SKIP BT-010 blocked_by: stale on GitHub; use --source map]" in out
                  and cells("010")[6] == "BT-008" and "BT-007" not in row("010"))
            p.write_text(stale_map.replace("| BT-008 | Blocker planned | planned |", "| BT-008 | Blocker done | done |"),
                         encoding="utf-8")
            before_text = p.read_text(encoding="utf-8")
            code, out = _run(["--heal", "--kind", "blocked_by", "--source", "gh", "--ids", "BT-010", "--backlog", path])
            check("heal blocked_by: all-stale blockers leave the map untouched",
                  code == 1 and out.count("[HEAL-SKIP BT-010 blocked_by") == 1 and "0 healed" in out
                  and p.read_text(encoding="utf-8") == before_text)

            # a failed write leaves neither a half-written map nor a stray .tmp
            p.write_text(HEALMAP, encoding="utf-8")
            real_replace = rec.os.replace
            rec.os.replace = lambda *a, **k: (_ for _ in ()).throw(OSError("boom"))
            try:
                try:
                    _run(["--heal", "--kind", "labels", "--source", "gh", "--ids", "BT-010", "--backlog", path])
                    failed = False
                except OSError:
                    failed = True
            finally:
                rec.os.replace = real_replace
            check("heal: a failed swap unlinks the .tmp and leaves the map intact",
                  failed and not (Path(td) / "BACKLOG_MAP.md.tmp").exists() and p.read_text(encoding="utf-8") == HEALMAP)

            # refusals
            check("heal needs --kind", _arg_error(["--heal", "--source", "gh", "--ids", "BT-010"]))
            check("heal needs --source", _arg_error(["--heal", "--kind", "labels", "--ids", "BT-010"]))
            check("heal needs an id scope (--ids or --all-open)", _arg_error(["--heal", "--kind", "labels", "--source", "gh"]))
            check("heal takes one known kind",
                  _arg_error(["--heal", "--kind", "stale_blocker", "--source", "gh", "--ids", "BT-010"])
                  and _arg_error(["--heal", "--kind", "closed", "--source", "gh", "--ids", "BT-010"])
                  and _arg_error(["--heal", "--kind", "labels,parent", "--source", "gh", "--ids", "BT-010"]))
            check("heal is not combined with --summary",
                  _arg_error(["--heal", "--kind", "labels", "--source", "gh", "--all-open", "--summary"]))
            check("--kind / --source need --heal", _arg_error(["--ids", "BT-010", "--kind", "labels"])
                  and _arg_error(["--ids", "BT-010", "--source", "gh"]))
            p.write_text(HEALMAP, encoding="utf-8")
            n1 = len(fetched)
            _arg_error(["--heal", "--source", "gh", "--ids", "BT-010", "--backlog", path])
            check("a refused heal reads nothing and writes nothing", len(fetched) == n1 and p.read_text(encoding="utf-8") == HEALMAP)

            rec.gh_available = lambda: False
            code, out = _run(["--heal", "--kind", "labels", "--source", "gh", "--ids", "BT-010", "--backlog", path])
            check("heal without gh: exit 3, nothing written",
                  code == 3 and "[HEAL-UNAVAILABLE" in out and p.read_text(encoding="utf-8") == HEALMAP)

            # non-heal behaviour unchanged: the gate still reports drift and never edits the map
            rec.gh_available = lambda: True
            code, out = _run(["--ids", "BT-010", "--backlog", path])
            check("non-heal run still reports drift (exit 1) and never edits the map",
                  code == 1 and "[MIRROR-DRIFT BT-010: labels" in out and p.read_text(encoding="utf-8") == HEALMAP)
        finally:
            rec.gh_available, rec.fetch_issue = orig_avail, orig_fetch


DONEMAP = """\
| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |
|----|-------|--------|--------|-----------|--------|------------|-----|-----|
| BT-021 | Shipped slice | done | area:api, type:feature, tier:slice, size:small | v1.2.0 | BT-005 | BT-006 | ICE: 1.0 | — |
| BT-022 | Slice in review | in review | area:api, type:feature, tier:slice, size:small | v1.2.0 | BT-005 | BT-006 | ICE: 1.0 | — |
"""


def ids_state_checks():
    """BT-188: the --ids gate fetches `state` under --fields status, so a done row whose issue is still
    OPEN (a dropped `gh issue close` at ship) and a CLOSED issue mapped short of done both fail the gate."""
    done, review = {"status": "done"}, {"status": "in review"}
    check("open_on_github: done + OPEN -> drift", rec.open_on_github(done, {"state": "OPEN"}) == "open on GitHub, map=done")
    check("open_on_github: done + CLOSED -> ok", rec.open_on_github(done, {"state": "CLOSED"}) is None)
    check("open_on_github: in review + OPEN -> ok", rec.open_on_github(review, {"state": "OPEN"}) is None)
    check("open_on_github: in progress + OPEN -> ok",
          rec.open_on_github({"status": "in progress"}, {"state": "OPEN"}) is None)
    check("open_on_github: state absent -> not checked", rec.open_on_github(done, {}) is None)
    check("drift_kind: open on GitHub -> closed", rec.drift_kind("open on GitHub, map=done") == "closed")

    orig_avail, orig_fetch = rec.gh_available, rec.fetch_issue
    try:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "BACKLOG_MAP.md"
            p.write_text(DONEMAP, encoding="utf-8")
            path = str(p)
            rec.gh_available = lambda: True
            asked = []

            def serve(status, state):
                def fetch(num, want_comments, want_state=False):
                    asked.append(want_state)
                    return dict(gh_issue(status=status), state=state)
                return fetch

            rec.fetch_issue = serve("done", "OPEN")
            code, out = _run(["--ids", "BT-021", "--backlog", path, "--fields", "status,blocked_by"])
            check("--ids --fields status: done + OPEN -> exit 1 with the drift line",
                  code == 1 and "[MIRROR-DRIFT BT-021: open on GitHub, map=done]" in out)
            check("--ids --fields status: state is requested", asked == [True])
            rec.fetch_issue = serve("done", "CLOSED")
            check("--ids --fields status: done + CLOSED -> exit 0",
                  _run(["--ids", "BT-021", "--backlog", path, "--fields", "status,blocked_by"])[0] == 0)

            asked.clear()
            rec.fetch_issue = serve("done", "OPEN")
            code, out = _run(["--ids", "BT-021", "--backlog", path, "--fields", "blocked_by"])
            check("--ids --fields blocked_by: state not requested, done + OPEN passes",
                  code == 0 and asked == [False] and "open on GitHub" not in out)

            rec.fetch_issue = serve("in review", "CLOSED")
            code, out = _run(["--ids", "BT-022", "--backlog", path, "--fields", "status"])
            check("--ids --fields status: CLOSED + map in review -> exit 1",
                  code == 1 and "[MIRROR-DRIFT BT-022: closed on GitHub, map=in review]" in out)
    finally:
        rec.gh_available, rec.fetch_issue = orig_avail, orig_fetch


EDGE_BASE = {  # id: (status, tier, milestone, parent, blocked_by) -- cleantech_jobs shape
    "BT-051": ("in progress", "epic", "v1.2.0", "—", "—"),
    "BT-204": ("in progress", "epic", "v1.2.0", "—", "—"),
    "BT-070": ("in review", "slice", "v1.2.5", "BT-051", "—"),
    "BT-207": ("planned", "slice", "v1.2.6", "BT-204", "BT-070"),
    "BT-300": ("planned", "epic", "v1.3.0", "—", "BT-051"),
    "BT-301": ("planned", "slice", "v1.3.1", "BT-300", "BT-070"),
    "BT-302": ("planned", "slice", "v1.3.2", "BT-300", "—"),
    "BT-309": ("planned", "epic", "—", "—", "—"),
    "BT-310": ("planned", "slice", "—", "BT-300", "—"),
}


def edge_text(status=None, blocked=None):
    """BACKLOG_MAP text of EDGE_BASE with status / blocked_by overrides ({id: value}). BT-309 is standalone (no tier)."""
    lines = ["| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |",
             "|----|-------|--------|--------|-----------|--------|------------|-----|-----|"]
    for bt, (st, tier, ms, parent, blk) in EDGE_BASE.items():
        label = "type:feature" if bt == "BT-309" else f"type:feature, tier:{tier}"
        lines.append(f"| {bt} | t | {(status or {}).get(bt, st)} | {label} | {ms} | {parent} | "
                     f"{(blocked or {}).get(bt, blk)} | ICE | — |")
    return "\n".join(lines) + "\n"


def edge_rows(status=None, blocked=None):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "BACKLOG_MAP.md"
        p.write_text(edge_text(status, blocked), encoding="utf-8")
        return rec.parse_backlog(p)


def _merged(table):
    """merged_of stub over {bt: 'merged'|'open'|'none'|None}; `.calls` records the lookups."""
    def merged_of(bt):
        merged_of.calls.append(bt)
        return table.get(bt)
    merged_of.calls = []
    return merged_of


def edge_checks():
    """BT-192: D3 predicate (same ship unit -> shipped; cross unit -> code on the default branch) and --edges."""
    rows = edge_rows()
    verdict = lambda dep, blk, r=None, m=None: rec.edge_verdict(dep, blk, r or rows, m or _merged({}))

    # 1. ship_unit adapter smoke (the rule itself is tested with pr_body.resolve_unit)
    check("ship_unit: slices v1.2.5 and v1.2.6 share release v1.2",
          rec.ship_unit("BT-070", rows) == rec.ship_unit("BT-207", rows) == "v1.2")
    check("ship_unit: milestone-less slice inherits its epic's release", rec.ship_unit("BT-310", rows) == "v1.3")
    check("ship_unit: epic row with a milestone is in that release", rec.ship_unit("BT-051", rows) == "v1.2")
    check("ship_unit: epic without a milestone is its own unit", rec.ship_unit("BT-309", rows) == "BT-309")
    standalone = edge_rows()
    standalone["BT-400"] = {"status": "planned", "labels": {"type:feature"}, "milestone": "v1.2.0",
                            "parent": "—", "blocked_by": set()}
    check("ship_unit: a standalone issue is its own unit even with a milestone",
          rec.ship_unit("BT-400", standalone) == "BT-400")
    bad = edge_rows()
    bad["BT-207"]["milestone"] = "Backlog"
    check("ship_unit: bad milestone -> None (unknown), never a crash", rec.ship_unit("BT-207", bad) is None)
    check("ship_unit: absent row -> None", rec.ship_unit("BT-404", rows) is None)

    # 2. same unit: shipped = in review | done
    for st, want in (("in review", "OK"), ("done", "OK"), ("in progress", "UNMET"), ("planned", "UNMET"),
                     ("blocked", "UNMET")):
        m = _merged({})
        v = rec.edge_verdict("BT-207", "BT-070", edge_rows({"BT-070": st}), m)
        check(f"same unit: blocker {st} -> {want}", v[0] == want and v[1] == "same-unit" and not m.calls)

    # 3. cross unit, child-slice blocker: the blocker's PR must be merged
    for state, want in (("merged", "OK"), ("open", "UNMET"), (None, "UNKNOWN"), ("none", "OK")):
        v = verdict("BT-301", "BT-070", m=_merged({"BT-070": state}))
        check(f"cross unit child blocker, PR {state} -> {want}", v[0] == want and v[1] == "cross-unit")
    m = _merged({"BT-070": "merged"})
    v = rec.edge_verdict("BT-301", "BT-070", edge_rows({"BT-070": "planned"}), m)
    check("cross unit child blocker not shipped -> UNMET without a PR lookup", v[0] == "UNMET" and not m.calls)
    m = _merged({"BT-070": "merged"})
    check("cross unit child blocker done + merged -> OK",
          rec.edge_verdict("BT-301", "BT-070", edge_rows({"BT-070": "done"}), m)[0] == "OK" and m.calls == ["BT-070"])

    # 4. cross unit, epic/standalone blocker: merged <=> closed <=> done (in review = PR still open)
    for st, want in (("done", "OK"), ("in review", "UNMET"), ("in progress", "UNMET")):
        m = _merged({})
        v = rec.edge_verdict("BT-300", "BT-051", edge_rows({"BT-051": st}), m)
        check(f"cross unit epic blocker {st} -> {want}, no PR lookup", v[0] == want and v[1] == "cross-unit" and not m.calls)
    check("blocker row absent -> UNKNOWN", verdict("BT-207", "BT-404")[0] == "UNKNOWN")
    check("dependent with an unresolvable milestone -> UNKNOWN", rec.edge_verdict("BT-207", "BT-070", bad, _merged({}))[0] == "UNKNOWN")

    # 5. effective blockers = own + parent epic's, deduped, never the dependent itself
    check("effective_blockers: inherited from the parent epic", rec.effective_blockers("BT-302", rows) == {"BT-051"})
    check("effective_blockers: own + parent's", rec.effective_blockers("BT-301", rows) == {"BT-070", "BT-051"})
    both = edge_rows(blocked={"BT-302": "BT-051"})
    check("effective_blockers: deduped", rec.effective_blockers("BT-302", both) == {"BT-051"})
    selfie = edge_rows(blocked={"BT-300": "BT-051, BT-302"})
    check("effective_blockers: a dependent never blocks itself", rec.effective_blockers("BT-302", selfie) == {"BT-051"})
    check("effective_blockers: parent row absent -> own only",
          rec.effective_blockers("BT-310", {"BT-310": dict(rows["BT-310"], parent="BT-999", blocked_by={"BT-070"})}) == {"BT-070"})
    check("inherited epic blocker is UNMET while the epic is in progress", verdict("BT-302", "BT-051")[0] == "UNMET")

    orig_avail, orig_state = rec.gh_available, rec.pr_merge_state
    try:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "BACKLOG_MAP.md"
            path = str(p)
            p.write_text(edge_text(), encoding="utf-8")
            rec.gh_available = lambda: True
            looked = []

            def state(table):
                def pr_state(bt, cache=None):
                    looked.append(bt)
                    return table.get(bt)
                return pr_state
            rec.pr_merge_state = state({"BT-070": "open"})

            # 6. --edges dependents
            code, out = _run(["--edges", "dependents", "--ids", "BT-070", "--backlog", path])
            lines = out.splitlines()
            check("dependents: same-unit edge CLEAR with a removeBlockedBy cmd line, exit 0",
                  code == 0 and lines[0].startswith("[CLEAR BT-207 <- BT-070] same-unit: ")
                  and lines[1].startswith("  cmd: ") and "removeBlockedBy" in lines[1])
            check("dependents: cross-unit edge with the PR open is KEEP (no cmd)",
                  any(l.startswith("[KEEP BT-301 <- BT-070] cross-unit: ") for l in lines)
                  and sum("cmd:" in l for l in lines) == 1)
            rec.pr_merge_state = state({"BT-070": "merged"})
            _, out = _run(["--edges", "dependents", "--ids", "BT-070", "--backlog", path])
            check("dependents: merged PR -> CLEAR", "[CLEAR BT-301 <- BT-070] cross-unit: " in out and "[KEEP" not in out)
            code, out = _run(["--edges", "dependents", "--all-open", "--backlog", path])
            heads = [l.split("]")[0] + "]" for l in out.splitlines() if l.startswith("[")]
            check("dependents --all-open: every stored edge once",
                  code == 0 and sorted(heads) == sorted(["[CLEAR BT-207 <- BT-070]", "[CLEAR BT-301 <- BT-070]",
                                                         "[KEEP BT-300 <- BT-051]"]))
            code, out = _run(["--edges", "dependents", "--ids", "BT-404", "--backlog", path])
            check("dependents: absent id -> exit 1", code == 1 and "BT-404" in out)
            looked.clear()
            _run(["--edges", "dependents", "--ids", "BT-051", "--backlog", path])
            check("dependents: epic blocker edges need no PR lookup", looked == [])

            # 7. --edges blockers exit codes and tokens
            p.write_text(edge_text(blocked={"BT-301": "BT-070"}), encoding="utf-8")
            code, out = _run(["--edges", "blockers", "--ids", "BT-207", "--backlog", path])
            check("blockers: all OK -> exit 0 with [BLOCKER-OK BT-207 <- BT-070] same-unit",
                  code == 0 and out.startswith("[BLOCKER-OK BT-207 <- BT-070] same-unit: "))
            code, out = _run(["--edges", "blockers", "--ids", "BT-302", "--backlog", path])
            check("blockers: parent epic's edge is UNMET -> exit 1",
                  code == 1 and out.startswith("[BLOCKER-UNMET BT-302 <- BT-051] cross-unit: "))
            rec.pr_merge_state = state({"BT-070": None})
            code, out = _run(["--edges", "blockers", "--ids", "BT-301", "--backlog", path])
            check("blockers: unknown PR state -> [BLOCKER-UNKNOWN], exit 1",
                  code == 1 and "[BLOCKER-UNKNOWN BT-301 <- BT-070] cross-unit: " in out)
            code, out = _run(["--edges", "blockers", "--ids", "BT-309", "--backlog", path])
            check("blockers: no effective blockers -> [BLOCKERS-NONE], exit 0",
                  code == 0 and out.strip() == "[BLOCKERS-NONE BT-309]")
            code, out = _run(["--edges", "blockers", "--ids", "BT-404", "--backlog", path])
            check("blockers: absent id -> exit 1", code == 1 and "BT-404" in out)
            code, out = _run(["--edges", "blockers", "--ids", "BT-207,BT-309", "--backlog", path])
            check("blockers: several ids, one line per edge", code == 0 and len(out.splitlines()) == 2)
            code, out = _run(["--edges", "blockers", "--all-open", "--backlog", path])
            check("blockers --all-open covers every open row", code == 1 and "[BLOCKER-OK BT-207 <- BT-070]" in out
                  and "[BLOCKERS-NONE BT-309]" in out)

            # 10. offline: same-unit edges still decide; cross-unit child edges are UNKNOWN, no gh lookup
            rec.gh_available = lambda: False
            looked.clear()
            code, out = _run(["--edges", "blockers", "--ids", "BT-207", "--backlog", path])
            check("offline blockers: same-unit edge -> exit 0", code == 0 and "[BLOCKER-OK BT-207 <- BT-070]" in out)
            code, out = _run(["--edges", "blockers", "--ids", "BT-301", "--backlog", path])
            check("offline blockers: cross-unit child blocker -> [BLOCKER-UNKNOWN], exit 1",
                  code == 1 and "[BLOCKER-UNKNOWN BT-301 <- BT-070]" in out)
            code, out = _run(["--edges", "dependents", "--ids", "BT-070", "--backlog", path])
            check("offline dependents: KEEP for the unknown edge, CLEAR for same-unit, exit 0",
                  code == 0 and "[KEEP BT-301 <- BT-070]" in out and "[CLEAR BT-207 <- BT-070]" in out)
            check("offline: pr_merge_state is never called", looked == [])
    finally:
        rec.gh_available, rec.pr_merge_state = orig_avail, orig_state

    # 8. stale_blockers flags an edge only when the predicate says OK
    xrows = edge_rows(blocked={"BT-301": "BT-070"})
    for state_, flagged in (("open", False), (None, False), ("merged", True)):
        out = rec.stale_blockers(xrows, _merged({"BT-070": state_}))
        check(f"stale_blockers: cross-unit child edge, PR {state_} -> {'flagged' if flagged else 'not flagged'}",
              ("BT-301: stale blocker BT-070 should be cleared" in out) == flagged)
    check("stale_blockers: same-unit shipped edge flagged without a PR lookup",
          "BT-207: stale blocker BT-070 should be cleared" in rec.stale_blockers(xrows, _merged({})))
    check("stale_blockers: default merged_of is unknown (never flags a cross-unit child edge)",
          not any(x.startswith("BT-301") for x in rec.stale_blockers(xrows)))

    # 9. heal skip: only an OK edge is skipped; a kept cross-unit edge GitHub still has is healed from gh
    heal_map = HEALMAP.replace("| BT-010 | Drifted | planned | type:feature, area:old | v1.0.0 | BT-005 | BT-006 |",
                               "| BT-010 | Drifted | planned | type:feature, area:old | v1.0.0 | BT-005 | — |") + (
        "| BT-007 | Blocker in review | in review | type:feature, tier:slice | v1.1.0 | BT-020 | — | ICE: 0.5 | — |\n"
        "| BT-008 | Blocker planned | planned | type:feature | v1.0.0 | BT-005 | — | ICE: 0.5 | — |\n")
    orig_avail, orig_fetch, orig_state = rec.gh_available, rec.fetch_issue, rec.pr_merge_state
    try:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "BACKLOG_MAP.md"
            path = str(p)
            rec.gh_available = lambda: True
            rec.fetch_issue = lambda num, want_comments, want_state=False: _healgh(num)
            for pr, skipped in (("open", False), ("merged", True)):
                rec.pr_merge_state = lambda bt, cache=None, pr=pr: pr
                p.write_text(heal_map, encoding="utf-8")
                code, out = _run(["--heal", "--kind", "blocked_by", "--source", "gh", "--ids", "BT-010", "--backlog", path])
                cell = [c.strip() for c in next(l for l in p.read_text(encoding="utf-8").splitlines()
                                                if l.startswith("| BT-010 ")).split("|")[1:-1]][6]
                check(f"heal blocked_by: cross-unit child blocker, PR {pr} -> "
                      f"{'skipped as stale' if skipped else 'healed from gh, not skipped'}",
                      ("HEAL-SKIP BT-010 blocked_by" in out) == skipped and cell == ("BT-008" if skipped else "BT-007, BT-008")
                      and code == (1 if skipped else 0))
    finally:
        rec.gh_available, rec.fetch_issue, rec.pr_merge_state = orig_avail, orig_fetch, orig_state

    # 11. pr_merge_state: last /pull/ comment wins; tri-state plus None
    orig_json, orig_pr = rec._gh_json, rec._pr_state
    try:
        asked = []

        def pr_state(k):
            asked.append(k)
            return {"10": "OPEN", "11": "MERGED", "12": "CLOSED", "13": None}[k]

        def comments(*bodies):
            return lambda num, fields: {"comments": [{"body": b} for b in bodies]}
        rec._pr_state = pr_state
        rec._gh_json = comments("Shipped in PR #10 https://x/o/r/pull/10", "noise", "Re-shipped https://x/o/r/pull/11")
        check("pr_merge_state: the last /pull/ comment wins -> merged", rec.pr_merge_state("BT-070") == "merged" and asked == ["11"])
        rec._gh_json = comments("https://x/o/r/pull/10")
        check("pr_merge_state: OPEN -> open", rec.pr_merge_state("BT-070") == "open")
        rec._gh_json = comments("https://x/o/r/pull/12")
        check("pr_merge_state: CLOSED unmerged -> open", rec.pr_merge_state("BT-070") == "open")
        rec._gh_json = comments("https://x/o/r/pull/13")
        check("pr_merge_state: PR lookup fails -> None", rec.pr_merge_state("BT-070") is None)
        asked.clear()
        rec._gh_json = comments("no link here", "none either")
        check("pr_merge_state: no /pull/ comment -> none, no PR lookup", rec.pr_merge_state("BT-070") == "none" and not asked)
        rec._gh_json = comments()
        check("pr_merge_state: no comments -> none", rec.pr_merge_state("BT-070") == "none")
        rec._gh_json = lambda num, fields: None
        check("pr_merge_state: gh failure -> None", rec.pr_merge_state("BT-070") is None)
        check("pr_merge_state: BT-LOCAL has no GitHub issue -> None", rec.pr_merge_state("BT-LOCAL-x") is None)
        n, cache = [], {}
        rec._gh_json = lambda num, fields: n.append(num) or {"comments": []}
        rec.pr_merge_state("BT-070", cache)
        rec.pr_merge_state("BT-070", cache)
        check("pr_merge_state: cached per run when a cache is passed", n == ["70"])
    finally:
        rec._gh_json, rec._pr_state = orig_json, orig_pr
    real_run = rec.subprocess.run
    try:
        class Done:
            def __init__(self, code, out):
                self.returncode, self.stdout = code, out
        rec.subprocess.run = lambda *a, **k: Done(0, '{"state": "MERGED"}')
        check("_pr_state parses gh pr view --json state", rec._pr_state("11") == "MERGED")
        rec.subprocess.run = lambda *a, **k: Done(1, "")
        check("_pr_state: gh error -> None", rec._pr_state("11") is None)
        rec.subprocess.run = lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError())
        check("_pr_state: no gh binary -> None", rec._pr_state("11") is None)
    finally:
        rec.subprocess.run = real_run

    # 12. argparse
    for flag, argv in (("--heal", ["--ids", "BT-007", "--heal", "--kind", "labels", "--source", "gh"]),
                       ("--summary", ["--all-open", "--summary"]), ("--pr-id", ["--ids", "BT-007", "--pr-id", "BT-007"]),
                       ("--fields", ["--ids", "BT-007", "--fields", "status"])):
        check(f"--edges refuses {flag}", _arg_error(["--edges", "blockers"] + argv))
    check("--edges needs --ids or --all-open", _arg_error(["--edges", "blockers"]))
    check("--edges takes blockers|dependents only", _arg_error(["--edges", "both", "--ids", "BT-007"]))


def gh_node(num, status="in review", state="OPEN", milestone=None, parent=None, parent_ms=None,
            blocked=(), blocking=(), comments=None, labels=("type:improvement", "tier:slice")):
    """A GraphQL issue node as `fetch_nodes` returns it (connections are {"nodes": [...]})."""
    names = ([f"status:{status}"] if status else []) + list(labels)

    def ref(n, st="OPEN", ms=None, tags=("tier:slice",)):
        return {"number": n, "state": st, "milestone": {"title": ms} if ms else None,
                "labels": {"nodes": [{"name": t} for t in tags]}}
    node = ref(num, state, milestone, names)
    node["labels"] = {"nodes": [{"name": n} for n in names]}
    node["parent"] = ref(parent, ms=parent_ms, tags=("tier:epic", "status:in progress")) if parent else None
    node["blockedBy"] = {"nodes": [ref(b) for b in blocked]}
    node["blocking"] = {"nodes": [dict(ref(n, tags=("tier:slice", "status:planned")),
                                       parent=ref(p, tags=("tier:epic",)) if p else None) for n, p in blocking]}
    node["comments"] = {"nodes": [{"body": c} for c in (comments or [])]}
    return node


def _arch(td, tracker, name="ARCHITECTURE.md"):
    p = Path(td) / name
    p.write_text("---\ntype: architecture\n" + (f"tracker: {tracker}\n" if tracker else "") + "version: \"1.0.0\"\n---\n# A\n",
                 encoding="utf-8")
    return str(p)


def backend_checks():
    """BT-195: the 4-step backend resolution; a transient gh failure never resolves to local."""
    orig = (rec.gh_available, rec._github_remote, rec.RETRY_DELAYS, rec._sleep)
    try:
        rec.RETRY_DELAYS, rec._sleep = (0, 0, 0), lambda s: None
        with tempfile.TemporaryDirectory() as td:
            m = write_backlog(td)
            gone = str(Path(td) / "NO_MAP.md")
            missing_arch = str(Path(td) / "NO_ARCH.md")
            rec.gh_available, rec._github_remote = lambda: True, lambda: True
            check("backend: key github wins even with a map", rec.resolve_backend(_arch(td, "github"), m) == "github")
            check("backend: key local wins", rec.resolve_backend(_arch(td, "local"), gone) == "local")
            check("backend: no key + map -> local", rec.resolve_backend(_arch(td, None), m) == "local")
            check("backend: no ARCHITECTURE file + map -> local", rec.resolve_backend(missing_arch, m) == "local")
            check("backend: no key, no map, gh ready + remote -> github", rec.resolve_backend(_arch(td, None), gone) == "github")
            rec._github_remote = lambda: False
            check("backend: no key, no map, no GitHub remote -> halt (None)", rec.resolve_backend(_arch(td, None), gone) is None)
            rec._github_remote = lambda: True
            calls = []
            rec.gh_available = lambda: calls.append(1) or False
            check("backend: no key, no map, gh not ready -> halt, never local",
                  rec.resolve_backend(_arch(td, None), gone) is None)
            check("backend: gh readiness retried 3 times after the first try", len(calls) == 4)
            flaky = iter([False, False, True])
            rec.gh_available = lambda: next(flaky)
            check("backend: a transient gh failure then success -> github",
                  rec.resolve_backend(_arch(td, None), gone) == "github")
            check("backend: a bad key value is a halt, not a guess",
                  rec.resolve_backend(_arch(td, "gitlab"), m) is None)
    finally:
        rec.gh_available, rec._github_remote, rec.RETRY_DELAYS, rec._sleep = orig


def expect_checks():
    exp = rec.parse_expect("BT-7:status=in review;BT-7:blocked_by=BT-6, BT-008;BT-9:milestone=—\n# note\nBT-9:labels=a,b")
    check("expect: ids are padded, scalar fields kept", exp["BT-007"]["status"] == "in review"
          and exp["BT-009"]["milestone"] == "—")
    check("expect: set fields are padded id / label sets", exp["BT-007"]["blocked_by"] == {"BT-006", "BT-008"}
          and exp["BT-009"]["labels"] == {"a", "b"})
    check("expect: none tokens make an empty set", rec.parse_expect("BT-7:blocked_by=—")["BT-007"]["blocked_by"] == set())
    for bad in ("BT-7", "BT-7:status", "BT-7:colour=red", "X-7:status=done"):
        try:
            rec.parse_expect(bad)
            check(f"expect: {bad!r} rejected", False)
        except ValueError:
            check(f"expect: {bad!r} rejected", True)
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "expect.txt"
        f.write_text("BT-7:status=done\nBT-8:status=planned\n", encoding="utf-8")
        check("expect: --expect-file reads one item per line",
              rec.parse_expect(f.read_text(encoding="utf-8")) == {"BT-007": {"status": "done"}, "BT-008": {"status": "planned"}})


def github_checks():
    """BT-195: GitHub mode (`tracker: github`, no map): one batched fetch, --expect as the intended state."""
    backend_checks()
    expect_checks()
    orig = (rec.gh_available, rec.fetch_nodes, rec._gh_run, rec.RETRY_DELAYS, rec._sleep, rec.pr_merge_state,
            rec.fetch_issue, rec._github_remote)
    try:
        rec.RETRY_DELAYS, rec._sleep = (0, 0, 0), lambda s: None
        rec.gh_available = lambda: True
        with tempfile.TemporaryDirectory() as td:
            arch, nomap = _arch(td, "github"), str(Path(td) / "BACKLOG_MAP.md")
            base = ["--arch", arch, "--backlog", nomap]
            calls = []

            def serve(table):
                def fetch(nums, comments=False, edges=False):
                    calls.append((list(nums), comments, edges))
                    return {n: table.get(n) for n in nums}
                rec.fetch_nodes = fetch

            serve({7: gh_node(7, comments=["Shipped in https://github.com/o/r/pull/42"], parent=5, blocked=(6,))})
            code, out = _run(base + ["--ids", "BT-007", "--pr-id", "BT-007",
                                     "--expect", "BT-7:status=in review;BT-7:blocked_by=BT-6;BT-7:parent=BT-5"])
            check("github: matching expectation -> OK, exit 0", code == 0 and "[MIRROR-OK BT-007]" in out)
            check("github: one batched fetch, comments only when a PR link is checked", calls == [([7], True, False)])
            check("github: nothing written next to the absent map", not Path(nomap).exists()
                  and sorted(p.name for p in Path(td).iterdir()) == ["ARCHITECTURE.md"])

            serve({7: gh_node(7, status=None)})
            code, out = _run(base + ["--ids", "BT-007", "--expect", "BT-7:status=in review"])
            check("github: missing status label -> drift", code == 1 and "[MIRROR-DRIFT BT-007: status expect=in review gh=None]" in out)

            serve({7: gh_node(7, comments=["unrelated"])})
            code, out = _run(base + ["--ids", "BT-007", "--pr-id", "BT-007", "--expect", "BT-7:status=in review"])
            check("github: missing PR-link comment -> drift", code == 1 and "pr-link absent" in out)

            serve({7: gh_node(7, status="done", state="OPEN")})
            code, out = _run(base + ["--ids", "BT-007", "--expect", "BT-7:status=done"])
            check("github: open-but-done -> drift", code == 1 and "[MIRROR-DRIFT BT-007: open on GitHub, expect=done]" in out)
            serve({7: gh_node(7, status="in review", state="CLOSED")})
            code, out = _run(base + ["--ids", "BT-007", "--expect", "BT-7:status=in review"])
            check("github: closed-but-not-done -> drift", code == 1 and "closed on GitHub, expect=in review" in out)

            serve({7: None})
            code, out = _run(base + ["--ids", "BT-007", "--expect", "BT-7:status=done"])
            check("github: issue absent -> not found", code == 1 and "[MIRROR-DRIFT BT-007: gh issue #7 not found]" in out)

            serve({n: gh_node(n) for n in (1, 2, 3, 4)})
            calls.clear()
            code, out = _run(base + ["--ids", "BT-001,BT-002,BT-003,BT-004", "--expect", "BT-1:status=in review;BT-4:status=in review"])
            check("github: 4 ids -> one fetch, ids without an expectation are only checked to exist",
                  code == 0 and len(calls) == 1 and "[MIRROR-OK BT-001,BT-002,BT-003,BT-004]" in out)

            check("github: --fields narrows the expected fields",
                  _run(base + ["--ids", "BT-001", "--fields", "milestone", "--expect", "BT-1:status=done"])[0] == 0)
            check("github: --expect-file works like --expect", _run(base + ["--ids", "BT-001", "--expect-file",
                  str(_expect_file(td, "BT-1:status=in review\n"))])[0] == 0)
            with tempfile.TemporaryDirectory() as td2:
                check("local: --with-edges / --expect need tracker github", _arg_error(
                    ["--arch", _arch(td2, "local"), "--backlog", write_backlog(td2), "--ids", "BT-007", "--with-edges", "dependents"]))
            check("github: --edges stays a separate run", _arg_error(base + ["--ids", "BT-007", "--edges", "dependents", "--pr-id", "BT-007"]))
            check("github: map-only runs are refused", all(_arg_error(base + a) for a in (
                ["--all-open"], ["--ids", "BT-001", "--heal", "--kind", "status", "--source", "gh"])))
            check("github: a malformed --expect is an argument error", _arg_error(base + ["--ids", "BT-001", "--expect", "BT-1"]))

            # combined mode: gate + dependents from ONE fetch
            serve({7: gh_node(7, parent=5, blocking=((8, 5), (10, None)))})
            rec.gh_available = lambda: True
            rec.pr_merge_state = lambda bt, cache=None: "open"
            calls.clear()
            code, out = _run(base + ["--ids", "BT-007", "--pr-id", "BT-007", "--with-edges", "dependents",
                                     "--expect", "BT-7:status=in review"])
            drift = "pr-link absent" in out
            check("combined: gate result and [CLEAR]/[KEEP] in one invocation",
                  "[CLEAR BT-008 <- BT-007] same-unit" in out and "[KEEP BT-010 <- BT-007] cross-unit" in out and drift)
            check("combined: one fetch with comments and edges", calls == [([7], True, True)])
            check("combined: exit follows the gate", code == 1)
            code, out = _run(base + ["--ids", "BT-007", "--with-edges", "dependents", "--expect", "BT-7:status=in review"])
            check("combined: clean gate + edges -> exit 0 and both outputs", code == 0 and "[MIRROR-OK BT-007]" in out and "[CLEAR BT-008" in out)

            serve({10: gh_node(10, blocked=(7,), parent=None)})
            code, out = _run(base + ["--ids", "BT-010", "--edges", "blockers"])
            check("github: --edges blockers reads the blockers from GitHub", "[BLOCKER-UNMET BT-010 <- BT-007]" in out and code == 1)

            # failure handling: retried, then a clear halt; never a local fallback
            rec.fetch_nodes = orig[1]
            attempts = []
            rec._gh_run = lambda args: attempts.append(args) or (1, "", "HTTP 502: bad gateway")
            code, out = _run(base + ["--ids", "BT-007", "--expect", "BT-7:status=done"])
            check("github: gh failure retried 3 times after the first try, then exit 3",
                  len(attempts) == 4 and code == 3 and "[GH-UNAVAILABLE" in out and "HTTP 502" in out)
            check("github: a failed run still writes nothing", sorted(p.name for p in Path(td).iterdir()) == ["ARCHITECTURE.md", "expect.txt"])

            import json
            attempts.clear()
            rec._gh_run = lambda args: attempts.append(args) or (1, json.dumps({"data": {"repository": {"i_7": None}}, "errors": [
                {"type": "NOT_FOUND", "path": ["repository", "i_7"]}]}), "")
            check("github: a NOT_FOUND-only partial response is data, not a failure",
                  rec.fetch_nodes([7]) == {7: None} and len(attempts) == 1)
            rec._gh_run = lambda args: (0, json.dumps({"errors": [{"type": "RATE_LIMITED"}]}), "")
            try:
                rec.fetch_nodes([7])
                check("github: a non-NOT_FOUND GraphQL error is a failure", False)
            except rec.GhError:
                check("github: a non-NOT_FOUND GraphQL error is a failure", True)

            # pagination: ids are fetched 50 per call, every row comes back
            queries = []

            def fake(args):
                q = next(a for a in args if a.startswith("query="))
                queries.append(q)
                nums = [int(n) for n in __import__("re").findall(r"i_(\d+): issue", q)]
                return 0, json.dumps({"data": {"repository": {f"i_{n}": gh_node(n) for n in nums}}}), ""
            rec._gh_run = fake
            got = rec.fetch_nodes(list(range(1, 102)))
            check("github: 101 ids -> 3 calls, all rows returned", len(queries) == 3 and sorted(got) == list(range(1, 102))
                  and all(got[n]["number"] == n for n in got))
            rec._gh_run = lambda args: (127, "", "gh: command not found")
            try:
                rec.fetch_nodes([1])
                check("github: gh missing is a GhError", False)
            except rec.GhError:
                check("github: gh missing is a GhError", True)

            # the local path is untouched by an explicit `tracker: local`
            seen = []
            rec.fetch_nodes = lambda *a, **k: seen.append(1)
            lp = write_backlog(td)
            rec.fetch_issue = lambda num, want_comments, want_state=False: gh_issue()
            code, out = _run(["--arch", _arch(td, "local"), "--backlog", lp, "--ids", "BT-007"])
            check("local: tracker local uses the map and never the batched fetch", code == 0 and not seen and "[MIRROR-OK BT-007]" in out)
            code, out = _run(["--arch", _arch(td, None), "--backlog", lp, "--ids", "BT-007"])
            check("local: no key + a map resolves to local", code == 0 and not seen)
            rec._github_remote = lambda: False
            code, out = _run(["--arch", _arch(td, None), "--backlog", str(Path(td) / "NO_MAP.md"), "--ids", "BT-007"])
            check("unresolved backend: halt with a clear message, exit 3", code == 3 and "[TRACKER-UNRESOLVED" in out)
            code, out = _run(["--arch", _arch(td, "gitlab"), "--backlog", lp, "--ids", "BT-007"])
            check("unknown tracker value: halt names the value, not a missing key",
                  code == 3 and "[TRACKER-UNRESOLVED" in out and "`tracker: gitlab`" in out and "no `tracker:` key" not in out)
    finally:
        (rec.gh_available, rec.fetch_nodes, rec._gh_run, rec.RETRY_DELAYS, rec._sleep, rec.pr_merge_state,
         rec.fetch_issue, rec._github_remote) = orig


def _expect_file(td, text):
    p = Path(td) / "expect.txt"
    p.write_text(text, encoding="utf-8")
    return p


def main():
    with tempfile.TemporaryDirectory() as td:
        path = write_backlog(td)
        rows = rec.parse_backlog(path)

    # parse_backlog
    check("parse skips header/separator/placeholder", set(rows) == {"BT-007", "BT-009"})
    check("parse status", rows["BT-007"]["status"] == "in review")
    check("parse labels set", rows["BT-007"]["labels"] ==
          {"area:api", "type:feature", "tier:slice", "size:small"})
    check("parse parent", rows["BT-007"]["parent"] == "BT-005")
    check("parse blocked_by", rows["BT-007"]["blocked_by"] == {"BT-006"})
    check("parse none-tokens empty", rows["BT-009"]["blocked_by"] == set()
          and rows["BT-009"]["parent"] == "—")

    r7 = rows["BT-007"]

    # compare — full-field
    check("all-agree -> no drift", rec.compare(r7, gh_issue(), ALL, False) == [])
    check("status drift", any("status" in x for x in rec.compare(r7, gh_issue(status="in progress"), ALL, False)))
    check("milestone drift", any("milestone" in x for x in rec.compare(r7, gh_issue(milestone="v1.3.0"), ALL, False)))
    check("blocked_by drift", any("blocked_by" in x for x in rec.compare(r7, gh_issue(blocked=("6", "8")), ALL, False)))

    # blockedBy shapes: real gh is {"nodes": [...], "totalCount": n}; flat list and None tolerated
    check("blockedBy nodes shape agrees", rec.compare(r7, gh_issue(blocked_shape="nodes"), ALL, False) == [])
    check("blockedBy flat list agrees", rec.compare(r7, gh_issue(blocked_shape="list"), ALL, False) == [])
    r9 = rows["BT-009"]
    check("blockedBy empty nodes agrees with no blockers",
          rec.compare(r9, gh_issue(blocked=(), parent_num=None, extra_labels=["type:feature", "tier:epic"],
                                   milestone=None, status="planned"), ALL, False) == [])
    check("blockedBy None treated as no blockers",
          rec.compare(r9, gh_issue(blocked_shape="none", parent_num=None, status="planned", milestone=None,
                                   extra_labels=["type:feature", "tier:epic"]), ALL, False) == [])
    nodes_drift = rec.compare(r7, gh_issue(blocked=("6", "8")), ALL, False)
    check("blockedBy nodes drift reports both ids", any("BT-008" in x for x in nodes_drift))
    check("parent drift", any("parent" in x for x in rec.compare(r7, gh_issue(parent_num="99"), ALL, False)))

    # labels: swapped and SUPERSET (GitHub carries a label the map doesn't mirror)
    check("label swap drift", any("labels" in x for x in
          rec.compare(r7, gh_issue(extra_labels=["area:api", "type:bug"]), ALL, False)))
    superset = rec.compare(r7, gh_issue(extra_labels=["area:api", "type:feature", "tier:slice",
                                                       "size:small", "priority:high"]), ALL, False)
    check("label SUPERSET (gh-only label) drift", any("gh_only=['priority:high']" in x for x in superset))

    # status:* in the map Labels cell is not label drift (status is compared separately)
    with_status = dict(r7, labels=r7["labels"] | {"status:in review"})
    check("map status: label is not label drift",
          rec.compare(with_status, gh_issue(), {"labels"}, False) == [])
    check("map status: label + matching gh -> no drift on all fields",
          rec.compare(with_status, gh_issue(), ALL, False) == [])
    check("real label drift still reported with a map status: label",
          any("labels" in x for x in rec.compare(with_status, gh_issue(extra_labels=["area:api"]), {"labels"}, False)))

    # --fields scoping: milestone-only ignores a status divergence
    d = rec.compare(r7, gh_issue(status="in progress"), {"milestone"}, False)
    check("fields scoping: status ignored when not requested", d == [])

    # absent optional fields -> not checked
    check("absent optional fields skipped",
          rec.compare(r7, gh_issue(with_blockedby=False, with_parent=False), ALL, False) == [])

    # check_pr scoping
    check("check_pr=False -> no pr drift even without comments",
          rec.compare(r7, gh_issue(comments=[]), ALL, False) == [])
    check("check_pr=True + missing PR link -> drift",
          any("pr-link" in x for x in rec.compare(r7, gh_issue(comments=[]), ALL, True)))
    check("check_pr=True + PR link present -> ok",
          rec.compare(r7, gh_issue(comments=[{"body": "https://github.com/o/r/pull/42"}]), ALL, True) == [])

    check("issue_number strips padding", rec.issue_number("BT-007") == "7")
    check("issue_number local -> None", rec.issue_number("BT-LOCAL-x") is None)

    # main() exit-code paths (gh monkeypatched)
    orig_avail, orig_fetch = rec.gh_available, rec.fetch_issue
    try:
        with tempfile.TemporaryDirectory() as td:
            path = write_backlog(td)
            rec.gh_available = lambda: False
            check("main offline + id present -> exit 0",
                  rec.main(["--ids", "BT-007", "--backlog", path]) == 0)
            check("main offline + id absent -> exit 1",
                  rec.main(["--ids", "BT-404", "--backlog", path]) == 1)

            rec.gh_available = lambda: True
            rec.fetch_issue = lambda num, want_comments, want_state=False: gh_issue()
            check("main online + agree -> exit 0",
                  rec.main(["--ids", "BT-007", "--backlog", path]) == 0)
            rec.fetch_issue = lambda num, want_comments, want_state=False: gh_issue(status="in progress")
            check("main online + drift -> exit 1",
                  rec.main(["--ids", "BT-007", "--backlog", path]) == 1)
    finally:
        rec.gh_available, rec.fetch_issue = orig_avail, orig_fetch

    ids_state_checks()
    all_open_checks()
    summary_checks()
    heal_checks()
    edge_checks()
    github_checks()

    if FAILS:
        print(f"\n{len(FAILS)} FAILED")
        return False
    print("\nAll reconcile tests PASSED.")
    return True


def test_reconcile():
    # Collected by pytest (this file used to be a __main__-only runner nothing ran).
    assert main(), f"reconcile checks failed: {FAILS}"


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
