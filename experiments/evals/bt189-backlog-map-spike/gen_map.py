#!/usr/bin/env python3
"""BT-189 A3: render a 9-column BACKLOG_MAP table from GitHub with ONE paginated GraphQL query.
Read-only (GraphQL query only). Usage: gen_map.py --repo OWNER/NAME --out PATH
Prints one JSON line: {"calls": n, "issues": n, "seconds": s, "chars": n}."""
import argparse
import json
import subprocess
import sys
import time

QUERY = """query($owner:String!,$name:String!,$after:String){repository(owner:$owner,name:$name){
issues(first:100,after:$after,orderBy:{field:CREATED_AT,direction:ASC}){pageInfo{hasNextPage endCursor}
nodes{number title state labels(first:50){nodes{name}} milestone{title} parent{number}
blockedBy(first:50){nodes{number}}}}}}"""


def fetch(repo):
    owner, name = repo.split('/')
    calls, after, nodes = 0, None, []
    while True:
        cmd = ['gh', 'api', 'graphql', '-f', f'query={QUERY}', '-f', f'owner={owner}', '-f', f'name={name}']
        if after:
            cmd += ['-f', f'after={after}']
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        calls += 1
        if r.returncode != 0:
            sys.exit(f"gh failed: {r.stderr[:500]}")
        page = json.loads(r.stdout)['data']['repository']['issues']
        nodes += page['nodes']
        if not page['pageInfo']['hasNextPage']:
            return nodes, calls
        after = page['pageInfo']['endCursor']


def bt(n):
    return f"BT-{int(n):03d}"


def render(nodes):
    head = ["| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |",
            "|---|---|---|---|---|---|---|---|---|"]
    rows = []
    for n in sorted(nodes, key=lambda x: -x['number']):
        labels = [l['name'] for l in n['labels']['nodes']]
        status = next((l[7:] for l in labels if l.startswith('status:')), None)
        if n['state'] == 'CLOSED':
            status = 'done'
        other = sorted(l for l in labels if not l.startswith('status:'))
        bb = sorted(bt(b['number']) for b in (n['blockedBy'] or {}).get('nodes', []))
        cells = [bt(n['number']), n['title'].replace('|', '/'), status or '—', ', '.join(other) or '—',
                 (n['milestone'] or {}).get('title') or '—', bt(n['parent']['number']) if n['parent'] else '—',
                 ', '.join(bb) or '—', '—', '—']
        rows.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(head + rows) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    t0 = time.perf_counter()
    nodes, calls = fetch(a.repo)
    text = render(nodes)
    dt = time.perf_counter() - t0
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print(json.dumps({'calls': calls, 'issues': len(nodes), 'seconds': round(dt, 2), 'chars': len(text)}))


if __name__ == '__main__':
    main()
