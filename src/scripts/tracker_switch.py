#!/usr/bin/env python3
"""tracker_switch.py — move a local-tracker project to GitHub (local -> GitHub only; never the reverse).

The source is the issues.py store (the `<repo>/issues` branch); a v5 `.memory/BACKLOG_MAP.md` must be migrated into
it first (`issues.py migrate`). Default is a dry run: prints the plan and writes nothing, locally or on GitHub.
`--apply` creates GitHub issues, rewrites IDs under .memory/ and docs/, and sets `tracker: github` in ARCHITECTURE.md.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _tracker_common import (
    LOCAL_ID, REWRITE_ROOTS, SKIP_DIRS, apply_rewrites, padded, pending_rewrites,
    read_tracker, real_number, report_other_hits, rewrite_ids, text_files,
    write_key, write_tracker
)
import issues as store_lib
import reconcile

ARCH = '.memory/ARCHITECTURE.md'
MARKER = re.compile(r'<!-- tracker-switch: (\S+) -->')
CARRIED = re.compile(r'^(Refs:|[-*]\s*\*\*(Impact|Confidence):\*\*).*$', re.M)


class GhFail(RuntimeError):
    pass


def gh(*args):
    rc, out, err = reconcile._gh_run(list(args))
    if rc:
        raise GhFail(f"gh {' '.join(args[:2])}: {(err or out).strip()[:200] or f'exit {rc}'}")
    return out


def read_rows(arch=ARCH):
    """The store's issues as `issues.full` rows."""
    s = store_lib.Tracker(arch).store()
    return [store_lib.full(i) for i in sorted(s.issues.values(), key=lambda i: i['id'])]


def extra_lines(row, body=''):
    """The `Refs:` and Impact/Confidence lines of the store issue whose kind `body` lacks."""
    have = {m.group(1) for m in CARRIED.finditer(body)}
    return [m.group(0) for m in CARRIED.finditer(row['body']) if m.group(1) not in have]


def body_file(text):
    p = Path('.tmp') / 'tracker-switch-body.md'
    p.parent.mkdir(exist_ok=True)
    p.write_text(text, encoding='utf-8', newline='\n')
    return str(p)


def issue_body(row, numbers=None):
    """The GitHub body of a store issue: its text plus the switch marker."""
    text = row['body'] if numbers is None else rewrite_ids(row['body'], numbers)
    return (text.rstrip('\n') + '\n\n' if text else '') + f"<!-- tracker-switch: {row['id']} -->\n"


def ensure_milestones(titles):
    """Create each milestone GitHub lacks."""
    have = {t.strip() for t in gh('api', '--paginate', 'repos/{owner}/{repo}/milestones?state=open', '--jq', '.[].title').splitlines()}
    for title in sorted(titles - have):
        gh('api', 'repos/{owner}/{repo}/milestones', '-f', f'title={title}')


def issue_labels(row):
    return [l for l in row['labels'] if not l.startswith('status:')] + [f"status:{row['status']}"]


def ensure_labels(names):
    """Create each label GitHub lacks."""
    if not names:
        return
    have = {n.strip().lower() for n in gh('label', 'list', '--limit', '1000', '--json', 'name', '--jq', '.[].name').splitlines()}
    for name in sorted(n for n in names if n.lower() not in have):
        gh('label', 'create', name)


def create_issue(row):
    labels = issue_labels(row)
    args = ['issue', 'create', '--title', row['title']]
    for label in labels:
        args += ['--label', label]
    if row['milestone']:
        args += ['--milestone', row['milestone']]
    out = gh(*args, '--body-file', body_file(issue_body(row)))
    return int(out.strip().rsplit('/', 1)[-1])


def node_id(number):
    return json.loads(gh('issue', 'view', str(number), '--json', 'id'))['id']


def link_parent(child, parent):
    """Put `child` under `parent`; skipped when it already is."""
    current = json.loads(gh('issue', 'view', str(child), '--json', 'parent'))['parent']
    if current and current['number'] == parent:
        return
    q = 'mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,subIssueId:$c}){issue{number}}}'
    gh('api', 'graphql', '-f', f'query={q}', '-f', f'p={node_id(parent)}', '-f', f'c={node_id(child)}')


def link_blocked_by(issue, blocker):
    """Mark `issue` blocked by `blocker`; skipped when it already is."""
    current = json.loads(gh('issue', 'view', str(issue), '--json', 'blockedBy'))['blockedBy']['nodes']
    if any(n['number'] == blocker for n in current):
        return
    q = 'mutation($i:ID!,$b:ID!){addBlockedBy(input:{issueId:$i,blockingIssueId:$b}){issue{number}}}'
    gh('api', 'graphql', '-f', f'query={q}', '-f', f'i={node_id(issue)}', '-f', f'b={node_id(blocker)}')


def norm(text):
    return text.replace('\r\n', '\n').strip()


