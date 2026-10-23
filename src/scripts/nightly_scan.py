#!/usr/bin/env python3
"""nightly_scan.py — read-only session pre-pass for 0d Phase 1: tool calls and failures per session.

  nightly_scan.py [--since ISO] [--project PATH] [--json]
                  [--claude-root DIR] [--agy-root DIR] [--state FILE]

Scans the transcripts of BOTH hosts for sessions with activity since a watermark, scoped to one project:
  Claude Code  <claude-root>/<project slug>/*.jsonl   (default ~/.claude/projects; the slug is the project path
                with every non-alphanumeric character replaced by `-`; worktree folders `<slug>--claude-worktrees-*` count)
  Antigravity  <agy-root>/*/.system_generated/logs/transcript.jsonl   (default ~/.gemini/antigravity/brain;
                sessions are not keyed by project: one belongs here when a tool call's Cwd / AbsolutePath /
                TargetFile / Path is under --project; string args may be JSON-quoted, those keys are unquoted)
--since defaults to `last_run` in --state (default <project>/docs/nightly/.last-run.json, loaded read-only through
nightly_state.py), else 24 hours ago. A session is listed when it has records at or after the watermark; only
those records are counted. Its start is its first such record.

Claude Code subagent transcripts (<slug>/<session>/subagents/*.jsonl) are scanned too and listed as their own
`sub` lines named <session>/<agent file>; `tool-results/` folders are not transcripts and are ignored.

Prints, per host, sessions / tool calls / errors; per session id, start, calls, errors, repeats (most errors first,
which is 0d's sampling order; `repeats` = calls whose tool and command/target already appeared in the same session,
the redundant-call signal); per failing call the tool name and its command/target, whitespace-collapsed, secret-looking
values masked, cut at 120 chars. Claude: the tool_use whose tool_result has is_error. Antigravity: each call of a
step whose status is ERROR/INVALID or that carries `error` (a failing step counts once, however many calls it has);
a GENERIC step that fails without tool_calls is the error of the step just before it and lists that step's calls.
Closes with `skipped: N unparsable/unknown records`. The transcript formats are undocumented host internals, so an
unreadable record is counted, never fatal.

Never prints message text, thinking, tool output or any key name from a record: only the fixed fields above.
Writes nothing. Stdlib only.
"""
import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nightly_state  # noqa: E402  (read-only `load` for the watermark)

LIMIT = 120
MAX_SHOWN = 8  # failing calls listed per session in text mode (--json has all)
CLAUDE_TARGET_KEYS = ('command', 'file_path', 'path', 'notebook_path', 'pattern', 'url')
AGY_SCOPE_KEYS = ('Cwd', 'AbsolutePath', 'TargetFile', 'Path')
AGY_TARGET_KEYS = ('CommandLine', 'TargetFile', 'AbsolutePath', 'Path')
NAME_RE = re.compile(r'^[\w.:\-]{1,60}$')
MASKS = ((re.compile(r'\beyJ[\w-]+\.[\w-]+\.[\w-]+'), '***'),
         (re.compile(r'(?i)\bbearer\s+\S+'), 'Bearer ***'),
         (re.compile(r'(?i)(--[\w-]*(?:token|password|passwd|secret|api-?key)[\w-]*)[ =]\S+'), r'\1=***'),
         (re.compile(r'(?i)\b(\w*(?:token|secret|passw(?:or)?d|api[_-]?key|authorization)\w*)\s*[=:]\s*\S+'), r'\1=***'),
         (re.compile(r'\b(?:gh[pousr]_|sk-|xox[abp]-|AKIA)[A-Za-z0-9_\-]{8,}'), '***'))


def parse_ts(value):
    """Aware datetime from an ISO string or epoch seconds/milliseconds; naive means local time; else None."""
    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return datetime.datetime.fromtimestamp(value / 1000 if value > 1e11 else value, datetime.timezone.utc)
        if isinstance(value, str):
            dt = datetime.datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
            return dt if dt.tzinfo else dt.astimezone()
    except (ValueError, OverflowError, OSError):
        pass
    return None


def fmt(dt):
    return dt.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if dt else '-'


def claude_slug(project):
    """Claude Code's project folder name: every non-alphanumeric character of the path becomes `-`."""
    return re.sub(r'[^A-Za-z0-9]', '-', str(project))


def trim(text):
    """One line, secret-looking values masked, cut at LIMIT characters."""
    text = ' '.join(str(text).split())
    for rx, sub in MASKS:
        text = rx.sub(sub, text)
    return text if len(text) <= LIMIT else text[:LIMIT - 1] + '…'


def tool_name(value):
    return value if isinstance(value, str) and NAME_RE.match(value) else '?'


