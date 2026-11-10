#!/usr/bin/env python3
"""_tracker_common.py — pure tracker logic, graph operations, expectation parsing and file rewrites."""
import graphlib
import re
from pathlib import Path

NONE_TOKENS = frozenset({'', '-', '—'})  # an empty value in a map cell, an argument or a row field
UNIT_ID_RE = re.compile(r'BT-(\d+|LOCAL-[a-z0-9-]+)')  # a GitHub number or a local-tracker id
MILESTONE_RE = re.compile(r'v(\d+)\.(\d+)\.(\d+)')
SHIPPED = ('in review', 'done')  # a same-ship-unit blocker in one of these satisfies its edge (D3)


def bt_id(n):
    return f"BT-{int(n):03d}"


def norm(token):
    return None if token in NONE_TOKENS else token


def csv_list(text):
    """The items of a comma list, none tokens dropped."""
    return [t.strip() for t in (text or '').split(',') if t.strip() not in NONE_TOKENS]


def make_row(status, labels, milestone, parent, blocked_by):
    """reconcile.py's row shape, which every tracker source builds."""
    return {'status': status, 'labels': set(labels), 'milestone': milestone or '—', 'parent': parent or '—',
            'blocked_by': set(blocked_by)}


def open_ids(rows):
    """BT ids of every row whose status is not `done`, in map order. Pure."""
    return [bt for bt, r in rows.items() if r['status'] != 'done']


# --- D1: the ship unit ----------------------------------------------------------------------------------------------

def _milestone(value, flag):
    """(X, Y) of a `vX.Y.Z` milestone, None for a none token; ValueError otherwise."""
    if value is None or value.strip() in NONE_TOKENS:
        return None
    m = MILESTONE_RE.fullmatch(value.strip())
    if not m:
        raise ValueError(f"{flag} must look like v<X>.<Y>.<Z> or be none (empty, '-' or an em dash), got {value!r}")
    return int(m.group(1)), int(m.group(2))


def _unit_id(bt):
    """`BT-<padded>` for a GitHub number, the id itself for a local-tracker `BT-LOCAL-<slug>`."""
    return f"BT-{int(bt[3:]):03d}" if bt[3:].isdigit() else bt


def resolve_unit(id, milestone, parent, parent_milestone=None, epic=False):
    """Ship unit of a slice (or of an epic row with epic=True): {unit, kind, globs}. Pure; no I/O."""
    if not UNIT_ID_RE.fullmatch(id):
        raise ValueError(f"--slice must look like BT-<n> or BT-LOCAL-<slug>, got {id!r}")
    if parent is not None and parent.strip() not in NONE_TOKENS and not UNIT_ID_RE.fullmatch(parent):
        raise ValueError(f"--parent must look like BT-<n>, BT-LOCAL-<slug> or be none, got {parent!r}")
    own, inherited = _milestone(milestone, "--milestone"), _milestone(parent_milestone, "--parent-milestone")
    has_parent = parent is not None and parent.strip() not in NONE_TOKENS
    own_glob = f"*/{_unit_id(id)}-*"
    if epic and own:
        return {"unit": f"v{own[0]}.{own[1]}", "kind": "release", "globs": [own_glob, f"*/v{own[0]}.{own[1]}-*"]}
    if epic or not has_parent:
        return {"unit": _unit_id(id), "kind": "epic" if epic else "issue", "globs": [own_glob]}
    parent_glob = f"*/{_unit_id(parent)}-*"
    release = own or inherited
    if release:
        return {"unit": f"v{release[0]}.{release[1]}", "kind": "release", "globs": [parent_glob, f"*/v{release[0]}.{release[1]}-*"]}
    return {"unit": _unit_id(parent), "kind": "epic", "globs": [parent_glob], "needs_milestone": True}


def longer_id_globs(ids, known):
    """`*/<longer>-*` globs of known ids that extend one of ids with `-...`."""
    ids = [i for i in ids if i and i.strip() not in NONE_TOKENS]
    return [f"*/{k}-*" for k in known if any(k != i and k.startswith(i + "-") for i in ids)]


