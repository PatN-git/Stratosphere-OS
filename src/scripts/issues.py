#!/usr/bin/env python3
"""issues.py — the local tracker backend (`tracker: local`): one markdown file per issue on the `<repo>/issues` branch.

The store is never in the working tree or in a feature branch: issue files live at `docs/issues/<id>.md` (closed ones
under `docs/issues/archive/`) on the tracker branch, so every branch and worktree reads one state, as on GitHub.
The branch is the `tracker_branch:` key of `.memory/ARCHITECTURE.md`, else `<repo>/issues` (`<repo>` = the `origin`
URL's last segment, else the top-level folder name). Writes use git plumbing (a temporary index, `commit-tree`,
then `update-ref <ref> <new> <old>`): the compare-and-set makes every write atomic, so two `claim` calls never both
win; a lost race re-reads and retries, never forces. Agents never edit issue files by hand.

  reads (JSON)   get <id> | list [--status S] [--label L] [--milestone M] [--parent P] [--all] | wip | children <id>
                 | blockers <id> | branch
  ready          3c/3z candidate lines (`ice_read.py candidates` format) whose effective blockers have cleared,
                 plus [MISSING-LABELS] and [BLOCKED <id> <- <blocker>] lines
  writes         create | set | comment | claim | close | reopen | label
  maintenance    init | check | sync [--remote origin] | migrate [--map .memory/BACKLOG_MAP.md]

Exit: 0 ok; 1 a finding, a refused write ([CLAIMED], [ERROR …]) or an unknown id.
"""
import argparse
import datetime
import json
import os
import re
import fnmatch
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _tracker_common import (NONE_TOKENS, candidates, csv_list, edge_verdict, effective_blockers, longer_id_globs,
                             make_row, resolve_unit)

ROOT = 'docs/issues'
ARCHIVE = f'{ROOT}/archive'
README = f'{ROOT}/README.md'
ARCH_DEFAULT = '.memory/ARCHITECTURE.md'
MAP_DEFAULT = '.memory/BACKLOG_MAP.md'
FIELDS = ('type', 'id', 'title', 'status', 'labels', 'milestone', 'parent', 'blocked_by', 'claimed_by',
          'created', 'updated', 'closed', 'close_reason')
STATUSES = ('needs_spec', 'planned', 'in progress', 'in review', 'blocked', 'done')
REASONS = ('completed', 'not planned')
# The canonical label vocabulary of references/label-taxonomy.md (a test pins the two equal); `area:*` slugs are the
# project's own and live in the store's README.
CANONICAL = {
    'type': ('bug', 'content', 'feature', 'improvement', 'maintenance', 'research'),
    'mode': ('HITL', 'AFK'),
    'tier': ('epic', 'slice'),
    'priority': ('high', 'medium', 'low'),
    'size': ('large', 'medium', 'small'),
    'scope': ('baseline', 'differentiator', 'deferred'),
    'concept': ('map', 'research', 'grilling', 'prototype', 'task'),
    'risk': ('one-way',),
}
README_TEXT = (
    "# Issues\n\n"
    "Local tracker store (`tracker: local`). Read and write it only with `python .agents/scripts/issues.py`; "
    "label rules: `references/label-taxonomy.md`.\n\n"
    "## Area labels\n")
MAX_RETRIES = 3
COMMENTS = '\n<!-- issues.py: comments -->\n## Comments\n'  # the marker keeps a body's own `## Comments` heading body text


class IssuesError(RuntimeError):
    """A refused read or write; the message is the one line to print."""


def today():
    return datetime.date.today().isoformat()


