#!/usr/bin/env python3
"""reconcile.py — Terminal Sync Invariant gate (never writes GitHub; `--heal` writes BACKLOG_MAP only).

Assert that GitHub issue state matches the `.memory/BACKLOG_MAP.md` mirror for the
given BT ids, at the end of a workflow's Publish/Commit & Sync phase. Exit non-zero
on drift so the calling workflow HALTS before closing/shipping; heal + re-run.

Each caller passes `--fields` = only the mirror fields it wrote, so a gate never
false-blocks on drift in a field outside its concern. `--pr-id` scopes the PR-link
check to the single issue that received the PR comment (e.g. the shipped slice),
so co-passed ids (cleared dependents, a flipped epic) are not required to carry it.

Offline / no `gh` -> internal-consistency check only, exit 0 (`[local-only]`).
Contract + heal protocol: .agents/skills/4a-verify-and-ship/references/terminal-sync-invariant.md

Usage:
  python .agents/scripts/reconcile.py --ids BT-007[,BT-006,BT-005] \
      [--pr-id BT-007] [--fields status,blocked_by]
  python .agents/scripts/reconcile.py --all-open --summary [--out .tmp/nightly-drift.txt] \
      [--keys-out .tmp/nightly-drift-keys.txt] [--state docs/nightly/.last-run.json]
  python .agents/scripts/reconcile.py --heal --kind labels --source gh|map (--ids BT-007[,…] | --all-open)

--heal (0d, approved heals): one drift kind per run. `--source gh` upserts that kind's BACKLOG_MAP cell
from GitHub, keyed by BT row (never appends a row, touches no other cell), atomic write, prints each
`[HEALED <kind> BT-n]`. `--source map` (the map is right, GitHub is wrong) writes nothing: it PRINTS the exact
`gh` / GraphQL commands (references/github-issue-relations.md) for the agent to run after the user approves.
Kinds: status, milestone, labels, parent, blocked_by. Not healable here: stale_blocker (both sides, a
workflow decision), closed (flips a row to done: a lifecycle call), pr_link (a GitHub comment, no map cell),
absent / not_found (a row would have to be appended or deleted). Re-run the sweep until it is clean.

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

STATUS_RE = re.compile(r'^status:(.+)$')
NONE_TOKENS = {'', '-', '—'}
ALL_FIELDS = ('status', 'milestone', 'labels', 'parent', 'blocked_by')


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


def stale_blockers(rows):
    """`BT-x: stale blocker BT-y should be cleared` for each open row blocked by a row that is
    already in review/done (4a/merge should have removed it). BACKLOG-only. Pure."""
    out = []
    for bt in open_ids(rows):
        for blocker in sorted(rows[bt]['blocked_by']):
            if blocker in rows and rows[blocker]['status'] in ('in review', 'done'):
                out.append(f"{bt}: stale blocker {blocker} should be cleared")
    return out


def closed_on_github(row, gh):
    """Drift text when the issue is CLOSED on GitHub while its row is not done, else None.
    Per-field compare cannot see this (the labels still say `in review`). Pure."""
    if gh.get('state') == 'CLOSED' and row['status'] != 'done':
        return f"closed on GitHub, map={row['status']}"
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
        gh_bb = {f"BT-{int(i['number']):03d}" for i in bb}
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


# Texts from compare()/closed_on_github(); stale/absent/not_found items are built with their kind directly.
KIND_PREFIXES = (('closed on GitHub', 'closed'), ('status', 'status'),
                 ('milestone', 'milestone'), ('labels', 'labels'), ('blocked_by', 'blocked_by'),
                 ('parent', 'parent'), ('pr-link', 'pr_link'))
CHRONIC_NIGHTS = 3
STATE_PATH = 'docs/nightly/.last-run.json'


def drift_kind(text):
    """Kind of one drift description (the text after `BT-x: `). Pure."""
    return next((k for p, k in KIND_PREFIXES if text.startswith(p)), 'other')


def load_drift_history(path):
    """{`BT-x|kind`: {first,last,nights}} from nightly_state's file; missing/old/malformed -> {}. Read-only."""
    try:
        raw = json.loads(Path(path).read_text(encoding='utf-8-sig')).get('drift')
    except (OSError, ValueError, AttributeError):
        return {}
    return {k: {'first': v['first'], 'last': v.get('last') or v['first'], 'nights': v['nights']}
            for k, v in (raw.items() if isinstance(raw, dict) else ())
            if isinstance(v, dict) and isinstance(v.get('nights'), int) and isinstance(v.get('first'), str)}


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
        return f"BT-{int(p['number']):03d}" if p else None
    bb = gh.get('blockedBy') or []
    if isinstance(bb, dict):
        bb = bb.get('nodes') or []
    return {f"BT-{int(i['number']):03d}" for i in bb}


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


