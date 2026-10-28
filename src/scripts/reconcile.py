#!/usr/bin/env python3
"""reconcile.py — Terminal Sync Invariant gate and blocker edge verdicts (never writes GitHub).

`tracker: github` (the default backend): GitHub is the only store. `--ids` asserts that the issues carry the
state the calling phase states itself, `--expect "BT-7:status=in review;BT-7:blocked_by=BT-6"` or `--expect-file F`
(fields as `--fields`; a caller passes only the fields it wrote, so a gate never false-blocks on a field outside
its concern). `--pr-id` scopes the PR-link check to the one issue that received the PR comment. With `status` in
the expectation the gate also checks issue state: closed must match done. One batched fetch serves the gate;
`--with-edges blockers|dependents` adds the edge verdicts from the same fetch. A `gh` failure after three retries
exits 3 (`[GH-UNAVAILABLE]`); GitHub mode never falls back to a local copy. Non-zero exit: the calling workflow
HALTS, applies the missing write and re-runs.

`tracker: local`: the issues.py store (the `<repo>/issues` branch) is the store and there is no gate; only `--edges`
runs, over its issues (closed ones count as done). `--backlog F` reads a v5 map file instead (fixtures).

--edges (read-only decision list; D3 blocker predicate): `blockers` prints each effective blocker (own + parent epic's)
of the ids as `[BLOCKER-OK|BLOCKER-UNMET|BLOCKER-UNKNOWN D <- B] same-unit|cross-unit: reason` (exit 1 unless all OK);
`dependents` prints each stored edge naming the ids as `[CLEAR D <- B]` + its `removeBlockedBy` cmd, or `[KEEP D <- B]`.
Same ship unit (pr_body.resolve_unit) -> blocker shipped; else its code must be on the default branch (PR merged).
`--all-open` (local backend) scopes `--edges` to every open issue.

Usage:
  python .agents/scripts/reconcile.py --ids BT-007[,BT-006] [--pr-id BT-007] [--fields status,blocked_by] \
      --expect "BT-007:status=done" [--with-edges dependents]
  python .agents/scripts/reconcile.py --edges blockers|dependents (--ids BT-007[,…] | --all-open)
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _tracker_common import bt_id, csv_list, edge_verdict, effective_blockers, make_row, norm, open_ids

STATUS_RE = re.compile(r'^status:(.+)$')
ALL_FIELDS = ('status', 'milestone', 'labels', 'parent', 'blocked_by')


def parse_backlog(path):
    """{BT-id: {fields}} of a v5 map file (issues.parse_backlog)."""
    import issues  # lazy: the GitHub gate runs with only this file and _tracker_common.py beside it
    return issues.parse_backlog(path)


def issue_number(bt):
    m = re.match(r'^BT-0*(\d+)$', bt)
    return m.group(1) if m else None


def closed_on_github(row, gh):
    """Drift text when the issue is CLOSED on GitHub while its row is not done, else None.
    Per-field compare cannot see this (the labels still say `in review`). Pure."""
    if gh.get('state') == 'CLOSED' and row['status'] != 'done':
        return f"closed on GitHub, expect={row['status']}"
    return None


def open_on_github(row, gh):
    """Drift text when the issue is still OPEN on GitHub while its row is done (a dropped `gh issue close`
    at ship), else None. Pure."""
    if gh.get('state') == 'OPEN' and row['status'] == 'done':
        return "open on GitHub, expect=done"
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
        if gh_status != norm(row['status']):
            drift.append(f"status expect={row['status']} gh={gh_status}")

    if 'milestone' in fields:
        gh_ms = (gh.get('milestone') or {}).get('title')
        if gh_ms != norm(row['milestone']):
            drift.append(f"milestone expect={norm(row['milestone'])} gh={gh_ms}")

    if 'labels' in fields:
        # status:* is compared under `status`; strip it on both sides.
        gh_nonstatus = {l for l in gh_labels if not STATUS_RE.match(l)}
        want_labels = {l for l in row['labels'] if not STATUS_RE.match(l)}
        if want_labels != gh_nonstatus:
            drift.append(f"labels expect_only={sorted(want_labels - gh_nonstatus)} "
                         f"gh_only={sorted(gh_nonstatus - want_labels)}")

    if 'blocked_by' in fields and 'blockedBy' in gh:
        # Real gh returns a connection {"nodes": [...], "totalCount": n} (not paginated
        # past its first page here); a flat list and None are tolerated.
        bb = gh.get('blockedBy') or []
        if isinstance(bb, dict):
            bb = bb.get('nodes') or []
        gh_bb = {bt_id(i['number']) for i in bb}
        if row['blocked_by'] != gh_bb:
            drift.append(f"blocked_by expect={sorted(row['blocked_by'])} gh={sorted(gh_bb)}")

    if 'parent' in fields and 'parent' in gh:
        p = gh.get('parent')
        gh_parent = bt_id(p['number']) if p else None
        if gh_parent != norm(row['parent']):
            drift.append(f"parent expect={norm(row['parent'])} gh={gh_parent}")

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


def edges_cmd(args, rows, ids, merged_of):
    """--edges: print one D3 verdict line per edge. Decides only, never writes. Returns the exit code."""
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


# --- GitHub mode (`tracker: github`): no map. GitHub is the only store; --expect states the intended state. ---------
ARCH_DEFAULT = '.memory/ARCHITECTURE.md'
RETRY_DELAYS = (1, 2, 4)  # seconds before each retry: one try, then 3 retries, then GhError
CHUNK = 50  # issues per GraphQL call; more ids paginate into several calls
EXPECT_FIELDS = ALL_FIELDS
_sleep = time.sleep


class GhError(RuntimeError):
    """GitHub unreachable or answering with errors after every retry. Never a reason to fall back to a local copy."""


def read_tracker(path):
    """`tracker:` value in the frontmatter of ARCHITECTURE.md, None when the file or the key is absent."""
    try:
        text = Path(path).read_text(encoding='utf-8-sig')
    except OSError:
        return None
    m = re.search(r'^tracker:\s*(\S+)\s*$', text.split('---', 2)[1] if text.startswith('---') else '', re.M)
    return m.group(1).strip('"\'') if m else None


def _github_remote():
    try:
        r = subprocess.run(['git', 'remote', 'get-url', 'origin'], capture_output=True, text=True)
    except FileNotFoundError:
        return False
    return r.returncode == 0 and 'github.com' in r.stdout


def _retry(ok):
    """True when `ok()` succeeds within one try plus len(RETRY_DELAYS) retries."""
    for i in range(len(RETRY_DELAYS) + 1):
        if i:
            _sleep(RETRY_DELAYS[i - 1])
        if ok():
            return True
    return False


def _has_store(arch):
    """True when the issues.py tracker branch exists in this repository."""
    import issues  # lazy: local backend only (the GitHub gate stands alone)
    try:
        return issues.head(f"refs/heads/{issues.branch_name(arch)}") is not None
    except (issues.IssuesError, OSError):
        return False


def resolve_backend(arch=ARCH_DEFAULT, backlog=None):
    """'github' | 'local' | None (halt). 1 key present -> use it (an unknown value halts); 2 no key + a v5 map or
    the issues.py tracker branch -> local; 3 no key, neither, a GitHub remote and gh ready -> github; 4 otherwise
    halt. A transient gh failure is retried and then halts: it is never read as `local`."""
    key = read_tracker(arch)
    if key:
        return key if key in ('github', 'local') else None
    import issues  # lazy: local backend only (the GitHub gate stands alone)
    if Path(backlog or issues.MAP_DEFAULT).exists() or _has_store(arch):
        return 'local'
    return 'github' if _github_remote() and _retry(gh_available) else None


def _gh_run(args):
    try:
        r = subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf-8', errors='replace')
    except FileNotFoundError:
        return 127, '', 'gh not found'
    return r.returncode, r.stdout, r.stderr


def gh_query(query):
    """The `repository` object of one GraphQL call. Retried; a response whose only errors are NOT_FOUND is data
    (the missing issue is a null alias). Raises GhError once the retries are spent."""
    args = ['api', 'graphql', '-F', 'owner={owner}', '-F', 'name={repo}', '-f', 'query=' + query]
    why = ''
    for i in range(len(RETRY_DELAYS) + 1):
        if i:
            _sleep(RETRY_DELAYS[i - 1])
        rc, out, err = _gh_run(args)
        try:
            body = json.loads(out)
        except json.JSONDecodeError:
            body = None
        body = body if isinstance(body, dict) else {}
        errors = body.get('errors') or []
        repo = (body.get('data') or {}).get('repository')
        if repo is not None and all(e.get('type') == 'NOT_FOUND' for e in errors):
            return repo
        reasons = [err.strip(), *(e.get('message') or e.get('type') or '' for e in errors), f"exit {rc}"]
        why = next(r for r in reasons if r).splitlines()[0]
    raise GhError(f"gh api graphql failed after {len(RETRY_DELAYS) + 1} attempts: {why}")


_NODE = ("number state milestone{title} labels(first:50){nodes{name}} "
         "parent{number state milestone{title} labels(first:50){nodes{name}}}")


def build_query(nums, comments=False, edges=False):
    sel = "...F blockedBy(first:100){nodes{...F}}"
    if comments:
        sel += " comments(last:100){nodes{body}}"
    if edges:  # dependents, and the parent epic's blockers (effective_blockers)
        sel += " blocking(first:100){nodes{...F}} parent{blockedBy(first:100){nodes{...F}}}"
    items = ' '.join(f"i_{n}: issue(number:{n}){{{sel}}}" for n in nums)
    return ("query($owner:String!,$name:String!){repository(owner:$owner,name:$name){" + items
            + "}} fragment F on Issue {" + _NODE + "}")


def fetch_nodes(nums, comments=False, edges=False):
    """{issue number: GraphQL node, or None when the issue does not exist}, CHUNK issues per call."""
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
    """A node in the shape `gh issue view --json` gives compare(). Pure."""
    return {'number': node['number'], 'state': node['state'], 'labels': [{'name': n} for n in _names(node)],
            'milestone': node.get('milestone'), 'blockedBy': {'nodes': _conn(node, 'blockedBy')},
            'parent': node.get('parent'), 'comments': _conn(node, 'comments')}


def node_row(node):
    """A node as a parse_backlog row. A closed issue without a status label counts as done (closed = done). Pure."""
    names = _names(node)
    status = next((m.group(1) for n in names if (m := STATUS_RE.match(n))), '') or ('done' if node['state'] == 'CLOSED' else '')
    parent = node.get('parent')
    return make_row(status, names, (node.get('milestone') or {}).get('title'),
                    bt_id(parent['number']) if parent else None, {bt_id(b['number']) for b in _conn(node, 'blockedBy')})


def rows_from_nodes(nodes):
    """{BT-id: row} of the fetched nodes and every issue they reference (blockers, dependents, parents), so edges_cmd
    and edge_verdict run unchanged. Referenced issues are stubs; a fetched node overrides its stub. Pure."""
    found = [n for n in nodes.values() if n]
    rows = {}

    def put(node):
        rows[bt_id(node['number'])] = node_row(node)

    for node in found:
        parent = node.get('parent')
        if parent:
            put(parent)
            rows[bt_id(parent['number'])]['blocked_by'] = {bt_id(b['number']) for b in _conn(parent, 'blockedBy')}
            for blocker in _conn(parent, 'blockedBy'):
                put(blocker)
        for ref in _conn(node, 'blockedBy') + _conn(node, 'blocking'):
            put(ref)
    for node in found:  # fetched nodes last: they carry the full row
        put(node)
    for node in found:  # a blocking edge is a stored `blocked_by` on the dependent
        for dep in _conn(node, 'blocking'):
            rows[bt_id(dep['number'])]['blocked_by'].add(bt_id(node['number']))
    return rows


def _padded(token):
    m = re.fullmatch(r'BT-0*(\d+)', token.strip())
    return bt_id(m.group(1)) if m else token.strip()


def parse_expect(text):
    """`BT-n:field=value` items split on `;` or newlines (`#` lines ignored) -> {BT-nnn: {field: value}}. labels and
    blocked_by take comma lists (sets), a none token means empty. ValueError on a malformed item. Pure."""
    out = {}
    for item in (i.strip() for i in re.split(r'[;\n]', text)):
        if not item or item.startswith('#'):
            continue
        head, eq, value = item.partition('=')
        ident, colon, field = head.partition(':')
        field, value = field.strip(), value.strip()
        if not (eq and colon and re.fullmatch(r'BT-\d+', ident.strip())) or field not in EXPECT_FIELDS:
            raise ValueError(f"bad expectation {item!r}: want BT-<n>:<field>=<value> with field one of {', '.join(EXPECT_FIELDS)}")
        if field in ('labels', 'blocked_by'):
            vals = set(csv_list(value))
            value = {_padded(v) for v in vals} if field == 'blocked_by' else vals
        elif field == 'parent':
            value = _padded(value)
        out.setdefault(_padded(ident), {})[field] = value
    return out


def github_gate(ids, nodes, expect, fields, pr_id):
    """The post-condition gate from GitHub alone: each id's expected fields (and the PR link on `pr_id`) against its
    node. Returns (exit code, lines). Pure."""
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
    """--ids against GitHub: one batched fetch feeds the gate and, with --edges, the blocker verdicts (combined mode)."""
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


def main(argv=None):
    ap = argparse.ArgumentParser(description="Terminal Sync Invariant gate (tracker: github) and D3 blocker edge verdicts.")
    scope = ap.add_mutually_exclusive_group(required=True)
    scope.add_argument('--ids', help="comma-separated BT ids, e.g. BT-007,BT-006")
    scope.add_argument('--all-open', action='store_true',
                       help="local backend with --edges: every open issue of the store")
    ap.add_argument('--pr-id', help="the id that must carry a PR-link comment (e.g. the shipped slice)")
    ap.add_argument('--fields', default=None,
                    help="fields to check (default: all). Pass only the fields this phase wrote.")
    ap.add_argument('--backlog', default=None,
                    help="local backend: read rows from this v5 map file instead of the issues.py store (fixtures)")
    ap.add_argument('--edges', choices=('blockers', 'dependents'),
                    help="D3 blocker verdicts for the --ids / --all-open scope, read-only: blockers = each effective "
                         "blocker of the ids; dependents = each stored edge naming the ids (CLEAR or KEEP)")
    ap.add_argument('--arch', default=ARCH_DEFAULT,
                    help="ARCHITECTURE.md whose `tracker: github|local` frontmatter key picks the backend")
    ap.add_argument('--expect', help="tracker: github only. The intended state: "
                                     "`BT-7:status=in review;BT-7:blocked_by=BT-6,BT-8` (fields: " + ', '.join(ALL_FIELDS) + ")")
    ap.add_argument('--with-edges', choices=('blockers', 'dependents'),
                    help="tracker: github only. Combined mode: the --ids gate plus the --edges verdicts from ONE fetch")
    ap.add_argument('--expect-file', help="--expect read from a file (`;` or one item per line, `#` comments)")
    args = ap.parse_args(argv)
    if args.edges and (args.pr_id or args.fields is not None):
        ap.error("--edges is a separate run: not with --pr-id/--fields (the gate plus edges: --with-edges)")
    args.fields = args.fields or ','.join(ALL_FIELDS)

    fields = {f.strip() for f in args.fields.split(',') if f.strip()}
    backend = resolve_backend(args.arch, args.backlog)
    if backend is None:
        key = read_tracker(args.arch)
        why = (f"`tracker: {key}` in ARCHITECTURE.md is not github or local" if key else
               "no `tracker:` key in ARCHITECTURE.md, no local issue store and no ready GitHub connection")
        print(f"[TRACKER-UNRESOLVED: {why}; nothing checked. Run /stratosphere-setup to record the tracker backend]")
        return 3
    github = backend == 'github'
    if github and args.all_open:
        ap.error("--all-open is a local-backend run: not with `tracker: github`")
    if not github and (args.expect or args.expect_file or args.with_edges):
        ap.error("--expect/--expect-file/--with-edges need `tracker: github`")
    if not github and not args.edges:
        ap.error("local backend: only --edges is supported (issues.py validates every write; there is no gate to run)")
    if github:
        gate = not args.edges
        args.edges = args.edges or args.with_edges
        try:
            text = (args.expect or '') + ';' + (Path(args.expect_file).read_text(encoding='utf-8') if args.expect_file else '')
            expect = parse_expect(text)
        except (OSError, ValueError) as e:
            ap.error(f"--expect/--expect-file: {e}")
        return github_main(args, [_padded(i) for i in args.ids.split(',') if i.strip()], expect, fields, gate)
    if args.backlog:
        rows, merged_of = parse_backlog(args.backlog), make_merged_of()
    else:
        import issues  # lazy: local backend only (the GitHub gate stands alone)
        try:
            store = issues.Tracker(args.arch).store()
        except issues.IssuesError as e:
            print(e)
            return 3
        rows, merged_of = store.rows(), issues.make_merged_of(store)
    ids = open_ids(rows) if args.all_open else [i.strip() for i in args.ids.split(',') if i.strip()]
    return edges_cmd(args, rows, ids, merged_of)


if __name__ == '__main__':
    sys.exit(main())
