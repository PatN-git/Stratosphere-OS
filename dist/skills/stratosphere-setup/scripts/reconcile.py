#!/usr/bin/env python3
"""reconcile.py — Terminal Sync Invariant gate (never writes GitHub; `--heal` writes BACKLOG_MAP only).

Assert that GitHub issue state matches the `.memory/BACKLOG_MAP.md` mirror for the
given BT ids, at the end of a workflow's Publish/Commit & Sync phase. Exit non-zero
on drift so the calling workflow HALTS before closing/shipping; heal + re-run.

Each caller passes `--fields` = only the mirror fields it wrote, so a gate never
false-blocks on drift in a field outside its concern. `--pr-id` scopes the PR-link
check to the single issue that received the PR comment (e.g. the shipped slice),
so co-passed ids (cleared dependents, a flipped epic) are not required to carry it.
With `status` in `--fields` the gate also checks issue state: closed must match done (a done row still open, or a closed issue not done, is drift).

Offline / no `gh` -> internal-consistency check only, exit 0 (`[local-only]`).
Contract + heal protocol: .agents/skills/4a-verify-and-ship/references/terminal-sync-invariant.md

Usage:
  python .agents/scripts/reconcile.py --ids BT-007[,BT-006,BT-005] \
      [--pr-id BT-007] [--fields status,blocked_by]
  python .agents/scripts/reconcile.py --all-open --summary [--out .tmp/nightly-drift.txt] \
      [--keys-out .tmp/nightly-drift-keys.txt] [--state docs/nightly/.last-run.json]
  python .agents/scripts/reconcile.py --heal --kind labels --source gh|map (--ids BT-007[,…] | --all-open)
  python .agents/scripts/reconcile.py --edges blockers|dependents (--ids BT-007[,…] | --all-open)

--heal (0d, approved heals): one drift kind per run. `--source gh` upserts that kind's BACKLOG_MAP cell
from GitHub, keyed by BT row (never appends a row, touches no other cell), atomic write, prints each
`[HEALED <kind> BT-n]`. `--source map` (the map is right, GitHub is wrong) writes nothing: it PRINTS the exact
`gh` / GraphQL commands (references/github-issue-relations.md) for the agent to run after the user approves.
Kinds: status, milestone, labels, parent, blocked_by. Not healable here: stale_blocker (both sides, a
workflow decision), closed (flips a row to done: a lifecycle call), pr_link (a GitHub comment, no map cell),
absent / not_found (a row would have to be appended or deleted). Re-run `--ids <healed> --fields <kind>` once. A blocked_by edge that `--edges` marks CLEAR is
skipped (`[HEAL-SKIP … stale on GitHub]`, use --source map): the map already cleared it.

--edges (read-only decision list; D3 blocker predicate): `blockers` prints each effective blocker (own + parent epic's)
of the ids as `[BLOCKER-OK|BLOCKER-UNMET|BLOCKER-UNKNOWN D <- B] same-unit|cross-unit: reason` (exit 1 unless all OK);
`dependents` prints each stored edge naming the ids as `[CLEAR D <- B]` + its `removeBlockedBy` cmd, or `[KEEP D <- B]`.
Same ship unit (pr_body.resolve_unit) -> blocker shipped; else its code must be on the default branch (PR merged).

--summary (0d): counts per drift kind, new items verbatim, carried items one line per kind with ages
(`[CHRONIC n]` from night 3). Ages come from nightly_state.py's drift map, read-only here. The only
files it writes are the scratch files named by --out / --keys-out (never the mirror, GitHub or state).
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

STATE_DEFAULT = 'docs/nightly/.last-run.json'  # nightly_state.STATE; imported lazily so the gate never depends on it


def _nightly_state():
    """Lazy import: only --summary needs nightly_state.py (drift history, date check)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import nightly_state
    return nightly_state

STATUS_RE = re.compile(r'^status:(.+)$')
NONE_TOKENS = {'', '-', '—'}
ALL_FIELDS = ('status', 'milestone', 'labels', 'parent', 'blocked_by')
SHIPPED = ('in review', 'done')  # a same-ship-unit blocker in one of these satisfies its edge (D3)


def _bt(n):
    return f"BT-{int(n):03d}"


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


