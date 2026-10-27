#!/usr/bin/env python3
"""nightly_state.py — sole writer of docs/nightly/.last-run.json (0d nightly cross-night memory).

  nightly_state.py slugs                                names of known findings (names only, no prose)
  nightly_state.py findings --slugs a,b                 record tonight's findings; prints `<slug> nights=N`
  nightly_state.py stamp [--now ISO]                    set last_run (the delta start for the next run)

Schema: {"last_run": ISO, "findings": {slug: {first,last,nights}}}
`nights` counts distinct nights, so re-running the same night never double-counts (keyed on --date,
default today). A missing file, the old `{"last_run"}`-only file, or a missing key reads as empty history.
Findings are pruned 90 days after `last`.
Flags `--state PATH` and `--date YYYY-MM-DD` work before or after the command.
Every write is UTF-8 without BOM. Stdlib only; runs from the repo root.
"""
import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

STATE = Path("docs") / "nightly" / ".last-run.json"
RETAIN_DAYS = 90
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _entries(raw):
    """Keep only well-formed {first,last,nights} entries; anything else is dropped as empty history."""
    out = {}
    for k, v in (raw if isinstance(raw, dict) else {}).items():
        if isinstance(v, dict) and isinstance(v.get("first"), str) and isinstance(v.get("nights"), int):
            out[k] = {"first": v["first"], "last": v.get("last") or v["first"], "nights": v["nights"]}
    return out


def load(path):
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raw = {}
    raw = raw if isinstance(raw, dict) else {}
    return {"last_run": raw.get("last_run") if isinstance(raw.get("last_run"), str) else None,
            "findings": _entries(raw.get("findings"))}


def save(path, state):
    out = {k: v for k, v in state.items() if k != "last_run" or v}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")  # write aside, then swap: a crash never leaves a half-written state
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:  # no BOM, LF
        f.write(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def bump(entries, key, date):
    """Count `date` once per entry: new -> nights 1; a later date -> +1; the same night again -> unchanged."""
    e = entries.get(key)
    if e is None:
        entries[key] = {"first": date, "last": date, "nights": 1}
    elif e["last"] < date:
        e["last"] = date
        e["nights"] += 1
    return entries[key]


def prune_findings(findings, date):
    cutoff = (datetime.date.fromisoformat(date) - datetime.timedelta(days=RETAIN_DAYS)).isoformat()
    return {k: v for k, v in findings.items() if v["last"] >= cutoff}


def valid_date(s):
    try:
        datetime.date.fromisoformat(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {s}")
    return s


def main(argv=None):
    ap = argparse.ArgumentParser(description="Owner of docs/nightly/.last-run.json.")
    ap.add_argument("--state", default=str(STATE))
    ap.add_argument("--date", type=valid_date, default=None, help="the night, YYYY-MM-DD (default: today)")
    common = argparse.ArgumentParser(add_help=False)  # same flags after the command; SUPPRESS keeps the earlier value
    common.add_argument("--state", default=argparse.SUPPRESS)
    common.add_argument("--date", type=valid_date, default=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("slugs", parents=[common])
    f = sub.add_parser("findings", parents=[common])
    f.add_argument("--slugs", required=True, help="comma-separated kebab-case slugs")
    s = sub.add_parser("stamp", parents=[common])
    s.add_argument("--now", help="ISO 8601 (default: now, local offset)")
    args = ap.parse_args(argv)

    date = args.date or datetime.date.today().isoformat()
    state = load(args.state)

    if args.cmd == "slugs":
        for slug in sorted(state["findings"]):
            print(slug)
        return 0

    if args.cmd == "findings":
        slugs = [x.strip() for x in args.slugs.split(",") if x.strip()]
        bad = [x for x in slugs if not SLUG_RE.match(x)]
        if bad:
            ap.error(f"slugs must be lowercase kebab-case: {bad}")
        state["findings"] = prune_findings(state["findings"], date)
        for slug in slugs:
            print(f"{slug} nights={bump(state['findings'], slug, date)['nights']}")
    else:  # stamp
        state["findings"] = prune_findings(state["findings"], date)
        state["last_run"] = args.now or datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        print(f"last_run={state['last_run']}")

    save(args.state, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