def sync_row(row, numbers, bodies):
    """Bring one row's issue up to date."""
    n = numbers[row['id']]
    is_existing = real_number(row['id']) is not None
    if is_existing and (lines := extra_lines(row, bodies.get(n, ''))):
        body = bodies.get(n, '').rstrip('\n') + '\n\n' + '\n'.join(lines) + '\n'
        gh('issue', 'edit', str(n), '--body-file', body_file(body))
    if not is_existing:
        want = issue_body(row, numbers)
        if norm(bodies.get(n, '')) != norm(want):
            gh('issue', 'edit', str(n), '--body-file', body_file(want))
        if row['claimed_by'] and not json.loads(gh('issue', 'view', str(n), '--json', 'assignees'))['assignees']:
            gh('issue', 'edit', str(n), '--add-assignee', '@me')
    if row['comments'] and not is_existing:
        marker = f"<!-- tracker-switch-comments: {row['id']} -->"
        posted = json.loads(gh('issue', 'view', str(n), '--json', 'comments'))['comments']
        if not any(marker in (c.get('body') or '') for c in posted):
            text = "Comments from the local tracker:\n\n" + rewrite_ids('\n'.join(row['comments']), numbers) + f"\n\n{marker}\n"
            gh('issue', 'comment', str(n), '--body-file', body_file(text))
    if row['close_reason'] and not is_existing:
        gh('issue', 'close', str(n), '--reason', row['close_reason'])
    related = [(row['parent'], link_parent)] if row['parent'] else []
    related += [(b, link_blocked_by) for b in row['blocked_by']]
    for other, link in related:
        target = numbers.get(other) or real_number(other)
        if target is None:
            print(f"[LINK-SKIP {row['id']}: {other} is not in the store]")
        else:
            link(n, target)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Move a local-tracker project to GitHub (dry run unless --apply).")
    ap.add_argument('--apply', action='store_true', help="write: create the issues, rewrite ids, set tracker: github")
    args = ap.parse_args(argv)
    if reconcile.read_tracker(ARCH) == 'github':
        print("[ALREADY-GITHUB: tracker is github; nothing to switch]")
        return 0
    try:
        rows = read_rows()
    except store_lib.IssuesError as e:
        print(f"{e}; nothing changed")
        return 2
    if reconcile._gh_run(['auth', 'status'])[0]:
        print("[GH-UNAVAILABLE: gh is missing or not logged in (`gh auth login`); nothing changed]")
        return 2
    try:
        issues = json.loads(gh('issue', 'list', '--state', 'all', '--limit', '1000', '--json', 'number,body'))
        marked = {m.group(1): i['number'] for i in issues for m in [MARKER.search(i['body'] or '')] if m}
        bodies = {i['number']: i['body'] or '' for i in issues}
        numbers = {r['id']: real_number(r['id']) or marked.get(r['id']) for r in rows}
        for r in rows:
            if numbers[r['id']] is None:
                ms = f" milestone={r['milestone']}" if r['milestone'] else ''
                print(f"[PLAN create {r['id']}: {r['title']!r} labels={r['labels']} status:{r['status']}{ms}]")
            elif real_number(r['id']) is None:
                print(f"[PLAN reuse {r['id']} -> {padded(numbers[r['id']])}: found by its marker]")
        if not args.apply:
            print(f"[PLAN rewrite ids in {len(list(pending_rewrites(numbers)))} file(s) under .memory/ and docs/ that already match; new ids are rewritten after creation]")
            report_other_hits(numbers)
            print(f"[SWITCH: dry run, {sum(n is None for n in numbers.values())} issue(s) to create; nothing written; re-run with --apply]")
            return 0
        if not Path(ARCH).read_bytes().decode('utf-8-sig').startswith('---'):
            print(f"[NO-ARCHITECTURE: {ARCH} needs frontmatter to hold `tracker:`; nothing changed]")
            return 2
        created = 0
        ensure_milestones({r['milestone'] for r in rows if numbers[r['id']] is None and r['milestone']})
        ensure_labels({l for r in rows if numbers[r['id']] is None for l in issue_labels(r)})
        for r in rows:
            if numbers[r['id']] is None:
                numbers[r['id']] = create_issue(r)
                bodies[numbers[r['id']]] = issue_body(r)
                created += 1
                print(f"[CREATED {r['id']} -> {padded(numbers[r['id']])}]")
        for r in rows:
            sync_row(r, numbers, bodies)
    except GhFail as e:
        print(f"[SWITCH-FAIL: {e}; no local file was rewritten, the store and key are unchanged. Fix the cause and re-run: created issues are found again by their marker]")
        return 1
    files = apply_rewrites(numbers)
    report_other_hits(numbers)
    write_tracker(ARCH, 'github')
    print(f"[SWITCHED: {created} issue(s) created, {files} file(s) rewritten, tracker: github; "
          f"branch {store_lib.branch_name(ARCH)} kept as the archive]")
    return 0


if __name__ == '__main__':
    sys.exit(main())