def now():
    """`updated`: a UTC timestamp, so sync's newest-wins merge orders two edits made on one day."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


# --- git ------------------------------------------------------------------------------------------------------------

def _git(*args, data=None, env=None, check=True):
    """stdout of one git call (bytes when `data` is bytes, else text). IssuesError on a non-zero exit when `check`."""
    binary = isinstance(data, bytes)
    r = subprocess.run(['git', *args], input=data, capture_output=True, text=not binary,
                       env={**os.environ, **(env or {})})
    if check and r.returncode:
        err = r.stderr.decode('utf-8', 'replace') if binary else r.stderr
        raise IssuesError(f"[ERROR] git {args[0]}: {(err.strip() or f'exit {r.returncode}').splitlines()[0]}")
    return r.stdout if check else (r.returncode, r.stdout)


def _identity():
    """Author/committer env for commit-tree when the repo has no user configured (CI, a fresh container)."""
    rc, _ = _git('config', 'user.email', check=False)
    if rc == 0:
        return {}
    return {'GIT_AUTHOR_NAME': 'issues.py', 'GIT_AUTHOR_EMAIL': 'issues.py@localhost',
            'GIT_COMMITTER_NAME': 'issues.py', 'GIT_COMMITTER_EMAIL': 'issues.py@localhost'}


def frontmatter_key(path, key):
    """A scalar frontmatter value of a markdown file, None when the file or key is absent."""
    try:
        text = Path(path).read_text(encoding='utf-8-sig')
    except OSError:
        return None
    fm = text.split('---', 2)[1] if text.startswith('---') else ''
    m = re.search(rf'^{re.escape(key)}:\s*(\S+)\s*$', fm, re.M)
    return m.group(1).strip('"\'') if m else None


def repo_name():
    rc, url = _git('remote', 'get-url', 'origin', check=False)
    if rc == 0 and url.strip():
        # https://host/o/r.git, git@host:o/r.git, C:\path\r.git: the last segment on any separator
        return re.sub(r'\.git$', '', re.split(r'[/\\:]', url.strip().rstrip('/\\'))[-1])
    return Path(_git('rev-parse', '--show-toplevel').strip()).name


def at_top(path):
    """A relative path resolved against the repository top level (issues.py may run from a subdirectory)."""
    p = Path(path)
    if p.is_absolute():
        return p
    rc, top = _git('rev-parse', '--show-toplevel', check=False)
    return Path(top.strip()) / p if rc == 0 and top.strip() else p


def branch_name(arch=ARCH_DEFAULT):
    """The `tracker_branch:` key (a template placeholder like `<repo>/issues` does not count), else `<repo>/issues`."""
    key = frontmatter_key(at_top(arch), 'tracker_branch')
    return key if key and '<' not in key else f"{repo_name()}/issues"


def head(ref):
    rc, out = _git('rev-parse', '--verify', '-q', f'{ref}^{{commit}}', check=False)
    return out.strip() if rc == 0 else None


def read_tree(sha):
    """{path: text} of every file under docs/issues/ at commit `sha`, in two git calls."""
    paths = [p for p in _git('ls-tree', '-r', '-z', '--full-tree', '--name-only', sha, '--', ROOT).split('\0') if p]
    if not paths:
        return {}
    out = _git('cat-file', '--batch', data=''.join(f'{sha}:{p}\n' for p in paths).encode())
    files, pos = {}, 0
    for p in paths:
        header_end = out.index(b'\n', pos)
        size = int(out[pos:header_end].split()[2])
        files[p] = out[header_end + 1:header_end + 1 + size].decode('utf-8')
        pos = header_end + 1 + size + 1
    return files


def commit(parents, base, changes, message):
    """A commit whose tree is `base` (a commit or None) with `changes` ({path: text | None}) applied. Returns its sha."""
    index = str(Path(_git('rev-parse', '--absolute-git-dir').strip()) / f'issues-index-{uuid.uuid4().hex}')
    env = {'GIT_INDEX_FILE': index}
    try:
        _git('read-tree', *([base] if base else ['--empty']), env=env)
        lines = []
        for path, text in sorted(changes.items()):
            if text is None:
                lines.append(f"0 {'0' * 40}\t{path}")
            else:
                sha = _git('hash-object', '-w', '--stdin', '--no-filters', data=text.encode('utf-8')).decode().strip()
                lines.append(f"100644 {sha}\t{path}")
        _git('update-index', '--index-info', data=('\n'.join(lines) + '\n').encode(), env=env)
        tree = _git('write-tree', env=env).strip()
    finally:
        Path(index).unlink(missing_ok=True)
    args = ['commit-tree', tree]
    for p in parents:
        args += ['-p', p]
    return _git(*args, '-m', message, env=_identity()).strip()


def update_ref(ref, new, old):
    """Compare-and-set: True when `ref` moved from `old` (None = must not exist) to `new`."""
    rc, _ = _git('update-ref', ref, new, old or '', check=False)
    return rc == 0


# --- issue files ----------------------------------------------------------------------------------------------------

def _scalar(text):
    text = text.strip()
    if text in ('', 'null', '~'):
        return None
    if text.startswith('"'):
        return json.loads(text)
    return text


def _emit(value):
    if value is None:
        return 'null'
    if isinstance(value, list):
        return '[' + ', '.join(_emit(v) for v in value) + ']'
    plain = (re.fullmatch(r'[A-Za-z0-9][\w.:/@<>()+-]*( [\w.:/@<>()+-]+)*', value) and ': ' not in value
             and value.lower() not in ('null', 'true', 'false', 'yes', 'no', 'on', 'off'))
    return value if plain else json.dumps(value, ensure_ascii=False)


def parse_issue(text):
    """{fields…, body, comments} of an issue file. IssuesError when there is no frontmatter."""
    if not text.startswith('---\n') or '\n---\n' not in text[3:]:
        raise IssuesError("[ERROR] issue file without frontmatter")
    fm, rest = text[4:].split('\n---\n', 1)
    issue = {k: None for k in FIELDS}
    for line in fm.splitlines():
        key, _, value = line.partition(':')
        value = value.strip()
        if value.startswith('['):
            inner = value[1:-1].strip()
            issue[key] = [_scalar(v) for v in re.findall(r'"(?:[^"\\]|\\.)*"|[^,]+', inner)] if inner else []
        else:
            issue[key] = _scalar(value)
    for key in ('labels', 'blocked_by'):
        issue[key] = [v for v in (issue[key] or []) if v]
    body, sep, comments = rest.rpartition(COMMENTS)
    if not sep:
        body, comments = rest, ''
    issue['body'] = body.strip('\n')
    issue['comments'] = re.findall(r'^- .*(?:\n  .*)*', comments, re.M)
    return issue


def render_issue(issue):
    fm = '\n'.join(f"{k}: {_emit(issue.get(k))}" for k in FIELDS)
    text = f"---\n{fm}\n---\n{issue.get('body') or ''}\n"
    if issue.get('comments'):
        text += COMMENTS + '\n'.join(issue['comments']) + '\n'
    return text


def path_of(issue):
    return f"{ARCHIVE if issue.get('closed') else ROOT}/{issue['id']}.md"


class Store:
    """The issues at one commit of the tracker branch: {id: issue}, plus the README's area slugs."""

    def __init__(self, files):
        self.files = files
        self.issues = {}
        for path, text in files.items():
            if path.endswith('.md') and path != README:
                issue = parse_issue(text)
                issue['_path'] = path
                self.issues[issue['id']] = issue
        self.areas = re.findall(r'^- (area:\S+)\s*$', files.get(README, ''), re.M)

    def get(self, bt):
        issue = self.issues.get(bt)
        if issue is None:
            raise IssuesError(f"[NOT-FOUND {bt}]")
        return issue

    def changes(self, issue):
        """{path: text | None} that writes `issue` and drops its old path when close/reopen moved it."""
        out = {path_of(issue): render_issue(issue)}
        if issue.get('_path') and issue['_path'] != path_of(issue):
            out[issue['_path']] = None
        return out

    def rows(self):
        """reconcile.py's row shape {id: {status, labels, milestone, parent, blocked_by}}; closed issues are done."""
        return {bt: make_row('done' if i['closed'] else i['status'], i['labels'], i['milestone'], i['parent'],
                             i['blocked_by']) for bt, i in self.issues.items()}