def ship_unit(bt, rows):
    """D1 ship-unit key (`vX.Y` or `BT-<padded>`) of row `bt`, or None when absent or unparseable."""
    r = rows.get(bt)
    if r is None:
        return None
    parent = norm(r.get('parent', '—'))
    prow = rows.get(parent) if parent else None
    try:
        return resolve_unit(bt, r.get('milestone'), parent, prow.get('milestone') if prow else None,
                            epic='tier:epic' in r.get('labels', ()))['unit']
    except ValueError:
        return None


# --- D3: blocker edges ----------------------------------------------------------------------------------------------

def effective_blockers(dep, rows):
    """Own `Blocked by` plus parent epic's, never dependent itself. Pure."""
    r = rows[dep]
    parent = norm(r.get('parent', '—'))
    prow = rows.get(parent) if parent else None
    return (set(r.get('blocked_by', ())) | set(prow.get('blocked_by', ()) if prow else ())) - {dep}


def _no_pr_state(bt):
    return None


def edge_verdict(dep, blk, rows, merged_of=_no_pr_state):
    """D3: (OK|UNMET|UNKNOWN, 'same-unit'|'cross-unit', reason) for edge dep <- blk."""
    b = rows.get(blk)
    if b is None:
        return 'UNKNOWN', 'cross-unit', 'blocker absent from the tracker'
    du, bu = ship_unit(dep, rows), ship_unit(blk, rows)
    if du is None or bu is None:
        return 'UNKNOWN', 'cross-unit', 'ship unit unknown (bad id or milestone)'
    status, shipped = b['status'], b['status'] in SHIPPED
    if du == bu:
        return ('OK' if shipped else 'UNMET'), 'same-unit', f"{du}, blocker {status}"
    if not norm(b.get('parent', '—')):
        return ('OK' if status == 'done' else 'UNMET'), 'cross-unit', f"{blk} is {status}, merged only when done"
    if not shipped:
        return 'UNMET', 'cross-unit', f"{blk} not shipped ({status})"
    m = merged_of(blk)
    if m == 'merged':
        return 'OK', 'cross-unit', f"{blk} PR merged"
    if m == 'none':
        return 'OK', 'cross-unit', f"{blk} has no PR (spike or manual close), no code to merge"
    if m == 'open':
        return 'UNMET', 'cross-unit', f"{blk} PR not merged"
    return 'UNKNOWN', 'cross-unit', f"{blk} PR state unknown (gh unavailable)"


# --- Graph & DAG operations -----------------------------------------------------------------------------------------

def topological_sort(graph):
    """Pure deterministic topological sort of a directed graph.
    graph: dict mapping node -> set/list of predecessor nodes.
    Returns (order, None) if acyclic, or (None, cycle_nodes) if cyclic.
    """
    clean_graph = {}
    for node, preds in graph.items():
        clean_graph.setdefault(node, set())
        for p in preds:
            clean_graph.setdefault(p, set())
            clean_graph[node].add(p)
    ts = graphlib.TopologicalSorter()
    for node in sorted(clean_graph.keys()):
        ts.add(node, *sorted(clean_graph[node]))
    try:
        return list(ts.static_order()), None
    except graphlib.CycleError as e:
        cycle = list(e.args[1]) if len(e.args) > 1 else []
        return None, cycle


def parse_edges(text: str):
    """Parse text containing dependency edges into a graph {node: set of predecessors}."""
    graph = {}
    for raw_line in text.splitlines():
        line = raw_line.split('#', 1)[0].strip()
        if not line:
            continue
        if ':blocked_by=' in line:
            target, blks = line.split(':blocked_by=', 1)
        elif '<-' in line:
            target, blks = line.split('<-', 1)
        elif '->' in line:
            preds, target = line.split('->', 1)
            target, blks = target, preds
        elif ':' in line:
            target, blks = line.split(':', 1)
        else:
            target, blks = line, ''
        target = target.strip()
        if target:
            graph.setdefault(target, set())
            for b in (x.strip() for x in blks.split(',') if x.strip()):
                graph[target].add(b)
                graph.setdefault(b, set())
    return graph