def parse_backlog(path):
    """Parse 9-col BACKLOG_MAP rows into {BT-id: {fields}}. Pure (reads one file)."""
    rows = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        hit = _row_cells(line)
        if not hit:
            continue
        bt, raw = hit
        parts = [p.strip() for p in raw]
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


def open_ids(rows):
    """BT ids of every row whose status is not `done`, in map order. Pure."""
    return [bt for bt, r in rows.items() if r['status'] != 'done']


def _pr_body():
    """Lazy import: only the D3 edge verdict needs pr_body.py (the single D1 ship-unit implementation)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pr_body
    return pr_body


def ship_unit(bt, rows):
    """D1 ship-unit key (`vX.Y` or `BT-<padded>`) of row `bt`, or None when the row is absent or its
    id/milestone/parent is unparseable (the edge is then UNKNOWN, never a crash). Pure."""
    r = rows.get(bt)
    if r is None:
        return None
    parent = _norm(r.get('parent', '—'))
    prow = rows.get(parent) if parent else None
    try:
        return _pr_body().resolve_unit(bt, r.get('milestone'), parent, prow.get('milestone') if prow else None,
                                       epic='tier:epic' in r.get('labels', ()))['unit']
    except ValueError:
        return None


def effective_blockers(dep, rows):
    """Own `Blocked by` plus the parent epic's, never the dependent itself. Pure."""
    r = rows[dep]
    parent = _norm(r.get('parent', '—'))
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
        return 'UNKNOWN', 'cross-unit', 'blocker row absent from BACKLOG_MAP'
    du, bu = ship_unit(dep, rows), ship_unit(blk, rows)
    if du is None or bu is None:
        return 'UNKNOWN', 'cross-unit', 'ship unit unknown (bad id or milestone)'
    status, shipped = b['status'], b['status'] in SHIPPED
    if du == bu:
        return ('OK' if shipped else 'UNMET'), 'same-unit', f"{du}, blocker {status}"
    if not _norm(b.get('parent', '—')):  # epic or standalone: closed <=> merged <=> done; `in review` = PR still open
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


def stale_blockers(rows, merged_of=_no_pr_state):
    """`BT-x: stale blocker BT-y should be cleared` for each open row with a stored edge the D3 predicate
    marks OK (4a/merge should have removed it); a kept or unverifiable edge is never flagged. BACKLOG-only. Pure."""
    out = []
    for bt in open_ids(rows):
        for blocker in sorted(rows[bt]['blocked_by']):
            if edge_verdict(bt, blocker, rows, merged_of)[0] == 'OK':
                out.append(f"{bt}: stale blocker {blocker} should be cleared")
    return out


def closed_on_github(row, gh):
    """Drift text when the issue is CLOSED on GitHub while its row is not done, else None.
    Per-field compare cannot see this (the labels still say `in review`). Pure."""
    if gh.get('state') == 'CLOSED' and row['status'] != 'done':
        return f"closed on GitHub, map={row['status']}"
    return None


def open_on_github(row, gh):
    """Drift text when the issue is still OPEN on GitHub while its row is done (a dropped `gh issue close`
    at ship), else None. Pure."""
    if gh.get('state') == 'OPEN' and row['status'] == 'done':
        return "open on GitHub, map=done"
    return None


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
        # status:* is compared under `status`; strip it on both sides.
        gh_nonstatus = {l for l in gh_labels if not STATUS_RE.match(l)}
        map_labels = {l for l in row['labels'] if not STATUS_RE.match(l)}
        if map_labels != gh_nonstatus:
            drift.append(f"labels map_only={sorted(map_labels - gh_nonstatus)} "
                         f"gh_only={sorted(gh_nonstatus - map_labels)}")

    if 'blocked_by' in fields and 'blockedBy' in gh:
        # Real gh returns a connection {"nodes": [...], "totalCount": n} (not paginated
        # past its first page here); a flat list and None are tolerated.
        bb = gh.get('blockedBy') or []
        if isinstance(bb, dict):
            bb = bb.get('nodes') or []
        gh_bb = {_bt(i['number']) for i in bb}
        if row['blocked_by'] != gh_bb:
            drift.append(f"blocked_by map={sorted(row['blocked_by'])} gh={sorted(gh_bb)}")

    if 'parent' in fields and 'parent' in gh:
        p = gh.get('parent')
        gh_parent = _bt(p['number']) if p else None
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