class Tracker:
    def __init__(self, arch=ARCH_DEFAULT, map_path=MAP_DEFAULT):
        self.branch = branch_name(arch)
        self.ref = f'refs/heads/{self.branch}'
        self.map_path = at_top(map_path).as_posix()

    def store(self):
        sha = head(self.ref)
        if sha is None:
            if Path(self.map_path).exists():
                raise IssuesError(f"[MIGRATE-FIRST] {self.map_path} exists and branch {self.branch} does not: "
                                  "run `python .agents/scripts/issues.py migrate`")
            raise IssuesError(f"[NO-STORE] branch {self.branch} does not exist: run `python .agents/scripts/issues.py init`")
        return Store(read_tree(sha))

    def write(self, mutate, message, allow_new=False):
        """Apply `mutate(store) -> (changes, result)` as one commit, retried when the ref moved meanwhile."""
        for _ in range(MAX_RETRIES + 1):
            old = head(self.ref)
            if old is None and not allow_new:
                self.store()  # raises the right halt
            changes, result = mutate(Store(read_tree(old)) if old else Store({}))
            if not changes:
                return result
            if update_ref(self.ref, commit([old] if old else [], old, changes, message), old):
                return result
        raise IssuesError(f"[CONFLICT] {self.branch} moved {MAX_RETRIES + 1} times during the write; nothing written")


# --- reads ----------------------------------------------------------------------------------------------------------

def summary(issue):
    return {k: issue[k] for k in FIELDS if k != 'type'} | {'state': 'CLOSED' if issue['closed'] else 'OPEN'}


def full(issue):
    """`get`'s JSON: the summary plus the body and the comment lines (tracker_switch.read_rows reads the same)."""
    return summary(issue) | {'body': issue['body'], 'comments': issue['comments']}


def select(store, status=None, labels=(), milestone=None, parent=None, include_closed=False):
    out = []
    for issue in sorted(store.issues.values(), key=lambda i: i['id']):
        if issue['closed'] and not include_closed:
            continue
        if status and issue['status'] != status:
            continue
        if any(l not in issue['labels'] for l in labels):
            continue
        if milestone and issue['milestone'] != milestone:
            continue
        if parent and issue['parent'] != parent:
            continue
        out.append(summary(issue))
    return out


