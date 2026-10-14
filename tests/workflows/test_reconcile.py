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
| BT-001 | Shipped | done | type:feature | v1.0.0 | — | — | ICE | — |
| BT-002 | In review | in review | type:feature | v1.0.0 | — | — | ICE | — |
| BT-003 | Waits on 2 | planned | type:feature | v1.0.0 | — | BT-002 | ICE | — |
| BT-004 | Waits on 1 | planned | type:feature | v1.0.0 | — | BT-001 | ICE | — |
| BT-005 | Waits on 9 | planned | type:feature | v1.0.0 | — | BT-009 | ICE | — |
| BT-009 | In progress | in progress | type:feature | v1.0.0 | — | — | ICE | — |
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
            clean = ALLOPEN.replace("| BT-003 | Waits on 2 | planned | type:feature | v1.0.0 | — | BT-002 |",
                                    "| BT-003 | Waits on 2 | planned | type:feature | v1.0.0 | — | — |").replace(
                "| BT-004 | Waits on 1 | planned | type:feature | v1.0.0 | — | BT-001 |",
                "| BT-004 | Waits on 1 | planned | type:feature | v1.0.0 | — | — |")
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
            rec.fetch_issue = lambda num, want_comments: gh_issue()
            check("main online + agree -> exit 0",
                  rec.main(["--ids", "BT-007", "--backlog", path]) == 0)
            rec.fetch_issue = lambda num, want_comments: gh_issue(status="in progress")
            check("main online + drift -> exit 1",
                  rec.main(["--ids", "BT-007", "--backlog", path]) == 1)
    finally:
        rec.gh_available, rec.fetch_issue = orig_avail, orig_fetch

    all_open_checks()
    summary_checks()
    heal_checks()

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