# --- Expectation parsing & drift comparison --------------------------------------------------------------------------

STATUS_RE = re.compile(r'^status:(.+)$')
ALL_FIELDS = ('status', 'milestone', 'labels', 'parent', 'blocked_by')
EXPECT_FIELDS = ALL_FIELDS


def issue_number(bt):
    m = re.match(r'^BT-0*(\d+)$', bt)
    return m.group(1) if m else None


def _padded(token):
    m = re.fullmatch(r'BT-0*(\d+)', token.strip())
    return bt_id(m.group(1)) if m else token.strip()


def _canon_id(val):
    if val is None:
        return None
    if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
        return bt_id(val)
    return _padded(str(val))


def closed_on_github(row, gh):
    """Drift text when the issue is CLOSED on GitHub while its row is not done, else None. Pure."""
    if gh.get('state') == 'CLOSED' and row['status'] != 'done':
        return f"closed on GitHub, expect={row['status']}"
    return None


def open_on_github(row, gh):
    """Drift text when the issue is still OPEN on GitHub while its row is done, else None. Pure."""
    if gh.get('state') == 'OPEN' and row['status'] == 'done':
        return "open on GitHub, expect=done"
    return None


def compare(row, gh, fields, check_pr, local=False):
    """Return a list of drift descriptions for one issue. Pure — unit-tested."""
    drift = []
    gh_labels = {l['name'] for l in gh.get('labels', [])}
    if 'status' in fields:
        gh_status = next((STATUS_RE.match(l).group(1) for l in gh_labels if STATUS_RE.match(l)), None)
        if gh_status != norm(row['status']):
            drift.append(f"status expect={row['status']} gh={gh_status}")
    if 'milestone' in fields:
        gh_ms = (gh.get('milestone') or {}).get('title')
        if gh_ms != norm(row['milestone']):
            drift.append(f"milestone expect={norm(row['milestone'])} gh={gh_ms}")
    if 'labels' in fields:
        gh_nonstatus = {l for l in gh_labels if not STATUS_RE.match(l)}
        want_labels = {l for l in row['labels'] if not STATUS_RE.match(l)}
        if want_labels != gh_nonstatus:
            drift.append(f"labels expect_only={sorted(want_labels - gh_nonstatus)} gh_only={sorted(gh_nonstatus - want_labels)}")
    if 'blocked_by' in fields and 'blockedBy' in gh:
        bb = gh.get('blockedBy') or []
        if isinstance(bb, dict):
            bb = bb.get('nodes') or []
        gh_bb = {_canon_id(i.get('number')) for i in bb}
        if row['blocked_by'] != gh_bb:
            drift.append(f"blocked_by expect={sorted(row['blocked_by'])} gh={sorted(gh_bb)}")
    if 'parent' in fields and 'parent' in gh:
        p = gh.get('parent')
        gh_parent = _canon_id(p.get('number')) if p else None
        if gh_parent != norm(row['parent']):
            drift.append(f"parent expect={norm(row['parent'])} gh={gh_parent}")
    if check_pr:
        marks = ('/pull/', 'Shipped on ') if local else ('/pull/',)
        if not any(m in (c.get('body') or '') for c in (gh.get('comments') or []) for m in marks):
            drift.append("pr-link absent from issue comments")
    return drift