def heal(args, rows, ids):
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
          f"BACKLOG_MAP only, GitHub untouched. Re-run reconcile.py until clean.]")
    return 1 if skipped else 0


def _valid_date(s):
    try:
        datetime.date.fromisoformat(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {s}")
    return s


def main(argv=None):
    ap = argparse.ArgumentParser(description="Terminal Sync Invariant gate.")
    scope = ap.add_mutually_exclusive_group(required=True)
    scope.add_argument('--ids', help="comma-separated BT ids, e.g. BT-007,BT-006")
    scope.add_argument('--all-open', action='store_true',
                       help="advisory sweep of every row whose status is not done, plus the "
                            "stale-blocker and closed-on-GitHub checks (0d; ~3 gh calls per row)")
    ap.add_argument('--pr-id', help="the id that must carry a PR-link comment (e.g. the shipped slice)")
    ap.add_argument('--fields', default=','.join(ALL_FIELDS),
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
    ap.add_argument('--state', default=STATE_PATH,
                    help="with --summary: nightly_state's file, read-only, for carried ages")
    ap.add_argument('--date', type=_valid_date, default=None, help="with --summary: tonight, YYYY-MM-DD (default: today)")
    ap.add_argument('--heal', action='store_true',
                    help="heal ONE drift kind for the --ids / --all-open scope; needs --kind and --source. "
                         "Writes BACKLOG_MAP only, never GitHub")
    ap.add_argument('--kind', choices=HEAL_KINDS, help="with --heal: the drift kind to heal")
    ap.add_argument('--source', choices=('gh', 'map'),
                    help="with --heal: gh = upsert the map cell from GitHub; map = print the gh/GraphQL "
                         "commands that make GitHub match the map (nothing is run)")
    args = ap.parse_args(argv)
    if args.heal:
        if not (args.kind and args.source):
            ap.error("--heal needs --kind and --source (one drift kind per run) plus --ids or --all-open")
        if args.summary:
            ap.error("--heal and --summary are separate runs")
    elif args.kind or args.source:
        ap.error("--kind/--source need --heal")
    if (args.summary or args.out or args.keys_out) and not (args.all_open and args.summary):
        ap.error("--out/--keys-out need --summary, and --summary needs --all-open")

    fields = {f.strip() for f in args.fields.split(',') if f.strip()}
    rows = parse_backlog(args.backlog)
    ids = open_ids(rows) if args.all_open else [i.strip() for i in args.ids.split(',') if i.strip()]
    if args.heal:
        if not gh_available():
            print("[HEAL-UNAVAILABLE: gh unavailable, nothing to heal from; nothing written]")
            return 3
        return heal(args, rows, ids)
    # (bt, kind, text); bt None = informational note. Non-summary prints them in order; summary groups the items.
    emit = [(d.split(':')[0], 'stale_blocker', f"[MIRROR-DRIFT {d}]")
            for d in (stale_blockers(rows) if args.all_open else [])]

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
            print("\n".join(summarize(items, load_drift_history(args.state), today)))
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
            gh = fetch_issue(num, want_comments=is_pr)
        if gh is None:
            not_found += 1
            emit.append((bt, 'not_found', f"[MIRROR-DRIFT {bt}: gh issue #{num} not found]"))
            exit_code = 1
            continue
        closed = closed_on_github(rows[bt], gh) if args.all_open else None
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