def as_gh(issue):
    """The `gh issue list --json` shape ice_read.candidates reads, keyed by `id` instead of `number`."""
    return {'id': issue['id'], 'title': issue['title'],
            'labels': [{'name': l} for l in issue['labels']] + [{'name': f"status:{issue['status']}"}],
            'milestone': {'title': issue['milestone']} if issue['milestone'] else None, 'body': issue['body']}


def open_as_gh(store):
    return [as_gh(i) for i in sorted(store.issues.values(), key=lambda i: i['id']) if not i['closed']]


def default_branch():
    rc, out = _git('symbolic-ref', '-q', '--short', 'refs/remotes/origin/HEAD', check=False)
    if rc == 0 and out.strip():
        return out.strip()
    return next((b for b in ('main', 'master') if head(f'refs/heads/{b}')), None)


def make_merged_of(store):
    """`merged_of(bt)` for reconcile.edge_verdict without a PR host: the blocker's ship-unit branches (pr_body
    globs) are merged when every local or remote-tracking one is an ancestor of the default branch, 'none' when no
    such branch exists (deleted after merge, or a Spike with no code), 'open' otherwise."""
    target = default_branch()
    refs = _git('for-each-ref', '--format=%(refname:short)', 'refs/heads', 'refs/remotes').split()

    def merged_of(bt):
        i = store.issues.get(bt)
        if i is None or target is None:
            return None
        parent = store.issues.get(i['parent']) if i['parent'] else None
        try:
            globs = resolve_unit(bt, i['milestone'] or '—', i['parent'] or '—',
                                 (parent or {}).get('milestone') or '—', 'tier:epic' in i['labels'])['globs']
        except ValueError:
            return None
        def local(r):
            return r.split('/', 1)[1] if r.startswith('origin/') else r
        longer = longer_id_globs([bt, i['parent']], store.issues)
        hits = [r for r in refs if any(fnmatch.fnmatch(local(r), g) for g in globs)
                and not any(fnmatch.fnmatch(local(r), g) for g in longer)]
        if not hits:
            return 'none'
        return 'merged' if all(_git('merge-base', '--is-ancestor', r, target, check=False)[0] == 0
                               for r in hits) else 'open'
    return merged_of


def ready(store, merged_of=None):
    """(candidate lines, other lines): open leaves whose effective blockers all clear, then [BLOCKED]/[MISSING-LABELS]."""
    rows = store.rows()
    merged_of = merged_of or make_merged_of(store)
    free, blocked = [], []
    for issue in open_as_gh(store):
        bt = issue['id']
        unmet = [(blk, why) for blk in sorted(effective_blockers(bt, rows))
                 for verdict, _, why in [edge_verdict(bt, blk, rows, merged_of)] if verdict != 'OK']
        if unmet:
            blocked += [f"[BLOCKED {bt} <- {blk}] {why}" for blk, why in unmet]
        else:
            free.append(issue)
    lines, missing = candidates(free)
    if blocked:
        shown = {line.split(' |', 1)[0] for line in lines + [m.split(' ')[1] for m in missing]}
        wanted = candidate_ids(store)
        blocked = [b for b in blocked if b.split(' ')[1] in wanted and b.split(' ')[1] not in shown]
    return lines, missing + blocked


def candidate_ids(store):
    lines, missing = candidates(open_as_gh(store))
    return {l.split(' |', 1)[0] for l in lines} | {m.split(' ')[1] for m in missing}


# --- writes ---------------------------------------------------------------------------------------------------------

def slug(title):
    words = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-').split('-')
    out = ''
    for w in words:
        if len(out) + len(w) + 1 > 40 and out:
            break
        out = f"{out}-{w}" if out else w
    return out or 'issue'


def new_id(store, title):
    base = f"BT-LOCAL-{slug(title)}"
    n, bt = 1, base
    while bt in store.issues:
        n += 1
        bt = f"{base}-{n}"
    return bt


def _status(value):
    if value not in STATUSES:
        raise IssuesError(f"[ERROR] status {value!r} is not one of {', '.join(STATUSES)}")
    return value


def _labels(values):
    out = []
    for v in values or ():
        out += csv_list(v)
    return out


def _require(store, ids, what):
    for bt in ids:
        if bt not in store.issues:
            raise IssuesError(f"[ERROR] {what} {bt} not found")


def _cycle(store, start):
    """The blocked-by cycle through `start` (a list of ids) or None."""
    stack, seen = [(start, [start])], set()
    while stack:
        node, trail = stack.pop()
        for nxt in store.issues.get(node, {}).get('blocked_by', []):
            if nxt == start:
                return trail + [start]
            if nxt not in seen:
                seen.add(nxt)
                stack.append((nxt, trail + [nxt]))
    return None


def _body(path):
    return Path(path).read_text(encoding='utf-8-sig').replace('\r\n', '\n').strip('\n') if path else ''