def fetch_issue(num, want_comments, want_state=False):
    """Core fields first; optional (blockedBy/parent) fetched separately so an
    unsupported field degrades to 'not checked' instead of failing the whole read."""
    core = ['number', 'labels', 'milestone']
    if want_comments:
        core.append('comments')
    if want_state:
        core.append('state')
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


def _pr_state(k):
    """`gh pr view <k>` state (MERGED|OPEN|CLOSED), None on any gh failure."""
    try:
        r = subprocess.run(['gh', 'pr', 'view', k, '--json', 'state'], capture_output=True, text=True)
        return json.loads(r.stdout).get('state') if r.returncode == 0 else None
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        return None


def pr_merge_state(bt, cache=None):
    """'merged' | 'open' | 'none' | None for a child slice's `Shipped in PR` PR: the last `/pull/<k>` comment wins
    (a re-shipped slice has the newest PR last); OPEN and unmerged CLOSED -> 'open'; no such comment -> 'none';
    gh failure, no gh or no GitHub issue -> None. `cache` (a dict) memoizes per run."""
    if cache is not None and bt in cache:
        return cache[bt]
    num, out = issue_number(bt), None
    data = _gh_json(num, ['comments']) if num else None
    if data is not None:
        links = [m.group(1) for c in data.get('comments') or [] if (m := re.search(r'/pull/(\d+)', c.get('body') or ''))]
        if not links:
            out = 'none'
        else:
            out = {'MERGED': 'merged', 'OPEN': 'open', 'CLOSED': 'open'}.get(_pr_state(links[-1]))
    if cache is not None:
        cache[bt] = out
    return out


def make_merged_of():
    """A per-run `merged_of(bt)` over pr_merge_state: gh_available is probed (and a PR looked up) only when an
    edge needs it, once per blocker; offline -> None (unknown)."""
    cache, online = {}, []

    def merged_of(bt):
        if bt not in cache:
            if not online:
                online.append(gh_available())
            cache[bt] = pr_merge_state(bt) if online[0] else None
        return cache[bt]
    return merged_of


# Texts from compare()/closed_on_github(); stale/absent/not_found items are built with their kind directly.
KIND_PREFIXES = (('closed on GitHub', 'closed'), ('open on GitHub', 'closed'), ('status', 'status'),
                 ('milestone', 'milestone'), ('labels', 'labels'), ('blocked_by', 'blocked_by'),
                 ('parent', 'parent'), ('pr-link', 'pr_link'))
CHRONIC_NIGHTS = 3


def drift_kind(text):
    """Kind of one drift description (the text after `BT-x: `). Pure."""
    return next((k for p, k in KIND_PREFIXES if text.startswith(p)), 'other')


def classify(items, history, today):
    """[(bt, kind, line, age)]: age 1 = new tonight; >1 = carried. `nights` counts nights already
    recorded, so tonight adds one unless nightly_state already recorded tonight. Pure."""
    out = []
    for bt, kind, line in items:
        e = history.get(f"{bt}|{kind}")
        if e is None or e['first'] == today:
            age = 1
        else:
            age = e['nights'] if e['last'] == today else e['nights'] + 1
        out.append((bt, kind, line, age))
    return out


def summarize(items, history, today):
    """Summary lines: count per kind, new items verbatim, carried items one line per kind with ages
    (`[CHRONIC n]` from night 3). Pure."""
    rows = classify(items, history, today)
    new = [r for r in rows if r[3] == 1]
    lines = [f"[DRIFT-SUMMARY {len(rows)} items: {len(new)} new, {len(rows) - len(new)} carried]"]
    kinds = {}
    for r in rows:
        kinds[r[1]] = kinds.get(r[1], 0) + 1
    lines.append("kinds: " + " · ".join(f"{k} {n}" for k, n in sorted(kinds.items())))
    if new:
        lines.append("new:")
        lines += [r[2] for r in new]
    for kind in sorted(kinds):
        carried = [r for r in rows if r[1] == kind and r[3] > 1]
        if not carried:
            continue
        ages = {}
        for r in carried:
            ages.setdefault(r[3], set()).add(r[0])
        parts = [f"night {a}: {' '.join(sorted(ids))}" + (f" [CHRONIC {a}]" if a >= CHRONIC_NIGHTS else "")
                 for a, ids in sorted(ages.items())]
        lines.append(f"carried {kind} {len(carried)}: " + " · ".join(parts))
    return lines


