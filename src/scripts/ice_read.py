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
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reconcile

EFFORT = {'small': 1, 'medium': 2, 'large': 3}
CANDIDATE_STATUS = ('planned', 'needs_spec')
REQUIRED = ('type:', 'mode:', 'tier:slice', 'size:')
LIST_FIELDS = 'number,title,labels,milestone,body'
LIST_LIMIT = 500  # gh issue list --limit; a result this long may have dropped issues


def _number(text):
    """First number of a metric value: `2.0`, `100%`, `80 %`, `0.8 (reason)`. A percent is a fraction. None if absent."""
    m = re.match(r'\s*([0-9]*\.?[0-9]+)\s*(%?)', text)
    return None if not m else float(m.group(1)) / (100 if m.group(2) else 1)


def parse_metrics(body):
    """{'impact', 'confidence'} from the body's metric lines; a missing one is None. Pure."""
    out = {}
    for key in ('impact', 'confidence'):
        m = re.search(rf'^[-*]\s*\*\*{key}:\*\*(.*)$', body or '', re.I | re.M)
        out[key] = _number(m.group(1)) if m else None
    return out


def effort_weight(labels):
    return next((EFFORT[l[5:]] for l in labels if l.startswith('size:') and l[5:] in EFFORT), None)


def ice_from_body(body, labels):
    """The ICE score (2 decimals), or None when the body or labels do not give one. Pure."""
    m = parse_metrics(body)
    weight = effort_weight(labels)
    if None in (m['impact'], m['confidence'], weight):
        return None
    return round(m['impact'] * m['confidence'] / weight, 2)


def _status(labels):
    return next((l[7:] for l in labels if l.startswith('status:')), '')


def candidates(issues):
    """(candidate lines, [MISSING-LABELS] lines) from `gh issue list --json number,title,labels,milestone,body`. Pure."""
    lines, missing = [], []
    for issue in issues:
        labels = [l['name'] for l in issue['labels']]
        if (_status(labels) not in CANDIDATE_STATUS or 'tier:epic' in labels or 'scope:deferred' in labels
                or any(l.startswith('concept:') for l in labels)):
            continue
        bt = issue.get('id') or reconcile._bt(issue['number'])
        absent = [r for r in REQUIRED if not any(l.startswith(r) for l in labels)]
        if absent:
            missing.append(f"[MISSING-LABELS] {bt} - {issue['title']} ({', '.join(absent)})")
            continue
        ice = ice_from_body(issue.get('body') or '', labels) if _status(labels) == 'planned' else None
        shown = ' '.join(sorted(l for l in labels if not l.startswith(('status:', 'tier:'))))
        milestone = (issue.get('milestone') or {}).get('title') or '—'
        score = '—' if ice is None else f"{ice:g}"
        lines.append(f"{bt} | {_status(labels)} | {issue['title']} | {shown} | {milestone} | ICE {score}")
    return lines, missing


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
        import issues as local
        try:
            lines, missing = candidates(local.open_as_gh(local.Tracker(args.arch).store()))
        except local.IssuesError as e:
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