def parse_expect(text):
    """`BT-n:field=value` items split on `;` or newlines (`#` lines ignored) -> {BT-nnn: {field: value}}."""
    out = {}
    lines = (ln for ln in text.split('\n') if not ln.strip().startswith('#'))
    for item in (i.strip() for ln in lines for i in ln.split(';')):
        if not item:
            continue
        head, eq, value = item.partition('=')
        ident, colon, field = head.partition(':')
        field, value = field.strip(), value.strip()
        if value.lower() == 'none' and field in ('labels', 'blocked_by', 'milestone', 'parent'):
            value = '—' if field in ('milestone', 'parent') else ''
        if not (eq and colon and re.fullmatch(r'BT-(\d+|LOCAL-[\w-]+)', ident.strip())) or field not in EXPECT_FIELDS:
            raise ValueError(f"bad expectation {item!r}: want BT-<n>:<field>=<value> with field one of {', '.join(EXPECT_FIELDS)}")
        if field in ('labels', 'blocked_by'):
            vals = set(csv_list(value))
            value = {_padded(v) for v in vals} if field == 'blocked_by' else vals
        elif field == 'parent':
            value = _padded(value)
        out.setdefault(_padded(ident), {})[field] = value
    return out


# --- Local file frontmatter & tracker switch rewrites ----------------------------------------------------------------

LOCAL_ID = re.compile(r'BT-LOCAL-[A-Za-z0-9_-]*[A-Za-z0-9_]')
REWRITE_ROOTS = ('.memory', 'docs')
SKIP_DIRS = {'.git', '.tmp', 'node_modules', '.agents', '.claude', 'dist', '__pycache__'}


def real_number(bt):
    m = re.match(r'^BT-0*(\d+)$', bt)
    return int(m.group(1)) if m else None


def padded(number):
    return f"BT-{number:03d}"


def read_tracker(path):
    """`tracker:` value in the frontmatter of ARCHITECTURE.md, None when the file or the key is absent."""
    try:
        text = Path(path).read_text(encoding='utf-8-sig')
    except OSError:
        return None
    m = re.search(r'^tracker:\s*(\S+)\s*$', text.split('---', 2)[1] if text.startswith('---') else '', re.M)
    return m.group(1).strip('"\'') if m else None


def write_tracker(path, value):
    """Set `tracker: <value>` in the frontmatter of `path`, keeping its line endings."""
    return write_key(path, 'tracker', value)


def write_key(path, key, value):
    """Set `<key>: <value>` in the frontmatter of `path`."""
    text = Path(path).read_bytes().decode('utf-8-sig')
    eol = '\r\n' if '\r\n' in text else '\n'
    m = re.match(r'---\r?\n(.*?\r?\n)?---(?=\r?\n|$)', text, re.S)
    if not m:
        raise ValueError(f"{path} has no frontmatter to hold `{key}:`")
    head = m.group(1) or ''
    line = f"{key}: {value}"
    if re.search(rf'^{re.escape(key)}:.*$', head, re.M):
        new_head = re.sub(rf'^{re.escape(key)}:.*?(?=\r?$)', lambda _: line, head, count=1, flags=re.M)
    else:
        new_head = head + line + eol
    if new_head == head:
        return False
    out = '---' + eol + new_head + text[m.end() - 3:]
    Path(path).write_bytes(out.encode('utf-8'))
    return True


def rewrite_ids(text, numbers):
    """`BT-LOCAL-x` -> `BT-<padded>` for every id with a number; others stay."""
    return LOCAL_ID.sub(lambda m: padded(numbers[m.group(0)]) if numbers.get(m.group(0)) else m.group(0), text)


def text_files(root, skip_roots=()):
    for p in sorted(Path(root).rglob('*')):
        rel = p.relative_to(root)
        if p.is_file() and not SKIP_DIRS & set(rel.parts) and not any(rel.as_posix().startswith(s + '/') for s in skip_roots):
            try:
                yield p, p.read_bytes().decode('utf-8')
            except (UnicodeDecodeError, OSError):
                continue


def pending_rewrites(numbers):
    """(path, new text) for every file under REWRITE_ROOTS that holds a mapped id."""
    for top in REWRITE_ROOTS:
        for p, text in text_files(top) if Path(top).is_dir() else ():
            if p.as_posix().startswith('.memory/archive/'):
                continue
            new = rewrite_ids(text, numbers)
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
