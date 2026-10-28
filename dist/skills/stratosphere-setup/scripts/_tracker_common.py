#!/usr/bin/env python3
"""_tracker_common.py — the pure tracker logic shared by issues.py, reconcile.py, pr_body.py and ice_read.py.

A leaf: it imports no sibling script and does no I/O, so every script (reconcile.py with only this file beside it
included) imports it at the top and none needs a lazy import to dodge a cycle. Owns the none tokens, the row shape,
the D1 ship-unit rule, the D3 blocker-edge verdicts and the 3c candidate list with its ICE score.
"""
import re

NONE_TOKENS = frozenset({'', '-', '—'})  # an empty value in a map cell, an argument or a row field
UNIT_ID_RE = re.compile(r'BT-(\d+|LOCAL-[a-z0-9-]+)')  # a GitHub number or a local-tracker id
MILESTONE_RE = re.compile(r'v(\d+)\.(\d+)\.(\d+)')
SHIPPED = ('in review', 'done')  # a same-ship-unit blocker in one of these satisfies its edge (D3)

EFFORT = {'small': 1, 'medium': 2, 'large': 3}
CANDIDATE_STATUS = ('planned', 'needs_spec')
REQUIRED = ('type:', 'mode:', 'tier:slice', 'size:')


def bt_id(n):
    return f"BT-{int(n):03d}"


def norm(token):
    return None if token in NONE_TOKENS else token


def csv_list(text):
    """The items of a comma list, none tokens dropped."""
    return [t.strip() for t in (text or '').split(',') if t.strip() not in NONE_TOKENS]


def make_row(status, labels, milestone, parent, blocked_by):
    """reconcile.py's row shape, which every tracker source (store, map file, GitHub node) builds."""
    return {'status': status, 'labels': set(labels), 'milestone': milestone or '—', 'parent': parent or '—',
            'blocked_by': set(blocked_by)}


def open_ids(rows):
    """BT ids of every row whose status is not `done`, in map order. Pure."""
    return [bt for bt, r in rows.items() if r['status'] != 'done']


# --- D1: the ship unit ----------------------------------------------------------------------------------------------

def _milestone(value, flag):
    """(X, Y) of a `vX.Y.Z` milestone, None for a none token (None, empty, `-`, `—`); ValueError otherwise."""
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
    """Ship unit of a slice (or of an epic row with epic=True): {unit, kind, globs}. ValueError on bad input.

    The only implementation of D1: a release `vX.Y` (own milestone, else the parent epic's), else the parent epic,
    else the issue itself (a standalone issue never joins a release). Globs are fnmatch patterns for branch names;
    the legacy own-epic glob comes first so a mid-flight per-epic branch keeps its epic. Pure; no I/O.
    """
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
    """`*/<longer>-*` globs of the `known` ids that extend one of `ids` with `-…`: the glob `*/BT-LOCAL-login-*` also
    matches a branch of `BT-LOCAL-login-form`, which belongs to that longer issue."""
    ids = [i for i in ids if i and i.strip() not in NONE_TOKENS]
    return [f"*/{k}-*" for k in known if any(k != i and k.startswith(i + "-") for i in ids)]


def ship_unit(bt, rows):
    """D1 ship-unit key (`vX.Y` or `BT-<padded>`) of row `bt`, or None when the row is absent or its
    id/milestone/parent is unparseable (the edge is then UNKNOWN, never a crash). Pure."""
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
    """Own `Blocked by` plus the parent epic's, never the dependent itself. Pure."""
    r = rows[dep]
    parent = norm(r.get('parent', '—'))
    prow = rows.get(parent) if parent else None
    return (set(r.get('blocked_by', ())) | set(prow.get('blocked_by', ()) if prow else ())) - {dep}


def _no_pr_state(bt):
    return None


def edge_verdict(dep, blk, rows, merged_of=_no_pr_state):
    """D3: (OK|UNMET|UNKNOWN, 'same-unit'|'cross-unit', reason) for the edge dep <- blk.
    Same ship unit -> OK once the blocker is shipped. Cross unit -> its code must be on the default branch:
    an epic/standalone blocker is merged <=> done; a child-slice blocker needs `merged_of(blk)`
    ('merged'|'open'|'none'|None) for its `Shipped in PR` PR. Pure given `merged_of`."""
    b = rows.get(blk)
    if b is None:
        return 'UNKNOWN', 'cross-unit', 'blocker absent from the tracker'
    du, bu = ship_unit(dep, rows), ship_unit(blk, rows)
    if du is None or bu is None:
        return 'UNKNOWN', 'cross-unit', 'ship unit unknown (bad id or milestone)'
    status, shipped = b['status'], b['status'] in SHIPPED
    if du == bu:
        return ('OK' if shipped else 'UNMET'), 'same-unit', f"{du}, blocker {status}"
    if not norm(b.get('parent', '—')):  # epic or standalone: closed <=> merged <=> done; `in review` = PR still open
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


# --- ICE on read and the 3c candidate list --------------------------------------------------------------------------

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
        bt = issue.get('id') or bt_id(issue['number'])
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
