#!/usr/bin/env python3
"""reconcile.py — Terminal Sync Invariant gate and blocker edge verdicts (never writes GitHub)."""
import argparse, json, re, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _tracker_common import (
    ALL_FIELDS, EXPECT_FIELDS, STATUS_RE, _canon_id, _padded, bt_id, closed_on_github,
    compare, csv_list, edge_verdict, effective_blockers, issue_number, make_row,
    norm, open_ids, open_on_github, parse_edges, parse_expect, read_tracker,
    topological_sort
)


def parse_backlog(path):
    """{BT-id: {fields}} of a v5 map file (issues.parse_backlog)."""
    import issues
    return issues.parse_backlog(path)


def _gh_json(num, fields):
    try:
        r = subprocess.run(['gh', 'issue', 'view', num, '--json', ','.join(fields)], capture_output=True, text=True)
        return json.loads(r.stdout) if r.returncode == 0 else None
    except FileNotFoundError:
        return None


def gh_available():
    try:
        return subprocess.run(['gh', 'auth', 'status'], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def _pr_state(k):
    try:
        r = subprocess.run(['gh', 'pr', 'view', k, '--json', 'state'], capture_output=True, text=True)
        return json.loads(r.stdout).get('state') if r.returncode == 0 else None
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        return None


def pr_merge_state(bt, cache=None):
    """'merged' | 'open' | 'none' | None for a child slice's `Shipped in PR` PR."""
    if cache is not None and bt in cache:
        return cache[bt]
    num, out = issue_number(bt), None
    data = _gh_json(num, ['comments']) if num else None
    if data is not None:
        links = [m.group(1) for c in data.get('comments') or [] if (m := re.search(r'/pull/(\d+)', c.get('body') or ''))]
        out = 'none' if not links else {'MERGED': 'merged', 'OPEN': 'open', 'CLOSED': 'open'}.get(_pr_state(links[-1]))
    if cache is not None:
        cache[bt] = out
    return out


def make_merged_of():
    cache, online = {}, []

    def merged_of(bt):
        if bt not in cache:
            if not online:
                online.append(gh_available())
            cache[bt] = pr_merge_state(bt) if online[0] else None
        return cache[bt]
    return merged_of


def _graphql(mutation, second, a, b):
    return (f"gh api graphql -f query='mutation($i:ID!,$j:ID!){{{mutation}(input:{{issueId:$i,{second}:$j}})"
            f"{{issue{{number}}}}}}' -f i=\"$(gh issue view {a} --json id -q .id)\" -f j=\"$(gh issue view {b} --json id -q .id)\"")


def _edge(mutation, second, a, b):
    nums = [(x, x if x.isdigit() else issue_number(x)) for x in (a, b)]
    return f"python .agents/scripts/issues.py set {a} --remove-blocker {b}" if any(n is None for _, n in nums) else _graphql(mutation, second, nums[0][1], nums[1][1])


def edges_cmd(args, rows, ids, merged_of):
    code = 0
    for bt in (i for i in ids if i not in rows):
        print(f"[EDGES-ABSENT {bt}: absent from the tracker]")
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
    for dep in open_ids(rows):
        for blk in sorted(rows[dep]['blocked_by']):
            if args.all_open or blk in ids:
                verdict, scope, why = edge_verdict(dep, blk, rows, merged_of)
                print(f"[{'CLEAR' if verdict == 'OK' else 'KEEP'} {dep} <- {blk}] {scope}: {why}")
                if verdict == 'OK':
                    print(f"  cmd: {_edge('removeBlockedBy', 'blockingIssueId', dep, blk)}")
    return code


ARCH_DEFAULT = '.memory/ARCHITECTURE.md'
RETRY_DELAYS = (1, 2, 4)
CHUNK = 50
_sleep = time.sleep


class GhError(RuntimeError):
    pass


def _github_remote():
    try:
        r = subprocess.run(['git', 'remote', 'get-url', 'origin'], capture_output=True, text=True)
        return r.returncode == 0 and 'github.com' in r.stdout
    except FileNotFoundError:
        return False


def _retry(ok):
    for i in range(len(RETRY_DELAYS) + 1):
        if i:
            _sleep(RETRY_DELAYS[i - 1])
        if ok():
            return True
    return False


def _has_store(arch):
    import issues
    try:
        return issues.head(f"refs/heads/{issues.branch_name(arch)}") is not None
    except (issues.IssuesError, OSError):
        return False


def resolve_backend(arch=ARCH_DEFAULT, backlog=None):
    key = read_tracker(arch)
    if key:
        return key if key in ('github', 'local') else None
    import issues
    if Path(backlog or issues.MAP_DEFAULT).exists() or _has_store(arch):
        return 'local'
    return 'github' if _github_remote() and _retry(gh_available) else None


def _gh_run(args):
    try:
        r = subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf-8', errors='replace')
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return 127, '', 'gh not found'


def gh_query(query):
    args = ['api', 'graphql', '-F', 'owner={owner}', '-F', 'name={repo}', '-f', 'query=' + query]
    why = ''
    for i in range(len(RETRY_DELAYS) + 1):
        if i:
            _sleep(RETRY_DELAYS[i - 1])
        rc, out, err = _gh_run(args)
        try:
            body = json.loads(out) if isinstance(json.loads(out), dict) else {}
        except (json.JSONDecodeError, TypeError):
            body = {}
        errors, repo = body.get('errors') or [], (body.get('data') or {}).get('repository')
        if repo is not None and all(e.get('type') == 'NOT_FOUND' for e in errors):
            return repo
        reasons = [err.strip(), *(e.get('message') or e.get('type') or '' for e in errors), f"exit {rc}"]
        why = next(r for r in reasons if r).splitlines()[0]
    raise GhError(f"gh api graphql failed after {len(RETRY_DELAYS) + 1} attempts: {why}")


_NODE = ("number state milestone{title} labels(first:50){nodes{name}} "
         "parent{number state milestone{title} labels(first:50){nodes{name}}}")


def build_query(nums, comments=False, edges=False):
    sel = "...F blockedBy(first:100){nodes{...F}}" + (" comments(last:100){nodes{body}}" if comments else "")
    if edges:
        sel += " blocking(first:100){nodes{...F}} parent{blockedBy(first:100){nodes{...F}}}"
    items = ' '.join(f"i_{n}: issue(number:{n}){{{sel}}}" for n in nums)
    return f"query($owner:String!,$name:String!){{repository(owner:$owner,name:$name){{{items}}}}} fragment F on Issue {{{_NODE}}}"


def fetch_nodes(nums, comments=False, edges=False):
    out = {}
    for i in range(0, len(nums), CHUNK):
        part = nums[i:i + CHUNK]
        repo = gh_query(build_query(part, comments, edges))
        out.update({n: repo.get(f"i_{n}") for n in part})
    return out


def _conn(node, key):
    return (node.get(key) or {}).get('nodes') or []


def _names(node):
    return [l['name'] for l in _conn(node, 'labels')]


def node_gh(node):
    return {'number': node['number'], 'state': node['state'], 'labels': [{'name': n} for n in _names(node)],
            'milestone': node.get('milestone'), 'blockedBy': {'nodes': _conn(node, 'blockedBy')},
            'parent': node.get('parent'), 'comments': _conn(node, 'comments')}


def node_row(node):
    names = _names(node)
    status = 'done' if node['state'] == 'CLOSED' else next((m.group(1) for n in names if (m := STATUS_RE.match(n))), '')
    p = node.get('parent')
    return make_row(status, names, (node.get('milestone') or {}).get('title'),
                    bt_id(p['number']) if p else None, {bt_id(b['number']) for b in _conn(node, 'blockedBy')})


def rows_from_nodes(nodes):
    found, rows = [n for n in nodes.values() if n], {}
    put = lambda node: rows.setdefault(bt_id(node['number']), node_row(node))
    for node in found:
        if (p := node.get('parent')):
            put(p)
            rows[bt_id(p['number'])]['blocked_by'] = {bt_id(b['number']) for b in _conn(p, 'blockedBy')}
            for blocker in _conn(p, 'blockedBy'):
                put(blocker)
        for ref in _conn(node, 'blockedBy') + _conn(node, 'blocking'):
            put(ref)
    for node in found:
        rows[bt_id(node['number'])] = node_row(node)
        for dep in _conn(node, 'blocking'):
            rows[bt_id(dep['number'])]['blocked_by'].add(bt_id(node['number']))
    return rows


def local_gate(ids, store, expect, fields, pr_id):
    lines, drifted = [], []
    for bt in ids:
        issue = store.issues.get(bt)
        if issue is None:
            drifted.append(f"[MIRROR-DRIFT {bt}: issue not found in local store]")
            continue
        want = {k: v for k, v in expect.get(bt, {}).items() if k in fields}
        target_gh = {
            'state': 'CLOSED' if issue['closed'] or issue['status'] == 'done' else 'OPEN',
            'labels': [{'name': l} for l in issue['labels']] + [{'name': f"status:{issue['status']}"}],
            'milestone': {'title': issue['milestone']} if issue['milestone'] else None,
            'blockedBy': {'nodes': [{'number': b} for b in issue['blocked_by']]},
            'parent': {'number': issue['parent']} if issue['parent'] else None,
            'comments': [{'body': c} for c in issue.get('comments', [])],
        }
        closed = (closed_on_github(want, target_gh) or open_on_github(want, target_gh)) if 'status' in want else None
        drift = [closed] if closed else compare(want, target_gh, set(want), check_pr=(bt == pr_id), local=True)
        drifted += [f"[MIRROR-DRIFT {bt}: {d}]" for d in drift]
    if not drifted:
        lines.append(f"[MIRROR-OK {','.join(ids)}]")
    return (1 if drifted else 0), lines + drifted


def github_gate(ids, nodes, expect, fields, pr_id):
    lines, drifted = [], []
    for bt in ids:
        num = issue_number(bt)
        if not num:
            lines.append(f"[local-only {bt} — no GitHub issue to check]")
            continue
        node = nodes.get(int(num))
        if node is None:
            drifted.append(f"[MIRROR-DRIFT {bt}: gh issue #{num} not found]")
            continue
        want = {k: v for k, v in expect.get(bt_id(num), {}).items() if k in fields}
        gh = node_gh(node)
        closed = (closed_on_github(want, gh) or open_on_github(want, gh)) if 'status' in want else None
        drift = [closed] if closed else compare(want, gh, set(want), check_pr=(bt == pr_id))
        drifted += [f"[MIRROR-DRIFT {bt}: {d}]" for d in drift]
    if not drifted:
        lines.append(f"[MIRROR-OK {','.join(ids)}]")
    return (1 if drifted else 0), lines + drifted


def github_main(args, ids, expect, fields, gate):
    nums = sorted({int(issue_number(i)) for i in ids if issue_number(i)})
    try:
        nodes = fetch_nodes(nums, comments=bool(args.pr_id), edges=bool(args.edges))
    except GhError as e:
        print(f"[GH-UNAVAILABLE: {e}; GitHub mode never falls back to a local copy, nothing written]")
        return 3
    code = 0
    if gate:
        code, lines = github_gate(ids, nodes, expect, fields, args.pr_id)
        print("\n".join(lines))
    if args.edges:
        code = max(code, edges_cmd(args, rows_from_nodes(nodes), ids, make_merged_of()))
    return code


def topo_sort_cli(args):
    if args.edges_file:
        text = sys.stdin.read() if args.edges_file == "-" else Path(args.edges_file).read_text(encoding="utf-8")
    elif args.backlog:
        rows = parse_backlog(args.backlog)
        graph = {bid: {_canon_id(b) for b in row.get('blocked_by', []) if _canon_id(b)} for bid, row in rows.items()}
        for bid, blks in list(graph.items()):
            for b in blks:
                graph.setdefault(b, set())
        order, cycle = topological_sort(graph)
        print(f"[CYCLE-DETECTED {' -> '.join(cycle)}]" if cycle else f"[TOPO-ORDER {','.join(order)}]")
        return 1 if cycle else 0
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        print("[TOPO-SORT-ERROR: missing --edges-file, --backlog, or stdin edges input]")
        return 1
    graph = parse_edges(text)
    order, cycle = topological_sort(graph)
    print(f"[CYCLE-DETECTED {' -> '.join(cycle)}]" if cycle else f"[TOPO-ORDER {','.join(order)}]")
    return 1 if cycle else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Terminal Sync Invariant gate (tracker: github) and D3 blocker edge verdicts.")
    scope = ap.add_mutually_exclusive_group(required=False)
    scope.add_argument('--ids', help="comma-separated BT ids, e.g. BT-007,BT-006")
    scope.add_argument('--all-open', action='store_true', help="local backend with --edges: every open issue of the store")
    ap.add_argument('--topo-sort', action='store_true', help="topological DAG sort of issues/edges")
    ap.add_argument('--edges-file', default=None, help="file containing edges for --topo-sort (or - for stdin)")
    ap.add_argument('--pr-id', help="the id that must carry a PR-link comment (e.g. the shipped slice)")
    ap.add_argument('--fields', default=None, help="fields to check (default: all).")
    ap.add_argument('--backlog', default=None, help="local backend: read rows from this v5 map file (fixtures)")
    ap.add_argument('--edges', choices=('blockers', 'dependents'), help="D3 blocker verdicts")
    ap.add_argument('--arch', default=ARCH_DEFAULT, help="ARCHITECTURE.md with tracker: github|local")
    ap.add_argument('--expect', help="The intended state")
    ap.add_argument('--with-edges', choices=('blockers', 'dependents'), help="Combined mode")
    ap.add_argument('--expect-file', help="--expect read from a file")
    args = ap.parse_args(argv)
    if args.topo_sort:
        return topo_sort_cli(args)
    if not (args.ids or args.all_open):
        ap.error("one of the arguments --ids --all-open is required")
    if args.edges and (args.pr_id or args.fields is not None):
        ap.error("--edges is a separate run: not with --pr-id/--fields (the gate plus edges: --with-edges)")
    fields = {f.strip() for f in (args.fields or ','.join(ALL_FIELDS)).split(',') if f.strip()}
    backend = resolve_backend(args.arch, args.backlog)
    if backend is None:
        key = read_tracker(args.arch)
        why = f"`tracker: {key}` in ARCHITECTURE.md is not github or local" if key else "no `tracker:` key in ARCHITECTURE.md, no local issue store and no ready GitHub connection"
        print(f"[TRACKER-UNRESOLVED: {why}; nothing checked. Run /stratosphere-setup to record the tracker backend]")
        return 3
    github = backend == 'github'
    if github and args.all_open:
        ap.error("--all-open is a local-backend run: not with `tracker: github`")
    if not github and not (args.expect or args.expect_file or args.edges or args.with_edges):
        ap.error("local backend: pass --expect/--expect-file (the gate), --edges or --with-edges")
    gate = bool(args.expect or args.expect_file) or (not args.edges)
    args.edges = args.edges or args.with_edges
    expect = {}
    if args.expect or args.expect_file:
        try:
            text = (args.expect or '') + '\n' + (Path(args.expect_file).read_text(encoding='utf-8') if args.expect_file else '')
            expect = parse_expect(text)
        except (OSError, ValueError) as e:
            ap.error(f"--expect/--expect-file: {e}")
    if github:
        return github_main(args, [_padded(i) for i in args.ids.split(',') if i.strip()], expect, fields, gate)
    if args.backlog:
        rows, merged_of, store = parse_backlog(args.backlog), make_merged_of(), None
    else:
        import issues
        try:
            store = issues.Tracker(args.arch).store()
        except issues.IssuesError as e:
            print(e)
            return 3
        rows, merged_of = store.rows(), issues.make_merged_of(store)
    ids = open_ids(rows) if args.all_open else [_padded(i) for i in args.ids.split(',') if i.strip()]
    code = 0
    if gate:
        if args.backlog:
            ap.error(f"{'--with-edges' if args.with_edges else '--expect'} is not supported with --backlog")
        code, lines = local_gate(ids, store, expect, fields, args.pr_id)
        print("\n".join(lines))
    if args.edges:
        code = max(code, edges_cmd(args, rows, ids, merged_of))
    return code


if __name__ == '__main__':
    sys.exit(main())
