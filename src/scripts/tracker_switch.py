#!/usr/bin/env python3
"""tracker_switch.py — move a local-tracker project to GitHub (local -> GitHub only; never the reverse).

Default is a dry run: prints the plan and writes nothing, locally or on GitHub. `--apply` then:
  1. creates a GitHub issue per `BT-LOCAL-*` row of `.memory/BACKLOG_MAP.md` (labels, status label, milestone; ICE and
     Refs in the body; a `done` row is closed), then links Parent and Blocked by through `gh api graphql`;
  2. appends the ICE and `Refs:` lines to the body of rows that already are real issues (`BT-007`);
  3. rewrites `BT-LOCAL-*` -> `BT-<padded>` under `.memory/` and `docs/`; every other hit is only reported;
  4. archives the map to `.memory/archive/` and, last, sets `tracker: github` in `.memory/ARCHITECTURE.md`.
Re-running is safe: an issue is found again by the `<!-- tracker-switch: BT-LOCAL-x -->` marker in its body, links
and body lines already present are skipped, and the key is the last write (`github` + no map = `[ALREADY-GITHUB]`).
A `gh` failure stops the run before any local rewrite. Exit: 0 ok/dry run, 1 a step failed, 2 cannot run.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reconcile

MAP = '.memory/BACKLOG_MAP.md'
ARCH = '.memory/ARCHITECTURE.md'
REWRITE_ROOTS = ('.memory', 'docs')
SKIP_DIRS = {'.git', '.tmp', 'node_modules', '.agents', '.claude', 'dist', '__pycache__'}
LOCAL_ID = re.compile(r'BT-LOCAL-[A-Za-z0-9_-]*[A-Za-z0-9_]')
MARKER = re.compile(r'<!-- tracker-switch: (\S+) -->')
NONE = reconcile.NONE_TOKENS | {'ICE: -'}


class GhFail(RuntimeError):
    pass


def write_tracker(path, value):
    """Set `tracker: <value>` in the frontmatter of `path`, keeping its line endings.
    True when the file changed. ValueError when the file has no frontmatter (nothing is written)."""
    text = Path(path).read_bytes().decode('utf-8-sig')
    eol = '\r\n' if '\r\n' in text else '\n'
    m = re.match(r'---\r?\n(.*?\r?\n)?---(?=\r?\n|$)', text, re.S)
    if not m:
        raise ValueError(f"{path} has no frontmatter to hold `tracker:`")
    head = m.group(1) or ''
    line = f"tracker: {value}"
    if re.search(r'^tracker:.*$', head, re.M):
        new_head = re.sub(r'^tracker:.*?(?=\r?$)', line, head, count=1, flags=re.M)
    else:
        new_head = head + line + eol
    if new_head == head:
        return False
    out = '---' + eol + new_head + text[m.end() - 3:]
    Path(path).write_bytes(out.encode('utf-8'))
    return True


def gh(*args):
    rc, out, err = reconcile._gh_run(list(args))
    if rc:
        raise GhFail(f"gh {' '.join(args[:2])}: {(err or out).strip()[:200]}")
    return out


def read_rows(path):
    """Rows of the map as dicts (id, title, status, labels, milestone, parent, blocked, ice, ref)."""
    rows = []
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        hit = reconcile._row_cells(line)
        if not hit:
            continue
        _, bt, title, status, labels, milestone, parent, blocked, ice, ref, _ = [p.strip() for p in hit[1]][:11]  # 9 columns between the outer pipes
        rows.append({'id': bt, 'title': title, 'status': status, 'milestone': milestone, 'parent': parent, 'ice': ice, 'ref': ref,
                     'labels': [l.strip() for l in labels.split(',') if l.strip() not in NONE],
                     'blocked': [b.strip() for b in blocked.split(',') if b.strip() not in NONE]})
    return rows


def extra_lines(row, body=''):
    """The ICE and `Refs:` lines the row holds that `body` lacks."""
    lines = []
    if row['ice'] not in NONE and not re.search(r'^ICE:', body, re.M):
        lines.append(row['ice'] if row['ice'].startswith('ICE:') else f"ICE: {row['ice']}")
    if row['ref'] not in NONE and not re.search(r'^Refs:', body, re.M):
        lines.append(f"Refs: {row['ref']}")
    return lines


def real_number(bt):
    m = re.match(r'^BT-0*(\d+)$', bt)
    return int(m.group(1)) if m else None


def padded(number):
    return f"BT-{number:03d}"


def body_file(text):
    p = Path('.tmp') / 'tracker-switch-body.md'
    p.parent.mkdir(exist_ok=True)
    p.write_text(text, encoding='utf-8', newline='\n')
    return str(p)


def create_issue(row):
    labels = [l for l in row['labels'] if not l.startswith('status:')] + [f"status:{row['status']}"]
    args = ['issue', 'create', '--title', row['title']]
    for label in labels:
        args += ['--label', label]
    if row['milestone'] not in NONE:
        args += ['--milestone', row['milestone']]
    body = '\n'.join([f"Migrated from local tracker `{row['id']}`.", f"<!-- tracker-switch: {row['id']} -->", *extra_lines(row)]) + '\n'
    out = gh(*args, '--body-file', body_file(body))
    return int(out.strip().rsplit('/', 1)[-1])


def node_id(number):
    return json.loads(gh('issue', 'view', str(number), '--json', 'id'))['id']


def link_parent(child, parent):
    """Put `child` under `parent`; skipped when it already is (`parent` reads as an object or null)."""
    current = json.loads(gh('issue', 'view', str(child), '--json', 'parent'))['parent']
    if current and current['number'] == parent:
        return
    q = 'mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,subIssueId:$c}){issue{number}}}'
    gh('api', 'graphql', '-f', f'query={q}', '-f', f'p={node_id(parent)}', '-f', f'c={node_id(child)}')


def link_blocked_by(issue, blocker):
    """Mark `issue` blocked by `blocker`; skipped when it already is (`blockedBy` reads as a connection)."""
    current = json.loads(gh('issue', 'view', str(issue), '--json', 'blockedBy'))['blockedBy']['nodes']
    if any(n['number'] == blocker for n in current):
        return
    q = 'mutation($i:ID!,$b:ID!){addBlockedBy(input:{issueId:$i,blockingIssueId:$b}){issue{number}}}'
    gh('api', 'graphql', '-f', f'query={q}', '-f', f'i={node_id(issue)}', '-f', f'b={node_id(blocker)}')


def text_files(root, skip_roots=()):
    for p in sorted(Path(root).rglob('*')):
        rel = p.relative_to(root)
        if p.is_file() and not SKIP_DIRS & set(rel.parts) and not any(rel.as_posix().startswith(s + '/') for s in skip_roots):
            try:
                yield p, p.read_bytes().decode('utf-8')
            except (UnicodeDecodeError, OSError):
                continue


def pending_rewrites(numbers):
    """(path, new text) for every file under REWRITE_ROOTS (the map and the archive excluded) that holds a mapped id."""
    for top in REWRITE_ROOTS:
        for p, text in text_files(top) if Path(top).is_dir() else ():
            if p.as_posix() == MAP or p.as_posix().startswith('.memory/archive/'):
                continue
            new = LOCAL_ID.sub(lambda m: padded(numbers[m.group(0)]) if numbers.get(m.group(0)) else m.group(0), text)
            if new != text:
                yield p, new


def apply_rewrites(numbers):
    """Write every pending rewrite; returns the count of files changed."""
    changed = list(pending_rewrites(numbers))
    for p, new in changed:
        p.write_bytes(new.encode('utf-8'))
    return len(changed)


def report_other_hits(numbers):
    for p, text in text_files('.', skip_roots=REWRITE_ROOTS):
        for n, line in enumerate(text.splitlines(), 1):
            for m in LOCAL_ID.finditer(line):
                num = numbers.get(m.group(0))
                print(f"[OTHER-HIT {p.as_posix()}:{n} {m.group(0)} -> {padded(num) if num else 'a new BT id'} (not edited)]")


def sync_row(row, numbers, bodies):
    """Bring one row's issue up to date: Refs/ICE lines on an existing issue, closed when done, Parent and Blocked by linked."""
    n = numbers[row['id']]
    is_existing = real_number(row['id']) is not None
    if is_existing and (lines := extra_lines(row, bodies.get(n, ''))):
        body = bodies.get(n, '').rstrip('\n') + '\n\n' + '\n'.join(lines) + '\n'
        gh('issue', 'edit', str(n), '--body-file', body_file(body))
    if row['status'] == 'done' and not is_existing:
        gh('issue', 'close', str(n))
    related = [(row['parent'], link_parent)] if row['parent'] not in NONE else []
    related += [(b, link_blocked_by) for b in row['blocked']]
    for other, link in related:
        target = numbers.get(other) or real_number(other)
        if target is None:
            print(f"[LINK-SKIP {row['id']}: {other} is not in the map]")
        else:
            link(n, target)