def cmd_create(store, a):
    labels = _labels(a.label)
    status = next((l[7:] for l in labels if l.startswith('status:')), None)
    labels = [l for l in labels if not l.startswith('status:')]
    parent = None if (a.parent or '—') in NONE_TOKENS else a.parent
    blockers = csv_list(a.blocked_by)
    _require(store, ([parent] if parent else []) + blockers, 'parent or blocker')
    bt = new_id(store, a.title)
    issue = {'type': 'issue', 'id': bt, 'title': a.title, 'status': _status(a.status or status or 'planned'),
             'labels': labels, 'milestone': None if (a.milestone or '—') in NONE_TOKENS else a.milestone,
             'parent': parent, 'blocked_by': blockers, 'claimed_by': None, 'created': today(), 'updated': now(),
             'closed': None, 'close_reason': None, 'body': _body(a.body_file), 'comments': []}
    store.issues[bt] = issue
    return store.changes(issue), bt


def cmd_set(store, a):
    issue = store.get(a.id)
    if a.status:
        if issue['closed'] and a.status != 'done':
            raise IssuesError(f"[ERROR] {a.id} is closed: `reopen` it first")
        issue['status'] = _status(a.status)
        if a.status == 'done' and not issue['closed']:  # done == closed, as on GitHub: archive it now
            issue.update(closed=today(), close_reason='completed', claimed_by=None)
    for l in _labels(a.add_label):
        if l.startswith('status:'):
            raise IssuesError("[ERROR] status is a field: use --status")
        if l not in issue['labels']:
            issue['labels'].append(l)
    issue['labels'] = [l for l in issue['labels'] if l not in _labels(a.remove_label)]
    if a.milestone is not None:
        issue['milestone'] = None if a.milestone in NONE_TOKENS else a.milestone
    if a.parent is not None:
        issue['parent'] = None if a.parent in NONE_TOKENS else a.parent
        if issue['parent'] == a.id:
            raise IssuesError(f"[ERROR] {a.id} cannot be its own parent")
        _require(store, [issue['parent']] if issue['parent'] else [], 'parent')
    add = csv_list(a.add_blocker)
    _require(store, add, 'blocker')
    if a.id in add:
        raise IssuesError(f"[ERROR] {a.id} cannot block itself")
    issue['blocked_by'] = [b for b in issue['blocked_by'] + [b for b in add if b not in issue['blocked_by']]
                           if b not in csv_list(a.remove_blocker)]
    if add and (cyc := _cycle(store, a.id)):
        raise IssuesError(f"[ERROR] blocked-by cycle: {' <- '.join(cyc)}")
    if a.title:
        issue['title'] = a.title
    if a.body_file:
        issue['body'] = _body(a.body_file)
    issue['updated'] = now()
    return store.changes(issue), a.id


def _comment_entry(text):
    lines = text.replace('\r\n', '\n').strip('\n').split('\n')
    return '\n'.join([f"- {today()}: {lines[0]}"] + [f"  {l}" for l in lines[1:]])


def cmd_comment(store, a):
    issue = store.get(a.id)
    issue['comments'].append(_comment_entry(a.body if a.body is not None else _body(a.body_file)))
    issue['updated'] = now()
    return store.changes(issue), a.id


def current_branch():
    rc, out = _git('branch', '--show-current', check=False)
    return out.strip() if rc == 0 and out.strip() else 'unknown'


def cmd_claim(store, a):
    issue = store.get(a.id)
    who = a.by or current_branch()
    if issue['closed'] or issue['status'] == 'done':
        raise IssuesError(f"[ERROR] {a.id} is done")
    if issue['claimed_by'] not in (None, who):
        raise IssuesError(f"[CLAIMED {a.id} by {issue['claimed_by']}]")
    if issue['status'] == 'in progress' and issue['claimed_by'] == who:
        return {}, a.id
    issue.update(status='in progress', claimed_by=who, updated=now())
    return store.changes(issue), a.id


def cmd_close(store, a):
    issue = store.get(a.id)
    if a.reason not in REASONS:
        raise IssuesError(f"[ERROR] --reason must be one of {', '.join(REASONS)}")
    if issue['closed'] and issue['close_reason'] == a.reason:
        return {}, a.id
    issue.update(status='done', closed=issue['closed'] or today(), close_reason=a.reason, claimed_by=None, updated=now())
    return store.changes(issue), a.id


def cmd_reopen(store, a):
    issue = store.get(a.id)
    issue.update(status=_status(a.status or 'planned'), closed=None, close_reason=None, updated=now())
    return store.changes(issue), a.id


def cmd_label(store, a):
    if not re.fullmatch(r'area:[\w<>-]+', a.name):
        raise IssuesError(f"[ERROR] only project `area:*` labels are added locally; {a.name!r} needs a "
                          "label-taxonomy change")
    if a.name in store.areas:
        return {}, a.name
    return {README: store.files.get(README, README_TEXT).rstrip('\n') + f"\n- {a.name}\n"}, a.name


