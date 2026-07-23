#!/usr/bin/env python3
"""Unit tests for src/scripts/reconcile.py — the Terminal Sync Invariant gate.

Pure logic (parse_backlog, compare) with fixtures + mocked gh JSON, plus main()
exit-code paths with gh monkeypatched — fully offline and deterministic.
"""
import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
             parent_num="5", comments=None, with_blockedby=True, with_parent=True):
    labels = [{"name": f"status:{status}"}] if status else []
    labels += [{"name": n} for n in (extra_labels if extra_labels is not None
                                      else ["area:api", "type:feature", "tier:slice", "size:small"])]
    d = {"number": 7, "labels": labels,
         "milestone": {"title": milestone} if milestone else None}
    if with_blockedby:
        d["blockedBy"] = [{"number": int(n)} for n in blocked]
    if with_parent:
        d["parent"] = {"number": int(parent_num)} if parent_num else None
    if comments is not None:
        d["comments"] = comments
    return d


def write_backlog(td):
    p = Path(td) / "BACKLOG_MAP.md"
    p.write_text(BACKLOG, encoding="utf-8")
    return str(p)


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
    check("parent drift", any("parent" in x for x in rec.compare(r7, gh_issue(parent_num="99"), ALL, False)))

    # labels: swapped and SUPERSET (GitHub carries a label the map doesn't mirror)
    check("label swap drift", any("labels" in x for x in
          rec.compare(r7, gh_issue(extra_labels=["area:api", "type:bug"]), ALL, False)))
    superset = rec.compare(r7, gh_issue(extra_labels=["area:api", "type:feature", "tier:slice",
                                                       "size:small", "priority:high"]), ALL, False)
    check("label SUPERSET (gh-only label) drift", any("gh_only=['priority:high']" in x for x in superset))

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

    if FAILS:
        print(f"\n{len(FAILS)} FAILED")
        sys.exit(1)
    print("\nAll reconcile tests PASSED.")


if __name__ == "__main__":
    main()