def archive_map():
    """Move the map to `.memory/archive/`, under a fresh name when an earlier run archived one."""
    dst = Path('.memory/archive/BACKLOG_MAP.md')
    dst.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    while dst.exists():
        n += 1
        dst = dst.with_name(f"BACKLOG_MAP.{n}.md")
    shutil.move(MAP, dst)
    return dst


def main(argv=None):
    ap = argparse.ArgumentParser(description="Move a local-tracker project to GitHub (dry run unless --apply).")
    ap.add_argument('--apply', action='store_true', help="write: create the issues, rewrite ids, archive the map, set tracker: github")
    args = ap.parse_args(argv)
    has_map = Path(MAP).is_file()
    if reconcile.read_tracker(ARCH) == 'github':
        print(f"[ALREADY-GITHUB: tracker is github; nothing to switch{'; the BACKLOG_MAP.md left in .memory/ is not touched' if has_map else ''}]")
        return 0
    if reconcile._gh_run(['auth', 'status'])[0]:
        print("[GH-UNAVAILABLE: gh is missing or not logged in (`gh auth login`); nothing changed]")
        return 2
    try:
        issues = json.loads(gh('issue', 'list', '--state', 'all', '--limit', '1000', '--json', 'number,body'))
        rows = read_rows(MAP) if has_map else []
        marked = {m.group(1): i['number'] for i in issues for m in [MARKER.search(i['body'] or '')] if m}
        bodies = {i['number']: i['body'] or '' for i in issues}
        numbers = {r['id']: real_number(r['id']) or marked.get(r['id']) for r in rows}
        for r in rows:
            if numbers[r['id']] is None:
                ms = f" milestone={r['milestone']}" if r['milestone'] not in NONE else ''
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
        for r in rows:
            if numbers[r['id']] is None:
                numbers[r['id']] = create_issue(r)
                created += 1
                print(f"[CREATED {r['id']} -> {padded(numbers[r['id']])}]")
        for r in rows:
            sync_row(r, numbers, bodies)
    except GhFail as e:
        print(f"[SWITCH-FAIL: {e}; no local file was rewritten, the map and key are unchanged. Fix the cause and re-run: created issues are found again by their marker]")
        return 1
    files = apply_rewrites(numbers)
    report_other_hits(numbers)
    archived = archive_map() if has_map else None
    write_tracker(ARCH, 'github')
    print(f"[SWITCHED: {created} issue(s) created, {files} file(s) rewritten, "
          f"map archived to {archived.as_posix() if archived else 'nowhere (none existed)'}, tracker: github]")
    return 0


if __name__ == '__main__':
    sys.exit(main())