# --- check ----------------------------------------------------------------------------------------------------------

def known_label(label, areas):
    prefix, _, value = label.partition(':')
    return value in CANONICAL.get(prefix, ()) or (prefix == 'area' and label in areas)


def check(store):
    findings = []
    for bt, i in sorted(store.issues.items()):
        def bad(why):
            findings.append(f"[CHECK-FAIL {bt}] {why}")
        if i['_path'] != path_of(i):
            bad(f"file {i['_path']} does not match its id or closed state")
        if i['status'] not in STATUSES:
            bad(f"status {i['status']!r}")
        if i['closed'] and i['status'] != 'done':
            bad("closed but not done")
        for l in i['labels']:
            if l.startswith('status:'):
                bad(f"status label {l} (status is a field)")
            elif not known_label(l, store.areas):
                bad(f"unknown label {l}")
        if not any(l.startswith('concept:') for l in i['labels']):
            count = {p: sum(l.startswith(p + ':') for l in i['labels']) for p in ('type', 'mode', 'size')}
            if 'tier:slice' in i['labels'] and any(count[p] != 1 for p in count):
                bad("a slice needs exactly one type:, mode: and size:")
            if 'tier:epic' in i['labels'] and (count['type'] != 1 or count['mode'] or count['size']):
                bad("an epic needs one type: and no mode: or size:")
        if i['parent'] == bt:
            bad("its own parent")
        if i['status'] == 'done' and not i['closed']:
            bad("done but not closed: run `issues.py close`")
        if i['parent'] and i['parent'] not in store.issues:
            bad(f"parent {i['parent']} not found")
        for b in i['blocked_by']:
            if b == bt or b not in store.issues:
                bad(f"blocker {b} {'is itself' if b == bt else 'not found'}")
        if (cyc := _cycle(store, bt)) and bt == min(cyc):
            bad(f"blocked-by cycle: {' <- '.join(cyc)}")
    return findings


# --- sync -----------------------------------------------------------------------------------------------------------

def _merge_issue(base, ours, theirs):
    """Field merge of one issue changed on both sides: a field one side left at base takes the other side; both
    changed -> the newer `updated` (ours on a tie); comment lines are a union in order."""
    newer = theirs if (theirs.get('updated') or '') > (ours.get('updated') or '') else ours
    merged = {}
    for key in FIELDS + ('body',):
        b = base.get(key) if base else None
        o, t = ours.get(key), theirs.get(key)
        merged[key] = t if o == b else o if t == b else newer.get(key)
    seen = list(ours['comments'])
    merged['comments'] = seen + [c for c in theirs['comments'] if c not in seen]
    merged['_path'] = ours['_path']
    return merged


def merge_stores(base, ours, theirs):
    """{path: text | None} that turns `ours` into the merge of `ours` and `theirs` over `base`."""
    changes = {}
    for bt in sorted(set(ours.issues) | set(theirs.issues)):
        b, o, t = base.issues.get(bt), ours.issues.get(bt), theirs.issues.get(bt)
        if t is None or (o is not None and render_issue(t) == render_issue(o)):
            continue
        if o is None:
            merged = dict(t, _path=None)
        elif b is not None and render_issue(o) == render_issue(b):
            merged = dict(t, _path=o['_path'])
        else:
            merged = _merge_issue(b, o, t)
        if o is None or render_issue(merged) != render_issue(o) or path_of(merged) != o['_path']:
            changes.update(ours.changes(merged))
    for area in theirs.areas:
        if area not in ours.areas:
            ours.areas.append(area)
            changes[README] = ours.files.get(README, README_TEXT).rstrip('\n') + '\n' + '\n'.join(
                f"- {a}" for a in ours.areas if f"- {a}" not in ours.files.get(README, '')) + '\n'
    return changes


def cmd_sync(tracker, remote):
    rc, _ = _git('fetch', '-q', remote, f'+{tracker.ref}:refs/remotes/{remote}/{tracker.branch}', check=False)
    theirs = head(f'refs/remotes/{remote}/{tracker.branch}') if rc == 0 else None
    if theirs is None:
        return f"[SYNC-LOCAL-ONLY] {remote} has no {tracker.branch}; push it with the next ship push"
    for _ in range(MAX_RETRIES + 1):
        ours = head(tracker.ref)
        if ours == theirs:
            return "[SYNC-UP-TO-DATE]"
        if ours is None or _git('merge-base', '--is-ancestor', ours, theirs, check=False)[0] == 0:
            if update_ref(tracker.ref, theirs, ours):
                return "[SYNC-FF]"
            continue
        if _git('merge-base', '--is-ancestor', theirs, ours, check=False)[0] == 0:
            return f"[SYNC-AHEAD] local {tracker.branch} has commits {remote} lacks; push it with the next ship push"
        base = _git('merge-base', ours, theirs).strip()
        o = Store(read_tree(ours))
        changes = merge_stores(Store(read_tree(base)), o, Store(read_tree(theirs)))
        new = commit([ours, theirs], ours, changes, f"issues: merge {remote}/{tracker.branch}")
        if update_ref(tracker.ref, new, ours):
            return f"[SYNC-MERGED] {len(changes)} file(s) field-merged"
    raise IssuesError(f"[CONFLICT] {tracker.branch} kept moving during sync; nothing written")