def first_str(mapping, keys):
    """Value of the first fixed key holding a non-empty string (cut early so a pending call stays small)."""
    if isinstance(mapping, dict):
        for k in keys:
            v = mapping.get(k)
            if isinstance(v, str) and v:
                return v[:LIMIT * 4]
    return ''


def records(path):
    """Yield one parsed JSON object per line; None for a line (or an unreadable file) that cannot be parsed."""
    try:
        with open(path, encoding='utf-8-sig', errors='replace') as f:
            for line in f:
                if line.strip():
                    try:
                        yield json.loads(line)
                    except ValueError:
                        yield None
    except OSError:
        yield None


class Session:
    def __init__(self, sid, sub=False):
        self.id, self.sub, self.start, self.calls, self.errors, self.repeats = sid, sub, None, 0, 0, 0
        self.failing, self.seen, self.called = [], False, set()

    def call(self, tool, target, live):
        """Count one tool call; a (tool, target) already called in this session is a repeat (no target: cannot tell)."""
        key = (tool, target)
        if live:
            self.calls += 1
            self.repeats += bool(target) and key in self.called
        self.called.add(key)

    def touch(self, ts):
        self.seen = True
        if ts and (self.start is None or ts < self.start):
            self.start = ts

    def fail(self, tool, target):
        self.errors += 1
        self.failing.append({'tool': tool, 'target': trim(target)})

    def as_dict(self):
        return {'id': self.id, 'sub': self.sub, 'start': fmt(self.start), 'tool_calls': self.calls,
                'errors': self.errors, 'repeats': self.repeats, 'failing': self.failing}


def scan_claude(path, since):
    """(Session | None, skipped). tool_use blocks are paired with their tool_result by id. A subagent transcript
    (<session>/subagents/<agent>.jsonl) is a `sub` session named <session>/<agent>."""
    sub = path.parent.name == 'subagents'
    s = Session(f"{path.parent.parent.name}/{path.stem}" if sub else path.stem, sub)
    skipped, pending, seen, last = 0, {}, set(), None
    for rec in records(path):
        if not isinstance(rec, dict) or not isinstance(rec.get('type'), str):
            skipped += 1
            continue
        ts = parse_ts(rec.get('timestamp')) or last
        last = ts
        live = ts is not None and ts >= since
        if live:
            s.touch(ts)
        msg = rec.get('message')
        content = msg.get('content') if isinstance(msg, dict) else None
        bad = False
        for item in content if isinstance(content, list) else ():
            kind = item.get('type') if isinstance(item, dict) else None
            if kind == 'tool_use':
                iid, name = item.get('id'), item.get('name')
                if not isinstance(iid, str) or not isinstance(name, str):
                    bad = True
                elif iid not in seen:
                    seen.add(iid)
                    pending[iid] = (tool_name(name), first_str(item.get('input'), CLAUDE_TARGET_KEYS))
                    s.call(*pending[iid], live)
            elif kind == 'tool_result' and item.get('is_error') is True and live:
                s.fail(*pending.get(item.get('tool_use_id'), ('?', '')))
        skipped += bad
    return (s if s.seen else None), skipped


def unquote(v):
    """Antigravity stores string args JSON-quoted (`"c:\\\\Users\\\\x"`): decode those, leave anything else as is."""
    if isinstance(v, str) and len(v) >= 2 and v[0] == v[-1] == '"':
        try:
            d = json.loads(v)
            return d if isinstance(d, str) else v
        except ValueError:
            return v[1:-1]
    return v


def under(path, root):
    if not isinstance(path, str) or not path:
        return False
    n = os.path.normcase(os.path.normpath(path))
    return n == root or n.startswith(root.rstrip(os.sep) + os.sep)


def scan_agy(path, since, root):
    """(Session | None, skipped). Scoped to the project by the paths its tool calls touch (any step, any time).
    A step that fails without tool_calls (type GENERIC: the error of the call before it) takes the calls of the step
    just before it."""
    s, skipped, last, mine, pending = Session(path.parents[2].name), 0, None, False, None
    for rec in records(path):
        if not isinstance(rec, dict) or not ({'type', 'status', 'tool_calls'} & rec.keys()):
            skipped += 1
            continue
        ts = parse_ts(rec.get('created_at')) or last
        last = ts
        live = ts is not None and ts >= since
        raw = rec.get('tool_calls')
        calls = [c for c in raw if isinstance(c, dict)] if isinstance(raw, list) else []
        argv = []
        for c in calls:
            a = c.get('args')
            if isinstance(a, str):
                try:
                    a = json.loads(a)
                except ValueError:
                    a = None
            a = a if isinstance(a, dict) else {}
            argv.append((tool_name(c.get('name')), {k: unquote(a[k]) for k in AGY_SCOPE_KEYS + AGY_TARGET_KEYS if k in a}))
        before, pending = pending, argv
        mine = mine or any(under(a.get(k), root) for _, a in argv for k in AGY_SCOPE_KEYS)
        for name, a in argv:
            s.call(name, first_str(a, AGY_TARGET_KEYS), live)
        if not live:
            continue
        s.touch(ts)
        status = rec.get('status')
        if (isinstance(status, str) and status.upper() in ('ERROR', 'INVALID')) or rec.get('error'):
            s.errors += 1
            if not argv and rec.get('type') == 'GENERIC':
                argv = before
            for name, a in argv or [(tool_name(rec.get('type')), {})]:
                s.failing.append({'tool': name, 'target': trim(first_str(a, AGY_TARGET_KEYS))})
    return (s if mine and s.seen else None), skipped