HEAL_KINDS = ('status', 'milestone', 'labels', 'parent', 'blocked_by')
HEAL_CELL = {'status': 3, 'labels': 4, 'milestone': 5, 'parent': 6, 'blocked_by': 7}  # index in the `|`-split row


def _gh_state(kind, gh):
    """What GitHub says for one kind: status/milestone/parent -> str|None; labels/blocked_by -> set. Pure."""
    labels = {l['name'] for l in gh.get('labels', [])}
    if kind == 'status':
        return next((STATUS_RE.match(l).group(1) for l in labels if STATUS_RE.match(l)), None)
    if kind == 'milestone':
        return (gh.get('milestone') or {}).get('title')
    if kind == 'labels':
        return {l for l in labels if not STATUS_RE.match(l)}
    if kind == 'parent':
        p = gh.get('parent')
        return _bt(p['number']) if p else None
    bb = gh.get('blockedBy') or []
    if isinstance(bb, dict):
        bb = bb.get('nodes') or []
    return {_bt(i['number']) for i in bb}


def _cell_text(kind, row, value):
    """BACKLOG_MAP cell text for `value`. Labels keep the map's own status:* tokens (compared under status). Pure."""
    if kind == 'labels':
        value = value | {l for l in row['labels'] if STATUS_RE.match(l)}
    if isinstance(value, set):
        return ', '.join(sorted(value)) or '—'
    return value or '—'


def _map_text(kind, row):
    v = row[kind]
    return (', '.join(sorted(v)) or '—') if isinstance(v, set) else (_norm(v) or '—')


def _graphql(mutation, second, a, b):
    """references/github-issue-relations.md mutation over issue numbers a (issueId) and b (`second`)."""
    def node(n):
        return f'"$(gh issue view {n} --json id -q .id)"'
    return (f"gh api graphql -f query='mutation($i:ID!,$j:ID!){{{mutation}(input:{{issueId:$i,{second}:$j}})"
            f"{{issue{{number}}}}}}' -f i={node(a)} -f j={node(b)}")


def _edge(mutation, second, a, b):
    """A relation mutation over two issues given as numbers or BT ids; a BT-LOCAL id has no GitHub issue."""
    nums = [(x, x if x.isdigit() else issue_number(x)) for x in (a, b)]
    gone = next((x for x, n in nums if n is None), None)
    return f"# skip {gone}: no GitHub issue" if gone else _graphql(mutation, second, nums[0][1], nums[1][1])


def gh_fix_commands(kind, num, row, gh):
    """`gh` / GraphQL commands that make GitHub match the map row (map -> GitHub). Printed, never run. Pure."""
    cmds, now = [], _gh_state(kind, gh)
    if kind == 'status':
        want = _norm(row['status'])
        rm = f' --remove-label "status:{now}"' if now else ''
        cmds.append(f'gh issue edit {num}{rm} --add-label "status:{want}"' if want else f'gh issue edit {num}{rm}')
    elif kind == 'milestone':
        want = _norm(row['milestone'])
        cmds.append(f'gh issue edit {num} --milestone "{want}"' if want else f'gh issue edit {num} --remove-milestone')
    elif kind == 'labels':
        want = {l for l in row['labels'] if not STATUS_RE.match(l)}
        flags = [f'--add-label "{l}"' for l in sorted(want - now)] + [f'--remove-label "{l}"' for l in sorted(now - want)]
        cmds.append(f'gh issue edit {num} ' + ' '.join(flags))
    elif kind == 'parent':
        want = _norm(row['parent'])
        if now:
            cmds.append(_edge('removeSubIssue', 'subIssueId', now, num))
        if want:
            cmds.append(_edge('addSubIssue', 'subIssueId', want, num))
    else:  # blocked_by
        for b in sorted(row['blocked_by'] - now):
            cmds.append(_edge('addBlockedBy', 'blockingIssueId', num, b))
        for b in sorted(now - row['blocked_by']):
            cmds.append(_edge('removeBlockedBy', 'blockingIssueId', num, b))
    return cmds