# --- migrate (one-shot: a v5 BACKLOG_MAP.md becomes the store) -----------------------------------------------------

def _ice_lines(cell):
    m = re.search(r'I:\s*([0-9.]+)\s*,\s*C:\s*([0-9.]+\s*%?)', cell or '')
    return [f"- **Impact:** {m.group(1)}", f"- **Confidence:** {m.group(2).replace(' ', '')}"] if m else []


def _row_cells(line):
    """(BT id, raw `|`-split cells) of a BACKLOG_MAP data row, else None (header, separator, placeholder)."""
    if not line.lstrip().startswith('|'):
        return None
    raw = line.split('|')
    if len(raw) < 11:  # leading + trailing empty cells around 9 columns
        return None
    bt = raw[1].strip()
    if not re.match(r'^BT-(LOCAL-)?\S+$', bt) or bt == 'BT-XXX':
        return None
    return bt, raw


def map_rows(text):
    """The 9-cell v5 BACKLOG_MAP data rows as [{id, title, status, labels, milestone, parent, blocked_by, ice, refs}]
    (the cells as written, none tokens dropped from the lists). Pure."""
    out = []
    for line in text.splitlines():
        hit = _row_cells(line)
        if hit:
            bt, raw = hit
            c = [x.strip() for x in raw]
            out.append({'id': bt, 'title': c[2], 'status': c[3], 'labels': csv_list(c[4]), 'milestone': c[5],
                        'parent': c[6], 'blocked_by': csv_list(c[7]), 'ice': c[8], 'refs': c[9]})
    return out


def parse_backlog(path):
    """{BT-id: {status, labels, milestone, parent, blocked_by}} of a map file, in reconcile.py's row shape."""
    return {r['id']: make_row(r['status'], r['labels'], r['milestone'], r['parent'], r['blocked_by'])
            for r in map_rows(Path(path).read_text(encoding='utf-8'))}


def migrate_issues(map_text, map_path):
    """{path: text} of the store a BACKLOG_MAP holds: one file per row (done rows archived), README with its areas."""
    files, areas = {}, []
    for line in map_text.splitlines():
        if '**Area (`area:xxx`)**' in line:
            areas = [a for a in re.findall(r'`(area:[^`]+)`', line) if '<' not in a and a != 'area:xxx']
    for r in map_rows(map_text):
        done = r['status'] == 'done'
        body = [f"Migrated from `{map_path}`."]
        if ice := _ice_lines(r['ice']):
            body.append('\n'.join(ice))
        if r['refs'] not in NONE_TOKENS:
            body.append(f"Refs: {r['refs']}")
        issue = {'type': 'issue', 'id': r['id'], 'title': r['title'],
                 'status': r['status'] if r['status'] in STATUSES else 'planned',
                 'labels': [l for l in r['labels'] if not l.startswith('status:')],
                 'milestone': None if r['milestone'] in NONE_TOKENS else r['milestone'],
                 'parent': None if r['parent'] in NONE_TOKENS else r['parent'], 'blocked_by': r['blocked_by'],
                 'claimed_by': None, 'created': today(), 'updated': today(),
                 'closed': today() if done else None, 'close_reason': 'completed' if done else None,
                 'body': '\n\n'.join(body), 'comments': []}
        files[path_of(issue)] = render_issue(issue)
    files[README] = README_TEXT + ''.join(f"- {a}\n" for a in areas)
    return files


def cmd_migrate(tracker, map_path):
    src = at_top(map_path)
    if not src.exists():
        raise IssuesError(f"[ERROR] {map_path} not found: nothing to migrate")
    old = head(tracker.ref)
    if old and Store(read_tree(old)).issues:
        raise IssuesError(f"[ERROR] branch {tracker.branch} already holds issues: the map was migrated before")
    files = migrate_issues(src.read_text(encoding='utf-8'), map_path)  # an `init`-only branch is built upon
    if not update_ref(tracker.ref, commit([old] if old else [], old, files, f"issues: migrate {map_path}"), old):
        raise IssuesError(f"[CONFLICT] {tracker.branch} appeared during the migration; nothing written")
    dest = src.parent / 'archive' / f"BACKLOG_MAP.{today()}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    src.replace(dest)
    return f"[MIGRATED] {len(files) - 1} issue(s) to {tracker.branch}; map moved to {dest.relative_to(at_top('.')).as_posix()}"


