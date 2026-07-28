#!/usr/bin/env python3
"""reconcile.py — Terminal Sync Invariant gate (detection only; never writes).

Assert that GitHub issue state matches the `.memory/BACKLOG_MAP.md` mirror for the
given BT ids, at the end of a workflow's Publish/Commit & Sync phase. Exit non-zero
on drift so the calling workflow HALTS before closing/shipping; heal + re-run.

Each caller passes `--fields` = only the mirror fields it wrote, so a gate never
false-blocks on drift in a field outside its concern. `--pr-id` scopes the PR-link
check to the single issue that received the PR comment (e.g. the shipped slice),
so co-passed ids (cleared dependents, a flipped epic) are not required to carry it.

Offline / no `gh` -> internal-consistency check only, exit 0 (`[local-only]`).
Contract + heal protocol: .agents/workflows/.reference/terminal-sync-invariant.md

Usage:
  python .agents/scripts/reconcile.py --ids BT-007[,BT-006,BT-005] \
      [--pr-id BT-007] [--fields status,blocked_by]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

STATUS_RE = re.compile(r'^status:(.+)$')
NONE_TOKENS = {'', '-', '—'}
ALL_FIELDS = ('status', 'milestone', 'labels', 'parent', 'blocked_by')


def parse_backlog(path):
    """Parse 9-col BACKLOG_MAP rows into {BT-id: {fields}}. Pure (reads one file)."""
    rows = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line.lstrip().startswith('|'):
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 11:  # leading + trailing empty cells around 9 columns
            continue
        bt = parts[1]
        if not re.match(r'^BT-(LOCAL-)?\S+$', bt) or bt == 'BT-XXX':
            continue  # header, separator, or placeholder row
        rows[bt] = {
            'status': parts[3],
            'labels': {l.strip() for l in parts[4].split(',') if l.strip() not in NONE_TOKENS},
            'milestone': parts[5],
            'parent': parts[6],
            'blocked_by': {b.strip() for b in parts[7].split(',') if b.strip() not in NONE_TOKENS},
        }
    return rows


def issue_number(bt):
    m = re.match(r'^BT-0*(\d+)$', bt)
    return m.group(1) if m else None


def _norm(token):
    return None if token in NONE_TOKENS else token


def compare(row, gh, fields, check_pr):
    """Return a list of drift descriptions for one issue. Pure — unit-tested.

    Only fields in `fields` are checked. Fields absent from `gh` (not exposed by the
    installed gh version/extension) are skipped, never reported as drift. PR-link is
    checked only when `check_pr` is True (the caller's --pr-id issue).
    """
    drift = []
    gh_labels = {l['name'] for l in gh.get('labels', [])}

    if 'status' in fields:
        gh_status = next((STATUS_RE.match(l).group(1) for l in gh_labels if STATUS_RE.match(l)), None)
        if gh_status != _norm(row['status']):
            drift.append(f"status map={row['status']} gh={gh_status}")

    if 'milestone' in fields:
        gh_ms = (gh.get('milestone') or {}).get('title')
        if gh_ms != _norm(row['milestone']):
            drift.append(f"milestone map={_norm(row['milestone'])} gh={gh_ms}")

    if 'labels' in fields:
        gh_nonstatus = {l for l in gh_labels if not STATUS_RE.match(l)}
        if row['labels'] != gh_nonstatus:
            drift.append(f"labels map_only={sorted(row['labels'] - gh_nonstatus)} "
                         f"gh_only={sorted(gh_nonstatus - row['labels'])}")

    if 'blocked_by' in fields and 'blockedBy' in gh:
        gh_bb = {f"BT-{int(i['number']):03d}" for i in (gh.get('blockedBy') or [])}
        if row['blocked_by'] != gh_bb:
            drift.append(f"blocked_by map={sorted(row['blocked_by'])} gh={sorted(gh_bb)}")

    if 'parent' in fields and 'parent' in gh:
        p = gh.get('parent')
        gh_parent = f"BT-{int(p['number']):03d}" if p else None
        if gh_parent != _norm(row['parent']):
            drift.append(f"parent map={_norm(row['parent'])} gh={gh_parent}")

    if check_pr:
        if not any('/pull/' in (c.get('body') or '') for c in (gh.get('comments') or [])):
            drift.append("pr-link absent from issue comments")

    return drift


def _gh_json(num, fields):
    try:
        r = subprocess.run(['gh', 'issue', 'view', num, '--json', ','.join(fields)],
                           capture_output=True, text=True)
    except FileNotFoundError:
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def fetch_issue(num, want_comments):
    """Core fields first; optional (blockedBy/parent) fetched separately so an
    unsupported field degrades to 'not checked' instead of failing the whole read."""
    core = ['number', 'labels', 'milestone']
    if want_comments:
        core.append('comments')
    data = _gh_json(num, core)
    if data is None:
        return None
    for opt in ('blockedBy', 'parent'):
        d = _gh_json(num, [opt])
        if d is not None and opt in d:
            data[opt] = d[opt]
    return data


def gh_available():
    try:
        return subprocess.run(['gh', 'auth', 'status'], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(description="Terminal Sync Invariant gate.")
    ap.add_argument('--ids', required=True, help="comma-separated BT ids, e.g. BT-007,BT-006")
    ap.add_argument('--pr-id', help="the id that must carry a PR-link comment (e.g. the shipped slice)")
    ap.add_argument('--fields', default=','.join(ALL_FIELDS),
                    help="mirror fields to check (default: all). Pass only the fields this phase wrote.")
    ap.add_argument('--backlog', default='.memory/BACKLOG_MAP.md')
    args = ap.parse_args(argv)

    ids = [i.strip() for i in args.ids.split(',') if i.strip()]
    fields = {f.strip() for f in args.fields.split(',') if f.strip()}
    rows = parse_backlog(args.backlog)

    if not gh_available():
        print("[local-only — GitHub not checked]")
        missing = [i for i in ids if i not in rows]
        if missing:
            print(f"[MIRROR-DRIFT: ids absent from BACKLOG_MAP: {missing}]")
            return 1
        return 0

    exit_code = 0
    for bt in ids:
        if bt not in rows:
            print(f"[MIRROR-DRIFT {bt}: absent from BACKLOG_MAP]")
            exit_code = 1
            continue
        if bt.startswith('BT-LOCAL'):
            print(f"[local-only {bt} — no GitHub issue to check]")
            continue
        num = issue_number(bt)
        is_pr = (bt == args.pr_id)
        gh = fetch_issue(num, want_comments=is_pr) if num else None
        if gh is None:
            print(f"[MIRROR-DRIFT {bt}: gh issue #{num} not found]")
            exit_code = 1
            continue
        drift = compare(rows[bt], gh, fields, check_pr=is_pr)
        for d in drift:
            print(f"[MIRROR-DRIFT {bt}: {d}]")
        if drift:
            exit_code = 1

    if exit_code == 0:
        print(f"[MIRROR-OK {','.join(ids)}]")
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