def upsert_cells(text, edits):
    """Rewrite only the named cells of the existing BT rows in BACKLOG_MAP `text`: {bt: {kind: cell text}}.
    Never appends a row; every other cell and every line ending is preserved. Edits every duplicate row of a
    BT id (parse_backlog keeps the last one), so a duplicate cannot stay stale. Returns the new text. Pure."""
    out = []
    for line in text.splitlines(keepends=True):
        hit = _row_cells(line)
        if hit and hit[0] in edits:
            body = line.rstrip('\r\n')
            raw = body.split('|')
            for kind, value in edits[hit[0]].items():
                raw[HEAL_CELL[kind]] = f' {value} '
            line = '|'.join(raw) + line[len(body):]
        out.append(line)
    return ''.join(out)


def heal(args, rows, ids, merged_of=_no_pr_state):
    """--heal: upsert one kind's map cells from GitHub (--source gh), or print the gh fix commands
    (--source map). Writes BACKLOG_MAP only, never GitHub. Returns the exit code (1 = some id skipped)."""
    kind, plan, cmds = args.kind, {}, []
    synced = skipped = local = 0
    for bt in ids:
        num = issue_number(bt)
        if bt in rows and not num:
            local += 1  # BT-LOCAL: no GitHub side, nothing to heal and nothing wrong
            continue
        if bt not in rows:
            print(f"[HEAL-SKIP {bt}: absent from BACKLOG_MAP; rows are never appended]")
            skipped += 1
            continue
        gh = fetch_issue(num, want_comments=False)
        if gh is None:
            print(f"[HEAL-SKIP {bt}: gh issue #{num} not found]")
            skipped += 1
            continue
        if not compare(rows[bt], gh, {kind}, check_pr=False):
            synced += 1
            continue
        if args.source == 'map':
            cmds.append((bt, gh_fix_commands(kind, num, rows[bt], gh)))
            continue
        value = _gh_state(kind, gh)
        if kind == 'status' and value is None:
            print(f"[HEAL-SKIP {bt}: GitHub has no status:* label; fix it there with --source map]")
            skipped += 1
            continue
        if kind == 'blocked_by':
            stale = {b for b in value - rows[bt]['blocked_by'] if edge_verdict(bt, b, rows, merged_of)[0] == 'OK'}
            if stale:  # a blocker the map already cleared: healing from GitHub would undo that
                print(f"[HEAL-SKIP {bt} blocked_by: stale on GitHub; use --source map]")
                skipped += 1
                value -= stale
                if value == rows[bt]['blocked_by']:
                    continue
        plan[bt] = {kind: _cell_text(kind, rows[bt], value)}
        print(f"[HEALED {kind} {bt}] {_map_text(kind, rows[bt])} -> {plan[bt][kind]}")
    if args.source == 'map':
        for bt, lines in cmds:
            print(f"# {bt} {kind}: make GitHub match the map")
            print("\n".join(lines))
        print(f"[HEAL-PLAN {kind}: {len(cmds)} issues need GitHub edits, {synced} in sync, {local} local, {skipped} skipped; "
              f"nothing run or written. Run the commands only after the user approves.]")
        return 1 if skipped else 0
    if plan:
        path = Path(args.backlog)
        tmp = path.with_name(path.name + '.tmp')  # write aside, then swap: a crash never half-writes the map
        try:
            tmp.write_bytes(upsert_cells(path.read_bytes().decode('utf-8'), plan).encode('utf-8'))
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)
    print(f"[HEAL-DONE {kind} from gh: {len(plan)} healed, {synced} in sync, {local} local, {skipped} skipped; "
          f"BACKLOG_MAP only, GitHub untouched. Re-run reconcile.py --ids <healed> --fields {kind} once.]")
    return 1 if skipped else 0


def edges_cmd(args, rows, ids, merged_of):
    """--edges: print one D3 verdict line per edge. Decides only, never writes. Returns the exit code."""
    code = 0
    for bt in (i for i in ids if i not in rows):
        print(f"[EDGES-ABSENT {bt}: absent from BACKLOG_MAP]")
        code = 1
    ids = [i for i in ids if i in rows]
    if args.edges == 'blockers':
        for dep in ids:
            blockers = sorted(effective_blockers(dep, rows))
            if not blockers:
                print(f"[BLOCKERS-NONE {dep}]")
            for blk in blockers:
                verdict, scope, why = edge_verdict(dep, blk, rows, merged_of)
                print(f"[BLOCKER-{verdict} {dep} <- {blk}] {scope}: {why}")
                if verdict != 'OK':
                    code = 1
        return code
    # dependents: stored edges on open rows, either all of them (--all-open) or those naming one of the ids
    for dep in open_ids(rows):
        for blk in sorted(rows[dep]['blocked_by']):
            if not args.all_open and blk not in ids:
                continue
            verdict, scope, why = edge_verdict(dep, blk, rows, merged_of)
            if verdict == 'OK':
                print(f"[CLEAR {dep} <- {blk}] {scope}: {why}")
                print(f"  cmd: {_edge('removeBlockedBy', 'blockingIssueId', dep, blk)}")
            else:
                print(f"[KEEP {dep} <- {blk}] {scope}: {why}")
    return code