def scan_host(files, scanner, since):
    sessions, skipped = [], 0
    for f in files:
        try:
            if since and f.stat().st_mtime < since.timestamp():
                continue  # untouched since the watermark: cannot hold a live record
        except OSError:
            skipped += 1
            continue
        s, n = scanner(f)
        skipped += n
        if s:
            sessions.append(s)
    sessions.sort(key=lambda x: (-x.errors, x.start or datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)))
    return sessions, skipped


def claude_files(root, slug):
    if not root.is_dir():
        return None
    want = slug.casefold()
    out = []
    for d in sorted(root.iterdir()):
        n = d.name.casefold()
        if d.is_dir() and (n == want or n.startswith(want + '--claude-worktrees-')):
            out += sorted(d.glob('*.jsonl')) + sorted(d.glob('*/subagents/*.jsonl'))
    return out


def agy_files(root):
    return sorted(root.glob('*/.system_generated/logs/transcript.jsonl')) if root.is_dir() else None


def render(report):
    lines = [f"[NIGHTLY-SCAN since {report['since']} · project {report['project']}]"]
    for host in ('claude', 'agy'):
        h = report['hosts'][host]
        if h is None:
            lines.append(f"{host}: transcript root not found")
            continue
        subs = sum(s['sub'] for s in h['sessions'])
        lines.append(f"{host}: {len(h['sessions']) - subs} sessions · {sum(s['tool_calls'] for s in h['sessions'])} tool calls"
                     f" · {sum(s['errors'] for s in h['sessions'])} errors" + (f" · {subs} subagent transcripts" if subs else ""))
        for s in h['sessions']:
            lines.append(f"  {'sub ' if s['sub'] else ''}{s['id']} {s['start']} calls={s['tool_calls']} "
                         f"errors={s['errors']} repeats={s['repeats']}")
            lines += [f"    ! {f['tool']}  {f['target']}".rstrip() for f in s['failing'][:MAX_SHOWN]]
            if len(s['failing']) > MAX_SHOWN:
                lines.append(f"    … +{len(s['failing']) - MAX_SHOWN} more failing calls (--json lists all)")
    lines.append(f"skipped: {report['skipped']} unparsable/unknown records")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only per-session tool-call and failure scan (0d Phase 1).")
    ap.add_argument('--since', help="ISO 8601 watermark (default: last_run in --state, else 24 hours ago)")
    ap.add_argument('--project', default='.', help="project root the sessions are scoped to (default: cwd)")
    ap.add_argument('--state', help="nightly_state file read for the default --since "
                                    "(default: <project>/docs/nightly/.last-run.json)")
    ap.add_argument('--claude-root', default=str(Path.home() / '.claude' / 'projects'))
    ap.add_argument('--agy-root', default=str(Path.home() / '.gemini' / 'antigravity' / 'brain'))
    ap.add_argument('--json', action='store_true', help="machine-readable output")
    args = ap.parse_args(argv)

    project = Path(args.project).resolve()
    if args.since:
        since = parse_ts(args.since)
        if since is None:
            ap.error(f"--since is not an ISO 8601 timestamp: {args.since}")
    else:
        state = Path(args.state) if args.state else project / nightly_state.STATE
        since = parse_ts(nightly_state.load(state)['last_run']) or \
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)

    root = os.path.normcase(os.path.normpath(str(project)))
    cfiles = claude_files(Path(args.claude_root), claude_slug(project))
    afiles = agy_files(Path(args.agy_root))
    claude, c_skip = scan_host(cfiles or (), lambda f: scan_claude(f, since), since)
    agy, a_skip = scan_host(afiles or (), lambda f: scan_agy(f, since, root), since)
    report = {'since': fmt(since), 'project': str(project), 'skipped': c_skip + a_skip,
              'hosts': {'claude': None if cfiles is None else {'sessions': [s.as_dict() for s in claude]},
                        'agy': None if afiles is None else {'sessions': [s.as_dict() for s in agy]}}}
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else render(report))
    return 0


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except AttributeError:
            pass
    sys.exit(main())
