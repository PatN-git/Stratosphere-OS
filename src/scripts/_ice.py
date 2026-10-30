#!/usr/bin/env python3
"""_ice.py — ICE on read and the 3c candidate list, shared by issues.py and ice_read.py.

A leaf like _tracker_common.py: stdlib plus that leaf, no I/O, no other sibling script. ICE = Impact * Confidence /
Effort, read from the body's metric lines and the `size:` label; nothing is stored.
"""
import re

from _tracker_common import bt_id

EFFORT = {'small': 1, 'medium': 2, 'large': 3}
CANDIDATE_STATUS = ('planned', 'needs_spec')
REQUIRED = ('type:', 'mode:', 'tier:slice', 'size:')


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