def main(argv=None):
    ap = argparse.ArgumentParser(description="Terminal Sync Invariant gate.")
    scope = ap.add_mutually_exclusive_group(required=True)
    scope.add_argument('--ids', help="comma-separated BT ids, e.g. BT-007,BT-006")
    scope.add_argument('--all-open', action='store_true',
                       help="advisory sweep of every row whose status is not done, plus the "
                            "stale-blocker and closed-on-GitHub checks (0d; ~3 gh calls per row)")
    ap.add_argument('--pr-id', help="the id that must carry a PR-link comment (e.g. the shipped slice)")
    ap.add_argument('--fields', default=None,
                    help="mirror fields to check (default: all). Pass only the fields this phase wrote.")
    ap.add_argument('--backlog', default='.memory/BACKLOG_MAP.md')
    ap.add_argument('--require-gh', action='store_true',
                    help="terminal gates pass this: refuse to report success when GitHub "
                         "cannot be reached, instead of silently not verifying")
    ap.add_argument('--summary', action='store_true',
                    help="with --all-open: print a count per drift kind, new items verbatim and carried "
                         "items one line per kind with ages ([CHRONIC n] from night 3) instead of every line")
    ap.add_argument('--out', help="with --summary: write every raw drift line to this file")
    ap.add_argument('--keys-out', help="with --summary: write tonight's `BT-x|kind` keys (input of "
                                       "nightly_state.py drift); not written when gh is unavailable")
    ap.add_argument('--state', default=STATE_DEFAULT,
                    help="with --summary: nightly_state's file, read-only, for carried ages")
    ap.add_argument('--date', default=None, help="with --summary: tonight, YYYY-MM-DD (default: today)")
    ap.add_argument('--heal', action='store_true',
                    help="heal ONE drift kind for the --ids / --all-open scope; needs --kind and --source. "
                         "Writes BACKLOG_MAP only, never GitHub")
    ap.add_argument('--kind', choices=HEAL_KINDS, help="with --heal: the drift kind to heal")
    ap.add_argument('--source', choices=('gh', 'map'),
                    help="with --heal: gh = upsert the map cell from GitHub; map = print the gh/GraphQL "
                         "commands that make GitHub match the map (nothing is run)")
    ap.add_argument('--edges', choices=('blockers', 'dependents'),
                    help="D3 blocker verdicts for the --ids / --all-open scope, read-only: blockers = each effective "
                         "blocker of the ids; dependents = each stored edge naming the ids (CLEAR or KEEP)")
    args = ap.parse_args(argv)
    if args.edges and (args.heal or args.summary or args.pr_id or args.fields is not None):
        ap.error("--edges is a separate run: not with --heal/--summary/--pr-id/--fields")
    args.fields = args.fields or ','.join(ALL_FIELDS)
    if args.heal:
        if not (args.kind and args.source):
            ap.error("--heal needs --kind and --source (one drift kind per run) plus --ids or --all-open")
        if args.summary:
            ap.error("--heal and --summary are separate runs")
    elif args.kind or args.source:
        ap.error("--kind/--source need --heal")
    if (args.summary or args.out or args.keys_out) and not (args.all_open and args.summary):
        ap.error("--out/--keys-out need --summary, and --summary needs --all-open")
    if args.date is not None:
        try:
            args.date = _nightly_state().valid_date(args.date)
        except (argparse.ArgumentTypeError, ValueError) as e:
            ap.error(f"--date: {e}")

    fields = {f.strip() for f in args.fields.split(',') if f.strip()}
    rows = parse_backlog(args.backlog)
    ids = open_ids(rows) if args.all_open else [i.strip() for i in args.ids.split(',') if i.strip()]
    merged_of = make_merged_of()
    if args.edges:
        return edges_cmd(args, rows, ids, merged_of)
    if args.heal:
        if not gh_available():
            print("[HEAL-UNAVAILABLE: gh unavailable, nothing to heal from; nothing written]")
            return 3
        return heal(args, rows, ids, merged_of)
    # (bt, kind, text); bt None = informational note. Non-summary prints them in order; summary groups the items.
    emit = [(d.split(':')[0], 'stale_blocker', f"[MIRROR-DRIFT {d}]")
            for d in (stale_blockers(rows, merged_of) if args.all_open else [])]

    def finish(code, gh_checked, ok_line=None):
        items = [(bt, k, t) for bt, k, t in emit if bt]
        if not args.summary:
            for _, _, t in emit:
                print(t)
            if ok_line and not items:
                print(ok_line)
            return code
        if not gh_checked:
            print("[local-only — GitHub not checked]")
        if not items:
            if ok_line:
                print(ok_line)
        else:
            today = args.date or datetime.date.today().isoformat()
            print("\n".join(summarize(items, _nightly_state().load(args.state)['drift'], today)))
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text("".join(t + "\n" for _, _, t in items), encoding='utf-8')
        if args.keys_out:
            keys = Path(args.keys_out)
            if gh_checked:
                keys.parent.mkdir(parents=True, exist_ok=True)
                keys.write_text("".join(f"{k}\n" for k in sorted({f"{bt}|{kind}" for bt, kind, _ in items})),
                                encoding='utf-8')
            elif keys.exists():
                keys.unlink()  # a partial (offline) key set must never reach nightly_state.py
        return code

    if not gh_available():
        # A terminal gate must not pass on an unverified mirror. Without
        # --require-gh this stays exit 0 so local dev runs are unaffected.
        if args.require_gh:
            print("[MIRROR-UNVERIFIED: gh unavailable — terminal invariant NOT checked]")
            return 3
        if not args.summary:
            print("[local-only — GitHub not checked]")
        missing = [i for i in ids if i not in rows]
        if missing:
            emit.append((None, 'absent', f"[MIRROR-DRIFT: ids absent from BACKLOG_MAP: {missing}]"))
        return finish(1 if missing or emit else 0, gh_checked=False)

    exit_code = 1 if emit else 0
    checked = not_found = 0
    for bt in ids:
        if bt not in rows:
            emit.append((bt, 'absent', f"[MIRROR-DRIFT {bt}: absent from BACKLOG_MAP]"))
            exit_code = 1
            continue
        if bt.startswith('BT-LOCAL'):
            emit.append((None, None, f"[local-only {bt} — no GitHub issue to check]"))
            continue
        checked += 1
        num = issue_number(bt)
        is_pr = (bt == args.pr_id)
        if not num:
            gh = None
        elif args.all_open:
            gh = fetch_issue(num, want_comments=False, want_state=True)
        else:
            gh = fetch_issue(num, want_comments=is_pr, want_state='status' in fields)
        if gh is None:
            not_found += 1
            emit.append((bt, 'not_found', f"[MIRROR-DRIFT {bt}: gh issue #{num} not found]"))
            exit_code = 1
            continue
        closed = ((closed_on_github(rows[bt], gh) or open_on_github(rows[bt], gh))
                  if (args.all_open or 'status' in fields) else None)
        # A closed issue's other fields are noise: the row itself is what needs healing.
        drift = [closed] if closed else compare(rows[bt], gh, fields, check_pr=is_pr)
        for d in drift:
            emit.append((bt, drift_kind(d), f"[MIRROR-DRIFT {bt}: {d}]"))
        if drift:
            exit_code = 1

    if args.summary and checked and checked == not_found:
        # Every fetch failed: gh is flaky or unauthenticated, not 74 deleted issues. Treat as unavailable so no
        # false drift reaches the report and a partial key set never resets ages in nightly_state.
        emit = [e for e in emit if e[1] != 'not_found']
        return finish(1 if any(e[0] for e in emit) else 0, gh_checked=False)
    ok_line = f"[MIRROR-OK {len(ids)} open rows]" if args.all_open else f"[MIRROR-OK {','.join(ids)}]"
    return finish(exit_code, gh_checked=True, ok_line=ok_line)


if __name__ == '__main__':
    sys.exit(main())