# --- CLI ------------------------------------------------------------------------------------------------------------

def parser():
    ap = argparse.ArgumentParser(description="Local tracker backend: one file per issue on the <repo>/issues branch.")
    ap.add_argument('--arch', default=ARCH_DEFAULT, help="ARCHITECTURE.md holding `tracker_branch:`")
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('get'); p.add_argument('id')
    p = sub.add_parser('list')
    p.add_argument('--status'); p.add_argument('--label', action='append'); p.add_argument('--milestone')
    p.add_argument('--parent'); p.add_argument('--all', action='store_true')
    sub.add_parser('wip')
    p = sub.add_parser('children'); p.add_argument('id')
    p = sub.add_parser('blockers'); p.add_argument('id')
    sub.add_parser('ready')
    sub.add_parser('branch')
    p = sub.add_parser('create')
    p.add_argument('--title', required=True); p.add_argument('--label', action='append')
    p.add_argument('--status'); p.add_argument('--milestone'); p.add_argument('--parent')
    p.add_argument('--blocked-by'); p.add_argument('--body-file')
    p = sub.add_parser('set'); p.add_argument('id')
    p.add_argument('--status'); p.add_argument('--add-label', action='append'); p.add_argument('--remove-label', action='append')
    p.add_argument('--milestone'); p.add_argument('--parent'); p.add_argument('--add-blocker'); p.add_argument('--remove-blocker')
    p.add_argument('--title'); p.add_argument('--body-file')
    p = sub.add_parser('comment'); p.add_argument('id')
    g = p.add_mutually_exclusive_group(required=True); g.add_argument('--body'); g.add_argument('--body-file')
    p = sub.add_parser('claim'); p.add_argument('id'); p.add_argument('--by')
    p = sub.add_parser('close'); p.add_argument('id'); p.add_argument('--reason', default='completed')
    p = sub.add_parser('reopen'); p.add_argument('id'); p.add_argument('--status')
    p = sub.add_parser('label'); p.add_argument('name')
    sub.add_parser('init')
    sub.add_parser('check')
    p = sub.add_parser('sync'); p.add_argument('--remote', default='origin')
    p = sub.add_parser('migrate'); p.add_argument('--map', default=MAP_DEFAULT)
    return ap


WRITES = {'create': cmd_create, 'set': cmd_set, 'comment': cmd_comment, 'claim': cmd_claim, 'close': cmd_close,
          'reopen': cmd_reopen, 'label': cmd_label}


def _dump(value):
    return json.dumps(value, ensure_ascii=False)


def run(a, out):
    tracker = Tracker(a.arch)
    if a.cmd == 'branch':
        out(tracker.branch)
    elif a.cmd == 'init':
        made = tracker.write(lambda s: ({} if s.files else {README: README_TEXT}, bool(not s.files)),
                             "issues: init", allow_new=True)
        out(f"[INIT {tracker.branch}]" if made else f"[INIT-EXISTS {tracker.branch}]")
    elif a.cmd == 'sync':
        out(cmd_sync(tracker, a.remote))
    elif a.cmd == 'migrate':
        out(cmd_migrate(tracker, a.map))
    elif a.cmd in WRITES:
        out(tracker.write(lambda s: WRITES[a.cmd](s, a), f"issues: {a.cmd} {getattr(a, 'id', '') or getattr(a, 'title', '') or getattr(a, 'name', '')}"))
    else:
        store = tracker.store()
        if a.cmd == 'get':
            out(_dump(full(store.get(a.id))))
        elif a.cmd == 'list':
            out(_dump(select(store, status=a.status, labels=a.label or (), milestone=a.milestone, parent=a.parent,
                             include_closed=a.all)))
        elif a.cmd == 'wip':
            out(_dump(select(store, status='in progress')))
        elif a.cmd == 'children':
            store.get(a.id)
            out(_dump(select(store, parent=a.id, include_closed=True)))
        elif a.cmd == 'blockers':
            rows = store.rows()
            out(_dump([{'id': b, 'title': store.issues[b]['title'] if b in rows else None,
                        'status': rows[b]['status'] if b in rows else None} for b in store.get(a.id)['blocked_by']]))
        elif a.cmd == 'ready':
            lines, other = ready(store)
            out('\n'.join(lines + other))
        elif a.cmd == 'check':
            findings = check(store)
            out('\n'.join(findings) if findings else f"[CHECK-OK {len(store.issues)} issue(s)]")
            return 1 if findings else 0
    return 0


def main(argv=None, out=print):
    a = parser().parse_args(argv)
    try:
        return run(a, out)
    except IssuesError as e:
        out(str(e))
        return 1


if __name__ == '__main__':
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
