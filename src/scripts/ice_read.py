#!/usr/bin/env python3
"""ice_read.py — ICE on read, and 3c's candidate list, on both tracker backends (no stored score).

ICE = Impact * Confidence / Effort. Impact and Confidence are the body's `- **Impact:**` / `- **Confidence:**`
lines (3b writes them); Effort comes from the `size:` label (small 1, medium 2, large 3). A Spike, a body without
metrics or an issue without a size label has no score (`—`): 3c's "recalculate if empty" path.

  ice_read.py candidates   open leaf issues at `status:planned|needs_spec`, no `concept:*`, no `scope:deferred`,
                           one line each; a leaf lacking a required label is listed as `[MISSING-LABELS]` instead.
                           `tracker: github`: one scoped `gh issue list`; `tracker: local`: the issues.py store.
Exit: 0 ok, 1 local store unreadable, 3 GitHub unreachable after the retries (never a local fallback).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reconcile
from _tracker_common import candidates

LIST_FIELDS = 'number,title,labels,milestone,body'
LIST_LIMIT = 500  # gh issue list --limit; a result this long may have dropped issues


def fetch_open_issues():
    """Every open issue (one call, retried). Raises reconcile.GhError once the retries are spent."""
    why = ''
    for i in range(len(reconcile.RETRY_DELAYS) + 1):
        if i:
            reconcile._sleep(reconcile.RETRY_DELAYS[i - 1])
        rc, out, err = reconcile._gh_run(['issue', 'list', '--state', 'open', '--limit', str(LIST_LIMIT), '--json', LIST_FIELDS])
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            why = (err.strip() or f"exit {rc}").splitlines()[0]
    raise reconcile.GhError(f"gh issue list failed after {len(reconcile.RETRY_DELAYS) + 1} attempts: {why}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="ICE on read and 3c candidates (both tracker backends).")
    ap.add_argument('command', choices=('candidates',))
    ap.add_argument('--arch', default=reconcile.ARCH_DEFAULT)
    args = ap.parse_args(argv)
    if reconcile.resolve_backend(args.arch) == 'local':
        import issues  # lazy: the GitHub path needs only reconcile.py and _tracker_common.py beside this file
        try:
            lines, missing = candidates(issues.open_as_gh(issues.Tracker(args.arch).store()))
        except issues.IssuesError as e:
            print(e)
            return 1
        print("\n".join(lines + missing))
        return 0
    try:
        issues = fetch_open_issues()
    except reconcile.GhError as e:
        print(f"[GH-UNAVAILABLE: {e}; GitHub mode never falls back to a local copy]")
        return 3
    lines, missing = candidates(issues)
    if len(issues) >= LIST_LIMIT:
        missing.append(f"[TRUNCATED: {len(issues)} open issues is the read cap; candidates may be missing]")
    print("\n".join(lines + missing))
    return 0


if __name__ == '__main__':
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
